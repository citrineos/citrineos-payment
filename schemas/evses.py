from enum import Enum
from pydantic import BaseModel, ConfigDict

from schemas.connectors import Connector

class EvseStatus(str, Enum):
    Available = "Available"
    Occupied = "Occupied"
    Reserved = "Reserved"
    Unavailable = "Unavailable"
    Faulted = "Faulted"


class Evse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evse_id: str
    ocpp_evse_id: int
    status: EvseStatus
    location_id: int
    connectors: list[Connector] = []
    
