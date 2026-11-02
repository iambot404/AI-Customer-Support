import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production-support-triage-2026")
    
    # Database configuration: defaults to local SQLite file
    # For Supabase / Postgres: set DATABASE_URL=postgresql://postgres:...
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    SQLITE_PATH = os.environ.get("SQLITE_PATH", str(BASE_DIR / "support_tickets.db"))

    # Supabase credentials
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mcgbcmaybudlfowynvgi.supabase.co")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

    # Gemini configuration
    # Check env first, then fallback to keys.txt if needed
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        keys_file = BASE_DIR / "keys.txt"
        if keys_file.exists():
            content = keys_file.read_text(encoding="utf-8").strip()
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                            gemini_key = v.strip().strip("'\"")
                            break
                    else:
                        gemini_key = line
                        break
    GEMINI_API_KEY = gemini_key

    # Comma-separated API keys for rotation
    api_keys_str = os.environ.get("GEMINI_API_KEYS", "") or gemini_key
    GEMINI_API_KEYS = [k.strip() for k in api_keys_str.split(",") if k.strip()]

    # Models list with priority fallback
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")
    models_str = os.environ.get("GEMINI_MODELS", "gemini-flash-lite-latest,gemini-3.1-flash-lite,gemini-3.8-flash")
    GEMINI_MODELS = [m.strip() for m in models_str.split(",") if m.strip()]
    if GEMINI_MODEL not in GEMINI_MODELS:
        GEMINI_MODELS.insert(0, GEMINI_MODEL)

    # Allowed taxonomy per specification
    CATEGORIES = [
        "Technical Issue",
        "Billing & Payments",
        "Account & Access",
        "Feature Request",
        "General Inquiry"
    ]

    PRIORITIES = [
        "Urgent",
        "High",
        "Medium",
        "Low"
    ]

    STATUSES = [
        "Open",
        "In Progress",
        "Resolved"
    ]

    CLASSIFICATION_STATUSES = [
        "Pending",
        "Completed",
        "Failed"
    ]
