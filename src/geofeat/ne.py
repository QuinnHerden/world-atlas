"""Natural Earth access and line helpers shared by the resolver and the renderer. The renderer reads it, so its source
is in every card's cache key; resolve.py, whose output is hashed as geometry, is not."""

import json
from functools import cache
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely
from pyproj import Geod
from shapely.geometry import LineString, MultiLineString
from shapely.geometry.base import BaseGeometry

from geofeat.model import LOCK, VENDOR

GEOD = Geod(ellps="WGS84")


@cache
def _locked_files() -> frozenset[str]:
    return frozenset(Path(entry["path"]).name for entry in json.loads(LOCK.read_text()))


@cache
def layer(name: str) -> gpd.GeoDataFrame:
    file = f"ne_{name}.geojson"
    if file not in _locked_files():
        raise ValueError(f"layer {name!r} is not in {LOCK.name}")
    gdf = gpd.read_file(VENDOR / file)
    gdf.columns = [c.lower() if c != "geometry" else c for c in gdf.columns]
    return gdf


def flow_lines(geometry: BaseGeometry) -> list[LineString]:
    """A flow geometry's lines, merged only head-to-tail, with longitudes unwrapped so a line split at ±180° rejoins."""
    pieces = []
    ref = None
    for line in shapely.get_parts(geometry):
        coords = shapely.get_coordinates(line)
        coords[:, 0] = np.unwrap(coords[:, 0], period=360)
        ref = coords[0, 0] if ref is None else ref
        coords[:, 0] += 360 * round((ref - coords[0, 0]) / 360)
        if len(coords) > 1:
            pieces.append(LineString(coords))
    merged = shapely.line_merge(MultiLineString(pieces), directed=True)
    return [line for line in shapely.get_parts(merged) if line.length > 0]
