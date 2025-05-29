# load_kamp_data.py (at project root)

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import server.models.user # Or e.g., from server.models.user import User
import server.models.password_reset # Or e.g., from server.models.password_reset import PasswordReset


# Add the 'server' directory to the Python path to allow imports
# like 'from server.database import ...'
project_root = Path(__file__).resolve().parent
server_dir = project_root / 'server'
sys.path.insert(0, str(project_root)) # Add project root first
# sys.path.insert(0, str(server_dir)) # Alternatively add server dir

# Now import components from the 'server' package
try:
    from sqlalchemy.orm import Session
    from server.database import SessionLocal, engine, Base # Import session factory and Base
    from server.models.problemset import Problemset # Import ORM model
    from server.models.problem import Problem       # Import ORM model
    from server.models.problemset_problems import ProblemsetProblems # Import Association Object ORM model
    # Import Pydantic schemas for validating the loaded JSON data
    from server.schemas.problemset import LectureProblemsOutput
    from server.schemas.problemset import ProblemOutput # Ensure this inner schema is defined
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Ensure this script is run from the project root directory containing the 'server' folder,")
    print("and that all __init__.py files are present.")
    sys.exit(1)

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATA_FILE_PATH = project_root / "experiments" / "data" / "ljetni_kamp_extracted_data_with_category.json"

# Define mapping or default values for fields not present in AI output
DEFAULT_PROBLEMSET_TYPE = "predavanje"
DEFAULT_PROBLEMSET_CONTEXT = "ljetni kamp" # Assuming this is constant for this file

# --- End Configuration ---


def load_json_data(filepath: Path) -> List[Dict[str, Any]]:
    """Loads the list of lecture data from the JSON file."""
    if not filepath.is_file():
        logging.error(f"Data file not found: {filepath}")
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            logging.error(f"Expected a JSON list in {filepath}, but got {type(data)}.")
            return []
        logging.info(f"Successfully loaded {len(data)} entries from {filepath}")
        return data
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from {filepath}: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred loading {filepath}: {e}", exc_info=True)
        return []

def process_and_load_lecture(db: Session, lecture_entry: Dict[str, Any]):
    """Processes a single lecture entry from JSON and loads it into the DB."""
    try:
        # 1. Validate input dictionary using the Pydantic model for AI output
        logging.debug(f"Validating data for lecture: {lecture_entry.get('lecture_name', 'N/A')}")
        ai_data = LectureProblemsOutput(**lecture_entry)
        logging.debug(f"Validation successful for: {ai_data.lecture_name}")

        # 2. Check if Problemset might already exist (simple check by title/group)
        # More robust checking might involve date, context etc. depending on requirements.
        # For now, we'll assume we create new ones or duplicates are okay for this script.
        # existing_ps = db.query(Problemset).filter_by(title=ai_data.lecture_name, group_name=ai_data.group_name).first()
        # if existing_ps:
        #     logging.warning(f"Problemset '{ai_data.lecture_name}' for group '{ai_data.group_name}' might already exist (ID: {existing_ps.id}). Skipping insertion.")
        #     return # Or decide how to handle updates/duplicates

        # 3. Create the Problemset ORM object
        db_problemset = Problemset(
            # Map fields from validated AI data (Pydantic object)
            # Adapt these mappings based on your FINAL Problemset ORM model structure
            title=ai_data.lecture_name,       # Using 'title' field in ORM model
            group_name=ai_data.group_name,  # Using 'group_name' field in ORM model
            type=DEFAULT_PROBLEMSET_TYPE,     # Set type
            part_of=DEFAULT_PROBLEMSET_CONTEXT, # Set context
            # Add other fields like date, school_year if they exist in the ORM model and you have data
        )
        db.add(db_problemset)
        # Flush here to get db_problemset.id if needed before creating links
        # but linking via object association often works without needing IDs explicitly first
        logging.info(f"Prepared Problemset ORM: {ai_data.lecture_name}")

        # 4. Create Problem ORM objects and Link objects
        problem_links = []
        processed_problems_in_set = {} # Track problems added *within this specific problemset*

        for index, problem_data in enumerate(ai_data.problems_latex):
            # problem_data is now a ProblemOutput Pydantic instance (or dict if validation skipped)
            latex_text = problem_data.latex_text
            category = problem_data.category

            # Optional: Basic duplicate check *within this problemset*
            if latex_text in processed_problems_in_set:
                logging.warning(f"Duplicate LaTeX found within problemset '{ai_data.lecture_name}'. Skipping redundant entry.")
                continue

            # --- Problem Existence Check (Optional but recommended) ---
            # Query DB to see if this exact problem LaTeX already exists
            db_problem = db.query(Problem).filter(Problem.latex_text == latex_text).first()
            if db_problem:
                logging.debug(f"Found existing Problem (ID: {db_problem.id}) for LaTeX: '{latex_text[:30]}...'")
                # Update category if existing one is different or null? Optional logic.
                # if db_problem.category != category:
                #     logging.info(f"Updating category for existing Problem ID {db_problem.id} to '{category}'")
                #     db_problem.category = category # SQLAlchemy tracks change
            else:
                # Create new Problem ORM object if it doesn't exist
                db_problem = Problem(
                    latex_text=latex_text,
                    category=category
                    # Add other Problem fields if necessary (comments, solution, versions)
                )
                db.add(db_problem) # Add new problem to session
                logging.debug(f"Prepared new Problem ORM object for LaTeX: '{latex_text[:30]}...'")
                # Must flush to get the ID for the link object if problem is new
                try:
                    db.flush() # Assigns ID to the new db_problem
                    if db_problem.id is None: raise ValueError("Flush did not assign ID")
                    logging.debug(f"Flushed new problem, got ID: {db_problem.id}")
                except Exception as flush_exc:
                     logging.error(f"Error flushing new problem: {flush_exc}", exc_info=True)
                     raise # Re-raise to trigger rollback

            # --- Create the Link object ---
            link = ProblemsetProblems(
                # Let SQLAlchemy handle FKs via relationship assignment
                problemset=db_problemset,
                problem=db_problem,
                position=index + 1
            )
            db.add(link) # Add link object to session
            processed_problems_in_set[latex_text] = True # Mark as processed for this set
            logging.debug(f"Prepared link object for Problem ID {db_problem.id} at position {index + 1}")

        # 5. Commit changes for this lecture entry
        # (Commit happens outside this function in the main loop)

    except Exception as e:
        logging.error(f"Failed processing entry for lecture '{lecture_entry.get('lecture_name', 'N/A')}': {e}", exc_info=True)
        raise # Re-raise the exception to trigger rollback in the main loop


# --- Main Execution ---
if __name__ == "__main__":
    logging.info(f"--- Starting Database Loading Script ---")
    logging.info(f"Loading data from: {DATA_FILE_PATH}")

    lecture_data_list = load_json_data(DATA_FILE_PATH)

    if not lecture_data_list:
        logging.warning("No lecture data loaded. Exiting.")
        sys.exit(0)

    # Get a database session
    db: Session = SessionLocal()
    processed_count = 0
    error_count = 0

    try:
        for lecture_entry in lecture_data_list:
            try:
                process_and_load_lecture(db, lecture_entry)
                # Commit after each successful lecture processing
                db.commit()
                processed_count += 1
                logging.info(f"Successfully committed data for lecture: {lecture_entry.get('lecture_name', 'N/A')}")
            except Exception as e:
                # Error logged within process_and_load_lecture
                logging.error(f"Rolling back transaction due to error processing lecture: {lecture_entry.get('lecture_name', 'N/A')}")
                db.rollback() # Rollback only the failed lecture
                error_count += 1

        logging.info(f"--- Database Loading Finished ---")
        logging.info(f"Successfully processed and committed: {processed_count} lectures.")
        logging.info(f"Failed to process: {error_count} lectures.")

    except Exception as e:
        logging.error(f"An critical error occurred during the main loop: {e}", exc_info=True)
        db.rollback() # Rollback any pending changes if the loop itself crashes
    finally:
        logging.info("Closing database session.")
        db.close() # Ensure session is closed