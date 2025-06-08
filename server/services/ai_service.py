import logging
from typing import AsyncIterator, Optional
from google.genai import types

from .gemini_service import GeminiService
from .prompts import (
    SYSTEM_PROMPTS,
    HELLO_EXAMPLES,
)

from ..config import settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = settings.GEMINI_FLASH_2_5

class AIService:
    '''
        Higher-level service that defines actions (hello, translate, fix_latex)
        and uses GeminiService to perform them.
    '''
    def __init__(self, gemini: GeminiService):
        self.gemini = gemini

    async def hello(
        self,
        message: str = "hi",
        model: Optional[str] = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        thinking_budget: Optional[int] = None,
    ) -> AsyncIterator[str]:
        system_prompt = SYSTEM_PROMPTS["hello"]
        shots = HELLO_EXAMPLES # list of (user, model)
        user_input = message
        response_schema = types.Schema(
            type=types.Type.OBJECT,
            required=["message"],
            properties={"message": types.Schema(type=types.Type.STRING)},
        )
        chosen_model = model or DEFAULT_MODEL
        return self.gemini.stream(
            model=chosen_model,
            system_prompt=system_prompt,
            shots=shots,
            user_input_text=user_input,
            temperature=temperature,
            top_p=top_p,
            thinking_budget=thinking_budget,
            response_mime_type="application/json",
            response_schema=response_schema,
        )
    
    async def fix_latex(
        self,
        user_input,
        model: Optional[str] = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        thinking_budget: Optional[int] = None,
    ) -> AsyncIterator[str]:
        system_prompt = SYSTEM_PROMPTS["fix_latex"]
        chosen_model = model or DEFAULT_MODEL
        # response_schema = types.Schema(
        #     type=types.Type.OBJECT,
        #     required=["fixed_latex_code"],
        #     properties={"fixed_latex_code": types.Schema(type=types.Type.STRING)},
        # )
        return self.gemini.stream(
            model=chosen_model,
            system_prompt=system_prompt,
            user_input_text=user_input,
            temperature=temperature,
            top_p=top_p,
            thinking_budget=thinking_budget,
            # response_mime_type="application/json",
            # response_schema=response_schema,
        )
    
    async def extract_latex_from_image(
        self,
        user_input_image: bytes,
        user_input_image_mime_type: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        top_p: float = 1.0,
        thinking_budget: Optional[int] = None,
    ) -> AsyncIterator[str]:
        system_prompt = SYSTEM_PROMPTS["extract_latex_from_image"]
        chosen_model = model or DEFAULT_MODEL

        return self.gemini.stream(
            model=chosen_model,
            system_prompt=system_prompt,
            user_input_bytes=user_input_image,
            user_input_bytes_mime_type=user_input_image_mime_type,
        )
        
