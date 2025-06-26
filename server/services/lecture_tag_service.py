from sqlalchemy.orm import Session
from ..models.tag_model import Tag
from ..models.lecture_tag_model import LectureTag
from ..models.problemset import Problemset

def update_tags_for_lecture(db: Session, lecture_id: int, tag_names: list[str]):
    lecture = db.query(Problemset).filter(Problemset.id == lecture_id).first()
    if not lecture:
        raise Exception("Predavanje ne postoji")

    db.query(LectureTag).filter(LectureTag.lecture_id == lecture_id).delete()

    for tag_name in tag_names:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.commit()
            db.refresh(tag)

        db.add(LectureTag(lecture_id=lecture_id, tag_id=tag.id))

    db.commit()
    return {"message": "Tagovi ažurirani"}

def get_tags_for_lecture(db: Session, lecture_id: int) -> list[str]:
    results = (
        db.query(Tag.name)
        .join(LectureTag, LectureTag.tag_id == Tag.id)
        .filter(LectureTag.lecture_id == lecture_id)
        .all()
    )
    return [r[0] for r in results]  
