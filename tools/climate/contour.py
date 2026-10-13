"""Smoothed fix density -> the outer contour polygon at a fraction of the peak. Writes a preview PNG; prints the ring.

usage: contour.py FIXES.npz LON0,LAT0,LON1,LAT1 RES_DEG FRACTION PREVIEW.png
The last printed line is the ring as JSON, which write_geo.py reads from <name>.poly.json.
"""
import json
import sys

import geopandas as gpd
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon

from common import NE_50M_LAND

npz, bbox, res, frac, out = sys.argv[1], [float(v) for v in sys.argv[2].split(",")], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
d = np.load(npz)
lon0, lat0, lon1, lat1 = bbox
xe, ye = np.arange(lon0, lon1 + res, res), np.arange(lat0, lat1 + res, res)
H = np.histogram2d(d["lon"], d["lat"], bins=[xe, ye])[0].T
k = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], float)
k /= k.sum()
P = np.pad(H, 1)
S = sum(k[i, j] * P[i:i + H.shape[0], j:j + H.shape[1]] for i in range(3) for j in range(3))
xc, yc = (xe[:-1] + xe[1:]) / 2, (ye[:-1] + ye[1:]) / 2
level = frac * S.max()
fig, ax = plt.subplots(figsize=(12, 7))
cs = ax.contour(xc, yc, S, levels=[level], colors="r")
ax.pcolormesh(xe, ye, S, cmap="Greys", alpha=0.6)
gpd.read_file(NE_50M_LAND).cx[lon0:lon1, lat0:lat1].boundary.plot(ax=ax, color="b", lw=0.5)
ax.set_xlim(lon0, lon1)
ax.set_ylim(lat0, lat1)
ax.grid(True)
polys = [Polygon(ring) for path in cs.get_paths() for ring in path.to_polygons() if len(ring) > 3]
big = max(polys, key=lambda p: p.area)
simp = big.buffer(res, join_style=2).buffer(-res, join_style=2).simplify(res * 0.4)
ax.plot(*simp.exterior.xy, "g-", lw=2)
fig.savefig(out, dpi=80)
print("peak", S.max(), "level", level, "pieces", len(polys), "areas", sorted(round(p.area) for p in polys)[-4:])
print(json.dumps([[round(a, 1), round(b, 1)] for a, b in simp.exterior.coords]))
