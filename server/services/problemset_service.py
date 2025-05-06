# server/services/problemset_service.py
import logging
from typing import List, Optional 

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, update as sql_update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError 

# --- Import ORM Models ---
try:
    from ..models.problemset import Problemset as DBProblemset
    from ..models.problem import Problem
    from ..models.problemset_problems import ProblemsetProblems 
except ImportError as e:
    logging.error(f"Failed to import SQLAlchemy models: {e}")
    raise

# --- Import Pydantic Schemas ---
try:
    from ..schemas.problemset import LectureProblemsOutput
    from ..schemas.problemset import ProblemsetCreate, ProblemsetUpdate, ProblemsetSchema
except ImportError as e:
    logging.error(f"Failed to import Pydantic schemas: {e}")
    raise

logger = logging.getLogger(__name__)

class ProblemsetServiceError(Exception):
    pass

class ProblemsetService:
    def __init__(self):
        logger.info("ProblemsetService initialized.")

    def create_problemset_from_ai_output(
            self,
            db: Session,
            ai_data: LectureProblemsOutput
        ) -> DBProblemset:
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
            db.refresh(db_problemset) # Refresh to get relationships if needed
            # Eagerly load problems for the returned object if ProblemsetSchema expects them
            db.refresh(db_problemset)
            if hasattr(DBProblemset, 'problems'): # Check if relationship exists
                 db.query(DBProblemset).options(joinedload(DBProblemset.problems)).filter(DBProblemset.id == db_problemset.id).first()

            logger.info(f"Service: Successfully created problemset (ID: {db_problemset.id}) with {len(problem_links)} links in DB.")
            return db_problemset
        except Exception as e:
            db.rollback()
            logger.error(f"Service: Failed to commit transaction: {e}", exc_info=True)
            raise ProblemsetServiceError(f"Failed to save data to database during commit: {e}")


def get_all(db: Session) -> List[DBProblemset]:
    logger.info("Service: Fetching all problemsets.")
    try:
        return db.query(DBProblemset).options(joinedload(DBProblemset.problems).joinedload(ProblemsetProblems.problem)).all()
    except SQLAlchemyError as e:
        logger.error(f"Service: Database error occurred fetching all problemsets: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error fetching all problemsets: {e}")
    except Exception as e:
        logger.error(f"Service: Unexpected error fetching all problemsets: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error fetching all problemsets: {e}")


def get_one(db: Session, problemset_id: int) -> Optional[DBProblemset]:
    logger.info(f"Service: Fetching problemset with id {problemset_id}.")
    try:
        # Eager load problems and their positions
        return db.query(DBProblemset).options(
            joinedload(DBProblemset.problems).joinedload(ProblemsetProblems.problem)
        ).filter(DBProblemset.id == problemset_id).first()
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


def add_problem_to_problemset(
    db: Session, problemset_id: int, problem_id: int, position: Optional[int] = None
) -> Optional[ProblemsetProblems]:
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
            return None 

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
    Also shifts down the positions of subsequent problems in the same problemset.
    Returns True on success, False if the link doesn't exist.
    Raises ProblemsetServiceError for database or unexpected errors.
    """
    logger.info(
        f"Service: Attempting to remove problem {problem_id} from problemset {problemset_id} and shift positions."
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

    deleted_position = link_to_delete.position

    try:
        db.delete(link_to_delete)
        logger.debug(f"Service: Marked link for deletion (problem {problem_id}, problemset {problemset_id}).")

        # --- Shift subsequent positions ---
        if deleted_position is not None:
            logger.debug(f"Service: Shifting positions greater than {deleted_position} for problemset {problemset_id}.")
            # Use SQLAlchemy Core update statement for efficiency
            stmt = (
                sql_update(ProblemsetProblems)
                .where(
                    ProblemsetProblems.id_problemset == problemset_id,
                    ProblemsetProblems.position > deleted_position
                )
                .values(position=ProblemsetProblems.position - 1)
                .execution_options(synchronize_session="fetch") # Important for ORM consistency
            )
            db.execute(stmt)
            logger.debug("Service: Executed position shift statement.")
        else:
             logger.warning(f"Service: Deleted link did not have a position. Skipping position shift.")


        db.commit()
        logger.info(
            f"Service: Successfully removed problem {problem_id} from problemset {problemset_id} and shifted positions."
        )
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            f"Service: Database error removing problem {problem_id} from problemset {problemset_id} or shifting: {e}",
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


def reorder_problems_in_problemset(
    db: Session, problemset_id: int, problem_ids_ordered: List[int]
) -> Optional[List[ProblemsetProblems]]:
    """
    Reorders problems within a problemset based on a provided list of problem IDs.
    """
    logger.info(f"Service: Reordering problems for problemset {problemset_id}. New order: {problem_ids_ordered}")

    db_problemset = db.query(DBProblemset).options(
        joinedload(DBProblemset.problems) # Eager load current links
    ).filter(DBProblemset.id == problemset_id).first()

    if not db_problemset:
        logger.warning(f"Service: Problemset {problemset_id} not found for reordering.")
        return None

    current_links = db_problemset.problems
    current_problem_ids_in_set = {link.id_problem for link in current_links}
    
    # Validate input: all provided IDs must exist in the current set
    if not set(problem_ids_ordered).issubset(current_problem_ids_in_set):
        missing_ids = set(problem_ids_ordered) - current_problem_ids_in_set
        logger.warning(f"Service: Reorder failed. Problem IDs {missing_ids} are not in problemset {problemset_id}.")
        # Potentially raise an error or return a more specific None reason
        raise ProblemsetServiceError(f"Reorder failed. Problem IDs {missing_ids} not found in problemset {problemset_id}.")


    # Validate input: all current problems must be in the provided order list
    if len(problem_ids_ordered) != len(current_problem_ids_in_set):
        dropped_ids = current_problem_ids_in_set - set(problem_ids_ordered)
        if dropped_ids: # if any problem was dropped
            logger.warning(f"Service: Reorder failed. Problem IDs {dropped_ids} were present in the set but omitted from the new order.")
            raise ProblemsetServiceError(f"Reorder failed. Problems {dropped_ids} were omitted from the new order for problemset {problemset_id}.")
        # This also implicitly covers if problem_ids_ordered has duplicates that reduce its unique count below current_problem_ids_in_set
        # Or if it tries to add new problems (which it shouldn't)
        logger.warning(f"Service: Reorder failed. The number of problems in the new order ({len(problem_ids_ordered)}) "
                         f"does not match the current number of problems in the set ({len(current_problem_ids_in_set)}).")
        raise ProblemsetServiceError("Reorder failed. Mismatch in the number of problems provided versus currently in the set.")


    # Check for duplicate problem IDs in the input list
    if len(problem_ids_ordered) != len(set(problem_ids_ordered)):
        logger.warning(f"Service: Reorder failed. Duplicate problem IDs found in the provided order: {problem_ids_ordered}")
        raise ProblemsetServiceError("Reorder failed. Duplicate problem IDs provided in the new order.")

    updated_links = []
    try:
        # Create a dictionary for quick lookup of links by problem_id
        link_map = {link.id_problem: link for link in current_links}

        for new_pos_idx, p_id in enumerate(problem_ids_ordered):
            link_to_update = link_map.get(p_id)
            if link_to_update: # Should always be true due to prior validations
                link_to_update.position = new_pos_idx + 1 # 1-based position
                updated_links.append(link_to_update)
            else:
                # This case should ideally be caught by earlier validations
                logger.error(f"Service: Reorder consistency error. Problem ID {p_id} not found in link_map for problemset {problemset_id}.")
                db.rollback() # Rollback if something went wrong with the mapping
                raise ProblemsetServiceError(f"Internal error during reordering: problem ID {p_id} link not found.")
        
        db.commit()
        # Refresh each updated link to reflect DB state, especially if schemas need it
        for link in updated_links:
            db.refresh(link)
            if hasattr(link, 'problem'): # Eager load problem details if schema expects it
                db.refresh(link.problem)
        
        logger.info(f"Service: Successfully reordered {len(updated_links)} problems in problemset {problemset_id}.")
        return updated_links
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error reordering problems for problemset {problemset_id}: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error reordering problems: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error reordering problems for problemset {problemset_id}: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error reordering problems: {e}")