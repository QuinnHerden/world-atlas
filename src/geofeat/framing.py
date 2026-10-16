"""Each country, territory and dispute card's region, which frame.py frames it on: the curriculum region it is studied
in (data/curriculum.yaml), or a fixed sub-frame where one frame doesn't suit (Oceania, the Lesser Antilles). A region is
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
from geofeat.regions import ring as curriculum_regions

Box = tuple[float, float, float, float]
Framing = tuple[str, BaseGeometry, Box | None, float | None, Box | None]

# Capitals and cities on their host's region frame (v2.1.0, ADR 0003). False reverts them to v2.0 framing
# (their host country's frame, or the 1,000 km close-dot frame) without touching the political cards.
CITY_REGION_FRAMING = True
OUTLIER = 2.5  # a member farther than this many times the median member's distance from the region's centre is left out
# Sub-frames with a fixed lon/lat box (west, south, east, north; east may pass 180°) and the cards drawn on them, for
# regions no single frame suits: Oceania, too vast, and the Lesser Antilles, too fine for the Caribbean frame. The
# boxes take in the anchors each island group is read against: eastern Australia and New Guinea for Melanesia, the
# Philippines and New Guinea for Micronesia, New Guinea and Hawaii for Kiribati, New Zealand and eastern Australia for
# Polynesia. Every other card in those regions keeps the region frame.
SUB_FRAMES = {
    "18-melanesia": ((128.0, -34.0, 182.0, 2.0),
                     ("australia", "papua-new-guinea", "solomon-islands", "vanuatu", "new-caledonia")),
    "18-micronesia": ((112.0, -12.0, 178.0, 26.0), ("palau", "micronesia", "guam", "marshall-islands", "nauru")),
    "18-central-pacific": ((145.0, -25.0, 228.0, 28.0), ("kiribati",)),
    "18-polynesia": ((148.0, -48.0, 228.0, -2.0),
                     ("new-zealand", "fiji", "tonga", "samoa", "tuvalu", "french-polynesia", "cook-islands")),
    "21-lesser-antilles": ((-64.0, 11.6, -58.8, 18.3),
                           ("antigua-and-barbuda", "saint-kitts-and-nevis", "dominica", "saint-lucia",
                            "saint-vincent-and-the-grenadines", "grenada", "barbados", "guadeloupe", "martinique")),
}
# A sub-frame too tight to place on its own gets a small regional locator: the Caribbean basin, Florida and Cuba to
# the north coast of South America (lon0, lon1, lat0, lat1)
LOCATORS = {"21-lesser-antilles": (-88.0, -56.0, 7.0, 28.0)}
MUST_SUB_FRAME = frozenset({18})  # every card in these regions must be on a sub-frame


@cache
def _entries() -> dict[str, tuple[int, BaseGeometry, tuple[str, ...]]]:
    """Every country, territory and dispute: its region, its card outline and what its frame `include`s."""
    countries, others = load_political()
    return {e.id: (e.region, e.outline(), tuple(e.frame.include)) for e in (*countries, *others)}


@cache
def _body(id: str) -> tuple[list[tuple[float, float]], bool]:
    """The lon/lat corners of the convex hull of a card's main body, and whether it is a giant."""
    outline = _entries()[id][1]
    projection = Equirectangular(*centre(outline))
    body, _ = main_group(project(outline, projection))
    x0, y0, x1, y1 = body.bounds
    xs, ys = np.array(body.convex_hull.exterior.coords).T
    lons, lats = Transformer.from_crs(projection.proj4_init, "EPSG:4326", always_xy=True).transform(xs, ys)
    return list(zip(lons, lats)), max(x1 - x0, (y1 - y0) * ASPECT) / FILL > GIANT_FRAME_M


def _hull_points(id: str) -> list[tuple[float, float]] | None:
    """A member's main body's hull corners, or None for a giant."""
    hull, giant = _body(id)
    return None if giant else hull


@cache
def _included(ids: tuple[str, ...]) -> Box:
    """The lon/lat box (west, south, east, north) round the main bodies a card's frame `include`s (giants too)."""
    if unknown := [i for i in ids if i not in _entries()]:
        raise ValueError(f"frame include: no country or territory {', '.join(unknown)}")
    lons, lats = zip(*(p for i in ids for p in _body(i)[0]))
    if max(lons) - min(lons) > 180:  # a lon/lat box across 180° would span the globe
        raise ValueError(f"frame include {', '.join(ids)}: the box round them crosses 180°, which isn't supported")
    return float(min(lons)), float(min(lats)), float(max(lons)), float(max(lats))


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


@cache
def _box_points(west: float, south: float, east: float, north: float) -> BaseGeometry:
    """Points along a lon/lat box's edges (east may pass 180°), wrapped into range."""
    lons, lats = np.linspace(west, east, 25), np.linspace(south, north, 9)
    edge = [(x, y) for x in lons for y in (south, north)] + [(x, y) for x in (west, east) for y in lats]
    return MultiPoint([((x + 180) % 360 - 180, y) for x, y in edge])


def region_of(id: str) -> tuple[str, tuple[str, ...]]:
    """The frame a card is drawn on: its name, and the members it is fitted to (none for a sub-frame's fixed box)."""
    entries = _entries()
    region = entries[id][0]
    if found := [name for name, (_, cards) in SUB_FRAMES.items() if id in cards]:
        return found[0], ()
    if region in MUST_SUB_FRAME:
        raise ValueError(f"{id}: region {region} is drawn on sub-frames only, and none of framing.SUB_FRAMES has it")
    return f"{region:02d}", tuple(sorted(i for i, (r, _, _) in entries.items() if r == region))


def region(id: str) -> Framing:
    """("region", the region's member points, None, its frame_margin, hold) or ("fixed", a sub-frame's box points, its
    regional locator, None, hold) for a political card. `hold` is the lon/lat box round the bodies its frame
    `include`s (New Zealand: Australia), which frame.py holds as it holds the subject; None if it includes none."""
    name, members = region_of(id)
    hold = _included(include) if (include := _entries()[id][2]) else None
    if name in SUB_FRAMES:
        return "fixed", _box_points(*SUB_FRAMES[name][0]), LOCATORS.get(name), None, hold
    return "region", _points(members), None, curriculum_regions()[int(name)].frame_margin, hold


def city_region(country_id: str) -> Callable[[], Framing] | None:
    """A capital's or city's region provider (its host's), or None while CITY_REGION_FRAMING is off."""
    return (lambda: region(country_id)) if CITY_REGION_FRAMING else None
