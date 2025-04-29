# server/routers/lectures.py

import logging

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
# Remove genai, types, json, run_in_threadpool as service handles them:
# from google import genai
# from google.genai import types
# import json
# from fastapi.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

# Import the service and its potential exceptions
try:
    from ..services.gemini_service import GeminiService, GeminiServiceError, GeminiJSONError, GeminiExtractionError
except ImportError as e:
     logging.error(f"Failed to import GeminiService from services: {e}")
     raise

# Import the service dependency provider
try:
    from ..dependencies import get_gemini_service
except ImportError as e:
    logging.error(f"Failed to import get_gemini_service from dependencies: {e}")
    raise


# Your APIRouter instance
router = APIRouter(
    prefix="/lectures", # Keep your prefix
    tags=["Lecture Management"]
)

# Your existing hello route
@router.get(
    "/hello",
    summary="Basic Hello endpoint",
)
async def read_lectures_hello():
    logger.info("Hello endpoint accessed.")
    return {"message": "Hello from the Lectures router"}


# --- The Process PDF Route (Simplified) ---
@router.post(
    "/process-pdf",
    # REMOVED: response_model=LectureProblemsOutput, # Still returning raw JSON
    summary="Process PDF Lecture and Extract Problems (Returns Raw JSON)",
)
async def process_lecture_pdf_upload(
    file: UploadFile = File(..., description="PDF file containing the lecture and math problem"),
    # Inject the GeminiService instance instead of the raw client
    gemini_service: GeminiService = Depends(get_gemini_service)
):
    """
    Receives a PDF file, uses the GeminiService to process it, and returns
    the extracted JSON data.
    """
    logger.info(f"Router: Received PDF file upload request: {file.filename} (type: {file.content_type})")

    # --- 1. File Validation (kept in router) ---
    if file.content_type != "application/pdf":
        logger.warning(f"Router: Invalid file type uploaded: {file.content_type}.")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Please upload a PDF file."
        )

    # --- 2. Read File Content (kept in router) ---
    try:
        pdf_bytes = await file.read()
        if not pdf_bytes:
             raise ValueError("Uploaded PDF file is empty.")
        logger.info(f"Router: Read {len(pdf_bytes)} bytes from uploaded file '{file.filename}'.")
    except Exception as e:
        logger.error(f"Router: Failed to read uploaded file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {e}"
        )
    finally:
        await file.close()

    # --- 3. Call the Service Method ---
    try:
        logger.info("Router: Calling GeminiService.process_lecture_pdf...")
        # Pass the raw bytes to the service
        extracted_data = await gemini_service.process_lecture_pdf(pdf_bytes)
        logger.info("Router: Received data from GeminiService.")
        # Return the result - FastAPI will serialize the dictionary to JSON
        return extracted_data

    except GeminiJSONError as e:
        logger.error(f"Router: Service returned JSON error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) # Use service error detail

    except GeminiServiceError as e:
        logger.error(f"Router: Service error during PDF processing: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error from AI service: {e}")

    except Exception as e:
        logger.error(f"Router: An unexpected error occurred: {e}", exc_info=True)
        # Catch any other unexpected errors and return a generic server error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred.")


# Keep other router definitions or code below if any
# You would create server/routers/translation.py and server/routers/conversion.py
# following this pattern (import service, define router, define routes, call service methods, handle errors)
# and include them in main.py
# @router.include_router(...)