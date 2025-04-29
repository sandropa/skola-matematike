# server/dependencies.py

import logging
from google import genai
from fastapi import HTTPException, status, Depends

logger = logging.getLogger(__name__)

# Import settings (assuming server/config.py)
try:
    from .config import settings
except ImportError as e:
    logger.error(f"Failed to import settings from config.py: {e}")
    raise

# Import the service class you just created
try:
    from .services.gemini_service import GeminiService
except ImportError as e:
    logger.error(f"Failed to import GeminiService: {e}")
    raise


# Module-level variables for caching
_cached_gemini_client = None
_cached_gemini_service = None # Cache the service instance too

def get_gemini_client():
    """
    FastAPI dependency function to get a cached Gemini client instance (API Key focus).
    """
    global _cached_gemini_client

    if _cached_gemini_client is None:
        logger.info("Instantiating new Gemini client (first request).")
        api_key = settings.GEMINI_API_KEY # Get API key from settings
        if not api_key:
             logger.error("API Key not found in settings.")
             raise HTTPException(
                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                 detail="AI service is not configured correctly (API Key missing)."
             )
        try:
            _cached_gemini_client = genai.Client(api_key=api_key)
            logger.debug("Gemini Client (API Key) instantiated.")
            # Optional: Connectivity check
            # try:
            #      _cached_gemini_client.list_models()
            #      logger.debug("Gemini client connectivity check successful.")
            # except Exception as conn_e:
            #       logger.warning(f"Gemini client connectivity check failed: {conn_e}", exc_info=True)

        except Exception as e:
            logger.error(f"Failed to instantiate Gemini client: {e}", exc_info=True)
            raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail="Failed to initialize connection to AI service."
            )
    else:
         logger.debug("Using cached Gemini client.")

    return _cached_gemini_client


# NEW: Dependency provider for the GeminiService
def get_gemini_service(
    client: genai.Client = Depends(get_gemini_client) # Depends on the client dependency
) -> GeminiService:
    """
    FastAPI dependency function to get a cached GeminiService instance.
    """
    global _cached_gemini_service

    if _cached_gemini_service is None:
        logger.info("Instantiating new GeminiService (first request).")
        # Instantiate the service, injecting the client it needs
        _cached_gemini_service = GeminiService(client=client)
    else:
        logger.debug("Using cached GeminiService.")

    return _cached_gemini_service

# Keep or add other dependency providers here
# def get_db_session(): ...