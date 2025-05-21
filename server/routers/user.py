import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from server.schemas.user import UserCreate, UserLogin, UserOut, UserUpdate
from server.services.auth import create_access_token
from server.services import user as user_service
from server.models.user import User
from server.dependencies import get_db

from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user_service.create(db, user)

@router.post("/login")
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    user = user_service.authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/", response_model=List[UserOut], summary="Get All Users")
def read_all_users(db: Session = Depends(get_db)):
    logger.info("Router: Request received for GET /users")
    users = user_service.get_all(db)
    return users

@router.get("/{user_id}", response_model=UserOut, summary="Get User by ID")
def read_user(user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Router: Request received for GET /users/{user_id}")
    user = user_service.get_one(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete User")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    logger.info(f"Router: Request received for DELETE /users/{user_id}")
    success = user_service.delete(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return None

@router.put("/{user_id}", response_model=UserOut, summary="Update Existing User")
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    logger.info(f"Router: Request received for PUT /users/{user_id}")
    try:
        updated_user = user_service.update(db, user_id, user_update)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except SQLAlchemyError as e:
        logger.error(f"Router: DB error during user update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during update")
    except Exception as e:
        logger.error(f"Router: Unexpected error during user update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error during update")
