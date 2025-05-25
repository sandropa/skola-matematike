import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from server.schemas.user import UserCreate, UserLogin, UserOut, UserPersonalUpdate, PasswordUpdate, InviteRequest
from server.services.auth import create_access_token
from server.services import user as user_service
from server.models.user import User
from server.models.invite import Invite
from server.dependencies import get_db
import smtplib
from fastapi import HTTPException
from email.message import EmailMessage
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from server.schemas.user import CompleteInviteRequest




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
    return {"access_token": token, "token_type": "bearer", "user_id": user.id}

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

@router.put("/{user_id}", response_model=UserOut, summary="Update user's name and surname")
def update_user(user_id: int, user_update: UserPersonalUpdate, db: Session = Depends(get_db)):
    logger.info(f"Router: Request received for PUT /users/{user_id}")

    # Dozvoljene izmjene samo za name i surname
    if hasattr(user_update, "password") and user_update.password:
        raise HTTPException(status_code=400, detail="Password cannot be updated here.")

    try:
        updated_user = user_service.update_name_surname(db, user_id, user_update.name, user_update.surname)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except SQLAlchemyError as e:
        logger.error(f"Router: DB error during user update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during update")
    except Exception as e:
        logger.error(f"Router: Unexpected error during user update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error during update")


@router.put("/{user_id}/password", summary="Change user's password")
def update_password(user_id: int, payload: PasswordUpdate, db: Session = Depends(get_db)):
    logger.info(f"Router: Request received for PUT /users/{user_id}/password")

    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")

    try:
        success = user_service.update_password(
            db=db,
            user_id=user_id,
            current_password=payload.current_password,
            new_password=payload.new_password
        )
        if not success:
            raise HTTPException(status_code=403, detail="Current password is incorrect or user not found.")
        return {"message": "Password updated successfully"}
    except SQLAlchemyError as e:
        logger.error(f"Router: DB error during password update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database error during password update")
    except Exception as e:
        logger.error(f"Router: Unexpected error during password update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected error during password update")

EMAIL_ADDRESS = "hrmenager2025@gmail.com"
EMAIL_PASSWORD = "fczv gsef gqyy oydb"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587

def send_email(to_email: str, invite_id: str):
    msg = EmailMessage()
    msg['Subject'] = "Invite za kreiranje predavačkog profila na Školi matematike"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(f"Pozdrav, Pozvani ste da se registrujete kao predavač na platformi Škola Matematike. Kliknite na link ispod da biste kreirali svoj nalog:, http://127.0.0.1:8000/users/accept-invite/{invite_id}")

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("SMTP ERROR:", str(e))  # ili logger.error(...)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/send-invite")
def send_invite(invite: InviteRequest, db: Session = Depends(get_db)):
   
    new_invite = Invite(
        email=invite.to_email,
        name=invite.name,
        surname=invite.surname
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)

    send_email(invite.to_email, new_invite.id)

    return {"message": f"Invitation sent and saved for {invite.to_email}"}


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

@router.post("/accept-invite/{invite_id}")
def accept_invite(invite_id: int, request: CompleteInviteRequest, db: Session = Depends(get_db)):
    invite = db.query(Invite).filter(Invite.id == invite_id).first()

    if not invite:
        raise HTTPException(status_code=404, detail="Pozivnica ne postoji")

    existing_user = db.query(User).filter(User.email == invite.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Korisnik sa ovom email adresom već postoji")

    new_user = User(
        email=invite.email,
        name=invite.name,
        surname=invite.surname,
        password=hash_password(request.password)
    )

    db.add(new_user)
    db.commit()

    return {"message": "Registracija uspešna!"}
