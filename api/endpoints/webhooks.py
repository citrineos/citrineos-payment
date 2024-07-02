import json
from uuid import uuid4
import stripe
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from logging import debug, exception
from json import loads
from sqlalchemy.orm import Session

from config import Config
from db.init_db import Connector, Evse, Transaction, get_db, Checkout as CheckoutModel
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
    connect_event_types = ["checkout.session.completed"]
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
    if event.get('type') == 'checkout.session.completed':
        # A Stripe Checkout session completed
        # Payment was successful, try to start a charging session
        checkout_session = event.get('data').get('object')
        paymentIntentId = checkout_session.get("payment_intent")
        metadata = checkout_session.get('metadata')
        checkoutId = metadata.get("checkoutId")
        stationId = metadata.get("stationId")
        transactionId = metadata.get("transactionId")
        debug(' [Stripe] stationId: %r, transactionId: %r, checkoutId: %r, paymentIntentId: %r', stationId, transactionId, checkoutId, paymentIntentId)
        
        ocpp_integration: OcppIntegration = request.app.ocpp_integration
        
        if (paymentIntentId and checkoutId and not transactionId):
            await handle_web_portal(db, ocpp_integration, paymentIntentId, checkoutId)
        elif (paymentIntentId and checkoutId and stationId and transactionId):
            await handle_scan_and_charge(db, ocpp_integration, paymentIntentId, checkoutId, stationId, transactionId)
        else:
            raise HTTPException(status_code=404, detail="Metadata missing")
        

    return

async def handle_web_portal(db: Session, ocpp_integration: OcppIntegration, paymentIntentId: str, checkoutId: str):
    db_checkout = db.query(CheckoutModel).filter(CheckoutModel.id == checkoutId).first()
    if db_checkout is None:
        raise HTTPException(status_code=404, detail="No checkout found for payment intent")
    
    db_checkout.payment_intent_id = paymentIntentId
    db.add(db_checkout)
    db.commit()
    
    # TODO: Remove this part when CitrineOS is correctly saving the idToken from RemoteStartRequests.
    authorization = await ocpp_integration.create_authorization(
        f"{Config.OCPP_REMOTESTART_IDTAG_PREFIX}{db_checkout.id}",
        "Central",
        [
            (paymentIntentId, "PaymentIntentId"),
        ]
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
    
    db_connector = db.query(Connector).filter(Connector.id == db_checkout.connector_id).first()
    if db_connector is None:
        debug(" [CitrineOS] Connector not found for remote start request: %r", db_checkout.id)
        return RequestStartStopStatusEnumType.REJECTED
    
    db_evse = db.query(Evse).filter(Evse.id == db_connector.evse_id).first()
    if db_evse is None:
        debug(" [CitrineOS] EVSE not found for remote start request: %r", db_checkout.id)
        return RequestStartStopStatusEnumType.REJECTED
    
    request_body["evseId"] = db_evse.ocpp_evse_id
        
    debug(" [Stripe] remote start request: %r", json.dumps(request_body))
    
    citrineos_module = "evdriver" # TODO set up programatic way to resolve module from action
    action = "requestStartTransaction"
    response = ocpp_integration.send_citrineos_message(station_id=db_evse.station_id, tenant_id=db_evse.tenant_id, url_path=f"{citrineos_module}/{action}", json_payload=request_body)
    remote_start_stop = RequestStartStopStatusEnumType.REJECTED
    if response.status_code == 200:
        if response.json().get("success") == True:
            remote_start_stop = RequestStartStopStatusEnumType.ACCEPTED
    db_checkout = db.query(CheckoutModel).filter(CheckoutModel.id == checkoutId).first()
    db_checkout.remote_request_status = remote_start_stop

    db.add(db_checkout)
    db.commit()
    debug(' [Stripe] paymentIntentId: %r, checkoutId: %r, requestStartStatus: %r', db_checkout.payment_intent_id, db_checkout.id, db_checkout.remote_request_status)

async def handle_scan_and_charge(db: Session, ocpp_integration: OcppIntegration, paymentIntentId: str, checkoutId: str, stationId: str, transactionId: str):
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
        str(uuid4()),
        "Central",
        [
            (transactionId, "TransactionId"),
            (paymentIntentId, "PaymentIntentId"),
        ]
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
    db_checkout = db.query(CheckoutModel).filter(CheckoutModel.id == checkoutId).first()
    db_checkout.remote_request_status = remote_start_stop
    db_checkout.payment_intent_id = paymentIntentId
    db.add(db_checkout)
    db.commit()
    
    citrineos_module = "configuration" # TODO set up programatic way to resolve module from action
    action = "clearDisplayMessage"
    ocpp_integration.send_citrineos_message(
        station_id=stationId, 
        tenant_id=db_evse.tenant_id, 
        url_path=f"{citrineos_module}/{action}", 
        json_payload={ "id" : db_checkout.qr_code_message_id }
    )
    

def cancel_payment_intent(paymentIntendId: str):
    try:
        stripe.PaymentIntent.cancel(paymentIntendId)
    except Exception as e:
        exception(" [Stripe] Error while canceling payment intent: %r", e.__str__())
