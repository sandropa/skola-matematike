from fastapi import HTTPException
from sqlalchemy.orm import Session
from server.models.user import User
from server.services.auth import create_access_token
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

def login_google_user(id_token_str: str, db: Session):
    try:
        id_info = google_id_token.verify_oauth2_token(id_token_str, google_requests.Request())
        email = id_info.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="Email nije pronađen u Google tokenu.")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Korisnik sa ovim emailom ne postoji.")

      
        token = create_access_token(data={"sub": user.email})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "role": user.role
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Nevažeći Google token.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Pogrešan email.")
