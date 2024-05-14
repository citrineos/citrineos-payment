from datetime import datetime
from enum import Enum
from pydantic import BaseModel


class TransactionEventEnumType(str, Enum):
    Ended = "Ended"
    Started = "Started"
    Updated = "Updated"


class TriggerReasonEnumType(str, Enum):
    Authorized = "Authorized"
    CablePluggedIn = "CablePluggedIn"
    ChargingRateChanged = "ChargingRateChanged"
    ChargingStateChanged = "ChargingStateChanged"
    Deauthorized = "Deauthorized"
    EnergyLimitReached = "EnergyLimitReached"
    EVCommunicationLost = "EVCommunicationLost"
    EVConnectTimeout = "EVConnectTimeout"
    MeterValueClock = "MeterValueClock"
    MeterValuePeriodic = "MeterValuePeriodic"
    TimeLimitReached = "TimeLimitReached"
    Trigger = "Trigger"
    UnlockCommand = "UnlockCommand"
    StopAuthorized = "StopAuthorized"
    EVDeparted = "EVDeparted"
    EVDetected = "EVDetected"
    RemoteStop = "RemoteStop"
    RemoteStart = "RemoteStart"
    AbnormalCondition = "AbnormalCondition"
    SignedDataReceived = "SignedDataReceived"
    ResetCommand = "ResetCommand"


class TransactionType(BaseModel):
    transactionId: str    
    remoteStartId: int 


class MeasurandEnumType(str, Enum):
    CurrentExport = "Current.Export"
    CurrentImport = "Current.Import"
    CurrentOffered = "Current.Offered"
    EnergyActiveExportRegister = "Energy.Active.Export.Register"
    EnergyActiveImportRegister = "Energy.Active.Import.Register"
    EnergyReactiveExportRegister = "Energy.Reactive.Export.Register"
    EnergyReactiveImportRegister = "Energy.Reactive.Import.Register"
    EnergyActiveExportInterval = "Energy.Active.Export.Interval"
    EnergyActiveImportInterval = "Energy.Active.Import.Interval"
    EnergyActiveNet = "Energy.Active.Net"
    EnergyReactiveExportInterval = "Energy.Reactive.Export.Interval"
    EnergyReactiveImportInterval = "Energy.Reactive.Import.Interval"
    EnergyReactiveNet = "Energy.Reactive.Net"
    EnergyApparentNet = "Energy.Apparent.Net"
    EnergyApparentImport = "Energy.Apparent.Import"
    EnergyApparentExport = "Energy.Apparent.Export"
    Frequency = "Frequency"
    PowerActiveExport = "Power.Active.Export"
    PowerActiveImport = "Power.Active.Import"
    PowerFactor = "Power.Factor"
    PowerOffered = "Power.Offered"
    PowerReactiveExport = "Power.Reactive.Export"
    PowerReactiveImport = "Power.Reactive.Import"
    SoC = "SoC"
    Voltage = "Voltage"
    

class PhaseEnumType(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    N = "N"
    L1N = "L1-N"
    L2N = "L2-N"
    L3N = "L3-N"
    L1L2 = "L1-L2"
    L2L3 = "L2-L3" 
    L3L1 = "L3-L1"

class UnitOfMeasureType(BaseModel):
    unit: str | None = "Wh"
    multiplier: float | None = 0


class SampledValueType(BaseModel):
    value: float
    measurand: MeasurandEnumType | None = MeasurandEnumType.EnergyActiveImportRegister
    phase: PhaseEnumType | None = None
    unitOfMeasure: UnitOfMeasureType | None = None


class MeterValueType(BaseModel):
    sampledValue: list[SampledValueType]


class TransactionEventRequest(BaseModel):
    eventType: TransactionEventEnumType
    timestamp: datetime
    triggerReason: TriggerReasonEnumType
    transactionInfo: TransactionType
    meterValue: list[MeterValueType] | None = None
