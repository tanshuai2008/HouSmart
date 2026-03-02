# HouSmart/backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""

    CENSUS_API_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
