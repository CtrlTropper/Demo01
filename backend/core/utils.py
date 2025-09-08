import re

def sanitize_input(text: str) -> str:
    """Sanitize input để tránh injection attacks."""
    text = re.sub(r'[^\w\s.,;:()\[\]?!\"\'\-–—…°%‰≥≤→←≠=+/*<>\n\r]', '', text)
    return text.strip()