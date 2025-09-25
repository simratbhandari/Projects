import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
    AI_MIN_CONFIDENCE = float(os.getenv("AI_MIN_CONFIDENCE", "0.65"))

    # Basic guard knobs
    RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))
    RATE_LIMIT_BURST = int(os.getenv("RATE_LIMIT_BURST", "30"))
    BLOCK_DURATION_SECONDS = int(os.getenv("BLOCK_DURATION_SECONDS", "900"))

    # Misc
    ENV = os.getenv("FLASK_ENV", "production")