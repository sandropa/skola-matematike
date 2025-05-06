# server/routers/problemsets.py

import logging
import io

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query 
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError 

from typing import List, Optional 

# Import Request Body model for reordering
from pydantic import BaseModel, Field

# Import service classes and their potential exceptions
try:
    from ..services.gemini_service import GeminiService, GeminiServiceError, GeminiJSONError, GeminiResponseValidationError
    from ..services.problemset_service import ProblemsetService, ProblemsetServiceError
    from ..services import problemset_service 
    from ..services import problem_service 
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
    from ..schemas.problemset import LectureProblemsOutput
    from ..schemas.problemset import ProblemsetSchema, ProblemsetCreate, ProblemsetUpdate
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

# --- Request Body Model for Reordering ---
class ReorderProblemsPayload(BaseModel):
    problem_ids_ordered: List[int] = Field(..., examples=[[3, 1, 2]])

router = APIRouter(
    prefix="/problemsets",
    tags=["Problemsets"], 
    responses={404: {"description": "Problemset not found"}} 
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
    logger.info(f"Router: Request received for POST /problemsets (Title: {problemset.title})")
    try:
        created_problemset = problemset_service.create(db=db, problemset=problemset)
        logger.info(f"Router: Problemset created successfully with id {created_problemset.id}")
        # Eagerly load relationships for the response model
        db.refresh(created_problemset)
        if hasattr(Problemset, 'problems'):
             db.query(Problemset).options(joinedload(Problemset.problems)).filter(Problemset.id == created_problemset.id).first()
        return created_problemset
    except (SQLAlchemyError, ProblemsetServiceError) as e: 
         logger.error(f"Router: Database/Service error during problemset creation: {e}", exc_info=True)
         detail = f"Database error occurred: {e}" if isinstance(e, SQLAlchemyError) else str(e)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
    except Exception as e:
        logger.error(f"Router: Unexpected error during problemset creation: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.get(
    "/",
    response_model=List[ProblemsetSchema],
    summary="Get All Problemsets"
)
def read_all_problemsets(db: Session = Depends(get_db)):
    logger.info("Router: Request received for GET /problemsets")
    try:
        problemsets = problemset_service.get_all(db)
        logger.info(f"Router: Returning {len(problemsets)} problemsets.")
        return problemsets
    except ProblemsetServiceError as e: 
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
    logger.info(f"Router: Request received for GET /problemsets/{problemset_id}")
    try:
        problemset_data = problemset_service.get_one(db, problemset_id) 
        if problemset_data is None:
            logger.warning(f"Router: Problemset with id {problemset_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problemset not found")
        
        # Sort problems by position before returning (consistency)
        if problemset_data.problems:
            problemset_data.problems.sort(key=lambda link: link.position if link.position is not None else float('inf'))
            
        logger.info(f"Router: Returning problemset with id {problemset_id}.")
        return problemset_data
    except ProblemsetServiceError as e:
        logger.error(f"Router: Service error fetching problemset id {problemset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e: 
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
    logger.info(f"Router: Request received for PUT /problemsets/{problemset_id}")
    try:
        updated_problemset = problemset_service.update(db=db, problemset_id=problemset_id, problemset_update=problemset_update)
        if updated_problemset is None:
            logger.warning(f"Router: Problemset with id {problemset_id} not found for update.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problemset not found")
        logger.info(f"Router: Problemset {problemset_id} updated successfully.")
        # Eager load relationships for the response model
        db.refresh(updated_problemset)
        if hasattr(Problemset, 'problems'):
             db.query(Problemset).options(joinedload(Problemset.problems)).filter(Problemset.id == updated_problemset.id).first()
        return updated_problemset
    except (SQLAlchemyError, ProblemsetServiceError) as e:
         logger.error(f"Router: Database/Service error during problemset update (id: {problemset_id}): {e}", exc_info=True)
         detail = f"Database error occurred: {e}" if isinstance(e, SQLAlchemyError) else str(e)
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
    except HTTPException as http_exc:
         raise http_exc 
    except Exception as e:
        logger.error(f"Router: Unexpected error during problemset update (id: {problemset_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.delete(
    "/{problemset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Problemset"
)
def delete_existing_problemset(problemset_id: int, db: Session = Depends(get_db)):
    logger.info(f"Router: Request received for DELETE /problemsets/{problemset_id}")
    try:
        success = problemset_service.delete(db=db, problemset_id=problemset_id)
        if not success:
            logger.warning(f"Router: Problemset with id {problemset_id} not found for deletion.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problemset not found")
        logger.info(f"Router: Problemset {problemset_id} deleted successfully.")
        return None
    except (SQLAlchemyError, ProblemsetServiceError) as e:
        logger.error(f"Router: Database/Service error during problemset deletion (id: {problemset_id}): {e}", exc_info=True)
        detail = f"Database error occurred: {e}" if isinstance(e, SQLAlchemyError) else str(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        logger.error(f"Router: Unexpected error during problemset deletion (id: {problemset_id}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# --- Endpoints for Managing Problem Associations ---

@router.post(
    "/{problemset_id}/problems/{problem_id}",
    response_model=ProblemsetProblemsSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add Problem to Problemset",
    tags=["Problemsets", "Associations"]
)
def add_problem_to_problemset_endpoint(
    problemset_id: int,
    problem_id: int,
    position: Optional[int] = Query(None, ge=1, description="Optional position for the problem in the set. If None, appends to the end."),
    db: Session = Depends(get_db)
):
    logger.info(f"Router: Attempting to add problem {problem_id} to problemset {problemset_id} at position {position}.")
    try:
        link = problemset_service.add_problem_to_problemset(
            db, problemset_id=problemset_id, problem_id=problem_id, position=position
        )
        if link is None:
            ps = problemset_service.get_one(db, problemset_id)
            if not ps:
                logger.warning(f"Router: Add failed - Problemset {problemset_id} not found.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Problemset with id {problemset_id} not found.")
            
            prob = problem_service.get_one(db, problem_id) 
            if not prob:
                logger.warning(f"Router: Add failed - Problem {problem_id} not found.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Problem with id {problem_id} not found.")
            
            existing_db_link = db.query(ProblemsetProblems).filter_by(id_problemset=problemset_id, id_problem=problem_id).first()
            if existing_db_link:
                logger.warning(f"Router: Add failed - Problem {problem_id} already in problemset {problemset_id}.")
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Problem {problem_id} is already in problemset {problemset_id}.")

            if position is not None:
                occupied_by_other = (
                    db.query(ProblemsetProblems)
                    .filter(
                        ProblemsetProblems.id_problemset == problemset_id,
                        ProblemsetProblems.position == position,
                        ProblemsetProblems.id_problem != problem_id 
                    )
                    .first()
                )
                if occupied_by_other:
                    logger.warning(f"Router: Add failed - Position {position} in problemset {problemset_id} is already occupied.")
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Position {position} in problemset {problemset_id} is already occupied.")
            
            logger.error(f"Router: Add problem to problemset failed for an unknown reason after checks.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to add problem to problemset. Ensure position is valid if provided.")

        logger.info(f"Router: Successfully added problem {problem_id} to problemset {problemset_id}.")
        return link
    except ProblemsetServiceError as e:
        logger.error(f"Router: Service error adding problem to problemset: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except HTTPException as http_exc: 
        raise http_exc
    except Exception as e:
        logger.error(f"Router: Unexpected error adding problem to problemset: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")


@router.delete(
    "/{problemset_id}/problems/{problem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Problem from Problemset",
    tags=["Problemsets", "Associations"]
)
def remove_problem_from_problemset_endpoint(
    problemset_id: int,
    problem_id: int,
    db: Session = Depends(get_db)
):
    logger.info(f"Router: Attempting to remove problem {problem_id} from problemset {problemset_id}.")
    try:
        success = problemset_service.remove_problem_from_problemset(
            db, problemset_id=problemset_id, problem_id=problem_id
        )
        if not success:
            logger.warning(f"Router: Link between problem {problem_id} and problemset {problemset_id} not found for deletion.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem association not found.")
        
        logger.info(f"Router: Successfully removed problem {problem_id} from problemset {problemset_id}.")
        return None 
    except ProblemsetServiceError as e:
        logger.error(f"Router: Service error removing problem from problemset: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except HTTPException as http_exc: 
        raise http_exc
    except Exception as e:
        logger.error(f"Router: Unexpected error removing problem from problemset: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

# --- NEW ENDPOINT FOR REORDERING PROBLEMS ---
@router.put(
    "/{problemset_id}/problems/order",
    response_model=ProblemsetSchema, # Return the full updated problemset
    summary="Reorder Problems in a Problemset",
    tags=["Problemsets", "Associations"]
)
def reorder_problems_in_problemset_endpoint(
    problemset_id: int,
    payload: ReorderProblemsPayload, # Use the Pydantic model for the body
    db: Session = Depends(get_db)
):
    """
    Updates the order of problems within a specific problemset.
    The request body should contain a list of problem IDs in the desired new order.
    This list MUST contain ALL problems currently associated with the problemset.
    """
    logger.info(f"Router: Reordering problems for problemset {problemset_id}. New order: {payload.problem_ids_ordered}")
    try:
        updated_links = problemset_service.reorder_problems_in_problemset(
            db, problemset_id=problemset_id, problem_ids_ordered=payload.problem_ids_ordered
        )
        
        if updated_links is None:
            # Service layer should raise specific exceptions for validation errors,
            # but if it returns None for 'not found' condition:
            logger.warning(f"Router: Reorder failed - Problemset {problemset_id} not found.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Problemset {problemset_id} not found for reordering.")

        logger.info(f"Router: Successfully reordered problems for problemset {problemset_id}.")
        
        # Fetch the updated problemset to return it
        # get_one already eager loads, but we call it again after commit
        updated_problemset = problemset_service.get_one(db, problemset_id)
        if not updated_problemset:
             # This shouldn't happen if reorder succeeded, but handle defensively
             logger.error(f"Router: Failed to fetch problemset {problemset_id} after successful reorder.")
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated problemset.")
        
        # Sort problems by position before returning
        if updated_problemset.problems:
            updated_problemset.problems.sort(key=lambda link: link.position if link.position is not None else float('inf'))
            
        return updated_problemset

    except ProblemsetServiceError as e:
        logger.error(f"Router: Service error during problem reorder for problemset {problemset_id}: {e}", exc_info=False) # Log less verbosely for validation errors
        # Check for specific validation messages if needed, otherwise return 400
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as http_exc: # Re-raise 404 if raised explicitly by service
        raise http_exc
    except Exception as e:
        logger.error(f"Router: Unexpected error reordering problems for problemset {problemset_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during reordering.")


# --- Existing Lecture/PDF Specific Endpoints ---

@router.get(
    "/{problemset_id}/lecture-data",
    response_model=ProblemsetSchema,
    summary="Get Eagerly Loaded Data for a Specific Problemset (e.g., Lecture)",
    tags=["Lectures"], 
    responses={
        404: {"description": "Problemset not found"},
    }
)
def get_lecture_data_by_id(
    problemset_id: int,
    db: Session = Depends(get_db)
) -> ProblemsetSchema:
    # Delegate to the main get_one function now that it eager loads
    return read_problemset(problemset_id=problemset_id, db=db)


@router.post(
    "/process-pdf",
    response_model=ProblemsetSchema,
    summary="Process PDF Lecture, Extract Data, and Save to Database",
    tags=["Lectures", "AI Processing"], 
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
        extracted_data = await gemini_service.process_lecture_pdf(pdf_bytes) 
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
    tags=["PDF Generation"], 
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
    logger.info(f"PDF download request received for Problemset ID: {problemset_id}")
    try:
        pdf_bytes = get_problemset_pdf(db, problemset_id)
        pdf_stream = io.BytesIO(pdf_bytes)
        problemset_db = db.query(Problemset).filter(Problemset.id == problemset_id).first() 
        safe_title = "problemset"
        if problemset_db and problemset_db.title:
            safe_title = "".join(c if c.isalnum() or c in ['-', '_'] else '_' for c in problemset_db.title.replace(' ', '_'))
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