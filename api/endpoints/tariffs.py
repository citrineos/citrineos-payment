from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.init_db import get_db, Tariff as TariffModel

from schemas.tariffs import Tariff

router = APIRouter()

@router.get("/{id}", response_model=Tariff)
def get_tariff(id: int, db: Session = Depends(get_db)):
    db_location = db.query(TariffModel).filter(TariffModel.id == id).first()
    if db_location is None:
        raise HTTPException(status_code=404, detail="Tariff not found")
    return db_location
