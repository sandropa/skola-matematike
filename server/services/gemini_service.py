# server/services/gemini_service.py

import logging
import json
from typing import Dict, Any # Keep Dict for intermediate parsed data

# Import the specific genai types used for API calls
from google import genai
from google.genai import types

# Import run_in_threadpool as service methods will be called from async routers
from fastapi.concurrency import run_in_threadpool

# Import the Pydantic model for AI output from schemas
try:
    from ..schemas.problemset import LectureProblemsOutput # Import the AI output model
except ImportError as e:
    logging.error(f"Failed to import Pydantic schema LectureProblemsOutput: {e}")
    raise


logger = logging.getLogger(__name__)

# Define model names as constants
GEMINI_FLASH_2_5 = "gemini-2.5-flash-preview-04-17"


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
    """
    Service class to encapsulate interactions with the Gemini API.
    """
    def __init__(self, client: genai.Client):
        """Initializes the GeminiService with an instantiated genai.Client."""
        self.client = client
        logger.info("GeminiService initialized.")


    # --- Return type hint is now the Pydantic AI output model ---
    async def process_lecture_pdf(self, pdf_bytes: bytes) -> LectureProblemsOutput:
        """
        Processes a PDF lecture file using Gemini and extracts structured data.

        Args:
            pdf_bytes: The binary content of the PDF file.

        Returns:
            A LectureProblemsOutput Pydantic model instance containing
            the extracted lecture name, group, and problems in LaTeX format.

        Raises:
            GeminiServiceError: If the API call fails or returns an empty response.
            GeminiJSONError: If AI returns invalid JSON.
            GeminiResponseValidationError: If AI returns valid JSON but it doesn't
                                         match the LectureProblemsOutput schema.
        """
        logger.info("Service method: processing lecture PDF.")

        # --- Prepare Contents using Inline Data ---
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(inline_data=types.Blob(
                        mime_type="application/pdf",
                        data=pdf_bytes
                    )),
                    types.Part.from_text(text="""Extract the lecture name, target group, and all distinct math problems in LaTeX format from this PDF document. Return the output as a JSON object conforming to the specified schema."""),
                ],
            ),
        ]
        logger.debug("Service: Constructed contents for PDF processing.")

        # --- Define generation config (copied from your working sample) ---
        # The response_schema here tells the AI the desired structure.
        # It should match the LectureProblemsOutput Pydantic model structure.
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=genai.types.Schema(
                type = genai.types.Type.OBJECT,
                required = ["lecture_name", "group_name", "problems_latex"],
                properties = {
                    "lecture_name": genai.types.Schema(type = genai.types.Type.STRING, description = "The main title or name of the lecture topic found in the document."),
                    "group_name": genai.types.Schema(type = genai.types.Type.STRING, description = "The target group for the lecture (e.g., 'Početna grupa', 'Srednja grupa', 'Napredna grupa', 'Predolimpijska grupa', 'Olimpijska grupa').",),
                    "problems_latex": genai.types.Schema(type = genai.types.Type.ARRAY, description = "A list containing the extracted LaTeX source string for each distinct problem identified in the document.", items = genai.types.Schema(type = types.Type.STRING),),
                },
            ),
            system_instruction=[types.Part.from_text(text="""You are an extraction engine for math lectures. You translate PDFs into JSON of the lecture, and problems in the lecture in Latex."""),],
        )
        logger.debug("Service: Defined generation config for PDF processing.")


        # --- Call generate_content_stream and collect response ---
        full_json_string = ""
        try:
            logger.info(f"Service: Calling Gemini model '{GEMINI_FLASH_2_5}' (streaming)...")

            def _get_streamed_response_text():
                text = ""
                stream = self.client.models.generate_content_stream(
                    model=GEMINI_FLASH_2_5,
                    contents=contents,
                    config=generate_content_config,
                )
                for chunk in stream:
                    if hasattr(chunk, 'text') and chunk.text:
                         text += chunk.text
                return text

            full_json_string = await run_in_threadpool(_get_streamed_response_text)

            logger.info("Service: Finished receiving streamed response.")
            logger.debug(f"Service: Full raw string received (first 500 chars): {full_json_string[:500]}...")

        except Exception as e:
             logger.error(f"Service: Error during Gemini generation streaming: {e}", exc_info=True)
             raise GeminiServiceError(f"AI content generation failed: {e}")


        # --- Parse and Validate the collected JSON string ---
        if not full_json_string:
            logger.warning("Service: Received empty response string from Gemini.")
            raise GeminiServiceError("AI service returned an empty response.")

        try:
            # Parse the string as JSON
            parsed_data: Dict[str, Any] = json.loads(full_json_string)
            logger.info("Service: Successfully parsed Gemini response as JSON.")

            # --- Validate parsed data against the Pydantic AI output model ---
            logger.debug("Service: Validating parsed data against LectureProblemsOutput schema...")
            validated_data = LectureProblemsOutput(**parsed_data)
            logger.info("Service: Parsed data successfully validated.")
            # --- Return the validated Pydantic model instance ---
            return validated_data

        except json.JSONDecodeError as e:
            logger.error(f"Service: Failed to decode JSON response: {e}. Raw string: {full_json_string}", exc_info=True)
            raise GeminiJSONError(f"AI service returned invalid JSON: {e}")
        except Exception as e: # Catch Pydantic ValidationError or other parsing issues
            logger.error(f"Service: An error occurred during JSON parsing or Pydantic validation: {e}", exc_info=True)
            raise GeminiResponseValidationError(f"AI response did not match expected data structure: {e}")

    # --- Add other Gemini interaction methods here (translate_latex, image_to_latex, etc.) ---
    # Copy/adapt these from your main.py and the previous GeminiService example
    # Make sure they return the appropriate types (e.g., str, or Pydantic models)

    async def translate_latex(self, latex_text: str) -> str:
        # ... implementation ... (as in previous GeminiService example)
        pass # Replace with actual implementation

    async def image_to_latex(self, image_bytes: bytes, mime_type: str) -> str:
        # ... implementation ... (as in previous GeminiService example)
        pass # Replace with actual implementation
    # --- Add other Gemini interaction methods here ---

    async def translate_latex(self, latex_text: str) -> str:
        """Translates LaTeX text to Bosnian."""
        logger.info(f"Service method: translating latex (first 50 chars) '{latex_text[:50]}...'")

        # Model name (can be different if needed)
        model = GEMINI_FLASH_2_5 # Or a different model suitable for translation

        # Define Configuration (copied from your main.py translation route)
        generation_config = types.GenerateContentConfig(
            # Note: thinking_config was in your translation sample
            thinking_config = types.ThinkingConfig(thinking_budget=0),
            response_mime_type="text/plain",
        )
        logger.debug(f"Service: Using model: {model} and GenerateContentConfig for translation.")

        # Construct Few-Shot Contents (copied from your main.py translation route)
        contents = [
            types.Content(role="user", parts=[types.Part.from_text(text="""Translate the following math problem to Bosnian. Keep Latex formatting: "Find the derivative of $f(x) = x^3 - 6x^2 + 5$. Calculate $f'(2)$." """),]),
            types.Content(role="model", parts=[types.Part.from_text(text="""Nađite derivaciju funkcije $f(x) = x^3 - 6x^2 + 5$. Izračunajte $f'(2)$."""),]),
            types.Content(role="user", parts=[types.Part.from_text(text=f"""Translate the following math problem to Bosnian. Keep Latex formatting: "{latex_text}" """),]),
        ]
        logger.debug(f"Service: Constructed contents for translation.")

        # --- Call Gemini API (Non-Streaming Equivalent as in your main.py) ---
        # Assume generate_content exists and is synchronous -> use run_in_threadpool
        try:
             logger.info(f"Service: Calling Gemini model '{model}' (non-streaming)...")
             # Function to run in the threadpool for sync call
             def _generate_content_sync():
                  return self.client.models.generate_content(
                      model=model,
                      contents=contents,
                      config=generation_config,
                  )

             # Run the sync call in a threadpool
             response = await run_in_threadpool(_generate_content_sync)

             logger.info("Service: Received translation response.")

             # Process Response (copied from your main.py translation route)
             if hasattr(response, 'text') and response.text:
                 translated_text = response.text
             elif hasattr(response, 'candidates') and response.candidates and response.candidates[0].content.parts:
                  translated_text = "".join(part.text for part in response.candidates[0].content.parts)
                  logger.debug("Service: Accessed translation text via candidates[0].content.parts")
             else:
                 logger.warning(f"Service: Could not extract text from translation response. Response object: {response}")
                 raise GeminiServiceError("Translation failed: Could not parse response from service.")

             logger.info(f"Service: Successfully translated text (first 50 chars) to: '{translated_text[:50]}...'")
             return translated_text.strip()

        except Exception as e:
            logger.error(f"Service: An unexpected error occurred during translation: {e}", exc_info=True)
            raise GeminiServiceError(f"An internal error occurred during translation: {e}")


    async def image_to_latex(self, image_bytes: bytes, mime_type: str) -> str:
        """Converts an image of a math problem to LaTeX."""
        logger.info(f"Service method: converting image to latex (type: {mime_type}).")

        # Model name
        model = GEMINI_FLASH_2_5 # Or a model suitable for image understanding

        # Define Configuration (copied from your main.py image-to-latex route)
        generation_config = types.GenerateContentConfig(
            # Note: thinking_config was NOT in your image sample
            response_mime_type="text/plain",
        )
        logger.debug(f"Service: Using model: {model} and GenerateContentConfig for image-to-latex.")

        # --- Construct Contents with Image Data and Text Prompt (copied from your main.py image-to-latex route) ---
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(inline_data=types.Blob(
                        mime_type=mime_type, # Use the provided mime type
                        data=image_bytes # Use the provided bytes
                    )),
                    types.Part.from_text(text="""Give me the latex for the following math problem."""),
                ]
            )
        ]
        logger.debug("Service: Constructed multi-part contents (image + text) for image-to-latex.")

        # --- Call Gemini API (Non-Streaming Equivalent as in your main.py) ---
        # Assume generate_content exists and is synchronous -> use run_in_threadpool
        try:
            logger.info(f"Service: Calling Gemini model '{model}' (non-streaming)...")
            def _generate_content_sync():
                 return self.client.models.generate_content(
                     model=model,
                     contents=contents,
                     config=generation_config,
                 )

            response = await run_in_threadpool(_generate_content_sync)

            logger.info("Service: Received image-to-latex response.")

            # Process Response (copied from your main.py image-to-latex route)
            if hasattr(response, 'text') and response.text:
                latex_text = response.text
            elif hasattr(response, 'candidates') and response.candidates and response.candidates[0].content.parts:
                 latex_text = "".join(part.text for part in response.candidates[0].content.parts)
                 logger.debug("Service: Accessed latex text via candidates[0].content.parts")
            else:
                 logger.warning(f"Service: Could not extract text from image-to-latex response. Response object: {response}")
                 raise GeminiServiceError("Image-to-LaTeX failed: Could not parse response from service.")

            logger.info(f"Service: Successfully generated LaTeX (first 50 chars): '{latex_text[:50]}...'")
            return latex_text.strip()

        except Exception as e:
            logger.error(f"Service: An unexpected error occurred during image-to-latex conversion: {e}", exc_info=True)
            raise GeminiServiceError(f"An internal error occurred during image conversion: {e}")

    # Add more methods for other Gemini features here (similarity, etc.)
    # async def check_similarity(self, problem1_latex: str, problem2_latex: str) -> float:
    #     ... call gemini ...
    #     return similarity_score

    # async def improve_text(self, text: str) -> str:
    #     ... call gemini ...
    #     return improved_text