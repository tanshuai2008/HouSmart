from __future__ import annotations

from supabase import Client, create_client

from app.core.config import settings


class _SupabaseNotConfigured:
    def __getattr__(self, name: str):
        raise RuntimeError(
            "Supabase is not configured. Set SUPABASE_URL and a key (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY)."
        )


def _resolve_supabase_key() -> str:
    return (
        settings.SUPABASE_SERVICE_ROLE_KEY
        or settings.SUPABASE_KEY
        or settings.SUPABASE_ANON_KEY
        or ""
    )


_key = _resolve_supabase_key()
if settings.SUPABASE_URL and _key:
    supabase: Client = create_client(settings.SUPABASE_URL, _key)
else:
    supabase = _SupabaseNotConfigured()
