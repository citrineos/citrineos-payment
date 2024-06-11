import stripe
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from logging import debug
from json import loads
from sqlalchemy.orm import Session

from config import Config
from db.init_db import get_db, Checkout as CheckoutModel
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
    connect_event_types = ["account.updated", "charge.succeeded",]
    try:
        event_type = loads(body.decode()).get('type')
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

    return
