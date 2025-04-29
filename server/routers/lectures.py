# To run this code you need to install the following dependencies:
# pip install google-genai python-dotenv uvicorn[standard] fastapi

# Keep existing imports:
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
# Remove if not used: from sqlalchemy.orm import Session
# Remove if not used for response validation: from pydantic import BaseModel

import base64 # Might not be needed anymore, can remove
from google import genai
from google.genai import types
import dotenv # Assuming you load dotenv here for the API key
import os


import logging

logger = logging.getLogger(__name__) # Use __name__ for logger name


# Add necessary imports:
import json # For parsing the JSON response
import io # For BytesIO
from fastapi.concurrency import run_in_threadpool # Needed for sync operations


dotenv.load_dotenv()

# Your existing get_gemini_client helper
def get_gemini_client():
    """Instantiates and returns the Gemini client using API Key."""
    # Basic check, can be expanded later
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
         # In a real app, this check should be done on startup
         print("GEMINI_API_KEY not found.") # Minimal feedback
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="API Key missing")
    return genai.Client(api_key=api_key)

# Your original generate function - keep it for reference, or remove if only used for testing
# def generate():
#     client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
#     ... (your generate function code) ...


# Your APIRouter instance
router = APIRouter(
    prefix="/lectures",
    tags=["Lecture Management"]
)

# Your existing hello route
@router.get(
    "/hello",
    summary="Basic Hello endpoint",
)
async def read_lectures_hello():
    return {"message": "Hello from the Lectures router"}

@router.post(
    "/process-pdf",
    # REMOVED: response_model=LectureProblemsOutput, # Removed to return raw JSON as requested
    summary="Process PDF Lecture and Extract Problems (Returns Raw JSON)",
)
async def process_lecture_pdf_upload(
    file: UploadFile = File(..., description="PDF file containing the lecture and math problem"),
    # Inject the Gemini client using FastAPI's dependency injection
    gemini_client: genai.Client = Depends(get_gemini_client)
):
    """
    Receives a PDF file, sends its content directly to the Gemini API,
    requests extraction of the lecture details and problems, and returns
    the raw JSON dictionary received from the AI.
    """
    logger.info(f"Received PDF file upload request: {file.filename} (type: {file.content_type})")

    # --- 1. File Validation ---
    # Basic MIME type validation for PDF
    if file.content_type != "application/pdf":
        logger.warning(f"Invalid file type uploaded: {file.content_type}. Expected application/pdf.")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Please upload a PDF file."
        )

    # --- 2. Read File Content ---
    # Read the binary data from the uploaded file
    try:
        pdf_bytes = await file.read()
        if not pdf_bytes:
             raise ValueError("Uploaded PDF file is empty.")
        logger.info(f"Read {len(pdf_bytes)} bytes from uploaded file '{file.filename}'.")
    except Exception as e:
        logger.error(f"Failed to read uploaded file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {e}"
        )
    finally:
        # Ensure the file handle is closed
        await file.close()


    # --- 3. Prepare Contents using Inline Data (like image-to-latex) ---
    # Model name from your generate() and main.py samples
    model = "gemini-2.5-flash-preview-04-17"

    # Construct contents with the PDF binary data using Blob and a text prompt
    contents = [
        types.Content(
            role="user",
            parts=[
                # Part 1: The PDF binary data using Blob (similar to your image route)
                types.Part(inline_data=types.Blob(
                    mime_type="application/pdf", # Specify PDF MIME type
                    data=pdf_bytes # The bytes read from the file
                )),
                # Part 2: A text prompt instructing the model what to do
                types.Part.from_text(text="""Extract the lecture name, target group, and all distinct math problems in LaTeX format from this PDF document. Return the output as a JSON object conforming to the specified schema."""),
            ],
        ),
    ]
    logger.debug("Constructed multi-part contents (PDF bytes + text prompt) for Gemini API using inline_data.")


    # --- 4. Define generation config (like in generate()) ---
    # This configuration block is copied directly from your working generate() function
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["lecture_name", "group_name", "problems_latex"],
            properties = {
                "lecture_name": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The main title or name of the lecture topic found in the document.",
                ),
                "group_name": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The target group for the lecture (e.g., 'Početna grupa', 'Srednja grupa', 'Napredna grupa', 'Predolimpijska grupa', 'Olimpijska grupa').",
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
        # System instruction (Exactly as in your sample)
        system_instruction=[
            types.Part.from_text(text="""You are an extraction engine for math lectures. You translate PDFs into JSON of the lecture, and problems in the lecture in Latex."""),
        ],
    )
    logger.debug("Defined generate_content_config with JSON schema and system instruction.")


    # --- 5. Call generate_content_stream and collect response (like in generate()) ---
    # client.models.generate_content_stream is synchronous -> use run_in_threadpool
    full_json_string = ""
    try:
        logger.info(f"Calling Gemini model '{model}' via Client API (streaming)...")

        # Define a sync function to run in the threadpool
        # This is needed because the Gemini client streaming is often synchronous
        # and iterating over it would block the async event loop.
        def get_streamed_response_text():
            text = ""
            # Call the synchronous streaming method from within the thread
            stream = gemini_client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            )
            # Iterate and collect text chunks from the synchronous stream
            for chunk in stream:
                if hasattr(chunk, 'text') and chunk.text:
                    text += chunk.text
            return text

        # Run the synchronous iteration logic in a separate thread
        full_json_string = await run_in_threadpool(get_streamed_response_text)

        logger.info("Finished receiving streamed response from Gemini.")
        # Log a snippet of the received string for debugging
        logger.debug(f"Full raw JSON string received (first 500 chars): {full_json_string[:500]}...")

    except Exception as e:
        logger.error(f"An error occurred during the Gemini content generation API call or streaming: {e}", exc_info=True)
        # Re-raise as HTTPException to return an error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content from AI service: {e}" # Provide error detail
        )

    # --- Cleanup: No file deletion needed with inline_data ---
    # If you were using client.files.upload, deletion would go here.
    # With inline_data, the data is sent directly in the request and not stored in the file service.
    logger.debug("Using inline_data, no file deletion needed.")


    # --- 6. Parse the collected JSON string ---
    if not full_json_string:
        logger.warning("Received empty response string from Gemini.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service returned an empty response."
        )

    try:
        # Parse the string as JSON
        parsed_data = json.loads(full_json_string)
        logger.info("Successfully parsed Gemini response as JSON.")
        # RETURN THE PARSED DICTIONARY DIRECTLY
        return parsed_data # FastAPI will convert this dict to JSON

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from Gemini: {e}", exc_info=True)
        logger.debug(f"Faulty JSON string that failed parsing: {full_json_string}") # Log the string that failed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or potentially 502 Bad Gateway if it's an external service issue
            detail=f"AI service returned invalid JSON: {e}" # Include JSON error detail
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred after JSON parsing: {e}", exc_info=True)
        raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="An internal error occurred processing the AI response."
        )