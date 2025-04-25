# server/config.py
import os
from dotenv import load_dotenv

# Construct the path to the .env file in the parent directory (SKOLA-MATEMATIKE)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")

settings = Settings()

# Optional: Add a check here if you want immediate feedback on startup
if not settings.GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables. Check your .env file.")
    # In a real app, you might want to raise an error here or handle it differently