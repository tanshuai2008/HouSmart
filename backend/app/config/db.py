"""Backward-compatible Supabase access.

Many services import `require_supabase()` from here. The actual Supabase client
is configured in `app.core.supabase_client` via `settings`.
"""

from app.core.supabase_client import supabase


def require_supabase():
	"""Return configured Supabase client or raise a clear error."""

	# `app.core.supabase_client.supabase` is either a real Client or a sentinel
	# object that raises on attribute access.
	try:
		getattr(supabase, "table")
	except Exception as exc:
		raise RuntimeError(
			"Supabase is not configured. Set SUPABASE_URL and a key (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY)."
		) from exc

	return supabase
