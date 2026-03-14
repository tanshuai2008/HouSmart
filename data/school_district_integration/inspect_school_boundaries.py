import geopandas as gpd


file_path = "/Users/sudhirachegu/Downloads/TL_2025_SD/TL_2025_US_SDU.shp"

# 2. Load the shapefile into memory
print("Loading Unified School District shapefile... (this might take a few seconds)")
gdf = gpd.read_file(file_path)

# 3. Print the column names
print("\n--- Exact Column Names ---")
print(gdf.columns.tolist())

# 4. Print a preview of the data
print("\n--- First 3 Rows of Data ---")
print(gdf.head(3))