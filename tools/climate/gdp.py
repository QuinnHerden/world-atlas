"""NOAA AOML Global Drifter Program annual-mean near-surface velocity (Laurindo, Mariano & Lumpkin 2017), 0.25 deg:
streamlines and previews used to trace and check the ocean currents. Reads $CLIMATE_DATA/gdp-annual.dat.

usage: gdp.py   (prints thinned Kuroshio and Gulf Stream streamlines and writes previews)
"""
import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import DATA, NE_50M_LAND

df = pd.read_csv(DATA / "gdp-annual.dat", sep=r"\s+")
LAT, LON = np.arange(-89.875, 90, 0.25), np.arange(-179.875, 180, 0.25)
U = np.full((len(LAT), len(LON)), np.nan)
V = U.copy()
i, j = np.round((df.Lat.values - LAT[0]) / 0.25).astype(int), np.round((df.Lon.values - LON[0]) / 0.25).astype(int)
U[i, j], V[i, j] = df.Ubar.values, df.Vbar.values


def smooth(a: np.ndarray, k: int) -> np.ndarray:
    """Box mean over (2k+1)^2 cells ignoring NaN; cells with under 30% data become NaN."""
    m = np.isfinite(a)
    zs, ms = np.pad(np.where(m, a, 0.0), k), np.pad(m.astype(float), k)
    out, cnt = np.zeros_like(a), np.zeros_like(a)
    for di in range(2 * k + 1):
        for dj in range(2 * k + 1):
            out += zs[di:di + a.shape[0], dj:dj + a.shape[1]]
            cnt += ms[di:di + a.shape[0], dj:dj + a.shape[1]]
    with np.errstate(invalid="ignore"):
        r = out / cnt
    r[cnt < (2 * k + 1) ** 2 * 0.3] = np.nan
    return r


def interp(a: np.ndarray, lon: float, lat: float) -> float:
    fi, fj = (lat - LAT[0]) / 0.25, (lon - LON[0]) / 0.25
    i0, j0 = int(np.floor(fi)), int(np.floor(fj))
    if not (0 <= i0 < len(LAT) - 1 and 0 <= j0 < len(LON) - 1):
        return np.nan
    di, dj = fi - i0, fj - j0
    return a[i0, j0] * (1 - di) * (1 - dj) + a[i0 + 1, j0] * di * (1 - dj) + a[i0, j0 + 1] * (1 - di) * dj + a[i0 + 1, j0 + 1] * di * dj


def streamline(u, v, lon, lat, km, step=25, minspeed=0.02) -> list[tuple[float, float]]:
    pts = [(lon, lat)]
    for _ in range(int(km / step)):
        uu, vv = interp(u, lon, lat), interp(v, lon, lat)
        if not np.isfinite(uu + vv) or np.hypot(uu, vv) < minspeed:
            break
        s = np.hypot(uu, vv)
        mlat, mlon = lat + step / 222 * vv / s, lon + step / (222 * np.cos(np.radians(lat))) * uu / s
        u2, v2 = interp(u, mlon, mlat), interp(v, mlon, mlat)
        if not np.isfinite(u2 + v2):
            break
        s2 = np.hypot(u2, v2)
        lat += step / 111 * v2 / s2
        lon += step / (111 * np.cos(np.radians(lat))) * u2 / s2
        pts.append((lon, lat))
    return pts


def preview(u, v, bbox, out, lines=(), stride=4) -> None:
    lon0, lat0, lon1, lat1 = bbox
    fig, ax = plt.subplots(figsize=(13, 9))
    gpd.read_file(NE_50M_LAND).cx[lon0:lon1, lat0:lat1].plot(ax=ax, color="#eee", edgecolor="#88a", lw=0.5)
    m, n = (LON >= lon0) & (LON <= lon1), (LAT >= lat0) & (LAT <= lat1)
    X, Y = np.meshgrid(LON[m][::stride], LAT[n][::stride])
    uu, vv = u[np.ix_(n, m)][::stride, ::stride], v[np.ix_(n, m)][::stride, ::stride]
    sp = np.hypot(uu, vv)
    ax.quiver(X, Y, uu / np.maximum(sp, 1e-3), vv / np.maximum(sp, 1e-3), sp, cmap="viridis", scale=60, clim=(0, 0.5))
    for ln in lines:
        xs, ys = zip(*ln)
        ax.plot(xs, ys, "r-", lw=2)
        ax.plot(xs[-1], ys[-1], "r>", ms=8)
    ax.set_xlim(lon0, lon1)
    ax.set_ylim(lat0, lat1)
    ax.grid(True, lw=0.3)
    fig.savefig(out, dpi=70, bbox_inches="tight")


if __name__ == "__main__":
    u, v = smooth(U, 2), smooth(V, 2)
    kuroshio = streamline(u, v, 123.5, 14, 3500)
    print("kuroshio", [(round(a, 1), round(b, 1)) for a, b in kuroshio[::8]])
    preview(u, v, (115, 8, 160, 42), DATA / "kuroshio.png", [kuroshio])
    gulf = streamline(u, v, -81.5, 24.3, 8000)
    print("gulf stream", [(round(a, 1), round(b, 1)) for a, b in gulf[::12]])
    preview(u, v, (-85, 20, 10, 68), DATA / "gulf-stream.png", [gulf], stride=6)
