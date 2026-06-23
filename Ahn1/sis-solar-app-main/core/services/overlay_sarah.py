import numpy as np, xarray as xr, pandas as pd
from PIL import Image

def sarah_slice_to_rgba(nc_path, t_utc, lat_min, lat_max, lon_min, lon_max,
                        vmin=None, vmax=None, upscale=8, palette="heat",
                        alpha=235, pct_low=5.0, pct_high=97.0):
    ds = xr.open_dataset(nc_path)
    try:
        t = (pd.Timestamp(t_utc).tz_convert("UTC").tz_localize(None)
             if getattr(t_utc, "tz", None) is not None else pd.Timestamp(t_utc))
        da = ds["SIS"].sel(time=t, method="nearest").sel(
            lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max)
        )
        arr = np.array(da)
        if arr.size == 0 or np.all(np.isnan(arr)):
            raise ValueError("Empty SARAH subset.")

        vmin = np.nanpercentile(arr, pct_low) if vmin is None else vmin
        vmax = np.nanpercentile(arr, pct_high) if vmax is None else vmax
        vmax = max(vmax, vmin + 1e-6)
        norm = np.clip((arr - vmin) / (vmax - vmin), 0, 1)

        if palette == "gray":
            gray = (norm * 255).astype(np.uint8)
            h,w = gray.shape
            rgba = np.zeros((h,w,4), dtype=np.uint8)
            rgba[...,0]=rgba[...,1]=rgba[...,2]=gray
            rgba[...,3]=alpha
        else:
            stops = [(0.00,(30,120,30)),(0.45,(210,230,90)),(0.70,(255,165,70)),(1.00,(220,50,32))]
            xs = np.linspace(0,1,256)
            lut = np.zeros((256,3), dtype=np.uint8)
            for i,x in enumerate(xs):
                for (p0,c0),(p1,c1) in zip(stops[:-1], stops[1:]):
                    if x <= p1:
                        tseg = 0.0 if p1==p0 else (x-p0)/(p1-p0)
                        lut[i] = [int(c0[j]+(c1[j]-c0[j])*tseg) for j in range(3)]
                        break
            idx = (norm*255).astype(np.uint8)
            rgb = lut[idx]; h,w = idx.shape
            rgba = np.zeros((h,w,4), dtype=np.uint8)
            rgba[...,:3]=rgb; rgba[...,3]=alpha

        if upscale and upscale>1:
            pil = Image.fromarray(rgba, "RGBA")
            pil = pil.resize((rgba.shape[1]*upscale, rgba.shape[0]*upscale), Image.BILINEAR)
            rgba = np.array(pil)

        bounds = [[float(da.lat.min()), float(da.lon.min())],
                  [float(da.lat.max()), float(da.lon.max())]]
        return rgba, bounds
    finally:
        ds.close()
