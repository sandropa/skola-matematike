from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from ..database import Base # Import Base from database.py

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    latex_content = Column(Text, nullable=False)
    image_filename = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Define relationship placeholder (will link via Lecture model)
    problemsets = relationship(
        "Problemset",
        secondary="problemset_problem_association", # Name of association table
        back_populates="problems"
    )

    def __repr__(self):
         return f"<Problem(id={self.id}, latex='{self.latex_content[:30]}...')>"