from enum import Enum
from io import BytesIO
import json
from typing import List, Tuple
from uuid import uuid4
from aio_pika import connect
from aio_pika.abc import AbstractExchange, AbstractIncomingMessage
from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_core import ValidationError
import requests
from sqlalchemy.orm import Session
import stripe
import qrcode

from config import Config
from logging import debug, exception, info, warning
from db.init_db import MessageInfo as MessageInfoModel, get_db, Checkout as CheckoutModel, Connector as ConnectorModel, Evse as EvseModel, Location as LocationModel, Tariff as TariffModel

from integrations.integration import FileIntegration, OcppIntegration
from schemas.checkouts import RequestStartStopStatusEnumType
from schemas.status_notification import StatusNotificationRequest
from schemas.transaction_event import MeasurandEnumType, TransactionEventEnumType, TriggerReasonEnumType, TransactionEventRequest


class CitrineOsEventAction(str, Enum):
    TRANSACTIONEVENT = "TransactionEvent"
    STATUSNOTIFICATION = "StatusNotification"


class CitrineOSevent(BaseModel):
    action: CitrineOsEventAction
    payload: dict

class CitrineOSeventHeaders(BaseModel):
    stationId: str 


class CitrineOSIntegration(OcppIntegration):
    def __init__(self, fileIntegration: FileIntegration):
        self.fileIntegration = fileIntegration

    async def create_authorization(self, idToken: str, idTokenType: str, additionalInfo: List[Tuple[str, str]], app: FastAPI = None,):
        idToken = {
            "idToken": idToken,
            "type": idTokenType,
            "additionalInfo": [
                {"additionalIdToken": item[0], "type": item[1]}
            for item in additionalInfo]
        }
        request_body = {
            "idToken": idToken,
            "idTokenInfo": {
                "status": "Accepted",
            }
        }
        module = "evdriver"
        data = "authorization"
        url_path = f"{module}/{data}"
        request_url = \
            f"{Config.CITRINEOS_DATA_API_URL}/{url_path}" \
            f"?idToken={idToken['idToken']}" \
            f"&type={idToken['type']}"
        
        response = requests.put(request_url, json=request_body)
        if response.status_code == 200:
            return request_body
        exception(" [CitrineOS] Error while creating authorization: %r", response)
        return
    

    def send_citrineos_message(self, station_id: str, tenant_id: str, url_path: str, json_payload: str) -> requests.Response:
        request_url = \
            f"{Config.CITRINEOS_MESSAGE_API_URL}/{url_path}" \
            f"?identifier={station_id}" \
            f"&tenantId={tenant_id}"
        
        return requests.post(request_url, json=json_payload)


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
                citrine_os_event_headers = CitrineOSeventHeaders(**event_message.headers)
                transaction_event = TransactionEventRequest(**citrine_os_event.payload)
                if transaction_event.eventType == TransactionEventEnumType.Started or transaction_event.triggerReason == TriggerReasonEnumType.RemoteStart:
                    await self.process_transaction_started(
                        transaction_event=transaction_event, 
                        citrine_os_event_headers=citrine_os_event_headers
                    )
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
        

    async def process_transaction_started(self, transaction_event: TransactionEventRequest, citrine_os_event_headers: CitrineOSeventHeaders) -> None:
        triggerReasonNoAuthArray = [TriggerReasonEnumType.CablePluggedIn, TriggerReasonEnumType.SignedDataReceived, TriggerReasonEnumType.EVDetected]
        if (Config.CITRINEOS_SCAN_AND_CHARGE and transaction_event.triggerReason in triggerReasonNoAuthArray and transaction_event.idToken is None):
            await self.process_transaction_started_scan_and_charge(
                transaction_event=transaction_event,
                citrine_os_event_headers=citrine_os_event_headers
            )
        else:
            await self.process_transaction_started_remote(transaction_event=transaction_event)


    async def process_transaction_started_scan_and_charge(self, transaction_event: TransactionEventRequest, citrine_os_event_headers: CitrineOSeventHeaders) -> None:
        transactionId = transaction_event.transactionInfo.transactionId
        stationId = citrine_os_event_headers.stationId
        
        db: Session = next(get_db())
        # If pricing is found to vary by evse, we need to change triggerReasonNoAuthArray to mandate events that know the evse
        # Then add a filter below, EvseModel.ocpp_evse_id == transaction_event.evse.id
        evse = db.query(EvseModel).filter(EvseModel.station_id == stationId).first()
        if evse is None:
            raise Exception("EVSE not found")
        
        tariff = db.query(TariffModel).filter(TariffModel.id == evse.connectors[0].tariff_id).first()
        if tariff is None:
            raise Exception("No Tariff for EVSE found")

        location = db.query(LocationModel).filter(LocationModel.id == evse.location_id).first()
        if location is None:
            raise Exception("No Location for EVSE found")

        db_checkout = CheckoutModel(
            connector_id=evse.connectors[0].id,
            tariff_id=tariff.id
        )
        db_checkout = self.update_checkout_with_meter_values(transaction_event=transaction_event, db_checkout=db_checkout)
        db.add(db_checkout)
        db.commit()
        db.refresh(db_checkout)
        
        if tariff.stripe_price_id is None:
            price = stripe.Price.create(
                currency= tariff.currency.lower(),
                metadata= { "tariffId": tariff.id },
                product_data= {"name": "Charging Session Authorization Amount"},
                tax_behavior= "inclusive",
                unit_amount= int(tariff.authorization_amount * 100),
            )
            tariff.stripe_price_id = price.id
            db.add(tariff)
            db.commit()
        
        payment_link_url =await self.create_payment_link(
            stripe_price_id=tariff.stripe_price_id, 
            stripe_account_id=location.operator.stripe_account_id, 
            stationId=stationId,
            evseId=evse.evse_id,
            transactionId=transactionId,
            checkoutId=db_checkout.id
        )
        
        qr_code_img = qrcode.make(payment_link_url)
        # Save the image to an in-memory buffer
        buffer = BytesIO()
        debug(type(qr_code_img))
        debug(dir(qr_code_img))
        qr_code_img.save(buffer)
        buffer.seek(0) # Rewind the buffer to the beginning
        
        qr_code_img_url = self.fileIntegration.upload_file(buffer, "image/png", f"qrcode_{stationId}_{transactionId}.png", f"QRCode_{stationId}_{transactionId}")
        
        mostRecentMessageInfoForStation = db \
            .query(MessageInfoModel) \
            .filter(MessageInfoModel.stationId == stationId) \
            .order_by(MessageInfoModel.id.desc()).first()
        nextMessageId = 0 if mostRecentMessageInfoForStation is None else mostRecentMessageInfoForStation.id + 1
        set_display_message_request = {
            "message": {
                "id": nextMessageId,
                "priority": "AlwaysFront",
                "transactionId": transactionId,
                "message": {
                    "format": "URI",
                    "content": qr_code_img_url
                }
            }
        }
        citrineos_module = "configuration" # TODO set up programatic way to resolve module from action
        action = "setDisplayMessage"
        
        self.send_citrineos_message(station_id=stationId, tenant_id=evse.tenant_id, url_path=f"{citrineos_module}/{action}", json_payload=set_display_message_request)
        db_checkout.qr_code_message_id = nextMessageId
        db.add(db_checkout)
        db.commit()
        
      
    async def create_payment_link(self, stripe_price_id: str, stripe_account_id: str, stationId: str, evseId: str, transactionId: str, checkoutId: int) -> str:
        transactionPaymentLink = stripe.PaymentLink.create(
            after_completion = {
                "redirect": {
                    "url": f"{Config.CLIENT_URL}/charging/{evseId}/{checkoutId}"
                },
                "type": "redirect"
            },
            line_items=[{
                "price": stripe_price_id,
                "quantity": 1,
            }],
            metadata = {
                "stationId": stationId,
                "transactionId": transactionId,
                "checkoutId": checkoutId
            },
            payment_intent_data={
                "capture_method": "manual",
            },
            payment_method_types=['card'],
            restrictions={
                "completed_sessions": { "limit": int(1) }
            },
            stripe_account=stripe_account_id,
        )
        return transactionPaymentLink.url
        
        
    async def process_transaction_started_remote(self, transaction_event: TransactionEventRequest) -> None:    
        db: Session = next(get_db())
        db_checkout = db.query(CheckoutModel) \
            .filter(CheckoutModel.id == transaction_event.transactionInfo.remoteStartId) \
            .first()
        if db_checkout is None:
            info(" [CitrineOS] Checkout not found for transaction start event: %r", transaction_event)
            return
        
        db_checkout.transaction_start_time = transaction_event.timestamp
        db_checkout.remote_request_transaction_id = transaction_event.transactionInfo.transactionId
        db_checkout = self.update_checkout_with_meter_values(transaction_event=transaction_event, db_checkout=db_checkout)
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
                        if db_checkout.transaction_last_meter_reading is None:
                            db_checkout.transaction_kwh = 0
                        if db_checkout.transaction_last_meter_reading is not None:
                            db_checkout.transaction_kwh += new_kwh_value - db_checkout.transaction_last_meter_reading
                        db_checkout.transaction_last_meter_reading = new_kwh_value

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
    