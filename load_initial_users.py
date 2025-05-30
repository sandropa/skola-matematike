import sys
from pathlib import Path

# Add the 'server' directory to the Python path
project_root = Path(__file__).resolve().parent
server_dir = project_root / 'server'
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from server.database import SessionLocal, engine, Base
from server.models.user import User
from server.services.user import get_password_hash

# Initial users data
INITIAL_USERS = [
    {
        "email": "amar.koric@skolamatematike.ba",
        "password": "amar123"
    },
    {
        "email": "sandro.paradzik@skolamatematike.ba",
        "password": "sandro123"
    },
    {
        "email": "imana.alibasic@skolamatematike.ba",
        "password": "imana123"
    },
    {
        "email": "adisa.bolic@skolamatematike.ba",
        "password": "adisa123"
    },
    {
        "email": "adi.hujic@skolamatematike.ba",
        "password": "adi123"
    },
    {
        "email": "selma.halilovic@skolamatematike.ba",
        "password": "selma123"
    },
    {
        "email": "dino.dervisevic@skolamatematike.ba",
        "password": "dino123"
    },
    {
        "email": "nina.kadic@skolamatematike.ba",
        "password": "nina123"
    },
    {
        "email": "jasmin.hadzic@skolamatematike.ba",
        "password": "jasmin123"
    },
    {
        "email": "ajla.mujic@skolamatematike.ba",
        "password": "ajla123"
    }
]

def create_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def load_initial_users():
    # First create the tables
    create_tables()
    
    db = SessionLocal()
    try:
        # Check if users already exist
        existing_users = db.query(User).all()
        if existing_users:
            print("Users already exist in the database. Skipping...")
            return

        # Create new users
        for user_data in INITIAL_USERS:
            hashed_password = get_password_hash(user_data["password"])
            db_user = User(
                email=user_data["email"],
                password=hashed_password
            )
            db.add(db_user)
        
        db.commit()
        print("Successfully added initial users to the database!")
        
    except Exception as e:
        print(f"Error adding users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_initial_users() 