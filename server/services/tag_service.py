from sqlalchemy.orm import Session
from ..models.tag_model import Tag
from ..models.lecture_tag_model import LectureTag
from ..schemas.tag_schema import TagCreate

def create_tag(db: Session, tag_data: TagCreate) -> Tag:
    tag = Tag(name=tag_data.name, color=tag_data.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

def get_all_tags(db: Session):
    return db.query(Tag).all()
