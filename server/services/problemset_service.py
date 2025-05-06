# server/services/problemset_service.py
import logging
from typing import List, Optional 

from sqlalchemy.orm import Session
from sqlalchemy import func # For func.max
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 

# --- Import ORM Models ---
try:
    # Alias the model for clarity, similar to problem_service
    from ..models.problemset import Problemset as DBProblemset
    from ..models.problem import Problem
    from ..models.problemset_problems import ProblemsetProblems # ORM model for the association
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
        logger.info(f"Service: Creating problemset '{ai_data.lecture_name}' (group: {ai_data.group_name}) and {len(ai_data.problems_latex)} problems in DB.")
        db_problemset = DBProblemset(
            title=ai_data.lecture_name,
            group_name=ai_data.group_name,
            type="predavanje", 
            part_of="skola matematike" 
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


# --- STANDALONE CRUD FUNCTIONS ---

def get_all(db: Session) -> List[DBProblemset]:
    logger.info("Service: Fetching all problemsets.")
    try:
        return db.query(DBProblemset).all()
    except SQLAlchemyError as e:
        logger.error(f"Service: Database error occurred fetching all problemsets: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error fetching all problemsets: {e}")
    except Exception as e:
        logger.error(f"Service: Unexpected error fetching all problemsets: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error fetching all problemsets: {e}")


def get_one(db: Session, problemset_id: int) -> Optional[DBProblemset]:
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
    logger.info(f"Service: Attempting to update problemset with id {problemset_id}.")
    db_problemset = get_one(db, problemset_id) 
    if not db_problemset:
        logger.warning(f"Service: Problemset with id {problemset_id} not found for update.")
        return None 

    update_data = problemset_update.model_dump(exclude_unset=True) 

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
    logger.info(f"Service: Attempting to delete problemset with id {problemset_id}.")
    db_problemset = get_one(db, problemset_id) 
    if not db_problemset:
        logger.warning(f"Service: Problemset with id {problemset_id} not found for deletion.")
        return False 

    try:
        db.delete(db_problemset)
        db.commit()
        logger.info(f"Service: Successfully deleted problemset with id {problemset_id}.")
        return True 
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurred during problemset deletion (id: {problemset_id}): {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error deleting problemset: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during problemset deletion (id: {problemset_id}): {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error deleting problemset: {e}")

# --- NEW FUNCTIONS FOR PROBLEM ASSOCIATION MANAGEMENT ---

def add_problem_to_problemset(
    db: Session, problemset_id: int, problem_id: int, position: Optional[int] = None
) -> Optional[ProblemsetProblems]:
    """
    Adds an existing problem to a problemset at a specific position (or appends).
    Handles checks for existence of both problemset and problem, potential
    constraint violations (duplicate entry, position conflict).
    Returns the created link object (ProblemsetProblems ORM instance) or None 
    if a logical issue occurs (e.g., not found, duplicate, position conflict).
    Raises ProblemsetServiceError for database or unexpected errors.
    """
    logger.info(
        f"Service: Attempting to add problem {problem_id} to problemset {problemset_id} at position {position}."
    )

    db_problemset = db.query(DBProblemset).filter(DBProblemset.id == problemset_id).first()
    if not db_problemset:
        logger.warning(f"Service: Problemset with id {problemset_id} not found.")
        return None

    db_problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not db_problem:
        logger.warning(f"Service: Problem with id {problem_id} not found.")
        return None

    existing_link = (
        db.query(ProblemsetProblems)
        .filter_by(id_problemset=problemset_id, id_problem=problem_id)
        .first()
    )
    if existing_link:
        logger.warning(
            f"Service: Problem {problem_id} is already associated with problemset {problemset_id}."
        )
        return None 

    actual_position: int
    if position is None:
        max_pos = (
            db.query(func.max(ProblemsetProblems.position))
            .filter(ProblemsetProblems.id_problemset == problemset_id)
            .scalar()
        )
        actual_position = (max_pos + 1) if max_pos is not None else 1
        logger.debug(f"Service: Appending problem. Calculated new position: {actual_position}.")
    else:
        actual_position = position
        logger.debug(f"Service: Adding problem at specified position: {actual_position}.")
        occupied_by_other = (
            db.query(ProblemsetProblems)
            .filter(
                ProblemsetProblems.id_problemset == problemset_id,
                ProblemsetProblems.position == actual_position,
            )
            .first()
        )
        if occupied_by_other:
            logger.warning(
                f"Service: Position {actual_position} in problemset {problemset_id} is already occupied by problem {occupied_by_other.id_problem}."
            )
            return None # Position conflict

    new_link = ProblemsetProblems(
        id_problemset=problemset_id,
        id_problem=problem_id,
        position=actual_position,
    )

    try:
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        logger.info(
            f"Service: Successfully added problem {problem_id} to problemset {problemset_id} at position {actual_position}."
        )
        return new_link
    except IntegrityError as e: 
        db.rollback()
        logger.error(
            f"Service: Integrity error (likely duplicate PK) adding link problem {problem_id} to problemset {problemset_id}: {e}",
            exc_info=True,
        )
        return None 
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Service: Database error adding problem {problem_id} to problemset {problemset_id}: {e}",
            exc_info=True,
        )
        raise ProblemsetServiceError(f"Database error adding problem to problemset: {e}")
    except Exception as e:
        db.rollback()
        logger.error(
            f"Service: Unexpected error adding problem {problem_id} to problemset {problemset_id}: {e}",
            exc_info=True,
        )
        raise ProblemsetServiceError(f"Unexpected error adding problem to problemset: {e}")


def remove_problem_from_problemset(
    db: Session, problemset_id: int, problem_id: int
) -> bool:
    """
    Removes the link between a specific problem and problemset.
    Returns True on success, False if the link doesn't exist.
    Raises ProblemsetServiceError for database or unexpected errors.
    """
    logger.info(
        f"Service: Attempting to remove problem {problem_id} from problemset {problemset_id}."
    )

    link_to_delete = (
        db.query(ProblemsetProblems)
        .filter_by(id_problemset=problemset_id, id_problem=problem_id)
        .first()
    )

    if not link_to_delete:
        logger.warning(
            f"Service: Link between problem {problem_id} and problemset {problemset_id} not found for deletion."
        )
        return False

    try:
        db.delete(link_to_delete)
        db.commit()
        logger.info(
            f"Service: Successfully removed problem {problem_id} from problemset {problemset_id}."
        )
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Service: Database error removing problem {problem_id} from problemset {problemset_id}: {e}",
            exc_info=True,
        )
        raise ProblemsetServiceError(f"Database error removing problem from problemset: {e}")
    except Exception as e:
        db.rollback()
        logger.error(
            f"Service: Unexpected error removing problem {problem_id} from problemset {problemset_id}: {e}",
            exc_info=True,
        )
        raise ProblemsetServiceError(f"Unexpected error removing problem from problemset: {e}")