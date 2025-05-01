# server/schemas/problem.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProblemSchema(BaseModel):
    id: int
    latex_content: str
    image_filename: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
