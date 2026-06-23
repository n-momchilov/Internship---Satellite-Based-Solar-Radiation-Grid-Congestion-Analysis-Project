import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import json
import pandas as pd

def render():
    # Load GeoJSON data
    grid_dir = Path("static/grid")

    grid_json = "{}"
    rad_json = "{}"
    seasonal_ghi_json = "{}"

    grid_path = grid_dir / "grid_data.geojson"
    rad_path = grid_dir / "radiation_layer.geojson"

    if grid_path.exists():
        grid_json = grid_path.read_text(encoding="utf-8")
    else:
        st.warning("grid_data.geojson not found in static/grid/")

    if rad_path.exists():
        rad_json = rad_path.read_text(encoding="utf-8")
    else:
        st.warning("radiation_layer.geojson not found in static/grid/")

    gpkg_candidates = [
        Path("../congestion_radiation_grid.gpkg"),
        Path("congestion_radiation_grid.gpkg"),
        grid_dir / "congestion_radiation_grid.gpkg",
    ]
    gpkg_path = next((p for p in gpkg_candidates if p.exists()), None)
    if gpkg_path is not None:
        try:
            import geopandas as gpd

            seasonal_cols = ["cell_id", "GHI_spring", "GHI_summer", "GHI_autumn", "GHI_winter"]
            seasonal_grid = gpd.read_file(gpkg_path, ignore_geometry=True)
            if all(col in seasonal_grid.columns for col in seasonal_cols):
                seasonal_grid = seasonal_grid[seasonal_cols].dropna(subset=["cell_id"])
                seasonal_data = {}
                for _, row in seasonal_grid.iterrows():
                    cell_id = int(row["cell_id"])
                    seasonal_data[cell_id] = {
                        col: None if row[col] is None or pd.isna(row[col]) else float(row[col])
                        for col in seasonal_cols
                        if col != "cell_id"
                    }
                seasonal_ghi_json = json.dumps(seasonal_data)
        except Exception:
            seasonal_ghi_json = "{}"

    # Read the map HTML
    map_html_path = grid_dir / "map.html"
    if not map_html_path.exists():
        st.error("map.html not found in static/grid/")
        return

    html_content = map_html_path.read_text(encoding="utf-8")

    # Read CSS and JS
    css_path = grid_dir / "style.css"
    js_path = grid_dir / "script.js"

    css_content = css_path.read_text(encoding="utf-8") if css_path.exists() else ""
    js_content = js_path.read_text(encoding="utf-8") if js_path.exists() else ""

    # Build a self-contained HTML page with inline data, CSS, and JS
    # This avoids all external file loading issues inside Streamlit
    inline_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css" />
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500&family=JetBrains+Mono:ital,wght@0,400;0,500&display=swap" rel="stylesheet">
    <style>{css_content}</style>
</head>
<body>
    <script>
      const GRID_DATA_INLINE = {grid_json};
      const RADIATION_DATA_INLINE = {rad_json};
      const SEASONAL_GHI_BY_CELL_INLINE = {seasonal_ghi_json};
      const USE_INLINE_DATA = true;
    </script>"""

    # Extract the body content from map.html (everything between <body> and </body>)
    import re
    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
    if body_match:
        body_content = body_match.group(1)
        # Remove external script/css references (we inline them)
        body_content = re.sub(r'<link[^>]*stylesheet[^>]*>', '', body_content)
        body_content = re.sub(r'<script[^>]*src="style\.css"[^>]*></script>', '', body_content)
        body_content = re.sub(r'<script[^>]*src="script\.js"[^>]*></script>', '', body_content)
        # Remove the inline GRID_GEOJSON_URL script block (we replace with inline data)
        body_content = re.sub(r"<script>\s*const GRID_GEOJSON_URL.*?</script>", '', body_content, flags=re.DOTALL)
    else:
        body_content = html_content

    inline_html += body_content
    inline_html += f"""
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
    <script>{js_content}</script>
</body>
</html>"""

    st.markdown("""<style>
[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],
section.main > div.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

[data-testid="stIFrame"],
iframe {
    width: 100% !important;
}
</style>""", unsafe_allow_html=True)
    components.html(inline_html, height=1500, scrolling=True)
