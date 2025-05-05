# server/services/problemset_service.py
import logging
from typing import List, Optional # <-- Add Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError # <-- Import SQLAlchemyError

# --- Import ORM Models ---
try:
    # Alias the model for clarity, similar to problem_service
    from ..models.problemset import Problemset as DBProblemset
    from ..models.problem import Problem
    from ..models.problemset_problems import ProblemsetProblems
except ImportError as e:
    logging.error(f"Failed to import SQLAlchemy models: {e}")
    raise

# --- Import Pydantic Schemas ---
try:
    # Schemas for AI processing (already present)
    from ..schemas.problemset import LectureProblemsOutput
    # Schemas for standard CRUD (newly added/refined)
    from ..schemas.problemset import ProblemsetCreate, ProblemsetUpdate, ProblemsetSchema
except ImportError as e:
    logging.error(f"Failed to import Pydantic schemas: {e}")
    raise

logger = logging.getLogger(__name__)

# --- Custom Exceptions (keep if needed for AI processing) ---
class ProblemsetServiceError(Exception):
    """Base exception for Problemset service errors."""
    pass

# --- Existing Class for AI-related logic ---
class ProblemsetService:
    """
    Service class to handle database operations related to Problemsets and Problems,
    especially those involving AI processing.
    """
    def __init__(self):
        logger.info("ProblemsetService initialized.")

    def create_problemset_from_ai_output(
            self,
            db: Session,
            ai_data: LectureProblemsOutput
        ) -> DBProblemset:
        """
        Creates a new Problemset and associated Problem entries in the database
        based on the output from the AI PDF processing. Sets 'type' to 'predavanje'
        by default.

        Args:
            db: The SQLAlchemy database session.
            ai_data: A LectureProblemsOutput Pydantic instance
                     containing the extracted data.

        Returns:
            The newly created SQLAlchemy Problemset ORM object.

        Raises:
            ProblemsetServiceError: If a database error occurs during creation.
        """
        # --- KEEP EXISTING IMPLEMENTATION HERE ---
        logger.info(f"Service: Creating problemset '{ai_data.lecture_name}' (group: {ai_data.group_name}) and {len(ai_data.problems_latex)} problems in DB.")
        db_problemset = DBProblemset(
            title=ai_data.lecture_name,
            group_name=ai_data.group_name,
            type="predavanje", # Default type
            part_of="skola matematike" # Default context, adjust if needed
        )
        db.add(db_problemset)

        problem_orms = []
        for problem_data in ai_data.problems_latex:
            db_problem = Problem(
                latex_text=problem_data.latex_text,
                category=problem_data.category
            )
            problem_orms.append(db_problem)
        db.add_all(problem_orms)

        try:
            logger.debug("Service: Flushing session to obtain IDs...")
            db.flush()
            logger.debug(f"Service: Problemset ID after flush: {db_problemset.id}")
            if problem_orms:
                logger.debug(f"Service: First problem ID after flush: {problem_orms[0].id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Service: Error during flush: {e}", exc_info=True)
            raise ProblemsetServiceError(f"Database error during object preparation: {e}")

        if db_problemset.id is None:
            db.rollback()
            logger.error("Service: Problemset ID is still None after flush.")
            raise ProblemsetServiceError("Failed to obtain Problemset ID before creating links.")

        problem_links = []
        for index, db_problem in enumerate(problem_orms):
            if db_problem.id is None:
                db.rollback()
                logger.error(f"Service: Problem ID is None after flush for problem index {index}.")
                raise ProblemsetServiceError("Failed to obtain Problem ID before creating links.")
            link = ProblemsetProblems(
                id_problemset = db_problemset.id,
                id_problem = db_problem.id,
                position = index + 1
            )
            problem_links.append(link)
        db.add_all(problem_links)

        try:
            logger.debug("Service: Committing transaction...")
            db.commit()
            db.refresh(db_problemset)
            logger.info(f"Service: Successfully created problemset (ID: {db_problemset.id}) with {len(problem_links)} links in DB.")
            return db_problemset
        except Exception as e:
            db.rollback()
            logger.error(f"Service: Failed to commit transaction: {e}", exc_info=True)
            raise ProblemsetServiceError(f"Failed to save data to database during commit: {e}")
        # --- END OF EXISTING IMPLEMENTATION ---


# --- NEW STANDALONE CRUD FUNCTIONS ---

def get_all(db: Session) -> List[DBProblemset]:
    """Retrieve all problemsets from the database."""
    logger.info("Service: Fetching all problemsets.")
    try:
        return db.query(DBProblemset).all()
    except SQLAlchemyError as e:
        logger.error(f"Service: Database error occurred fetching all problemsets: {e}", exc_info=True)
        # Decide how to handle: re-raise, return empty list, or raise custom error
        raise ProblemsetServiceError(f"Database error fetching all problemsets: {e}")
    except Exception as e:
        logger.error(f"Service: Unexpected error fetching all problemsets: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error fetching all problemsets: {e}")


def get_one(db: Session, problemset_id: int) -> Optional[DBProblemset]:
    """Retrieve a single problemset by its ID."""
    logger.info(f"Service: Fetching problemset with id {problemset_id}.")
    try:
        return db.query(DBProblemset).filter(DBProblemset.id == problemset_id).first()
    except SQLAlchemyError as e:
        logger.error(f"Service: Database error occurred fetching problemset id {problemset_id}: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error fetching problemset id {problemset_id}: {e}")
    except Exception as e:
        logger.error(f"Service: Unexpected error fetching problemset id {problemset_id}: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error fetching problemset id {problemset_id}: {e}")


def create(db: Session, problemset: ProblemsetCreate) -> DBProblemset:
    """Create a new problemset in the database."""
    logger.info(f"Service: Creating new problemset with title '{problemset.title}'.")
    problemset_data = problemset.model_dump(exclude_unset=True)
    db_problemset = DBProblemset(**problemset_data)
    try:
        db.add(db_problemset)
        db.commit()
        db.refresh(db_problemset)
        logger.info(f"Service: Successfully created problemset with id {db_problemset.id}.")
        return db_problemset
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurred during problemset creation: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error creating problemset: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during problemset creation: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error creating problemset: {e}")


def update(db: Session, problemset_id: int, problemset_update: ProblemsetUpdate) -> Optional[DBProblemset]:
    """Update an existing problemset in the database."""
    logger.info(f"Service: Attempting to update problemset with id {problemset_id}.")
    db_problemset = get_one(db, problemset_id) # Reuse get_one for finding
    if not db_problemset:
        logger.warning(f"Service: Problemset with id {problemset_id} not found for update.")
        return None # Indicate not found

    update_data = problemset_update.model_dump(exclude_unset=True) # Get data to update

    try:
        for key, value in update_data.items():
            setattr(db_problemset, key, value)
        logger.debug(f"Service: Updating fields for problemset {problemset_id}: {update_data.keys()}")
        db.commit()
        db.refresh(db_problemset)
        logger.info(f"Service: Successfully updated problemset with id {problemset_id}.")
        return db_problemset
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurred during problemset update (id: {problemset_id}): {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error updating problemset: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during problemset update (id: {problemset_id}): {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error updating problemset: {e}")


def delete(db: Session, problemset_id: int) -> bool:
    """Delete a problemset from the database."""
    logger.info(f"Service: Attempting to delete problemset with id {problemset_id}.")
    db_problemset = get_one(db, problemset_id) # Reuse get_one
    if not db_problemset:
        logger.warning(f"Service: Problemset with id {problemset_id} not found for deletion.")
        return False # Indicate not found

    try:
        db.delete(db_problemset)
        db.commit()
        logger.info(f"Service: Successfully deleted problemset with id {problemset_id}.")
        return True # Indicate success
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurred during problemset deletion (id: {problemset_id}): {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error deleting problemset: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during problemset deletion (id: {problemset_id}): {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error deleting problemset: {e}")