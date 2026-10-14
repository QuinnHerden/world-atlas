"""Which ring region each physical feature belongs to, and how continents are composed from countries.

The rules are docs/world-atlas-plan.md's "Assigning physical features to regions", applied in order:

1. the oceans, the planetary wind belts and the continents go to orientation;
2. a strait, canal or cape goes to the later region, in ring order, of its shores; a sea route goes to its owner;
3. a regional climate system goes to the land it shapes;
4. anything else goes to the region holding the largest share of its extent: area, length, or, for a body of water
   that no country covers, shoreline.

A `region:` override in features.yaml replaces the derived region. Rule 5 there (parent before child) is the order
engine's job, not this module's. `python -m geofeat.regions` prints the assignment of every active feature.

A region's outline is the union of its member countries' outlines. Until P2.2 and data/curriculum.yaml land, the
members come from the plan's ring table and the outlines from `country_geometry`.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import cache
from typing import Literal

import shapely
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from geofeat.model import Feature, active, load_features
from geofeat.ne import GEOD, layer
from geofeat.resolve import area_km2, resolve
from geofeat.sources.features import orientation

ORIENTATION = 0  # the block before region 1: oceans, planetary wind belts, continents
SHORE_TYPES = frozenset({"Strait", "Canal", "Cape"})
SHORE_BUFFER_DEG = 0.5  # how far from a passage counts as its shore
SHORE_MIN_SHARE = 0.15  # a region with less of the shore than this is a passing neighbour, not a shore
CLIMATE_BUFFER_DEG = 3.0  # how far either side of a flow line its climate reaches over land
SHORELINE_EPS_DEG = 0.1  # how close to a region a water body's edge counts as its shore
COVERED_SHARE = 0.5  # below this share of its area inside countries, a water body is measured by its shoreline

# The ring, from the plan's table: number -> (name, country ids in walk order). Northern Cyprus and Somaliland are
# inside Cyprus and Somalia's composed outlines; Western Sahara is a pocket of region 10.
REGIONS: dict[int, tuple[str, tuple[str, ...]]] = {
    1: ("Western Europe", ("portugal", "spain", "andorra", "france", "monaco", "belgium", "luxembourg", "netherlands", "united-kingdom", "ireland")),
    2: ("Nordic & Baltic", ("iceland", "norway", "sweden", "denmark", "finland", "estonia", "latvia", "lithuania")),
    3: ("Central Europe & Italy",
        ("poland", "germany", "czechia", "austria", "switzerland", "liechtenstein", "italy", "san-marino", "vatican-city", "malta", "slovenia", "hungary", "slovakia")),
    4: ("Balkans", ("croatia", "bosnia-and-herzegovina", "serbia", "kosovo", "montenegro", "albania", "north-macedonia", "greece", "bulgaria", "romania")),
    5: ("Eastern Europe", ("moldova", "ukraine", "belarus", "russia")),
    6: ("Caucasus & Anatolia", ("georgia", "azerbaijan", "armenia", "turkey", "cyprus")),
    7: ("Levant & Mesopotamia", ("syria", "lebanon", "israel", "palestine", "jordan", "iraq")),
    8: ("Arabian Peninsula", ("kuwait", "saudi-arabia", "bahrain", "qatar", "united-arab-emirates", "oman", "yemen")),
    9: ("Horn & East Africa", ("djibouti", "eritrea", "ethiopia", "somalia", "kenya", "tanzania", "burundi", "rwanda", "uganda", "south-sudan", "sudan")),
    10: ("North Africa", ("egypt", "libya", "tunisia", "algeria", "morocco", "western-sahara")),
    11: ("West Africa", ("mauritania", "senegal", "gambia", "cabo-verde", "guinea-bissau", "guinea", "sierra-leone", "liberia", "cote-divoire", "mali", "burkina-faso", "ghana", "togo",
                         "benin", "nigeria", "niger")),
    12: ("Central Africa", ("chad", "cameroon", "central-african-republic", "equatorial-guinea", "sao-tome-and-principe", "gabon", "congo", "dr-congo")),
    13: ("Southern Africa & Indian Ocean", ("angola", "zambia", "malawi", "mozambique", "zimbabwe", "botswana", "namibia", "south-africa", "lesotho", "eswatini",
                                            "madagascar", "comoros", "mauritius", "seychelles")),
    14: ("South Asia", ("maldives", "sri-lanka", "india", "bangladesh", "bhutan", "nepal", "pakistan")),
    15: ("Iran & Central Asia", ("afghanistan", "iran", "turkmenistan", "uzbekistan", "tajikistan", "kyrgyzstan", "kazakhstan")),
    16: ("East Asia", ("china", "mongolia", "north-korea", "south-korea", "japan", "taiwan")),
    17: ("Southeast Asia", ("philippines", "malaysia", "brunei", "singapore", "thailand", "myanmar", "laos", "vietnam", "cambodia", "indonesia", "timor-leste")),
    18: ("Oceania", ("australia", "papua-new-guinea", "solomon-islands", "vanuatu", "new-zealand", "fiji", "tonga", "samoa", "tuvalu", "kiribati", "nauru", "marshall-islands", "micronesia",
                     "palau")),
    19: ("North & Central America", ("united-states", "canada", "mexico", "guatemala", "belize", "el-salvador", "honduras", "nicaragua", "costa-rica", "panama")),
    20: ("South America", ("colombia", "ecuador", "peru", "chile", "bolivia", "argentina", "uruguay", "paraguay", "brazil", "suriname", "guyana", "venezuela")),
    21: ("Caribbean", ("trinidad-and-tobago", "grenada", "saint-vincent-and-the-grenadines", "barbados", "saint-lucia", "dominica", "antigua-and-barbuda", "saint-kitts-and-nevis", "dominican-republic", "haiti", "jamaica", "cuba", "bahamas")),
}
# Territories have no place in the ring yet (open decision 5, default: geographic pockets). Their land still frames
# features, so each counts towards the region it lies in. Greenland and Bermuda wait for the manual look the decision
# names; Antarctica is in no region.
TERRITORIES: dict[int, tuple[str, ...]] = {
    1: ("gibraltar",),
    2: ("aland", "faroe-islands"),
    6: ("dhekelia", "akrotiri"),  # the UK's Cyprus base areas
    13: ("reunion", "mayotte"),
    16: ("hong-kong", "macau"),
    18: ("new-caledonia", "french-polynesia"),
    20: ("french-guiana", "falkland-islands"),
    21: ("puerto-rico", "us-virgin-islands", "british-virgin-islands", "cayman-islands", "turks-and-caicos-islands", "aruba", "curacao", "sint-maarten", "saint-martin", "saint-barthelemy", "anguilla", "montserrat", "guadeloupe", "martinique"),
}

# Country outlines, per docs/research/ne-political-layers.md (a) and (c): the admin_0 row, or the map unit for the four
# states whose row carries overseas parts (and France's overseas departments), composed with the recognised-border rows.
# id -> NE admin_0 ADM0_A3, or map-unit GU_A3.
_ADMIN_0 = {
    "portugal": "PRT", "spain": "ESP", "andorra": "AND", "monaco": "MCO",
    "belgium": "BEL", "luxembourg": "LUX", "united-kingdom": "GBR", "ireland": "IRL",
    "iceland": "ISL", "sweden": "SWE", "denmark": "DNK", "finland": "FIN",
    "estonia": "EST", "latvia": "LVA", "lithuania": "LTU", "poland": "POL",
    "germany": "DEU", "czechia": "CZE", "austria": "AUT", "switzerland": "CHE",
    "liechtenstein": "LIE", "italy": "ITA", "san-marino": "SMR", "vatican-city": "VAT",
    "malta": "MLT", "slovenia": "SVN", "hungary": "HUN", "slovakia": "SVK",
    "croatia": "HRV", "bosnia-and-herzegovina": "BIH", "serbia": "SRB", "kosovo": "KOS",
    "montenegro": "MNE", "albania": "ALB", "north-macedonia": "MKD", "greece": "GRC",
    "bulgaria": "BGR", "romania": "ROU", "moldova": "MDA", "ukraine": "UKR",
    "belarus": "BLR", "russia": "RUS", "georgia": "GEO", "azerbaijan": "AZE",
    "armenia": "ARM", "turkey": "TUR", "cyprus": "CYP", "syria": "SYR",
    "lebanon": "LBN", "israel": "ISR", "palestine": "PSX", "jordan": "JOR",
    "iraq": "IRQ", "kuwait": "KWT", "saudi-arabia": "SAU", "bahrain": "BHR",
    "qatar": "QAT", "united-arab-emirates": "ARE", "oman": "OMN", "yemen": "YEM",
    "djibouti": "DJI", "eritrea": "ERI", "ethiopia": "ETH", "somalia": "SOM",
    "kenya": "KEN", "tanzania": "TZA", "burundi": "BDI", "rwanda": "RWA",
    "uganda": "UGA", "south-sudan": "SDS", "sudan": "SDN", "egypt": "EGY",
    "libya": "LBY", "tunisia": "TUN", "algeria": "DZA", "morocco": "MAR",
    "western-sahara": "SAH", "mauritania": "MRT", "senegal": "SEN", "gambia": "GMB",
    "cabo-verde": "CPV", "guinea-bissau": "GNB", "guinea": "GIN", "sierra-leone": "SLE",
    "liberia": "LBR", "cote-divoire": "CIV", "mali": "MLI", "burkina-faso": "BFA",
    "ghana": "GHA", "togo": "TGO", "benin": "BEN", "nigeria": "NGA",
    "niger": "NER", "chad": "TCD", "cameroon": "CMR", "central-african-republic": "CAF",
    "equatorial-guinea": "GNQ", "sao-tome-and-principe": "STP", "gabon": "GAB", "congo": "COG",
    "dr-congo": "COD", "angola": "AGO", "zambia": "ZMB", "malawi": "MWI",
    "mozambique": "MOZ", "zimbabwe": "ZWE", "botswana": "BWA", "namibia": "NAM",
    "south-africa": "ZAF", "lesotho": "LSO", "eswatini": "SWZ", "madagascar": "MDG",
    "comoros": "COM", "mauritius": "MUS", "seychelles": "SYC", "maldives": "MDV",
    "sri-lanka": "LKA", "india": "IND", "bangladesh": "BGD", "bhutan": "BTN",
    "nepal": "NPL", "pakistan": "PAK", "afghanistan": "AFG", "iran": "IRN",
    "turkmenistan": "TKM", "uzbekistan": "UZB", "tajikistan": "TJK", "kyrgyzstan": "KGZ",
    "kazakhstan": "KAZ", "china": "CHN", "mongolia": "MNG", "north-korea": "PRK",
    "south-korea": "KOR", "japan": "JPN", "taiwan": "TWN", "philippines": "PHL",
    "malaysia": "MYS", "brunei": "BRN", "singapore": "SGP", "thailand": "THA",
    "myanmar": "MMR", "laos": "LAO", "vietnam": "VNM", "cambodia": "KHM",
    "indonesia": "IDN", "timor-leste": "TLS", "australia": "AUS", "papua-new-guinea": "PNG",
    "solomon-islands": "SLB", "vanuatu": "VUT", "fiji": "FJI", "tonga": "TON",
    "samoa": "WSM", "tuvalu": "TUV", "kiribati": "KIR", "nauru": "NRU",
    "marshall-islands": "MHL", "micronesia": "FSM", "palau": "PLW", "united-states": "USA",
    "canada": "CAN", "mexico": "MEX", "guatemala": "GTM", "belize": "BLZ",
    "el-salvador": "SLV", "honduras": "HND", "nicaragua": "NIC", "costa-rica": "CRI",
    "panama": "PAN", "colombia": "COL", "ecuador": "ECU", "peru": "PER",
    "chile": "CHL", "bolivia": "BOL", "argentina": "ARG", "uruguay": "URY",
    "paraguay": "PRY", "brazil": "BRA", "suriname": "SUR", "guyana": "GUY",
    "venezuela": "VEN", "trinidad-and-tobago": "TTO", "grenada": "GRD", "saint-vincent-and-the-grenadines": "VCT",
    "barbados": "BRB", "saint-lucia": "LCA", "dominica": "DMA", "antigua-and-barbuda": "ATG",
    "saint-kitts-and-nevis": "KNA", "dominican-republic": "DOM", "haiti": "HTI", "jamaica": "JAM",
    "cuba": "CUB", "bahamas": "BHS", "gibraltar": "GIB", "aland": "ALD",
    "faroe-islands": "FRO", "dhekelia": "ESB", "akrotiri": "WSB", "hong-kong": "HKG",
    "macau": "MAC", "new-caledonia": "NCL", "french-polynesia": "PYF", "falkland-islands": "FLK",
    "puerto-rico": "PRI", "us-virgin-islands": "VIR", "british-virgin-islands": "VGB", "cayman-islands": "CYM",
    "turks-and-caicos-islands": "TCA", "aruba": "ABW", "curacao": "CUW", "sint-maarten": "SXM",
    "saint-martin": "MAF", "saint-barthelemy": "BLM", "anguilla": "AIA", "montserrat": "MSR",
}
_MAP_UNIT = {
    "france": "FXX", "netherlands": "NLX", "norway": "NOW", "new-zealand": "NZL",
    "reunion": "REU", "mayotte": "MYT", "french-guiana": "GUF", "guadeloupe": "GLP",
    "martinique": "MTQ",
}
_COMPOSITION: dict[str, tuple[tuple[Literal["+", "-"], str, int], ...]] = {
    "ukraine": (("+", "10m_admin_0_disputed_areas", 1159321217),),  # Crimea
    "russia": (("-", "10m_admin_0_disputed_areas", 1159321217),),
    "cyprus": (("+", "10m_admin_0_countries", 1159320531), ("+", "10m_admin_0_countries", 1159320511)),  # N. Cyprus, buffer zone
    "syria": (("+", "10m_admin_0_disputed_areas", 1159320905),),  # Golan
    "israel": (("-", "10m_admin_0_disputed_areas", 1159320905),),
    "morocco": (("-", "10m_admin_0_disputed_areas", 1159321037),),  # Western Sahara's Moroccan-held part
    "western-sahara": (("+", "10m_admin_0_disputed_areas", 1159321037),),
    "somalia": (("+", "10m_admin_0_countries", 1159321259),),  # Somaliland
    "india": (("+", "10m_admin_0_countries", 1159320963),),  # Siachen
    "kazakhstan": (("+", "10m_admin_0_countries", 1159320965),),  # Baikonur
    "cuba": (("+", "10m_admin_0_countries", 1159320529),),  # Guantanamo Bay
}


def _row(layer_name: str, ne_id: int) -> BaseGeometry:
    rows = layer(layer_name)
    return shapely.make_valid(rows[rows.ne_id == ne_id].geometry.iloc[0])


@cache
def country_geometry(id: str) -> BaseGeometry:
    """A country's or territory's recognised-border outline, keyed by its slug id. A stand-in until P2.2's
    countries.yaml and territories.yaml replace it."""
    if id in _MAP_UNIT:
        units = layer("10m_admin_0_map_units")
        base = units[units.gu_a3 == _MAP_UNIT[id]].geometry.iloc[0]
    else:
        rows = layer("10m_admin_0_countries")
        base = rows[rows.adm0_a3 == _ADMIN_0[id]].geometry.iloc[0]
    geometry = shapely.make_valid(base)
    for op, layer_name, ne_id in _COMPOSITION.get(id, ()):
        part = _row(layer_name, ne_id)
        geometry = geometry.union(part) if op == "+" else geometry.difference(part)
    return geometry


@cache
def region_outlines() -> dict[int, BaseGeometry]:
    return {n: unary_union([country_geometry(c) for c in (*members, *TERRITORIES.get(n, ()))])
            for n, (_, members) in REGIONS.items()}


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
    return max(n for n, share in shares.items() if share >= SHORE_MIN_SHARE)


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


def override_errors(features: Iterable[Feature]) -> list[str]:
    """A `region:` override must name a region of the ring (the plan's table until data/curriculum.yaml lands)."""
    return [f"{f.id}: region {f.region} is not in the ring" for f in features
            if f.region is not None and f.region not in REGIONS]


def derive(feature: Feature, geometry: BaseGeometry, regions: Mapping[int, BaseGeometry]) -> Assignment:
    """The feature's region by the plan's rules, then its `region:` override if it has one."""
    if errors := override_errors([feature]):
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
    return "Orientation" if n == ORIENTATION else REGIONS[n][0]


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
    counts = {n: sum(a.region == n for a in assignments.values()) for n in (ORIENTATION, *REGIONS)}
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
