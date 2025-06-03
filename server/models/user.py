# server/models/user.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    profile_image = Column(String, nullable=True)
    role = Column(String, default="user")



    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
