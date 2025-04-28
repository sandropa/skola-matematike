# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
from google import genai
from google.genai import types
import dotenv
import os

dotenv.load_dotenv()

def generate():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    files = [
        # Please ensure that the file is available in local system working direrctory or change the file path.
        client.files.upload(file="server/routers/test.pdf"),
    ]
    model = "gemini-2.5-flash-preview-04-17"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_uri(
                    file_uri=files[0].uri,
                    mime_type=files[0].mime_type,
                ),
                types.Part.from_text(text="""INSERT_INPUT_HERE"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["lecture_name", "group_name", "problems_latex"],
            properties = {
                "lecture_name": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The main title or name of the lecture topic found in the document.",
                ),
                "group_name": genai.types.Schema(
                    type = genai.types.Type.STRING,
                    description = "The target group for the lecture (e.g., 'Početna grupa', 'Srednja grupa', 'Napredna grupa', 'Predolimpijska grupa', 'Olimpijska grupa').",
                ),
                "problems_latex": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    description = "A list containing the extracted LaTeX source string for each distinct problem identified in the document.",
                    items = genai.types.Schema(
                        type = genai.types.Type.STRING,
                        description = "The full LaTeX representation of a single math problem.",
                    ),
                ),
            },
        ),
        system_instruction=[
            types.Part.from_text(text="""You are an extraction engine for math lectures. You translate PDFs into JSON of the lecture, and problems in the lecture in Latex."""),
        ],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")

if __name__ == "__main__":
    generate()
