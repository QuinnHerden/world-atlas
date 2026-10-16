"""Pipeline gates. `data`: before rendering. `deck`: before `ankc build`. `package`: after it."""

import json
import math
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import NamedTuple

import geopandas as gpd
import shapely
from pyproj import Transformer
from ruamel.yaml import YAML
from shapely import unary_union
from shapely.geometry import MultiLineString, Point, Polygon
from shapely.geometry.base import BaseGeometry

import geofeat.positions as positions
from geofeat.ankc import ankc_command, ankc_version, ankc_version_text, writes_pos
from geofeat.card import card_key, load_media
from geofeat.frame import laea, project
from geofeat.deckgen import ideal_order, ordered
from geofeat.ids import duplicate_uids, uids as entry_uids
from geofeat.model import DECK, GEOMETRY, NOTE_MARKER, ROOT, ROOT_DECK, Feature, Verify, active, load_features
from geofeat.polities import read_countries, read_territory_file
from geofeat.order import Siblings, load_siblings, save_siblings
from geofeat.pairs import NEAR_M, UNCOMPARED_FAMILIES, find_pairs
from geofeat.resolve import area_km2, features_by_id, flow_lines, land_within, layer, provenance_errors, resolve_with_trim
from geofeat.sources import PATHS, all_cards, cities, political
from geofeat.sources import features as features_source

RIVER_GAP_M = 20_000
MOUTH_M = 5_000
JUNCTION_M = 2_000  # Natural Earth river parts meet within about a kilometre, not on shared nodes
MOUTH_WATER = {"sea": "10m_ocean", "lake": "10m_lakes"}  # NE puts the Caspian in the ocean layer
WATER_HOLE_KM2 = 10_000
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


def water_holes(geometry: BaseGeometry) -> list[float]:
    """km² of each hole in a water body that isn't land: a hole there means a neighbouring sea was left out."""
    holes = [Polygon(ring) for part in shapely.get_parts(geometry) if part.geom_type == "Polygon" for ring in part.interiors]
    holes = [hole for hole in holes if area_km2(hole) > WATER_HOLE_KM2]  # a smaller hole can't hold enough water
    return [area for hole in holes if (area := area_km2(hole.difference(land_within(hole.bounds)))) > WATER_HOLE_KM2]


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
    if feature.type in ("Ocean", "Sea") and (holes := water_holes(geometry)):
        return [f"{feature.id}: {len(holes)} hole(s) of open water over {WATER_HOLE_KM2:,} km² ({max(holes):,.0f} km²); union the missing sea"]
    mouth = feature.expect.mouth
    if feature.type == "River" and feature.style == "line" and mouth != "none" and not _reaches(geometry, MOUTH_WATER[mouth]):
        return [f"{feature.id}: no end within {MOUTH_M // 1000} km of the {mouth} (expect.mouth: {mouth})"]
    return []


def missing_notes(features: list[Feature]) -> list[str]:
    return [f"{f.id}: no note (1-3 sentences on why it matters)" for f in active(features) if not f.note]


class Noted(NamedTuple):
    key: str  # card key, kind:id
    note: str | None
    verify: list[Verify]


def noted() -> list[Noted]:
    """Every card that can carry a note, in file order: active features, countries and their capitals, territories
    and disputes, cities."""
    rows = [Noted(features_source.key(f), f.note, f.verify) for f in active(load_features())]
    for c in read_countries():
        rows.append(Noted(card_key("country", c.id), c.note, c.verify))
        if c.capital:
            rows.append(Noted(card_key("capital", c.id), c.capital.note, c.capital.verify))
    rows += [Noted(card_key(e.kind, e.id), e.note, e.verify) for e in read_territory_file()]
    rows += [Noted(card_key("city", c.id), c.note, c.verify) for c in cities.load_cities()]
    return rows


def note_markers(rows: list[Noted]) -> list[str]:
    return [f"{r.key}: note has research marker {m.group()!r}; move the claim to `verify` and keep the note clean"
            for r in rows if r.note and (m := NOTE_MARKER.search(r.note))]


def open_verify(rows: list[Noted]) -> list[str]:
    return [f"{r.key}: {len(r.verify)} open verify item(s); see `make verify-report`" for r in rows if r.verify]


def missing_card_notes(rows: list[Noted]) -> list[str]:
    """Every card's back shows its note, so the political and city cards need one too (`missing_notes` does features)."""
    return [f"{r.key}: no note (1-3 sentences on why it matters)" for r in rows
            if not r.note and r.key.partition(":")[0] in ("country", "capital", "city", "territory", "dispute")]


def verify_errors(release: bool) -> list[str]:
    try:
        rows = noted()
    except (ValueError, OSError) as exc:
        return [str(exc)]
    return missing_card_notes(rows) + note_markers(rows) + (open_verify(rows) if release else [])


def verify_report(rows: list[Noted]) -> str:
    """Every open verify item, by card, and a count by kind."""
    open_rows = [r for r in rows if r.verify]
    lines = []
    kinds: Counter[str] = Counter()
    for r in open_rows:
        lines.append(r.key)
        lines += [f"  [{v.as_of}] {v.claim}" + (f" (source: {v.source})" if v.source else "") for v in r.verify]
        kinds[r.key.partition(":")[0]] += len(r.verify)
    by_kind = ", ".join(f"{k} {n}" for k, n in kinds.items())
    lines.append(f"{kinds.total()} open verify item(s) on {len(open_rows)} card(s)" + (f": {by_kind}" if by_kind else ""))
    return "\n".join(lines)


def retired_references(features: list[Feature]) -> tuple[list[str], list[str]]:
    """Errors and notes for active features that point at retired ones. Retired entries aren't re-validated, so a
    reference keeps working only as long as the retired shape still resolves."""
    retired = {f.id for f in features if f.retired}
    errors, notes = [], []
    for feature in active(features):
        for part in feature.geometry:
            if part.feature in retired:
                use = "subtracts" if part.subtract else "adds"
                notes.append(f"retired input: {feature.id} {use} retired {part.feature!r} in its geometry")
        notes += [f"retired input: {feature.id} draws retired {other!r} as frame.context"
                  for other in feature.frame.context if other in retired]
        errors += [f"{feature.id}: allow_nested names retired feature {o.id!r}; drop it"
                   for o in feature.allow_nested if o.id in retired]
    return errors, notes


def check_data(release: bool = False) -> tuple[list[str], list[str]]:
    """Errors, and notes that must stay visible: trims, nesting overrides, and flagged or nested sibling pairs. A
    release also fails while any verify item is open."""
    all_features = load_features()
    features = active(all_features)
    errors = [f"{f.id}: no uid (run `make ids` and commit)" for f in features if f.uid is None]
    errors += missing_notes(all_features)
    errors += [f"uid {uid} is used more than once across {', '.join(p.name for p in PATHS)}"
               for uid in duplicate_uids(list(PATHS))]
    if not errors:
        try:
            all_cards()
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    for path in sorted(GEOMETRY.glob("*.geojson")):
        errors += provenance_errors(path.name, json.loads(path.read_text()))
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
    political_errors, outlines = political.check()  # no-ops until the political data files exist
    errors += political_errors + cities.check(outlines)
    retired_errors, retired_notes = retired_references(all_features)
    errors += retired_errors
    notes += retired_notes
    all_pairs = find_pairs(clean)
    pairs = [p for p in all_pairs if p.flagged or p.nested]
    errors += [f"{p.a} ~ {p.b}: highlights too alike (IoU {p.iou:.2f}, cover {p.cover:.2f})" for p in pairs if p.flagged]
    if not errors:
        siblings = Siblings(
            # continents are never paired, so their area would only make siblings depend on the political data
            area_km2={i: area_km2(g) for i, (f, g) in clean.items() if f.family not in UNCOMPARED_FAMILIES},
            close=[(p.a, p.b) for p in all_pairs],
            nested=[(p.b if p.inner == p.a else p.a, p.inner) for p in pairs if p.nested],
        )
        try:
            ordered(features, siblings)
            save_siblings(siblings)
        except ValueError as exc:
            errors.append(f"study order: {exc}")
    errors += lock_freeze_errors(release)
    errors += verify_errors(release)  # last, so that nothing it finds holds back the checks above
    notes.append(f"sibling pairs flagged or nested (within {NEAR_M // 1000} km or overlapping; `make pairs` lists all):")
    return errors, notes + [f"  {p}" for p in pairs]


def lock_freeze_errors(release: bool) -> list[str]:
    """The freeze guard (ADR 0006): a frozen lock only adds to the frozen locks on the base ref and the newest
    release tag. A release build must be able to read the base ref; any other build without it (a source archive)
    only warns."""
    try:
        lock = positions.read()
    except (SystemExit, ValueError) as exc:
        return [str(exc)]
    errors, warnings = positions.guard(lock, strict=release)
    for warning in warnings:
        print(f"warning: {warning}")
    return errors


def retired_lock_errors(lock: positions.Lock, active: set[str], entries: list[dict]) -> list[str]:
    """A frozen lock keeps retired uids (ADR 0006), so every locked uid must belong to a source entry, active or
    marked `retired: true`: deleting a retired entry would hide its uid from the duplicate-uid check."""
    known = {u for e in entries for u in entry_uids(e)}
    retired = {u for e in entries if e.get("retired") for u in entry_uids(e)}
    errors = []
    if orphans := sorted(set(lock.entries) - known):
        errors.append(f"{positions.LOCK_FILE.name} holds uids no source entry has (keep a retired entry): {orphans}")
    if loose := sorted(set(lock.entries) & (known - active - retired)):
        errors.append(f"{positions.LOCK_FILE.name} holds inactive uids whose entries aren't `retired: true`: {loose}")
    return errors


def ankc_supported() -> str | None:
    """An error unless the configured ankc is 0.5.x or 0.6.x: both keep `::` in footnote tags and number new cards
    in source order; 0.6 also reads `[^pos]`."""
    version = ankc_version()
    if version is None or not (0, 5) <= version < (0, 7):
        return f"`{' '.join(ankc_command())} --version` says {ankc_version_text()!r}; >=0.5,<0.7 required"
    return None


def check_deck() -> list[str]:
    errors = []
    media = load_media()
    cards = all_cards()
    for c in cards:
        if c.key not in media or not (DECK / media[c.key]).exists():
            errors.append(f"{c.key}: not rendered (run `make render`)")
    lock = positions.read()
    if missing := sorted(c.uid for c in cards if c.uid not in lock.positions):
        errors.append(f"uids not in {positions.LOCK_FILE.name} (run `make positions`): {missing}")
    entries = [e for path in PATHS for e in (YAML(typ="safe").load(path) or [])]
    errors += retired_lock_errors(lock, {c.uid for c in cards}, entries)
    if error := ankc_supported():
        return errors + [error]
    if error := positions.lock_error(lock):
        errors.append(error)
    if not lock.draft and not writes_pos():
        errors.append(f"{positions.LOCK_FILE.name} is frozen (draft: false), so ankc 0.6+ is required to write it")
    command = [*ankc_command(), "check", "--deck", ROOT_DECK, "--path", str(DECK)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        errors.append(f"ankc check failed:\n{result.stdout}{result.stderr}")
    return errors


def check_package() -> list[str]:
    packages = list((ROOT / "dist").glob("*.apkg"))
    if len(packages) != 1:
        return [f"expected exactly one package in dist/, found {len(packages)}"]
    cards = ideal_order()
    expected = {c.uid for c in all_cards()}
    with zipfile.ZipFile(packages[0]) as archive, tempfile.TemporaryDirectory() as tmp:
        archive.extract("collection.anki2", tmp)
        packaged_media = set(json.loads(archive.read("media")).values())
        db = sqlite3.connect(Path(tmp) / "collection.anki2")
        decks = json.loads(db.execute("select decks from col").fetchone()[0])
        rows = db.execute("select n.guid, n.tags, c.did, c.type, c.queue, c.due from notes n join cards c on c.nid = n.id").fetchall()
        db.close()
    note_tags = {guid: set(tags.split()) for guid, tags, *_ in rows}
    guids = set(note_tags)
    name = packages[0].name
    lock = positions.read()
    errors = [f"{name}: note {c.uid} ({c.key}) lacks tags {sorted(missing)}" for c in cards if c.uid in note_tags
              and (missing := set(positions.locked_tags(c.tags, lock.entries.get(c.uid))) - note_tags[c.uid])]
    if wrong := sorted({decks[str(did)]["name"] for _, _, did, *_ in rows} - {ROOT_DECK}):
        errors.append(f"{name}: cards outside the {ROOT_DECK!r} deck: {wrong}")
    if any((ctype, queue) != (0, 0) for *_, ctype, queue, _ in rows):
        errors.append(f"{name}: some cards aren't new")
    media = load_media()
    if odd := packaged_media ^ {media.get(c.key) for c in cards}:  # nothing a card's text pulled in from elsewhere
        errors.append(f"{name}: packaged media differ from the rendered maps: {sorted(map(str, odd))}")
    for guid, tags, *_ in rows:  # the tags filtered decks search must name the block and region the lock placed it in
        if (entry := lock.entries.get(guid)) is None:
            continue
        placed = {t for t in tags.split() if t.startswith(("block::", "pass::", "region::"))}
        if f"block::{entry.block}" not in placed or placed - set(positions.locked_tags(list(placed), entry)):
            errors.append(f"{name}: note {guid}'s tags {sorted(placed)} differ from its lock entry {entry}")
    if writes_pos() or not lock.draft:
        if wrong := sorted(g for g, *_, due in rows if g in expected and due != lock.positions.get(g)):
            errors.append(f"{name}: new-card positions differ from {positions.LOCK_FILE.name} for {wrong}")
    else:
        due = sorted((d, guid) for guid, *_, d in rows)
        if [guid for _, guid in due] != [c.uid for c in cards] or len({d for d, _ in due}) != len(due):
            errors.append(f"{name}: new-card positions don't follow the study order")
    if missing := expected - guids:
        errors.append(f"{name}: missing notes for uids {sorted(missing)}")
    if extra := guids - expected:
        errors.append(f"{name}: unexpected note guids {sorted(extra)}")
    return errors


def main() -> None:
    stage, *flags = sys.argv[1:] or [""]
    if stage not in ("data", "deck", "package", "verify-report") or flags not in ([], ["--release"]) \
            or (flags and stage != "data"):
        sys.exit("usage: python -m geofeat.check data [--release] | deck | package | verify-report")
    if stage == "verify-report":
        print(verify_report(noted()))
        return
    if stage == "data":
        errors, notes = check_data(release=flags == ["--release"])
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
