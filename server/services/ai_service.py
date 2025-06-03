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
            user_input=user_input,
            temperature=temperature,
            top_p=top_p,
            thinking_budget=thinking_budget,
            response_mime_type="application/json",
            response_schema=response_schema,
        )
