# Geometry tools

These scripts made the geometry files that aren't hand-drawn or taken straight from Natural Earth. They aren't part of the build: run one only to redo a geometry, then commit the files it writes.

Run them from the repo root with `uv run python tools/...`. Downloads go to `$CLIMATE_DATA`, which defaults to `build/climate-data/` and is gitignored. The command blocks below abbreviate `uv run python` as `python` and `$CLIMATE_DATA` as `$D`.

## Where the scripts came from

The climate scripts were written during phase 3 in a scratch directory that has since been deleted. They were rebuilt from the session transcript, using each file's final version with later in-place patches applied. Scratch paths became `$CLIMATE_DATA`, and `write_geo.py` now writes the `method` and `refs` provenance fields.

How far the rebuild was checked:

- **Self-contained sections:** `write_geo.py itcz monsoons currents` rebuilds the committed files byte for byte.
- **Data-dependent writers:** `storms`, `winds` and `highs` read derived JSON. Given JSON extracted from the committed files, `storms` and `winds` write identical output.
- **Data steps:** `density.py`, `contour.py`, `highs.py`, `trace_winds.py` and `gdp.py` haven't been re-run since the rebuild; the datasets weren't re-fetched.

## Datasets

All are US-government public domain, accessed 2026-10-12 between 23:26 and 23:55 UTC.

| Dataset | Version / DOI | Fetched with | Used for |
|---|---|---|---|
| IBTrACS, NOAA NCEI | v04r01, [doi:10.25921/82ty-9e16](https://doi.org/10.25921/82ty-9e16) | `curl -o $CLIMATE_DATA/ibtracs.$B.csv https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.$B.list.v04r01.csv` for `B` in `NA WP NI` (a few hundred MB) | storm belts |
| ICOADS 2° enhanced, monthly long-term mean 1971–2000, NOAA PSL | ERDDAP dataset `esrlIcoads2gec71_LonPM180` (no DOI) | `curl -o $CLIMATE_DATA/icoads.csv "https://coastwatch.pfeg.noaa.gov/erddap/griddap/esrlIcoads2gec71_LonPM180.csv?slp[][][],uwnd[][][],vwnd[][][],sst[][][]"` (URL-encode the brackets) | subtropical highs, trade winds, westerlies; checks for the ITCZ and monsoons |
| Global Drifter Program annual-mean near-surface velocity, NOAA AOML | Laurindo, Mariano & Lumpkin 2017, *Deep-Sea Res. I* 124: 73–92, [doi:10.1016/j.dsr.2017.04.009](https://doi.org/10.1016/j.dsr.2017.04.009); dataset [doi:10.7266/N7SJ1HN5](https://doi.org/10.7266/N7SJ1HN5) | `curl -o $CLIMATE_DATA/gdp-annual.dat https://www.aoml.noaa.gov/phod/dac/drifter_annualmeans_ascii.dat` | ocean currents |
| Natural Earth | 50m land, from the pinned `vendor/` copy | `make fetch` | contour previews; clipping the highs to the sea |

**Checksums.** Record each download's sha256 straight after fetching it, and verify it before deriving any geometry:

```sh
(cd $D && sha256sum ibtracs.*.csv icoads.csv gdp-annual.dat > SHA256SUMS)   # after downloading
(cd $D && sha256sum -c SHA256SUMS)                                          # before running any step below
```

Then copy the hashes into this table. They are missing because the phase 3 downloads weren't kept; fill them in at the next re-fetch, and treat a mismatch with a recorded hash as an upstream change to review.

| File | sha256 |
|---|---|
| `ibtracs.NA.csv`, `ibtracs.WP.csv`, `ibtracs.NI.csv` | not recorded (files not present) |
| `icoads.csv` | not recorded (file not present) |
| `gdp-annual.dat` | not recorded (file not present) |

Two other sources were tried in phase 3 and dropped:

- **FNMOC monthly winds** (ERDDAP `erdlasFnWPr_LonPM180`, 2001–2020): no wind data between 10° S and 10° N, which rules it out for the trades, the ITCZ and the monsoons. A small helper, `clim.py`, averaged them; it isn't kept.
- **JPL OSCAR currents** (ERDDAP `jplOscar`): downloads kept timing out; the GDP climatology replaced it.

## Climate geometry, file by file

`method` is the provenance class recorded in each GeoJSON feature (see `docs/adr/0002-provenance-classes.md`).

### Storm belts

Files: `atlantic-hurricane-belt`, `typhoon-alley` and `bay-of-bengal-cyclones`. Method: `pd-dataset`.

1. Select the IBTrACS main-track fixes at 00/06/12/18 UTC for seasons 1971–2020. Use the USA wind, falling back to the WMO wind.
2. Bin the fixes on a grid and apply 1-2-1 smoothing. Take the outer contour at 15% of the peak. Close it with a ±1-cell buffer, then simplify it by 0.4 cells.

```sh
python tools/climate/density.py $D/ibtracs.NA.csv - 64 1971 2020 2.5 $D/na_hur.npz
python tools/climate/density.py $D/ibtracs.WP.csv - 64 1971 2020 2.5 $D/wp_ty.npz
python tools/climate/density.py $D/ibtracs.NI.csv SUBBASIN=BB 34 1971 2020 2.5 $D/bb.npz
python tools/climate/contour.py $D/na_hur.npz -105,0,0,50 2.5 0.15 $D/na_hur.png | tail -1 > $D/na_hur.poly.json
python tools/climate/contour.py $D/wp_ty.npz 100,0,180,50 2.5 0.15 $D/wp_ty.png | tail -1 > $D/wp_ty.poly.json
python tools/climate/contour.py $D/bb.npz 75,0,100,30 1.25 0.15 $D/bb.png | tail -1 > $D/bb.poly.json
python tools/climate/write_geo.py storms
```

### Subtropical highs

File: `subtropical-highs`. Method: `pd-dataset`.

1. Contour the annual-mean ICOADS sea-level pressure at 1018 hPa, between 10° and 48° N/S.
2. Smooth the cells, clip them to the sea with NE 50m land, simplify them, and keep each cell's largest part.

```sh
python tools/climate/highs.py 1018 $D/highs.json $D/highs.png
python tools/climate/write_geo.py highs
```

### Trade winds and westerlies

Files: `trade-winds` and `westerlies`. Method: `pd-dataset`, except one westerlies segment that is `hand-drawn`.

1. Trace midpoint-method streamlines of the annual-mean ICOADS surface wind from the fixed seeds in `trace_winds.py`, in 100 km steps.
   - Westerlies run 1,900 km.
   - Trades run 1,800 km and stop 6° from the equator.
2. Keep every third point.
3. In the south-east Pacific the westerlies trace dies for lack of ship reports. A hand-drawn segment at 46–47° S replaces it.

```sh
python tools/climate/trace_winds.py
python tools/climate/write_geo.py winds
```

### ITCZ (July)

File: `itcz`. Method: `hand-drawn`.

The file is a 6° band around a hand-placed centre line, interpolated every 2.5° of longitude.

- **Over the oceans,** the line was read off the July wind reversal in ICOADS (`wind.preview(7, …)`).
- **Over land,** it follows NOAA CPC's July Intertropical Front climatology and standard textbook charts.

The coordinates are in `write_geo.py`.

### Monsoons

Files: `south-asian-monsoon` (July), `east-asian-monsoon` (June) and `west-african-monsoon` (August). Method: `hand-drawn`.

1. Trace the sea parts as ICOADS streamlines for the month: `wind.streamline(lon, lat, month, km)`.
2. Simplify them and type them into `write_geo.py`.

The inland ends are schematic.

### Ocean currents

Method: `hand-drawn` for every file except the first Gulf Stream feature, which is `pd-dataset`.

`gdp.py` smooths the drifter climatology to about 1° (a 5×5-cell box mean) and traces streamlines.

- **Gulf Stream:** the Florida Current and the Gulf Stream to the Grand Banks are a traced streamline, simplified. The North Atlantic Current is drawn by hand and checked against the streamlines.
- **Kuroshio:** a traced streamline, nudged north, east of 137° E, to the typical non-meander path. The start and the Extension are placed by hand.
- **Canary, Benguela and Humboldt:** hand-traced axes, checked against the streamlines.

```sh
python tools/climate/gdp.py          # prints the traced Kuroshio and Gulf Stream; writes previews
python tools/climate/write_geo.py currents
```

## Other derived geometry

- `siliguri_corridor.py` writes the polygon in `geometry/siliguri-corridor.geojson`: NE India within 40 km of both Nepal and Bangladesh.

## Surveys

Read-only scripts that inspect the pinned `vendor/` layers and write nothing.

- `ne_survey.py` prints the tables in [docs/research/ne-political-layers.md](../docs/research/ne-political-layers.md): state rows and capitals, territory and dispute outlines, the recognised-border composition, the point-of-view check, stale shapes and continents. Run `uv run python tools/ne_survey.py` after a re-pin and diff its tables against the doc's. Once P2 lands, its data files are the source of truth and this script is a cross-check.
