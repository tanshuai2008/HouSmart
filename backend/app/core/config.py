from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
