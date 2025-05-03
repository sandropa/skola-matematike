# server/schemas/problemset.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime # Keep if ORM model still has datetime fields

# Import the schema for the link object
from .problemset_problems import ProblemsetProblemsSchema

# Keep the AI Output schema if still needed elsewhere
class LectureProblemsOutput(BaseModel):
    lecture_name: str
    group_name: str
    problems_latex: List[str]


class ProblemsetSchema(BaseModel):
    """Pydantic schema for representing a Problemset object in API responses."""
    id: int
    # --- Adjust fields to match the Problemset ORM model ---
    title: str      # Use the fields from your current ORM model
    type: str       # Use the fields from your current ORM model
    part_of: str    # Use the fields from your current ORM model
    # REMOVE or ADD fields here to EXACTLY match the Problemset ORM model attributes
    # name: str         # REMOVE if not in ORM model
    # group_name: str   # REMOVE if not in ORM model
    # created_at: datetime # REMOVE if not in ORM model

    # Relationship using the Association Object Schema
    problems: List[ProblemsetProblemsSchema] = [] # List of LINK objects

    # Config for ORM mode
    class Config:
        orm_mode = True
    # model_config = ConfigDict(from_attributes=True) # Pydantic v2