"""Each state's, territory's and dispute's recognised-border outline, composed from Natural Earth rows. Shared by the
adjacency graph and the region derivation; P2.2's countries.yaml and territories.yaml replace the recipe tables, and
`outline(id)` keeps the same interface. Ids are curriculum.yaml's slugs."""

from functools import cache

import shapely
from shapely.geometry.base import BaseGeometry

from geofeat import ne

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

# Territory and dispute cards, from docs/research/ne-political-layers.md (b). A dispute's land is mostly inside a
# state's outline already; only Western Sahara's is in none.
TERRITORY_SOURCES: dict[str, str] = {
    "gibraltar": "A0 1159320719",
    "isle-of-man": "A0 1159320721",
    "jersey": "A0 1159320725",
    "guernsey": "A0 1159320715",
    "faroe-islands": "A0 1159320549",
    "svalbard": "MU 1159321119",
    "reunion": "MU 1159320661",
    "british-indian-ocean-territory": "A0 1159320723",
    "hong-kong": "A0 1159320473",
    "macau": "A0 1159320475",
    "guam": "A0 1159321359",
    "new-caledonia": "A0 1159320641",
    "french-polynesia": "A0 1159320643",
    "greenland": "A0 1159320551",
    "bermuda": "A0 1159320705",
    "falkland-islands": "A0 1159320711",
    "french-guiana": "MU 1159320655",
    "aruba": "A0 1159321097",
    "curacao": "A0 1159321099",
    "puerto-rico": "A0 1159321363",
    "cayman-islands": "A0 1159320707",
    "guadeloupe": "MU 1159320653",
    "martinique": "MU 1159320657",
}
DISPUTE_SOURCES: dict[str, str] = {
    "crimea": "DA 1159321217",
    "transnistria": "DA 1159321047",
    "abkhazia": "DA 1159320785",
    "south-ossetia": "DA 1159320787",
    "northern-cyprus": "A0 1159320531",
    "golan-heights": "DA 1159320905",
    "somaliland": "A0 1159321259",
    "western-sahara": "DA 1159321037 + A0 1159321223",
    "kashmir-indian-administered": "DA 1159320869 + DA 1159320865 + A0 1159320963",
    "kashmir-pakistani-administered": "DA 1159321157 + DA 1159321155",
    "arunachal-pradesh": "DA 1159320857",
    "aksai-chin": "DA 1159320487 + DA 1159320485",
    "kuril-islands": "DA 1159321213",
    "spratly-islands": "A0 1159321165",
    "essequibo": "DA 1159320821",
}
RECIPES = SOURCES | TERRITORY_SOURCES | DISPUTE_SOURCES



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
    """A state's, territory's or dispute's recognised-border outline, composed from its Natural Earth rows."""
    base, plus, minus = _parse(RECIPES[country_id])
    geometry = shapely.union_all([_row(*base), *(_row(*r) for r in plus)])
    if minus:
        geometry = geometry.difference(shapely.union_all([_row(*r) for r in minus]))
    return geometry


def outlines() -> dict[str, BaseGeometry]:
    return {i: outline(i) for i in sorted(SOURCES)}
