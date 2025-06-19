from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import lecture_tag_service
from typing import List

router = APIRouter(prefix="/lecture-tags", tags=["lecture-tags"])

@router.patch("/{lecture_id}")
def update_lecture_tags(lecture_id: int, tags: List[str], db: Session = Depends(get_db)):
    return lecture_tag_service.update_tags_for_lecture(db, lecture_id, tags)



@router.get("/{lecture_id}", response_model=list[str])
def get_lecture_tags(lecture_id: int, db: Session = Depends(get_db)):
    return lecture_tag_service.get_tags_for_lecture(db, lecture_id)