from enum import Enum
import json
from aio_pika import connect
from aio_pika.abc import AbstractExchange, AbstractIncomingMessage
from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_core import ValidationError
import requests
from sqlalchemy.orm import Session

from config import Config
from logging import debug, exception, info, warning
from db.init_db import get_db, Checkout as CheckoutModel, Connector as ConnectorModel, Evse as EvseModel

from integrations.integration import Integration
from schemas.checkouts import RequestStartStopStatusEnumType
from schemas.status_notification import StatusNotificationRequest
from schemas.transaction_event import MeasurandEnumType, TransactionEventEnumType, TransactionEventRequest


class CitrineOsEventAction(str, Enum):
    TRANSACTIONEVENT = "TransactionEvent"
    STATUSNOTIFICATION = "StatusNotification"


class CitrineOSevent(BaseModel):
    action: CitrineOsEventAction
    payload: dict

class CitrineOSeventHeaders(BaseModel):
    stationId: str 


class CitrineOSIntegration(Integration):
    def __init__(self) -> None:
        pass

    async def request_remote_start(self, app: FastAPI = None, checkout_id: int = None,) -> RequestStartStopStatusEnumType:
        db: Session = next(get_db())
        db_checkout = db.query(CheckoutModel).filter(CheckoutModel.id == checkout_id).first()
        if db_checkout is None:
            debug(" [CitrineOS] Checkout not found for remote start request: %r", checkout_id)
            return RequestStartStopStatusEnumType.REJECTED
        
        db_connector = db.query(ConnectorModel).filter(ConnectorModel.id == db_checkout.connector_id).first()
        if db_connector is None:
            debug(" [CitrineOS] Connector not found for remote start request: %r", checkout_id)
            return RequestStartStopStatusEnumType.REJECTED
        
        db_evse = db.query(EvseModel).filter(EvseModel.id == db_connector.evse_id).first()
        if db_evse is None:
            debug(" [CitrineOS] EVSE not found for remote start request: %r", checkout_id)
            return RequestStartStopStatusEnumType.REJECTED
        
        request_url = \
            f"{Config.CITRINEOS_REST_API_REMOTE_START}" \
            f"?identifier={db_evse.station_id}" \
            f"&tenantId={db_evse.tenant_id}"
        request_body = {
            "evseId": db_evse.ocpp_evse_id,
            "remoteStartId": db_checkout.id,
            "idToken": {
                "idToken": f"{Config.OCPP_REMOTESTART_IDTAG_PREFIX}{db_checkout.id}",
                "type": "Central"
            }
        }
        response = requests.post(request_url, json=request_body)
        debug(" [CitrineOS] request_remote_start response: %r", response)
        remote_start_stop = RequestStartStopStatusEnumType.REJECTED
        if response.status_code == 200:
            if response.json().get("success") == True:
                remote_start_stop = RequestStartStopStatusEnumType.ACCEPTED
        return remote_start_stop


    async def receive_events(self, app: FastAPI = None) -> None:
        # Perform connection
        connection = await connect(
            ssl=Config.MESSAGE_BROKER_SSL_ACTIVE,
            host=Config.MESSAGE_BROKER_HOST, 
            port=Config.MESSAGE_BROKER_PORT,
            login=Config.MESSAGE_BROKER_USER,
            password=Config.MESSAGE_BROKER_PASSWORD,
            virtualhost=Config.MESSAGE_BROKER_VHOST,
        )

        # Creating a channel
        channel = await connection.channel()
        exchange: AbstractExchange = await channel.declare_exchange(name=Config.MESSAGE_BROKER_EXCHANGE_NAME, type=Config.MESSAGE_BROKER_EXCHANGE_TYPE)

        # Declaring queue
        queue = await channel.declare_queue(Config.MESSAGE_BROKER_EVENT_CONSUMER_QUEUE_NAME, durable=True)

        # Bind headers
        arguments_list = [
            { 
                "action": "TransactionEvent",
                "state": "1",
                "x-match": "all",
            },
            {
                "action": "StatusNotification",
                "state": "1",
                "x-match": "all",
            }
        ]
        for arguments in arguments_list:
            await queue.bind(
                exchange=exchange,
                routing_key="",
                arguments=arguments,
            )

        info(" [CitrineOS] Awaiting events with keys: %r ", arguments_list.__str__())

        # Start listening the queue with name 'hello'
        async with queue.iterator() as qiterator:
            message: AbstractIncomingMessage
            async for message in qiterator:
                try:
                    async with message.process():   # Processor acknowledges messages implicitly
                        debug(f" [CitrineOS] event_message({message.headers.__str__()})")
                        await self.process_incoming_event(event_message=message, exchange=exchange)
                        debug(" [CitrineOS] Event processed successfully: %r", message.headers.__str__())
                except Exception as e:
                    exception(" [CitrineOS] Processing error for message %r", message)


    async def process_incoming_event(self, event_message: AbstractIncomingMessage, exchange: AbstractExchange) -> None:
        try:
            decoded_body = event_message.body.decode()
            citrine_os_event = CitrineOSevent(**json.loads(decoded_body))

            if(citrine_os_event.action == CitrineOsEventAction.TRANSACTIONEVENT):
                transaction_event = TransactionEventRequest(**citrine_os_event.payload)
                if transaction_event.eventType == TransactionEventEnumType.Started:
                    await self.process_transaction_started(transaction_event=transaction_event, )
                elif transaction_event.eventType == TransactionEventEnumType.Updated:
                    await self.process_transaction_updated(transaction_event=transaction_event, )
                elif transaction_event.eventType == TransactionEventEnumType.Ended:
                    await self.process_transaction_ended(transaction_event=transaction_event, )
                return
            elif(citrine_os_event.action == CitrineOsEventAction.STATUSNOTIFICATION):
                citrine_os_event_headers = CitrineOSeventHeaders(**event_message.headers)
                status_notification = StatusNotificationRequest(**citrine_os_event.payload)
                await self.process_status_notification(
                    status_notification=status_notification, 
                    citrine_os_event_headers=citrine_os_event_headers
                )
        except ValidationError as e:
            if e.title == CitrineOSevent.__name__:
                debug(" [CitrineOS] Received event which is not valid CitrineOS event: %r", e.errors())
            elif e.title == TransactionEventRequest.__name__:
                warning(" [CitrineOS] Received valid TransactionEvent, but fields missing: %r", e.errors())
            else:
                raise e
        except Exception as e:
            exception(" [CitrineOS] Processing error for incoming event: %r", e.__str__)
            raise e
        

    async def process_transaction_started(self, transaction_event: TransactionEventRequest) -> None:
        db: Session = next(get_db())
        db_checkout = db.query(CheckoutModel) \
            .filter(CheckoutModel.id == transaction_event.transactionInfo.remoteStartId) \
            .first()
        if db_checkout is None:
            info(" [CitrineOS] Checkout not found for transaction start event: %r", transaction_event)
            return
        
        db_checkout.transaction_start_time = transaction_event.timestamp
        db_checkout.remote_request_transaction_id = transaction_event.transactionInfo.transactionId
        db.add(db_checkout)
        db.commit()
        db.refresh(db_checkout)
        return
    

    async def process_transaction_updated(self, transaction_event: TransactionEventRequest) -> None:
        db: Session = next(get_db())
        db_checkout = db.query(CheckoutModel) \
            .filter(CheckoutModel.id == transaction_event.transactionInfo.remoteStartId) \
            .first()
        if db_checkout is None:
            info(" [CitrineOS] Checkout not found for transaction update event: %r", transaction_event)
            return
        
        db_checkout = self.update_checkout_with_meter_values(transaction_event=transaction_event, db_checkout=db_checkout)
        db.add(db_checkout)
        db.commit()
        db.refresh(db_checkout)
        return
    

    async def process_transaction_ended(self, transaction_event: TransactionEventRequest) -> None:
        db: Session = next(get_db())
        db_checkout = db.query(CheckoutModel) \
            .filter(CheckoutModel.id == transaction_event.transactionInfo.remoteStartId) \
            .first()
        if db_checkout is None:
            info(" [CitrineOS] Checkout not found for transaction end event: %r", transaction_event)
            return
        
        
        db_checkout = self.update_checkout_with_meter_values(transaction_event=transaction_event, db_checkout=db_checkout)
        db_checkout.transaction_end_time = transaction_event.timestamp
        db.add(db_checkout)
        db.commit()
        db.refresh(db_checkout)

        await self.capture_payment_transaction(app=None, checkout_id=db_checkout.id)

        return
    

    def update_checkout_with_meter_values(self, transaction_event: TransactionEventRequest, db_checkout: CheckoutModel) -> CheckoutModel:
        if transaction_event.meterValue != None and len(transaction_event.meterValue) > 0:
            latest_meter_value = transaction_event \
                .meterValue[len(transaction_event.meterValue) - 1]
            for sampled_value in latest_meter_value.sampledValue:
                if sampled_value.measurand == MeasurandEnumType.EnergyActiveImportRegister and \
                    sampled_value.phase == None:
                        new_kwh_value = sampled_value.value
                        if sampled_value.unitOfMeasure.unit is None or sampled_value.unitOfMeasure.unit == "Wh":
                            new_kwh_value = new_kwh_value / 1000
                        if sampled_value.unitOfMeasure.multiplier is not None:
                            new_kwh_value = new_kwh_value * 10 ** sampled_value.unitOfMeasure.multiplier
                        db_checkout.transaction_kwh = new_kwh_value

                elif sampled_value.measurand == MeasurandEnumType.PowerActiveImport and \
                    sampled_value.phase == None:
                        new_power_value = sampled_value.value
                        if sampled_value.unitOfMeasure.unit is None or sampled_value.unitOfMeasure.unit == "W":
                            new_power_value = new_power_value / 1000
                        if sampled_value.unitOfMeasure.multiplier is not None:
                            new_power_value = new_power_value * 10 ** sampled_value.unitOfMeasure.multiplier
                        db_checkout.power_active_import = new_power_value

                elif sampled_value.measurand == MeasurandEnumType.SoC and \
                    sampled_value.phase == None:
                        new_soc_value = sampled_value.value
                        if sampled_value.unitOfMeasure.multiplier is not None:
                            new_soc_value = new_soc_value * 10 ** sampled_value.unitOfMeasure.multiplier
                        db_checkout.transaction_soc = new_soc_value
        return db_checkout
    
    async def process_status_notification(self, status_notification: StatusNotificationRequest, citrine_os_event_headers: CitrineOSeventHeaders) -> None:
        db: Session = next(get_db())
        db_evse = db.query(EvseModel) \
            .filter(EvseModel.station_id == citrine_os_event_headers.stationId) \
            .filter(EvseModel.ocpp_evse_id == status_notification.evseId) \
            .first()
        if db_evse is None:
            info(" [CitrineOS] EVSE not found for status notification event: %r", status_notification)
            return
        
        db_evse.status = status_notification.connectorStatus
        db.add(db_evse)
        db.commit()
        db.refresh(db_evse)
        return
    