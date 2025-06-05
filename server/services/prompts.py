IMAGE_TO_LATEX_USER="Give me the latex for the following math problem."

SYSTEM_PROMPTS = {
    "translate": "You are a helpful assistant that translates math problems from English to Bosnian.",
    "fix_latex": "You are a LaTeX expert who fixes malformed LaTeX code. Don't put the code inside '```'. Don't try to solve the problems, just return everything the same except for fixed latex code.",
    "hello": "You are a friendly assistant that responds with a JSON greeting message.",
}

HELLO_EXAMPLES: list[tuple[str, str]] = [
    ("how are you?", "{\"message\": \"HELLO!!!\"}"),
    ("hey", "{\"message\": \"HELLO!\"}"),
]