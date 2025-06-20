from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services import tag_service
from ..schemas.tag_schema import TagCreate, TagOut
from typing import List

router = APIRouter(prefix="/tags", tags=["tags"])

@router.post("/", response_model=TagOut)
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    return tag_service.create_tag(db, tag)

@router.get("/", response_model=List[TagOut])
def get_tags(db: Session = Depends(get_db)):
    return tag_service.get_all_tags(db)

@router.delete("/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag_service.delete_tag(db, tag_id)
    return {"message": "Tag uspješno obrisan"}