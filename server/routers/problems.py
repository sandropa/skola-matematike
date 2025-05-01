'''
This file is currently mostly for testing. 
We can use it to see that we can insert a problem into 
the database using this route
'''

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from ..database import get_db
from ..models.problem import Problem as DBProblem # The SQLAlchemy model

from ..schemas.problem import ProblemSchema as Problem
from ..services import problem_service

# --- Minimal Input Model (Inline) ---
# Define this directly in the router file for this quick test
class TempProblemInput(BaseModel):
    latex_content: str
    image_filename: str | None = None # Use Python 3.10+ union type or Optional[str]

# Create an API router instance
router = APIRouter(
    prefix="/problems",
    tags=["Problems (Quick Test)"],
)

@router.post("/quick-insert/", status_code=status.HTTP_201_CREATED) # Changed path for clarity
async def quick_create_problem(
    problem_input: TempProblemInput, # Use the minimal inline model for input
    db: Session = Depends(get_db)
):
    """
    Quick test endpoint to insert a problem into the database.
    Bypasses detailed schemas for now.
    """
    # Create an instance of the SQLAlchemy model
    db_problem = DBProblem(
        latex_content=problem_input.latex_content,
        image_filename=problem_input.image_filename
    )
    try:
        db.add(db_problem)
        db.commit()
        db.refresh(db_problem)
        # Return a simple dictionary confirmation
        return {
            "message": "Problem created successfully!",
            "problem_id": db_problem.id,
            "latex_content": db_problem.latex_content,
            "created_at": db_problem.created_at.isoformat() # Convert datetime to string
        }
    except Exception as e:
        db.rollback()
        print(f"Error creating problem: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}" # Include error details for debugging (remove in production)
        )


@router.get("/", response_model=List[Problem])
def all_problems(db: Session = Depends(get_db)):
  
    return problem_service.get_all(db)

@router.get("/{problem_id}", response_model=Problem)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
  
    problem = problem_service.get_one(db, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

@router.post("/", response_model=Problem, status_code=201)
def create_problem(problem: Problem, db: Session = Depends(get_db)):
   
    return problem_service.create(db, problem)

@router.put("/{problem_id}", response_model=Problem)
def update_problem(problem_id: int, new_problem: Problem, db: Session = Depends(get_db)):
  
    problem = problem_service.update(db, problem_id, new_problem)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem

@router.delete("/{problem_id}", status_code=204)
def delete_problem(problem_id: int, db: Session = Depends(get_db)):
  
    success = problem_service.delete(db, problem_id)
    if not success:
        raise HTTPException(status_code=404, detail="Problem not found")
    return {"message": "Problem deleted successfully"}

