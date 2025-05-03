'''
API routes for problem management.
'''

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from ..database import get_db
from ..models.problem import Problem as DBProblem # The SQLAlchemy model

from ..schemas.problem import ProblemSchema as Problem
from ..services import problem_service


# Create an API router instance
router = APIRouter(
    prefix="/problems",
    tags=["Problems"],
)

@router.get("/", response_model=List[Problem])
def all_problems(db: Session = Depends(get_db)):
    return problem_service.get_all(db)

# todo (old code before refactoring):
# @router.get("/{problem_id}", response_model=Problem)
# def get_problem(problem_id: int, db: Session = Depends(get_db)):
#     problem = problem_service.get_one(db, problem_id)
#     if not problem:
#         raise HTTPException(status_code=404, detail="Problem not found")
#     return problem

# @router.post("/", response_model=Problem, status_code=201)
# def create_problem(problem: Problem, db: Session = Depends(get_db)):
#     return problem_service.create(db, problem)

# @router.put("/{problem_id}", response_model=Problem)
# def update_problem(problem_id: int, new_problem: Problem, db: Session = Depends(get_db)):
#     problem = problem_service.update(db, problem_id, new_problem)
#     if not problem:
#         raise HTTPException(status_code=404, detail="Problem not found")
#     return problem

# @router.delete("/{problem_id}", status_code=204)
# def delete_problem(problem_id: int, db: Session = Depends(get_db)):
#     success = problem_service.delete(db, problem_id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Problem not found")
#     return {"message": "Problem deleted successfully"}

