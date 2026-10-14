"""Read-only survey of the Natural Earth political layers for the World Atlas.

Prints the markdown tables behind docs/research/ne-political-layers.md: the 197 state rows
and capitals, territory and dispute outlines, the recognised-border composition, the
point-of-view comparison, NE's stale shapes and the continent rows. Reads vendor/ only.

    uv run python tools/ne_survey.py > build/ne-survey.md
"""

import json
from pathlib import Path

from pyproj import Geod
from shapely import make_valid, unary_union
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry

VENDOR = Path(__file__).resolve().parents[1] / "vendor"
GEOD = Geod(ellps="WGS84")

# 193 UN member states (ISO 3166-1 alpha-3), plus the four extra country cards.
UN_MEMBERS = """
AFG ALB DZA AND AGO ATG ARG ARM AUS AUT AZE BHS BHR BGD BRB BLR BEL BLZ BEN BTN BOL BIH BWA BRA BRN
BGR BFA BDI CPV KHM CMR CAN CAF TCD CHL CHN COL COM COG CRI CIV HRV CUB CYP CZE PRK COD DNK DJI DMA
DOM ECU EGY SLV GNQ ERI EST SWZ ETH FJI FIN FRA GAB GMB GEO DEU GHA GRC GRD GTM GIN GNB GUY HTI HND
HUN ISL IND IDN IRN IRQ IRL ISR ITA JAM JPN JOR KAZ KEN KIR KWT KGZ LAO LVA LBN LSO LBR LBY LIE LTU
LUX MDG MWI MYS MDV MLI MLT MHL MRT MUS MEX FSM MCO MNG MNE MAR MOZ MMR NAM NRU NPL NLD NZL NIC NER
NGA MKD NOR OMN PAK PLW PAN PNG PRY PER PHL POL PRT QAT KOR MDA ROU RUS RWA KNA LCA VCT WSM SMR STP
SAU SEN SRB SYC SLE SGP SVK SVN SLB SOM ZAF SSD ESP LKA SDN SUR SWE CHE SYR TJK THA TLS TGO TON TTO
TUN TUR TKM TUV UGA UKR ARE GBR TZA USA URY UZB VUT VEN VNM YEM ZMB ZWE
""".split()
EXTRA_STATES = ["VAT", "PSE", "KOS", "TWN"]
# ISO code -> NE ADM0_A3 where they differ.
NE_CODE = {"SSD": "SDS", "PSE": "PSX"}

# States whose admin_0 row carries overseas parts: use the map unit for the mainland.
MAP_UNIT_SOURCE = {"FRA": "FXX", "NLD": "NLX", "NOR": "NOW", "NZL": "NZL"}

# Recognised-border composition, by decision: (layer, ne_id) rows added (+) or removed (-).
COMPOSITION: dict[str, list[tuple[str, str, int]]] = {
    "UKR": [("+", "DA", 1159321217)],
    "RUS": [("-", "DA", 1159321217)],
    "GEO": [],
    "MDA": [],
    "CYP": [("+", "A0", 1159320531), ("+", "A0", 1159320511)],
    "SYR": [("+", "DA", 1159320905)],
    "ISR": [("-", "DA", 1159320905)],
    "MAR": [("-", "DA", 1159321037)],
    "SOM": [("+", "A0", 1159321259)],
    "IND": [("+", "A0", 1159320963)],
    "KAZ": [("+", "A0", 1159320965)],
    "CUB": [("+", "A0", 1159320529)],
}
# Why the rows outside the decision's nine states move.
REASONS = {
    ("A0", 1159320963): "Siachen Glacier: administered by India; Kashmir parts stay with administrators",
    ("A0", 1159320965): "Baykonur: leased to Russia, Kazakh sovereignty",
    ("A0", 1159320529): "Guantanamo Bay: leased to the US, Cuban sovereignty",
}
# Inside an admin_0 row already, so no change: shown for the record.
ALREADY_INSIDE = {
    "UKR": [1763286545, 1763286547],
    "GEO": [1159320785, 1159320787],
    "MDA": [1159321047],
    "RUS": [1159321213],
}
# Rows the decision leaves open, shown with areas so P2 can choose.
OPEN_ROWS = {
    "ISR": [1159320907, 1746265961, 1159320911, 1159320909, 1746265963],
}

# Capital notes are keyed by ISO code.
# One official seat where NE tags more than one Admin-0 capital.
CAPITAL_PICK = {
    "BOL": (1159151095, "Sucre (constitutional); La Paz 1159151133 is the seat of government"),
    "ZAF": (1159150661, "Pretoria (executive); Cape Town 1159151583, Bloemfontein 1159150659; Johannesburg 1159151515 is mis-tagged"),
    "CIV": (1159150999, "Yamoussoukro (official); Abidjan 1159151439 is de facto"),
    "MMR": (1159151179, "Naypyidaw; Yangon 1159151477 is the former capital (tagged, ADM0CAP 0)"),
}
# Single tag, but worth a decision or a fix in P2.
CAPITAL_FLAGS = {
    "BEN": "tag is Cotonou (seat of government); constitutional capital Porto-Novo is `Admin-0 capital alt` 1159150345",
    "TZA": "tag is Dar es Salaam; official capital Dodoma is `Admin-0 capital alt` 1159149731",
    "LKA": "tag is Colombo; official capital Sri Jayawardenepura Kotte is `Admin-0 capital alt` 1159149593",
    "KAZ": "NE name `Nur-Sultan` is stale: renamed Astana in 2022",
    "ISR": "Jerusalem: NE notes de facto capital; status contested. Tel Aviv is `Admin-0 capital alt` 1159151417",
    "SSD": "Juba is tagged `Admin-0 capital` but ADM0CAP 0; code SSD in populated_places",
    "SWZ": "Mbabane (administrative); Lobamba is `Admin-0 capital alt` 1159146343",
}

GAP_NOTES = {
    "PSE": "no `Admin-0 capital` row; Ramallah is `Admin-0 region capital` 1159121947; East Jerusalem has no point",
    "NRU": "no populated_places row for Nauru at all (Yaren, the seat of government, is missing)",
}

# Territory and dispute cards: (name, [(layer, ne_id)]).
TERRITORIES = [
    ("Greenland", [("A0", 1159320551)]),
    ("Faroe Islands", [("A0", 1159320549)]),
    ("Svalbard", [("MU", 1159321119)]),
    ("Hong Kong", [("A0", 1159320473)]),
    ("Macau", [("A0", 1159320475)]),
    ("Puerto Rico", [("A0", 1159321363)]),
    ("Guam", [("A0", 1159321359)]),
    ("Gibraltar", [("A0", 1159320719)]),
    ("Falkland Islands", [("A0", 1159320711)]),
    ("Bermuda", [("A0", 1159320705)]),
    ("Cayman Islands", [("A0", 1159320707)]),
    ("British Indian Ocean Territory", [("A0", 1159320723)]),
    ("Isle of Man", [("A0", 1159320721)]),
    ("Jersey", [("A0", 1159320725)]),
    ("Guernsey", [("A0", 1159320715)]),
    ("New Caledonia", [("A0", 1159320641)]),
    ("French Polynesia", [("A0", 1159320643)]),
    ("French Guiana", [("MU", 1159320655)]),
    ("Réunion", [("MU", 1159320661)]),
    ("Guadeloupe", [("MU", 1159320653)]),
    ("Martinique", [("MU", 1159320657)]),
    ("Aruba", [("A0", 1159321097)]),
    ("Curaçao", [("A0", 1159321099)]),
]
DISPUTES = [
    ("Crimea", [("DA", 1159321217)]),
    ("Kashmir: Indian-administered", [("DA", 1159320869), ("DA", 1159320865), ("A0", 1159320963)]),
    ("Kashmir: Pakistani-administered", [("DA", 1159321157), ("DA", 1159321155)]),
    ("Aksai Chin", [("DA", 1159320487), ("DA", 1159320485)]),
    ("Arunachal Pradesh", [("DA", 1159320857)]),
    ("Western Sahara", [("DA", 1159321037), ("A0", 1159321223)]),
    ("Golan Heights", [("DA", 1159320905)]),
    ("Abkhazia", [("DA", 1159320785)]),
    ("South Ossetia", [("DA", 1159320787)]),
    ("Transnistria", [("DA", 1159321047)]),
    ("Northern Cyprus", [("A0", 1159320531)]),
    ("Somaliland", [("A0", 1159321259)]),
    ("Kuril Islands", [("DA", 1159321213)]),
    ("Spratly Islands", [("A0", 1159321165)]),
    ("Essequibo", [("DA", 1159320821)]),
]

# Where each contested unit goes under the decision, for the point-of-view check.
POV_EXPECT = [
    ("DA", 1159321217, "UKR"),  # Crimea
    ("DA", 1763286545, "UKR"),  # Donetsk PR
    ("DA", 1763286547, "UKR"),  # Luhansk PR
    ("DA", 1159320785, "GEO"),  # Abkhazia
    ("DA", 1159320787, "GEO"),  # South Ossetia
    ("DA", 1159321047, "MDA"),  # Transnistria
    ("DA", 1159320905, "SYR"),  # Golan
    ("DA", 1159321213, "RUS"),  # Kurils
    ("DA", 1159320869, "IND"),  # Jammu and Kashmir
    ("DA", 1159320857, "IND"),  # Arunachal
    ("DA", 1159321157, "PAK"),  # Azad Kashmir
    ("DA", 1159321155, "PAK"),  # Gilgit-Baltistan
    ("DA", 1159320487, "CHN"),  # Aksai Chin
    ("DA", 1159320485, "CHN"),  # Shaksam
    ("DA", 1159321037, "SAH"),  # W. Sahara, Moroccan-held
    ("DA", 1159320821, "GUY"),  # Essequibo
    ("A0", 1159321223, "SAH"),  # W. Sahara, SADR-held
    ("A0", 1159320531, "CYP"),  # N. Cyprus
    ("A0", 1159321259, "SOM"),  # Somaliland
    ("A0", 1159321007, "KOS"),  # Kosovo
    ("A0", 1159321335, "TWN"),  # Taiwan
    ("A0", 1159320899, "PSX"),  # Palestine
    ("A0", 1159320963, "IND"),  # Siachen
]

STALE = [("DA", 1159320385), ("DA", 1763286545), ("DA", 1763286547), ("A0", 1159321259)]
STALE_LINE_TERMS = ("Nagorno-Karabakh", "Donetsk", "Luhansk", "Donbass")


def load(name: str) -> list[dict]:
    return json.loads((VENDOR / f"{name}.geojson").read_text())["features"]


def km2(geom: BaseGeometry) -> float:
    return abs(GEOD.geometry_area_perimeter(geom)[0]) / 1e6


def ne_id(props: dict) -> int:
    return props["NE_ID"]


class Layers:
    def __init__(self) -> None:
        self.raw = {
            "A0": load("ne_10m_admin_0_countries"),
            "MU": load("ne_10m_admin_0_map_units"),
            "DA": load("ne_10m_admin_0_disputed_areas"),
        }
        self.places = load("ne_10m_populated_places")
        self.lines = load("ne_10m_admin_0_boundary_lines_disputed_areas")
        self.land_lines = load("ne_10m_admin_0_boundary_lines_land")
        self.regions = load("ne_10m_geography_regions_polys")
        self.props = {(k, ne_id(f["properties"])): f["properties"] for k, fs in self.raw.items() for f in fs}
        self._geoms: dict[tuple[str, int], BaseGeometry] = {}

    def geom(self, layer: str, nid: int) -> BaseGeometry:
        key = (layer, nid)
        if key not in self._geoms:
            feat = next(f for f in self.raw[layer] if ne_id(f["properties"]) == nid)
            self._geoms[key] = make_valid(shape(feat["geometry"]))
        return self._geoms[key]

    def name(self, layer: str, nid: int) -> str:
        p = self.props[(layer, nid)]
        return p["BRK_NAME"] if layer == "DA" else p["NAME"]

    def by_code(self, layer: str, field: str, code: str) -> dict:
        return next(f["properties"] for f in self.raw[layer] if f["properties"][field] == code)


def inside(part: BaseGeometry, base: BaseGeometry) -> float:
    return km2(part.intersection(base)) / km2(part)


def ref(layer: str, nid: int) -> str:
    return f"{layer} `{nid}`"


def state_source(L: Layers, iso: str) -> tuple[str, int, list[tuple[str, str, int]]]:
    code = NE_CODE.get(iso, iso)
    if code in MAP_UNIT_SOURCE:
        return "MU", ne_id(L.by_code("MU", "GU_A3", MAP_UNIT_SOURCE[code])), COMPOSITION.get(code, [])
    return "A0", ne_id(L.by_code("A0", "ADM0_A3", code)), COMPOSITION.get(code, [])


def capital(L: Layers, iso: str) -> tuple[int | None, str, str]:
    code = NE_CODE.get(iso, iso)
    if iso in CAPITAL_PICK:
        nid, note = CAPITAL_PICK[iso]
        p = next(f["properties"] for f in L.places if f["properties"]["NE_ID"] == nid)
        return nid, p["NAME"], note
    tagged = [f["properties"] for f in L.places
              if f["properties"]["FEATURECLA"] == "Admin-0 capital" and f["properties"]["ADM0_A3"] in (iso, code)]
    if len(tagged) == 1:
        return tagged[0]["NE_ID"], tagged[0]["NAME"], CAPITAL_FLAGS.get(iso, "")
    if not tagged:
        return None, "", "no `Admin-0 capital` row"
    names = ", ".join(f"{p['NAME']} {p['NE_ID']}" for p in tagged)
    return None, "", f"several tagged rows and no pick: {names}"


def section_states(L: Layers) -> None:
    states = UN_MEMBERS + EXTRA_STATES
    assert len(UN_MEMBERS) == 193 and len(set(states)) == 197
    print("## (a) States\n")
    print("| # | State | ISO | Outline source | Capital | populated_places `ne_id` | Note |")
    print("|---|---|---|---|---|---|---|")
    gaps = []
    rows = []
    for iso in states:
        layer, nid, ops = state_source(L, iso)
        src = ref(layer, nid) + "".join(f" {op} {ref(lyr, n)}" for op, lyr, n in ops)
        cap_id, cap_name, note = capital(L, iso)
        note = GAP_NOTES.get(iso, note)
        if cap_id is None:
            gaps.append((iso, note))
        rows.append((L.props[(layer, nid)]["NAME_LONG"], iso, src, cap_name, cap_id or "—", note))
    for i, (name, iso, src, cap, cid, note) in enumerate(sorted(rows, key=lambda r: r[0].casefold()), 1):
        print(f"| {i} | {name} | {iso} | {src} | {cap} | {cid} | {note} |")
    print(f"\n{len(rows)} states; {len(gaps)} without a capital `ne_id`: "
          + "; ".join(f"{iso}: {n}" for iso, n in gaps) + "\n")


def union_of(L: Layers, parts: list[tuple[str, int]]) -> BaseGeometry:
    return unary_union([L.geom(lyr, n) for lyr, n in parts])


def section_cards(L: Layers) -> None:
    for title, items in (("Territories", TERRITORIES), ("Disputes", DISPUTES)):
        print(f"### {title}\n")
        print("| Card | Rows (union) | NE names | Area km² |")
        print("|---|---|---|---|")
        for card, parts in items:
            rows = " + ".join(ref(lyr, n) for lyr, n in parts)
            names = " + ".join(L.name(lyr, n) for lyr, n in parts)
            print(f"| {card} | {rows} | {names} | {km2(union_of(L, parts)):,.0f} |")
        print()
    jk, dem = L.geom("DA", 1159320869), L.geom("DA", 1159320865)
    sia = L.geom("A0", 1159320963)
    aru = L.geom("DA", 1159320857)
    print(f"Adjacency checks: Demchok touches J&K {dem.distance(jk) < 1e-6}; "
          f"Siachen touches J&K {sia.distance(jk) < 1e-6}; "
          f"Tirpani touches Arunachal {L.geom('DA', 1159320859).distance(aru) < 1e-6}.\n")


def section_composition(L: Layers) -> None:
    print("## (c) Recognised-border composition\n")
    print("| State | Base row | Base km² | Change | Row km² | Result km² |")
    print("|---|---|---|---|---|---|")
    for code in COMPOSITION:
        layer, base_id, ops = state_source(L, code)
        geom = base = L.geom(layer, base_id)
        changes = []
        for op, lyr, n in ops:
            part = L.geom(lyr, n)
            share = inside(part, base)
            assert (op == "+" and share < 0.001) or (op == "-" and share > 0.999), (code, n, share)
            geom = geom.union(part) if op == "+" else geom.difference(part)
            changes.append((f"{op} {ref(lyr, n)} {L.name(lyr, n)}", f"{km2(part):,.0f}"))
        for mark, label, ids in (("0", "no change", ALREADY_INSIDE), ("?", "open", OPEN_ROWS)):
            for n in ids.get(code, []):
                part = L.geom("DA", n)
                changes.append((f"{mark} {ref('DA', n)} {L.name('DA', n)} ({label}; {inside(part, base):.1%} inside base)",
                                f"{km2(part):,.0f}"))
        expected = km2(base) + sum(km2(L.geom(lyr, n)) * (1 if op == "+" else -1) for op, lyr, n in ops)
        assert abs(km2(geom) - expected) < 1, (code, km2(geom), expected)
        if not changes:
            changes = [("none", "")]
        for i, (c, a) in enumerate(changes):
            head = (f"{L.name(layer, base_id)}", ref(layer, base_id), f"{km2(base):,.0f}") if i == 0 else ("", "", "")
            tail = f"{km2(geom):,.0f}" if i == len(changes) - 1 else ""
            print(f"| {head[0]} | {head[1]} | {head[2]} | {c} | {a} | {tail} |")
    print()
    a0 = [(ne_id(f["properties"]), L.geom("A0", ne_id(f["properties"]))) for f in L.raw["A0"]]
    partial = []
    for f in L.raw["DA"]:
        n = ne_id(f["properties"])
        part = L.geom("DA", n)
        best = max((inside(part, g) for _, g in a0 if g.intersects(part)), default=0.0)
        if best < 0.999:
            partial.append(f"{L.name('DA', n)} `{n}` {best:.1%}")
    print(f"DA rows at least 99.9% inside one A0 row: {len(L.raw['DA']) - len(partial)} of {len(L.raw['DA'])}. "
          f"The rest, with their best share: {'; '.join(partial)}.\n")
    for (lyr, n), why in REASONS.items():
        print(f"- {ref(lyr, n)}: {why}")
    print()
    codes = {"CYN", "CNM", "SOL", "KAS", "KAB", "USG"}
    print("Land-boundary segments touching composed rows "
          "(`ne_10m_admin_0_boundary_lines_land`):\n")
    print("| `ne_id` | Class | Left / right | km |")
    print("|---|---|---|---|")
    for f in L.land_lines:
        p = f["properties"]
        pair = {p["ADM0_A3_L"], p["ADM0_A3_R"]}
        crimea = pair == {"RUS", "UKR"} and p["FEATURECLA"].startswith("Disputed")
        if pair & codes or crimea or pair in ({"ISR", "SYR"}, {"MAR", "SAH"}):
            km = GEOD.geometry_length(shape(f["geometry"])) / 1e3
            print(f"| {p['ne_id']} | {p['FEATURECLA']} | {p['ADM0_A3_L']} / {p['ADM0_A3_R']} | {km:,.0f} |")
    print()


def section_pov(L: Layers) -> None:
    sample = L.props[("DA", 1159321217)]
    povs = sorted(k[-2:] for k in sample if k.startswith("ADM0_A3_") and len(k) == 10)
    print("## (d) Point-of-view check\n")
    print("| POV | Matches | Mismatches (unit → POV owner) |")
    print("|---|---|---|")
    results = []
    for pov in povs:
        miss = []
        for lyr, n, want in POV_EXPECT:
            got = L.props[(lyr, n)][f"ADM0_A3_{pov}"]
            if got != want:
                miss.append(f"{ref(lyr, n)} {L.name(lyr, n)} → {got}")
        results.append((len(miss), pov, miss))
    for nmiss, pov, miss in sorted(results):
        print(f"| {pov} | {len(POV_EXPECT) - nmiss}/{len(POV_EXPECT)} | {'; '.join(miss)} |")
    print()


def section_stale(L: Layers) -> None:
    print("## (e) Stale shapes\n")
    print("| Layer `ne_id` | NE name | Type | km² | NE note |")
    print("|---|---|---|---|---|")
    for lyr, n in STALE:
        p = L.props[(lyr, n)]
        print(f"| {ref(lyr, n)} | {L.name(lyr, n)} | {p['TYPE']} | {km2(L.geom(lyr, n)):,.0f} | {p['NOTE_BRK']} |")
    print()
    print("| Lines `ne_id` | Class | Name | km |")
    print("|---|---|---|---|")
    for f in L.lines:
        p = f["properties"]
        text = " ".join(str(p[k]) for k in ("NAME", "COMMENT", "BRK_NAME_L", "BRK_NAME_R") if p[k])
        if any(t in text for t in STALE_LINE_TERMS):
            km = GEOD.geometry_length(shape(f["geometry"])) / 1e3
            print(f"| {p['ne_id']} | {p['FEATURECLA']} | {p['NAME']} | {km:,.0f} |")
    print()
    sol = L.geom("A0", 1159321259)
    for f in L.places:
        p = f["properties"]
        if p["NAME"] in ("Laascaanood", "Ceerigaabo"):
            inside = sol.contains(Point(f["geometry"]["coordinates"]))
            print(f"- populated_places `{p['NE_ID']}` {p['NAME']}: ADM0_A3 {p['ADM0_A3']}, inside A0 Somaliland: {inside}")
    print()


def section_continents(L: Layers) -> None:
    print("## (f) Continents\n")
    print("| `ne_id` | NAME | REGION | km² | bbox |")
    print("|---|---|---|---|---|")
    conts = [(f["properties"], make_valid(shape(f["geometry"])))
             for f in L.regions if f["properties"]["FEATURECLA"] == "Continent"]
    for p, g in conts:
        bbox = ", ".join(f"{v:.0f}" for v in g.bounds)
        print(f"| {p['NE_ID']} | {p['NAME']} | {p['REGION']} | {km2(g):,.0f} | {bbox} |")
    probes = {n: next(f for f in L.places if f["properties"]["NE_ID"] == n) for n in
              (1159151171, 1159150663, 1159151699, 1159151577, 1159151309, 1159150587, 1159151609,
               1159151599, 1159150835, 1159151347, 1159150939, 1159151585, 1159151579, 1159150961,
               1159151123, 1159151119, 1159151603, 1159150667)}
    print()
    for n, f in probes.items():
        pt = Point(f["geometry"]["coordinates"])
        hit = [p["NAME"] for p, g in conts if g.buffer(0.05).contains(pt)]
        print(f"- {f['properties']['NAME']} (`{n}`) is in: {', '.join(hit) or 'none'}")
    print()


def main() -> None:
    L = Layers()
    section_states(L)
    print("## (b) Territory and dispute outlines\n")
    section_cards(L)
    section_composition(L)
    section_pov(L)
    section_stale(L)
    section_continents(L)


if __name__ == "__main__":
    main()
