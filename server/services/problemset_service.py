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

    # Method to create a Problemset and its associated Problems in the DB
    def create_problemset_and_problems(
        self,
        db: Session, 
        problemset_data: LectureProblemsOutput 
    ) -> Problemset:
        """
        Creates a new Problemset and associated Problem entries in the database.

        Args:
            db: The SQLAlchemy database session.
            problemset_data: A LectureProblemsOutput Pydantic instance
                          containing the extracted data.

        Returns:
            The newly created SQLAlchemy Problemset ORM object.

        Raises:
            ProblemsetServiceError: If a database error occurs during creation.
        """
        logger.info(f"Service: Creating problemset '{problemset_data.title}' and {len(problemset_data.problems_latex)} problems in DB.")

        # Create the Problemset ORM object
        db_problemset = Problemset(
            title=problemset_data.title,
            type=problemset_data.type,
            part_of=problemset_data.part_of
        )

        # Process and Create Problem ORM objects
        problem_orms = []
        for latex_text in problemset_data.problems_latex:
            db_problem = Problem(
                latex_text=latex_text,
                category='N'  # Default category, can be updated later
            )
            problem_orms.append(db_problem)
            logger.debug(f"Service: Created ORM object for problem (first 30 chars): '{latex_text[:30]}...'")

        # Add problems to the database first so they have IDs
        db.add_all(problem_orms)
        db.flush()  # Flush to get IDs without committing
        
        # Add the problemset to get its ID
        db.add(db_problemset)
        db.flush()
        
        # Create associations between problemset and problems
        for problem in problem_orms:
            association = ProblemsetProblems(
                id_problem=problem.id,
                id_problemset=db_problemset.id
            )
            db.add(association)

        try:
            db.commit()  # Commit the transaction to save to the database
            db.refresh(db_problemset)  # Refresh the problemset object to load its ID and relationships

            logger.info(f"Service: Successfully created problemset (ID: {db_problemset.id}) and problems in DB.")
            return db_problemset

        except Exception as e:
            db.rollback()  # Roll back the transaction in case of errors
            logger.error(f"Service: Failed to create problemset and problems in DB: {e}", exc_info=True)
            # Raise a service-level error
            raise ProblemsetServiceError(f"Failed to save extracted data to database: {e}")

    # Add other database interaction methods here if needed