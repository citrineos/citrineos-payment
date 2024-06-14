from datetime import datetime
import stripe
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.init_db import get_db, \
Evse as EvseModel, \
Tariff as TariffModel, \
Location as LocationModel, \
Checkout as CheckoutModel

from schemas.checkouts import Checkout, CheckoutCreate ,CheckoutCreateResponse, Pricing
from utils.utils import generate_pricing

router = APIRouter()

@router.post("/", response_model=CheckoutCreateResponse)
def create_checkout(request_body: CheckoutCreate, db: Session = Depends(get_db)):
    evse = db.query(EvseModel).filter(EvseModel.evse_id == request_body.evse_id).first()
    if evse is None:
        raise HTTPException(status_code=404, detail="EVSE not found")
    
    tariff = db.query(TariffModel).filter(TariffModel.id == evse.connectors[0].tariff_id).first()
    if tariff is None:
        raise HTTPException(status_code=404, detail="No Tariff for EVSE found")

    location = db.query(LocationModel).filter(LocationModel.id == evse.location_id).first()
    if location is None:
        raise HTTPException(status_code=404, detail="No Location for EVSE found")

    db_checkout = CheckoutModel(
        connector_id=evse.connectors[0].id,
        tariff_id=tariff.id
    )
    db.add(db_checkout)
    db.commit()
    db.refresh(db_checkout)

    checkout = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                "price_data": {
                    "currency": tariff.currency.lower(),
                    "product_data": {"name": "Charging Session Authorization Amount"},
                    "unit_amount": int(tariff.authorization_amount * 100),
                    "tax_behavior": "inclusive",
                },
                "quantity": 1,
            },
        ],
        metadata= {
            "checkoutId": db_checkout.id
        },
        payment_intent_data={"capture_method": "manual",},
        stripe_account=location.operator.stripe_account_id,
        mode='payment',
        success_url=f"{request_body.success_url}/{db_checkout.id}",
        cancel_url=request_body.cancel_url,
    )
    db_checkout.payment_intent_id = checkout.payment_intent
    db.add(db_checkout)
    db.commit()
    db.refresh(db_checkout)

    return CheckoutCreateResponse(
        id=db_checkout.id, 
        url=checkout.url,
    )


@router.get("/{id}", response_model=Checkout)
def get_checkout(id: int, db: Session = Depends(get_db)):
    db_checkout = db.query(CheckoutModel).filter(CheckoutModel.id == id).first()
    if db_checkout is None:
        raise HTTPException(status_code=404, detail="charging.error.sessionnotfound")
    
    output_checkout = Checkout(**{
        **db_checkout.__dict__, 
        "pricing": generate_pricing(db_checkout.id)
    })

    return output_checkout
