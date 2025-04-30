# server/routes/lecture_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from ..database import get_db
from ..models.lecture import Lecture as DBLecture
from ..schemas.lecture_schema import LectureSchema as Lecture
from ..services import lecture_service

# --- Minimal Input Model (Inline) for quick test ---
class TempLectureInput(BaseModel):
    name: str
    group_name: str

# Create an API router instance
router = APIRouter(
    prefix="/lectures",
    tags=["Lectures"],
)

@router.post("/quick-insert/", status_code=status.HTTP_201_CREATED)
async def quick_create_lecture(
    lecture_input: TempLectureInput,
    db: Session = Depends(get_db)
):
    """
    Quick test endpoint to insert a lecture into the database.
    """
    db_lecture = DBLecture(
        name=lecture_input.name,
        group_name=lecture_input.group_name
    )
    try:
        db.add(db_lecture)
        db.commit()
        db.refresh(db_lecture)
        return {
            "message": "Lecture created successfully!",
            "lecture_id": db_lecture.id,
            "name": db_lecture.name,
            "group_name": db_lecture.group_name,
            "created_at": db_lecture.created_at.isoformat()
        }
    except Exception as e:
        db.rollback()
        print(f"Error creating lecture: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )

@router.get("/", response_model=List[Lecture])
def all_lectures(db: Session = Depends(get_db)):
    return lecture_service.get_all(db)

@router.get("/{lecture_id}", response_model=Lecture)
def get_lecture(lecture_id: int, db: Session = Depends(get_db)):
    lecture = lecture_service.get_one(db, lecture_id)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    return lecture

@router.post("/", response_model=Lecture, status_code=201)
def create_lecture(lecture: Lecture, db: Session = Depends(get_db)):
    return lecture_service.create(db, lecture)

@router.put("/{lecture_id}", response_model=Lecture)
def update_lecture(lecture_id: int, new_lecture: Lecture, db: Session = Depends(get_db)):
    lecture = lecture_service.update(db, lecture_id, new_lecture)
    if not lecture:
        raise HTTPException(status_code=404, detail="Lecture not found")
    return lecture

@router.delete("/{lecture_id}", status_code=204)
def delete_lecture(lecture_id: int, db: Session = Depends(get_db)):
    success = lecture_service.delete(db, lecture_id)
    if not success:
        raise HTTPException(status_code=404, detail="Lecture not found")
    return {"message": "Lecture deleted successfully"}
