from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from .problem import ProblemSchema


# --- Pydantic Model matching AI Output JSON Structure ---
# This represents the data *received directly from the AI*
class LectureProblemsOutput(BaseModel):
    """Pydantic model for the raw JSON output structure from the AI."""
    lecture_name: str = Field(..., description="The main title or name of the lecture topic found in the document.")
    group_name: str = Field(..., description="The target group for the lecture (e.g., 'Početna grupa', 'Srednja grupa', 'Napredna grupa', 'Predolimpijska grupa', 'Olimpijska grupa').")
    problems_latex: List[str] = Field(..., description="A list containing the extracted LaTeX source string for each distinct problem identified in the document.")


class ProblemsetSchema(BaseModel):
    """Pydantic schema for representing a Lecture object in API responses."""
    id: int 
    name: str
    group_name: str
    created_at: datetime
    type: str = Field(..., description="One of: predavanje, samostalan_rad, test, shortlist.")

    problems: List[ProblemSchema] = []

    class Config:
        orm_mode = True