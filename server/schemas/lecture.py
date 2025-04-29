# server/schemas/lecture.py

from pydantic import BaseModel, Field
from typing import Optional, List # Need List for problems
from datetime import datetime
from pydantic import ConfigDict # For Pydantic v2

# Import the Pydantic schema for Problem from the same schemas directory
from .problem import ProblemSchema


# --- Pydantic Model matching AI Output JSON Structure ---
# This represents the data *received directly from the AI*
class LectureProblemsOutput(BaseModel):
    """Pydantic model for the raw JSON output structure from the AI."""
    lecture_name: str = Field(..., description="The main title or name of the lecture topic found in the document.")
    group_name: str = Field(..., description="The target group for the lecture (e.g., 'Početna grupa', 'Srednja grupa', 'Napredna grupa', 'Predolimpijska grupa', 'Olimpijska grupa').")
    problems_latex: List[str] = Field(..., description="A list containing the extracted LaTeX source string for each distinct problem identified in the document.")


class LectureSchema(BaseModel):
    """Pydantic schema for representing a Lecture object in API responses."""
    id: int # Assuming ID is returned from DB
    name: str
    group_name: str
    created_at: datetime
    # Include the problems relationship, represented as a list of ProblemSchema
    problems: List[ProblemSchema] = [] # Default to empty list if no problems

    # Pydantic v1 compatibility
    class Config:
        orm_mode = True

    # Pydantic v2 configuration (alternative to Config)
    # model_config = ConfigDict(from_attributes=True)