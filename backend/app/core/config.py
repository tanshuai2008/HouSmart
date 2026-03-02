from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Required credentials
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # Flood service
    FLOOD_CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 180
    FEMA_QUERY_URL: str = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
    FEMA_HTTP_TIMEOUT_SECONDS: int = 15
    FEMA_DEBUG_TIMEOUT_SECONDS: int = 30
    HTTP_USER_AGENT: str = "Mozilla/5.0 (compatible; HouSmart/1.0)"

    # Transit service
    TRANSIT_CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 30
    OVERPASS_HTTP_TIMEOUT_SECONDS: int = 30
    OVERPASS_QUERY_TIMEOUT_SECONDS: int = 25
    OVERPASS_MIRRORS: str = (
        "https://overpass-api.de/api/interpreter,"
        "https://overpass.kumi.systems/api/interpreter,"
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
