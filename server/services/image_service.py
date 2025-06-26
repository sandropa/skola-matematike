import os
import shutil
from uuid import uuid4
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from server.models.user import User

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_profile_image(db: Session, user_id: int, file: UploadFile):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    filename = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Obriši staru sliku ako postoji
    if user.profile_image:
        old_path = user.profile_image.lstrip("/")
        if os.path.exists(old_path):
            os.remove(old_path)

    user.profile_image = f"/{UPLOAD_DIR}/{filename}"
    db.commit()

    return user.profile_image

def delete_profile_image(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Korisnik nije pronađen")

    if user.profile_image:
        image_path = user.profile_image.lstrip("/")
        if os.path.exists(image_path):
            os.remove(image_path)
        user.profile_image = None
        db.commit()

    return True
