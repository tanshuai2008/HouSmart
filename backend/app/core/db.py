from typing import Generator
from supabase import Client
from app.core.supabase_client import supabase


def get_db() -> Generator[Client, None, None]:
    """FastAPI dependency — yields the shared Supabase client."""
    try:
        yield supabase
    finally:
        pass