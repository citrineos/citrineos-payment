from logging import error
from sqlalchemy.orm import Session

from db.init_db import Checkout, Tariff, get_db
from model.transaction_summary import TransactionSummary
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

    transaction_summary = TransactionSummary(
        start_time=db_checkout.transaction_start_time,
        end_time=db_checkout.transaction_end_time,
        kwh=db_checkout.transaction_kwh,
        currency=db_tariff.currency,
        price_minute=db_tariff.price_minute,
        price_session=db_tariff.price_session,
        price_kwh=db_tariff.price_kwh,
        tax_rate=db_tariff.tax_rate,
        payment_fee=db_tariff.payment_fee,
    )

    return Pricing(
        currency=transaction_summary.currency,
        tax_rate=transaction_summary.tax_rate,
        payment_fee=transaction_summary.payment_fee,
        energy_consumption_kwh=transaction_summary.kwh,
        energy_costs=transaction_summary.energy_costs.get_amount_in_sub_unit()
        if transaction_summary.energy_costs is not None
        else None,
        time_consumption_min=transaction_summary.time_consumption_min,
        time_costs=transaction_summary.time_costs.get_amount_in_sub_unit()
        if transaction_summary.time_costs is not None
        else None,
        session_consumption=1,
        session_costs=transaction_summary.session_costs.get_amount_in_sub_unit()
        if transaction_summary.session_costs is not None
        else None,
        payment_costs_tax_rate=0,
        total_costs_net=transaction_summary.total_costs_net.get_amount_in_sub_unit(),
        tax_costs=transaction_summary.tax_costs.get_amount_in_sub_unit(),
        total_costs_gross=transaction_summary.total_costs_gross.get_amount_in_sub_unit(),
        payment_costs_gross=transaction_summary.payment_costs_gross.get_amount_in_sub_unit(),
        payment_costs_net=transaction_summary.payment_costs_net.get_amount_in_sub_unit(),
    )
