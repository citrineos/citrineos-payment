
from io import BytesIO
from logging import error, info
from fastapi import FastAPI
import stripe
from sqlalchemy.orm import Session

from db.init_db import get_db, Checkout, Connector, Evse, Location, Operator
from schemas.checkouts import RequestStartStopStatusEnumType
from utils.utils import generate_pricing


class OCPPIntegration:
    def __init__(self) -> None:
        pass

    async def request_remote_start(self, app: FastAPI = None, checkout_id: int = None,) -> RequestStartStopStatusEnumType:
        pass

    async def receive_events(self, app: FastAPI = None) -> None:
        pass


    async def capture_payment_transaction(self, app: FastAPI = None, checkout_id: int = None) -> None:
        '''Capture the payment transaction for the given checkout_id.
        '''
        db: Session = next(get_db())
        db_checkout = db.query(Checkout).filter(Checkout.id == checkout_id).first()
        if db_checkout is None:
            error(f" [integrations] CAPTURE ERROR - Could not find Checkout: {checkout_id}")
            return

        db_operator: Operator = db.query(
                Operator
            ).filter(
                Connector.id == db_checkout.connector_id,
            ).filter(
                Evse.id == Connector.evse_id,
            ).filter(
                Location.id == Evse.location_id,
            ).first()

        pricing = generate_pricing(checkout_id=checkout_id)

        suc_intent = stripe.PaymentIntent.capture(
                intent=db_checkout.payment_intent_id,
                stripe_account=db_operator.stripe_account_id,
                amount_to_capture=pricing.total_costs_gross,
                application_fee_amount=pricing.payment_costs_gross,
        )
        
        if suc_intent.status != 'succeeded':
            error(f"CAPTURE ERROR - Could not capture the costs for Checkout: {db_checkout.id}")
            return
    
        info(f"CAPTURE SUCCESS - Captured the costs for Checkout: {db_checkout.id}")
        return
    
class FileIntegration:
    def __init__(self) -> None:
        pass
    
    """
    Uploads a file to FileIntegration.
    
    Parameters:
        self: FileIntegration - The FileIntegration instance.
        file: BytesIO - The file to upload.
        mime_type: str - The MIME type of the file.
        filename: str - The name of the file.
        filetitle: str - The title of the file.
    
    Returns:
        str - A url to the uploaded file.
    """
    def upload_file(self, file: BytesIO, mime_type: str, filename: str, filetitle: str) -> str:
        pass
