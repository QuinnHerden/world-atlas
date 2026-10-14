"""Turn a feature's geometry parts into one shapely geometry, checking every selector and expectation."""

import json
import re
from functools import cache
from pathlib import Path
from typing import get_args

import shapely
from shapely import unary_union
from shapely.geometry import MultiLineString, shape
from shapely.geometry.base import BaseGeometry

from geofeat.model import GEOMETRY, LAND_FAMILIES, Feature, Method, Part, load_features
from geofeat.ne import GEOD, flow_lines, layer  # noqa: F401  flow_lines re-exported for check.py and tests

SLIVER_KM2 = 2_500
MAX_DROPPED_SHARE = 0.01
NOT_VERIFIED = re.compile(r"unverified|placeholder", re.IGNORECASE)


def geometry_path(file: str) -> Path:
    """A file in geometry/, refusing any name that resolves outside it."""
    path = (GEOMETRY / file).resolve()
    if not path.is_relative_to(GEOMETRY.resolve()):
        raise ValueError(f"{file}: outside {GEOMETRY}")
    return path


def provenance_errors(name: str, collection: dict) -> list[str]:
    """Every hand-authored feature says where it came from: a `source` that isn't a placeholder, a `method`, `refs`."""
    features = collection.get("features") if isinstance(collection, dict) else None
    if not isinstance(features, list):
        return [f"{name}: not a GeoJSON FeatureCollection with a `features` list"]
    errors = []
    for i, feature in enumerate(features):
        props = (feature.get("properties") if isinstance(feature, dict) else None) or {}
        where = f"{name} feature {i}"
        source = props.get("source")
        if not isinstance(source, str) or not source:
            errors.append(f"{where}: `source` must be non-empty text")
        elif NOT_VERIFIED.search(source):
            errors.append(f"{where}: `source` says it is unverified or a placeholder")
        if props.get("method") not in get_args(Method):
            errors.append(f"{where}: `method` must be one of {', '.join(get_args(Method))}")
        refs = props.get("refs")
        if not isinstance(refs, list) or not refs or not all(isinstance(r, str) and r for r in refs):
            errors.append(f"{where}: `refs` must be a non-empty list of references")
    return errors


def custom(file: str) -> BaseGeometry:
    collection = json.loads(geometry_path(file).read_text())
    if errors := provenance_errors(file, collection):
        raise ValueError("; ".join(errors))
    return combine([shape(f["geometry"]) for f in collection["features"]])


def combine(geometries: list[BaseGeometry]) -> BaseGeometry:
    """Union the parts, except all-line parts, which stay as drawn: a union would split them where they cross."""
    if all(g.geom_type in ("LineString", "MultiLineString") for g in geometries):
        return MultiLineString([line for g in geometries for line in shapely.get_parts(g) if not line.is_empty])
    return unary_union(geometries)


@cache
def features_by_id() -> dict[str, Feature]:
    return {f.id: f for f in load_features()}


def _part(feature: Feature, part: Part, stack: tuple[str, ...]) -> BaseGeometry:
    if part.file:
        return custom(part.file)
    if part.feature:
        if part.feature in stack:
            raise ValueError(f"{feature.id}: feature reference cycle {' -> '.join((*stack, part.feature))}")
        if part.feature not in features_by_id():
            raise ValueError(f"{feature.id}: references unknown feature {part.feature!r}")
        return resolve_with_trim(features_by_id()[part.feature], stack)[0]
    gdf = layer(part.layer)
    unknown = {k.lower() for k in part.select} - set(gdf.columns)
    if unknown:
        raise ValueError(f"{feature.id}: {part.layer} has no column(s) {sorted(unknown)}")
    mask = True
    for key, value in part.select.items():
        mask = mask & (gdf[key.lower()] == value)
    matched = gdf[mask]
    if len(matched) != part.rows:
        raise ValueError(f"{feature.id}: {part.layer} {part.select} matched {len(matched)} rows, expected {part.rows}")
    return unary_union(matched.geometry.values)


def area_km2(geometry: BaseGeometry) -> float:
    return abs(GEOD.geometry_area_perimeter(geometry)[0]) / 1e6


def _drop_slivers(feature: Feature, keep: BaseGeometry, cut_result: BaseGeometry) -> tuple[BaseGeometry, float]:
    """Drop small polygons the cut created where borders don't quite match; untouched pieces, lines and points stay.

    With `trim_to_largest`, every polygon but the largest goes, cut or not; the caller reports how much.
    """
    original = shapely.get_parts(keep)
    pieces = list(shapely.get_parts(cut_result))
    largest = max((p for p in pieces if p.geom_type == "Polygon"), key=area_km2, default=None)
    kept, slivers, trimmed = [], 0.0, 0.0
    for piece in pieces:
        if piece.geom_type != "Polygon" or piece is largest:
            kept.append(piece)
        elif feature.trim_to_largest:
            trimmed += area_km2(piece)
        elif any(piece.equals(o) for o in original):
            kept.append(piece)
        elif (area := area_km2(piece)) < SLIVER_KM2:
            slivers += area
        else:
            kept.append(piece)
    result = unary_union(kept)
    if slivers > MAX_DROPPED_SHARE * area_km2(result):
        raise ValueError(f"{feature.id}: subtracting dropped {slivers:.0f} km² of slivers; check the cut")
    return result, trimmed


def land_within(bounds: tuple[float, float, float, float]) -> BaseGeometry:
    """Natural Earth 10m land inside a lon/lat box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = bounds
    return unary_union([shapely.clip_by_rect(g, x0, y0, x1, y1) for g in layer("10m_land").cx[x0:x1, y0:y1].geometry])


def clip_to_land(feature: Feature, geometry: BaseGeometry) -> BaseGeometry:
    """Cut an area feature of a land family (plain, plateau, peninsula, region…) to Natural Earth 10m land, so no
    highlight spills into the sea whatever its source polygon did."""
    if feature.style != "area" or feature.family not in LAND_FAMILIES:
        return geometry
    clipped = shapely.make_valid(geometry.intersection(land_within(geometry.bounds)))
    return unary_union([g for g in shapely.get_parts(clipped) if g.geom_type in ("Polygon", "MultiPolygon")])


def resolve_with_trim(feature: Feature, stack: tuple[str, ...] = ()) -> tuple[BaseGeometry, float]:
    """The feature's geometry, and the km² that `trim_to_largest` removed (0 without it)."""
    stack = (*stack, feature.id)
    keep = clip_to_land(feature, combine([_part(feature, p, stack) for p in feature.geometry if not p.subtract]))
    cut = [_part(feature, p, stack) for p in feature.geometry if p.subtract]
    geometry, trimmed = (keep, 0.0)
    if cut:
        geometry, trimmed = _drop_slivers(feature, keep, shapely.make_valid(keep.difference(unary_union(cut))))
    _check_expect(feature, geometry)
    return geometry, trimmed


def resolve(feature: Feature, stack: tuple[str, ...] = ()) -> BaseGeometry:
    return resolve_with_trim(feature, stack)[0]


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
        _in_range(feature.id, "length_km", GEOD.geometry_length(unary_union(geometry)) / 1000, expect.length_km)
    if expect.area_km2:
        _in_range(feature.id, "area_km2", abs(GEOD.geometry_area_perimeter(geometry)[0]) / 1e6, expect.area_km2)


def _in_range(feature_id: str, label: str, value: float, bounds: tuple[float, float]) -> None:
    if not bounds[0] <= value <= bounds[1]:
        raise ValueError(f"{feature_id}: {label} {value:.0f} outside expected {bounds}")
