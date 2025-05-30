from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class ProgramTypeEnum(enum.Enum):
    SKOLA_MATEMATIKE = "skola matematike"
    LJETNI_KAMP = "ljetni kamp"
    ZIMSKI_KAMP = "zimski kamp"

class ProblemsetStatusEnum(enum.Enum):
    DRAFT = "DRAFT"
    FINALIZED = "FINALIZED"

class Problemset(Base):
    __tablename__ = "problemsets"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)
    part_of = Column(String, nullable=False)

    group_name = Column(String)
    
    # New fields
    raw_latex = Column(Text, nullable=True)  # Store the raw LaTeX text
    status = Column(Enum(ProblemsetStatusEnum), nullable=False, default=ProblemsetStatusEnum.DRAFT)
    
    # Relationships
    problems = relationship("ProblemsetProblems", back_populates="problemset")

    def __repr__(self):
         return f"<Problemset(id={self.id}, title='{self.title}', type='{self.type}', part_of='{self.part_of}', status='{self.status}')>"