# server/models/lecture.py
from sqlalchemy import Column, Integer, String, DateTime, func, Table, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base # Import Base

# Define the association table that links Lectures and Problems
lecture_problems_association = Table(
    'lecture_problems_association', Base.metadata,
    Column('lecture_id', Integer, ForeignKey('lectures.id'), primary_key=True),
    Column('problem_id', Integer, ForeignKey('problems.id'), primary_key=True)
)

class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False) # Name of the lecture
    group_name = Column(String(100), index=True, nullable=False) # Target student group
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Define relationship to Problem model via the association table
    problems = relationship(
        "Problem",
        secondary=lecture_problems_association,
        back_populates="lectures"
    )

    def __repr__(self):
         return f"<Lecture(id={self.id}, name='{self.name}', group='{self.group_name}')>"