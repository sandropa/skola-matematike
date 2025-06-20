from pydantic import BaseModel
from typing import List



class TagCreate(BaseModel):
    name: str
    color: str



class TagOut(BaseModel):
    id: int
    name: str
    color: str

    class Config:
        orm_mode = True
