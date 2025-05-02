from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from .problem import ProblemSchema


# --- Pydantic Model matching AI Output JSON Structure ---
# This represents the data *received directly from the AI*
class LectureProblemsOutput(BaseModel):
    """Pydantic model for the raw JSON output structure from the AI."""
    title: str = Field(..., description="The title of the problemset.")
    type: str = Field(..., description="The type of the problemset.")
    part_of: str = Field(..., description="What program this is part of (e.g., 'skola matematike', 'ljetni kamp', 'zimski kamp').")
    problems_latex: List[str] = Field(..., description="A list containing the extracted LaTeX source string for each distinct problem identified in the document.")


class ProblemsetSchema(BaseModel):
    """Pydantic schema for representing a Problemset object in API responses."""
    id: int 
    title: str
    type: str
    part_of: str

    problems: List[ProblemSchema] = []

    class Config:
        orm_mode = True