from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict


class RequestStartStopStatusEnumType(str, Enum):
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"


class CheckoutBase(BaseModel):
    id: int


class CheckoutCreate(BaseModel):
    evse_id: str
    success_url: str
    cancel_url: str


class CheckoutCreateResponse(CheckoutBase):
    url: str


class Pricing(BaseModel):
    currency: str
    tax_rate: int
    payment_fee: int
    energy_consumption_kwh: float | None = None
    energy_costs: int | None = None
    time_consumption_min: float | None = None
    time_costs: int | None = None
    session_consumption: int | None = None
    session_costs: int | None = None
    payment_costs_tax_rate: int = 0  # Used for tax reverse charge scenarios
    total_costs_net: int = 0
    tax_costs: int = 0
    total_costs_gross: int = 0
    payment_costs_gross: int = 0
    payment_costs_net: int = 0


class Checkout(CheckoutBase):
    model_config = ConfigDict(from_attributes=True)

    payment_intent_id: str
    connector_id: int
    tariff_id: int
    remote_request_status: RequestStartStopStatusEnumType | None
    remote_request_transaction_id: str | None
    transaction_start_time: datetime | None
    transaction_end_time: datetime | None
    transaction_kwh: float | None
    power_active_import: float | None
    transaction_soc: float | None
    pricing: Pricing | None
