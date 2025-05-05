# server/models/problem.py

# --- Make sure ARRAY and Text are imported from sqlalchemy ---
from sqlalchemy import Column, Integer, String, Text, JSON
# --- (Keep other imports like relationship, Base, enum) ---
from sqlalchemy.orm import relationship
from ..database import Base
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
    # --- Ensure this definition is exactly ARRAY(Text) ---
    latex_versions = Column(JSON, nullable=True)
    # -------------------------------------------------------
    solution = Column(Text, nullable=True)
    category = Column(String, nullable=False) # Keep as String, potentially add Enum here later if needed

    problemsets = relationship(
        "ProblemsetProblems",
        back_populates="problem"
    )

    def __repr__(self):
         return f"<Problem(id={self.id}, latex='{self.latex_text[:30]}...')>"
    