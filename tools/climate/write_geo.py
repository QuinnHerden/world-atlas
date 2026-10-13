"""Write the climate geometry files from the derived JSON in $CLIMATE_DATA plus hand-placed coordinates.

usage: write_geo.py [SECTION ...]   sections: storms highs winds itcz monsoons currents (default: all)
Set GEOMETRY_OUT to write somewhere other than geometry/, e.g. to diff a re-run against the committed files.
`storms`, `highs` and `winds` need the outputs of contour.py, highs.py and trace_winds.py; the rest is self-contained.
"""
import json
import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import shapely
from shapely.geometry import Polygon, mapping
from shapely.geometry.polygon import orient

from common import DATA, GEOMETRY, NE_50M_LAND

OUT = Path(os.environ.get("GEOMETRY_OUT", GEOMETRY))
TOOLS = "tools/README.md"
IBT_REF = "NOAA NCEI IBTrACS v04r01, doi:10.25921/82ty-9e16 (accessed 2026-10-12)"
ICOADS_REF = "NOAA PSL ICOADS 2-degree enhanced monthly LTM 1971-2000, ERDDAP esrlIcoads2gec71 (accessed 2026-10-12)"
GDP_REF = ("NOAA AOML GDP drifter annual-mean climatology (Laurindo, Mariano & Lumpkin 2017, doi:10.1016/j.dsr.2017.04.009; "
           "dataset doi:10.7266/N7SJ1HN5; accessed 2026-10-12)")
CPC_REF = "NOAA CPC Intertropical Front climatology"


def feat(source: str, geom: dict, method: str, refs: list[str]) -> dict:
    return {"type": "Feature", "properties": {"source": source, "method": method, "refs": refs}, "geometry": geom}


def line(coords) -> dict:
    return {"type": "LineString", "coordinates": [[round(x, 2), round(y, 2)] for x, y in coords]}


def poly(p: Polygon) -> dict:
    return json.loads(json.dumps(mapping(orient(p, 1.0)), default=list).replace("(", "[").replace(")", "]"))


def rounded(g):
    return shapely.set_precision(g, 0.01)


def write(name: str, features: list[dict]) -> None:
    lines = ",\n".join("    " + json.dumps(f, ensure_ascii=False) for f in features)
    (OUT / f"{name}.geojson").write_text('{\n  "type": "FeatureCollection",\n  "features": [\n' + lines + "\n  ]\n}\n")


def storms() -> None:
    ibt = ("NOAA NCEI IBTrACS v04r01 (public domain), {basin} {what}, seasons 1971-2020: 6-hourly fixes binned on a "
           "{res} deg grid, 1-2-1 smoothed, outer contour at 15% of peak density, closed and simplified by script. "
           "A climatological track-density envelope, not any single storm.")
    for name, (f, kw) in {
        "atlantic-hurricane-belt": ("na_hur", dict(basin="North Atlantic basin", what="hurricane-strength fixes (>= 64 kt)", res="2.5")),
        "typhoon-alley": ("wp_ty", dict(basin="Western Pacific basin", what="typhoon-strength fixes (>= 64 kt)", res="2.5")),
        "bay-of-bengal-cyclones": ("bb", dict(basin="North Indian basin, Bay of Bengal sub-basin",
                                              what="cyclonic-storm-strength fixes (>= 34 kt)", res="1.25")),
    }.items():
        ring = json.loads((DATA / f"{f}.poly.json").read_text())
        write(name, [feat(ibt.format(**kw), poly(Polygon(ring)), "pd-dataset", [IBT_REF, TOOLS])])


def highs() -> None:
    src = ("NOAA PSL ICOADS 2-degree enhanced monthly long-term mean 1971-2000 (public domain, via NOAA ERD ERDDAP "
           "esrlIcoads2gec71): annual-mean sea-level pressure contoured at 1018 hPa between 10 and 48 deg N/S, closed and "
           "smoothed, clipped to the sea with Natural Earth 50m land and simplified by script. Marine data only, so the "
           "cells stop at the coast; the antimeridian splits the North Pacific cell in two.")
    land50 = shapely.unary_union(gpd.read_file(NE_50M_LAND).cx[-180:180, -50:50].geometry.values)
    parts = []
    for c in json.loads((DATA / "highs.json").read_text()):
        g = Polygon(c).buffer(0).difference(land50).buffer(-0.5).buffer(1.0).buffer(-0.5).simplify(0.4)
        g = max(getattr(g, "geoms", [g]), key=lambda x: x.area)
        parts.append(rounded(Polygon(g.exterior)))
    write("subtropical-highs", [feat(src, poly(h), "pd-dataset", [ICOADS_REF, "Natural Earth 50m land", TOOLS]) for h in parts])


def winds() -> None:
    wsrc = ("NOAA PSL ICOADS 2-degree enhanced monthly long-term mean 1971-2000 (public domain, via NOAA ERD ERDDAP "
            "esrlIcoads2gec71): streamline of the annual-mean surface wind, traced by script for about 1900 km from a "
            "seed at 37-49 N or 43-47 S. Seed spacing is a drawing choice.")
    gap = ("Hand-drawn west-to-east segment at 46-47 S across the data-sparse southeast Pacific, where ICOADS has too few "
           "ship reports to trace a streamline; placed to match the neighbouring traced westerly segments. Schematic.")
    features = []
    for traced in json.loads((DATA / "westerlies.json").read_text()):
        if len(traced) < 3:  # the trace died in the data gap: replace it with a hand-drawn segment
            features.append(feat(gap, line([(-120, -46.5), (-109, -47), (-98, -47.5)]), "hand-drawn", [ICOADS_REF, TOOLS]))
        else:
            features.append(feat(wsrc, line(traced), "pd-dataset", [ICOADS_REF, TOOLS]))
    write("westerlies", features)
    tsrc = ("NOAA PSL ICOADS 2-degree enhanced monthly long-term mean 1971-2000 (public domain, via NOAA ERD ERDDAP "
            "esrlIcoads2gec71): streamline of the annual-mean surface wind, traced by script for up to 1800 km from a seed "
            "at 17-23 N/S and stopped 6 deg from the equator. The north Indian Ocean is left out because its winds are monsoonal.")
    write("trade-winds", [feat(tsrc, line(t), "pd-dataset", [ICOADS_REF, TOOLS]) for t in json.loads((DATA / "trades.json").read_text())])


def itcz() -> None:
    centre = [(-180, 7), (-160, 7), (-140, 9), (-120, 11), (-100, 12), (-90, 10), (-80, 9), (-70, 10), (-60, 9), (-50, 7),
              (-40, 8), (-30, 10), (-20, 12), (-15, 15), (-10, 18), (0, 19), (10, 18), (20, 16.5), (30, 15), (40, 16),
              (50, 20), (60, 25), (70, 27), (80, 25), (90, 23), (100, 20), (110, 18), (120, 17), (130, 16), (140, 13),
              (150, 10), (160, 8), (170, 7), (180, 7)]
    xs = np.arange(-180, 180.5, 2.5)
    ys = np.interp(xs, [c[0] for c in centre], [c[1] for c in centre])
    ring = [(x, y + 3) for x, y in zip(xs, ys)] + [(x, y - 3) for x, y in zip(xs[::-1], ys[::-1])]
    src = ("July ITCZ / near-equatorial trough, a 6-deg band around a centre line. Over the oceans the centre line follows "
           "the July surface convergence (northerly-to-southerly wind reversal) in the NOAA PSL ICOADS 2-degree monthly "
           "long-term mean 1971-2000 (public domain): about 6-10 N in the central/west Pacific and Atlantic, 10-14 N in the "
           "east Pacific. Over land it is schematic: about 18-19 N over West Africa after NOAA CPC's July Intertropical Front "
           "climatology (16.6 N mean for 15W-35E, 18.7 N for 10W-10E), and 25-27 N along the South Asian monsoon trough "
           "and Pakistan heat low per standard textbook July charts.")
    write("itcz", [feat(src, poly(Polygon(ring)), "hand-drawn", [ICOADS_REF, CPC_REF, TOOLS])])


def monsoons() -> None:
    refs = [ICOADS_REF, TOOLS]
    sam = ("Over the sea: streamline of the July surface wind in the NOAA PSL ICOADS 2-degree monthly long-term mean "
           "1971-2000 (public domain), traced by script and simplified. {land}")
    write("south-asian-monsoon", [
        feat(sam.format(land="Arabian Sea branch: cross-equatorial Somali jet turning onto the Konkan coast near 19 N; the short "
                             "inland end is schematic."),
             line([(49.6, -2.5), (49.9, 0.6), (51.8, 3.7), (54.1, 6.4), (56.7, 9.0), (59.3, 11.5), (62.1, 13.9), (65.2, 15.9),
                   (68.6, 17.4), (72.2, 18.6), (75.5, 19.8)]), "hand-drawn", refs),
        feat(sam.format(land="Bay of Bengal branch: northward over the Bay to the Bengal coast; the turn north-west up the "
                             "Ganges plain along the monsoon trough is schematic, after IMD and standard textbook July charts."),
             line([(79.0, 4.5), (82.2, 5.2), (85.2, 7.1), (87.9, 9.5), (89.8, 13.0), (90.5, 17.0), (90.6, 20.5), (89.8, 23.2),
                   (87.5, 25.2), (84.0, 26.3), (80.5, 27.5)]), "hand-drawn", refs),
    ])
    eam = ("Over the sea: streamline of the June surface wind in the NOAA PSL ICOADS 2-degree monthly long-term mean 1971-2000 "
           "(public domain), traced by script and simplified. {land} June is the Meiyu/Baiu season (mid-June to mid-July over the "
           "Yangtze valley and Japan); the front itself is not drawn.")
    write("east-asian-monsoon", [
        feat(eam.format(land="South China Sea branch onto the south China coast; the run north-east inland toward the Yangtze is schematic."),
             line([(110.0, 8.0), (112.2, 9.6), (114.1, 11.5), (115.7, 13.8), (116.7, 16.3), (117.3, 19.0), (117.0, 21.6),
                   (117.8, 25.0), (119.5, 28.5)]), "hand-drawn", refs),
        feat(eam.format(land="Philippine Sea branch east of Taiwan toward the Yangtze mouth; the short end over land is schematic."),
             line([(125.0, 15.0), (124.0, 17.5), (123.0, 20.0), (123.1, 22.7), (122.8, 25.4), (122.4, 28.1), (121.1, 30.5),
                   (119.5, 32.5)]), "hand-drawn", refs),
        feat(eam.format(land="Western-Pacific branch along the west flank of the North Pacific High onto southern Japan and the Korea Strait."),
             line([(135.0, 18.0), (132.8, 19.7), (131.3, 22.0), (130.9, 24.6), (131.2, 27.3), (131.9, 30.0), (132.4, 32.6),
                   (132.3, 35.3)]), "hand-drawn", refs),
    ])
    wam = ("Over the Gulf of Guinea: streamline of the August surface wind in the NOAA PSL ICOADS 2-degree monthly long-term "
           "mean 1971-2000 (public domain), traced by script and simplified. Over land it is schematic: south-westerly inflow "
           "ending short of the August Intertropical Front at about 19-20 N (NOAA CPC climatology), i.e. across the Sahel.")
    refs = [ICOADS_REF, CPC_REF, TOOLS]
    write("west-african-monsoon", [
        feat(wam, line([(-18.0, 0.3), (-18.9, 2.4), (-19.3, 4.6), (-19.1, 6.9), (-17.9, 8.7), (-16.0, 10.1), (-13.5, 11.8),
                        (-10.5, 14.0), (-7.5, 16.0)]), "hand-drawn", refs),
        feat(wam, line([(-6.4, -2.5), (-6.4, 1.3), (-6.0, 4.0), (-4.5, 7.5), (-2.5, 11.0), (-0.5, 14.5), (1.0, 16.5)]), "hand-drawn", refs),
        feat(wam, line([(4.8, -2.8), (5.0, -0.5), (5.6, 1.7), (6.8, 3.6), (7.8, 6.5), (9.0, 10.0), (10.5, 13.5), (12.0, 16.0)]),
             "hand-drawn", refs),
    ])


def currents() -> None:
    gdp = "NOAA AOML Global Drifter Program annual-mean near-surface velocity climatology (Laurindo, Mariano & Lumpkin 2017; public domain)"
    refs = [GDP_REF, TOOLS]
    write("gulf-stream", [
        feat(f"Florida Current and Gulf Stream to the Tail of the Grand Banks: streamline traced by script through the {gdp}, "
             "smoothed to about 1 deg and simplified (separation from the shelf at Cape Hatteras, 35.4 N).",
             line([(-81.5, 24.3), (-80.1, 26.5), (-80.0, 29.1), (-79.6, 31.7), (-77.0, 33.3), (-74.9, 35.4), (-72.3, 37.1),
                   (-69.1, 37.9), (-65.7, 38.3), (-62.5, 39.2), (-59.1, 39.8), (-55.6, 40.1), (-51.5, 40.3), (-48.5, 41.5)]),
             "pd-dataset", refs),
        feat(f"North Atlantic Current and Drift: hand-traced simplified axis, checked against streamlines of the {gdp}, which "
             "show it north along the Grand Banks to the Northwest Corner near 51 N 43 W, east near 50-52 N across the "
             "Mid-Atlantic Ridge, then north-east past Rockall and through the Faroe-Shetland Channel into the Norwegian Sea. "
             "The mean flow here is broad and eddy-rich, so this line is schematic.",
             line([(-48.5, 41.5), (-46.0, 43.5), (-44.5, 46.5), (-43.5, 49.5), (-42.2, 51.0), (-38.0, 50.5), (-34.0, 50.4),
                   (-30.0, 51.5), (-26.0, 52.9), (-22.6, 53.3), (-19.5, 54.5), (-16.1, 55.7), (-12.0, 57.0), (-8.7, 58.6),
                   (-5.0, 60.2), (-1.0, 61.6), (2.5, 63.2), (4.5, 64.8)]), "hand-drawn", refs),
    ])
    write("kuroshio", [feat(
        f"Streamline traced by script through the {gdp}, smoothed to about 1 deg and simplified: from the North Equatorial "
        "Current bifurcation east of Luzon, through the Luzon Strait side and east of Taiwan, along the East China Sea shelf "
        "break, through the Tokara Strait, along Japan's south coast to separation off the Boso Peninsula (about 35 N 141 E), "
        "then the Kuroshio Extension. East of 137 E the line is nudged north from the drifter mean (which averages in the "
        "large-meander path) to the typical straight path; the start and the Extension are hand-placed.",
        line([(125.0, 13.5), (123.3, 16.5), (122.7, 18.2), (121.8, 19.8), (121.6, 21.3), (122.0, 23.0), (122.6, 24.7),
              (123.9, 25.8), (125.6, 26.5), (126.9, 28.0), (128.3, 29.3), (130.2, 29.6), (132.0, 30.2), (133.1, 31.7),
              (135.0, 32.6), (137.5, 33.3), (139.5, 33.8), (141.0, 35.0), (143.0, 35.5), (146.5, 35.5), (150.0, 35.3),
              (153.5, 35.6)]), "hand-drawn", refs)])
    ebc = (f"Hand-traced simplified axis, checked against streamlines of the {gdp}. {{detail}} Eastern boundary currents are "
           "broad (several hundred km) and slow in the mean, so the single line is schematic.")
    write("canary-current", [feat(ebc.format(detail=(
        "South-west from off the Strait of Gibraltar along the Moroccan coast about 200 km offshore, through the Canary "
        "Islands (between Fuerteventura and Gran Canaria), south along the Saharan coast to Cape Blanc (about 21 N), then "
        "west into the North Equatorial Current north of Cape Verde. The drifter mean also shows much of the flow peeling "
        "off west at 25-30 N.")),
        line([(-14.0, 36.5), (-12.5, 34.0), (-11.8, 32.0), (-12.8, 30.0), (-14.9, 28.4), (-16.3, 26.5), (-17.4, 24.0),
              (-18.2, 22.0), (-18.8, 20.8), (-20.5, 19.8), (-23.5, 19.0), (-27.5, 18.2)]), "hand-drawn", refs)])
    write("benguela-current", [feat(ebc.format(detail=(
        "North-west from off the Cape Peninsula along the Namibian coast about 150-250 km offshore, leaving the coast "
        "north of Walvis Bay (about 23 S) and turning north-west into the South Equatorial Current; the drifter mean shows "
        "the offshore part turning west between 22 and 28 S.")),
        line([(17.6, -34.6), (16.5, -32.0), (15.0, -29.5), (13.5, -27.0), (12.3, -24.5), (10.5, -21.5), (8.0, -19.0),
              (4.5, -17.0), (1.0, -15.5)]), "hand-drawn", refs)])
    write("humboldt-current", [feat(ebc.format(detail=(
        "North from where the West Wind Drift meets South America (about 43 S), along the Chilean coast about 150-300 km "
        "offshore, close inshore off Peru, leaving the coast near Punta Aguja (about 6 S) and turning west into the South "
        "Equatorial Current just south of the equator, short of the Galapagos.")),
        line([(-78.0, -43.0), (-76.0, -38.0), (-74.5, -33.0), (-73.5, -28.0), (-72.5, -23.0), (-72.8, -19.0), (-75.5, -16.0),
              (-78.5, -12.0), (-80.8, -8.5), (-82.3, -5.5), (-84.5, -3.0), (-88.5, -1.8)]), "hand-drawn", refs)])


SECTIONS = {"storms": storms, "highs": highs, "winds": winds, "itcz": itcz, "monsoons": monsoons, "currents": currents}

if __name__ == "__main__":
    for name in sys.argv[1:] or SECTIONS:
        SECTIONS[name]()
        print("wrote", name)
