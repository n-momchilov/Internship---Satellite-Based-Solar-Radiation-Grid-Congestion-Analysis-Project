import numpy as np

def add_time_features(df):
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
