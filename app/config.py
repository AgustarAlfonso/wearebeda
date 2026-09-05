import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = os.getenv("DATA_PATH", str(BASE_DIR / "data" / "data.md"))
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "beda_system.db"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLASSIFY_MODEL = os.getenv("CLASSIFY_MODEL", "claude-haiku-4-5-20251001")
DRAFT_MODEL = os.getenv("DRAFT_MODEL", "claude-sonnet-5")
