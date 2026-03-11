from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    SUPABASE_URL : str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_ANON_KEY: str
    GOOGLE_MAPS_API_KEY: str

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()