from fastapi import APIRouter, Depends, Body, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from ..dependencies import get_gemini_service
from ..services.gemini_service import GeminiService
from ..services.ai_service import AIService

from ..schemas.llm import LatexRequest, MathImageRequest

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM"])

class HelloRequest(BaseModel):
    message: str

@router.post("/hello", summary="Stream a hello response from Gemini")
async def hello_stream(
    request: HelloRequest = Body(...),
    gemini_service: GeminiService = Depends(get_gemini_service),
):
    ai_service = AIService(gemini=gemini_service)
    stream = await ai_service.hello(message=request.message)
    return StreamingResponse(stream, media_type="application/json")


@router.post("/fix-latex", summary="Fix LaTeX code.")
async def fix_latex(
    request: LatexRequest = Body(...),
    gemini_service: GeminiService = Depends(get_gemini_service),
):
    ai_service = AIService(gemini=gemini_service)
    stream = await ai_service.fix_latex(user_input=request.code)
    return StreamingResponse(stream)


@router.post("/extract-latex-from-image", summary="Extracts LaTeX code from image.")
async def extract_latex_from_image(
    file: UploadFile = File(..., description="Image file of the math problem"),
    gemini_service: GeminiService = Depends(get_gemini_service),
):
    logger.info(f"Received image file upload request: {file.filename} (type: {file.content_type})")
    
    ai_service = AIService(gemini=gemini_service)

    # Basic MIME type validation
    if not file.content_type or not file.content_type.startswith("image/"):
        logger.warning(f"Invalid file type uploaded: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Please upload an image (e.g., PNG, JPEG)."
        )

    # Read image data
    try:
        image_bytes = await file.read()
        if not image_bytes:
             raise ValueError("Uploaded file is empty.")
        logger.info(f"Read {len(image_bytes)} bytes from uploaded file '{file.filename}'.")
    except Exception as e:
        logger.error(f"Failed to read uploaded file '{file.filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {e}"
        )
    finally:
        # Ensure the file is closed (important for temp files)
        await file.close()

    try:
        stream = await ai_service.extract_latex_from_image(
            user_input_image_mime_type=file.content_type,
            user_input_image=image_bytes
        )
        return StreamingResponse(stream)
    except Exception as e:
        logger.error(f"An unexpected error occurred during image-to-latex conversion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during the image conversion process.")

