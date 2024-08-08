from datetime import datetime, timezone
from logging import error
from sqlalchemy.orm import Session

from db.init_db import Checkout, Tariff, get_db
from schemas.checkouts import Pricing


def generate_pricing(
    checkout_id: int,
) -> Pricing:
    db: Session = next(get_db())
    db_checkout = db.query(Checkout).filter(Checkout.id == checkout_id).first()
    if db_checkout is None:
        error(
            f" [utils] generate_pricing ERROR - Could not find Checkout: {checkout_id}"
        )
        return None

    db_tariff = db.query(Tariff).filter(Tariff.id == db_checkout.tariff_id).first()
    if db_tariff is None:
        error(
            f" [utils] generate_pricing ERROR - Could not find Tariff: {db_checkout.tariff_id}"
        )
        return None

    session_time_min = 0
    if db_checkout.transaction_start_time is not None:
        session_end_time = (
            db_checkout.transaction_end_time
            if db_checkout.transaction_end_time is not None
            else datetime.now(timezone.utc)
        )
        session_time_min = (
            session_end_time - db_checkout.transaction_start_time
        ).total_seconds() / 60
    pricing = Pricing(
        currency=db_tariff.currency,
        tax_rate=db_tariff.tax_rate,
        payment_fee=db_tariff.payment_fee,
        energy_consumption_kwh=db_checkout.transaction_kwh,
        energy_costs=int((db_checkout.transaction_kwh * db_tariff.price_kwh * 100))
        if db_checkout.transaction_kwh is not None and db_tariff.price_kwh is not None
        else None,
        time_consumption_min=session_time_min,
        time_costs=int((session_time_min * db_tariff.price_minute * 100))
        if session_time_min is not None and db_tariff.price_minute is not None
        else None,
        session_consumption=1,
        session_costs=int((db_tariff.price_session * 100))
        if db_tariff.price_session is not None
        else None,
        payment_costs_tax_rate=0,  # currently 0. needed for reverse charge scenarios
    )
    return pricing
