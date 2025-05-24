# server/schemas/user.py
from pydantic import BaseModel, EmailStr,Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    surname: str

    class Config:
        orm_mode = True

class InviteRequest(BaseModel):
    to_email: str
    name: str
    
    surname: str
class CompleteInviteRequest(BaseModel):
    password: str = Field(min_length=6)