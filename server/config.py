# server/config.py
import os
from dotenv import load_dotenv

# Construct the path to the .env file in the parent directory (SKOLA-MATEMATIKE)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    # --- API Keys ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

    # -- Gemini models --
    GEMINI_FLASH_2_5="gemini-2.5-flash-preview-05-20"
    GEMINI_PRO_2_5="gemini-2.5-pro-preview-05-06"

    # --- Database Connection ---
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost") # Default to localhost
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")       # Default to 5432
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")             # e.g., "math_school"

    # --- Constructed Database URL ---
    SQLALCHEMY_DATABASE_URL: str = None # Initialize as None

    # Check if essential DB components are present before constructing URL
    if all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_SERVER, POSTGRES_PORT]):
        SQLALCHEMY_DATABASE_URL = (
            f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
            f"{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )
    else:
        # Keep SQLALCHEMY_DATABASE_URL as None if essential parts are missing
        print("Warning: One or more essential PostgreSQL environment variables "
              "(POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB) are missing in .env. "
              "Database connection will fail.")


# Instantiate the settings
settings = Settings()

# --- Optional Checks (can be placed after instantiation) ---
if not settings.GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables. Check your .env file.")

if not settings.SQLALCHEMY_DATABASE_URL:
     print("Critical Warning: SQLALCHEMY_DATABASE_URL could not be constructed. "
           "Database operations will fail. Check .env and PostgreSQL variables.")
