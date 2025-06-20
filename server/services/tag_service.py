from sqlalchemy.orm import Session
from ..models.tag_model import Tag
from ..models.lecture_tag_model import LectureTag
from ..schemas.tag_schema import TagCreate
from fastapi import HTTPException
from ..models.problemset import Problemset 
from ..models.lecture_tag_model import LectureTag 

def create_tag(db: Session, tag_data: TagCreate) -> Tag:
    tag = Tag(name=tag_data.name, color=tag_data.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

def get_all_tags(db: Session):
    return db.query(Tag).all()

def delete_tag(db: Session, tag_id: int):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag nije pronađen")
    db.delete(tag)
    db.commit()
    
    
def get_lectures_by_tag(tag_id: int, db: Session):
    return (
        db.query(Problemset)
        .join(LectureTag, Problemset.id == LectureTag.lecture_id)
        .filter(LectureTag.tag_id == tag_id)
        .all()
    )