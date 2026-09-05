import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present in project root or app folder
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / "app" / ".env")

DATA_PATH = os.getenv("DATA_PATH", str(BASE_DIR / "data" / "data.md"))
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "beda_system.db"))

# Gemini API Configuration (Default LLM Engine: Gemini 3.8 Flash)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Anthropic Configuration (Secondary / Legacy Fallback)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLASSIFY_MODEL = os.getenv("CLASSIFY_MODEL", "claude-haiku-4-5-20251001")
DRAFT_MODEL = os.getenv("DRAFT_MODEL", "claude-sonnet-5")

