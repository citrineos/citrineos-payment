from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.init_db import get_db, Evse as EvseModel
from schemas.evses import Evse as EvseSchema

router = APIRouter()


@router.get(
    "/{evse_id}", 
    response_model=EvseSchema
)
async def read_evses(evse_id: str, db: Session = Depends(get_db)):
    evse = db.query(EvseModel).filter(EvseModel.evse_id == evse_id).first()
    if evse is None:
        raise HTTPException(status_code=404, detail="EVSE not found")

    return evse
