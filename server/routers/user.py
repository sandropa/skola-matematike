import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from server.schemas.user import UserCreate, UserLogin, UserOut, UserPersonalUpdate, PasswordUpdate, InviteRequest,PasswordResetConfirm, PasswordResetRequest
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
from server.models.password_reset import PasswordReset
import secrets
from datetime import datetime, timezone, timedelta
import shutil
import os
from uuid import uuid4
from server.schemas.user import GoogleCompleteInviteRequest
from server.services.invite_google_service import accept_invite_with_google

from fastapi import UploadFile, File, Depends, HTTPException
from server.schemas.user import GoogleLoginRequest
from server.services.auth_google_service import login_google_user
from server.schemas.user import SetPasswordRequest
from server.services.user import set_user_password
from server.services import email_service
from server.services import image_service
from server.services import profile_service
from server.services.user import get_password_hash


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
    return {"access_token": token, "token_type": "bearer", "user_id": user.id, "role": user.role}

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
    if hasattr(user_update, "password") and user_update.password:
        raise HTTPException(status_code=400, detail="Password cannot be updated here.")

    return profile_service.update_name_and_surname(
        db=db,
        user_id=user_id,
        name=user_update.name,
        surname=user_update.surname
    )


@router.put("/{user_id}/password", summary="Change user's password")
def update_password(user_id: int, payload: PasswordUpdate, db: Session = Depends(get_db)):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")

    profile_service.update_user_password(
        db=db,
        user_id=user_id,
        current_password=payload.current_password,
        new_password=payload.new_password
    )

    return {"message": "Password updated successfully"}




@router.post("/send-invite")
def send_invite(invite: InviteRequest, db: Session = Depends(get_db)):
    if invite.role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    new_invite = Invite(
        email=invite.to_email,
        name=invite.name,
        surname=invite.surname,
        role=invite.role  
    )
    db.add(new_invite)
    db.commit()
    db.refresh(new_invite)

    email_service.send_invite_email(invite.to_email, new_invite.id)


    return {"message": f"Invitation sent and saved for {invite.to_email}"}



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
        password=hash_password(request.password),
        role=invite.role or "user" 
    )

    db.add(new_user)
    db.delete(invite)
    db.commit()
    return {"message": "Registracija uspešna!"}


@router.put("/{user_id}/role")
def update_user_role(user_id: int, payload: dict, db: Session = Depends(get_db)):
    new_role = payload.get("role")
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = new_role
    db.commit()
    return {"message": "Uloga uspješno promijenjena"}



    
@router.post("/password-reset-request")
def request_password_reset(data: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik ne postoji")

    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)

    reset = PasswordReset(user_id=user.id, token=token, expires_at=expires)
    db.add(reset)
    db.commit()

    link = f"http://localhost:5173/reset-password?token={token}"
    email_service.send_reset_email(user.email, link)

    return {"message": "Email sa linkom za reset je poslan."}

@router.post("/password-reset-confirm")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    reset = db.query(PasswordReset).filter(PasswordReset.token == data.token).first()

    if not reset or reset.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Neispravan ili istekao token")

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    user.password = hash_password(data.new_password)
    db.delete(reset)
    db.commit()

    return {"message": "Lozinka je uspješno resetovana."}



@router.post("/{user_id}/upload-photo", summary="Upload profile image")
def upload_profile_image(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    image_url = image_service.save_profile_image(db, user_id, file)
    return {"message": "Slika uspješno uploadovana", "image_path": image_url}


@router.delete("/{user_id}/delete-photo", summary="Delete profile image")
def delete_profile_image(user_id: int, db: Session = Depends(get_db)):
    image_service.delete_profile_image(db, user_id)
    return {"message": "Profilna slika je obrisana"}


@router.post("/accept-invite/google/{invite_id}")
def accept_invite_google(invite_id: int, payload: GoogleCompleteInviteRequest, db: Session = Depends(get_db)):
    return accept_invite_with_google(invite_id, payload.id_token, db)
@router.post("/login/google")
def login_with_google(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    return login_google_user(payload.id_token, db)

@router.post("/{user_id}/set-password")
def set_password(user_id: int, payload: SetPasswordRequest, db: Session = Depends(get_db)):
    return set_user_password(
        db=db,
        user_id=user_id,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password
    )
