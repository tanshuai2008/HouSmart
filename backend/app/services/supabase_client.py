from __future__ import annotations
import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from supabase import Client
from app.core.supabase_client import supabase as core_supabase

class SupabaseConfigError(RuntimeError):
    """Raised when required Supabase environment variables are missing."""

# Ensure .env is loaded even for direct script execution from different CWDs.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_DIR / ".env")

def _get_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise SupabaseConfigError(f"Environment variable '{var_name}' is required for Supabase access")
    return value

def _get_supabase_key() -> str:
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not key:
        raise SupabaseConfigError("Set SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY for Supabase access")
    return key

@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached Supabase client instance."""
    _get_env("SUPABASE_URL")
    _get_supabase_key()
    return core_supabase

def ensure_supabase_ready() -> None:
    """Force the Supabase client to initialize to fail fast during startup."""
    get_supabase()
