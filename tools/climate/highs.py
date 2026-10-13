"""Subtropical highs: annual-mean ICOADS sea-level pressure >= LEVEL hPa between 10 and 48 deg N/S.

usage: highs.py LEVEL OUT.json PREVIEW.png   (the deck uses LEVEL 1018; write_geo.py reads $CLIMATE_DATA/highs.json)
The field is tiled twice in longitude so the North Pacific cell isn't cut at 180; cells are kept once, by centroid.
"""
import json
import sys

from shapely import affinity
from shapely.geometry import Polygon, box

from wind import LAT, LON, field, np, plt, preview

level = float(sys.argv[1])
p = field("slp", 0).copy()
p[~((np.abs(LAT) > 10) & (np.abs(LAT) < 48)), :] = np.nan
fig, ax = plt.subplots()
LX, PX = np.concatenate([LON, LON + 360]), np.concatenate([p, p], axis=1)
cs = ax.contourf(LX, LAT, PX, levels=[level, 1100])
polys = []
for path in cs.get_paths():
    for ring in path.to_polygons():
        if len(ring) > 3:
            pg = Polygon(ring).buffer(0)
            if pg.area > 20 and -140 <= pg.centroid.x < 220:
                polys.append(pg)
polys = [pg.buffer(1.5, join_style=1).buffer(-1.5, join_style=1).simplify(0.8) for pg in polys]
for pg in sorted(polys, key=lambda g: g.centroid.x):
    print(round(pg.centroid.x), round(pg.centroid.y), round(pg.area), [round(b, 1) for b in pg.bounds], len(pg.exterior.coords))
out = []
for pg in polys:
    for part in [pg.intersection(box(-180, -90, 180, 90)), affinity.translate(pg.intersection(box(180, -90, 540, 90)), -360)]:
        for g in getattr(part, "geoms", [part]):
            if not g.is_empty and g.geom_type == "Polygon":
                out.append([[round(x, 1), round(y, 1)] for x, y in g.exterior.coords])
json.dump(out, open(sys.argv[2], "w"))
print(len(out), "parts")
preview(0, (-180, -60, 180, 60), sys.argv[3], polys=out, stride=2)
