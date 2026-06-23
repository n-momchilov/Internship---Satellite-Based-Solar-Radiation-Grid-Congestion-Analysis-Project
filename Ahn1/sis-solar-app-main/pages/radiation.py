# pages/radiation.py

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

from core import state
from core.services.geocode import geocode_osm, pick_best_hit, fuzzy_suggest
from ui.components import confirm_box
from ui import map as ui_map

# -----------------------
# Paths / meta loading
# -----------------------

ROOT = Path(__file__).resolve().parents[1]
UI_META_PATH = ROOT / "data" / "precomputed" / "ui_assets_meta.json"


@st.cache_data
def _load_ui_meta() -> dict:
    with UI_META_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def _load_block(model_key: str):
    """
    Load precomputed arrays for Model A or B.
    Returns (dates_idx_utc, sis, mean, roi_pct)
    """
    meta = _load_ui_meta()
    block = meta["modelA"] if model_key == "A" else meta["modelB"]

    dates = np.load(ROOT / block["dates_file"])
    sis = np.load(ROOT / block["sis_file"])      # (T, H, W)
    mean = np.load(ROOT / block["mean_file"])    # (T,)
    roi = np.load(ROOT / block["roi_pct_file"])  # (T, H, W)

    dates_idx = pd.to_datetime(dates)
    if getattr(dates_idx, "tz", None) is None:
        dates_idx = dates_idx.tz_localize("UTC")
    else:
        dates_idx = dates_idx.tz_convert("UTC")
    dates_idx = dates_idx.normalize()

    return dates_idx, sis, mean, roi


@st.cache_data
def _load_explain_assets():
    """
    Load NDVI, cloud proxy and terrain for explainable layers,
    plus SARAH "truth" mean for validation.
    """
    meta_ex = _load_ui_meta()["explain"]

    elev = np.load(ROOT / meta_ex["terrain"]["elevation"])
    slope = np.load(ROOT / meta_ex["terrain"]["slope"])
    aspect = np.load(ROOT / meta_ex["terrain"]["aspect"])

    months_raw = np.load(ROOT / meta_ex["ndvi_monthly"]["months"])
    months_dt = pd.to_datetime(months_raw)
    months_num = months_dt.month.to_numpy()

    ndvi = np.load(ROOT / meta_ex["ndvi_monthly"]["ndvi"])  # (M, H, W)

    cloud_B = np.load(ROOT / meta_ex["cloud_daily"]["cloud_B"])
    dates_B, _, _, _ = _load_block("B")

    sarah_truth = None
    if "sarah_truth" in meta_ex:
        truth_dates = np.load(ROOT / meta_ex["sarah_truth"]["dates_file"])
        truth_mean = np.load(ROOT / meta_ex["sarah_truth"]["mean_file"])

        truth_dates_idx = pd.to_datetime(truth_dates)
        if getattr(truth_dates_idx, "tz", None) is None:
            truth_dates_idx = truth_dates_idx.tz_localize("UTC")
        else:
            truth_dates_idx = truth_dates_idx.tz_convert("UTC")
        truth_dates_idx = truth_dates_idx.normalize()

        sarah_truth = {"dates": truth_dates_idx, "mean": truth_mean}

    return {
        "terrain": {"elev": elev, "slope": slope, "aspect": aspect},
        "ndvi": {"months_num": months_num, "ndvi": ndvi},
        "cloud_B": {"dates": dates_B, "cloud": cloud_B},
        "sarah_truth": sarah_truth,
    }


# -----------------------
# Helpers: date → assets
# -----------------------

def _pick_by_doy(dates_idx: pd.DatetimeIndex, target: pd.Timestamp) -> int:
    """Pick index with closest day-of-year in a reference index."""
    doy_all = dates_idx.dayofyear.to_numpy()
    doy_t = target.dayofyear
    diffs = np.abs(doy_all - doy_t)
    return int(diffs.argmin())


def _get_day_assets(selected_date: pd.Timestamp) -> dict:
    """
    Core logic:
    - If selected_date is within precomputed A/B dates → data-backed mode.
    - Else → scenario mode: map by day-of-year to nearest 2024/2025 day.
    """
    dates_A, sis_A, mean_A, roi_A = _load_block("A")
    dates_B, sis_B, mean_B, roi_B = _load_block("B")

    sel = pd.to_datetime(selected_date)
    if sel.tzinfo is None:
        sel = sel.tz_localize("UTC")
    else:
        sel = sel.tz_convert("UTC")
    sel = sel.normalize()

    # --- DATA-BACKED MODE ---
    if sel in dates_A:
        idx = int(np.where(dates_A == sel)[0][0])
        return {
            "mode": "data",
            "model_id": "A",
            "date_requested": sel,
            "date_used": sel,
            "sis_map": sis_A[idx],
            "city_mean": float(mean_A[idx]),
            "roi_pct": roi_A[idx],
        }

    if sel in dates_B:
        idx = int(np.where(dates_B == sel)[0][0])
        return {
            "mode": "data",
            "model_id": "B",
            "date_requested": sel,
            "date_used": sel,
            "sis_map": sis_B[idx],
            "city_mean": float(mean_B[idx]),
            "roi_pct": roi_B[idx],
        }

    # --- SCENARIO MODE (outside data window) ---
    # Rule: if request is 2024 -> prefer A; otherwise prefer B (if available)
    if sel.year == 2024 and len(dates_A) > 0:
        model_id = "A"
        dates_ref, sis_ref, mean_ref, roi_ref = dates_A, sis_A, mean_A, roi_A
    else:
        if len(dates_B) > 0:
            model_id = "B"
            dates_ref, sis_ref, mean_ref, roi_ref = dates_B, sis_B, mean_B, roi_B
        else:
            model_id = "A"
            dates_ref, sis_ref, mean_ref, roi_ref = dates_A, sis_A, mean_A, roi_A

    idx = _pick_by_doy(dates_ref, sel)
    used = dates_ref[idx]

    return {
        "mode": "scenario",
        "model_id": model_id,
        "date_requested": sel,
        "date_used": used,
        "sis_map": sis_ref[idx],
        "city_mean": float(mean_ref[idx]),
        "roi_pct": roi_ref[idx],
    }


# -----------------------
# Color helpers (grid → RGBA)
# -----------------------

def _grid_to_rgba_roi(arr: np.ndarray, alpha: int = 235, upscale: int = 16) -> np.ndarray:
    """Diverging palette for ROI % grid (relative to city mean = 100%)."""
    arr = np.array(arr, dtype="float32")
    if arr.ndim != 2:
        raise ValueError("Expected 2D array for ROI overlay.")
    if np.all(np.isnan(arr)):
        h, w = arr.shape
        return np.zeros((h, w, 4), dtype=np.uint8)

    dev = arr - 100.0
    dev = np.nan_to_num(dev, nan=0.0)

    p5 = np.nanpercentile(dev, 5.0)
    p95 = np.nanpercentile(dev, 95.0)
    vmax = max(abs(p5), abs(p95), 1e-6)
    norm = np.clip(dev / vmax, -1.0, 1.0)
    norm01 = (norm + 1.0) / 2.0

    stops = [
        (0.00, (40, 80, 160)),
        (0.50, (245, 245, 245)),
        (1.00, (200, 40, 40)),
    ]
    xs = np.linspace(0, 1, 256)
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i, x in enumerate(xs):
        for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
            if x <= p1:
                tseg = 0.0 if p1 == p0 else (x - p0) / (p1 - p0)
                lut[i] = (
                    int(round(c0[0] + (c1[0] - c0[0]) * tseg)),
                    int(round(c0[1] + (c1[1] - c0[1]) * tseg)),
                    int(round(c0[2] + (c1[2] - c0[2]) * tseg)),
                )
                break

    idx = (norm01 * 255).astype(np.uint8)
    rgb = lut[idx]
    h, w = rgb.shape[:2]
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = alpha

    if upscale and upscale > 1:
        pil = Image.fromarray(rgba, mode="RGBA")
        pil = pil.resize((w * upscale, h * upscale), resample=Image.BILINEAR)
        rgba = np.array(pil)

    return rgba


def _grid_to_rgba_ndvi(arr: np.ndarray, alpha: int = 130, upscale: int = 16) -> np.ndarray:
    """Greenish overlay for NDVI."""
    arr = np.array(arr, dtype="float32")
    if arr.ndim != 2:
        raise ValueError("Expected 2D array for NDVI overlay.")
    if np.all(np.isnan(arr)):
        h, w = arr.shape
        return np.zeros((h, w, 4), dtype=np.uint8)

    vmin = np.nanpercentile(arr, 10.0)
    vmax = np.nanpercentile(arr, 90.0)
    if vmax <= vmin:
        vmax = vmin + 1e-6
    norm = np.clip((arr - vmin) / (vmax - vmin), 0, 1)

    stops = [
        (0.00, (140, 100, 40)),
        (0.50, (190, 210, 100)),
        (1.00, (20, 140, 60)),
    ]
    xs = np.linspace(0, 1, 256)
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i, x in enumerate(xs):
        for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
            if x <= p1:
                tseg = 0.0 if p1 == p0 else (x - p0) / (p1 - p0)
                lut[i] = (
                    int(round(c0[0] + (c1[0] - c0[0]) * tseg)),
                    int(round(c0[1] + (c1[1] - c0[1]) * tseg)),
                    int(round(c0[2] + (c1[2] - c0[2]) * tseg)),
                )
                break

    idx = (norm * 255).astype(np.uint8)
    rgb = lut[idx]
    h, w = rgb.shape[:2]
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = alpha

    if upscale and upscale > 1:
        pil = Image.fromarray(rgba, mode="RGBA")
        pil = pil.resize((w * upscale, h * upscale), resample=Image.BILINEAR)
        rgba = np.array(pil)

    return rgba


def _grid_to_rgba_terrain(arr: np.ndarray, alpha: int = 130, upscale: int = 16) -> np.ndarray:
    """Brownish overlay for terrain (elevation)."""
    arr = np.array(arr, dtype="float32")
    if arr.ndim != 2:
        raise ValueError("Expected 2D array for terrain overlay.")
    if np.all(np.isnan(arr)):
        h, w = arr.shape
        return np.zeros((h, w, 4), dtype=np.uint8)

    vmin = np.nanpercentile(arr, 5.0)
    vmax = np.nanpercentile(arr, 95.0)
    if vmax <= vmin:
        vmax = vmin + 1e-6
    norm = np.clip((arr - vmin) / (vmax - vmin), 0, 1)

    stops = [
        (0.00, (230, 220, 200)),
        (0.50, (200, 170, 130)),
        (1.00, (150, 110, 70)),
    ]
    xs = np.linspace(0, 1, 256)
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i, x in enumerate(xs):
        for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
            if x <= p1:
                tseg = 0.0 if p1 == p0 else (x - p0) / (p1 - p0)
                lut[i] = (
                    int(round(c0[0] + (c1[0] - c0[0]) * tseg)),
                    int(round(c0[1] + (c1[1] - c0[1]) * tseg)),
                    int(round(c0[2] + (c1[2] - c0[2]) * tseg)),
                )
                break

    idx = (norm * 255).astype(np.uint8)
    rgb = lut[idx]
    h, w = rgb.shape[:2]
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = alpha

    if upscale and upscale > 1:
        pil = Image.fromarray(rgba, mode="RGBA")
        pil = pil.resize((w * upscale, h * upscale), resample=Image.BILINEAR)
        rgba = np.array(pil)

    return rgba


def _grid_to_rgba_cloud(arr: np.ndarray, alpha: int = 120, upscale: int = 16) -> np.ndarray:
    """Soft white overlay for cloud proxy."""
    arr = np.array(arr, dtype="float32")
    if arr.ndim != 2:
        raise ValueError("Expected 2D array for cloud overlay.")
    if np.all(np.isnan(arr)):
        h, w = arr.shape
        return np.zeros((h, w, 4), dtype=np.uint8)

    vmin = np.nanpercentile(arr, 10.0)
    vmax = np.nanpercentile(arr, 90.0)
    if vmax <= vmin:
        vmax = vmin + 1e-6
    norm = np.clip((arr - vmin) / (vmax - vmin), 0, 1)

    base = 220 + 35 * norm
    rgb = np.clip(base, 0, 255)[..., None].repeat(3, axis=2).astype(np.uint8)

    h, w = rgb.shape[:2]
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = (alpha * norm).astype(np.uint8)

    if upscale and upscale > 1:
        pil = Image.fromarray(rgba, mode="RGBA")
        pil = pil.resize((w * upscale, h * upscale), resample=Image.BILINEAR)
        rgba = np.array(pil)

    return rgba


# -----------------------
# Explanation helpers
# -----------------------

def _classify_ghi_level(city_mean: float) -> str:
    if city_mean < 150:
        return "a low sunlight level in our dataset"
    if city_mean < 300:
        return "a medium sunlight level in our dataset"
    if city_mean < 450:
        return "a high sunlight level in our dataset"
    return "a very high sunlight level in our dataset"


def _summarize_roi_pattern(roi_pct: np.ndarray | None) -> str:
    if roi_pct is None or not isinstance(roi_pct, np.ndarray):
        return ""

    roi = roi_pct.astype("float32")
    roi = roi[np.isfinite(roi)]
    if roi.size == 0:
        return ""

    spread = float(np.nanstd(roi))

    if spread < 5:
        return (
            "Overall the sunlight values are quite similar across the city, "
            "with only small differences between neighbourhoods."
        )
    if spread < 12:
        return (
            "Most neighbourhoods are close to the city average, with some areas "
            "slightly brighter or darker than others."
        )

    high_share = float((roi > 110).mean() * 100.0)
    low_share = float((roi < 90).mean() * 100.0)
    parts = []
    if high_share > 5:
        parts.append(f"about {high_share:.0f}% of the area above the city average")
    if low_share > 5:
        parts.append(f"around {low_share:.0f}% below the average")
    if parts:
        return "There are differences: " + " and ".join(parts) + "."
    return "Some neighbourhoods still stand out with higher or lower values than the city average."


def _build_explanation(
    day: dict,
    use_cloud: bool,
    use_ndvi: bool,
    use_terrain: bool,
    cloud_score: float | None,
) -> str:
    city_mean = float(day.get("city_mean", np.nan))
    ghi_part = ""
    if np.isfinite(city_mean):
        level_txt = _classify_ghi_level(city_mean)
        ghi_part = (
            f"On this day the average sunlight over your selected area is about "
            f"{city_mean:.0f} W/m², which is {level_txt}. "
        )

    roi_part = _summarize_roi_pattern(day.get("roi_pct"))
    base_intro = (ghi_part + roi_part).strip()

    sky = None
    if cloud_score is not None:
        if cloud_score >= 0.6:
            sky = "cloudy"
        elif cloud_score <= 0.3:
            sky = "clear"
        else:
            sky = "mixed"

    if not (use_cloud or use_ndvi or use_terrain):
        if day["mode"] == "data":
            core = (
                "This map shows how each small 1×1 km square compares to the city-average sunlight on this day. "
                "Redder cells receive a bit more sunlight than the city average, bluer cells a bit less. "
                "It only shows relative sunlight, not temperature."
            )
        else:
            core = (
                "For this date the app shows a typical sunlight pattern for this time of year, based on similar days in our data. "
                "Again, redder cells receive a bit more sunlight than the city average for that pattern, bluer cells a bit less. "
                "It only shows relative sunlight, not temperature."
            )
        return (base_intro + " " + core).strip()

    if use_cloud and not use_ndvi and not use_terrain:
        if sky == "cloudy":
            details = "It is quite cloudy today, so some areas have less sunlight come from clouds blocking part of the sunlight."
        elif sky == "clear":
            details = "Since today is mostly clear, clouds only play a small role and most places have ROI values close to the city average."
        else:
            details = "Some parts of the city are cloudier than others today. Cloudier areas tend to have ROI values below the city average."
        return (base_intro + " " + details).strip()

    if use_ndvi and not use_cloud and not use_terrain:
        details = (
            "This view also takes greenness into account. Parks and tree-rich areas often behave differently from built-up areas, "
            "so they can show slightly lower or higher ROI values than nearby neighbourhoods depending on the conditions that day."
        )
        return (base_intro + " " + details).strip()

    if use_terrain and not use_cloud and not use_ndvi:
        details = (
            "The terrain in this region is mostly flat, but small height and slope differences can still make some grid cells "
            "slightly above or below the city-average sunlight."
        )
        return (base_intro + " " + details).strip()

    if use_cloud and use_ndvi and not use_terrain:
        if sky == "cloudy":
            details = (
                "Today’s ROI pattern comes from both clouds and land cover: cloudier spots receive less direct sun, "
                "and greener areas like parks can react differently than built-up areas."
            )
        elif sky == "clear":
            details = (
                "Because the sky is mostly clear, the ROI differences mainly come from the land surface: "
                "green parks and trees may behave differently than concrete and roofs."
            )
        else:
            details = (
                "Today’s pattern comes from both clouds and the type of surface: cloudier cells tend to be below the average, "
                "and greener areas can stand out from nearby built-up neighbourhoods."
            )
        return (base_intro + " " + details).strip()

    if use_cloud and use_terrain and not use_ndvi:
        if sky == "cloudy":
            details = (
                "Today’s sunlight levels are mainly reduced by clouds. Small height and slope differences in the terrain then make "
                "some cells slightly above or below the city average."
            )
        elif sky == "clear":
            details = (
                "With mostly clear skies, small height and slope differences in the terrain can make some parts of the region receive "
                "slightly more or slightly less sunlight than the average."
            )
        else:
            details = (
                "Today’s ROI pattern is shaped by both cloud cover and small height differences: cloudier or lower areas are often below the average, "
                "while slightly higher or more exposed places are closer to or above it."
            )
        return (base_intro + " " + details).strip()

    if use_ndvi and use_terrain and not use_cloud:
        details = (
            "Here the differences mostly come from the land: greener parks and fields and small height changes together make some cells "
            "slightly above or below the city-average sunlight."
        )
        return (base_intro + " " + details).strip()

    if use_cloud and use_ndvi and use_terrain:
        details = (
            "Different parts of the region get and keep different amounts of sunlight today because some areas are cloudier, "
            "greener, or slightly higher than others. This combination shows up as variations around the city-average ROI value."
        )
        return (base_intro + " " + details).strip()

    return (base_intro + " This sunlight pattern is shaped by a mix of clouds, greenness and small height differences across the region.").strip()


# -----------------------
# Simple grid congestion helpers
# -----------------------

PV_CAPACITY_MWP = 250.0
GRID_CAPACITY_MW = 100.0


def _day_jitter_factor(date_used: pd.Timestamp | None) -> float:
    if date_used is None or not isinstance(date_used, pd.Timestamp):
        return 1.0
    d = int(date_used.dayofyear)
    y = int(date_used.year)
    base = (d * 37 + y * 13) % 21
    return 0.9 + (base / 20.0) * 0.2


def _estimate_pv_output_mw(city_mean: float, date_used: pd.Timestamp | None = None) -> float:
    if not np.isfinite(city_mean) or PV_CAPACITY_MWP <= 0:
        return 0.0
    cf = float(city_mean) / 1000.0
    cf *= _day_jitter_factor(date_used)
    cf = max(0.0, min(cf, 1.2))
    return PV_CAPACITY_MWP * cf


def _classify_congestion_ratio(ratio: float) -> tuple[str, str]:
    if not np.isfinite(ratio) or ratio <= 0:
        return "Very low", "The solar power is much lower than the grid capacity in this simple example."
    if ratio < 0.4:
        return "Low", "The grid still has a lot of spare room compared to the solar power in this example."
    if ratio < 0.8:
        return "Medium", "Solar power already uses a clear part of the grid capacity, but there is still space."
    if ratio < 1.1:
        return "High", "Solar power is close to the grid capacity. In reality this could already give congestion moments."
    return "Very high", "Solar power is above the grid capacity in this example, so congestion is likely."


# -----------------------
# Legend helper (ROI)
# -----------------------

def _render_legend(extra_class: str = "", label: str = "ROI (% of city mean)"):
    note = "Values are % of city-average GHI (100% = city mean)"
    ticks = (
        "<span>≤ 90%</span>"
        "<span>95–100%</span>"
        "<span>100–105%</span>"
        "<span>≥ 110%</span>"
    )
    gradient_div = (
        "<div class='legend-gradient' "
        "style='background: linear-gradient(to right, "
        "#2850a0, #f5f5f5, #c82828);'></div>"
    )

    st.markdown(
        f"""
        <div class="legend-box {extra_class}">
          <div class="legend-title">☀️ {label}</div>
          <div class="legend-scale">
            {gradient_div}
            <div class="legend-labels">
              {ticks}
            </div>
          </div>
          <div class="legend-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------
# Step C helper: truth vs prediction
# -----------------------

def _lookup_truth_mean(explain_assets: dict, date_utc: pd.Timestamp) -> float | None:
    truth = explain_assets.get("sarah_truth")
    if not truth:
        return None

    dates = truth["dates"]
    mean = truth["mean"]

    if date_utc in dates:
        idx = int(np.where(dates == date_utc)[0][0])
        val = float(mean[idx])
        return val if np.isfinite(val) else None

    return None


# -----------------------
# Reliability score (data-driven from historical validation error)
# -----------------------

@st.cache_data
def _validation_mape_by_month() -> dict:
    explain = _load_explain_assets()
    truth = explain.get("sarah_truth")
    if not truth:
        return {"A": {"overall": None, "by_month": {}}, "B": {"overall": None, "by_month": {}}}

    truth_dates = truth["dates"]
    truth_mean = np.asarray(truth["mean"], dtype="float32")
    truth_map = {d: i for i, d in enumerate(truth_dates)}

    stats = {}
    for model_id in ["A", "B"]:
        dates, _, mean_pred, _ = _load_block(model_id)
        mean_pred = np.asarray(mean_pred, dtype="float32")

        apes = []
        by_month = {m: [] for m in range(1, 13)}

        for i, d in enumerate(dates):
            j = truth_map.get(d)
            if j is None:
                continue

            t = float(truth_mean[j])
            p = float(mean_pred[i])
            if not (np.isfinite(t) and np.isfinite(p)):
                continue

            den = (abs(t) + abs(p)) / 2.0
            if den == 0:
                continue

            ape = abs(p - t) / den
            apes.append(ape)

            m = int(d.month)
            by_month[m].append(ape)

        overall = float(np.mean(apes) * 100.0) if apes else None
        by_month_mape = {m: (float(np.mean(v) * 100.0) if v else None) for m, v in by_month.items()}

        stats[model_id] = {"overall": overall, "by_month": by_month_mape}

    return stats


def _confidence_from_mape(mape_pct: float | None) -> float:
    if mape_pct is None or not np.isfinite(mape_pct):
        return 80.0

    m = float(mape_pct)
    base = 95.0 - 0.6 * m
    return float(np.clip(base, 45.0, 95.0))


def _cloud_penalty(cloud_score: float | None) -> float:
    if cloud_score is None or not np.isfinite(cloud_score):
        return 0.0
    cs = float(cloud_score)
    if 0.40 <= cs <= 0.60:
        return 5.0
    return 1.0


def _horizon_penalty(day: dict) -> float:
    req_year = int(day["date_requested"].year)
    if req_year >= 2028:
        return 8.0
    if req_year >= 2026:
        return 5.0
    if req_year >= 2025:
        return 3.0
    return 0.0


def _label_from_pct(pct: float) -> str:
    if pct >= 80:
        return "High"
    if pct >= 60:
        return "Medium"
    return "Low"


def _scenario_reliability(day: dict, cloud_score: float | None) -> dict:
    stats = _validation_mape_by_month()
    model_id = day.get("model_id", "B")
    month = int(day["date_requested"].month)

    mape_month = stats.get(model_id, {}).get("by_month", {}).get(month)
    mape_overall = stats.get(model_id, {}).get("overall")
    mape_used = mape_month if (mape_month is not None and np.isfinite(mape_month)) else mape_overall

    base = _confidence_from_mape(mape_used)

    penalty_scenario = 3.5 if day.get("mode") == "scenario" else 0.0
    penalty_horizon = _horizon_penalty(day)
    penalty_cloud = _cloud_penalty(cloud_score)

    raw_score = float(base - (penalty_scenario + penalty_horizon + penalty_cloud))
    final_score = float(np.clip(raw_score, 40.0, 95.0))

    return {
        "reliability_pct": final_score,
        "label": _label_from_pct(final_score),
        "mape_used": mape_used,
    }


# -----------------------
# Main render
# -----------------------

def render():
    ss = state.init()

    # Make metric text readable on your dark background
    st.markdown(
        """
        <style>
          [data-testid="stMetricLabel"] { color: rgba(255,255,255,0.92) !important; }
          [data-testid="stMetricValue"] { color: #ffffff !important; }
          [data-testid="stMetricDelta"] { color: rgba(255,255,255,0.85) !important; }

          .stCaption, .stCaption p, [data-testid="stCaptionContainer"] {
            color: rgba(235,240,255,0.85) !important;
          }

          [data-testid="stAlert"] * { color: rgba(255,255,255,0.92) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Apply canonical name before widget
    if getattr(ss, "place_override", None):
        st.session_state["place_input"] = ss.place_override
        ss.place = ss.place_override
        ss.place_override = None

    col_map, col_right = st.columns([2.35, 1.0], gap="small")

    # =========================
    # RIGHT: controls
    # =========================
    with col_right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)

        # --- LOCATION INPUT ---
        st.markdown("<div class='panel-title'>Location</div>", unsafe_allow_html=True)
        place = st.text_input(
            "Search",
            ss.place,
            key="place_input",
            label_visibility="collapsed",
            placeholder="City e.g., Eindhoven",
        )
        if place.strip() != ss.place:
            ss.place = place

        hits = geocode_osm(ss.place, country="nl", limit=3) if ss.place.strip() else []
        if hits:
            top = pick_best_hit(hits)
            city_name = top.address.split(",")[0]
            st.info(f"Found: **{city_name}**")
            if abs(top.latitude - ss.center_lat) > 1e-6 or abs(top.longitude - ss.center_lon) > 1e-6:
                ss.candidate = {"name": city_name, "lat": top.latitude, "lon": top.longitude}
                ss.pending_confirm = True
        else:
            sugg = fuzzy_suggest(ss.place)
            if sugg:
                st.markdown("**Did you mean:**")
                st.markdown("<div class='pill-row'>", unsafe_allow_html=True)
                sugg_cols = st.columns(min(3, len(sugg)))
                for i, name in enumerate(sugg):
                    if sugg_cols[i % 3].button(name, key=f"suggest_{name}", use_container_width=True):
                        hits2 = geocode_osm(name, country="nl", limit=1)
                        if hits2:
                            t = hits2[0]
                            ss.candidate = {"name": name, "lat": t.latitude, "lon": t.longitude}
                            ss.pending_confirm = True
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        if ss.input_mode == "draw":
            ss.pending_confirm = False
            ss.candidate = None

        # --- CONFIRM BOX ---
        if ss.pending_confirm and ss.candidate:
            nm, la, lo = ss.candidate["name"], ss.candidate["lat"], ss.candidate["lon"]
            confirm_box(nm, la, lo)
            c1, c2 = st.columns(2)
            if c1.button("✅ Yes", use_container_width=True, key="confirm_yes"):
                ss.place_override = nm
                ss.center_lat, ss.center_lon = la, lo
                delta = 0.15
                ss.roi_bounds = [[la - delta, lo - delta], [la + delta, lo + delta]]
                ss.input_mode = "city"
                ss.confirmed = True
                ss.pending_confirm = False
                ss.candidate = None
                st.rerun()

            if c2.button("❌ No", use_container_width=True, key="confirm_no"):
                ss.pending_confirm = False
                ss.candidate = None
                st.rerun()

        # --- DATE ---
        st.markdown("<div class='panel-title'>Day (UTC)</div>", unsafe_allow_html=True)
        default_date = getattr(ss, "selected_date", pd.to_datetime("2024-06-10"))
        selected_date = st.date_input("Day", default_date, key="selected_day")
        ss.selected_date = selected_date

        # --- Map info (ROI only) ---
        st.markdown("<div class='panel-title'>Map view</div>", unsafe_allow_html=True)
        st.caption(
            "The map shows ROI (% of city mean): how each 1×1 km grid cell compares to the "
            "city-average sunlight on this day (100% = average, red = above, blue = below)."
        )

        # --- Explainable layers (with mini legends under each option) ---
        st.markdown("<div class='panel-title'>Explainable layers</div>", unsafe_allow_html=True)

        use_cloud = st.checkbox("☁️ Cloud layer", value=True, key="use_cloud")
        st.caption("Legend: whiter haze = more cloud (proxy). More cloud usually reduces sunlight.")

        use_ndvi = st.checkbox("🌳 Greenness layer (parks vs built areas)", value=True, key="use_ndvi")
        st.caption("Legend: greener = more vegetation (NDVI). This is land cover context, not sunlight itself.")

        use_terrain = st.checkbox("⛰️ Terrain layer (small height differences)", value=False, key="use_terrain")
        st.caption("Legend: browner = higher elevation. Mostly small differences in NL.")

        # --- ROI INFO ---
        (lat_min, lon_min), (lat_max, lon_max) = ss.roi_bounds
        center_lat = (lat_min + lat_max) / 2
        center_lon = (lon_min + lon_max) / 2
        st.markdown("<div class='panel-title'>Region of Interest (ROI)</div>", unsafe_allow_html=True)
        st.caption(f"Lat {center_lat:.4f} • Lon {center_lon:.4f}")

        run = st.button("Show radiation", type="primary", use_container_width=True, key="run_btn")

        if run:
            if not ss.confirmed and ss.input_mode != "draw":
                st.warning("⚠️ Please confirm a location or draw a region first.")
            else:
                try:
                    day = _get_day_assets(selected_date)
                    explain = _load_explain_assets()

                    # Base map: ROI %
                    grid_base = day["roi_pct"]
                    legend_label = "ROI (% of city mean)"
                    base_rgba = _grid_to_rgba_roi(grid_base, alpha=235, upscale=16)

                    overlay_bounds = ss.roi_bounds
                    overlays = [{"image": base_rgba, "bounds": overlay_bounds, "opacity": 0.85}]

                    cloud_score = None

                    # Cloud overlay
                    if use_cloud:
                        cloud_info = explain["cloud_B"]
                        dates_cloud = cloud_info["dates"]
                        cloud_array = cloud_info["cloud"]  # (T, H, W)

                        idx_cloud = _pick_by_doy(dates_cloud, day["date_used"])
                        cloud_grid = cloud_array[idx_cloud]

                        cloud_score = (
                            float(np.nanmean(cloud_grid))
                            if isinstance(cloud_grid, np.ndarray)
                            else float(cloud_grid)
                        )

                        cloud_rgba = _grid_to_rgba_cloud(cloud_grid, alpha=120, upscale=16)
                        overlays.append({"image": cloud_rgba, "bounds": overlay_bounds, "opacity": 0.95})

                    # NDVI overlay
                    if use_ndvi:
                        ndvi_info = explain["ndvi"]
                        months_num = ndvi_info["months_num"]
                        ndvi_all = ndvi_info["ndvi"]
                        month = int(day["date_used"].month)

                        diffs = np.abs(months_num.astype(int) - month)
                        mi = int(diffs.argmin())
                        ndvi_grid = ndvi_all[mi]

                        ndvi_rgba = _grid_to_rgba_ndvi(ndvi_grid, alpha=130, upscale=16)
                        overlays.append({"image": ndvi_rgba, "bounds": overlay_bounds, "opacity": 0.70})

                    # Terrain overlay
                    if use_terrain:
                        elev = explain["terrain"]["elev"]
                        terr_rgba = _grid_to_rgba_terrain(elev, alpha=130, upscale=16)
                        overlays.append({"image": terr_rgba, "bounds": overlay_bounds, "opacity": 0.70})

                    explanation = _build_explanation(day, use_cloud, use_ndvi, use_terrain, cloud_score)

                    truth_mean = _lookup_truth_mean(explain, day["date_used"])

                    reliability_pack = None
                    if day["mode"] == "scenario" or truth_mean is None or not np.isfinite(truth_mean):
                        reliability_pack = _scenario_reliability(day, cloud_score)

                    ss.result = {
                        "day": day,
                        "overlay_bounds": overlay_bounds,
                        "overlays": overlays,
                        "legend_label": legend_label,
                        "loc_name": (ss.place if ss.input_mode == "city" else None),
                        "loc_lat": ss.center_lat,
                        "loc_lon": ss.center_lon,
                        "explanation": explanation,
                        "truth_mean": truth_mean,
                        "reliability_pack": reliability_pack,
                        "cloud_score": cloud_score,
                    }
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # LEFT: map + drawings
    # =========================
    with col_map:
        st.markdown(
            """
            <div style="
                background: rgba(33,150,243,0.08);
                border: 1px solid rgba(33,150,243,0.3);
                padding: 10px 12px;
                border-radius: 10px;
                font-size: 13.5px;
                line-height: 1.45;
                margin-bottom: 10px;
            ">
              <b>Prototype – how to use this page</b><br/>
              1. Pick a location by typing in the box or drawing a region on the map, then confirm your choice on the right.<br/>
              <span style="opacity:0.9;">
              Note: this demo is calibrated for the Eindhoven area. You can try other cities to see the geocoding function,
              but the red box and data are still based on Eindhoven.
              </span><br/>
              2. Pick a day (UTC) in the calendar.<br/>
              3. The map shows <b>ROI&nbsp;%</b>: how each small 1×1 km grid cell compares to the city-average sunlight for that day
                 (100% = average, red = above, blue = below).<br/>
              4. Optionally switch on the explainable layers (clouds, greenness, terrain) for extra context.<br/>
              5. Click <b>"Show radiation"</b> to update the map, legend and explanation text.<br/>
              <span style="opacity:0.9;">
              Below the map you also see a very simple example of estimated solar power and "grid risk".
              This uses only the sunlight value plus two fixed assumptions and is <b>not</b> real grid data.
              </span><br/>
              For dates outside the 2024–early 2025 data window, the app shows a typical pattern for that time of year
              (<i>scenario mode</i>) instead of a detailed weather forecast.
            </div>
            """,
            unsafe_allow_html=True,
        )

        r = ss.result or {}

        if r.get("explanation"):
            st.markdown("#### Why this prediction?", unsafe_allow_html=True)
            st.info(r["explanation"])

        def overlay_caption():
            day = r.get("day")
            if not day:
                return
            req = day["date_requested"].strftime("%Y-%m-%d")
            used = day["date_used"].strftime("%Y-%m-%d")
            if day["mode"] == "data":
                st.caption(f"Data-backed UNet estimate for {used} (UTC)")
            else:
                st.caption(f"Scenario mode: requested {req}, using typical pattern from {used} (UTC)")

        overlays_arg = r.get("overlays")
        map_state = ui_map.build_map(
            ss.center_lat,
            ss.center_lon,
            ss.roi_bounds,
            overlays=overlays_arg,
            caption_fn=(overlay_caption if overlays_arg else None),
        )

        if overlays_arg:
            _render_legend("legend--desktop", label=r.get("legend_label", "ROI (% of city mean)"))

        # Draw handling
        try:
            last_obj = None
            if map_state and map_state.get("last_active_drawing"):
                last_obj = map_state["last_active_drawing"]
            elif map_state and map_state.get("all_drawings"):
                last_obj = map_state["all_drawings"][-1]

            if last_obj and "geometry" in last_obj:
                gtype = last_obj["geometry"].get("type")
                coords = last_obj["geometry"].get("coordinates")

                if gtype == "Point" and isinstance(coords, (list, tuple)) and len(coords) == 2:
                    lon, lat = coords
                    ss.center_lat, ss.center_lon = float(lat), float(lon)
                    delta = 0.15
                    ss.roi_bounds = [[lat - delta, lon - delta], [lat + delta, lon + delta]]

                    ss.input_mode = "draw"
                    ss.confirmed = False
                    ss.pending_confirm = False
                    ss.candidate = None

                    ss.toast_msg = "📍 Using marker location for analysis."
                    st.rerun()

                elif gtype == "Polygon" and coords:
                    ring = coords[0]
                    lats = [pt[1] for pt in ring]
                    lons = [pt[0] for pt in ring]
                    ss.roi_bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
                    ss.center_lat = (ss.roi_bounds[0][0] + ss.roi_bounds[1][0]) / 2
                    ss.center_lon = (ss.roi_bounds[0][1] + ss.roi_bounds[1][1]) / 2

                    ss.input_mode = "draw"
                    ss.confirmed = False
                    ss.pending_confirm = False
                    ss.candidate = None

                    ss.toast_msg = "🗺️ Using drawn region for analysis."
                    st.rerun()
        except Exception as e:
            st.write(f"draw-parse issue: {e}")

        if getattr(ss, "toast_msg", None):
            st.success(ss.toast_msg)
            ss.toast_msg = None

    # =========================
    # RESULTS (centered)
    # =========================
    if ss.result:
        r = ss.result
        day = r["day"]
        _, center, _ = st.columns([1, 1.4, 1])

        with center:
            mode_label = (
                "Model A • data-backed (rich inputs)"
                if day["model_id"] == "A"
                else "Model B • future-safe (stable inputs)"
            )
            if day["mode"] == "scenario":
                mode_label += " • scenario mode"
            st.markdown(f"<div class='badge'>{mode_label}</div>", unsafe_allow_html=True)

            if r.get("loc_name"):
                loc_display = f"{r['loc_name']}<br><span class='caption'>{r['loc_lat']:.2f}N, {r['loc_lon']:.2f}E</span>"
            else:
                loc_display = f"{r['loc_lat']:.2f}N, {r['loc_lon']:.2f}E"

            date_req_str = day["date_requested"].strftime("%Y-%m-%d")

            st.markdown(
                f"""
                <div class='info-row'>
                    <div>📍 <b>Location</b></div>
                    <div class='info-right'>{loc_display}</div>
                </div>
                <div class='info-row'>
                    <div>📅 <b>Day (UTC)</b></div>
                    <div class='info-right'>{date_req_str}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            pred_mean = float(day["city_mean"])
            truth_mean = r.get("truth_mean")
            reliability_pack = r.get("reliability_pack")

            # DATA mode: Predicted + Actual + % error
            if day["mode"] == "data" and truth_mean is not None and np.isfinite(truth_mean):
                truth_mean = float(truth_mean)
                diff = pred_mean - truth_mean
                abs_err = abs(diff)
                pct_err = (abs_err / truth_mean * 100.0) if truth_mean != 0 else np.nan

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        label="Test (Predicted)",
                        value=f"{pred_mean:.0f} W/m²",
                    )

                with c2:
                    st.metric(
                        label="Actual (SARAH-3)",
                        value=f"{truth_mean:.0f} W/m²",
                    )

                with c3:
                    if np.isfinite(pct_err):
                        st.metric(
                            label="Error (%)",
                            value=f"{pct_err:.1f}%",
                        )
                    else:
                        st.metric(label="📉 Error (%)", value="—")

                err_txt = f"Diff: {diff:+.0f} W/m² • Abs error: {abs_err:.0f} W/m²"
                st.caption(err_txt)

            # Scenario mode / no truth: Typical day + Estimated mean + Reliability
            else:
                ref_date = day["date_used"].strftime("%Y-%m-%d")

                if not reliability_pack:
                    reliability_pack = {"reliability_pct": 70.0, "label": "Medium", "mape_used": None}

                rel_pct = float(reliability_pack["reliability_pct"])
                rel_label = str(reliability_pack["label"])
                mape_used = reliability_pack.get("mape_used")

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric(
                        label="Date data used",
                        value=ref_date,
                    )
                with c2:
                    st.metric(
                        label="Estimated mean GHI",
                        value=f"{pred_mean:.0f} W/m²",
                    )
                with c3:
                    st.metric(
                        label=f"Reliability score",
                        value=f"{rel_pct:.0f}%",
                    )

            # ---- Simple grid congestion demo (fixed assumptions) ----
            est_pv = _estimate_pv_output_mw(day["city_mean"], day["date_used"])
            ratio = est_pv / GRID_CAPACITY_MW if GRID_CAPACITY_MW > 0 else 0.0
            risk_label, risk_text = _classify_congestion_ratio(ratio)
            ratio_pct = 0.0 if not np.isfinite(ratio) else ratio * 100.0

            st.markdown(
                f"""
                <div class='info-row'>
                  <div>🔆 <b>Estimated solar power</b></div>
                  <div class='info-right'>
                    <div class='kpi'>{est_pv:.0f} MW</div>
                    <div class='kpi-sub'>
                      Rough guess based on the sunlight value and a fixed assumption of {PV_CAPACITY_MWP:.0f} MWp solar panels in the red box
                    </div>
                  </div>
                </div>
                <div class='info-row'>
                  <div>🔌 <b>Grid load risk</b></div>
                  <div class='info-right'>
                    <div class='kpi'>{risk_label}</div>
                    <div class='kpi-sub'>
                      In this simple example the solar power is about {ratio_pct:.0f}% of a fixed {GRID_CAPACITY_MW:.0f} MW grid capacity.<br/>
                      {risk_text}
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                f"This section is only a simple illustration. It uses the sunlight value, "
                f"an assumed {PV_CAPACITY_MWP:.0f} MWp of solar panels and a fixed "
                f"{GRID_CAPACITY_MW:.0f} MW grid capacity for the red-box area. "
                "MWp describes the peak power of solar panels under full sun; MW is the power that the grid could transport. "
                "This is not based on real grid data or real PV installations."
            )

    # Mobile-only legend
    if ss.result and ss.result.get("overlays"):
        _render_legend("legend--mobile", label=ss.result.get("legend_label", "ROI (% of city mean)"))
