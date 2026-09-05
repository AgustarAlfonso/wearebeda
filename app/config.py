import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present in project root or app folder
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "app" / ".env")

DATA_PATH = os.getenv("DATA_PATH", str(BASE_DIR / "data" / "data.md"))
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "beda_system.db"))

# Gemini API Configuration with Multi-Model Fallback Cascade
# If the primary model hits rate limit or quota, system cascades to next available model.
DEFAULT_GEMINI_FALLBACKS = [
    "gemini-3.6-flash",       # Primary workhorse (suksesor resmi 2.5-flash, kuota aktif & cepat)
    "gemini-3.7-flash",       # Fallback 1: High intelligence flash model
    "gemini-3.5-flash-lite",  # Fallback 2: Suksesor resmi 2.5-flash-lite (hemat kuota)
    "gemini-3.1-flash-lite",  # Fallback 3: Ultra-low latency & kuota cadangan
    "gemini-3.8-flash",       # Fallback 4: Flagship reasoning model (jika kuota harian tersedia)
]

raw_models = os.getenv("GEMINI_MODELS", "")
if raw_models:
    GEMINI_MODELS = [m.strip() for m in raw_models.split(",") if m.strip()]
elif os.getenv("GEMINI_MODEL"):
    single = os.getenv("GEMINI_MODEL").strip()
    GEMINI_MODELS = [single] + [m for m in DEFAULT_GEMINI_FALLBACKS if m != single]
else:
    GEMINI_MODELS = DEFAULT_GEMINI_FALLBACKS

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = GEMINI_MODELS[0]

# Anthropic Configuration (Secondary / Legacy Fallback)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLASSIFY_MODEL = os.getenv("CLASSIFY_MODEL", "claude-haiku-4-5-20251001")
DRAFT_MODEL = os.getenv("DRAFT_MODEL", "claude-sonnet-5")


