import io
import numpy as np
import pandas as pd
import xarray as xr
from PIL import Image  # NEW

# ---------- Time features ----------
def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    idx = df.index
    out = df.copy()
    out["hour"] = idx.hour
    out["dayofyear"] = idx.dayofyear
    out["month"] = idx.month
    out["is_weekend"] = (idx.weekday >= 5).astype(int)
    out["sin_hour"] = np.sin(2*np.pi*out["hour"]/24)
    out["cos_hour"] = np.cos(2*np.pi*out["hour"]/24)
    out["sin_doy"]  = np.sin(2*np.pi*out["dayofyear"]/366)
    out["cos_doy"]  = np.cos(2*np.pi*out["dayofyear"]/366)
    return out

# ---------- CAMS ----------
def load_cams_30(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["time_utc"]).set_index("time_utc").sort_index()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df

def slice_cams(df: pd.DataFrame, start_utc: str, end_utc: str) -> pd.DataFrame:
    s = pd.to_datetime(start_utc).tz_localize("UTC")
    e = pd.to_datetime(end_utc).tz_localize("UTC")
    return df.loc[s:e]

# ---------- Model I/O ----------
def load_model(model_path: str, meta_path: str):
    import joblib, json
    model = joblib.load(model_path)
    with open(meta_path, "r") as f:
        meta = json.load(f)
    return model, meta

def build_feature_frame(cams_window: pd.DataFrame, feature_names: list) -> pd.DataFrame:
    feat = add_time_features(cams_window)
    return feat[feature_names]

def build_future_feature_frame(start_utc: str, end_utc: str, feature_names: list) -> pd.DataFrame:
    ix = pd.date_range(start=start_utc, end=end_utc, freq="30min", tz="UTC", inclusive="both")
    df = pd.DataFrame(index=ix)
    df["Reliability"] = 1.0
    feat = add_time_features(df)
    for c in feature_names:
        if c not in feat:
            feat[c] = 0.0
    return feat[feature_names]

# ---------- Geocoding (with fuzzy) ----------
from geopy.geocoders import Nominatim
from rapidfuzz import fuzz
from unidecode import unidecode

PLACES = [
    "Eindhoven","Tilburg","Breda","Helmond","'s-Hertogenbosch","Den Bosch",
    "Oss","Roosendaal","Bergen op Zoom","Waalwijk","Oosterhout","Veldhoven",
    "Etten-Leur","Uden","Veghel","Boxtel","Best","Vught","Oirschot","Schijndel",
    "Son en Breugel","Nuenen","Heeze-Leende","Geldrop","Mierlo","Goirle",
    "Rijen","Dongen","Drunen","Sint-Oedenrode","Cuijk","Boxmeer","Veghel"
]
BBOX = (51.2, 51.8, 4.0, 6.0)  # lat_min, lat_max, lon_min, lon_max

def _norm(s): return unidecode((s or "").strip().lower())
def in_bbox(lat, lon, bbox=BBOX): return bbox[0] <= lat <= bbox[1] and bbox[2] <= lon <= bbox[3]

def geocode_osm(query: str, country="nl", limit=3, timeout=5):
    geo = Nominatim(user_agent="sis-demo-ui")
    try:
        res = geo.geocode(query, addressdetails=False, language="en",
                          country_codes=country, exactly_one=False,
                          limit=limit, timeout=timeout)
        return res or []
    except Exception:
        return []

def pick_best_hit(hits):
    if not hits: return None
    for h in hits:
        if in_bbox(h.latitude, h.longitude):
            return h
    return hits[0]

def fuzzy_suggest(query: str, choices=PLACES, k=5, min_score=70):
    qn = _norm(query)
    scored = [(name, fuzz.WRatio(qn, _norm(name))) for name in choices]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [name for name, score in scored[:k] if score >= min_score]

# ---------- Pick a good daytime snapshot for overlay ----------
def pick_overlay_time(d1_utc: str, d2_utc: str, is_future: bool, cams_window: pd.DataFrame | None):
    if (not is_future) and (cams_window is not None) and (not cams_window.empty):
        df = cams_window.between_time("10:00", "14:00")
        if not df.empty and "GHI_Wm2" in df:
            t = df["GHI_Wm2"].idxmax()
            if t is not None:
                return pd.Timestamp(t).tz_convert("UTC")
        t0 = pd.to_datetime(d1_utc).tz_localize("UTC")
        return (t0 + pd.Timedelta(hours=12))
    else:
        start = pd.to_datetime(d1_utc).tz_localize("UTC")
        end   = pd.to_datetime(d2_utc).tz_localize("UTC")
        mid   = start + (end - start) / 2
        return (mid.normalize() + pd.Timedelta(hours=12))

# ---------- SARAH-3 → RGBA array for folium (colorized + upscaling) ----------
def sarah_slice_to_rgba(
    nc_path: str,
    t_utc: pd.Timestamp,
    lat_min: float, lat_max: float,
    lon_min: float, lon_max: float,
    vmin=None, vmax=None,
    upscale: int = 8,
    palette: str = "heat",          # "heat" or "gray"
    alpha: int = 235,               # 0..255
    pct_low: float = 5.0,           # robust contrast low
    pct_high: float = 97.0          # robust contrast high
):
    ds = xr.open_dataset(nc_path)
    try:
        t = (pd.Timestamp(t_utc).tz_convert("UTC").tz_localize(None)
             if getattr(t_utc, "tz", None) is not None else pd.Timestamp(t_utc))
        da = ds["SIS"].sel(time=t, method="nearest").sel(
            lat=slice(lat_min, lat_max),
            lon=slice(lon_min, lon_max)
        )

        arr = np.array(da)
        if arr.size == 0 or np.all(np.isnan(arr)):
            raise ValueError("Empty SARAH subset (check ROI/time).")

        vmin = np.nanpercentile(arr, pct_low) if vmin is None else vmin
        vmax = np.nanpercentile(arr, pct_high) if vmax is None else vmax
        vmax = max(vmax, vmin + 1e-6)

        norm = np.clip((arr - vmin) / (vmax - vmin), 0, 1)

        if palette == "gray":
            gray = (norm * 255).astype(np.uint8)
            h, w = gray.shape
            rgba = np.zeros((h, w, 4), dtype=np.uint8)
            rgba[..., 0] = gray
            rgba[..., 1] = gray
            rgba[..., 2] = gray
            rgba[..., 3] = alpha
        else:
            # Warm heat palette (green → yellow → orange → red)
            stops = [
                (0.00, ( 30, 120,  30)),
                (0.45, (210, 230,  90)),
                (0.70, (255, 165,  70)),
                (1.00, (220,  50,  32)),
            ]
            xs = np.linspace(0, 1, 256)
            lut = np.zeros((256, 3), dtype=np.uint8)
            for i, x in enumerate(xs):
                for (p0, c0), (p1, c1) in zip(stops[:-1], stops[1:]):
                    if x <= p1:
                        tseg = 0.0 if p1 == p0 else (x - p0) / (p1 - p0)
                        r = int(round(c0[0] + (c1[0] - c0[0]) * tseg))
                        g = int(round(c0[1] + (c1[1] - c0[1]) * tseg))
                        b = int(round(c0[2] + (c1[2] - c0[2]) * tseg))
                        lut[i] = (r, g, b)
                        break
            idx = (norm * 255).astype(np.uint8)
            rgb = lut[idx]
            h, w = idx.shape
            rgba = np.zeros((h, w, 4), dtype=np.uint8)
            rgba[..., :3] = rgb
            rgba[..., 3] = alpha

        if upscale and upscale > 1:
            pil = Image.fromarray(rgba, mode="RGBA")
            pil = pil.resize((rgba.shape[1] * upscale, rgba.shape[0] * upscale), resample=Image.BILINEAR)
            rgba = np.array(pil)

        bounds = [
            [float(da.lat.min()), float(da.lon.min())],
            [float(da.lat.max()), float(da.lon.max())]
        ]
        return rgba, bounds
    finally:
        ds.close()