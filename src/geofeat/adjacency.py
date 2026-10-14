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

from geofeat import countries_ne, ne
from geofeat.countries_ne import outlines, parts, state_ids
from geofeat.curriculum import Region, load_curriculum
from geofeat.model import BUILD, LOCK, ROOT

OVERRIDES = ROOT / "data/adjacency.yaml"
CACHE = BUILD / "adjacency.json"

LAND_KM = 1.0  # outlines this close touch: the 1 km buffer absorbs 10m slivers
SEA_KM = 200.0  # outlines closer than this across water get a sea edge
KM_PER_DEG = 111.32


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
    return state_ids()


def outline_specs() -> dict[str, list[dict]]:
    """Each state's geometry parts from data/countries.yaml. The cache key hashes these, not the whole file, so editing
    a note or a capital doesn't recompute the graph."""
    return {i: [p.model_dump(exclude_defaults=True) for p in parts(i)] for i in state_ids()}


def geometry_key() -> str:
    """Hash of everything the computed edges depend on: the states' geometry parts, this module's code and thresholds, the NE
    reader, the pinned layers' lock (which pins each file's sha256; `make fetch` verifies it), and the geometry
    libraries' versions."""
    versions = f"shapely {shapely.__version__} geos {shapely.geos_version_string} pyproj {pyproj.__version__} " \
               f"proj {pyproj.proj_version_str}"
    specs = json.dumps(outline_specs(), sort_keys=True)
    return _hash([Path(__file__), Path(countries_ne.__file__), Path(ne.__file__), LOCK], f"{versions}\0{specs}")


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
    lines, ok = report(ids, computed, edges, load_curriculum(state_ids()).regions)
    print("\n".join(lines))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
