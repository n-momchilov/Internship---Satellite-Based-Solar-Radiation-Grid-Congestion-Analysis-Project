# ui/map.py

import folium
from folium.plugins import Draw
from streamlit_folium import st_folium


def build_map(
    center_lat,
    center_lon,
    roi_bounds,
    overlay=None,
    overlay_bounds=None,
    overlays=None,
    caption_fn=None,
):
    """
    If 'overlays' is provided, it should be a list of dicts:
      {"image": rgba_array,
       "bounds": [[lat_min, lon_min],[lat_max, lon_max]],
       "opacity": float}

    'overlay' + 'overlay_bounds' are kept for backward compatibility (single layer).
    """
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=9,
        control_scale=True,
        prefer_canvas=True,
        width="100%",
        height="520px",
    )

    # ROI rectangle
    (lat_min, lon_min), (lat_max, lon_max) = roi_bounds
    folium.Rectangle(
        [[lat_min, lon_min], [lat_max, lon_max]],
        color="#ef4444",
        weight=2,
        dash_array="6",
        fill=True,
        fill_opacity=0.08,
    ).add_to(m)

    # Prepare overlay list
    overlay_list = []
    if overlays:
        overlay_list = overlays
    elif overlay is not None and overlay_bounds is not None:
        overlay_list = [{"image": overlay, "bounds": overlay_bounds, "opacity": 0.85}]

    # Add overlays if present
    for ol in overlay_list:
        folium.raster_layers.ImageOverlay(
            image=ol["image"],
            bounds=ol["bounds"],
            opacity=ol.get("opacity", 0.85),
            interactive=False,
            cross_origin=False,
        ).add_to(m)

    if overlay_list and caption_fn:
        caption_fn()

    # Draw controls
    draw = Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": False,
            "polygon": False,
            "circle": False,
            "circlemarker": False,
            "marker": True,
            "rectangle": True,
        },
        edit_options={"edit": True, "remove": True},
    )
    draw.add_to(m)

    return st_folium(m, height=520, key="roi_map", use_container_width=True)
