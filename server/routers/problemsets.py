'''
API routes for problemset management.
'''

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import logging

from ..database import get_db
from ..models.problemset import Problemset as DBProblemset

from ..schemas.problemset import ProblemsetSchema as Problemset
from ..schemas.problemset import LectureProblemsOutput
from ..services.problemset_service import ProblemsetService, ProblemsetServiceError

logger = logging.getLogger(__name__)

# Create service instance
problemset_service = ProblemsetService()

# Create an API router instance
router = APIRouter(
    prefix="/problemsets",
    tags=["Problemsets"],
)

@router.get("/", response_model=List[Problemset])
def all_problemsets(db: Session = Depends(get_db)):
    logger.info("Fetching all problemsets from DB.")
    problemsets_orm = db.query(DBProblemset).all()
    logger.info(f"Fetched {len(problemsets_orm)} problemsets.")
    return problemsets_orm

# @router.get("/{problemset_id}", response_model=Problemset)
# def get_problemset(problemset_id: int, db: Session = Depends(get_db)):
#     problemset = db.query(DBProblemset).filter(DBProblemset.id == problemset_id).first()
#     if not problemset:
#         raise HTTPException(status_code=404, detail="Problemset not found")
#     return problemset

# @router.post("/", response_model=Problemset, status_code=201)
# def create_problemset_with_problems(problemset_data: LectureProblemsOutput, db: Session = Depends(get_db)):
#     try:
#         db_problemset = problemset_service.create_problemset_and_problems(db, problemset_data)
#         return db_problemset
#     except ProblemsetServiceError as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/{problemset_id}", status_code=204)
# def delete_problemset(problemset_id: int, db: Session = Depends(get_db)):
#     problemset = db.query(DBProblemset).filter(DBProblemset.id == problemset_id).first()
#     if not problemset:
#         raise HTTPException(status_code=404, detail="Problemset not found")
    
#     db.delete(problemset)
#     db.commit()
#     return {"message": "Problemset deleted successfully"} 