from pydantic import BaseModel, Field
from typing import Optional

class ScheduleEntryBase(BaseModel):
    cycle: str
    row: int
    group: str
    date: Optional[str] = None
    topic: Optional[str] = None
    lecturer: Optional[str] = None
    comments: Optional[str] = None
    problemset_id: Optional[int] = None

class ScheduleEntryCreate(ScheduleEntryBase):
    pass

class ScheduleEntryUpdate(BaseModel):
    date: Optional[str] = None
    topic: Optional[str] = None
    lecturer: Optional[str] = None
    comments: Optional[str] = None
    problemset_id: Optional[int] = None

class ScheduleEntrySchema(ScheduleEntryBase):
    id: int
    class Config:
        orm_mode = True 