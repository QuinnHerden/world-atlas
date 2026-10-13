"""ICOADS 2-degree enhanced monthly long-term mean 1971-2000 (NOAA PSL, via NOAA ERD ERDDAP esrlIcoads2gec71):
fields, streamlines and quiver previews. Reads $CLIMATE_DATA/icoads.csv."""
import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common import DATA, NE_50M_LAND

_df = pd.read_csv(DATA / "icoads.csv", skiprows=[1])
_times = sorted(_df.time.unique())
LAT, LON = np.sort(_df.latitude.unique()), np.sort(_df.longitude.unique())
F = {}
for v in ["slp", "uwnd", "vwnd", "sst"]:
    arr = np.full((12, len(LAT), len(LON)), np.nan)
    for m, t in enumerate(_times):
        arr[m] = _df[_df.time == t].pivot(index="latitude", columns="longitude", values=v).reindex(index=LAT, columns=LON).values
    F[v] = arr
F["annual"] = {v: np.nanmean(F[v], axis=0) for v in ["slp", "uwnd", "vwnd", "sst"]}


def field(v: str, month: int) -> np.ndarray:
    """Month 1..12, or 0 for the annual mean."""
    return F["annual"][v] if month == 0 else F[v][month - 1]


def interp(a: np.ndarray, lon: float, lat: float) -> float:
    lon = (lon + 180) % 360 - 180
    i, j = (lat - LAT[0]) / (LAT[1] - LAT[0]), (lon - LON[0]) / (LON[1] - LON[0])
    i0, j0 = int(np.floor(i)), int(np.floor(j)) % len(LON)
    if i0 < 0 or i0 + 1 >= len(LAT):
        return np.nan
    j1, fi, fj = (j0 + 1) % len(LON), i - np.floor(i), j - np.floor(j)
    return a[i0, j0] * (1 - fi) * (1 - fj) + a[i0 + 1, j0] * fi * (1 - fj) + a[i0, j1] * (1 - fi) * fj + a[i0 + 1, j1] * fi * fj


def streamline(lon: float, lat: float, month: int, km: float, step_km: float = 50) -> list[tuple[float, float]]:
    """Midpoint-method streamline of the surface wind; stops on missing data or below 0.3 m/s."""
    u, v = field("uwnd", month), field("vwnd", month)
    pts = [(lon, lat)]
    for _ in range(int(km / step_km)):
        uu, vv = interp(u, lon, lat), interp(v, lon, lat)
        if not np.isfinite(uu + vv) or np.hypot(uu, vv) < 0.3:
            break
        s = np.hypot(uu, vv)
        dlat, dlon = step_km / 111.0 * vv / s, step_km / (111.0 * np.cos(np.radians(lat))) * uu / s
        u2, v2 = interp(u, lon + dlon / 2, lat + dlat / 2), interp(v, lon + dlon / 2, lat + dlat / 2)
        if not np.isfinite(u2 + v2):
            break
        s2 = np.hypot(u2, v2)
        lat += step_km / 111.0 * v2 / s2
        lon += step_km / (111.0 * np.cos(np.radians(lat))) * u2 / s2
        pts.append((lon, lat))
    return pts


def preview(month, bbox, out, lines=(), polys=(), stride=1, slp=True) -> None:
    lon0, lat0, lon1, lat1 = bbox
    fig, ax = plt.subplots(figsize=(14, 8))
    gpd.read_file(NE_50M_LAND).cx[lon0:lon1, lat0:lat1].plot(ax=ax, color="#eee", edgecolor="#88a", lw=0.5)
    m, n = (LON >= lon0) & (LON <= lon1), (LAT >= lat0) & (LAT <= lat1)
    X, Y = np.meshgrid(LON[m], LAT[n])
    u, v = field("uwnd", month)[np.ix_(n, m)], field("vwnd", month)[np.ix_(n, m)]
    ax.quiver(X[::stride, ::stride], Y[::stride, ::stride], u[::stride, ::stride], v[::stride, ::stride],
              np.hypot(u, v)[::stride, ::stride], cmap="viridis", scale=250)
    if slp:
        cs = ax.contour(X, Y, field("slp", month)[np.ix_(n, m)], levels=np.arange(996, 1030, 2), colors="k", linewidths=0.4)
        ax.clabel(cs, fontsize=6)
    for ln in lines:
        xs, ys = zip(*ln)
        ax.plot(xs, ys, "r-", lw=2)
        ax.plot(xs[-1], ys[-1], "r>", ms=8)
    for pg in polys:
        ax.plot(*zip(*pg), "m-", lw=2)
    ax.set_xlim(lon0, lon1)
    ax.set_ylim(lat0, lat1)
    ax.grid(True, lw=0.3)
    ax.set_title(f"month {month}")
    fig.savefig(out, dpi=70, bbox_inches="tight")
