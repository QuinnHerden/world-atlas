"""Pipeline gates. `data`: before rendering. `deck`: before `ankc build`. `package`: after it."""

import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from shapely import unary_union
from shapely.geometry.base import BaseGeometry

from geofeat.frame import laea, project
from geofeat.model import DECK, MEDIA_INDEX, ROOT, ROOT_DECK, Feature, active, load_features
from geofeat.resolve import resolve

RIVER_GAP_M = 20_000
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


def _check_feature(feature: Feature) -> list[str]:
    try:
        geometry = resolve(feature)
    except (ValueError, OSError) as exc:
        return [str(exc)]
    if geometry.is_empty:
        return [f"{feature.id}: empty geometry"]
    errors = []
    types = {g.geom_type for g in getattr(geometry, "geoms", [geometry])} if geometry.geom_type == "GeometryCollection" else {geometry.geom_type}
    if not types <= STYLE_GEOMETRY[feature.style]:
        errors.append(f"{feature.id}: {sorted(types)} geometry doesn't fit style {feature.style!r}")
    if feature.style == "line" and (pieces := _pieces(geometry)) > 1:
        errors.append(f"{feature.id}: line is {pieces} disconnected pieces (gaps > {RIVER_GAP_M // 1000} km)")
    return errors


def check_data() -> list[str]:
    features = active(load_features())
    errors = [f"{f.id}: no uid (run `make ids` and commit)" for f in features if f.uid is None]
    for feature in features:
        errors += _check_feature(feature)
    return errors


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
    errors = {"data": check_data, "deck": check_deck, "package": check_package}[stage]()
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        sys.exit(1)
    print(f"check {stage}: ok")


if __name__ == "__main__":
    main()
