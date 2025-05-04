# server/routers/problemsets.py

import logging
import io # <-- Import io for StreamingResponse

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
# --- Import StreamingResponse ---
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from typing import List

# Import service classes and their potential exceptions
try:
    from ..services.gemini_service import GeminiService, GeminiServiceError, GeminiJSONError, GeminiResponseValidationError
    from ..services.problemset_service import ProblemsetService, ProblemsetServiceError
    # --- Import the new PDF service and its exceptions ---
    from ..services.pdf_service import get_problemset_pdf, PDFGenerationError, ProblemsetNotFound
except ImportError as e:
     logging.error(f"Failed to import service classes: {e}")
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
    from ..schemas.problemset import LectureProblemsOutput
    from ..schemas.problemset import ProblemsetSchema
    from ..schemas.problemset_problems import ProblemsetProblemsSchema
except ImportError as e:
    logging.error(f"Failed to import Pydantic schemas: {e}")
    raise

# Import SQLAlchemy ORM models
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
    tags=["Problemsets", "Lectures"] # Add Lectures tag if desired
)

# ... (keep your existing routes like /process-pdf, / and /{problemset_id}/lecture-data) ...
@router.get("/", response_model=List[ProblemsetSchema])
def all_problemsets(db: Session = Depends(get_db)):
    logger.info("Fetching all problemsets from DB.")
    problemsets_orm = db.query(Problemset).all()
    logger.info(f"Fetched {len(problemsets_orm)} problemsets.")
    return problemsets_orm

@router.get(
    "/{problemset_id}/lecture-data",
    response_model=ProblemsetSchema,
    summary="Get Data for a Specific Lecture (Problemset)",
    responses={
        404: {"description": "Problemset not found"},
    }
)
def get_lecture_data_by_id(
    problemset_id: int,
    db: Session = Depends(get_db)
) -> ProblemsetSchema:
    logger.info(f"Fetching data for problemset ID: {problemset_id}")
    problemset_orm = db.query(Problemset)\
        .options(
            joinedload(Problemset.problems)
            .joinedload(ProblemsetProblems.problem)
        )\
        .filter(Problemset.id == problemset_id)\
        .first() # Removed .filter(Problemset.type == 'predavanje') to fetch any type

    if not problemset_orm:
        logger.warning(f"Problemset with ID {problemset_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Problemset with ID {problemset_id} not found."
        )

    try:
        if problemset_orm.problems:
             problemset_orm.problems.sort(key=lambda link: link.position if link.position is not None else float('inf'))
             logger.debug(f"Sorted problems for problemset ID {problemset_id} by position.")
        else:
             logger.debug(f"No problems found for problemset ID {problemset_id} to sort.")
    except AttributeError as e:
         logger.error(f"AttributeError during sorting for problemset ID {problemset_id}: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Internal error processing problem order")
    except Exception as e:
        logger.error(f"Error sorting problems by position for problemset ID {problemset_id}: {e}", exc_info=True)
        pass

    logger.info(f"Successfully fetched data for problemset ID: {problemset_id}, Title: {problemset_orm.title}")
    return problemset_orm

@router.post(
    "/process-pdf",
    response_model=ProblemsetSchema,
    summary="Process PDF Lecture, Extract Data, and Save to Database",
    status_code=status.HTTP_201_CREATED
)
async def process_lecture_pdf_upload(
    file: UploadFile = File(..., description="PDF file containing the lecture and math problem"),
    gemini_service: GeminiService = Depends(get_gemini_service),
    lecture_service: ProblemsetService = Depends(get_lecture_service),
    db: Session = Depends(get_db)
) -> ProblemsetSchema:
    logger.info(f"Router: Received PDF file upload request: {file.filename} (type: {file.content_type})")
    if file.content_type != "application/pdf":
        logger.warning(f"Router: Invalid file type uploaded: {file.content_type}.")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Please upload a PDF file."
        )
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

    extracted_data: LectureProblemsOutput
    try:
        logger.info("Router: Calling GeminiService.process_lecture_pdf for extraction...")
        extracted_data = await gemini_service.process_lecture_pdf(pdf_bytes)
        logger.info("Router: Received extracted and validated data from GeminiService.")
    except (GeminiJSONError, GeminiResponseValidationError) as e:
        logger.error(f"Router: Service returned data validation error during extraction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing AI response data: {e}")
    except GeminiServiceError as e:
        logger.error(f"Router: Generic Gemini Service error during extraction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error from AI service: {e}")
    except Exception as e:
        logger.error(f"Router: An unexpected error occurred during extraction: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred during data extraction.")

    created_lecture_orm: Problemset
    try:
        logger.info("Router: Calling LectureService.create_lecture_and_problems to save to DB...")
        created_lecture_orm = lecture_service.create_problemset_from_ai_output(db=db, ai_data=extracted_data)
        logger.info(f"Router: Successfully saved lecture (ID: {created_lecture_orm.id}) and problems to DB.")
    except ProblemsetServiceError as e:
         logger.error(f"Router: Lecture Service error saving data to DB: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save extracted data to database: {e}")
    except Exception as e:
         logger.error(f"Router: An unexpected error occurred while saving data to DB: {e}", exc_info=True)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while saving data.")

    return created_lecture_orm

# --- NEW PDF DOWNLOAD ENDPOINT ---
@router.get(
    "/{problemset_id}/pdf",
    summary="Generate and Download PDF for a Problemset",
    response_class=StreamingResponse, # Use StreamingResponse for binary data
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Successful PDF generation and download.",
        },
        404: {"description": "Problemset not found."},
        500: {"description": "Internal server error during PDF generation."},
        503: {"description": "PDF generation service unavailable (e.g., pdflatex not found)."},
    }
)
async def download_problemset_pdf(
    problemset_id: int,
    db: Session = Depends(get_db)
):
    """
    Generates a PDF document for the specified problemset using LaTeX
    and returns it for download.
    """
    logger.info(f"PDF download request received for Problemset ID: {problemset_id}")
    try:
        # Call the service function to get the PDF bytes
        pdf_bytes = get_problemset_pdf(db, problemset_id)

        # Create a StreamingResponse
        # Wrap bytes in BytesIO for the stream interface
        pdf_stream = io.BytesIO(pdf_bytes)

        # Sanitize title for filename (replace spaces, remove unsafe chars)
        # Fetch title again or pass it from service (fetching again is simpler here)
        problemset = db.query(Problemset).filter(Problemset.id == problemset_id).first()
        safe_title = "problemset" # Default
        if problemset and problemset.title:
            safe_title = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in problemset.title.replace(' ', '_'))
        filename = f"{safe_title}_{problemset_id}.pdf"

        logger.info(f"Streaming PDF response for {filename}")
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={
                # Suggest a filename to the browser
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ProblemsetNotFound as e:
        logger.warning(f"Problemset not found for PDF generation (ID: {problemset_id}): {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    except FileNotFoundError as e: # Specifically catch if pdflatex isn't found
        logger.error(f"PDF generation prerequisite missing: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"PDF generation tool not found on server: {e}")

    except PDFGenerationError as e:
        logger.error(f"Error during PDF generation for Problemset ID {problemset_id}: {e}", exc_info=True)
        # Optionally include log details in production if safe, otherwise just a generic error
        # log_detail = f" Compilation Log: {e.log}" if e.log else "" # Be cautious exposing logs
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation failed: {e}") # {log_detail}

    except Exception as e:
        logger.exception(f"Unexpected error during PDF download for Problemset ID {problemset_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred generating the PDF.")
    
    