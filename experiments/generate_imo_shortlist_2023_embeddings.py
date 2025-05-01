import os
import json
import time # To add delays between API calls
import numpy as np # For efficient numerical array handling
from google import genai # Use the specific import from your working code
from google.api_core import exceptions # To catch potential API errors like QuotaExceeded
import dotenv
import logging # Use logging for better output control

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API Key from .env file located at the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # Adjust if script location differs
dotenv_path = os.path.join(project_root, '.env')
logging.info(f"Loading .env file from: {dotenv_path}")
dotenv.load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("GEMINI_API_KEY")

# Define the embedding model
EMBEDDING_MODEL = "gemini-embedding-exp-03-07" # Your working model
TASK_TYPE = "RETRIEVAL_DOCUMENT" # Or appropriate task type

# Define input and output file paths (relative to this script's location)
# Assumes script is OUTSIDE data/, but points INTO data/
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data') # Path to experiments/data/
INPUT_JSON_FILE = os.path.join(DATA_DIR, 'imo_shortlist_2023.json')
OUTPUT_EMBEDDINGS_FILE = os.path.join(DATA_DIR, 'imo_2023_embeddings.npy') # Save embeddings as numpy array
OUTPUT_METADATA_FILE = os.path.join(DATA_DIR, 'imo_2023_metadata.json') # Save corresponding IDs/categories

# Delay between API calls (seconds)
API_DELAY = 1.5 # Slightly increased delay might help with rate limits
# --- End Configuration ---

def load_problems(filepath):
    """Loads problem data from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'problems' not in data or not isinstance(data['problems'], list):
            raise ValueError("JSON file must contain a 'problems' key with a list of problem objects.")
        logging.info(f"Successfully loaded {len(data['problems'])} problems definition from {filepath}")
        return data['problems']
    except FileNotFoundError:
        logging.error(f"Input JSON file not found at {filepath}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON from {filepath}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred loading {filepath}: {e}", exc_info=True)
        return None

def load_existing_progress(embeddings_filepath, metadata_filepath):
    """Loads previously generated embeddings and metadata, returns them and processed IDs."""
    processed_ids = set()
    existing_embeddings = []
    existing_metadata = []

    if os.path.exists(metadata_filepath) and os.path.exists(embeddings_filepath):
        logging.warning(f"Output files found. Attempting to load existing progress...")
        try:
            with open(metadata_filepath, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
            # Convert list of lists/arrays back to numpy array if needed after loading JSON
            # For npy, just load it:
            loaded_npy = np.load(embeddings_filepath)
            existing_embeddings = list(loaded_npy) # Work with a list for easier appending

            if len(existing_metadata) != len(existing_embeddings):
                 logging.error("Mismatch between loaded metadata count and embeddings count. Starting fresh.")
                 return set(), [], [] # Return empty if inconsistent

            for item in existing_metadata:
                if 'problem_id' in item:
                    processed_ids.add(item['problem_id'])

            logging.info(f"Loaded {len(processed_ids)} previously processed problems.")
            return processed_ids, existing_embeddings, existing_metadata

        except Exception as e:
            logging.error(f"Error loading existing progress files: {e}. Starting fresh.", exc_info=True)
            # If loading fails, reset progress
            return set(), [], []
    else:
        logging.info("No existing output files found. Starting fresh.")
        return processed_ids, existing_embeddings, existing_metadata

def save_progress(embeddings_list, metadata_list, embeddings_filepath, metadata_filepath):
    """Saves the current embeddings (NumPy) and metadata (JSON) to files."""
    try:
        # Ensure directories exist
        os.makedirs(os.path.dirname(embeddings_filepath), exist_ok=True)
        os.makedirs(os.path.dirname(metadata_filepath), exist_ok=True)

        # Convert list of embedding vectors to a NumPy array before saving
        embeddings_array = np.array(embeddings_list)
        np.save(embeddings_filepath, embeddings_array) # Overwrites existing file

        # Save metadata as JSON
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, indent=2, ensure_ascii=False) # Overwrites existing file

        logging.debug(f"Progress saved. Embeddings: {embeddings_array.shape}, Metadata items: {len(metadata_list)}")

    except Exception as e:
        logging.error(f"ERROR: Failed to save progress: {e}", exc_info=True)


def generate_embeddings_resumable(client, problems, processed_ids, current_embeddings, current_metadata):
    """
    Generates embeddings, skipping processed IDs and saving progress incrementally.

    Args:
        client: Initialized genai.Client.
        problems: List of all problem dictionaries from input JSON.
        processed_ids: Set of problem_ids already processed.
        current_embeddings: List of embedding vectors loaded from previous runs.
        current_metadata: List of metadata dicts loaded from previous runs.

    Returns:
        Tuple: (final_embeddings_list, final_metadata_list)
    """
    total_problems = len(problems)
    newly_processed_count = 0

    logging.info(f"Starting embedding generation loop. Model: {EMBEDDING_MODEL}. Total problems: {total_problems}. Already processed: {len(processed_ids)}.")

    for i, problem in enumerate(problems):
        problem_id = problem.get('problem_id', f'unknown_id_{i}')
        category = problem.get('category', 'unknown')
        latex_content = problem.get('problem_statement_latex')

        # --- Skip if already processed ---
        if problem_id in processed_ids:
            # Log skipping less frequently to avoid clutter
            if (i + 1) % 10 == 0 or i == 0:
                 logging.debug(f"Skipping problem {i+1}/{total_problems}: {problem_id} (already processed).")
            continue

        # --- Process if not skipped ---
        logging.info(f"Processing problem {i+1}/{total_problems}: {problem_id} ({category})... ")

        if not latex_content:
            logging.warning(f"Skipping problem {problem_id} due to missing 'problem_statement_latex'.")
            continue

        try:
            # --- Use the EXACT client.models.embed_content structure ---
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,     # Use model name WITHOUT 'models/' prefix
                contents=latex_content,    # Use the keyword 'contents'
            )

            # --- Extract the embedding vector ---
            if hasattr(result, 'embeddings') and result.embeddings:
                embedding_vector = result.embeddings[0]
            else:
                 logging.warning(f"Could not extract embedding from result for problem {problem_id}. Result structure: {result}")
                 embedding_vector = None

            # --- If successful, append and SAVE progress ---
            if embedding_vector:
                current_embeddings.append(embedding_vector)
                current_metadata.append({'problem_id': problem_id, 'category': category})
                processed_ids.add(problem_id) # Add to processed set immediately
                newly_processed_count += 1
                logging.info(f"Success for {problem_id}. Saving progress...")
                # Save after each successful call
                save_progress(current_embeddings, current_metadata, OUTPUT_EMBEDDINGS_FILE, OUTPUT_METADATA_FILE)
            else:
                 logging.warning(f"Failed for {problem_id} (Embedding not found in result).")

        except exceptions.ResourceExhausted as e:
             logging.error(f"Failed for {problem_id} (Rate limit likely exceeded: {e}). Stopping generation.")
             break # Stop processing loop
        except Exception as e:
            logging.error(f"Failed for {problem_id} (API Error: {e}).", exc_info=True)
            # Decide whether to continue or stop on other errors
            # For now, let's stop on any API error to be safe
            break

        # Add a delay between requests AFTER attempting an API call
        logging.debug(f"Waiting {API_DELAY}s before next request...")
        time.sleep(API_DELAY)

    logging.info(f"Embedding generation loop finished. Newly processed in this run: {newly_processed_count}.")
    return current_embeddings, current_metadata


# --- Main Execution ---
if __name__ == "__main__":
    logging.info("--- Starting Resumable Embedding Generation ---")

    if not API_KEY:
        logging.error("GEMINI_API_KEY not found in environment variables. Exiting.")
        exit() # Exit if no API key

    # 1. Load ALL Problems definitions
    problems_to_process = load_problems(INPUT_JSON_FILE)

    if problems_to_process:
        # 2. Load Existing Progress (if any)
        processed_ids_set, embeddings_list, metadata_list = load_existing_progress(
            OUTPUT_EMBEDDINGS_FILE, OUTPUT_METADATA_FILE
        )

        # 3. Initialize Client
        try:
            client = genai.Client(api_key=API_KEY)
            logging.info("Gemini client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Gemini client: {e}", exc_info=True)
            client = None

        if client:
            # 4. Generate Embeddings (Resumable)
            final_embeddings, final_metadata = generate_embeddings_resumable(
                client,
                problems_to_process,
                processed_ids_set,
                embeddings_list, # Pass loaded embeddings
                metadata_list      # Pass loaded metadata
            )

            logging.info(f"Final state: {len(final_embeddings)} embeddings, {len(final_metadata)} metadata entries saved.")
            # Final save is redundant due to incremental saving, but doesn't hurt
            # save_progress(final_embeddings, final_metadata, OUTPUT_EMBEDDINGS_FILE, OUTPUT_METADATA_FILE)

        else:
            logging.error("Exiting due to Gemini client initialization failure.")

    else:
        logging.error("Exiting because problem data could not be loaded.")

    logging.info("--- Resumable Embedding Generation Finished ---")