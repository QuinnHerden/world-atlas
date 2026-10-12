"""Pipeline gates. `data`: before rendering. `deck`: before `ankc build`. `package`: after it."""

import json
import math
import re
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import shapely
from pyproj import Transformer
from shapely import unary_union
from shapely.geometry import MultiLineString, Point
from shapely.geometry.base import BaseGeometry

from geofeat.frame import laea, project
from geofeat.model import DECK, MEDIA_INDEX, ROOT, ROOT_DECK, Feature, active, load_features
from geofeat.pairs import NEAR_M, find_pairs
from geofeat.resolve import features_by_id, flow_lines, layer, resolve_with_trim

RIVER_GAP_M = 20_000
MOUTH_M = 5_000
JUNCTION_M = 2_000  # Natural Earth river parts meet within about a kilometre, not on shared nodes
MOUTH_WATER = {"sea": "10m_ocean", "lake": "10m_lakes"}  # NE puts the Caspian in the ocean layer
STYLE_GEOMETRY = {
    "area": {"Polygon", "MultiPolygon"},
    "band": {"Polygon", "MultiPolygon"},
    "line": {"LineString", "MultiLineString"},
    "flow-current": {"LineString", "MultiLineString"},
    "flow-wind": {"LineString", "MultiLineString"},
    "strait": {"Polygon", "MultiPolygon", "LineString", "MultiLineString"},
    "point": {"Point", "MultiPoint"},
}


def _pieces(geometry: BaseGeometry) -> int:
    """Number of separate pieces after closing gaps up to RIVER_GAP_M."""
    merged = unary_union(project(geometry, laea(geometry)).buffer(RIVER_GAP_M / 2))
    return len(getattr(merged, "geoms", [merged]))


def _chain_breaks(geometry: BaseGeometry) -> bool:
    """True when some pieces only join if one is reversed, i.e. a hand-drawn segment points the wrong way."""
    lines = flow_lines(geometry)
    return len(shapely.get_parts(shapely.line_merge(MultiLineString(lines)))) < len(lines)


def _true_ends(geometry: BaseGeometry) -> list[tuple[float, float]]:
    """Ends of the merged line that touch no other line: sources and mouths, not junctions or lake hand-offs."""
    lines = list(shapely.get_parts(shapely.line_merge(unary_union(geometry))))
    projection = laea(geometry)
    projected = [project(line, projection) for line in lines]
    ends = []
    for i, line in enumerate(lines):
        for at in (0, -1):
            end = project(Point(line.coords[at]), projection)
            others = [p for j, p in enumerate(projected) if j != i]
            if line.coords[0] != line.coords[-1] and all(o.distance(end) > JUNCTION_M for o in others):
                ends.append(line.coords[at][:2])
    return ends


def _reaches(geometry: BaseGeometry, water: str) -> bool:
    """Whether a true end of the line is within MOUTH_M of the given water layer."""
    return any(_near(layer(water), lon, lat) for lon, lat in _true_ends(geometry))


def _near(water: gpd.GeoDataFrame, lon: float, lat: float) -> bool:
    lat_margin = 2 * MOUTH_M / 111_000
    lon_margin = lat_margin / max(math.cos(math.radians(lat)), 0.05)
    to_local = Transformer.from_crs("EPSG:4326", f"+proj=aeqd +lon_0={lon} +lat_0={lat}", always_xy=True)
    for polygon in water.cx[lon - lon_margin:lon + lon_margin, lat - lat_margin:lat + lat_margin].geometry:
        nearby = shapely.clip_by_rect(polygon, lon - lon_margin, lat - lat_margin, lon + lon_margin, lat + lat_margin)
        if not nearby.is_empty and shapely.transform(nearby, to_local.transform, interleaved=False).distance(Point(0, 0)) <= MOUTH_M:
            return True
    return False


def _check_feature(feature: Feature, geometry: BaseGeometry) -> list[str]:
    if geometry.is_empty:
        return [f"{feature.id}: empty geometry"]
    types = {g.geom_type for g in getattr(geometry, "geoms", [geometry])} if geometry.geom_type == "GeometryCollection" else {geometry.geom_type}
    if not types <= STYLE_GEOMETRY[feature.style]:
        return [f"{feature.id}: {sorted(types)} geometry doesn't fit style {feature.style!r}"]
    if feature.style == "line" and (pieces := _pieces(geometry)) > 1:
        return [f"{feature.id}: line is {pieces} disconnected pieces (gaps > {RIVER_GAP_M // 1000} km)"]
    for other in feature.frame.context:
        if other not in features_by_id() or other == feature.id or features_by_id()[other].style != "line":
            return [f"{feature.id}: frame.context {other!r} must be another feature drawn as a line"]
    for allowed in feature.allow_nested:
        if allowed.id not in features_by_id() or allowed.id == feature.id:
            return [f"{feature.id}: allow_nested names unknown feature {allowed.id!r}"]
    if feature.style.startswith("flow") and any(p.subtract for p in feature.geometry):
        return [f"{feature.id}: flow features can't subtract parts; the cut would split lines where they cross"]
    if feature.style.startswith("flow") and _chain_breaks(geometry):
        return [f"{feature.id}: flow lines don't chain head-to-tail; a piece is drawn backwards"]
    mouth = feature.expect.mouth
    if feature.type == "River" and feature.style == "line" and mouth != "none" and not _reaches(geometry, MOUTH_WATER[mouth]):
        return [f"{feature.id}: no end within {MOUTH_M // 1000} km of the {mouth} (expect.mouth: {mouth})"]
    return []


def check_data() -> tuple[list[str], list[str]]:
    """Errors, and notes that must stay visible: trims, nesting overrides, and flagged or nested sibling pairs."""
    features = active(load_features())
    errors = [f"{f.id}: no uid (run `make ids` and commit)" for f in features if f.uid is None]
    notes = []
    clean = {}
    for feature in features:
        try:
            geometry, trimmed = resolve_with_trim(feature)
            problems = _check_feature(feature, geometry)
        except (ValueError, OSError) as exc:
            problems = [str(exc)]
        errors += problems
        if problems:
            continue
        clean[feature.id] = (feature, geometry)
        if feature.trim_to_largest:
            notes.append(f"trim: {feature.id} keeps its largest piece, dropping {trimmed:,.0f} km²")
        notes += [f"override: {feature.id} ~ {o.id} may nest: {o.reason}" for o in feature.allow_nested]
    pairs = [p for p in find_pairs(clean) if p.flagged or p.nested]
    errors += [f"{p.a} ~ {p.b}: highlights too alike (IoU {p.iou:.2f}, cover {p.cover:.2f})" for p in pairs if p.flagged]
    notes.append(f"sibling pairs flagged or nested (within {NEAR_M // 1000} km or overlapping; `make pairs` lists all):")
    return errors, notes + [f"  {p}" for p in pairs]


def check_deck() -> list[str]:
    errors = []
    media = json.loads(MEDIA_INDEX.read_text()) if MEDIA_INDEX.exists() else {}
    for f in active(load_features()):
        if f.id not in media or not (DECK / media[f.id]).exists():
            errors.append(f"{f.id}: not rendered (run `make render`)")

    version = subprocess.run(["ankc", "--version"], capture_output=True, text=True).stdout.strip()
    if not re.fullmatch(r"0\.4\.\d+", version):
        errors.append(f"ankc {version!r} found; 0.4.x required")
    result = subprocess.run(["ankc", "check", "--deck", ROOT_DECK, "--path", str(DECK)], capture_output=True, text=True)
    if result.returncode != 0:
        errors.append(f"ankc check failed:\n{result.stdout}{result.stderr}")
    return errors


def check_package() -> list[str]:
    packages = list((ROOT / "dist").glob("*.apkg"))
    if len(packages) != 1:
        return [f"expected exactly one package in dist/, found {len(packages)}"]
    expected = {f.uid for f in active(load_features())}
    with zipfile.ZipFile(packages[0]) as archive, tempfile.TemporaryDirectory() as tmp:
        archive.extract("collection.anki2", tmp)
        db = sqlite3.connect(Path(tmp) / "collection.anki2")
        guids = {row[0] for row in db.execute("select guid from notes")}
        db.close()
    errors = []
    if missing := expected - guids:
        errors.append(f"{packages[0].name}: missing notes for uids {sorted(missing)}")
    if extra := guids - expected:
        errors.append(f"{packages[0].name}: unexpected note guids {sorted(extra)}")
    return errors


def main() -> None:
    stage = sys.argv[1]
    if stage == "data":
        errors, notes = check_data()
        print("\n".join(notes))
    else:
        errors = {"deck": check_deck, "package": check_package}[stage]()
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        sys.exit(1)
    print(f"check {stage}: ok")


if __name__ == "__main__":
    main()
