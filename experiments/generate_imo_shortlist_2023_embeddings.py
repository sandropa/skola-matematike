import os
import json
import time # To add delays between API calls
import numpy as np # For efficient numerical array handling
from google import genai # Use the specific import from your working code
from google.api_core import exceptions # To catch potential API errors like QuotaExceeded
import dotenv

# --- Configuration ---
# Load API Key from .env file located at the project root
# Assumes this script is run from within the experiments/ folder structure
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # Adjust if script location differs
dotenv_path = os.path.join(project_root, '.env')
print(f"Loading .env file from: {dotenv_path}")
dotenv.load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("GEMINI_API_KEY")

# Define the embedding model (using the one from your working example)
# Note: 'gemini-embedding-exp-03-07' might be experimental. Consider production models
# like 'models/embedding-001' or 'models/text-embedding-004' if available/preferred.
EMBEDDING_MODEL = "gemini-embedding-exp-03-07"
# Task type for embedding documents for later retrieval/similarity comparison
TASK_TYPE = "RETRIEVAL_DOCUMENT"

# Define input and output file paths (relative to this script's location)
# Assumes your data folder is directly in experiments/
# Adjust path if data/ is inside 01_embedding.../
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data') # Path to experiments/data/
INPUT_JSON_FILE = os.path.join(DATA_DIR, 'imo_shortlist_2023.json')
OUTPUT_EMBEDDINGS_FILE = os.path.join(DATA_DIR, 'imo_2023_embeddings.npy') # Save embeddings as numpy array
OUTPUT_METADATA_FILE = os.path.join(DATA_DIR, 'imo_2023_metadata.json') # Save corresponding IDs/categories

# Delay between API calls (seconds) to respect potential rate limits
API_DELAY = 1 # Adjust as needed (e.g., 1-2 seconds)
# --- End Configuration ---

def load_problems(filepath):
    """Loads problem data from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'problems' not in data or not isinstance(data['problems'], list):
            raise ValueError("JSON file must contain a 'problems' key with a list of problem objects.")
        print(f"Successfully loaded {len(data['problems'])} problems from {filepath}")
        return data['problems']
    except FileNotFoundError:
        print(f"ERROR: Input JSON file not found at {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {filepath}")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred loading {filepath}: {e}")
        return None

def generate_embeddings(client, problems):
    """Generates embeddings for a list of problems using the Gemini API."""
    embeddings = []
    metadata = []
    total_problems = len(problems)

    print(f"\nGenerating embeddings using model: {EMBEDDING_MODEL}")

    for i, problem in enumerate(problems):
        problem_id = problem.get('problem_id', f'unknown_id_{i}')
        category = problem.get('category', 'unknown')
        latex_content = problem.get('problem_statement_latex')

        if not latex_content:
            print(f"WARNING: Skipping problem {problem_id} due to missing 'problem_statement_latex'.")
            continue

        print(f"Processing problem {i+1}/{total_problems}: {problem_id} ({category})... ", end="")

        try:
            # --- Use the EXACT client.models.embed_content structure FROM YOUR WORKING CODE---
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,     # Use model name WITHOUT 'models/' prefix
                contents=latex_content,    # Use the keyword 'contents'
                # REMOVED task_type=TASK_TYPE # Remove task_type as it wasn't in working code
            )
            # --- End corrected API call ---


            # --- Extract the embedding vector ---
            # Based on your working example printing result.embeddings,
            # it's likely the result object has an 'embeddings' attribute
            # which is a list containing the vector.
            if hasattr(result, 'embeddings') and result.embeddings:
                # Assuming the embedding is the first (and only) element in the list
                embedding_vector = result.embeddings[0]
            else:
                 # Fallback if the structure is different - print to debug
                 print(f"\nWARNING: Could not extract embedding from result for problem {problem_id}. Result structure: {result}")
                 embedding_vector = None


            if embedding_vector:
                embeddings.append(embedding_vector)
                metadata.append({'problem_id': problem_id, 'category': category})
                print("Success.")
            else:
                 print("Failed (Embedding not found in result).")


        except exceptions.ResourceExhausted as e:
             print(f"Failed (Rate limit likely exceeded: {e}). Stopping.")
             break # Stop processing if rate limit hit
        except Exception as e:
            # Catch other potential API errors
            print(f"Failed (API Error: {e}).")
            # Decide whether to continue or stop on other errors
            # continue

        # Add a delay between requests
        time.sleep(API_DELAY)

    return np.array(embeddings), metadata # Convert list of embeddings to NumPy array
def save_data(embeddings, metadata, embeddings_filepath, metadata_filepath):
    """Saves embeddings (NumPy) and metadata (JSON) to files."""
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(embeddings_filepath), exist_ok=True)
        os.makedirs(os.path.dirname(metadata_filepath), exist_ok=True)

        # Save embeddings using NumPy
        np.save(embeddings_filepath, embeddings)
        print(f"\nSuccessfully saved {len(embeddings)} embeddings to {embeddings_filepath}")

        # Save metadata as JSON
        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"Successfully saved metadata for {len(metadata)} problems to {metadata_filepath}")

    except Exception as e:
        print(f"ERROR: Failed to save data: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    print("--- Starting Embedding Generation ---")

    if not API_KEY:
        print("ERROR: GEMINI_API_KEY not found in environment variables. Exiting.")
        exit() # Exit if no API key

    # 1. Load Problems
    problems = load_problems(INPUT_JSON_FILE)

    if problems:
        # 2. Initialize Client
        try:
            # Use the client initialization from your working code
            client = genai.Client(api_key=API_KEY)
            print("Gemini client initialized successfully.")
        except Exception as e:
            print(f"ERROR: Failed to initialize Gemini client: {e}")
            client = None # Ensure client is None if init fails

        if client:
            # 3. Generate Embeddings
            embeddings_array, metadata_list = generate_embeddings(client, problems)

            # 4. Save Results
            if len(embeddings_array) > 0 and len(metadata_list) > 0:
                save_data(embeddings_array, metadata_list, OUTPUT_EMBEDDINGS_FILE, OUTPUT_METADATA_FILE)
            else:
                print("\nNo embeddings were generated or retrieved successfully.")

    print("--- Embedding Generation Finished ---")