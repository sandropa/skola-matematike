import os
import json
import time
import logging
from pathlib import Path # For easier path manipulation

# Use the specific imports for genai from your working code
from google import genai
from google.genai import types
from google.api_core import exceptions # To catch potential API errors like QuotaExceeded
import dotenv

# Use run_in_threadpool for the synchronous streaming call
# Need to install threadpoolctl or manage async differently if not in FastAPI context
# Simpler approach for a script: run the sync code directly.
# If performance is critical for many files, asyncio + run_in_threadpool could be used.
# For now, let's keep it synchronous for simplicity.

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API Key from .env file located at the project root
# Assumes this script is run from experiments/
project_root = Path(__file__).resolve().parent.parent # Go up two levels from experiments/script.py
dotenv_path = project_root / '.env'
logging.info(f"Loading .env file from: {dotenv_path}")
dotenv.load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("GEMINI_API_KEY")

# Define the embedding model from your working code
MODEL_NAME = "gemini-2.5-flash-preview-04-17"

# Define input and output paths relative to the project root
DATA_DIR = project_root / 'experiments' / 'data'
INPUT_KAMP_DIR = DATA_DIR / 'ljetni_kamp'
OUTPUT_JSON_FILE = DATA_DIR / 'ljetni_kamp_extracted_data.json'

# Delay between API calls (seconds) - adjust as needed
API_DELAY = 10
# --- End Configuration ---


def get_gemini_client(api_key):
    """Initializes and returns the Gemini client."""
    if not api_key:
        logging.error("GEMINI_API_KEY not found. Please set it in your .env file.")
        return None
    try:
        client = genai.Client(api_key=api_key)
        logging.info("Gemini client initialized successfully.")
        # Optional: Add a quick test call like client.list_models() here if needed
        return client
    except Exception as e:
        logging.error(f"Failed to initialize Gemini client: {e}", exc_info=True)
        return None


def get_generate_config():
    """Returns the GenerateContentConfig object based on your provided structure."""
    # Directly use the schema definition you provided
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["lecture_name", "group_name", "problems_latex"],
            properties = {
                "lecture_name": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The main title or name/topic of the lecture found in the document.",
                ),
                "group_name": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The target group for the lecture, mapped precisely to one of the five allowed values.",
                    enum = ["napredna", "olimpijska", "pocetna", "predolimpijska", "srednja"],
                ),
                "problems_latex": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    description = "A list containing the extracted LaTeX source string for each distinct problem identified in the document.",
                    items = genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "The full LaTeX representation of a single math problem.",
                    ),
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text="""You are a highly accurate extraction engine specializing in mathematical lecture documents (PDFs) from math camps. Your task is to parse the provided PDF and extract the following specific pieces of information:

1.  **Lecture Title:** Identify and extract the primary title or main topic of the lecture presented in the document.
2.  **Target Group:** Determine the target student group for the lecture. This group name **MUST** be exactly one of the following five strings: 'napredna', 'olimpijska', 'pocetna', 'predolimpijska', 'srednja'. Carefully analyze the document content; if you find variations (e.g., 'Olimpijska Grupa', 'Početna', 'Srednja grupa'), map it accurately to one of the five required standard names. Output only the standard name.
3.  **Problems (LaTeX):** Identify each distinct mathematical problem presented within the lecture. For each problem found, extract its complete and accurate LaTeX source code representation as a single string. Collect these LaTeX strings into a list.
4. The language is Bosnian."""),
        ],
    )

def process_single_pdf(client, pdf_path: Path, config: types.GenerateContentConfig):
    """Processes a single PDF file using the Gemini API and returns structured data."""
    logging.info(f"Processing PDF: {pdf_path.relative_to(project_root)}")
    try:
        # Read PDF binary content
        pdf_bytes = pdf_path.read_bytes()
        if not pdf_bytes:
            logging.warning(f"Skipping empty PDF: {pdf_path}")
            return None

        # Prepare contents using inline_data
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(inline_data=types.Blob(
                        mime_type="application/pdf",
                        data=pdf_bytes
                    )),
                    # Minimal text prompt is okay as instructions are in system_instruction
                    types.Part.from_text(text="Extract structured data from this PDF based on the provided schema and instructions."),
                ],
            ),
        ]

        # Call the API (synchronously for this script) and collect streamed response
        full_json_string = ""
        stream = client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=config,
        )
        for chunk in stream:
            if hasattr(chunk, 'text') and chunk.text:
                full_json_string += chunk.text

        # Parse the JSON response
        if not full_json_string:
            logging.warning(f"Received empty response string for {pdf_path}")
            return None

        extracted_data = json.loads(full_json_string)
        logging.info(f"Successfully extracted data for: {pdf_path.name}")
        return extracted_data

    except FileNotFoundError:
        logging.error(f"File not found during processing: {pdf_path}")
        return None
    except exceptions.ResourceExhausted as e:
        logging.error(f"Rate limit likely exceeded while processing {pdf_path}: {e}. Stopping.")
        raise # Re-raise to stop the script
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON response for {pdf_path}: {e}. Response: '{full_json_string[:500]}...'")
        return None # Skip this file
    except Exception as e:
        logging.error(f"An unexpected error occurred processing {pdf_path}: {e}", exc_info=True)
        return None # Skip this file


# --- Main Execution ---
if __name__ == "__main__":
    logging.info("--- Starting Ljetni Kamp PDF Processing ---")

    client = get_gemini_client(API_KEY)
    if not client:
        exit() # Stop if client fails to initialize

    config = get_generate_config()
    all_extracted_data = [] # List to store results from all PDFs

    if not INPUT_KAMP_DIR.is_dir():
        logging.error(f"Input directory not found: {INPUT_KAMP_DIR}")
        exit()

    logging.info(f"Scanning for PDF files in: {INPUT_KAMP_DIR}")
    pdf_files_found = list(INPUT_KAMP_DIR.rglob('*.pdf')) # Find all PDFs recursively
    total_pdfs = len(pdf_files_found)
    logging.info(f"Found {total_pdfs} PDF files to process.")

    for i, pdf_path in enumerate(pdf_files_found):
        logging.info(f"--- Processing file {i+1}/{total_pdfs} ---")
        try:
            result = process_single_pdf(client, pdf_path, config)

            if result:
                # Add source file path information to the result
                result['source_pdf'] = str(pdf_path.relative_to(DATA_DIR)) # Store relative path
                all_extracted_data.append(result)

            # Add delay even if processing failed for a file, before the next attempt
            if i < total_pdfs - 1: # Don't sleep after the last file
                 logging.info(f"Waiting {API_DELAY}s before next file...")
                 time.sleep(API_DELAY)

        except exceptions.ResourceExhausted:
             # Error already logged in process_single_pdf, exit loop
             break
        except Exception as e:
             # Catch any unexpected errors during the loop itself
             logging.error(f"Unexpected error in main loop for {pdf_path}: {e}", exc_info=True)
             # Optionally decide to continue or break here
             # break # Safer to stop if unexpected things happen

    # --- Save all collected data ---
    logging.info(f"--- Processing complete. Saving {len(all_extracted_data)} results ---")
    try:
        # Ensure output directory exists
        OUTPUT_JSON_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully saved all extracted data to: {OUTPUT_JSON_FILE}")

    except Exception as e:
        logging.error(f"Failed to save the final JSON output: {e}", exc_info=True)

    logging.info("--- Script Finished ---")