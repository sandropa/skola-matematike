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

from ..schemas.problem_schema import ProblemSchema as Task
from ..services import task_service

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


@router.get("/", response_model=List[Task])
def all_tasks(db: Session = Depends(get_db)):
  
    return task_service.get_all(db)

@router.get("/{task_id}", response_model=Task)
def get_task(task_id: int, db: Session = Depends(get_db)):
  
    task = task_service.get_one(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/", response_model=Task, status_code=201)
def create_task(task: Task, db: Session = Depends(get_db)):
   
    return task_service.create(db, task)

@router.put("/{task_id}", response_model=Task)
def update_task(task_id: int, new_task: Task, db: Session = Depends(get_db)):
  
    task = task_service.update(db, task_id, new_task)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
  
    success = task_service.delete(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

