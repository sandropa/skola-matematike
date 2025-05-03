# server/dependencies.py

import logging
from google import genai
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session # Import Session type

# Import settings (assuming server/config.py)
try:
    from .config import settings
except ImportError as e:
    logging.error(f"Failed to import settings from config.py: {e}")
    raise # Critical error

# Import service classes
try:
    from .services.gemini_service import GeminiService
    from .services.problemset_service import ProblemsetService # Import the new service
except ImportError as e:
    logging.error(f"Failed to import service classes: {e}")
    raise # Critical error

# Import database dependency provider (assuming server/database.py)
try:
    from .database import get_db # Import the database session dependency
except ImportError as e:
    logging.error(f"Failed to import get_db from database.py: {e}")
    raise # Critical error


logger = logging.getLogger(__name__)

# Module-level variables for caching service instances
_cached_gemini_client = None
_cached_gemini_service = None
_cached_lecture_service = None

# Dependency provider for the Gemini Client (API Key version)
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


# Dependency provider for the GeminiService
def get_gemini_service(
    client: genai.Client = Depends(get_gemini_client) # Depends on the client dependency
) -> GeminiService:
    """
    FastAPI dependency function to get a cached GeminiService instance.
    """
    global _cached_gemini_service

    if _cached_gemini_service is None:
        logger.info("Instantiating new GeminiService (first request).")
        _cached_gemini_service = GeminiService(client=client) # Instantiate the service
    else:
        logger.debug("Using cached GeminiService.")

    return _cached_gemini_service


# Dependency provider for the LectureService
def get_lecture_service() -> ProblemsetService:
    """
    FastAPI dependency function to get a cached LectureService instance.
    DB session is passed per-method to allow service methods to be simpler.
    """
    global _cached_lecture_service

    if _cached_lecture_service is None:
        logger.info("Instantiating new LectureService (first request).")
        _cached_lecture_service = ProblemsetService() # Instantiate the service
    else:
        logger.debug("Using cached LectureService.")

    return _cached_lecture_service

# The get_db dependency is imported from database.py
# Its signature is def get_db(): yield SessionLocal() ...