"""IBTrACS (NOAA NCEI, public domain) track fixes for one basin, written as an .npz of lat/lon for contour.py.

usage: density.py IBTRACS_CSV BASIN_FILTER WIND_MIN_KT FIRST_SEASON LAST_SEASON RES_DEG OUT.npz
BASIN_FILTER is "-" or COLUMN=VALUE (e.g. SUBBASIN=BB). Only main tracks and synoptic 00/06/12/18 UTC fixes count.
"""
import sys

import numpy as np
import pandas as pd

path, basin_filter, wind_min, y0, y1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
df = pd.read_csv(path, skiprows=[1], usecols=["SID", "SEASON", "BASIN", "SUBBASIN", "ISO_TIME", "LAT", "LON", "USA_WIND",
                                               "WMO_WIND", "TRACK_TYPE"], low_memory=False, keep_default_na=False)
df = df[df.TRACK_TYPE == "main"]
df["SEASON"] = pd.to_numeric(df.SEASON)
df = df[(df.SEASON >= y0) & (df.SEASON <= y1)]
df["W"] = pd.to_numeric(df.USA_WIND.replace(" ", np.nan), errors="coerce").fillna(
    pd.to_numeric(df.WMO_WIND.replace(" ", np.nan), errors="coerce"))
df = df[df.W >= wind_min]
df = df[pd.to_datetime(df.ISO_TIME).dt.hour.isin([0, 6, 12, 18])]
if basin_filter != "-":
    key, val = basin_filter.split("=")
    df = df[df[key] == val]
lat, lon = pd.to_numeric(df.LAT), pd.to_numeric(df.LON)
lon = lon.where(lon <= 180, lon - 360)
np.savez(sys.argv[7], lat=lat.values, lon=lon.values)
print(len(df), "fixes,", df.SID.nunique(), "storms")
