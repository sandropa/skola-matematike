# server/main.py

import os
import logging
# --- Use EXACT imports from your working sample ---
from google import genai
from google.genai import types
# --- End of sample-specific imports ---

from fastapi import FastAPI, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

# Import the settings from your config file (assuming config.py loads .env)
from .config import settings

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Check for API Key on Startup (Optional but good practice) ---
if not settings.GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not found in environment variables. Translation endpoint might fail.")
else:
    logger.info("GEMINI_API_KEY found in environment variables.")


# --- FastAPI App ---
app = FastAPI(
    title="Skola Matematike API",
    description="API using the specific Gemini Client structure provided.",
    version="0.2.0" # Incremented version
)

# --- Pydantic Models ---
class LatexInput(BaseModel):
    latex_text: str = Field(..., min_length=1, examples=["Solve $x^2 + 5x + 6 = 0$."])

class TranslationOutput(BaseModel):
    original_text: str
    translated_text: str
    language: str = "Bosnian"

# --- API Endpoints ---
@app.get("/")
async def root():
    """ Basic API root endpoint. """
    logger.info("Root endpoint '/' accessed.")
    return {"message": "Welcome to the Skola Matematike API (Using Specific Client)"}

@app.post(
    "/translate/latex-to-bosnian",
    response_model=TranslationOutput,
    summary="Translate LaTeX Math Problem to Bosnian (Specific Client)",
    tags=["Translation"]
)
async def translate_latex(payload: LatexInput):
    """
    Receives mathematical text (potentially including LaTeX) and translates
    it to Bosnian using the specific Gemini Client structure provided,
    attempting to preserve LaTeX formatting. Uses few-shot prompting.

    - **latex_text**: The text containing the math problem (required).
    """
    logger.info(f"Received translation request for text: '{payload.latex_text[:50]}...'")

    if not settings.GEMINI_API_KEY:
         logger.error("Translation attempt failed: Gemini API key not configured.")
         raise HTTPException(
             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
             detail="Translation service is not configured correctly (API Key missing)."
         )

    try:
        # --- Instantiate Client (as per your sample) ---
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.debug("Gemini Client instantiated.")

        # --- Define Model and Configuration (EXACTLY as per your sample) ---
        model_name = "gemini-2.5-flash-preview-04-17" # Model from your sample
        generation_config = types.GenerateContentConfig( # Class from your sample
            thinking_config = types.ThinkingConfig( # Class from your sample
                thinking_budget=0,
            ),
            response_mime_type="text/plain",
        )
        logger.debug(f"Using model: {model_name} and GenerateContentConfig.")

        # --- Construct Few-Shot Contents (using sample's types) ---
        # Using the same few-shot structure as before
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""Translate the following math problem to Bosnian. Keep Latex formatting: "Find the derivative of $f(x) = x^3 - 6x^2 + 5$. Calculate $f'(2)$." """),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part.from_text(text="""Nađite derivaciju funkcije $f(x) = x^3 - 6x^2 + 5$. Izračunajte $f'(2)$."""),
                ],
            ),
            # Add more examples here if needed
            types.Content(
                role="user",
                parts=[
                    # Insert the actual user input
                    types.Part.from_text(text=f"""Translate the following math problem to Bosnian. Keep Latex formatting: "{payload.latex_text}" """),
                ],
            ),
        ]
        logger.debug(f"Constructed contents for Gemini API. Final user part starts with: '{payload.latex_text[:30]}...'")

        # --- Call Gemini API (Attempting Non-Streaming Equivalent) ---
        # Based on your sample's client.models.generate_content_stream,
        # we ASSUME client.models.generate_content exists for non-streaming.
        # If this fails with AttributeError, we'll need to adjust.
        logger.info(f"Calling Gemini model '{model_name}' via Client API (attempting non-streaming)...")
        try:
            # Assume the non-streaming method exists here
            api_call_func = client.models.generate_content
        except AttributeError:
            logger.error("Failed to find 'client.models.generate_content'. Streaming collection needed but not implemented.")
            raise HTTPException(status_code=501, detail="Server API method mismatch: Non-streaming call failed.")

        response = await run_in_threadpool(
            api_call_func,                  # The function to run
            model=model_name,               # Arguments for the function
            contents=contents,
            # IMPORTANT: Use 'config=' parameter name, as seen in your sample's stream call
            config=generation_config,
        )
        logger.info("Received response from Gemini.")
        # Note: Response structure might differ between stream/non-stream and Client/GenerativeModel APIs
        logger.debug(f"Gemini raw response object type: {type(response)}")
        # Attempt to log common feedback attributes if they exist
        if hasattr(response, 'prompt_feedback'):
             logger.debug(f"Gemini response prompt feedback: {response.prompt_feedback}")

        # --- Process Response ---
        # Accessing response text might need adjustment depending on the actual object returned
        if hasattr(response, 'text') and response.text:
            translated_text = response.text
        elif hasattr(response, 'candidates') and response.candidates and response.candidates[0].content.parts:
             # Fallback attempt similar to GenerativeModel API response structure
             translated_text = "".join(part.text for part in response.candidates[0].content.parts)
             logger.debug("Accessed text via response.candidates[0].content.parts")
        else:
            # If text cannot be extracted
            logger.warning(f"Could not extract text from Gemini response. Response object: {response}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Translation failed: Could not parse response from translation service."
            )

        logger.info(f"Successfully translated text to: '{translated_text[:50]}...'")
        return TranslationOutput(
            original_text=payload.latex_text,
            translated_text=translated_text.strip()
        )

    # --- Error Handling ---
    # Catch specific errors from the 'genai' library if known
    # except genai.APIError as api_error: # Example - replace with actual error types if known
    #     logger.error(f"Gemini API error: {api_error}", exc_info=True)
    #     raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Translation service API error.")
    except Exception as e:
        # Log the full error details for debugging
        logger.error(f"An unexpected error occurred during translation: {e}", exc_info=True)
        # Return a generic error to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during the translation process."
        )