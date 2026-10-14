"""Which ring region each physical feature belongs to, and how continents are composed from countries.

The rules are docs/world-atlas-plan.md's "Assigning physical features to regions", applied in order:

1. the oceans, the planetary wind belts and the continents go to orientation;
2. a strait, canal or cape goes to the later region, in ring order, of its shores; a sea route goes to its owner;
3. a regional climate system goes to the land it shapes;
4. anything else goes to the region holding the largest share of its extent: area, length, or, for a body of water
   that no country covers, shoreline.

A `region:` override in features.yaml replaces the derived region. Rule 5 there (parent before child) is the order
engine's job, not this module's. `python -m geofeat.regions` prints the assignment of every active feature.

Ring membership comes from data/curriculum.yaml. A region's outline is the union of its member states and the
territories placed in it, plus any land of a dispute placed there that no state's outline holds (Western Sahara);
the outlines come from countries_ne.py.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import cache
from typing import Literal

import shapely
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from geofeat.countries_ne import outline, state_ids
from geofeat.curriculum import Region, load_curriculum
from geofeat.model import Feature, active, load_features
from geofeat.ne import GEOD
from geofeat.resolve import area_km2, resolve
from geofeat.sources.features import orientation

ORIENTATION = 0  # the block before region 1: oceans, planetary wind belts, continents
SHORE_TYPES = frozenset({"Strait", "Canal", "Cape"})
SHORE_BUFFER_DEG = 0.5  # how far from a passage counts as its shore
SHORE_MIN_SHARE = 0.15  # a region with less of the shore than this is a passing neighbour, not a shore
CLIMATE_BUFFER_DEG = 3.0  # how far either side of a flow line its climate reaches over land
SHORELINE_EPS_DEG = 0.1  # how close to a region a water body's edge counts as its shore
COVERED_SHARE = 0.5  # below this share of its area inside countries, a water body is measured by its shoreline


@cache
def ring() -> dict[int, Region]:
    return {r.number: r for r in load_curriculum(state_ids()).regions}


def region_outline(members: Iterable[BaseGeometry], disputes: Iterable[BaseGeometry],
                   held: BaseGeometry) -> BaseGeometry:
    """A region's land: its member states and territories, plus whatever of its disputes no state holds (`held`)."""
    return unary_union([*members, *(d.difference(held) for d in disputes)])


@cache
def region_outlines() -> dict[int, BaseGeometry]:
    held = unary_union([outline(c) for r in ring().values() for c in r.countries])
    return {n: region_outline([outline(c) for c in (*r.countries, *r.territories)],
                              [outline(d) for d in r.disputes], held)
            for n, r in ring().items()}


Rule = Literal["orientation", "shore", "owner", "climate", "extent", "override"]
Measure = Literal["none", "area", "length", "shoreline", "point", "shore", "land"]


@dataclass(frozen=True)
class Assignment:
    region: int
    rule: Rule
    measure: Measure
    shares: dict[int, float]  # region -> share of the measure; empty for orientation
    derived: int  # what the rules give, before any override

    @property
    def share(self) -> float:
        return self.shares.get(self.region, 0.0)


def _ranked(measures: Mapping[int, float], total: float) -> dict[int, float]:
    """Each region's share of `total`, largest first, ties to the earlier region; zero shares dropped."""
    shares = {n: m / total for n, m in measures.items() if total > 0 and m > 0}
    return dict(sorted(shares.items(), key=lambda item: (-item[1], item[0])))


def _length_km(geometry: BaseGeometry) -> float:
    return GEOD.geometry_length(geometry) / 1000


def _near(regions: Mapping[int, BaseGeometry], geometry: BaseGeometry) -> dict[int, BaseGeometry]:
    box = shapely.box(*geometry.bounds)
    return {n: outline for n, outline in regions.items() if outline.intersects(box)}


def _buffer_land(regions: Mapping[int, BaseGeometry], geometry: BaseGeometry, degrees: float) -> dict[int, float]:
    """km² of each region's land within `degrees` of the geometry."""
    zone = geometry.buffer(degrees)
    return {n: area_km2(outline.intersection(zone)) for n, outline in _near(regions, zone).items()}


def extent_shares(geometry: BaseGeometry, regions: Mapping[int, BaseGeometry]) -> tuple[Measure, dict[int, float]]:
    """Rule 4: each region's share of the feature's extent. A point goes to the nearest region. A polygon is measured
    by area, unless less than half of it lies inside countries (a sea, the Caspian): then by the length of its edge
    that runs along each region's coast, as a share of its whole coast."""
    polygons = [g for g in shapely.get_parts(geometry) if g.geom_type == "Polygon"]
    lines = [g for g in shapely.get_parts(geometry) if g.geom_type == "LineString"]
    if polygons:
        shape = unary_union(polygons)
        total = area_km2(shape)
        areas = {n: area_km2(outline.intersection(shape)) for n, outline in _near(regions, shape).items()}
        if sum(areas.values()) >= COVERED_SHARE * total:
            return "area", _ranked(areas, total)
        edge = shape.boundary
        coasts = {n: _length_km(edge.intersection(outline.buffer(SHORELINE_EPS_DEG)))
                  for n, outline in _near(regions, shape.buffer(SHORELINE_EPS_DEG)).items()}
        return "shoreline", _ranked(coasts, sum(coasts.values()))
    if lines:
        line = shapely.MultiLineString(lines)
        lengths = {n: _length_km(outline.intersection(line)) for n, outline in _near(regions, line).items()}
        return "length", _ranked(lengths, _length_km(line))
    nearest = min(regions, key=lambda n: (regions[n].distance(geometry), n))
    return "point", {nearest: 1.0}


def shore_shares(geometry: BaseGeometry, regions: Mapping[int, BaseGeometry]) -> dict[int, float]:
    """Each region's share of the land along a passage: the land within SHORE_BUFFER_DEG of it."""
    land = _buffer_land(regions, geometry, SHORE_BUFFER_DEG)
    return _ranked(land, sum(land.values()))


def later_shore(shares: Mapping[int, float]) -> int:
    """Rule 2: of the regions holding a real share of the shore, the later in ring order."""
    return max((n for n, share in shares.items() if share >= SHORE_MIN_SHARE), default=next(iter(shares)))


def climate_shares(geometry: BaseGeometry, regions: Mapping[int, BaseGeometry]) -> dict[int, float]:
    """Rule 3: each region's share of the land under a band, or within CLIMATE_BUFFER_DEG of a flow line."""
    if any(g.geom_type == "Polygon" for g in shapely.get_parts(geometry)):
        land = {n: area_km2(outline.intersection(geometry)) for n, outline in _near(regions, geometry).items()}
    else:
        land = _buffer_land(regions, geometry, CLIMATE_BUFFER_DEG)
    return _ranked(land, sum(land.values()))


def _top(feature: Feature, shares: Mapping[int, float]) -> int:
    if not shares:
        raise ValueError(f"{feature.id}: no region holds any of its extent")
    return next(iter(shares))


def override_errors(features: Iterable[Feature], ring: Iterable[int]) -> list[str]:
    """A `region:` override must name a region of the ring."""
    numbers = set(ring)
    return [f"{f.id}: region {f.region} is not in the ring" for f in features
            if f.region is not None and f.region not in numbers]


def derive(feature: Feature, geometry: BaseGeometry, regions: Mapping[int, BaseGeometry]) -> Assignment:
    """The feature's region by the plan's rules, then its `region:` override if it has one."""
    if errors := override_errors([feature], regions):
        raise ValueError(errors[0])
    if orientation(feature):
        rule, measure, shares, derived = "orientation", "none", {}, ORIENTATION
    elif feature.type in SHORE_TYPES:
        rule, measure, shares = "shore", "shore", shore_shares(geometry, regions)
        derived = later_shore(shares) if shares else _top(feature, shares)
    elif feature.type == "Sea route":
        rule, measure, shares = "owner", "shore", shore_shares(geometry, regions)
        derived = _top(feature, shares)
    elif feature.family == "climate":
        rule, measure, shares = "climate", "land", climate_shares(geometry, regions)
        derived = _top(feature, shares)
    else:
        rule = "extent"
        measure, shares = extent_shares(geometry, regions)
        derived = _top(feature, shares)
    if feature.region is not None:
        return Assignment(feature.region, "override", measure, shares, derived)
    return Assignment(derived, rule, measure, shares, derived)


def assign(features: Iterable[Feature]) -> dict[str, Assignment]:
    regions = region_outlines()
    return {f.id: derive(f, resolve(f), regions) for f in features}


def region_name(n: int) -> str:
    return "Orientation" if n == ORIENTATION else ring()[n].name


def report(features: list[Feature], assignments: Mapping[str, Assignment]) -> str:
    lines = ["| Feature | Type | Rule | Measure | Region | Share | Runner-up |", "|---|---|---|---|---|---|---|"]
    for f in features:
        a = assignments[f.id]
        others = [(n, s) for n, s in a.shares.items() if n != a.region]
        runner = f"{others[0][0]} ({others[0][1]:.0%})" if others else ""
        note = f" (derived {a.derived})" if a.rule == "override" else ""
        share = f"{a.share:.0%}" if a.shares else ""
        lines.append(f"| {f.id} | {f.type} | {a.rule}{note} | {a.measure} | {a.region} {region_name(a.region)} "
                     f"| {share} | {runner} |")
    counts = {n: sum(a.region == n for a in assignments.values()) for n in (ORIENTATION, *ring())}
    lines += ["", "| Region | Features |", "|---|---|"]
    lines += [f"| {n} {region_name(n)} | {count} |" for n, count in counts.items()]
    return "\n".join(lines)


# Continents (P2.6). The orientation block's continent cards are the union of their member countries' outlines
# (decision 7 in the plan). A transcontinental state is split along Natural Earth's continent line: the union of
# `ne_10m_geography_regions_polys` rows of one REGION with FEATURECLA in {Continent, Island, Island group, Isthmus},
# per docs/research/continents.md. Wiring this to real data waits for P2.2's country outlines.
TRANSCONTINENTAL = frozenset({
    "russia", "turkey", "kazakhstan", "azerbaijan", "georgia",  # the Europe–Asia line: Urals, Ural River, Caspian, Caucasus crest, Straits
    "egypt",  # Suez; NE draws the Africa–Asia line along Egypt's border with Israel, so Sinai falls in Africa
    "indonesia",  # western New Guinea is Oceania in NE
    "united-states", "chile",  # Hawaii and Easter Island are Oceania in NE
    "spain", "portugal",  # the Canaries and Madeira are Africa in NE
})


def disjoint(landmasses: Mapping[str, BaseGeometry]) -> dict[str, BaseGeometry]:
    """NE's continents overlap a little (Europe and Asia in the Caucasus, Africa and Asia near Sinai). Give each
    overlap to the smaller continent, per continents.md, so no land is on two continent cards."""
    by_size = sorted(landmasses, key=lambda name: (landmasses[name].area, name))
    result = {}
    for i, name in enumerate(by_size):
        smaller = unary_union([landmasses[other] for other in by_size[:i]])
        result[name] = landmasses[name].difference(smaller) if i else landmasses[name]
    return result


def continent_geometry(continent: str, members: Mapping[str, str | tuple[str, ...]],
                       countries: Mapping[str, BaseGeometry], landmasses: Mapping[str, BaseGeometry]) -> BaseGeometry:
    """The union of `continent`'s member countries. `members` maps a country to its continent, or to every continent
    it spans if it is in TRANSCONTINENTAL. Such a country gives each continent the part of it on that continent's
    landmass, plus any part off every landmass (an island NE leaves out) that lies nearest that landmass."""
    lands = disjoint(landmasses)
    pieces = []
    for country, continents in members.items():
        spans = (continents,) if isinstance(continents, str) else continents
        if continent not in spans:
            continue
        outline = countries[country]
        if country not in TRANSCONTINENTAL:
            pieces.append(outline)
            continue
        pieces.append(outline.intersection(lands[continent]))
        stray = outline.difference(unary_union([lands[c] for c in spans]))
        for part in shapely.get_parts(stray):
            if min(spans, key=lambda c: (lands[c].distance(part), c)) == continent:
                pieces.append(part)
    return unary_union(pieces)


def main() -> None:
    features = active(load_features())
    print(report(features, assign(features)))


if __name__ == "__main__":
    main()
