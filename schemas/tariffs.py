from pydantic import BaseModel, ConfigDict

class TariffBase(BaseModel):
    id: int
    price_kwh: float | None
    price_minute: float | None
    price_session: float | None
    currency: str
    tax_rate: float
    authorization_amount: float
    # Add other fields as needed

class TariffCreate(TariffBase):
    pass

class Tariff(TariffBase):
    model_config = ConfigDict(from_attributes=True)
    