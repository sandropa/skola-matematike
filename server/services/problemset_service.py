import logging
from typing import List

from sqlalchemy.orm import Session
try:
    from ..models.problemset import Problemset
    from ..models.problem import Problem 
    from ..models.problemset_problems import ProblemsetProblems
except ImportError as e:
    logging.error(f"Failed to import SQLAlchemy models: {e}")
    raise

try:
    from ..schemas.problemset import LectureProblemsOutput 
except ImportError as e:
    logging.error(f"Failed to import LectureProblemsOutput schema: {e}")
    raise


logger = logging.getLogger(__name__)

class ProblemsetServiceError(Exception):
    """Base exception for Problemset service errors."""
    pass


class ProblemsetService:
    """
    Service class to handle database operations related to Problemsets and Problems.
    """
    def __init__(self):
        """
        ProblemsetService doesn't need dependencies injected at init for this simple case,
        as the DB session is passed per-method.
        """
        logger.info("ProblemsetService initialized.")


    def create_problemset_from_ai_output(
            self,
            db: Session,
            ai_data: LectureProblemsOutput
        ) -> Problemset:
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

            # --- 1. Create the Problemset ORM object IN MEMORY ---
            db_problemset = Problemset(
                title=ai_data.lecture_name,
                group_name=ai_data.group_name,
                type="predavanje",
                part_of="skola matematike" # Add other fields as needed
            )
            # Add the problemset to the session early
            db.add(db_problemset)

            # --- 2. Create all Problem ORM objects IN MEMORY ---
            problem_orms = []
            for latex_content in ai_data.problems_latex:
                db_problem = Problem(
                    latex_text=latex_content,
                    category="N" # Default category
                    # Add other fields as needed
                )
                problem_orms.append(db_problem)
                logger.debug(f"Service: Prepared ORM object for problem: '{latex_content[:30]}...'")

            # Add all problems to the session so they get IDs on flush
            db.add_all(problem_orms)

            # --- 3. Flush to get IDs ---
            # This assigns IDs to db_problemset and all db_problem objects in problem_orms
            # without ending the transaction.
            try:
                logger.debug("Service: Flushing session to obtain IDs...")
                db.flush()
                logger.debug(f"Service: Problemset ID after flush: {db_problemset.id}")
                # Log first problem ID for confirmation
                if problem_orms:
                    logger.debug(f"Service: First problem ID after flush: {problem_orms[0].id}")
            except Exception as e:
                db.rollback()
                logger.error(f"Service: Error during flush: {e}", exc_info=True)
                raise ProblemsetServiceError(f"Database error during object preparation: {e}")


            # --- 4. Create all Association Link objects IN MEMORY ---
            problem_links = []
            # Ensure we actually flushed and got IDs
            if db_problemset.id is None:
                db.rollback() # Should not happen if flush worked, but safety check
                logger.error("Service: Problemset ID is still None after flush.")
                raise ProblemsetServiceError("Failed to obtain Problemset ID before creating links.")

            for index, db_problem in enumerate(problem_orms):
                if db_problem.id is None:
                    db.rollback() # Safety check
                    logger.error(f"Service: Problem ID is None after flush for problem index {index}.")
                    raise ProblemsetServiceError("Failed to obtain Problem ID before creating links.")

                link = ProblemsetProblems(
                    id_problemset = db_problemset.id, # Use flushed ID
                    id_problem = db_problem.id,       # Use flushed ID
                    position = index + 1              # Set position
                )
                problem_links.append(link)
                logger.debug(f"Service: Prepared link object for problem pos {index + 1} (Problem ID: {db_problem.id})")

            # Add all link objects to the session
            db.add_all(problem_links)

            # --- 5. Commit the transaction (only ONCE, outside the loop) ---
            try:
                logger.debug("Service: Committing transaction...")
                db.commit()
                db.refresh(db_problemset) # Refresh parent object AFTER commit
                # You might need to refresh related objects too if accessed immediately,
                # but often lazy loading handles this when needed.
                logger.info(f"Service: Successfully created problemset (ID: {db_problemset.id}) with {len(problem_links)} links in DB.")

                # --- 6. Return the final object (only ONCE, outside the loop) ---
                return db_problemset

            except Exception as e:
                db.rollback() # Roll back the transaction in case of commit errors
                logger.error(f"Service: Failed to commit transaction: {e}", exc_info=True)
                raise ProblemsetServiceError(f"Failed to save data to database during commit: {e}")
                    