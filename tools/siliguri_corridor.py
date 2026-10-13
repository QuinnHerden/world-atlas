"""Derive geometry/siliguri-corridor.geojson: India within 40 km of both Nepal and Bangladesh (NE 10m admin-0).

usage: uv run python tools/siliguri_corridor.py   (prints the polygon as GeoJSON; paste it into the file's geometry)
"""
import json

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import box, mapping
from shapely.geometry.polygon import orient

from geofeat.resolve import layer

REACH_M = 40_000
LAEA = "+proj=laea +lon_0=88.4 +lat_0=26.6"
to_m = Transformer.from_crs("EPSG:4326", LAEA, always_xy=True)
to_deg = Transformer.from_crs(LAEA, "EPSG:4326", always_xy=True)


def project(g, t: Transformer):
    return shapely.transform(g, lambda xy: np.column_stack(t.transform(xy[:, 0], xy[:, 1])))


countries = layer("10m_admin_0_countries")
india, nepal, bangladesh = (
    project(countries[countries.adm0_a3 == code].geometry.iloc[0].intersection(box(86.5, 25.0, 90.5, 28.0)), to_m)
    for code in ("IND", "NPL", "BGD")
)
lens = india.intersection(nepal.buffer(REACH_M, quad_segs=32)).intersection(bangladesh.buffer(REACH_M, quad_segs=32))
corridor = project(max(shapely.get_parts(lens), key=lambda p: p.area), to_deg)
corridor = orient(shapely.set_precision(corridor.simplify(0.003), 0.001), 1.0)
print(json.dumps(mapping(corridor)))
