# server/services/problemset_service.py
import logging
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, update as sql_update # <-- Import update
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# --- Import ORM Models ---
try:
    from ..models.problemset import Problemset as DBProblemset, ProblemsetStatusEnum
    from ..models.problem import Problem
    from ..models.problemset_problems import ProblemsetProblems
except ImportError as e:
    logging.error(f"Failed to import SQLAlchemy models: {e}")
    raise

# --- Import Pydantic Schemas ---
try:
    from ..schemas.problemset import LectureProblemsOutput
    from ..schemas.problemset import ProblemsetCreate, ProblemsetUpdate, ProblemsetSchema, ProblemsetFinalize
except ImportError as e:
    logging.error(f"Failed to import Pydantic schemas: {e}")
    raise

logger = logging.getLogger(__name__)

class ProblemsetServiceError(Exception):
    pass

class ProblemsetService:
    # ... (keep existing __init__ and create_problemset_from_ai_output) ...
    def __init__(self):
        logger.info("ProblemsetService initialized.")

    def create_problemset_from_ai_output(
            self,
            db: Session,
            ai_data: LectureProblemsOutput
        ) -> DBProblemset:
        # (Implementation remains unchanged)
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
            if hasattr(DBProblemset, 'problems'):
                 db.query(DBProblemset).options(joinedload(DBProblemset.problems)).filter(DBProblemset.id == db_problemset.id).first()

            logger.info(f"Service: Successfully created problemset (ID: {db_problemset.id}) with {len(problem_links)} links in DB.")
            return db_problemset
        except Exception as e:
            db.rollback()
            logger.error(f"Service: Failed to commit transaction: {e}", exc_info=True)
            raise ProblemsetServiceError(f"Failed to save data to database during commit: {e}")

# --- STANDALONE CRUD FUNCTIONS ---
# (Keep get_all, get_one, create, update, delete as they are)
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


# --- ENHANCED add_problem_to_problemset ---
def add_problem_to_problemset(
    db: Session, problemset_id: int, problem_id: int, position: Optional[int] = None
) -> Optional[ProblemsetProblems]:
    """
    Adds an existing problem to a problemset. If position is specified, inserts
    at that position and shifts subsequent problems. If position is None, appends.
    """
    logger.info(
        f"Service: Attempting to add problem {problem_id} to problemset {problemset_id} at position {position}."
    )

    # --- Initial Checks (Remain the same) ---
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

    # --- Logic based on position ---
    actual_position: int
    new_link: ProblemsetProblems

    try:
        if position is None:
            # Append logic
            max_pos = (
                db.query(func.max(ProblemsetProblems.position))
                .filter(ProblemsetProblems.id_problemset == problemset_id)
                .scalar()
            )
            actual_position = (max_pos + 1) if max_pos is not None else 1
            logger.debug(f"Service: Appending problem. Calculated new position: {actual_position}.")

            new_link = ProblemsetProblems(
                id_problemset=problemset_id,
                id_problem=problem_id,
                position=actual_position,
            )
            db.add(new_link)
            # No shifting needed for append

        else:
            # Insert at specific position logic
            actual_position = position
            if actual_position <= 0:
                logger.warning(f"Service: Invalid position specified: {actual_position}. Must be positive.")
                # Returning None as it's a logical validation failure
                return None

            logger.debug(f"Service: Inserting problem at specified position: {actual_position}.")

            # --- ATOMIC SHIFT AND INSERT ---
            # 1. Shift existing items (executed within the transaction)
            shift_stmt = (
                sql_update(ProblemsetProblems)
                .where(
                    ProblemsetProblems.id_problemset == problemset_id,
                    ProblemsetProblems.position >= actual_position # Shift items at this position and later
                )
                .values(position=ProblemsetProblems.position + 1)
                .execution_options(synchronize_session="fetch")
            )
            db.execute(shift_stmt)
            logger.debug(f"Service: Executed position shift statement for position >= {actual_position}.")

            # 2. Create the new link at the specified position
            new_link = ProblemsetProblems(
                id_problemset=problemset_id,
                id_problem=problem_id,
                position=actual_position,
            )
            db.add(new_link)
            # Shifting and adding are now part of the same transaction block

        # Commit changes (either append or insert+shift)
        db.commit()
        db.refresh(new_link) # Refresh the newly created link

        logger.info(
            f"Service: Successfully added problem {problem_id} to problemset {problemset_id} at position {actual_position}."
        )
        return new_link

    except IntegrityError as e:
        db.rollback()
        # This could happen if somehow the duplicate check failed (race condition?) or other constraint violation
        logger.error(f"Service: Integrity error during add operation: {e}", exc_info=True)
        return None # Logical failure (duplicate or other constraint)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error during add operation: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error adding problem to problemset: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during add operation: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error adding problem to problemset: {e}")


# --- ENHANCED remove_problem_from_problemset ---
def remove_problem_from_problemset(
    db: Session, problemset_id: int, problem_id: int
) -> bool:
    """
    Removes the link between a specific problem and problemset.
    Also shifts down the positions of subsequent problems in the same problemset.
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

        # Shift subsequent positions if the deleted item had a position
        if deleted_position is not None:
            logger.debug(f"Service: Shifting positions greater than {deleted_position} for problemset {problemset_id}.")
            stmt = (
                sql_update(ProblemsetProblems)
                .where(
                    ProblemsetProblems.id_problemset == problemset_id,
                    ProblemsetProblems.position > deleted_position
                )
                .values(position=ProblemsetProblems.position - 1)
                .execution_options(synchronize_session="fetch")
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


# --- Keep reorder_problems_in_problemset as is ---
def reorder_problems_in_problemset(
    db: Session, problemset_id: int, problem_ids_ordered: List[int]
) -> Optional[List[ProblemsetProblems]]:
    """
    Reorders problems within a problemset based on a provided list of problem IDs.
    Returns the list of updated link objects on success, None if problemset not found.
    Raises ProblemsetServiceError for validation errors or DB errors.
    """
    logger.info(f"Service: Reordering problems for problemset {problemset_id}. New order: {problem_ids_ordered}")

    db_problemset = db.query(DBProblemset).options(
        joinedload(DBProblemset.problems)
    ).filter(DBProblemset.id == problemset_id).first()

    if not db_problemset:
        logger.warning(f"Service: Problemset {problemset_id} not found for reordering.")
        return None

    current_links = db_problemset.problems
    current_problem_ids_in_set = {link.id_problem for link in current_links}

    ordered_ids_set = set(problem_ids_ordered)
    if not ordered_ids_set.issubset(current_problem_ids_in_set):
        missing_ids = ordered_ids_set - current_problem_ids_in_set
        logger.warning(f"Service: Reorder failed. Problem IDs {missing_ids} are not in problemset {problemset_id}.")
        raise ProblemsetServiceError(f"Reorder failed. Problem IDs {missing_ids} not found in problemset {problemset_id}.")

    if len(problem_ids_ordered) != len(current_problem_ids_in_set):
        dropped_ids = current_problem_ids_in_set - ordered_ids_set
        if dropped_ids:
            logger.warning(f"Service: Reorder failed. Problem IDs {dropped_ids} were present in the set but omitted from the new order.")
            raise ProblemsetServiceError(f"Reorder failed. Problems {dropped_ids} were omitted from the new order for problemset {problemset_id}.")
        logger.warning(f"Service: Reorder failed. The number of problems in the new order ({len(problem_ids_ordered)}) "
                         f"does not match the current number of problems in the set ({len(current_problem_ids_in_set)}).")
        raise ProblemsetServiceError("Reorder failed. Mismatch in the number of problems provided versus currently in the set.")

    if len(problem_ids_ordered) != len(ordered_ids_set):
        logger.warning(f"Service: Reorder failed. Duplicate problem IDs found in the provided order: {problem_ids_ordered}")
        raise ProblemsetServiceError("Reorder failed. Duplicate problem IDs provided in the new order.")

    updated_links = []
    try:
        link_map = {link.id_problem: link for link in current_links}

        for new_pos_idx, p_id in enumerate(problem_ids_ordered):
            link_to_update = link_map.get(p_id)
            if link_to_update:
                new_position = new_pos_idx + 1
                if link_to_update.position != new_position:
                    link_to_update.position = new_position
                    logger.debug(f"Service: Setting problem {p_id} to position {new_position} in problemset {problemset_id}.")
                updated_links.append(link_to_update)
            else:
                logger.error(f"Service: Reorder consistency error. Problem ID {p_id} not found in link_map for problemset {problemset_id}.")
                db.rollback()
                raise ProblemsetServiceError(f"Internal error during reordering: problem ID {p_id} link not found.")

        db.commit()

        refreshed_links = []
        for link in updated_links:
            db.refresh(link)
            if hasattr(link, 'problem'):
                 db.refresh(link.problem)
            refreshed_links.append(link)

        logger.info(f"Service: Successfully reordered {len(refreshed_links)} problems in problemset {problemset_id}.")
        return refreshed_links
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error reordering problems for problemset {problemset_id}: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error reordering problems: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error reordering problems for problemset {problemset_id}: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error reordering problems: {e}")

async def finalize_problemset(db: Session, problemset_id: int, finalize_data: ProblemsetFinalize) -> Optional[DBProblemset]:
    """
    Finalizes a problemset by:
    1. Updating its status to FINALIZED
    2. Parsing the raw LaTeX text into individual problems using GeminiService
    3. Creating the problems and their relationships
    """
    logger.info(f"Service: Finalizing problemset with id {problemset_id}")
    
    # Get the problemset
    db_problemset = get_one(db, problemset_id)
    if not db_problemset:
        logger.warning(f"Service: Problemset with id {problemset_id} not found for finalization.")
        return None
    
    if db_problemset.status == ProblemsetStatusEnum.FINALIZED:
        logger.warning(f"Service: Problemset {problemset_id} is already finalized.")
        return db_problemset

    try:
        # Update the raw LaTeX text
        db_problemset.raw_latex = finalize_data.raw_latex
        
        # Create a temporary PDF from the LaTeX text
        from ..services.pdf_service import compile_latex_to_pdf
        pdf_bytes = compile_latex_to_pdf(finalize_data.raw_latex)
        
        # Use GeminiService to parse the problems
        from ..services.gemini_service import GeminiService
        gemini_service = GeminiService(None)  # TODO: Get proper client instance
        parsed_data = await gemini_service.process_lecture_pdf(pdf_bytes)
        
        # Create Problem objects for each parsed problem
        problem_orms = []
        for problem_data in parsed_data.problems_latex:
            db_problem = Problem(
                latex_text=problem_data.latex_text,
                category=problem_data.category
            )
            problem_orms.append(db_problem)
        db.add_all(problem_orms)
        
        # Create links between problemset and problems
        problem_links = []
        for index, db_problem in enumerate(problem_orms):
            link = ProblemsetProblems(
                id_problemset=db_problemset.id,
                id_problem=db_problem.id,
                position=index + 1
            )
            problem_links.append(link)
        db.add_all(problem_links)
        
        # Update status to FINALIZED
        db_problemset.status = ProblemsetStatusEnum.FINALIZED
        
        db.commit()
        db.refresh(db_problemset)
        logger.info(f"Service: Successfully finalized problemset with id {problemset_id}")
        return db_problemset
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurred during problemset finalization: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error finalizing problemset: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during problemset finalization: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error finalizing problemset: {e}")

def save_draft(db: Session, problemset_id: int, raw_latex: str) -> Optional[DBProblemset]:
    """
    Saves a draft of a problemset by updating its raw LaTeX text.
    Does not parse or create individual problems.
    """
    logger.info(f"Service: Saving draft for problemset with id {problemset_id}")
    
    db_problemset = get_one(db, problemset_id)
    if not db_problemset:
        logger.warning(f"Service: Problemset with id {problemset_id} not found for draft save.")
        return None

    try:
        db_problemset.raw_latex = raw_latex
        db_problemset.status = ProblemsetStatusEnum.DRAFT
        
        db.commit()
        db.refresh(db_problemset)
        logger.info(f"Service: Successfully saved draft for problemset with id {problemset_id}")
        return db_problemset
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Service: Database error occurred during draft save: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Database error saving draft: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Service: Unexpected error during draft save: {e}", exc_info=True)
        raise ProblemsetServiceError(f"Unexpected error saving draft: {e}")