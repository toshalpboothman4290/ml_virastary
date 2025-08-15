import re
def detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06FF]", text): return "fa"
    if re.search(r"[A-Za-z]", text): return "en"
    return "fa"
