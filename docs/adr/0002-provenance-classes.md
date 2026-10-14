# 2. Provenance classes for hand-authored geometry

Status: accepted, 2026-10-13. Still the current rule; the summary is in [architecture.md](../architecture.md#geometry-and-provenance). Some examples below (passes, Siliguri, Kuroshio, Canary, the East Asian and West African monsoons) are now retired cards; their files and provenance remain.

## Context

`geometry/` held 52 GeoJSON files that Natural Earth selectors can't express. Until now the only provenance was a free-text `source`, which ranged from "traced by script from IBTrACS" to "general knowledge… Unverified" (Kerch Strait), and some shapes drawn from Britannica's prose read as if traced from its maps.

Free text can't be checked, and it doesn't separate reproducible shapes from judgement calls.

## Decision

Every feature in a `geometry/` file carries three properties:

- `source`: free text saying what was done. It must be honest about approximation.
- `method`: one of four classes:

| Method | Meaning | Examples |
|---|---|---|
| `ne-derived` | Computed from Natural Earth geometry by a stated rule, possibly with a hand-drawn cut line | Siliguri Corridor (India within 40 km of Nepal and Bangladesh), Wakhan, Sinai, Italian Peninsula |
| `pd-dataset` | Computed by script from a public-domain dataset; the script is in `tools/` | storm belts (IBTrACS), subtropical highs and traced winds (ICOADS), the traced Gulf Stream (GDP) |
| `reference-coords` | Placed from published coordinates (Wikipedia, Britannica), checked against NE land | passes, Kerch, Hormuz, Bering |
| `hand-drawn` | Drawn by judgement, from text descriptions or general knowledge, or by hand-tracing a dataset | Iranian Plateau, Levant, Fertile Crescent arc, Eurasian Steppe parts, Grand Canal, currents checked against GDP |

- `refs`: a non-empty list of references, including `tools/README.md` where a script was used.

Rules:

- A feature takes the weakest class that honestly fits. If a large part of a line is hand-placed, the feature is `hand-drawn` even if checked against a dataset (Kuroshio, Canary, monsoons).
- Shapes drawn from Britannica's text are `hand-drawn`, and their `source` says "drawn from Britannica's text description, not its map images".
- No OSM or CC-BY-SA geometry, in line with the licence rule in [architecture.md](../architecture.md#geometry-and-provenance) (then PLAN.md).
- Wikipedia and Britannica are used only for facts and coordinates. Geometry is never traced from Wikipedia, Wikimedia or OSM.

`make check-data` fails when:

- `method` is missing or not one of the four;
- `refs` is missing or empty;
- `source` contains "unverified" or "placeholder", in any case.

## Consequences

- An unfinished shape can't ship: a placeholder note fails the build.
- A reviewer can see at a glance which shapes are reproducible (`ne-derived`, `pd-dataset`) and which need a judgement review (`hand-drawn`).
- Counts per GeoJSON feature (53 files): 43 `pd-dataset`, 38 `hand-drawn` (37 at adoption, plus the Aral Sea's 1960 shore), 13 `reference-coords`, 5 `ne-derived`.
- Kerch was redrawn from reference points to drop "Unverified": Cape Fonar, Chushka Spit, Tuzla Island, the strait centre, and NE vertices for Capes Takhil and Panagia.
