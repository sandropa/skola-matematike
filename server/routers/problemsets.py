# server/routers/problemsets.py

import logging
import io

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError # Import SQLAlchemyError for handling DB errors

from typing import List

# Import service classes and their potential exceptions
try:
    from ..services.gemini_service import GeminiService, GeminiServiceError, GeminiJSONError, GeminiResponseValidationError
    # Import the ProblemsetService *class* for AI processing
    from ..services.problemset_service import ProblemsetService, ProblemsetServiceError
    # Import the standalone CRUD service functions
    from ..services import problemset_service
    from ..services.pdf_service import get_problemset_pdf, PDFGenerationError, ProblemsetNotFound
except ImportError as e:
     logging.error(f"Failed to import service classes/functions: {e}")
     raise

# Import dependency providers
try:
    from ..dependencies import get_gemini_service, get_lecture_service
    from ..database import get_db
except ImportError as e:
    logging.error(f"Failed to import dependencies: {e}")
    raise

# Import Pydantic schemas
try:
    # AI Processing Schema
    from ..schemas.problemset import LectureProblemsOutput
    # CRUD Schemas
    from ..schemas.problemset import ProblemsetSchema, ProblemsetCreate, ProblemsetUpdate
    # Association Schema (needed for ProblemsetSchema)
    from ..schemas.problemset_problems import ProblemsetProblemsSchema
except ImportError as e:
    logging.error(f"Failed to import Pydantic schemas: {e}")
    raise

# Import SQLAlchemy ORM models (needed for lecture-data route's query)
try:
    from ..models.problemset import Problemset
    from ..models.problem import Problem
    from ..models.problemset_problems import ProblemsetProblems
except ImportError as e:
    logging.error(f"Failed to import SQLAlchemy models: {e}")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/problemsets",
    tags=["Problemsets"], # Keep tag concise
    responses={404: {"description": "Problemset not found"}} # Default 404 response
)

# --- Standard CRUD Endpoints ---

@router.post(
    "/",
    response_model=ProblemsetSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create New Problemset"
)
def create_new_problemset(
    problemset: ProblemsetCreate,
    db: Session = Depends(get_db)
):
    """Create a new problemset entry in the database."""
    logger.info(f"Router: Request received for POST /problemsets (Title: {problemset.title})")
    try:
        created_problemset = problemset_service.create(db=db, problemset=problemset)
        logger.info(f"Router: Problemset created successfully with id {created_problemset.id}")
        return created_problemset
    except (SQLAlchemyError, ProblemsetServiceError) as e: # Catch DB or Service errors
         logger.error(f"Router: Database/Service error during problemset creation: {e}", exc_info=True)
         # Use a more specific error detail if possible, otherwise generic
         detail = f"Database error occurred: {e}" if isinstance(e, SQLAlchemyError) else str(e)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
    except Exception as e:
        logger.error(f"Router: Unexpected error during problemset creation: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


# --- Modified GET / to use service ---
@router.get(
    "/",
    response_model=List[ProblemsetSchema],
    summary="Get All Problemsets"
)
def read_all_problemsets(db: Session = Depends(get_db)):
    """Retrieve a list of all problemsets."""
    logger.info("Router: Request received for GET /problemsets")
    try:
        problemsets = problemset_service.get_all(db)
        logger.info(f"Router: Returning {len(problemsets)} problemsets.")
        return problemsets
    except ProblemsetServiceError as e: # Catch potential service errors
        logger.error(f"Router: Service error fetching all problemsets: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Router: Unexpected error fetching all problemsets: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get(
    "/{problemset_id}",
    response_model=ProblemsetSchema,
    summary="Get Problemset by ID"
)
def read_problemset(problemset_id: int, db: Session = Depends(get_db)):
    """Retrieve a single problemset by its ID."""
    logger.info(f"Router: Request received for GET /problemsets/{problemset_id}")
    try:
        problemset = problemset_service.get_one(db, problemset_id)
        if problemset is None:
            logger.warning(f"Router: Problemset with id {problemset_id} not found.")
            # Raise the 404 exception here
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problemset not found")
        logger.info(f"Router: Returning problemset with id {problemset_id}.")
        return problemset
    except ProblemsetServiceError as e:
        logger.error(f"Router: Service error fetching problemset id {problemset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    # --- ADDED: Catch HTTPException specifically and re-raise ---
    except HTTPException as http_exc:
        raise http_exc # Let FastAPI handle specific HTTP exceptions we raised
    # --- END ADDED BLOCK ---
    except Exception as e: # Generic handler for other unexpected errors
        logger.error(f"Router: Unexpected error fetching problemset id {problemset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")
    

@router.put(
    "/{problemset_id}",
    response_model=ProblemsetSchema,
    summary="Update Existing Problemset"
)
def update_existing_problemset(
    problemset_id: int,
    problemset_update: ProblemsetUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing problemset identified by its ID."""
    logger.info(f"Router: Request received for PUT /problemsets/{problemset_id}")
    try:
        updated_problemset = problemset_service.update(db=db, problemset_id=problemset_id, problemset_update=problemset_update)
        if updated_problemset is None:
            logger.warning(f"Router: Problemset with id {problemset_id} not found for update.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problemset not found")
        logger.info(f"Router: Problemset {problemset_id} updated successfully.")
        return updated_problemset
    except (SQLAlchemyError, ProblemsetServiceError) as e:
         logger.error(f"Router: Database/Service error during problemset update (id: {problemset_id}): {e}", exc_info=True)
         detail = f"Database error occurred: {e}" if isinstance(e, SQLAlchemyError) else str(e)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
    except HTTPException as http_exc:
         raise http_exc # Re-raise 404 if raised explicitly
    except Exception as e:
        logger.error(f"Router: Unexpected error during problemset update (id: {problemset_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.delete(
    "/{problemset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Problemset"
)
def delete_existing_problemset(problemset_id: int, db: Session = Depends(get_db)):
    """Delete a problemset identified by its ID."""
    logger.info(f"Router: Request received for DELETE /problemsets/{problemset_id}")
    try:
        success = problemset_service.delete(db=db, problemset_id=problemset_id)
        if not success:
            logger.warning(f"Router: Problemset with id {problemset_id} not found for deletion.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problemset not found")
        logger.info(f"Router: Problemset {problemset_id} deleted successfully.")
        # No content returned on successful deletion
        return None
    except (SQLAlchemyError, ProblemsetServiceError) as e:
        logger.error(f"Router: Database/Service error during problemset deletion (id: {problemset_id}): {e}", exc_info=True)
        detail = f"Database error occurred: {e}" if isinstance(e, SQLAlchemyError) else str(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
    except HTTPException as http_exc:
        raise http_exc # Re-raise 404 if raised explicitly
    except Exception as e:
        logger.error(f"Router: Unexpected error during problemset deletion (id: {problemset_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# --- Existing Lecture/PDF Specific Endpoints (Keep as is) ---

@router.get(
    "/{problemset_id}/lecture-data",
    response_model=ProblemsetSchema,
    summary="Get Eagerly Loaded Data for a Specific Problemset (e.g., Lecture)",
    tags=["Lectures"], # Specific tag for lecture-related endpoints
    responses={
        404: {"description": "Problemset not found"},
    }
)
def get_lecture_data_by_id(
    problemset_id: int,
    db: Session = Depends(get_db)
) -> ProblemsetSchema:
    """Retrieves a specific problemset with its associated problems eagerly loaded."""
    logger.info(f"Fetching EAGER data for problemset ID: {problemset_id}")
    problemset_orm = db.query(Problemset)\
        .options(
            joinedload(Problemset.problems) # Eager load links
            .joinedload(ProblemsetProblems.problem) # Eager load problems via links
        )\
        .filter(Problemset.id == problemset_id)\
        .first()

    if not problemset_orm:
        logger.warning(f"Problemset with ID {problemset_id} not found (for lecture-data).")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problemset with ID {problemset_id} not found."
        )

    # Sort problems by position (important for lectures)
    try:
        if problemset_orm.problems:
             problemset_orm.problems.sort(key=lambda link: link.position if link.position is not None else float('inf'))
             logger.debug(f"Sorted problems for problemset ID {problemset_id} by position.")
        else:
             logger.debug(f"No problems found for problemset ID {problemset_id} to sort.")
    except Exception as e:
        logger.error(f"Error sorting problems by position for problemset ID {problemset_id}: {e}", exc_info=True)
        # Decide if this should be a 500 error or just proceed unsorted
        # raise HTTPException(status_code=500, detail="Internal error processing problem order")

    logger.info(f"Successfully fetched EAGER data for problemset ID: {problemset_id}, Title: {problemset_orm.title}")
    return problemset_orm


@router.post(
    "/process-pdf",
    response_model=ProblemsetSchema,
    summary="Process PDF Lecture, Extract Data, and Save to Database",
    tags=["Lectures", "AI Processing"], # Add AI tag
    status_code=status.HTTP_201_CREATED
)
async def process_lecture_pdf_upload(
    file: UploadFile = File(..., description="PDF file containing the lecture and math problem"),
    # Use the ProblemsetService CLASS instance for AI processing method
    gemini_service: GeminiService = Depends(get_gemini_service), # Keep for potential other AI use
    lecture_service: ProblemsetService = Depends(get_lecture_service), # Get instance of the class
    db: Session = Depends(get_db)
) -> ProblemsetSchema:
    """Processes a PDF, extracts lecture/problem data using AI, and saves it."""
    # (Keep the existing implementation, ensuring it calls the CLASS method)
    logger.info(f"Router: Received PDF file upload request: {file.filename} (type: {file.content_type})")
    if file.content_type != "application/pdf":
        logger.warning(f"Router: Invalid file type uploaded: {file.content_type}.")
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported file type: PDF only.")
    try:
        pdf_bytes = await file.read()
        if not pdf_bytes: raise ValueError("Uploaded PDF file is empty.")
        logger.info(f"Router: Read {len(pdf_bytes)} bytes from '{file.filename}'.")
    except Exception as e:
        logger.error(f"Router: Failed to read uploaded file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read uploaded file: {e}")
    finally:
        await file.close()

    extracted_data: LectureProblemsOutput
    try:
        logger.info("Router: Calling GeminiService.process_lecture_pdf for extraction...")
        extracted_data = await gemini_service.process_lecture_pdf(pdf_bytes) # Assumes GeminiService handles AI part
        logger.info("Router: Received extracted data from GeminiService.")
    except (GeminiJSONError, GeminiResponseValidationError, GeminiServiceError) as e:
        logger.error(f"Router: AI Service error during extraction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing AI response: {e}")
    except Exception as e:
        logger.error(f"Router: Unexpected error during extraction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error during data extraction.")

    created_lecture_orm: Problemset
    try:
        logger.info("Router: Calling ProblemsetService CLASS method create_problemset_from_ai_output...")
        # Call the method on the CLASS instance obtained via dependency injection
        created_lecture_orm = lecture_service.create_problemset_from_ai_output(db=db, ai_data=extracted_data)
        logger.info(f"Router: Successfully saved lecture (ID: {created_lecture_orm.id}) and problems.")
    except ProblemsetServiceError as e:
         logger.error(f"Router: Problemset Service error saving data: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save extracted data: {e}")
    except Exception as e:
         logger.error(f"Router: Unexpected error while saving data: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error while saving data.")

    return created_lecture_orm


@router.get(
    "/{problemset_id}/pdf",
    summary="Generate and Download PDF for a Problemset",
    tags=["PDF Generation"], # Specific tag
    response_class=StreamingResponse,
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Successful PDF download."},
        404: {"description": "Problemset not found."},
        500: {"description": "Internal server error during PDF generation."},
        503: {"description": "PDF generation service unavailable."},
    }
)
async def download_problemset_pdf(
    problemset_id: int,
    db: Session = Depends(get_db)
):
    """Generates and returns a PDF for the specified problemset."""
    # (Keep existing implementation)
    logger.info(f"PDF download request received for Problemset ID: {problemset_id}")
    try:
        pdf_bytes = get_problemset_pdf(db, problemset_id)
        pdf_stream = io.BytesIO(pdf_bytes)
        problemset = db.query(Problemset).filter(Problemset.id == problemset_id).first()
        safe_title = "problemset"
        if problemset and problemset.title:
            safe_title = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in problemset.title.replace(' ', '_'))
        filename = f"{safe_title}_{problemset_id}.pdf"
        logger.info(f"Streaming PDF response for {filename}")
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ProblemsetNotFound as e:
        logger.warning(f"PDF Gen: Problemset not found (ID: {problemset_id}): {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileNotFoundError as e:
        logger.error(f"PDF Gen: Prerequisite missing: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"PDF generation tool missing: {e}")
    except PDFGenerationError as e:
        logger.error(f"PDF Gen Error (ID: {problemset_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation failed: {e}")
    except Exception as e:
        logger.exception(f"Unexpected PDF download error (ID: {problemset_id}): {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error generating PDF.")