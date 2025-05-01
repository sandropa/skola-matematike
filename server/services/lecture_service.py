# server/services/lecture_service.py

import logging
from typing import List # Needed for type hints

# Import SQLAlchemy Session and models
from sqlalchemy.orm import Session
try:
    from ..models.lecture import Lecture # Import the SQLAlchemy Lecture ORM model
    from ..models.problem import Problem # Import the SQLAlchemy Problem ORM model
    # No need to import the association table here unless directly manipulated
except ImportError as e:
    logging.error(f"Failed to import SQLAlchemy models: {e}")
    raise

# Import the Pydantic model from the AI output
try:
    from ..schemas.lecture import LectureProblemsOutput # Import the Pydantic AI output model
except ImportError as e:
    logging.error(f"Failed to import LectureProblemsOutput schema: {e}")
    raise


logger = logging.getLogger(__name__)

# Define custom service-level exception for DB operations
class LectureServiceError(Exception):
    """Base exception for Lecture service errors."""
    pass


class LectureService:
    """
    Service class to handle database operations related to Lectures and Problems.
    """
    def __init__(self):
        """
        LectureService doesn't need dependencies injected at init for this simple case,
        as the DB session is passed per-method.
        """
        logger.info("LectureService initialized.")

    # Method to create a Lecture and its associated Problems in the DB
    # This method takes the validated Pydantic data and the DB session
    def create_lecture_and_problems(
        self,
        db: Session, # Inject the database session
        lecture_data: LectureProblemsOutput # The validated data from the AI
    ) -> Lecture: # Type hint return as SQLAlchemy Lecture ORM model
        """
        Creates a new Lecture and associated Problem entries in the database.

        Args:
            db: The SQLAlchemy database session.
            lecture_data: A LectureProblemsOutput Pydantic instance
                          containing the extracted data.

        Returns:
            The newly created SQLAlchemy Lecture ORM object.

        Raises:
            LectureServiceError: If a database error occurs during creation.
        """
        logger.info(f"Service: Creating lecture '{lecture_data.lecture_name}' and {len(lecture_data.problems_latex)} problems in DB.")

        # --- 1. Create the Lecture ORM object ---
        db_lecture = Lecture(
            name=lecture_data.lecture_name,
            group_name=lecture_data.group_name,
            # created_at is set automatically by server_default
        )

        # --- 2. Process and Create Problem ORM objects ---
        # Here, we create a new Problem ORM object for each LaTeX string extracted
        # If you wanted to check for existing problems and reuse them, this logic
        # would involve querying the 'db' session.
        problem_orms = []
        for latex_content in lecture_data.problems_latex:
            db_problem = Problem(
                latex_content=latex_content,
                image_filename=None, # Since it's from PDF extraction, no image
                # created_at is set automatically
            )
            problem_orms.append(db_problem)
            logger.debug(f"Service: Created ORM object for problem (first 30 chars): '{latex_content[:30]}...'")


        # --- 3. Associate Problems with the Lecture ---
        # SQLAlchemy handles the association table implicitly when you append Problem objects
        # to the 'problems' relationship list of the Lecture object.
        db_lecture.problems.extend(problem_orms)
        logger.debug(f"Service: Associated {len(problem_orms)} problems with the lecture ORM object.")

        # --- 4. Add to Session, Commit, and Refresh ---
        try:
            db.add(db_lecture) # Add the lecture (and implicitly the associated problems) to the session
            db.commit() # Commit the transaction to save to the database
            db.refresh(db_lecture) # Refresh the lecture object to load its ID and relationships

            logger.info(f"Service: Successfully created lecture (ID: {db_lecture.id}) and problems in DB.")
            return db_lecture # Return the SQLAlchemy Lecture ORM object

        except Exception as e:
            db.rollback() # Roll back the transaction in case of errors
            logger.error(f"Service: Failed to create lecture and problems in DB: {e}", exc_info=True)
            # Raise a service-level error
            raise LectureServiceError(f"Failed to save extracted data to database: {e}")

    # Add other database interaction methods here if needed (e.g., get_lecture_by_id)