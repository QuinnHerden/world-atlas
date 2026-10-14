"""The country adjacency graph (ADR 0008): which of the 197 states touch by land or lie within 200 km across water,
plus the hand edits in data/adjacency.yaml. Computed from the recognised-border outlines and cached in
build/adjacency.json, keyed by a hash of its inputs. `python -m geofeat.adjacency` prints the report."""

import hashlib
import json
import math
import os
import sys
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from functools import cache
from pathlib import Path
from typing import Literal

import numpy as np
import pyproj
import shapely
from pydantic import BaseModel, ConfigDict, Field
from pyproj import Transformer
from ruamel.yaml import YAML
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points
from shapely.strtree import STRtree

from geofeat import ne
from geofeat.model import BUILD, LOCK, ROOT

CURRICULUM = ROOT / "data/curriculum.yaml"
OVERRIDES = ROOT / "data/adjacency.yaml"
CACHE = BUILD / "adjacency.json"

LAND_KM = 1.0  # outlines this close touch: the 1 km buffer absorbs 10m slivers
SEA_KM = 200.0  # outlines closer than this across water get a sea edge
KM_PER_DEG = 111.32

LAYERS = {"A0": "10m_admin_0_countries", "MU": "10m_admin_0_map_units", "DA": "10m_admin_0_disputed_areas"}

# Each state's recognised-border outline, from docs/research/ne-political-layers.md (a) and (c): a base row, then rows
# added (+) or cut out (-). Beyond the research table, the brief's defaults are applied: Shebaa Farms goes to Syria with
# the Golan, and East Jerusalem, both no-man's-land strips and Mount Scopus go to Palestine. P2.2's countries.yaml
# replaces this table; `outline(country_id)` keeps the same interface.
SOURCES: dict[str, str] = {
    "afghanistan": "A0 1159320319",
    "albania": "A0 1159320325",
    "algeria": "A0 1159320565",
    "andorra": "A0 1159320327",
    "angola": "A0 1159320323",
    "antigua-and-barbuda": "A0 1159320345",
    "argentina": "A0 1159320331",
    "armenia": "A0 1159320333",
    "australia": "A0 1159320355",
    "austria": "A0 1159320379",
    "azerbaijan": "A0 1159320381",
    "bahamas": "A0 1159320415",
    "bahrain": "A0 1159320413",
    "bangladesh": "A0 1159320407",
    "barbados": "A0 1159320449",
    "belarus": "A0 1159320427",
    "belgium": "A0 1159320389",
    "belize": "A0 1159320431",
    "benin": "A0 1159320399",
    "bhutan": "A0 1159320453",
    "bolivia": "A0 1159320439",
    "bosnia-and-herzegovina": "A0 1159320417",
    "botswana": "A0 1159320461",
    "brazil": "A0 1159320441",
    "brunei": "A0 1159320451",
    "bulgaria": "A0 1159320409",
    "burkina-faso": "A0 1159320405",
    "burundi": "A0 1159320387",
    "cambodia": "A0 1159320979",
    "cameroon": "A0 1159320509",
    "canada": "A0 1159320467",
    "central-african-republic": "A0 1159320463",
    "chad": "A0 1159321301",
    "chile": "A0 1159320493",
    "china": "A0 1159320471",
    "colombia": "A0 1159320517",
    "comoros": "A0 1159320521",
    "costa-rica": "A0 1159320525",
    "croatia": "A0 1159320833",
    "cuba": "A0 1159320527 + A0 1159320529",
    "cyprus": "A0 1159320533 + A0 1159320531 + A0 1159320511",
    "czechia": "A0 1159320535",
    "cote-divoire": "A0 1159320507",
    "north-korea": "A0 1159321181",
    "dr-congo": "A0 1159320513",
    "denmark": "A0 1159320547",
    "djibouti": "A0 1159320541",
    "dominica": "A0 1159320543",
    "dominican-republic": "A0 1159320563",
    "ecuador": "A0 1159320567",
    "egypt": "A0 1159320575",
    "el-salvador": "A0 1159321253",
    "equatorial-guinea": "A0 1159320801",
    "eritrea": "A0 1159320581",
    "estonia": "A0 1159320615",
    "ethiopia": "A0 1159320617",
    "micronesia": "A0 1159320691",
    "fiji": "A0 1159320625",
    "finland": "A0 1159320623",
    "france": "MU 1159320651",
    "gabon": "A0 1159320693",
    "georgia": "A0 1159320779",
    "germany": "A0 1159320539",
    "ghana": "A0 1159320793",
    "greece": "A0 1159320811",
    "grenada": "A0 1159320813",
    "guatemala": "A0 1159320815",
    "guinea": "A0 1159320795",
    "guinea-bissau": "A0 1159320799",
    "guyana": "A0 1159320817",
    "haiti": "A0 1159320839",
    "honduras": "A0 1159320827",
    "hungary": "A0 1159320841",
    "iceland": "A0 1159320917",
    "india": "A0 1159320847 + A0 1159320963",
    "indonesia": "A0 1159320845",
    "iran": "A0 1159320881",
    "iraq": "A0 1159320887",
    "ireland": "A0 1159320877",
    "israel": "A0 1159320895 - DA 1159320905 - DA 1159320907 - DA 1746265961 - DA 1159320911 - DA 1159320909 - DA 1746265963",
    "italy": "A0 1159320919",
    "jamaica": "A0 1159320931",
    "japan": "A0 1159320937",
    "jordan": "A0 1159320935",
    "kazakhstan": "A0 1159320967 + A0 1159320965",
    "kenya": "A0 1159320971",
    "eswatini": "A0 1159321289",
    "kiribati": "A0 1159320981",
    "kosovo": "A0 1159321007",
    "kuwait": "A0 1159321009",
    "kyrgyzstan": "A0 1159320977",
    "laos": "A0 1159321011",
    "latvia": "A0 1159321033",
    "lebanon": "A0 1159321013",
    "lesotho": "A0 1159321027",
    "liberia": "A0 1159321015",
    "libya": "A0 1159321017",
    "liechtenstein": "A0 1159321021",
    "lithuania": "A0 1159321029",
    "luxembourg": "A0 1159321031",
    "madagascar": "A0 1159321051",
    "malawi": "A0 1159321081",
    "malaysia": "A0 1159321083",
    "maldives": "A0 1159321053",
    "mali": "A0 1159321063",
    "malta": "A0 1159321065",
    "marshall-islands": "A0 1159321057",
    "mauritania": "A0 1159321075",
    "mauritius": "A0 1159321079",
    "mexico": "A0 1159321055",
    "moldova": "A0 1159321045",
    "monaco": "A0 1159321043",
    "mongolia": "A0 1159321071",
    "montenegro": "A0 1159321069",
    "morocco": "A0 1159321035 - DA 1159321037",
    "mozambique": "A0 1159321073",
    "myanmar": "A0 1159321067",
    "namibia": "A0 1159321085",
    "nauru": "A0 1159321123",
    "nepal": "A0 1159321121",
    "netherlands": "MU 1159321105",
    "new-zealand": "MU 1159321135",
    "nicaragua": "A0 1159321091",
    "niger": "A0 1159321087",
    "nigeria": "A0 1159321089",
    "north-macedonia": "A0 1159321061",
    "norway": "MU 1159321117",
    "oman": "A0 1159321151",
    "pakistan": "A0 1159321153",
    "palau": "A0 1159321171",
    "palestine": "A0 1159320899 + DA 1746265961 + DA 1159320911 + DA 1159320909 + DA 1746265963",
    "panama": "A0 1159321161",
    "papua-new-guinea": "A0 1159321173",
    "paraguay": "A0 1159321195",
    "peru": "A0 1159321163",
    "philippines": "A0 1159321169",
    "poland": "A0 1159321179",
    "portugal": "A0 1159321187",
    "qatar": "A0 1159321197",
    "cabo-verde": "A0 1159320523",
    "south-korea": "A0 1159320985",
    "congo": "A0 1159320515",
    "romania": "A0 1159321199",
    "russia": "A0 1159321201 - DA 1159321217",
    "rwanda": "A0 1159321219",
    "saint-kitts-and-nevis": "A0 1159320983",
    "saint-lucia": "A0 1159321019",
    "saint-vincent-and-the-grenadines": "A0 1159321409",
    "samoa": "A0 1159321423",
    "san-marino": "A0 1159321255",
    "saudi-arabia": "A0 1159321225",
    "senegal": "A0 1159321243",
    "serbia": "A0 1159321267",
    "seychelles": "A0 1159321291",
    "sierra-leone": "A0 1159321251",
    "singapore": "A0 1159321247",
    "slovakia": "A0 1159321283",
    "slovenia": "A0 1159321285",
    "solomon-islands": "A0 1159321249",
    "somalia": "A0 1159321261 + A0 1159321259",
    "south-africa": "A0 1159321431",
    "south-sudan": "A0 1159321235",
    "spain": "A0 1159320587",
    "sri-lanka": "A0 1159321025",
    "sudan": "A0 1159321229",
    "suriname": "A0 1159321281",
    "sweden": "A0 1159321287",
    "switzerland": "A0 1159320491",
    "syria": "A0 1159321295 + DA 1159320905 + DA 1159320907",
    "sao-tome-and-principe": "A0 1159321273",
    "taiwan": "A0 1159321335",
    "tajikistan": "A0 1159321307",
    "tanzania": "A0 1159321337",
    "thailand": "A0 1159321305",
    "gambia": "A0 1159320797",
    "timor-leste": "A0 1159321313",
    "togo": "A0 1159321303",
    "tonga": "A0 1159321319",
    "trinidad-and-tobago": "A0 1159321321",
    "tunisia": "A0 1159321327",
    "turkey": "A0 1159321331",
    "turkmenistan": "A0 1159321309",
    "tuvalu": "A0 1159321333",
    "uganda": "A0 1159321343",
    "ukraine": "A0 1159321345 + DA 1159321217",
    "united-arab-emirates": "A0 1159320329",
    "united-kingdom": "A0 1159320713",
    "united-states": "A0 1159321369",
    "uruguay": "A0 1159321353",
    "uzbekistan": "A0 1159321405",
    "vanuatu": "A0 1159321421",
    "vatican": "A0 1159321407",
    "venezuela": "A0 1159321411",
    "vietnam": "A0 1159321417",
    "yemen": "A0 1159321425",
    "zambia": "A0 1159321439",
    "zimbabwe": "A0 1159321441",
}

Kind = Literal["land", "sea", "override"]


@dataclass(frozen=True)
class Edge:
    a: str
    b: str
    kind: Kind
    km: float | None = None
    reason: str | None = None

    @property
    def pair(self) -> tuple[str, str]:
        return self.a, self.b


def pair(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


# Outlines


def _parse(source: str) -> tuple[tuple[str, int], list[tuple[str, int]], list[tuple[str, int]]]:
    tokens = source.split()
    if len(tokens) % 3 != 2 or any(op not in "+-" for op in tokens[2::3]):
        raise ValueError(f"bad outline recipe {source!r}")
    base = (tokens[0], int(tokens[1]))
    plus, minus = [], []
    for op, layer, nid in zip(tokens[2::3], tokens[3::3], tokens[4::3]):
        (plus if op == "+" else minus).append((layer, int(nid)))
    return base, plus, minus


@cache
def _row(layer: str, nid: int) -> BaseGeometry:
    rows = ne.layer(LAYERS[layer])
    match = rows[rows["ne_id"] == nid]
    if len(match) != 1:
        raise ValueError(f"{layer} {nid}: {len(match)} rows")
    return shapely.make_valid(match.geometry.iloc[0])


def outline(country_id: str) -> BaseGeometry:
    """A state's recognised-border outline, composed from its Natural Earth rows."""
    base, plus, minus = _parse(SOURCES[country_id])
    geometry = shapely.union_all([_row(*base), *(_row(*r) for r in plus)])
    if minus:
        geometry = geometry.difference(shapely.union_all([_row(*r) for r in minus]))
    return geometry


def outlines() -> dict[str, BaseGeometry]:
    return {i: outline(i) for i in sorted(SOURCES)}


# Edges


def _copies(geometry: BaseGeometry) -> list[BaseGeometry]:
    """The geometry, plus a copy shifted by 360° when it comes within SEA_KM of the antimeridian (a margin measured at
    its highest latitude), so pairs across ±180° are found."""
    box = _search_box(geometry, SEA_KM).bounds
    copies = [geometry]
    if box[0] < -180.0:
        copies.append(shapely.transform(geometry, lambda c: c + [360.0, 0.0]))
    if box[2] > 180.0:
        copies.append(shapely.transform(geometry, lambda c: c - [360.0, 0.0]))
    return copies


def _search_box(geometry: BaseGeometry, km: float) -> BaseGeometry:
    minx, miny, maxx, maxy = geometry.bounds
    dlat = km / KM_PER_DEG
    dlon = min(dlat / math.cos(math.radians(min(85.0, max(abs(miny), abs(maxy)) + dlat))), 360.0)
    return shapely.box(minx - dlon, miny - dlat, maxx + dlon, maxy + dlat)


def _sinusoidal_nearest(a: BaseGeometry, b: BaseGeometry, lon0: float) -> tuple[Point, Point]:
    """The nearest points in a sinusoidal frame, where a degree of longitude shrinks with latitude as it does on the
    ground; degrees alone miss close pairs at high latitude."""
    def fwd(c: np.ndarray) -> np.ndarray:
        return np.column_stack([(c[:, 0] - lon0) * np.cos(np.radians(c[:, 1])), c[:, 1]])

    qa, qb = nearest_points(shapely.transform(a, fwd), shapely.transform(b, fwd))
    return tuple(Point(q.x / math.cos(math.radians(q.y)) + lon0, q.y) for q in (qa, qb))


def _lower_bound_km(a: BaseGeometry, b: BaseGeometry) -> float:
    """A cheap lower bound on distance_km: degrees of longitude shrunk to their length at the pair's highest latitude,
    and a degree of latitude at its shortest (110.5 km), so the true distance can't be smaller."""
    lat = max(abs(a.bounds[1]), abs(a.bounds[3]), abs(b.bounds[1]), abs(b.bounds[3]))
    scale = np.array([math.cos(math.radians(min(lat, 90.0))), 1.0])
    return shapely.distance(shapely.transform(a, lambda c: c * scale), shapely.transform(b, lambda c: c * scale)) * 110.5


def distance_km(a: BaseGeometry, b: BaseGeometry) -> float:
    """Shortest distance between two lon/lat geometries. Two first guesses at the nearest pair (in degrees, and in a
    sinusoidal frame) are each refined in an equidistant projection centred between them, re-centred on the projected
    nearest pair until it settles; the smallest distance wins."""
    if a.intersects(b):
        return 0.0
    pa, pb = nearest_points(a, b)
    best = math.inf
    for ga, gb in ((pa, pb), _sinusoidal_nearest(a, b, (pa.x + pb.x) / 2)):
        lon, lat = (ga.x + gb.x) / 2, (ga.y + gb.y) / 2
        half_km = 2 * SEA_KM + ne.GEOD.inv(ga.x, ga.y, gb.x, gb.y)[2] / 1000
        for _ in range(4):
            project = Transformer.from_crs("EPSG:4326", f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84",
                                           always_xy=True)
            dlat = half_km / KM_PER_DEG
            dlon = min(dlat / math.cos(math.radians(min(85.0, abs(lat) + dlat))), 180.0)
            window = (lon - dlon, lat - dlat, lon + dlon, lat + dlat)
            la, lb = (shapely.transform(shapely.clip_by_rect(g, *window),
                                        lambda c: np.column_stack(project.transform(c[:, 0], c[:, 1])))
                      for g in (a, b))
            if la.is_empty or lb.is_empty:
                break
            best = min(best, shapely.distance(la, lb) / 1000)
            qa, qb = nearest_points(la, lb)
            new_lon, new_lat = project.transform((qa.x + qb.x) / 2, (qa.y + qb.y) / 2, direction="INVERSE")
            if ne.GEOD.inv(lon, lat, new_lon, new_lat)[2] < 1000:
                break
            lon, lat = new_lon, new_lat
    return best


def compute_edges(geometries: dict[str, BaseGeometry]) -> list[Edge]:
    """Land edges (within LAND_KM) and sea edges (within SEA_KM) between every pair of geometries."""
    items = [(i, g) for i in sorted(geometries) for g in _copies(geometries[i])]
    tree = STRtree([g for _, g in items])
    best: dict[tuple[str, str], float] = {}
    for a, ga in items:
        for j in sorted(tree.query(_search_box(ga, SEA_KM))):
            b, gb = items[j]
            if a >= b or _lower_bound_km(ga, gb) > SEA_KM:
                continue
            km = distance_km(ga, gb)
            if km < best.get((a, b), math.inf):
                best[(a, b)] = km
    return [Edge(a, b, "land" if km <= LAND_KM else "sea", round(float(km), 1))
            for (a, b), km in sorted(best.items()) if km < SEA_KM]


# Hand edits


class Override(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    a: str
    b: str
    reason: str = Field(min_length=1)


class Overrides(BaseModel):
    model_config = ConfigDict(extra="forbid")
    add: list[Override] = []
    remove: list[Override] = []


def load_overrides(path: Path = OVERRIDES) -> Overrides:
    return Overrides.model_validate(YAML(typ="safe").load(path) or {})


def apply_overrides(edges: list[Edge], overrides: Overrides, ids: Iterable[str],
                    km: dict[tuple[str, str], float | None] | None = None) -> list[Edge]:
    """The computed edges with the hand edits applied; `km` gives each added edge's measured length. An edit naming an unknown id, a self-loop, an edge already
    present (add) or absent (remove), or the same pair twice is an error, so a stale edit can't linger."""
    known = set(ids)
    by_pair = {e.pair: e for e in edges}
    errors, seen = [], set()
    for op, entries in (("add", overrides.add), ("remove", overrides.remove)):
        for o in entries:
            p = pair(o.a, o.b)
            if unknown := [i for i in p if i not in known]:
                errors.append(f"{op} {o.a}–{o.b}: unknown id {', '.join(unknown)}")
            elif o.a == o.b:
                errors.append(f"{op} {o.a}–{o.b}: an edge needs two countries")
            elif p in seen:
                errors.append(f"{op} {o.a}–{o.b}: listed twice")
            elif op == "add" and p in by_pair:
                errors.append(f"add {o.a}–{o.b}: already a {by_pair[p].kind} edge ({by_pair[p].km} km)")
            elif op == "remove" and p not in by_pair:
                errors.append(f"remove {o.a}–{o.b}: no such edge")
            seen.add(p)
    if errors:
        raise ValueError("adjacency.yaml: " + "; ".join(errors))
    for o in overrides.remove:
        del by_pair[pair(o.a, o.b)]
    for o in overrides.add:
        a, b = pair(o.a, o.b)
        by_pair[(a, b)] = Edge(a, b, "override", (km or {}).get((a, b)), o.reason)
    return [by_pair[p] for p in sorted(by_pair)]


# Cache


def _hash(paths: Iterable[Path], extra: str = "") -> str:
    h = hashlib.sha256(extra.encode())
    for path in paths:
        data = path.read_bytes()
        h.update(f"{path.name}\0{len(data)}\0".encode() + data)
    return h.hexdigest()


def country_ids() -> list[str]:
    return sorted(SOURCES)


def outline_specs() -> dict[str, str]:
    """Each state's outline recipe. P2.2's countries.yaml replaces this and `country_ids`; the cache key hashes the
    recipes themselves, so it stays honest once they move out of this file."""
    return dict(SOURCES)


def geometry_key() -> str:
    """Hash of everything the computed edges depend on: the outline recipes, this module's code and thresholds, the NE
    reader, the pinned layers' lock (which pins each file's sha256; `make fetch` verifies it), and the geometry
    libraries' versions."""
    versions = f"shapely {shapely.__version__} geos {shapely.geos_version_string} pyproj {pyproj.__version__} " \
               f"proj {pyproj.proj_version_str}"
    specs = json.dumps(outline_specs(), sort_keys=True)
    return _hash([Path(__file__), Path(ne.__file__), LOCK], f"{versions}\0{specs}")


def _read(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def _measure(geometries: dict[str, BaseGeometry], a: str, b: str) -> float | None:
    km = min(distance_km(ga, geometries[b]) for ga in _copies(geometries[a]))
    return round(float(km), 1) if math.isfinite(km) else None


def build_graph(geometries: Callable[[], dict[str, BaseGeometry]], ids: Iterable[str], key: str,
                overrides_path: Path = OVERRIDES, cache_path: Path = CACHE) -> tuple[list[Edge], list[Edge]]:
    """(computed, final) edges. The computed edges, and the measured length of each added edge, are reused from the
    cache while `key` matches; the hand edits are re-applied on every call, so the cached final edges are output for
    other readers, never input."""
    ids = sorted(ids)
    overrides = load_overrides(overrides_path)
    data = _read(cache_path)
    fresh = data.get("geometry") == key
    computed = [Edge(**e) for e in data["computed"]] if fresh else None
    measured = {pair(*k.split("|")): v for k, v in data.get("override_km", {}).items()} if fresh else {}
    g = None
    if computed is None:
        g = geometries()
        computed = compute_edges(g)
    known, present = set(ids), {e.pair for e in computed}
    missing = [p for o in overrides.add
               if (p := pair(o.a, o.b)) not in measured and p not in present and set(p) <= known and p[0] != p[1]]
    if missing:
        g = g or geometries()
        measured |= {p: _measure(g, *p) for p in missing}
    edges = apply_overrides(computed, overrides, ids, measured)
    _write(cache_path, {"geometry": key, "computed": [asdict(e) for e in computed],
                        "override_km": {f"{a}|{b}": km for (a, b), km in sorted(measured.items())},
                        "edges": [asdict(e) for e in edges]})
    return computed, edges


def graph() -> list[Edge]:
    """The final adjacency edges for the 197 states."""
    return build_graph(outlines, country_ids(), geometry_key())[1]


# Curriculum. A runtime check of the parts of data/curriculum.yaml this module and P3 rely on; P3 can move it into its
# own module.


class Placement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    region: str
    host: str


class Ambiguous(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card: str
    default: Placement
    alternative: Placement
    reason: str = Field(min_length=1)


class Pass(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    ring: bool
    kinds: list[Literal["feature", "continent", "country", "capital", "territory", "dispute", "city"]]
    feature_tiers: list[int] = []
    city_tiers: list[Literal["core", "secondary"]] = []
    global_features: bool = False


class Region(BaseModel):
    model_config = ConfigDict(extra="forbid")
    number: int
    slug: str
    name: str
    entry: str
    exit: str
    way_in: str = ""
    countries: list[str]
    pockets: dict[str, str] = {}
    territories: dict[str, str] = {}
    disputes: dict[str, str] = {}

    def placed(self) -> dict[str, str]:
        return self.territories | self.disputes


class Curriculum(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passes: list[Pass]
    start: str
    regions: list[Region]
    ambiguous: list[Ambiguous] = []
    confusables: list[list[str]]

    def check(self, states: Iterable[str]) -> list[str]:
        """Errors: every state in exactly one region, regions numbered in ring order, entry and exit walk nodes, hosts
        walk nodes of the region, ambiguous cards at their default, confusables naming known cards."""
        errors = []
        states = set(states)
        slugs = [r.slug for r in self.regions]
        if [r.number for r in self.regions] != list(range(1, len(self.regions) + 1)):
            errors.append("regions must be numbered 1..n in ring order")
        if len(set(slugs)) != len(slugs) or self.start not in slugs:
            errors.append("region slugs must be unique and `start` one of them")
        members = [c for r in self.regions for c in r.countries]
        if dupes := sorted({c for c in members if members.count(c) > 1}):
            errors.append(f"in more than one region: {', '.join(dupes)}")
        if extra := sorted(set(members) - states):
            errors.append(f"unknown states: {', '.join(extra)}")
        if unplaced := sorted(states - set(members)):
            errors.append(f"states in no region: {', '.join(unplaced)}")
        cards = [c for r in self.regions for c in r.placed()]
        if dupes := sorted({c for c in cards if cards.count(c) > 1} | (set(cards) & states)):
            errors.append(f"territory or dispute placed twice or clashing with a state: {', '.join(dupes)}")
        for r in self.regions:
            walk = set(r.countries) - set(r.pockets)
            for role, c in (("entry", r.entry), ("exit", r.exit)):
                if c not in walk:
                    errors.append(f"{r.slug}: {role} {c} is not a walk node (a member and not a pocket)")
            for card, host in r.pockets.items() | r.placed().items():
                if card in r.pockets and card not in r.countries:
                    errors.append(f"{r.slug}: pocket {card} is not a member")
                if host not in walk:
                    errors.append(f"{r.slug}: {card}'s host {host} is not a walk node")
        by_slug = {r.slug: r for r in self.regions}
        for a in self.ambiguous:
            for label, p in (("default", a.default), ("alternative", a.alternative)):
                region = by_slug.get(p.region)
                if region is None or p.host not in set(region.countries) - set(region.pockets):
                    errors.append(f"ambiguous {a.card}: {label} host {p.host} is not a walk node of {p.region}")
            if by_slug.get(a.default.region) and by_slug[a.default.region].placed().get(a.card) != a.default.host:
                errors.append(f"ambiguous {a.card}: not placed at its default")
        for group in self.confusables:
            if len(group) < 2 or not set(group) <= states | set(cards):
                errors.append(f"confusables {group}: needs two or more known cards")
        return errors


def load_curriculum(path: Path = CURRICULUM, states: Iterable[str] | None = None) -> Curriculum:
    curriculum = Curriculum.model_validate(YAML(typ="safe").load(path))
    if errors := curriculum.check(country_ids() if states is None else states):
        raise ValueError(f"{path.name}: " + "; ".join(errors))
    return curriculum


# The report


def neighbours(edges: Iterable[Edge]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for e in edges:
        out.setdefault(e.a, set()).add(e.b)
        out.setdefault(e.b, set()).add(e.a)
    return out


def components(members: Iterable[str], edges: Iterable[Edge]) -> list[list[str]]:
    """The connected components of the subgraph induced on `members`, largest first, then by first id."""
    members = set(members)
    adj = neighbours(e for e in edges if e.a in members and e.b in members)
    left, out = set(members), []
    while left:
        stack, comp = [min(left)], set()
        while stack:
            node = stack.pop()
            if node not in comp:
                comp.add(node)
                stack.extend(adj.get(node, set()) - comp)
        left -= comp
        out.append(sorted(comp))
    return sorted(out, key=lambda c: (-len(c), c[0]))


def isolated(ids: Iterable[str], edges: Iterable[Edge]) -> list[str]:
    adj = neighbours(edges)
    return sorted(i for i in ids if not adj.get(i))


def _fmt(e: Edge) -> str:
    return f"{e.a}–{e.b} ({e.kind}, {e.km} km)" + (f": {e.reason}" if e.reason else "")


def report(ids: list[str], computed: list[Edge], edges: list[Edge], regions: list[Region]) -> tuple[list[str], bool]:
    """The report lines, and whether the graph passes: no isolated state and every region connected. Seams without an
    edge are listed, not failed: the ring has open-water crossings by design."""
    ok = True
    lines = [f"{len(ids)} states, {len(edges)} edges: "
             + ", ".join(f"{sum(e.kind == k for e in edges)} {k}" for k in ("land", "sea", "override"))]
    before, after = isolated(ids, computed), isolated(ids, edges)
    lines.append(f"isolated before hand edits ({len(before)}): {', '.join(before) or 'none'}")
    lines.append(f"isolated after hand edits ({len(after)}): {', '.join(after) or 'none'}")
    ok &= not after
    lines.append("hand edits (P3 counts an edge over 200 km as a jump):")
    lines += [f"  {_fmt(e)}" for e in edges if e.kind == "override"]
    lines.append("regions:")
    for r in regions:
        comps = components(r.countries, edges)
        ok &= len(comps) == 1
        status = "connected" if len(comps) == 1 else f"{len(comps)} components: " + " | ".join(map(", ".join, comps))
        lines.append(f"  {r.number:2} {r.name} ({len(r.countries)}): {status}")
    lines.append("ring seams (exit → next entry):")
    for r, nxt in zip(regions, regions[1:] + regions[:1]):
        here, there = set(r.countries), set(nxt.countries)
        cross = [e for e in edges if {e.a, e.b} & here and {e.a, e.b} & there and not {e.a, e.b} <= here
                 and not {e.a, e.b} <= there]
        direct = [e for e in cross if {e.a, e.b} == {r.exit, nxt.entry}]
        seam = f"  {r.number:2}→{nxt.number:<2} {r.exit} → {nxt.entry}: " + (_fmt(direct[0]) if direct else "no direct edge")
        seam += f"; {len(cross)} cross edge(s)"
        if cross and not direct:
            seam += ": " + ", ".join(_fmt(e) for e in cross[:4])
        lines.append(seam)
    return lines, ok


def main() -> None:
    ids = country_ids()
    computed, edges = build_graph(outlines, ids, geometry_key())
    lines, ok = report(ids, computed, edges, load_curriculum().regions)
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
