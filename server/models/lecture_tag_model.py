from sqlalchemy import Column, ForeignKey
from ..database import Base

class LectureTag(Base):
    __tablename__ = "lecture_tags"

    lecture_id = Column(ForeignKey("problemsets.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
