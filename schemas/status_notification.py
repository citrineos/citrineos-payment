from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class ConnectorStatusEnumType(str, Enum):
    Available = "Available"
    Occupied = "Occupied"
    Reserved = "Reserved"
    Unavailable = "Unavailable"
    Faulted = "Faulted"


class StatusNotificationRequest(BaseModel):
    timestamp: datetime
    connectorId: int
    evseId: int
    connectorStatus: ConnectorStatusEnumType
