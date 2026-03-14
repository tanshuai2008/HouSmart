from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    # Some feature branches used SUPABASE_KEY instead of SUPABASE_SERVICE_ROLE_KEY.
    SUPABASE_KEY: str = ""

    # External APIs
    CENSUS_API_KEY: str = ""
    FBI_API_KEY: str = ""
    FBI_API_BASE_URL: str = "https://api.usa.gov/crime/fbi/cde"

    # Flood service
    FLOOD_CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 180
    FEMA_QUERY_URL: str = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
    FEMA_HTTP_TIMEOUT_SECONDS: int = 15
    FEMA_DEBUG_TIMEOUT_SECONDS: int = 30

    # Shared HTTP config
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

    # Geocoding (OSM Nominatim)
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org/search"
    NOMINATIM_HTTP_TIMEOUT_SECONDS: int = 10

    # Caching (Supabase)
    MEDIAN_HOUSE_PRICE_CACHE_TTL_SECONDS: int = 60 * 60 * 24  # 24h
    NOISE_CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 30  # 30d

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
