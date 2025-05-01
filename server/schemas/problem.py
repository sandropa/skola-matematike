from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProblemSchema(BaseModel):
    """Pydantic schema for representing a Problem object in API responses."""
    id: int
    latex_content: str
    created_at: datetime

    class Config:
        orm_mode = True
