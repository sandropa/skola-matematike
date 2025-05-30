import sys
from pathlib import Path

# Add the 'server' directory to the Python path
project_root = Path(__file__).resolve().parent
server_dir = project_root / 'server'
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from server.database import SessionLocal, engine, Base
from server.models.problemset import Problemset
from server.models.problem import Problem
from server.models.problemset_problems import ProblemsetProblems
from server.models.user import User

def recreate_tables():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables recreated successfully!")

if __name__ == "__main__":
    recreate_tables() 