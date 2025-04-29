# server/schemas/problem.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict # For Pydantic v2, use ConfigDict

class ProblemSchema(BaseModel):
    """Pydantic schema for representing a Problem object in API responses."""
    id: int # Assuming ID is returned from DB
    latex_content: str
    image_filename: Optional[str] = None
    created_at: datetime

    # Pydantic v1 compatibility
    class Config:
        orm_mode = True # Allows Pydantic to read from SQLAlchemy ORM models

    # Pydantic v2 configuration (alternative to Config)
    # model_config = ConfigDict(from_attributes=True)