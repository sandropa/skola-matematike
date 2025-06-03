# server/schemas/user.py
from pydantic import BaseModel, EmailStr,Field
from pydantic import BaseModel, EmailStr
from typing import Optional


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

class UserPersonalUpdate(BaseModel):
    name: str
    surname: str

class PasswordUpdate(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    surname: str
    profile_image: Optional[str] = None
    role: str

    class Config:
        orm_mode = True

class InviteRequest(BaseModel):
    to_email: str
    name: str
    surname: str
    role: str = "user"
class CompleteInviteRequest(BaseModel):
    password: str = Field(min_length=6)

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str