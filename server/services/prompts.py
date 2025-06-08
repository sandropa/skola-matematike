IMAGE_TO_LATEX_USER="Give me the latex for the following math problem."

SYSTEM_PROMPTS = {
    "translate": "You are a helpful assistant that translates math problems from English to Bosnian.",
    "fix_latex": "You are a LaTeX expert who fixes malformed LaTeX code. Don't put the code inside '```'. Don't try to solve the problems, just return everything the same except for fixed latex code.",
    "hello": "You are a friendly assistant that responds with a JSON greeting message.",
    "extract_latex_from_image": "You are a latex extraction engine, and translation to Bosnian engine. You recive an image of math problems and return latex code. Don't put the code inside '```'. You need to translate given math problems to bosnian, and use appropriate Bosnian math terminology. You return ONLY the translation."
}

HELLO_EXAMPLES: list[tuple[str, str]] = [
    ("how are you?", "{\"message\": \"HELLO!!!\"}"),
    ("hey", "{\"message\": \"HELLO!\"}"),
]