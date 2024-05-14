from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, computed_field


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
    payment_costs_tax_rate: int = 0     # Used for tax reverse charge scenarios
    
    @computed_field
    @property
    def total_costs_net(self) -> int:
        result = 0
        if self.energy_costs is not None:
            result += self.energy_costs
        if self.time_costs is not None:
            result += self.time_costs
        if self.session_costs is not None:
            result += self.session_costs
        return result
    @computed_field
    @property
    def tax_costs(self) -> int:
        return int(self.total_costs_net * self.tax_rate / 100)
    @computed_field
    @property
    def total_costs_gross(self) -> int:
        return int(self.total_costs_net + self.tax_costs)
    @computed_field
    @property
    def payment_costs_gross(self) -> int:
        return int(self.total_costs_net * (1 + self.payment_costs_tax_rate / 100) * self.payment_fee / 100)
    @computed_field
    @property
    def payment_costs_net(self) -> int:
        return int(self.total_costs_net * self.payment_fee / 100)


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
    