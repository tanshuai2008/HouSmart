from supabase import Client, create_client
from app.core.config import settings

supabase_key = (
    settings.SUPABASE_SERVICE_ROLE_KEY
    or settings.SUPABASE_KEY
    or settings.SUPABASE_ANON_KEY
)

if not settings.SUPABASE_URL or not supabase_key:
    raise RuntimeError("Missing SUPABASE_URL or Supabase key environment variable")

supabase: Client = create_client(settings.SUPABASE_URL, supabase_key)
