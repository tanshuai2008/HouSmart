import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Ensure we load the project env file even when running scripts from other CWDs.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing Supabase credentials")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
