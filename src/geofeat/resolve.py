"""Turn a feature's geometry parts into one shapely geometry, checking every selector and expectation."""

import json
from functools import cache
from pathlib import Path

import geopandas as gpd
import shapely
from pyproj import Geod
from shapely import unary_union
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from geofeat.model import GEOMETRY, LOCK, VENDOR, Feature

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


def _custom(file: str) -> BaseGeometry:
    path = (GEOMETRY / file).resolve()
    if not path.is_relative_to(GEOMETRY.resolve()):
        raise ValueError(f"{file}: outside {GEOMETRY}")
    collection = json.loads(path.read_text())
    for feature in collection["features"]:
        if not feature.get("properties", {}).get("source"):
            raise ValueError(f"{file}: every feature needs a `source` property")
    return unary_union([shape(f["geometry"]) for f in collection["features"]])


def resolve(feature: Feature) -> BaseGeometry:
    parts = []
    for part in feature.geometry:
        if part.file:
            parts.append(_custom(part.file))
            continue
        gdf = layer(part.layer)
        unknown = {k.lower() for k in part.select} - set(gdf.columns)
        if unknown:
            raise ValueError(f"{feature.id}: {part.layer} has no column(s) {sorted(unknown)}")
        mask = True
        for key, value in part.select.items():
            mask = mask & (gdf[key.lower()] == value)
        matched = gdf[mask]
        if len(matched) != part.rows:
            raise ValueError(
                f"{feature.id}: {part.layer} {part.select} matched {len(matched)} rows, expected {part.rows}"
            )
        parts.append(unary_union(matched.geometry.values))
    geometry = unary_union(parts)
    _check_expect(feature, geometry)
    return geometry


def _in_bbox(geometry: BaseGeometry, bbox: tuple[float, float, float, float]) -> bool:
    lon_min, lat_min, lon_max, lat_max = bbox
    coords = shapely.get_coordinates(geometry)
    lons, lats = coords[:, 0], coords[:, 1]
    if lon_min <= lon_max:
        in_lon = (lons >= lon_min) & (lons <= lon_max)
    else:
        in_lon = (lons >= lon_min) | (lons <= lon_max)
    return bool((in_lon & (lats >= lat_min) & (lats <= lat_max)).all())


def _check_expect(feature: Feature, geometry: BaseGeometry) -> None:
    expect = feature.expect
    if not _in_bbox(geometry, expect.bbox):
        raise ValueError(f"{feature.id}: geometry falls outside expected bbox {expect.bbox}")
    if expect.length_km:
        _in_range(feature.id, "length_km", GEOD.geometry_length(geometry) / 1000, expect.length_km)
    if expect.area_km2:
        _in_range(feature.id, "area_km2", abs(GEOD.geometry_area_perimeter(geometry)[0]) / 1e6, expect.area_km2)


def _in_range(feature_id: str, label: str, value: float, bounds: tuple[float, float]) -> None:
    if not bounds[0] <= value <= bounds[1]:
        raise ValueError(f"{feature_id}: {label} {value:.0f} outside expected {bounds}")
