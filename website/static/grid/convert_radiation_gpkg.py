import geopandas as gpd
import pandas as pd
import os

gpkg_path = os.path.join('..', 'congestion_radiation_grid.gpkg')

gdf = gpd.read_file(gpkg_path)
print(f"Loaded {len(gdf)} cells")
print(f"Columns: {list(gdf.columns)}")
print(f"CRS: {gdf.crs}")

gdf = gdf.to_crs(epsg=4326)

# Derived columns
gdf['solar_radiation_daily_summer'] = gdf['GHI_summer'] * 24 / 1000
gdf['seasonal_variation_ratio'] = gdf['GHI_seasonal_ratio']

# Combined priority score
cong_norm = gdf['congestion_class'].fillna(0) / 2
ghi_max = gdf['GHI_annual_mean'].max()
ghi_norm = gdf['GHI_annual_mean'].fillna(0) / (ghi_max if ghi_max > 0 else 1)
pv_max = gdf['pv_penetration'].max() if 'pv_penetration' in gdf.columns else 1
pv_norm = gdf['pv_penetration'].fillna(0) / (pv_max if pv_max > 0 else 1) if 'pv_penetration' in gdf.columns else 0
gdf['combined_priority'] = 0.50 * cong_norm + 0.25 * ghi_norm + 0.25 * pv_norm

def label_priority(x):
    if pd.isna(x): return None
    if x > 0.66: return 'High'
    if x > 0.33: return 'Medium'
    return 'Low'

gdf['combined_priority_label'] = gdf['combined_priority'].apply(label_priority)

# Shorten congestion driver names
driver_map = {
    'Solar-driven congestion': 'Solar-driven',
    'Consumption-driven congestion': 'Consumption-driven',
    'Mixed drivers': 'Mixed',
    'Low/Medium risk': 'Low risk'
}
if 'congestion_driver' in gdf.columns:
    gdf['congestion_driver_short'] = gdf['congestion_driver'].map(driver_map).fillna('No data')
    print(f"Driver value counts:\n{gdf['congestion_driver_short'].value_counts()}")
else:
    gdf['congestion_driver_short'] = 'No data'
    print("Warning: congestion_driver column not found")

# Select only columns needed for radiation layer
keep = ['cell_id', 'GHI_annual_mean', 'GHI_summer', 'GHI_winter',
        'GHI_seasonal_ratio', 'solar_radiation_daily_summer',
        'seasonal_variation_ratio', 'congestion_driver_short',
        'combined_priority', 'combined_priority_label']
export_cols = [c for c in keep if c in gdf.columns]

gdf[export_cols + ['geometry']].to_file('radiation_layer.geojson', driver='GeoJSON')
print(f"\nExported {len(gdf)} cells to radiation_layer.geojson")
print(f"Columns: {export_cols}")
