from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base

class ProblemsetProblems(Base):
    __tablename__ = "problemset_problems"
    
    id_problem = Column(Integer, ForeignKey("problems.id"), primary_key=True)
    id_problemset = Column(Integer, ForeignKey("problemsets.id"), primary_key=True)
    
    # Relationships
    problem = relationship("Problem", back_populates="problemsets")
    problemset = relationship("Problemset", back_populates="problems") 