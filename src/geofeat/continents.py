"""The orientation block's continents, composed from country outlines (docs/world-atlas-plan.md, decision 7).

A continent is the union of the full outlines (countries_ne.py, never a card's `mainland` crop) of its member states
and carded territories, plus whatever land of a dispute placed with them that no state holds (Western Sahara), as a
ring region's outline is. Membership follows the UN geoscheme: each entry takes the continent of its ring region in
data/curriculum.yaml (REGION_CONTINENT), except the few the geoscheme places elsewhere (MEMBERSHIP). Central America
and the Caribbean are North America; Indonesia, Papua included, is Asia; Hawaii is North America; Easter Island is
South America. Antarctica has no states: its card is NE's Antarctica polygon, a plain layer part.

A transcontinental state (TRANSCONTINENTAL) is split along Natural Earth's continent line: the union of
`10m_geography_regions_polys` rows of one REGION with FEATURECLA in LANDMASS_CLASSES, per docs/research/continents.md.

A feature draws a continent with the part `{layer: continent, select: {id: <continent id>}}`; resolve.py hands it here.
"""

from collections.abc import Mapping
from functools import cache

import shapely
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from geofeat.countries_ne import outline
from geofeat.model import Part
from geofeat.ne import layer
from geofeat.regions import held_land, region_outline, ring
from geofeat.resolve import CONTINENT_LAYER

COMPOSED = ("africa", "asia", "europe", "north-america", "oceania", "south-america")
REGION_CONTINENT = {  # by slug, so renumbering the ring can't move a region to another continent
    "western-europe": "europe", "nordic-baltic": "europe", "central-europe-italy": "europe", "balkans": "europe",
    "eastern-europe": "europe",
    "caucasus-anatolia": "asia", "levant-mesopotamia": "asia", "arabian-peninsula": "asia",
    "horn-east-africa": "africa", "north-africa": "africa", "west-africa": "africa", "central-africa": "africa",
    "southern-africa-indian-ocean": "africa",
    "south-asia": "asia", "iran-central-asia": "asia", "east-asia": "asia", "southeast-asia": "asia",
    "oceania": "oceania",
    "north-central-america": "north-america",
    "south-america": "south-america",
    "caribbean": "north-america",
}
MEMBERSHIP = {
    "british-indian-ocean-territory": "africa",  # M49 Eastern Africa; the ring places it with the Maldives
    "aruba": "north-america", "curacao": "north-america",  # Caribbean islands; the ring places them by Venezuela
}
# Split along NE's line. Europe–Asia: the Urals, Ural River, Caspian, Caucasus crest and Turkish Straits. Egypt: NE
# draws the Africa–Asia line along Egypt's border with Israel, not at Suez, so Sinai falls in Africa and the split
# leaves Egypt whole there (about 30 km² of coastal scraps go to Asia); continents.md's Sinai deviation.
TRANSCONTINENTAL: dict[str, tuple[str, ...]] = {
    "russia": ("europe", "asia"),
    "turkey": ("europe", "asia"),
    "kazakhstan": ("europe", "asia"),
    "azerbaijan": ("europe", "asia"),
    "georgia": ("europe", "asia"),
    "egypt": ("africa", "asia"),
}
NE_REGION = {"africa": "Africa", "asia": "Asia", "europe": "Europe"}
LANDMASS_CLASSES = frozenset({"Continent", "Island", "Island group", "Isthmus"})
LANDMASS_LAYER = "10m_geography_regions_polys"
# About 1 km: under a pixel on any continent's frame, and it cuts the 10m outlines' vertices by two thirds, which the
# pair check (it projects each continent against every feature near it) otherwise spends minutes on. Each continent
# is simplified on its own, so neighbours' shared edges drift by up to this much: Europe and Asia overlap by about
# 12 km² along the line, North and South America by about 1 km².
SIMPLIFY_DEG = 0.01


def members() -> dict[str, str | tuple[str, ...]]:
    """Every state, territory and dispute the ring places: its continent, or every continent a transcontinental
    state spans."""
    placed = {i: REGION_CONTINENT[r.slug] for r in ring().values() for i in (*r.countries, *r.territories, *r.disputes)}
    return placed | MEMBERSHIP | TRANSCONTINENTAL


def disjoint(landmasses: Mapping[str, BaseGeometry]) -> dict[str, BaseGeometry]:
    """NE's continents overlap a little (Europe and Asia in the Caucasus, Africa and Asia near Sinai). Give each
    overlap to the smaller continent, per continents.md, so no land is on two continent cards."""
    by_size = sorted(landmasses, key=lambda name: (landmasses[name].area, name))
    result = {}
    for i, name in enumerate(by_size):
        smaller = unary_union([landmasses[other] for other in by_size[:i]])
        result[name] = landmasses[name].difference(smaller) if i else landmasses[name]
    return result


@cache
def landmasses() -> dict[str, BaseGeometry]:
    """NE's landmass for each continent a transcontinental state spans, made disjoint."""
    rows = layer(LANDMASS_LAYER)
    rows = rows[rows["featurecla"].isin(LANDMASS_CLASSES)]
    return disjoint({c: unary_union(rows[rows["region"] == NE_REGION[c]].geometry.values) for c in NE_REGION})


def continent_geometry(continent: str, members: Mapping[str, str | tuple[str, ...]],
                       countries: Mapping[str, BaseGeometry], lands: Mapping[str, BaseGeometry]) -> BaseGeometry:
    """The union of `continent`'s member outlines. `members` maps an entry to its continent, or to every continent
    it spans. A spanning entry gives each continent the part of it on that continent's landmass (`lands`, disjoint),
    plus any part off every landmass (an island NE leaves out, a coast NE draws further in) nearest that landmass."""
    pieces = []
    for id, continents in members.items():
        spans = (continents,) if isinstance(continents, str) else continents
        if continent not in spans:
            continue
        shape = countries[id]
        if len(spans) == 1:
            pieces.append(shape)
            continue
        pieces.append(shape.intersection(lands[continent]))
        stray = shape.difference(unary_union([lands[c] for c in spans]))
        for part in shapely.get_parts(stray):
            if min(spans, key=lambda c: (lands[c].distance(part), c)) == continent:
                pieces.append(part)
    return unary_union(pieces)


@cache
def _outlines() -> dict[str, BaseGeometry]:
    return {i: outline(i) for i in members()}


@cache
def geometry(continent: str) -> BaseGeometry:
    """A composed continent from the real data: its states and territories, plus its disputes' land no state holds."""
    if continent not in COMPOSED:
        raise ValueError(f"no composed continent {continent!r}; one of {', '.join(COMPOSED)}")
    everyone, outlines = members(), _outlines()
    disputes = {d for r in ring().values() for d in r.disputes}
    entries = {i: c for i, c in everyone.items() if i not in disputes}
    countries = continent_geometry(continent, entries, outlines, landmasses())
    mine = [outlines[d] for d in disputes if everyone[d] == continent]
    composed = region_outline([countries], mine, held_land())
    return shapely.make_valid(shapely.simplify(composed, SIMPLIFY_DEG, preserve_topology=True))


def part_geometry(owner: str, part: Part) -> BaseGeometry:
    """The geometry of a `{layer: continent, select: {id: <continent>}}` part."""
    if part.subtract or part.rows != 1 or set(part.select or {}) != {"id"}:
        raise ValueError(f"{owner}: a {CONTINENT_LAYER} part is exactly {{layer: {CONTINENT_LAYER}, select: {{id: <continent>}}}}")
    return geometry(str(part.select["id"]))
