"""Each country, territory and dispute card's neighbourhood, which frame.py fits its regional frame to: its land
neighbours; an island's sea neighbours within 200 km; or, for a subject with neither, the nearest recognisable
landmass. Read when jobs are built; the geometries it returns travel in the render job, so they are in its key."""

import math
from functools import cache
from typing import Literal

import numpy as np
import shapely
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from geofeat import adjacency
from geofeat.countries_ne import outlines
from geofeat.frame import centre
from geofeat.ne import GEOD

Framing = Literal["neighbours", "remote"]
Neighbourhood = tuple[Framing, tuple[BaseGeometry, ...]]

WINDOW_KM = 3000  # neighbours are cut to this far round the subject: France's overseas departments don't count
LANDMASS_KM2 = 9000  # a remote subject's frame reaches the nearest land part at least this big (Bougainville, Jamaica)
LANDMASS_VIEW_KM = 400  # and shows this much of it round its nearest point
SIMPLIFY_DEG = 0.01  # ~1 km: under a pixel at any political frame, and it keeps the jobs small in memory


def _window(geometry: BaseGeometry, km: float, clamp: bool = True) -> BaseGeometry:
    x0, y0, x1, y1 = geometry.bounds
    dlat = km / adjacency.KM_PER_DEG
    dlon = min(dlat / math.cos(math.radians(min(80.0, max(abs(y0), abs(y1)) + dlat))), 180.0)
    if not clamp:
        return box(x0 - dlon, y0 - dlat, x1 + dlon, y1 + dlat)
    return box(max(x0 - dlon, -180), max(y0 - dlat, -90), min(x1 + dlon, 180), min(y1 + dlat, 90))


def _windows(subject: BaseGeometry, km: float) -> list[BaseGeometry]:
    """The box `km` round the subject (unwrapped about its centre), cut at ±180° and each piece wrapped back into
    range, so a window across the antimeridian keeps both sides."""
    lon = centre(subject)[0]
    unwrapped = shapely.transform(subject, lambda c: np.column_stack([c[:, 0] - 360 * np.round((c[:, 0] - lon) / 360), c[:, 1]]))
    reach = _window(unwrapped, km, clamp=False)
    world = box(-180, -90, 180, 90)
    return [w for shift in (0.0, 360.0, -360.0)
            if not (w := shapely.transform(reach, lambda c: c + [shift, 0.0]).intersection(world)).is_empty]


def _clip(geometry: BaseGeometry, windows: list[BaseGeometry]) -> BaseGeometry:
    return unary_union([geometry.intersection(w) for w in windows])


def _near(subject: BaseGeometry, geometries: list[BaseGeometry]) -> tuple[BaseGeometry, ...]:
    windows = _windows(subject, WINDOW_KM)
    return tuple(shapely.simplify(c, SIMPLIFY_DEG) for g in geometries if not (c := _clip(g, windows)).is_empty)


@cache
def _graph() -> dict[str, dict[str, str]]:
    """Each state's land and sea neighbours from the cached graph; hand edits (curricular bridges) don't count."""
    out: dict[str, dict[str, str]] = {}
    for e in adjacency.graph():
        if e.kind in ("land", "sea"):
            out.setdefault(e.a, {})[e.b] = e.kind
            out.setdefault(e.b, {})[e.a] = e.kind
    return out


@cache
def _outlines() -> dict[str, BaseGeometry]:
    return outlines()


def _pick(kinds: dict[str, str], subject: BaseGeometry) -> Neighbourhood:
    land = [i for i, k in kinds.items() if k == "land"]
    sea = [i for i, k in kinds.items() if k == "sea"]
    if ids := land or sea:
        return "neighbours", _near(subject, [_outlines()[i] for i in sorted(ids)])
    return "remote", (landmass(subject),)


def country(id: str, subject: BaseGeometry) -> Neighbourhood:
    return _pick(_graph().get(id, {}), subject)


def outline(subject: BaseGeometry) -> Neighbourhood:
    """A territory's or dispute's neighbours, measured as the graph measures states'. A state whose outline holds the
    subject (Ukraine round Crimea) counts by what is left of it, so it is a land neighbour only if that still touches."""
    kinds = {}
    for id, g in _outlines().items():
        if g.intersects(subject):
            g = g.difference(subject.buffer(1e-6))
        if g.is_empty or min(adjacency._lower_bound_km(c, g) for c in adjacency._copies(subject)) > adjacency.SEA_KM:
            continue
        km = min(adjacency.distance_km(c, g) for c in adjacency._copies(subject))
        if km < adjacency.SEA_KM:
            kinds[id] = "land" if km <= adjacency.LAND_KM else "sea"
    return _pick(kinds, subject)


@cache
def _landmasses() -> list[BaseGeometry]:
    from geofeat.ne import layer

    parts = [p for g in layer("50m_land").geometry for p in shapely.get_parts(g)]
    big = [p for p in parts if _km2(p) >= LANDMASS_KM2]
    return big


def _km2(g: BaseGeometry) -> float:
    lat = (g.bounds[1] + g.bounds[3]) / 2
    return g.area * adjacency.KM_PER_DEG ** 2 * math.cos(math.radians(lat))


def landmass(subject: BaseGeometry) -> BaseGeometry:
    """The part of the nearest landmass (LANDMASS_KM2 or more, and not the subject's own) round its vertex nearest
    the subject's centre, measured on the ellipsoid, so the search runs across ±180°."""
    parts = _landmasses()
    own = subject.buffer(0.05)
    lon, lat = centre(subject)
    best = (math.inf, None)
    for part in parts:
        if part.intersects(own):
            continue
        xs, ys = shapely.get_coordinates(part).T
        metres = GEOD.inv(np.full(len(xs), lon), np.full(len(xs), lat), xs, ys)[2]
        i = int(np.argmin(metres))
        best = min(best, (metres[i], (xs[i], ys[i])), key=lambda t: t[0])
    if best[1] is None:
        return subject.centroid
    near = shapely.Point(best[1])
    windows = _windows(near, LANDMASS_VIEW_KM)
    return unary_union([_clip(p, windows) for p in parts if not p.intersects(own)])
