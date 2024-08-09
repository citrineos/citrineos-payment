from pydantic import BaseModel, ConfigDict

from schemas.operators import Operator


class LocationBase(BaseModel):
    id: int
    location_id: str
    address: str | None
    postal_code: str | None
    city: str | None
    state: str | None
    country: str | None
    operator: Operator


class LocationCreate(LocationBase):
    pass


class Location(LocationBase):
    model_config = ConfigDict(from_attributes=True)
