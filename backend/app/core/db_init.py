from sqlalchemy import text
from app.core.database import engine


def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_properties_location
            ON properties
            USING GIST (location);
        """))
        conn.commit()