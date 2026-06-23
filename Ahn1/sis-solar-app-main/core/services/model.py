import joblib, json, pandas as pd
from ..utils.time_features import add_time_features

def load_model(model_path, meta_path):
    model = joblib.load(model_path)
    with open(meta_path, "r") as f: meta = json.load(f)
    return model, meta

def build_feature_frame(cams_window, feature_names):
    feat = add_time_features(cams_window)
    return feat[feature_names]

def build_future_feature_frame(start_utc, end_utc, feature_names):
    ix = pd.date_range(start=start_utc, end=end_utc, freq="30min", tz="UTC", inclusive="both")
    df = pd.DataFrame(index=ix)
    df["Reliability"] = 1.0
    feat = add_time_features(df)
    for c in feature_names:
        if c not in feat: feat[c] = 0.0
    return feat[feature_names]
