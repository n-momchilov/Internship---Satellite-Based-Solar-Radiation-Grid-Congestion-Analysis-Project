import geopandas as gpd
import json

gdf = gpd.read_file('congestion_risk_grid.gpkg', layer='congestion_risk')
gdf = gdf.to_crs(epsg=4326)

sentinel_cols = [
    'bevolkingsdichtheid_inwoners_per_km2', 'omgevingsadressendichtheid',
    'stedelijkheid_adressen_per_km2', 'gemiddeld_elektriciteitsverbruik_totaal',
    'woningvoorraad', 'percentage_meergezinswoning', 'percentage_koopwoningen'
]
for col in sentinel_cols:
    if col in gdf.columns:
        gdf[col] = gdf[col].where(gdf[col] > -9000, other=None)

gdf.to_file('grid_data.geojson', driver='GeoJSON')
print(f"Exported {len(gdf)} cells to grid_data.geojson")
print(f"Columns: {list(gdf.columns)}")
