from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProblemSchema(BaseModel):
    """Pydantic schema for representing a Problem object in API responses."""
    id: int
    latex_text: str
    comments: Optional[str] = None
    latex_versions: Optional[List[str]] = None
    solution: Optional[str] = None
    category: str

    class Config:
        orm_mode = True
