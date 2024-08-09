from enum import Enum
from pydantic import BaseModel, ConfigDict


class ConnectorPowerType(str, Enum):
    AC_1_PHASE = "AC_1_PHASE"
    AC_3_PHASE = "AC_3_PHASE"
    DC = "DC"


class Connector(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    connector_id: str
    power_type: ConnectorPowerType
    max_voltage: int
    max_amperage: int
    tariff_id: int | None
