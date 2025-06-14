from fastapi import HTTPException
from sqlalchemy.orm import Session
from server.models.user import User
from server.models.invite import Invite
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
import logging

logger = logging.getLogger(__name__)

def accept_invite_with_google(invite_id: int, id_token: str, db: Session):
    try:
    
        id_info = google_id_token.verify_oauth2_token(id_token, google_requests.Request())

        email = id_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google token does not contain an email.")

        invite = db.query(Invite).filter(Invite.id == invite_id).first()
        if not invite:
            raise HTTPException(status_code=404, detail="Invite not found")

      
        if invite.email != email:
            raise HTTPException(status_code=400, detail="Email from Google does not match the invite")

       
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

      
        new_user = User(
            email=email,
            name=invite.name,
            surname=invite.surname,
            password=None,
            role=invite.role or "user"
        )

        db.add(new_user)
        db.delete(invite)
        db.commit()

        return {"message": "Google registration successful"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")
    except Exception as e:
        logger.error(f"Error during Google invite acceptance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Server error during Google invite acceptance")
