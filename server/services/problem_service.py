import logging
from sqlalchemy.orm import Session
from ..models.problem import Problem as DBProblem 
from ..schemas.problem import ProblemSchema, ProblemCreate, ProblemUpdate, ProblemPartialUpdate

from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def get_all(db: Session):
    '''Retrieve all problems from the database'''
    logger.info("Service: Fetching all problems.")
    return db.query(DBProblem).all()


def get_one(db: Session, problem_id: int):
    '''Retrieve a single problem by its ID.'''
    logger.info(f"Service: Fetching problem with id {problem_id}.")
    return db.query(DBProblem).filter(DBProblem.id == problem_id).first()


def create(db: Session, problem: ProblemCreate) -> DBProblem:
    """Create a new problem in the database."""
    logger.info(f"Service: Creating new problem.")
    # Create SQLAlchemy model instance from ProblemCreate schema
    problem_data = problem.model_dump(exclude_unset=True) # No need to check for 'id' here
    db_problem = DBProblem(**problem_data)
    try:
        db.add(db_problem)
        db.commit()
        db.refresh(db_problem)
        logger.info(f"Service: Successfully created problem with id {db_problem.id}.")
        return db_problem
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurred during problem creation: {e}", exc_info=True)
        raise SQLAlchemyError(f"Database error creating problem: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during problem creation: {e}", exc_info=True)
        raise


def update(db: Session, problem_id: int, problem_update: ProblemUpdate) -> DBProblem | None:
    """Update an existing problem in the database."""
    logger.info(f"Service: Attempting to update problem with id {problem_id}.")
    db_problem = get_one(db, problem_id)
    if not db_problem:
        logger.warning(f"Service: Problem with id {problem_id} not found for update.")
        return None

    # Use ProblemUpdate schema for update data
    update_data = problem_update.model_dump(exclude_unset=True)

    try:
        for key, value in update_data.items():
            # Still prevent updating 'id', though it's not in ProblemUpdate anyway
            if key != "id":
                setattr(db_problem, key, value)
        logger.debug(f"Service: Updating fields for problem {problem_id}: {update_data.keys()}")
        db.commit()
        db.refresh(db_problem)
        logger.info(f"Service: Successfully updated problem with id {problem_id}.")
        return db_problem
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurred during problem update (id: {problem_id}): {e}", exc_info=True)
        raise SQLAlchemyError(f"Database error updating problem: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during problem update (id: {problem_id}): {e}", exc_info=True)
        raise


def patch(
    db: Session, problem_id: int, problem_update: ProblemPartialUpdate
) -> Optional[DBProblem]:
    '''Partially update an existing problem using PATCH.'''
    logger.info(f"Service: Attempting to partially update (PATCH) problem with id {problem_id}")
    db_problem = get_one(db, problem_id)
    if not db_problem:
        logger.warning(f"Service: Problem with id {problem_id} not found for PATCH update.")
        return None
    
    update_data = problem_update.model_dump(exclude_unset=True)

    if not update_data:
        logger.info(f"'Service: PATCH request for problem {problem_id} had no fields to update.")
        return db_problem
    
    try:
        for key, value in update_data.items():
            setattr(db_problem, key, value)
        logger.debug(f"Service: PATCH updating fields for problem {problem_id}: {update_data.keys()}")
        db.commit()
        db.refresh(db_problem)
        logger.info(f"Service: Succesfully updated (PATCH) problem with id {problem_id}.")
        return db_problem
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurred during problem update (PATCH) (id: {problem_id}): {e}", exc_info=True)
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during problem update (PATCH) (id: {problem_id}): {e}")
        raise


def delete(db: Session, problem_id: int) -> bool:
    '''Delete a problem from the database.'''
    logger.info(f"Service: Attempting to delete problem with id {problem_id}.")
    db_problem = get_one(db, problem_id)
    if not db_problem:
        logger.warning(f"Service: Problem with id {problem_id} not found for deletion.")
        return False
    
    try:
        db.delete(db_problem)
        db.commit()
        logger.info(f"Service: Successfully deleted problem with id {problem_id}.")
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurerred during problem deletion (id: {problem_id}): {e}", exc_info=True)
        raise SQLAlchemyError(f"Database error deleting problem: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during problem deletion (id: {problem_id}): {e}", exc_info=True)
        raise
