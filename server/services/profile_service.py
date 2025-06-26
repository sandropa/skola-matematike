from fastapi import HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from server.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def update_name_and_surname(db: Session, user_id: int, name: str, surname: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = name
    user.surname = surname
    db.commit()
    db.refresh(user)
    return user


def update_user_password(db: Session, user_id: int, current_password: str, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(current_password, user.password):
        raise HTTPException(status_code=403, detail="Current password is incorrect.")

    user.password = hash_password(new_password)
    db.commit()
