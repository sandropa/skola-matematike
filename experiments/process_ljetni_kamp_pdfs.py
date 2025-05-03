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

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API Key from .env file located at the project root
project_root = Path(__file__).resolve().parent.parent
dotenv_path = project_root / '.env'
logging.info(f"Loading .env file from: {dotenv_path}")
dotenv.load_dotenv(dotenv_path=dotenv_path)

API_KEY = os.getenv("GEMINI_API_KEY")

# Define the model name
MODEL_NAME = "gemini-2.5-flash-preview-04-17" # Your working model

# Define input and output paths relative to the project root
DATA_DIR = project_root / 'experiments' / 'data'
INPUT_KAMP_DIR = DATA_DIR / 'ljetni_kamp'
OUTPUT_JSON_FILE = DATA_DIR / 'ljetni_kamp_extracted_data_with_category.json' # Changed output filename

# Delay between API calls (seconds) - adjust as needed
API_DELAY = 10 # Keep delay, might need increase if calls are more complex
# --- End Configuration ---


def get_gemini_client(api_key):
    """Initializes and returns the Gemini client."""
    if not api_key:
        logging.error("GEMINI_API_KEY not found. Please set it in your .env file.")
        return None
    try:
        client = genai.Client(api_key=api_key)
        logging.info("Gemini client initialized successfully.")
        return client
    except Exception as e:
        logging.error(f"Failed to initialize Gemini client: {e}", exc_info=True)
        return None


def get_generate_config_with_category(): # Renamed function for clarity
    """Returns the GenerateContentConfig object expecting problem categories."""
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        # --- Updated response_schema ---
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["lecture_name", "group_name", "problems_latex"],
            properties = {
                "lecture_name": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The main title or name/topic of the lecture found in the document."
                ),
                "group_name": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The target group for the lecture, mapped precisely to one of the five allowed values.",
                    enum = ["napredna", "olimpijska", "pocetna", "predolimpijska", "srednja"]
                ),
                # --- Modify problems_latex property ---
                "problems_latex": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    description = "A list of objects, each containing the LaTeX source and category for a distinct problem.",
                    # Define the structure of objects WITHIN the array
                    items = genai.types.Schema(
                        type = genai.types.Type.OBJECT,
                        # Define properties of the objects in the array
                        properties = {
                            'latex_text': genai.types.Schema(
                                type=genai.types.Type.STRING,
                                description="The full LaTeX representation of a single math problem."
                            ),
                            'category': genai.types.Schema(
                                type=genai.types.Type.STRING,
                                description="The category of the problem (A, N, G, or C).",
                                # Add enum constraint for the category within the items
                                enum = ['A', 'N', 'G', 'C']
                            )
                        },
                        # Define required fields for each object in the array
                        required = ['latex_text', 'category']
                    ) # End of items schema
                ), # End of problems_latex property
                # --- End modification ---
            }, # End of top-level properties
        ), # End of top-level schema
        # --- Updated System instruction ---
        system_instruction=[
            types.Part.from_text(text="""You are a highly accurate extraction engine specializing in mathematical lecture documents (PDFs) from math camps. Your task is to parse the provided PDF and extract the following specific pieces of information:

1.  **Lecture Title:** Identify and extract the primary title or main topic of the lecture presented in the document.
2.  **Target Group:** Determine the target student group for the lecture. This group name **MUST** be exactly one of the following five strings: 'napredna', 'olimpijska', 'pocetna', 'predolimpijska', 'srednja'. Map variations accurately to one of these.
3.  **Problems:** Identify each distinct mathematical problem. For each problem, provide its full LaTeX source code AND its most likely category ('A' for Algebra, 'N' for Number Theory, 'G' for Geometry, or 'C' for Combinatorics). Collect this information as a list of objects, where each object contains the LaTeX and the category.
4.  The language of the document is typically Bosnian/Serbo-Croatian.

Adhere strictly to the provided JSON output schema."""),
        ],
    ) # End of GenerateContentConfig


def process_single_pdf(client, pdf_path: Path, config: types.GenerateContentConfig):
    """Processes a single PDF file using the Gemini API and returns structured data."""
    logging.info(f"Processing PDF: {pdf_path.relative_to(project_root)}")
    try:
        pdf_bytes = pdf_path.read_bytes()
        if not pdf_bytes:
            logging.warning(f"Skipping empty PDF: {pdf_path}")
            return None

        # Prepare contents using inline_data (prompt can be simpler now)
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(inline_data=types.Blob(
                        mime_type="application/pdf",
                        data=pdf_bytes
                    )),
                    # Simple text prompt sufficient as details are in system prompt + schema
                    types.Part.from_text(text="Extract lecture title, group, and list of problems (including LaTeX and category 'A', 'N', 'G', or 'C') according to the schema."),
                ],
            ),
        ]

        # Call the API and collect streamed response
        full_json_string = ""
        stream = client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=contents,
            config=config, # Pass the config with updated schema
        )
        for chunk in stream:
            if hasattr(chunk, 'text') and chunk.text:
                full_json_string += chunk.text

        # Parse the JSON response
        if not full_json_string:
            logging.warning(f"Received empty response string for {pdf_path}")
            return None

        extracted_data = json.loads(full_json_string)
        # Basic validation (does it have the required keys?)
        if not all(k in extracted_data for k in ["lecture_name", "group_name", "problems_latex"]):
             logging.warning(f"Extracted data missing required keys for {pdf_path}. Data: {extracted_data}")
             return None
        # Check if problems_latex is a list
        if not isinstance(extracted_data.get("problems_latex"), list):
             logging.warning(f"Extracted 'problems_latex' is not a list for {pdf_path}. Data: {extracted_data}")
             return None

        logging.info(f"Successfully extracted data (including categories) for: {pdf_path.name}")
        return extracted_data

    # --- Keep Error Handling ---
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
    logging.info("--- Starting Ljetni Kamp PDF Processing (with Categories) ---")

    client = get_gemini_client(API_KEY)
    if not client:
        exit()

    # Get the updated config
    config = get_generate_config_with_category()
    all_extracted_data = []

    if not INPUT_KAMP_DIR.is_dir():
        logging.error(f"Input directory not found: {INPUT_KAMP_DIR}")
        exit()

    logging.info(f"Scanning for PDF files in: {INPUT_KAMP_DIR}")
    pdf_files_found = list(INPUT_KAMP_DIR.rglob('*.pdf'))
    total_pdfs = len(pdf_files_found)
    logging.info(f"Found {total_pdfs} PDF files to process.")

    for i, pdf_path in enumerate(pdf_files_found):
        logging.info(f"--- Processing file {i+1}/{total_pdfs} ---")
        try:
            # Pass the updated config to the processing function
            result = process_single_pdf(client, pdf_path, config)

            if result:
                # Add source file path information
                result['source_pdf'] = str(pdf_path.relative_to(DATA_DIR))
                all_extracted_data.append(result)

            # Delay
            if i < total_pdfs - 1:
                 logging.info(f"Waiting {API_DELAY}s before next file...")
                 time.sleep(API_DELAY)

        except exceptions.ResourceExhausted:
             logging.info("Rate limit hit. Stopping processing.")
             break # Exit loop gracefully
        except Exception as e:
             logging.error(f"Unexpected error in main loop for {pdf_path}: {e}", exc_info=True)
             break # Stop on other major errors

    # --- Save all collected data ---
    logging.info(f"--- Processing complete. Saving {len(all_extracted_data)} results ---")
    try:
        OUTPUT_JSON_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_extracted_data, f, indent=2, ensure_ascii=False)
        logging.info(f"Successfully saved all extracted data to: {OUTPUT_JSON_FILE}")
    except Exception as e:
        logging.error(f"Failed to save the final JSON output: {e}", exc_info=True)

    logging.info("--- Script Finished ---")