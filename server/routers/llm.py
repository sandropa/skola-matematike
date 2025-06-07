from fastapi import APIRouter, Depends, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from ..dependencies import get_gemini_service
from ..services.gemini_service import GeminiService
from ..services.ai_service import AIService

from ..schemas.llm import LatexRequest

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
