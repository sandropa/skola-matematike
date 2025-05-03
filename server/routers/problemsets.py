import logging

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session # Import Session type for the database dependency

from typing import List

# Import service classes and their potential exceptions
try:
    from ..services.gemini_service import GeminiService, GeminiServiceError, GeminiJSONError, GeminiResponseValidationError
    from ..services.problemset_service import ProblemsetService, ProblemsetServiceError # Import the new service and its errors
except ImportError as e:
     logging.error(f"Failed to import service classes: {e}")
     raise

# Import dependency providers
try:
    # Import dependencies for both services and the database session
    from ..dependencies import get_gemini_service, get_lecture_service
    from ..database import get_db # Import the database session dependency
except ImportError as e:
    logging.error(f"Failed to import dependencies: {e}")
    raise

# Import Pydantic schemas
try:
    # We need LectureProblemsOutput schema to define the type received from GeminiService
    from ..schemas.problemset import LectureProblemsOutput
    # We need LectureSchema schema to define the API response structure
    from ..schemas.problemset import ProblemsetSchema # Import the Pydantic schema for Lecture
except ImportError as e:
    logging.error(f"Failed to import Pydantic schemas: {e}")
    raise


# Import the SQLAlchemy ORM model for Lecture
try:
    from ..models.problemset import Problemset # Import the SQLAlchemy Lecture model
except ImportError as e:
    logging.error(f"Failed to import SQLAlchemy Lecture model: {e}")
    raise


logger = logging.getLogger(__name__)

# APIRouter instance
router = APIRouter(
    prefix="/problemsets", # Keep your prefix
    tags=["Problemsets"]
)

@router.get("/", response_model=List[ProblemsetSchema])
def all_problemsets(db: Session = Depends(get_db)):
    logger.info("Fetching all problemsets from DB.")
    problemsets_orm = db.query(Problemset).all()
    logger.info(f"Fetched {len(problemsets_orm)} problemsets.")
    return problemsets_orm

# --- The Process PDF Route (Saves to DB) ---
@router.post(
    "/process-pdf",
    # --- Set response_model to the LectureSchema ---
    response_model=ProblemsetSchema, # API returns the created Lecture object (serialized by this schema)
    summary="Process PDF Lecture, Extract Data, and Save to Database",
    status_code=status.HTTP_201_CREATED # Use 201 Created for resource creation
)
# --- Add dependencies for services and DB session ---
async def process_lecture_pdf_upload(
    file: UploadFile = File(..., description="PDF file containing the lecture and math problem"),
    gemini_service: GeminiService = Depends(get_gemini_service), # Inject the Gemini service
    lecture_service: ProblemsetService = Depends(get_lecture_service), # Inject the new Lecture service
    db: Session = Depends(get_db) # Inject the database session for this request
) -> ProblemsetSchema: # Update return type hint
    """
    Receives a PDF file, uses the GeminiService to extract data,
    uses the LectureService to save the extracted data to the database,
    and returns the created Lecture object (serialized by LectureSchema).
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

    # --- 3. Call the Gemini Service to Extract Data ---
    extracted_data: LectureProblemsOutput # Type hint for clarity
    try:
        logger.info("Router: Calling GeminiService.process_lecture_pdf for extraction...")
        # Call the Gemini service, which returns a validated LectureProblemsOutput Pydantic instance
        extracted_data = await gemini_service.process_lecture_pdf(pdf_bytes)
        logger.info("Router: Received extracted and validated data from GeminiService.")

    # --- Error handling for the Gemini Service call ---
    # Catch specific errors raised by the GeminiService methods
    except (GeminiJSONError, GeminiResponseValidationError) as e:
        logger.error(f"Router: Service returned data validation error during extraction: {e}", exc_info=True)
        # 500 Internal Server Error indicates the *AI's response* had an issue
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing AI response data: {e}")

    except GeminiServiceError as e:
        logger.error(f"Router: Generic Gemini Service error during extraction: {e}", exc_info=True)
         # 500 for other AI service failures (connection, API error, etc.)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error from AI service: {e}")

    except Exception as e:
        logger.error(f"Router: An unexpected error occurred during extraction: {e}", exc_info=True)
        # Catch any other unexpected errors during the extraction process
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred during data extraction.")


    # --- 4. Call the Lecture Service to Save Data to DB ---
    created_lecture_orm: Problemset # Type hint for clarity (SQLAlchemy model)
    try:
        logger.info("Router: Calling LectureService.create_lecture_and_problems to save to DB...")
        # Pass the DB session (injected by Depends) and the extracted Pydantic data (from GeminiService)
        created_lecture_orm = lecture_service.create_problemset_from_ai_output(db=db, ai_data=extracted_data)
        logger.info(f"Router: Successfully saved lecture (ID: {created_lecture_orm.id}) and problems to DB.")

    # --- Error handling for the Database Service call ---
    # Catch specific errors raised by the LectureService methods
    except ProblemsetServiceError as e:
         logger.error(f"Router: Lecture Service error saving data to DB: {e}", exc_info=True)
         # A DB error should generally be a 500 Internal Server Error
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save extracted data to database: {e}")

    except Exception as e:
         # Catch any other unexpected errors during the DB saving process
         logger.error(f"Router: An unexpected error occurred while saving data to DB: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while saving data.")


    # --- 5. Return the Created ORM Object ---
    # FastAPI will automatically serialize the SQLAlchemy ORM object (created_lecture_orm)
    # using the LectureSchema defined in the 'response_model' decorator parameter.
    # Because LectureSchema has orm_mode=True and includes the 'problems' relationship
    # (which itself uses ProblemSchema with orm_mode=True), FastAPI will traverse
    # the ORM object's relationships and build the correct JSON response.
    return created_lecture_orm
