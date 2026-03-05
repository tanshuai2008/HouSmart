from __future__ import annotations
import os
from functools import lru_cache
from supabase import Client, create_client

class SupabaseConfigError(RuntimeError):
    """Raised when required Supabase environment variables are missing."""

def _get_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise SupabaseConfigError(f"Environment variable '{var_name}' is required for Supabase access")
    return value

def _get_supabase_key() -> str:
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not key:
        raise SupabaseConfigError("Set SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY for Supabase access")
    return key

@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached Supabase client instance using the official API."""
    url = _get_env("SUPABASE_URL")
    key = _get_supabase_key()
    return create_client(url, key)

def ensure_supabase_ready() -> None:
    """Force the Supabase client to initialize to fail fast during startup."""
    get_supabase()
