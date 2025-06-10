from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.schedule_entry import ScheduleEntry
from ..schemas import ScheduleEntrySchema, ScheduleEntryCreate, ScheduleEntryUpdate

router = APIRouter(prefix="/schedule", tags=["Schedule"])

@router.get("/", response_model=List[ScheduleEntrySchema])
def get_schedule(db: Session = Depends(get_db)):
    return db.query(ScheduleEntry).all()

@router.post("/", response_model=ScheduleEntrySchema, status_code=status.HTTP_201_CREATED)
def create_entry(entry: ScheduleEntryCreate, db: Session = Depends(get_db)):
    db_entry = ScheduleEntry(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.put("/{entry_id}", response_model=ScheduleEntrySchema)
def update_entry(entry_id: int, entry: ScheduleEntryUpdate, db: Session = Depends(get_db)):
    db_entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Schedule entry not found")
    for key, value in entry.dict(exclude_unset=True).items():
        setattr(db_entry, key, value)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    db_entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id).first()
    if not db_entry:
        raise HTTPException(status_code=404, detail="Schedule entry not found")
    db.delete(db_entry)
    db.commit()
    return None 