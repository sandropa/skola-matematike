import logging
import json
from typing import Dict, Any, AsyncIterator, List, Tuple, Optional

from google import genai
from google.genai import types

from fastapi.concurrency import run_in_threadpool

try:
    from ..schemas.problemset import LectureProblemsOutput # Import the AI output model
except ImportError as e:
    logging.error(f"Failed to import Pydantic schema LectureProblemsOutput: {e}")
    raise

from ..config import settings


logger = logging.getLogger(__name__)

GEMINI_FLASH_2_5 = settings.GEMINI_FLASH_2_5
GEMINI_PRO_2_5 = settings.GEMINI_PRO_2_5

# Define custom service-level exceptions
class GeminiServiceError(Exception):
    """Base exception for Gemini service errors."""
    pass

class GeminiJSONError(GeminiServiceError):
    """Exception raised when Gemini returns invalid JSON."""
    pass

class GeminiResponseValidationError(GeminiServiceError):
     """Exception raised when AI response JSON fails Pydantic validation."""
     pass


class GeminiService:
    '''
        Low-level wrapper around the client for streaming.
    '''
    def __init__(self, client: genai.Client):
        self.client = client
        logger.info("GeminiService initialized.")

    async def stream(
        self,
        model: str,
        system_prompt: str,
        shots: List[Tuple[str, str]], # list of (user_example, model_example)
        user_input: str,
        temperature: float = 0.0,
        top_p: float = 1.0,
        thinking_budget: Optional[int] = None,
        response_mime_type: str = "text/plain",
        response_schema: Optional[types.Schema] = None, # might not work with other llms
    ) -> AsyncIterator[str]:
        '''
            Build contents from system prompt, few-shot pairs, and user input,
            then stream text chunks from Gemini.
        '''
        contents: List[types.Content] = []

        # Add few-shot examples
        for user_ex, model_ex in shots:
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=user_ex)])
            )
            contents.append(
                types.Content(role="model", parts=[types.Part.from_text(text=model_ex)])
            )
        # Add final user input
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=user_input)])
        )

        # Build GenerateContentConfig
        system_prompt = [types.Part.from_text(text=system_prompt)]
        thinking_config = types.ThinkingConfig(thinking_budget=thinking_budget or 0)

        config_kwargs = {
            "temperature": temperature,
            "top_p": top_p,
            "thinking_config": thinking_config,
            "response_mime_type": response_mime_type,
            "system_instruction": system_prompt
        }
        if response_schema is not None:
            config_kwargs["response_schema"] = response_schema
        gen_config = types.GenerateContentConfig(**config_kwargs)

        response_stream = await self.client.aio.models.generate_content_stream(
            model=model,
            contents=contents,
            config=gen_config,
        )

        # Call Gemini streaming API
        async for chunk in response_stream:
            text_to_yield = None # Initialized to None
            if hasattr(chunk, 'text') and chunk.text:
                text_to_yield = chunk.text
            elif hasattr(chunk, 'candidates') and chunk.candidates and \
                    hasattr(chunk.candidates[0], 'content') and chunk.candidates[0].content and \
                    hasattr(chunk.candidates[0].content, 'parts') and chunk.candidates[0].content.parts:
                part_texts = [part.text for part in chunk.candidates[0].content.parts if hasattr(part, 'text')]
                if part_texts: # This condition is important
                    text_to_yield = "".join(part_texts)
            
            if text_to_yield is not None: # This condition ensures we only yield actual text
                yield text_to_yield
            else:
                # This else block means if text_to_yield is STILL None, nothing is yielded FOR THIS CHUNK
                logger.debug(f"Received chunk with no text content: {chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk}")
