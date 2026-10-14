"""Seed data/countries.yaml: one entry per state in data/curriculum.yaml, in ring and walk order.

Not part of the build. It was run once to write countries.yaml, which is the source of truth from then on; re-running
it would overwrite hand edits (minted uids are kept), so it refuses to unless given --force. Inputs:

- data/curriculum.yaml: the ids, their order and the pockets (`host`);
- countries_ne.SOURCES: each outline's Natural Earth rows, mirrored into `geometry` parts (tests/test_countries.py
  checks the two agree);
- docs/research/ne-political-layers.md table (a): each capital's populated_places row, with the overrides below;
- the four P2.7 blurb files, given as arguments: the country and capital names and notes, copied as written.

    uv run python tools/seed_countries.py [--force] BLURB.md... && make ids
"""

import io
import math
import re
import sys
import unicodedata
from pathlib import Path

import shapely
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import FoldedScalarString

from geofeat.countries_ne import LAYERS, SOURCES
from geofeat.curriculum import CURRICULUM, Curriculum
from geofeat.model import ROOT
from geofeat.sources.political import COUNTRIES, PLACES, Country, place
from geofeat.resolve import layer

RESEARCH = ROOT / "docs/research/ne-political-layers.md"

# Microstates and small island states only: the 38 states the PoC's ring rule rings (docs/poc-countries.md on
# poc/countries), less Northern Cyprus, which has a dispute card only, and less Kosovo, Palestine and Cyprus (tier 1).
TIER_3 = {
    "andorra", "bahrain", "barbados", "brunei", "cabo-verde", "comoros", "dominica", "grenada",
    "liechtenstein", "luxembourg", "malta", "monaco", "nauru", "saint-lucia", "san-marino", "singapore",
    "sao-tome-and-principe", "saint-kitts-and-nevis", "saint-vincent-and-the-grenadines", "trinidad-and-tobago",
    "vatican",
    "antigua-and-barbuda", "fiji", "kiribati", "maldives", "marshall-islands", "mauritius", "micronesia", "palau",
    "samoa", "seychelles", "tonga", "tuvalu", "vanuatu",
}
NO_CAPITAL = {"monaco", "vatican", "singapore", "san-marino", "luxembourg", "palestine"}
# Official or constitutional seats where NE's Admin-0 capital tag differs.
CAPITAL_ROW = {"benin": 1159150345, "tanzania": 1159149731, "sri-lanka": 1159149593, "burundi": 1159146001}
CAPITAL_FILE = {"nauru": "yaren.geojson"}
CAPITAL_NAME = {"equatorial-guinea": "Malabo"}  # the blurb file's row is for Ciudad de la Paz
ALT_NAMES = {"nauru": ["Naoero"]}
# Blurb text used instead of the row in the file, each with its reason.
NOTE_OVERRIDE = {
    # b-regions-08-13.md, flag 2: the blurb to use if the user keeps Malabo (the brief does).
    ("equatorial-guinea", "capital"): (
        "Malabo, on the island of Bioko in the Bight of Biafra, was Equatorial Guinea's capital until January 2026, "
        "when a decree named Ciudad de la Paz on the mainland as capital. The move of government is still under way "
        "(as of 2026-10, verify)."),
}
# Notes may not contain square brackets (model._UNSAFE_NOTE); an editorial insertion in a quote becomes parentheses.
BRACKETS = str.maketrans("[]", "()")
# Drop remote outliers that carry no card and only widen the frame (lon_min, lat_min, lon_max, lat_max; a box with
# lon_min > lon_max crosses 180°). France, the Netherlands and Norway already use their mainland map unit, and no single
# box can drop the US's Northwestern Hawaiian Islands while keeping the Aleutians; their boxes are a guard only.
MAINLAND = {
    "france": (-5.5, 41.0, 10.0, 51.5),
    "netherlands": (3.0, 50.5, 7.5, 54.0),
    "norway": (4.0, 57.5, 31.5, 71.5),
    "new-zealand": (166.0, -48.0, 179.0, -34.0),  # drops the Kermadecs, the Chathams and the sub-Antarctic islands
    "united-states": (172.0, 18.5, -66.5, 72.0),
    "brazil": (-75.0, -34.0, -32.0, 6.0),  # drops Trindade and Martim Vaz, St Peter and St Paul Rocks (as the PoC did)
    "japan": (122.0, 24.0, 146.0, 46.0),  # drops Minami-Torishima and Okinotorishima (as the PoC did)
    "south-africa": (16.0, -35.5, 33.5, -22.0),  # drops the Prince Edward Islands
    "australia": (112.0, -44.0, 160.0, -9.0),  # drops Macquarie Island
}
NAME_ALIASES = {"The Gambia": "gambia", "Republic of the Congo": "congo", "Democratic Republic of the Congo": "dr-congo"}
POINT_MARGIN = 0.05
WIDTH = 116  # notes fold to features.yaml's line length, at their 4-space indent


def slug(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return NAME_ALIASES.get(name) or re.sub(r"[^a-z0-9]+", "-", ascii_name.lower().replace("'", "")).strip("-")


def read_blurbs(paths: list[Path]) -> dict[tuple[str, str], tuple[str, str]]:
    """(country id, kind) -> (name, blurb). A capital row belongs to the country row before it."""
    out, country = {}, None
    for path in paths:
        for line in path.read_text().splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            if len(cells) != 5 or cells[1] not in ("country", "capital"):
                continue
            _, kind, name, blurb, _ = cells
            if kind == "country":
                country = slug(name)
            if (country, kind) in out:
                raise ValueError(f"{path.name}: second {kind} row for {country}")
            out[country, kind] = (name, blurb)
    return out


def research_capitals() -> dict[int, int | None]:
    """Base outline ne_id -> the capital's populated_places ne_id, from table (a)."""
    out = {}
    for line in RESEARCH.read_text().splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == 7 and cells[0].isdigit():
            base = int(re.search(r"`(\d+)`", cells[3]).group(1))
            out[base] = int(cells[5]) if cells[5].isdigit() else None
    return out


def parts(recipe: str) -> list[dict]:
    tokens = recipe.split()
    out = [{"layer": LAYERS[tokens[0]], "select": {"ne_id": int(tokens[1])}}]
    for op, tag, nid in zip(tokens[2::3], tokens[3::3], tokens[4::3]):
        out.append({"layer": LAYERS[tag], "select": {"ne_id": int(nid)}} | ({"subtract": True} if op == "-" else {}))
    return out


def tight_bbox(geometry) -> tuple[float, float, float, float]:
    """The smallest lon/lat box, crossing 180° when that is smaller, rounded outward to 0.01°."""
    coords = shapely.get_coordinates(geometry)
    lons, lats = sorted(set(coords[:, 0].tolist())), coords[:, 1]
    gaps = [(b - a, a, b) for a, b in zip(lons, lons[1:])] + [(lons[0] + 360 - lons[-1], lons[-1], lons[0])]
    gap, east, west = max(gaps)
    lon_min, lon_max = (west, east) if (east, west) != (lons[-1], lons[0]) else (lons[0], lons[-1])
    down = lambda v, lo: max(lo, math.floor(v * 100) / 100)
    up = lambda v, hi: min(hi, math.ceil(v * 100) / 100)
    return down(lon_min, -180), down(lats.min(), -90), up(lon_max, 180), up(lats.max(), 90)


def folded(text: str, indent: int) -> FoldedScalarString:
    """A `>-` scalar folded at spaces so no line passes WIDTH; it loads back to exactly `text`."""
    out = FoldedScalarString(text)
    out.fold_pos, start = [], 0
    while len(text) - start > WIDTH - indent:
        cut = text.rfind(" ", start, start + WIDTH - indent + 1)
        if cut <= start:
            break
        out.fold_pos.append(cut)
        start = cut + 1
    return out


def flow(values) -> CommentedSeq:
    seq = CommentedSeq(values)
    seq.fa.set_flow_style()
    return seq


def flow_map(values: dict) -> CommentedMap:
    m = CommentedMap(values)
    m.fa.set_flow_style()
    return m


def existing_uids() -> dict[str, dict]:
    if not COUNTRIES.exists():
        return {}
    return {e["id"]: dict(e["uids"]) for e in YAML(typ="safe").load(COUNTRIES) or []}


def entry(country_id: str, host: str | None, blurbs: dict, capitals: dict[int, int | None], uids: dict) -> CommentedMap:
    recipe = SOURCES[country_id]
    geometry = parts(recipe)
    mainland = MAINLAND.get(country_id)
    name, note = blurbs[country_id, "country"]
    e = CommentedMap()
    e["id"] = country_id
    e["name"] = name
    if country_id in ALT_NAMES:
        e["alt_names"] = flow(ALT_NAMES[country_id])
    has_capital = country_id not in NO_CAPITAL
    kept = uids.get(country_id, {})
    e["uids"] = flow_map({k: kept.get(k) for k in (("country", "capital") if has_capital else ("country",))})
    e["tier"] = 3 if country_id in TIER_3 else 1
    if host:
        e["host"] = host
    e["note"] = folded(note.translate(BRACKETS), 4)
    e["geometry"] = [flow_map({k: flow_map(v) if isinstance(v, dict) else v for k, v in p.items()}) for p in geometry]
    if mainland:
        e["mainland"] = flow(mainland)
    # expect: the outline's own tight box, computed with a placeholder that admits everything
    shape = Country.model_validate({**e, "uids": {"country": "x" * 10} | ({"capital": "y" * 10} if has_capital else {}),
                                    "geometry": geometry, "mainland": mainland, "expect": (-180, -90, 180, 90),
                                    "capital": None if not has_capital else {"name": "x", "ne_id": 0, "expect": (0, 0, 0, 0)}}
                                   ).outline()
    e["expect"] = flow(tight_bbox(shape))
    if not has_capital:
        e["capital"] = None
        return e
    capital_name, capital_note = blurbs[country_id, "capital"]
    c = CommentedMap()
    c["name"] = CAPITAL_NAME.get(country_id, capital_name)
    if country_id in CAPITAL_FILE:
        c["file"] = CAPITAL_FILE[country_id]
        point = place(country_id, None, c["file"], (-180, -90, 180, 90))
    else:
        c["ne_id"] = CAPITAL_ROW.get(country_id) or capitals[int(geometry[0]["select"]["ne_id"])]
        point = place(country_id, c["ne_id"], None, (-180, -90, 180, 90))
    c["expect"] = flow([max(-180, round(point.x - POINT_MARGIN, 2)), max(-90, round(point.y - POINT_MARGIN, 2)),
                        min(180, round(point.x + POINT_MARGIN, 2)), min(90, round(point.y + POINT_MARGIN, 2))])
    c["note"] = folded(NOTE_OVERRIDE.get((country_id, "capital"), capital_note).translate(BRACKETS), 6)
    e["capital"] = c
    return e


HEADER = """\
# World Atlas country cards (ADR 0005, 0008): a country card and, unless `capital: null`, a capital card per state.
# Seeded by tools/seed_countries.py; edit here from now on. Region membership is not stored here: it comes from
# data/curriculum.yaml, and every id must be in one of its regions. Entries were seeded in ring and walk order, but
# their order here means nothing: the curriculum holds the order.
#
# - geometry: Natural Earth rows; the first is the base, `subtract` parts are cut out (recognised borders, ADR 0008).
#   Mirrors countries_ne.SOURCES; tests/test_countries.py checks they agree.
# - mainland: keep only the outline's parts wholly inside this box (drops remote outliers that get no card). A display
#   crop for the card only: adjacency and region derivation use the full outline (countries_ne).
# - expect: the outline's bbox (lon_min > lon_max crosses 180°); a capital's is a box around its point.
# - tier 3: microstates and small island states (the PoC's ring rule); host: a pocket's host in curriculum.yaml.
# - note: the P2.7 blurbs, copied as written.
"""


def main() -> None:
    args = sys.argv[1:]
    force = "--force" in args
    if COUNTRIES.exists() and not force:
        sys.exit(f"{COUNTRIES.relative_to(ROOT)} exists and is the source of truth; pass --force to overwrite it")
    blurbs = read_blurbs([Path(p) for p in args if p != "--force"])
    capitals = research_capitals()
    curriculum = Curriculum.model_validate(YAML(typ="safe").load(CURRICULUM))
    ids = [c for r in curriculum.regions for c in r.countries]
    pockets = {p: h for r in curriculum.regions for p, h in r.pockets.items()}
    if missing := [f"{c} {k}" for c in ids for k in ("country", "capital")
                   if (c, k) not in blurbs and not (k == "capital" and c in NO_CAPITAL)]:
        sys.exit(f"missing blurbs: {', '.join(missing)}")
    if extra := sorted({c for c, _ in blurbs} - set(ids)):
        sys.exit(f"blurbs for unknown ids: {extra}")
    layer(PLACES)
    uids = existing_uids()
    entries = [entry(c, pockets.get(c), blurbs, capitals, uids) for c in ids]
    yaml = YAML()
    yaml.width = 4096
    stream = io.StringIO()
    yaml.dump(entries, stream)
    text = HEADER + "\n" + stream.getvalue().replace("\n- id: ", "\n\n- id: ")
    for written, made in zip(YAML(typ="safe").load(text), entries):  # validate, and check the folding round-trips
        Country.model_validate(written)
        notes = [(written["note"], made["note"])] + ([(written["capital"]["note"], made["capital"]["note"])] if made["capital"] else [])
        if any(a != str(b) for a, b in notes):
            sys.exit(f"{made['id']}: a note doesn't load back as written")
    COUNTRIES.write_text(text)
    print(f"wrote {len(entries)} countries to {COUNTRIES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
