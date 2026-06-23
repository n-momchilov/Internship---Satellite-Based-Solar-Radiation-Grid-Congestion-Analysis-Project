import pandas as pd

def load_cams_30(path):
    df = pd.read_csv(path, parse_dates=["time_utc"]).set_index("time_utc").sort_index()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    return df

def slice_cams(df, start_utc, end_utc):
    s = pd.to_datetime(start_utc).tz_localize("UTC")
    e = pd.to_datetime(end_utc).tz_localize("UTC")
    return df.loc[s:e]
