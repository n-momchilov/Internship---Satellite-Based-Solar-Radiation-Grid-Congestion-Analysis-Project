import pandas as pd

def pick_overlay_time(d1_utc, d2_utc, is_future, cams_window=None):
    if (not is_future) and (cams_window is not None) and (not cams_window.empty):
        df = cams_window.between_time("10:00", "14:00")
        if not df.empty and "GHI_Wm2" in df:
            t = df["GHI_Wm2"].idxmax()
            if t is not None: return pd.Timestamp(t).tz_convert("UTC")
        t0 = pd.to_datetime(d1_utc).tz_localize("UTC")
        return (t0 + pd.Timedelta(hours=12))
    start = pd.to_datetime(d1_utc).tz_localize("UTC")
    end   = pd.to_datetime(d2_utc).tz_localize("UTC")
    mid   = start + (end - start) / 2
    return (mid.normalize() + pd.Timedelta(hours=12))
