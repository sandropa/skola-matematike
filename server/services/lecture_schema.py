# server/services/lecture_service.py
from sqlalchemy.orm import Session
from ..models.lecture import Lecture as DBLecture
from ..schemas.lecture_schema import LectureSchema

def get_all(db: Session):
    return db.query(DBLecture).all()

def get_one(db: Session, lecture_id: int):
    return db.query(DBLecture).filter(DBLecture.id == lecture_id).first()

def create(db: Session, lecture: LectureSchema):
    db_lecture = DBLecture(**lecture.dict())
    db.add(db_lecture)
    db.commit()
    db.refresh(db_lecture)
    return db_lecture

def update(db: Session, lecture_id: int, new_lecture: LectureSchema):
    db_lecture = db.query(DBLecture).filter(DBLecture.id == lecture_id).first()
    if not db_lecture:
        return None

    for key, value in new_lecture.dict().items():
        setattr(db_lecture, key, value)

    db.commit()
    db.refresh(db_lecture)
    return db_lecture

def delete(db: Session, lecture_id: int):
    db_lecture = db.query(DBLecture).filter(DBLecture.id == lecture_id).first()
    if not db_lecture:
        return False

    db.delete(db_lecture)
    db.commit()
    return True
