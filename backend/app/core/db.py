from typing import Generator


def get_db() -> Generator:
    """
    FastAPI dependency that yields a DB session.
    Currently a stub — yields None so the server starts without a real DB.
    Replace with real SQLAlchemy/asyncpg session when Supabase is connected.
    """
    db = None
    try:
        yield db
    finally:
        pass