import json
from uuid import uuid4
import stripe
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from logging import debug, exception
from json import loads
from sqlalchemy.orm import Session

from config import Config
from db.init_db import Evse, Transaction, get_db, Checkout as CheckoutModel
from integrations.integration import OcppIntegration
from schemas.checkouts import RequestStartStopStatusEnumType

router = APIRouter()

@router.post('/stripe')
async def stripe_webhook(request: Request, STRIPE_SIGNATURE: str | None = Header(default=None), db: Session = Depends(get_db)):
    event = None
    body = b''
    async for chunk in request.stream():
        body += chunk

    # charge.succeed is in connect_event_types, as we are using Stripe Standard accounts
    # for which the events are coming via the Connect-Webhook.
    # If we would use Stripe Express accounts, the events would be coming via the Account-Webhook
    account_event_types = []
    connect_event_types = ["account.updated", "charge.succeeded", "checkout.session.completed"]
    try:
        event_type = loads(body.decode()).get('type')
        debug(' [*WEBHOOK*] Event type {}'.format(event_type))
        if event_type in account_event_types:
            event = stripe.Webhook.construct_event(
                body, STRIPE_SIGNATURE, Config.STRIPE_ENDPOINT_SECRET_ACCOUNT
            )
        elif event_type in connect_event_types:
            event = stripe.Webhook.construct_event(
                body, STRIPE_SIGNATURE, Config.STRIPE_ENDPOINT_SECRET_CONNECT
            )
        else:
            debug(' [*WEBHOOK*] Unhandled event type {}'.format(event_type))
            return {}
    except ValueError as e:
        raise e
    except stripe.error.SignatureVerificationError as e:
        raise e
    
    # Handle the event
    '''
        Removed handling of account changes for now
    '''
    # if event.get('type') == 'account.updated':
    #     # Updating Stripe Account (e.g. after onboarding finished)
    #     account = event.get('data').get('object')
    #     async def update_account(account):
    #         db = Database()
    #         current_account = db.get_by_id(table="Account", id=account.id)
    #         if current_account is not None:
    #             ampay_account = {**current_account, **account}
    #             db.insert_or_update_list(table="Account", items=[ampay_account])
    #             await publish_message(topic="ampay.Account.updated", message=ampay_account)
    #     create_task(update_account(account=account))
    # elif event.get('type') == 'charge.succeeded':
    if event.get('type') == 'charge.succeeded':
        # Payment was successful, try to start a charging session

        payment_intent: str = event.get('data').get('object').get('payment_intent')
        if payment_intent is None:
            raise HTTPException(status_code=404, detail="No payment intent found in event")
        
        db_checkout = db.query(CheckoutModel).filter(CheckoutModel.payment_intent_id == payment_intent).first()
        if db_checkout is None:
            raise HTTPException(status_code=404, detail="No checkout found for payment intent")
        
        ocpp_integration: OcppIntegration = request.app.ocpp_integration
        db_checkout.remote_request_status: RequestStartStopStatusEnumType = \
            await ocpp_integration.request_remote_start(
                checkout_id = db_checkout.id
            )
        db.add(db_checkout)
        db.commit()
        db.refresh(db_checkout)
        
        return None
    if event.get('type') == 'checkout.session.completed':
        # A Stripe Checkout session completed
        checkout_session = event.get('data').get('object')
        paymentIntentId = checkout_session.get("payment_intent")
        metadata = checkout_session.get('metadata')
        checkoutId = metadata.get("checkoutId")
        stationId = metadata.get("stationId")
        transactionId = metadata.get("transactionId")
        
        ocpp_integration: OcppIntegration = request.app.ocpp_integration
        
        if (paymentIntentId and checkoutId and not transactionId):
            handle_web_portal(db, ocpp_integration, paymentIntentId, checkoutId)
        elif (paymentIntentId and checkoutId and stationId and transactionId):
            handle_scan_and_charge(db, ocpp_integration, paymentIntentId, checkoutId, stationId, transactionId)
        else:
            raise HTTPException(status_code=404, detail="Metadata missing")
        

    return

async def handle_web_portal(db: Session, ocpp_integration: OcppIntegration, paymentIntentId: str, checkoutId: str):
    # Payment was successful, try to start a charging session
    
    db_checkout = db.query(CheckoutModel).filter(CheckoutModel.id == checkoutId).first()
    if db_checkout is None:
        raise HTTPException(status_code=404, detail="No checkout found for payment intent")
    
    db_checkout.payment_intent_id = paymentIntentId
    
    db_checkout.remote_request_status: RequestStartStopStatusEnumType = \
        await ocpp_integration.request_remote_start(
            checkout_id = db_checkout.id
        )
    db.add(db_checkout)
    db.commit()
    db.refresh(db_checkout)

async def handle_scan_and_charge(db: Session, ocpp_integration: OcppIntegration, paymentIntentId: str, checkoutId: str, stationId: str, transactionId: str):
    debug(' [Stripe] stationId: %r, transactionId: %r, checkoutId: %r, paymentIntentId: %r', stationId, transactionId, checkoutId, paymentIntentId)
    
    ocppTransaction = db.query(Transaction) \
        .filter(Transaction.stationId == stationId, 
                Transaction.transactionId == transactionId) \
        .first()
    if ocppTransaction is None:
        debug(" [Stripe] No transaction found for checkout session")
        cancel_payment_intent(paymentIntentId)
        raise HTTPException(status_code=404, detail="No transaction found for checkout session")
    if ocppTransaction.isActive is False:
        debug(" [Stripe] Transaction is not active")
        cancel_payment_intent(paymentIntentId)
        raise HTTPException(status_code=404, detail="Transaction is not active")
    
    authorization = await ocpp_integration.create_authorization(
        transaction_id = transactionId,
        payment_intent_id = paymentIntentId
    )
    if authorization is None:
        debug(" [Stripe] Unable to create authorization for transaction")
        cancel_payment_intent(paymentIntentId)
        raise HTTPException(status_code=404, detail="Unable to create authorization for transaction")
    
    
    idToken = authorization['idToken']
    request_body = {
        "remoteStartId": checkoutId,
        "idToken": idToken
    }
    
    if ocppTransaction.evse is not None:
        request_body["evseId"] = ocppTransaction.evse.id
        
    debug(" [Stripe] remote start request: %r", json.dumps(request_body))
    
    db_evse = db.query(Evse).filter(Evse.station_id == stationId).first()
    citrineos_module = "evdriver" # TODO set up programatic way to resolve module from action
    action = "requestStartTransaction"
    response = ocpp_integration.send_citrineos_message(station_id=stationId, tenant_id=db_evse.tenant_id, url_path=f"{citrineos_module}/{action}", json_payload=request_body)
    remote_start_stop = RequestStartStopStatusEnumType.REJECTED
    if response.status_code == 200:
        if response.json().get("success") == True:
            remote_start_stop = RequestStartStopStatusEnumType.ACCEPTED
    db.query(CheckoutModel).filter(CheckoutModel.id == checkoutId).update({CheckoutModel.remote_request_status: remote_start_stop})
    db.commit()

def cancel_payment_intent(paymentIntendId: str):
    try:
        stripe.PaymentIntent.cancel(paymentIntendId)
    except Exception as e:
        exception(" [Stripe] Error while canceling payment intent: %r", e.__str__())
