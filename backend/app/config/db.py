import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Ensure we load the project env file even when running scripts from other CWDs.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Keep this as a module-level singleton to match existing imports.
# If credentials are missing, this stays as None so the API can still start
# for endpoints that don't require Supabase.
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


def require_supabase():
    if supabase is None:
        raise RuntimeError(
            "Missing Supabase credentials (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)"
        )
    return supabase
