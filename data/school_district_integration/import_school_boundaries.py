import geopandas as gpd
from sqlalchemy import create_engine, text
from geoalchemy2 import Geometry
from shapely.geometry import Polygon, MultiPolygon
from urllib.parse import quote_plus

# ===============================
# CONFIG
# ===============================

PROJECT_REF = ""
DB_USER = ""

# ⚠️ PASTE YOUR *DATABASE* PASSWORD HERE (NOT SUPABASE LOGIN)
RAW_DB_PASSWORD = ""

DB_PASSWORD = quote_plus(RAW_DB_PASSWORD)

DB_CONNECTION_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}"
    f"@db.{PROJECT_REF}.supabase.co:5432/postgres"
)

SHAPEFILE_PATH = "/Users/sudhirachegu/Downloads/TL_2025_SD/TL_2025_US_SDU.shp"
TABLE_NAME = "school_districts"

# ===============================
# 1. TEST CONNECTION (FAIL FAST)
# ===============================

print("Testing database connection...")
engine = create_engine(DB_CONNECTION_URL)

with engine.connect() as conn:
    print("Connected as:", conn.execute(text("SELECT current_user;")).fetchone())

print("✅ Database connection successful\n")

# ===============================
# 2. LOAD SHAPEFILE
# ===============================

print("Loading Unified School District shapefile...")
gdf = gpd.read_file(SHAPEFILE_PATH)

# ===============================
# 3. MAP COLUMNS
# ===============================

print("Mapping columns to schema...")
gdf = gdf.rename(
    columns={
        "GEOID": "district_id",
        "NAME": "name",
        "STATEFP": "state",
    }
)

gdf = gdf[["district_id", "name", "state", "geometry"]]

# ===============================
# 4. CRS → EPSG:4326
# ===============================

if gdf.crs != "EPSG:4326":
    print("Reprojecting to EPSG:4326...")
    gdf = gdf.to_crs(epsg=4326)

# ===============================
# 5. FORCE MULTIPOLYGON
# ===============================

print("Enforcing MultiPolygon format...")

def enforce_multipolygon(geom):
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    return geom

gdf["geometry"] = gdf["geometry"].apply(enforce_multipolygon)

gdf = gdf.rename(columns={"geometry": "boundary"})
gdf = gdf.set_geometry("boundary")

# ===============================
# 6. UPLOAD TO SUPABASE (CHUNKED)
# ===============================

print("Uploading data to Supabase...")

gdf.to_postgis(
    name=TABLE_NAME,
    con=engine,
    if_exists="replace",
    index=False,
    chunksize=1000,
    dtype={"boundary": Geometry("MULTIPOLYGON", srid=4326)},
)

print("✅ Success! School boundaries imported into Supabase.")