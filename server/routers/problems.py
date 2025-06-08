# server/routers/problems.py

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from ..database import get_db
# Import the new schemas
from ..schemas.problem import ProblemSchema, ProblemCreate, ProblemUpdate, ProblemPartialUpdate
from ..services import problem_service
from ..schemas.problem import ProblemWithLectureSchema  


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/problems",
    tags=["Problems"],
    responses={404: {"description": "Problem not found"}}
)
@router.get("/with-lecture", response_model=List[ProblemWithLectureSchema])
def get_problems_with_lecture(db: Session = Depends(get_db)):
    return problem_service.get_all_with_lecture(db)


# --- GET / remains the same ---
@router.get("/", response_model=List[ProblemSchema], summary="Get All Problems")
def read_all_problems(db: Session = Depends(get_db)):
    logger.info("Router: Request received for GET /problems")
    problems = problem_service.get_all(db)
    logger.info(f"Router: Returning {len(problems)} problems.")
    return problems

# --- GET /{id} remains the same ---
@router.get("/{problem_id}", response_model=ProblemSchema, summary="Get Problem by ID")
def read_problem(problem_id: int, db: Session = Depends(get_db)):
    logger.info(f"Router: Request received for GET /problems/{problem_id}")
    problem = problem_service.get_one(db, problem_id)
    if problem is None:
        logger.warning(f"Router: Problem with id {problem_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
    logger.info(f"Router: Returning problem with id {problem_id}.")
    return problem

# --- POST / uses ProblemCreate for input ---
@router.post("/", response_model=ProblemSchema, status_code=status.HTTP_201_CREATED, summary="Create New Problem")
def create_new_problem(problem: ProblemCreate, db: Session = Depends(get_db)): # <-- Use ProblemCreate
    """Create a new problem entry in the database."""
    logger.info("Router: Request received for POST /problems")
    try:
        # Pass the ProblemCreate schema to the service
        created_problem = problem_service.create(db=db, problem=problem)
        logger.info(f"Router: Problem created successfully with id {created_problem.id}")
        return created_problem
    except SQLAlchemyError as e:
         logger.error(f"Router: Database error during problem creation: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred while creating the problem.")
    except Exception as e:
        logger.error(f"Router: Unexpected error during problem creation: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# --- PUT /{id} uses ProblemUpdate for input ---
@router.put("/{problem_id}", response_model=ProblemSchema, summary="Update Existing Problem")
def update_existing_problem(problem_id: int, problem_update: ProblemUpdate, db: Session = Depends(get_db)): # <-- Use ProblemUpdate
    """Update an existing problem identified by its ID."""
    logger.info(f"Router: Request received for PUT /problems/{problem_id}")
    try:
        # Pass the ProblemUpdate schema to the service
        updated_problem = problem_service.update(db=db, problem_id=problem_id, problem_update=problem_update)
        if updated_problem is None:
            logger.warning(f"Router: Problem with id {problem_id} not found for update.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
        logger.info(f"Router: Problem {problem_id} updated successfully.")
        return updated_problem
    except SQLAlchemyError as e:
         logger.error(f"Router: Database error during problem update (id: {problem_id}): {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred while updating the problem.")
    # --- Specific handling for HTTPException ---
    except HTTPException as http_exc:
        raise http_exc # Re-raise known HTTP exceptions (like 404)
    # --- Catch other exceptions last ---
    except Exception as e:
        logger.error(f"Router: Unexpected error during problem update (id: {problem_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

@router.patch("/{problem_id}", response_model=ProblemSchema, summary="Partially Update Existing Problem")
def patch_existing_problem(
    problem_id: int, 
    problem_update: ProblemPartialUpdate, 
    db: Session = Depends(get_db)):
    '''Partially update an existing problem identified by its ID.'''
    logger.info(f"Router: Request received for PATCH /problems/{problem_id}")
    if not problem_update.model_dump(exclude_unset=True):
        logger.warning(f"Router: PATCH request for problem {problem_id} received with no update data.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data is provided in PATCH request.")

    try:
        updated_problem = problem_service.patch(db=db, problem_id=problem_id, problem_update=problem_update)
        if updated_problem is None:
            logger.warning(f"Router: Problem with id {problem_id} not found for PATCH update.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
        logger.info(f"Router: Problem {problem_id} updated seccessfully (PATCH).")
        return updated_problem
    except SQLAlchemyError as e:
        logger.error(f"Router: Database error during problem update (PATCH) (id: {problem_id}): {e}", exc_info=True)
        raise
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Router: Unexpected error during problem update (PATCH) (id: {problem_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occured.")


# --- DELETE /{id} - Fix exception handling ---
@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete Problem")
def delete_existing_problem(problem_id: int, db: Session = Depends(get_db)):
    """Delete a problem identified by its ID."""
    logger.info(f"Router: Request received for DELETE /problems/{problem_id}")
    try:
        success = problem_service.delete(db=db, problem_id=problem_id)
        if not success:
            logger.warning(f"Router: Problem with id {problem_id} not found for deletion.")
            # Raising 404 here is correct
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
        logger.info(f"Router: Problem {problem_id} deleted successfully.")
        return None
    except SQLAlchemyError as e:
        logger.error(f"Router: Database error during problem deletion (id: {problem_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred while deleting the problem.")
    # --- Specific handling for HTTPException ---
    except HTTPException as http_exc:
        raise http_exc # Re-raise known HTTP exceptions (like the 404 above)
    # --- Catch other exceptions last ---
    except Exception as e:
        logger.error(f"Router: Unexpected error during problem deletion (id: {problem_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")
   


