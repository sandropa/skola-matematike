import logging
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from ..models.user import User as DBUser
from ..schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(DBUser).filter(DBUser.email == email).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

def create(db: Session, user: UserCreate) -> DBUser:
    logger.info("Service: Creating new user.")
    hashed_pw = get_password_hash(user.password)
    db_user = DBUser(
        email=user.email,
        password=hashed_pw,
        name=user.name,
        surname=user.surname
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Service: Successfully created user with id {db_user.id}")
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: DB error during user creation: {e}", exc_info=True)
        raise


def get_all(db: Session):
    logger.info("Service: Fetching all users.")
    return db.query(DBUser).all()

def get_one(db: Session, user_id: int):
    logger.info(f"Service: Fetching user with id {user_id}.")
    return db.query(DBUser).filter(DBUser.id == user_id).first()

def delete(db: Session, user_id: int) -> bool:
    logger.info(f"Service: Attempting to delete user with id {user_id}.")
    db_user = get_one(db, user_id)
    if not db_user:
        logger.warning(f"Service: User with id {user_id} not found for deletion.")
        return False
    try:
        db.delete(db_user)
        db.commit()
        logger.info(f"Service: Successfully deleted user with id {user_id}.")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: DB error during deletion: {e}", exc_info=True)
        raise

def update_name_surname(db: Session, user_id: int, name: str, surname: str) -> DBUser | None:
    logger.info(f"Service: Updating name and surname for user with id {user_id}")
    db_user = get_one(db, user_id)
    if not db_user:
        logger.warning(f"Service: User with id {user_id} not found for name update.")
        return None

    try:
        db_user.name = name
        db_user.surname = surname
        db.commit()
        db.refresh(db_user)
        logger.info(f"Service: Successfully updated name and surname for user {user_id}")
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: DB error during name update of user {user_id}: {e}", exc_info=True)
        raise

def update_password(db: Session, user_id: int, current_password: str, new_password: str) -> bool:
    logger.info(f"Service: Attempting to update password for user with id {user_id}")
    db_user = get_one(db, user_id)
    if not db_user:
        logger.warning(f"Service: User with id {user_id} not found for password update.")
        return False

    if not verify_password(current_password, db_user.password):
        logger.warning(f"Service: Incorrect current password for user {user_id}")
        return False

    try:
        db_user.password = get_password_hash(new_password)
        db.commit()
        logger.info(f"Service: Successfully updated password for user {user_id}")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: DB error during password update of user {user_id}: {e}", exc_info=True)
        raise
