from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.init_db import get_db, Location as LocationModel

from schemas.locations import Location

router = APIRouter()

@router.get("/{id}", response_model=Location)
def get_location(id: int, db: Session = Depends(get_db)):
    db_location = db.query(LocationModel).filter(LocationModel.id == id).first()
    if db_location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return db_location
