# server/schemas/lecture.py
from pydantic import BaseModel
from typing import List
from datetime import datetime
from schemas.problem_schema import ProblemSchema

class LectureSchema(BaseModel):
    id: int
    name: str
    group_name: str
    created_at: datetime
    problems: List[ProblemSchema]

    class Config:
        orm_mode = True
