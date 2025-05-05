# tests/backend/conftest.py

# --- Add these lines at the top ---
import sys
import os

# Calculate the project root directory (which is two levels up from this file)
# os.path.dirname(__file__) -> tests/backend
# os.path.join(..., '..') -> tests/
# os.path.join(..., '..', '..') -> skola-matematike/ (project root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Add the project root to the Python path if it's not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End of added lines ---

# Now the rest of your imports should work
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from server.main import app # This import should now succeed
from server.database import Base, get_db
from server.models import problem, problemset, problemset_problems # Ensure models are imported

# --- Test Database Setup ---
# (Keep the rest of the file as it was)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()