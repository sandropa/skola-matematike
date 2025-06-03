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
            yield chunk.text

# class GeminiService:
#     """
#     Service class to encapsulate interactions with the Gemini API.
#     """
#     def __init__(self, client: genai.Client):
#         """Initializes the GeminiService with an instantiated genai.Client."""
#         self.client = client
#         logger.info("GeminiService initialized.")


#     async def hello(self, message="hi", model=GEMINI_FLASH_2_5) -> AsyncIterator[str]:
#         '''
#             Returns an async-generator of text chunks from Gemini.
#         '''
#         logger.info("Service method: saying hello.")

#         contents = [
#             # few-shot learning
#             types.Content(role="user", parts=[types.Part.from_text(text="how are you?")]),
#             types.Content(role="model", parts=[types.Part.from_text(text="{\"message\": \"HELLO!\"}")]),
#             types.Content(role="user", parts=[types.Part.from_text(text="hey")]),
#             types.Content(role="model", parts=[types.Part.from_text(text="{\"message\": \"HELLO!\"}")]),

#             # our message (request prompt)
#             types.Content(role="user", parts=[types.Part.from_text(text=message)]),
#         ]

#         generate_content_config = types.GenerateContentConfig(
#             temperature=0,
#             top_p=1,
#             thinking_config = types.ThinkingConfig(
#                 thinking_budget=0,
#             ),
#             response_mime_type="application/json", # "text/plain"
#             response_schema=types.Schema(
#                 type=types.Type.OBJECT,
#                 required=["message"],
#                 properties={
#                     "message": types.Schema(
#                         type=types.Type.STRING,
#                     ),
#                 },
#             ),
#             system_instruction=[
#                 types.Part.from_text(text="You are a nice assistant saying hello.")
#             ],
#         )

#         for chunk in self.client.models.generate_content_stream(
#             model=model,
#             contents=contents,
#             config=generate_content_config,
#         ):
#             yield chunk.text


#     async def process_lecture_pdf(self, pdf_bytes: bytes) -> LectureProblemsOutput:
#         """
#         Processes a PDF lecture file using Gemini and extracts structured data,
#         including problem categories.

#         Returns:
#             A LectureProblemsOutput Pydantic model instance.
#         """
#         logger.info("Service method: processing lecture PDF for text and category.")

#         # --- Prepare Contents using Inline Data (with updated prompt) ---
#         contents = [
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part(inline_data=types.Blob(
#                         mime_type="application/pdf",
#                         data=pdf_bytes
#                     )),
#                     types.Part.from_text(text="""Extract the following from this PDF document:
# 1. The lecture name (title/topic).
# 2. The target group, mapping it to one of: 'napredna', 'olimpijska', 'pocetna', 'predolimpijska', 'srednja'.
# 3. A list of all distinct math problems. For EACH problem in the list, provide:
#     a. Its full LaTeX source code.
#     b. Its most likely category, assigning exactly one letter: 'A' for Algebra, 'N' for Number Theory, 'G' for Geometry, or 'C' for Combinatorics.
# Return the output as a single JSON object conforming to the specified schema."""),
#                 ],
#             ),
#         ]
#         logger.debug("Service: Constructed contents for PDF processing including category.")

#         # --- Define generation config with updated response_schema ---
#         generate_content_config = types.GenerateContentConfig(
#             response_mime_type="application/json",
#             response_schema=genai.types.Schema(
#                 type = genai.types.Type.OBJECT,
#                 required = ["lecture_name", "group_name", "problems_latex"],
#                 properties = {
#                     "lecture_name": genai.types.Schema(type = genai.types.Type.STRING, description = "The main title or name/topic of the lecture found in the document."),
#                     "group_name": genai.types.Schema(type = genai.types.Type.STRING, description = "The target group for the lecture, mapped precisely to one of the five allowed values.", enum = ["napredna", "olimpijska", "pocetna", "predolimpijska", "srednja"]),
#                     "problems_latex": genai.types.Schema(
#                         type = genai.types.Type.ARRAY,
#                         description = "A list of objects, each containing the LaTeX source and category for a distinct problem.",
#                         items = genai.types.Schema(
#                             type = genai.types.Type.OBJECT,
#                             properties = {
#                                 'latex_text': genai.types.Schema(type=genai.types.Type.STRING, description="The full LaTeX representation of a single math problem."),
#                                 'category': genai.types.Schema(type=genai.types.Type.STRING, description="The category of the problem (A, N, G, or C).", enum = ['A', 'N', 'G', 'C'])
#                             },
#                             required = ['latex_text', 'category']
#                         )
#                     ),
#                 },
#             ),
#             system_instruction=[types.Part.from_text(text="""You are a highly accurate extraction engine specializing in mathematical lecture documents (PDFs) from math camps. Your task is to parse the provided PDF and extract the lecture title, target group (mapped to 'napredna', 'olimpijska', 'pocetna', 'predolimpijska', or 'srednja'), and a list of problems. For each problem, provide its LaTeX source and its category ('A', 'N', 'G', or 'C'). Adhere strictly to the provided JSON output schema."""),],
#         )
#         logger.debug("Service: Defined generation config with updated response schema for problem categories.")

#         # --- Call generate_content_stream and collect response ---
#         full_json_string = ""
#         try:
#             logger.info(f"Service: Calling Gemini model '{GEMINI_FLASH_2_5}' (streaming)...")
#             def _get_streamed_response_text():
#                 text = ""
#                 stream = self.client.models.generate_content_stream(model=GEMINI_FLASH_2_5, contents=contents, config=generate_content_config,)
#                 for chunk in stream:
#                     if hasattr(chunk, 'text') and chunk.text: text += chunk.text
#                 return text
#             full_json_string = await run_in_threadpool(_get_streamed_response_text)
#             logger.info("Service: Finished receiving streamed response.")
#             logger.debug(f"Service: Full raw string received (first 500 chars): {full_json_string[:500]}...")
#         except Exception as e:
#              logger.error(f"Service: Error during Gemini generation streaming: {e}", exc_info=True)
#              raise GeminiServiceError(f"AI content generation failed: {e}")

#         # --- Parse and Validate the collected JSON string ---
#         if not full_json_string:
#             logger.warning("Service: Received empty response string from Gemini.")
#             raise GeminiServiceError("AI service returned an empty response.")
#         try:
#             parsed_data: Dict[str, Any] = json.loads(full_json_string)
#             logger.info("Service: Successfully parsed Gemini response as JSON.")
#             logger.debug("Service: Validating parsed data against LectureProblemsOutput schema...")
#             validated_data = LectureProblemsOutput(**parsed_data) # Validation happens here
#             logger.info("Service: Parsed data successfully validated.")
#             return validated_data # Return validated Pydantic object
#         except json.JSONDecodeError as e:
#             logger.error(f"Service: Failed to decode JSON response: {e}. Raw string: {full_json_string}", exc_info=True)
#             raise GeminiJSONError(f"AI service returned invalid JSON: {e}")
#         except Exception as e: # Catch Pydantic ValidationError etc.
#             logger.error(f"Service: An error occurred during JSON parsing or Pydantic validation: {e}", exc_info=True)
#             raise GeminiResponseValidationError(f"AI response did not match expected data structure: {e}")


#     async def translate_latex(self, latex_text: str) -> str:
#         """Translates LaTeX text to Bosnian."""
#         logger.info(f"Service method: translating latex (first 50 chars) '{latex_text[:50]}...'")

#         # Model name (can be different if needed)
#         model = GEMINI_FLASH_2_5 # Or a different model suitable for translation

#         # Define Configuration (copied from your main.py translation route)
#         generation_config = types.GenerateContentConfig(
#             # Note: thinking_config was in your translation sample
#             thinking_config = types.ThinkingConfig(thinking_budget=0),
#             response_mime_type="text/plain",
#         )
#         logger.debug(f"Service: Using model: {model} and GenerateContentConfig for translation.")

#         # Construct Few-Shot Contents (copied from your main.py translation route)
#         contents = [
#             types.Content(role="user", parts=[types.Part.from_text(text="""Translate the following math problem to Bosnian. Keep Latex formatting: "Find the derivative of $f(x) = x^3 - 6x^2 + 5$. Calculate $f'(2)$." """),]),
#             types.Content(role="model", parts=[types.Part.from_text(text="""Nađite derivaciju funkcije $f(x) = x^3 - 6x^2 + 5$. Izračunajte $f'(2)$."""),]),
#             types.Content(role="user", parts=[types.Part.from_text(text=f"""Translate the following math problem to Bosnian. Keep Latex formatting: "{latex_text}" """),]),
#         ]
#         logger.debug(f"Service: Constructed contents for translation.")

#         # --- Call Gemini API (Non-Streaming Equivalent as in your main.py) ---
#         # Assume generate_content exists and is synchronous -> use run_in_threadpool
#         try:
#              logger.info(f"Service: Calling Gemini model '{model}' (non-streaming)...")
#              # Function to run in the threadpool for sync call
#              def _generate_content_sync():
#                   return self.client.models.generate_content(
#                       model=model,
#                       contents=contents,
#                       config=generation_config,
#                   )

#              # Run the sync call in a threadpool
#              response = await run_in_threadpool(_generate_content_sync)

#              logger.info("Service: Received translation response.")

#              # Process Response (copied from your main.py translation route)
#              if hasattr(response, 'text') and response.text:
#                  translated_text = response.text
#              elif hasattr(response, 'candidates') and response.candidates and response.candidates[0].content.parts:
#                   translated_text = "".join(part.text for part in response.candidates[0].content.parts)
#                   logger.debug("Service: Accessed translation text via candidates[0].content.parts")
#              else:
#                  logger.warning(f"Service: Could not extract text from translation response. Response object: {response}")
#                  raise GeminiServiceError("Translation failed: Could not parse response from service.")

#              logger.info(f"Service: Successfully translated text (first 50 chars) to: '{translated_text[:50]}...'")
#              return translated_text.strip()

#         except Exception as e:
#             logger.error(f"Service: An unexpected error occurred during translation: {e}", exc_info=True)
#             raise GeminiServiceError(f"An internal error occurred during translation: {e}")


#     async def image_to_latex(self, image_bytes: bytes, mime_type: str) -> str:
#         """Converts an image of a math problem to LaTeX."""
#         logger.info(f"Service method: converting image to latex (type: {mime_type}).")

#         # Model name
#         model = GEMINI_FLASH_2_5 # Or a model suitable for image understanding

#         # Define Configuration (copied from your main.py image-to-latex route)
#         generation_config = types.GenerateContentConfig(
#             # Note: thinking_config was NOT in your image sample
#             response_mime_type="text/plain",
#         )
#         logger.debug(f"Service: Using model: {model} and GenerateContentConfig for image-to-latex.")

#         # --- Construct Contents with Image Data and Text Prompt (copied from your main.py image-to-latex route) ---
#         contents = [
#             types.Content(
#                 role="user",
#                 parts=[
#                     types.Part(inline_data=types.Blob(
#                         mime_type=mime_type, # Use the provided mime type
#                         data=image_bytes # Use the provided bytes
#                     )),
#                     types.Part.from_text(text="""Give me the latex for the following math problem."""),
#                 ]
#             )
#         ]
#         logger.debug("Service: Constructed multi-part contents (image + text) for image-to-latex.")

#         # --- Call Gemini API (Non-Streaming Equivalent as in your main.py) ---
#         # Assume generate_content exists and is synchronous -> use run_in_threadpool
#         try:
#             logger.info(f"Service: Calling Gemini model '{model}' (non-streaming)...")
#             def _generate_content_sync():
#                  return self.client.models.generate_content(
#                      model=model,
#                      contents=contents,
#                      config=generation_config,
#                  )

#             response = await run_in_threadpool(_generate_content_sync)

#             logger.info("Service: Received image-to-latex response.")

#             # Process Response (copied from your main.py image-to-latex route)
#             if hasattr(response, 'text') and response.text:
#                 latex_text = response.text
#             elif hasattr(response, 'candidates') and response.candidates and response.candidates[0].content.parts:
#                  latex_text = "".join(part.text for part in response.candidates[0].content.parts)
#                  logger.debug("Service: Accessed latex text via candidates[0].content.parts")
#             else:
#                  logger.warning(f"Service: Could not extract text from image-to-latex response. Response object: {response}")
#                  raise GeminiServiceError("Image-to-LaTeX failed: Could not parse response from service.")

#             logger.info(f"Service: Successfully generated LaTeX (first 50 chars): '{latex_text[:50]}...'")
#             return latex_text.strip()

#         except Exception as e:
#             logger.error(f"Service: An unexpected error occurred during image-to-latex conversion: {e}", exc_info=True)
#             raise GeminiServiceError(f"An internal error occurred during image conversion: {e}")
