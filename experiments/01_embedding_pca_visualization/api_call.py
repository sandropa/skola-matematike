from google import genai
import dotenv
import os

dotenv.load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(api_key)

client = genai.Client(api_key=api_key)

result = client.models.embed_content(
    model="gemini-embedding-exp-03-07",
    contents="How does alphafold work?",
)

print(result.embeddings)
