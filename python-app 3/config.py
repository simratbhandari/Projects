import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1200"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

    # Security headers / CSP (relaxed for CDN usage)
    CONTENT_SECURITY_POLICY = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com https://unpkg.com 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "font-src 'self' data:; "
        "media-src 'self'"
    )