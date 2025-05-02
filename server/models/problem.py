from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from ..database import Base # Import Base from database.py
import enum

class CategoryEnum(enum.Enum):
    A = "A"  # Algebra
    N = "N"  # Number theory
    G = "G"  # Geometry
    C = "C"  # Combinatorics

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    latex_text = Column(Text, nullable=False)
    comments = Column(Text, nullable=True)
    latex_versions = Column(ARRAY(Text), nullable=True)  # Array of text for multiple versions
    solution = Column(Text, nullable=True)
    category = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Define relationship placeholder (will link via Lecture model)
    problemsets = relationship(
        "ProblemsetProblems",
        back_populates="problem"
    )

    def __repr__(self):
         return f"<Problem(id={self.id}, latex='{self.latex_text[:30]}...')>"