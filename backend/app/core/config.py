from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings across all integrated service modules."""

    # Shared Supabase credentials
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""

    # Amenity/Education/Income
    CENSUS_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""
    GOOGLE_PLACES_HTTP_TIMEOUT_SECONDS: int = 15
    GOOGLE_ROADS_HTTP_TIMEOUT_SECONDS: int = 15

    # Flood service
    FLOOD_CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 180
    FEMA_QUERY_URL: str = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
    FEMA_HTTP_TIMEOUT_SECONDS: int = 15
    FEMA_DEBUG_TIMEOUT_SECONDS: int = 30
    HTTP_USER_AGENT: str = "Mozilla/5.0 (compatible; HouSmart/1.0)"

    # Transit service
    TRANSIT_CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 30
    CRIME_CACHE_TTL_SECONDS: int = 60 * 60 * 24 * 7

    # Geocoding
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org/search"
    NOMINATIM_HTTP_TIMEOUT_SECONDS: int = 10

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
