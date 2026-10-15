"""Each country, territory and dispute card's region, which frame.py frames it on: the curriculum region it is studied
in (data/curriculum.yaml), or for Oceania, which no single frame holds, one of three Pacific sub-frames. A region is
passed as the hull points of its members' main bodies, so overseas parts and outlying islands don't stretch it. Giant
members (frame.GIANT_FRAME_M), which keep their v2.0 frames, and outlying members (the Falklands) don't count. Read when jobs are
built; the points travel in the render job, so they are in its key."""

from collections.abc import Callable
from functools import cache

import numpy as np
from pyproj import Transformer
from shapely.geometry import MultiPoint
from shapely.geometry.base import BaseGeometry

from geofeat.frame import ASPECT, FILL, GIANT_FRAME_M, Equirectangular, centre, main_group, project
from geofeat.ne import GEOD
from geofeat.polities import load_political

Framing = tuple[str, BaseGeometry]

# Capitals and cities on their host's region frame: a proposal under review. False reverts them to v2.0 framing
# (their host country's frame, or the 1,000 km close-dot frame) without touching the political cards.
CITY_REGION_FRAMING = True
OUTLIER = 2.5  # a member farther than this many times the median member's distance from the region's centre is left out
OCEANIA = 18
# Oceania's sub-frames: the members each is fitted to (an anchor landmass in each: New Guinea, New Zealand) and the
# cards drawn on it. Australia is a giant and keeps its v2.0 frame.
PACIFIC_FRAMES = {
    "melanesia": (("papua-new-guinea", "solomon-islands", "vanuatu", "new-caledonia"),
                  ("australia", "papua-new-guinea", "solomon-islands", "vanuatu", "new-caledonia")),
    "micronesia": (("papua-new-guinea", "palau", "micronesia", "guam", "marshall-islands", "nauru"),
                   ("palau", "micronesia", "guam", "marshall-islands", "nauru", "kiribati")),
    "polynesia": (("new-zealand", "fiji", "tonga", "samoa", "tuvalu"),
                  ("new-zealand", "fiji", "tonga", "samoa", "tuvalu", "french-polynesia")),
}


@cache
def _entries() -> dict[str, tuple[int, BaseGeometry]]:
    """Every country, territory and dispute: its region and its card outline."""
    countries, others = load_political()
    return {e.id: (e.region, e.outline()) for e in (*countries, *others)}


@cache
def _hull_points(id: str) -> list[tuple[float, float]] | None:
    """The lon/lat corners of the convex hull of a member's main body, or None for a giant."""
    outline = _entries()[id][1]
    projection = Equirectangular(*centre(outline))
    body, _ = main_group(project(outline, projection))
    x0, y0, x1, y1 = body.bounds
    if max(x1 - x0, (y1 - y0) * ASPECT) / FILL > GIANT_FRAME_M:
        return None
    xs, ys = np.array(body.convex_hull.exterior.coords).T
    lons, lats = Transformer.from_crs(projection.proj4_init, "EPSG:4326", always_xy=True).transform(xs, ys)
    return list(zip(lons, lats))


@cache
def _points(members: tuple[str, ...]) -> BaseGeometry:
    hulls = {m: hull for m in members if (hull := _hull_points(m))}
    if not hulls:
        raise ValueError(f"region of {', '.join(members)}: every member is a giant, so nothing shapes its frame")
    centres = {m: centre(MultiPoint(h)) for m, h in hulls.items()}
    mid = centre(MultiPoint(list(centres.values())))
    far = {m: GEOD.inv(*mid, *c)[2] for m, c in centres.items()}
    typical = float(np.median(list(far.values())))
    return MultiPoint([p for m, h in hulls.items() if len(hulls) < 4 or far[m] <= OUTLIER * typical for p in h])


def region_of(id: str) -> tuple[str, tuple[str, ...]]:
    """The frame a card is drawn on: its name, and the members it is fitted to."""
    entries = _entries()
    region = entries[id][0]
    if region == OCEANIA:
        found = [(n, f) for n, f in PACIFIC_FRAMES.items() if id in f[1]]
        if not found:
            raise ValueError(f"{id}: in Oceania but on none of framing.PACIFIC_FRAMES; add it to one")
        name, (members, _) = found[0]
        return f"{OCEANIA}-{name}", members
    return f"{region:02d}", tuple(sorted(i for i, (r, _) in entries.items() if r == region))


def region(id: str) -> Framing:
    """("region" or "pacific", the frame's member points) for a political card."""
    name, members = region_of(id)
    return ("pacific" if name.startswith(f"{OCEANIA}-") else "region"), _points(members)


def city_region(country_id: str) -> Callable[[], Framing] | None:
    """A capital's or city's region provider (its host's), or None while CITY_REGION_FRAMING is off."""
    return (lambda: region(country_id)) if CITY_REGION_FRAMING else None
