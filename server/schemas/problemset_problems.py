# server/schemas/problemset_problems.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

# Import the schema for the nested Problem object
from .problem import ProblemSchema

class ProblemsetProblemsSchema(BaseModel):
    """Pydantic schema representing the link between a Problemset and a Problem."""
    # --- ADD position ---
    position: int
    # Add other fields if needed (e.g., problem_version_key)

    # Include the nested Problem details
    problem: ProblemSchema

    # Config for ORM mode
    class Config:
        orm_mode = True
    # model_config = ConfigDict(from_attributes=True) # Pydantic v2