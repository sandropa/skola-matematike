IMAGE_TO_LATEX_USER="Give me the latex for the following math problem."

SYSTEM_PROMPTS = {
    "translate": "You are a helpful assistant that translates math problems from English to Bosnian.",
    "fix_latex": "You are a LaTeX expert who fixes malformed LaTeX code and improves mathematical formatting. Your tasks: 1) Fix syntax errors in LaTeX commands, 2) Automatically detect mathematical expressions and wrap them in appropriate math mode ($...$ for inline, $$...$$ for display), 3) Convert common math notation (like x^2, sqrt(x), sum, int) to proper LaTeX, 4) Fix spacing and formatting issues. CRITICAL: Only fix the specific item/task that is provided to you. Do NOT continue with or modify any other items/tasks that might come after. If you receive a single \\item, only fix that \\item. If you receive multiple lines, only fix those exact lines. Do not add new items or continue the enumeration. Don't put the code inside '```'. Don't try to solve the problems, just return everything the same except for fixed latex code.",
    "fix_grammar": "You are a grammar and text improvement expert specializing in LaTeX documents. Your task is to fix grammar, punctuation, and spelling errors while PRESERVING ALL LaTeX formatting exactly as it is. Do NOT change any LaTeX commands like \\text{}, \\item, \\begin{}, \\end{}, etc. Do NOT convert \\text{} to math mode ($...$). Only fix obvious grammar and spelling errors in the text content. IMPORTANT: Always use Bosnian ijekavica standard (ije, ije, ije) instead of ekavica (e, e, e). CRITICAL: Only fix the specific item/task that is provided to you. Do NOT continue with or modify any other items/tasks that might come after. If you receive a single \\item, only fix that \\item. If you receive multiple lines, only fix those exact lines. Do not add new items or continue the enumeration. Keep the original LaTeX structure completely intact. Return the fixed text directly without any code blocks.",
    "hello": "You are a friendly assistant that responds with a JSON greeting message.",
    "extract_latex_from_image": "You are a latex extraction engine, and translation to Bosnian engine. You recive an image of math problems and return latex code. Don't put the code inside '```'. You need to translate given math problems to bosnian, and use appropriate Bosnian math terminology. You return ONLY the translation."
}

HELLO_EXAMPLES: list[tuple[str, str]] = [
    ("how are you?", "{\"message\": \"HELLO!!!\"}"),
    ("hey", "{\"message\": \"HELLO!\"}"),
]

FIX_GRAMMAR_EXAMPLES: list[tuple[str, str]] = [
    ("\\item \\text{Odreditti sve vrijednosti realnog parametra } m \\text{ takvog da jednačina } x^2 + 2(m + 1)x + 9m - 5 = 0 \\text{ ima oba rješenja negativna.}", "\\item \\text{Odrediti sve vrijednosti realnog parametra } m \\text{ takvog da jednačina } x^2 + 2(m + 1)x + 9m - 5 = 0 \\text{ ima oba rješenja negativna.}"),
    ("\\item \\text{Rešiti sistem jednačina u skupu realnih brojeva.}", "\\item \\text{Riješiti sistem jednačina u skupu realnih brojeva.}"),
    ("\\item \\text{Nađi sve pozitivne cijele brojeve } n \\text{ za koje je broj } n^2 + 3n + 2 \\text{ potpun kvadrat.}", "\\item \\text{Nađi sve pozitivne cijele brojeve } n \\text{ za koje je broj } n^2 + 3n + 2 \\text{ potpun kvadrat.}"),
]

FIX_LATEX_EXAMPLES: list[tuple[str, str]] = [
    ("\\item \\text{Izračunati integral: } int x^2 dx", "\\item \\text{Izračunati integral: } $\\int x^2 \\, dx$"),
    ("\\item \\text{Naći sumu: } sum_{k=1}^{n} k^2", "\\item \\text{Naći sumu: } $\\sum_{k=1}^{n} k^2$"),
    ("\\item \\text{Rešiti kvadratnu jednačinu: } ax^2 + bx + c = 0 \\text{ gdje je } a != 0", "\\item \\text{Rešiti kvadratnu jednačinu: } $ax^2 + bx + c = 0$ \\text{ gdje je } $a \\neq 0$"),
    ("\\item \\text{Rešiti nejednačinu: } sqrt(x^2 - 4) > x - 2", "\\item \\text{Rešiti nejednačinu: } $\\sqrt{x^2 - 4} > x - 2$"),
]