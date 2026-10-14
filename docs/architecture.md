# Architecture

How the Geographic Features deck is built. This describes the system as it is now; the reasons for the larger choices are in the [ADRs](adr/), and the planned extension to countries is in the [World Atlas plan](world-atlas-plan.md).

The deck has 166 entries in `data/features.yaml`: 132 active cards (126 places and 6 climate systems) and 34 retired ones (7 passes, 3 corridors, 15 islands and 9 climate systems). One command turns the data into an `.apkg`, with no manual step per build.

## Pipeline

```
data/features.yaml ─> sources/ ─> Card ─┐
geometry/*.geojson ─┐                   │
vendor/ (NE, pinned)┴─> resolve ────────┴─> render ─> deck/<sha256[:12]>.png + build/media.json ─┐
                        check data ─> build/siblings.json ───────────────────────────────────────┼─> deckgen ─> deck/geographic-features.md ─> ankc check ─> ankc build ─> dist/*.apkg
                        data/positions.lock (written by `make positions`) ───────────────────────┘
```

The diagram is simplified: deckgen also reads the Cards and the study order, and `make positions` reads the study order too.

`make all` runs `test → fetch → check-data → render → deck → check → build`. Each step is a module in `src/geofeat/`:

| Target | Module | Does |
|---|---|---|
| `make ids` | `ids.py` | Mints a uid for each entry in every card source that lacks one, with `ankc gen chunk`, and writes it into the source's YAML file. Not part of `make all`. |
| `make fetch` | `fetch.py` | Downloads the pinned Natural Earth files through `gh api` and verifies their checksums against `data/sources.lock`. `--relock` re-pins. |
| `make check-data` | `check.py data` | Schema, geometry, provenance and sibling-pair checks. Caches the pair results in `build/siblings.json`. |
| `make positions` | `positions.py` | Places new uids in `data/positions.lock` (below). The lock's only writer; commit the result. Not part of `make all`. |
| `make render` | `jobs.py`, `render.py` | One PNG per active card, cached by its cache key (below). Writes `build/media.json` (`card.key` → file name). |
| `make deck` | `deckgen.py` | Writes every card, in study order, to `deck/geographic-features.md`, with a `[^pos]` footnote from the lock when ankc is 0.6. |
| `make check` | `check.py deck` | Every card rendered and in the lock; ankc `>=0.5,<0.7`; `ankc check` passes. |
| `make build` | `ankc build`, then `check.py package` | Builds `dist/geographic-features.apkg` and checks it. |
| `make guide` | `guide.py` | The PDF guide (below). |

`deck/`, `build/`, `dist/` and `vendor/` are gitignored. `deck/` is pure output: nothing reads it back.

**ankc.** `ankc.py` runs the compiler named by `$ANKC`. The Makefile sets it (default `ankc`); it may be a full command line such as `uv run --with ../ankcompiler ankc`. `ids.py`, the checks and `make build` all go through it. `ankc.py` also reads `ankc --version`; `writes_pos()` is true from 0.6, the first version that reads `[^pos]`.

## Repo layout

```
data/features.yaml     the feature list; the only hand-edited data besides geometry/
data/positions.lock    each card's new-card position, keyed by uid; written only by `make positions`
data/sources.lock      Natural Earth repo, commit, path, sha256 and git blob sha per file
geometry/*.geojson     53 hand-authored or derived shapes, each with provenance
src/geofeat/           the pipeline (model, card, sources/, fetch, ne, resolve, frame, spec, render, jobs, style, pairs, order, positions, deckgen, ankc, check, guide, sheet, cvd, ids)
tests/                 unit tests (`make test`)
tools/                 scripts that made the derived geometry; not part of the build (tools/README.md)
docs/                  this file, the ADRs, the World Atlas plan, historical research
```

Python 3.12, managed with uv. `uv.lock` pins the geo stack so renders are byte-stable.

## Data model

`src/geofeat/model.py` defines the schema (pydantic, unknown keys rejected).

```yaml
- id: nile                    # slug; free to change
  uid: w5NtfRCzSA             # Anki note GUID; minted once by `make ids`, never edited or reused
  name: Nile
  alt_names: []               # shown in brackets after the name
  type: River                 # the word on the card front; one of 23
  qualifier: null             # optional detail after the type word, e.g. the season: "Wind system, July"
  category: Rivers & Deltas   # category::<slug> tag; groups the PDF guide
  tier: 1
  note: >-                    # 1–3 sentences on why it matters; PDF guide only; required on active cards
    It created Pharaonic Egypt, ...
  style: line                 # area | line | point | strait | flow-current | flow-wind | band
  geometry:                   # parts, unioned; `subtract` parts are cut out
  - {layer: 10m_rivers_lake_centerlines, select: {name: Nile, rivernum: 4}, rows: 2}
  - {layer: 10m_rivers_lake_centerlines, select: {name: El Bahr el Abyad, rivernum: 17}}
  expect: {bbox: [...], length_km: [...]}
  frame: {centre: [32.0, 16.5], min_span_km: 5500}
  allow_nested: []            # [{id, reason}]
  trim_to_largest: false
  retired: false
```

**Geometry parts.** Each part has exactly one source:

- `layer` + `select`: rows of a vendored Natural Earth layer matching every key in `select` (`ne_id` by default; rivers have no ids, so `{name, rivernum}`). `rows` (default 1) is the exact number of rows that must match. This catches wrong-river matches.
- `file`: a file in `geometry/`.
- `feature`: another card's resolved geometry. With `subtract: true` it cuts that card out (the ranges out of the Tibetan Plateau, the Nile Delta out of the Indo-Gangetic Plain). Prefer a reference to copying another card's selector.

`trim_to_largest: true` keeps only the largest polygon left after a cut; `make check-data` reports the area dropped.

**`expect` is a drift check, not a fact check.** `bbox` (lon_min, lat_min, lon_max, lat_max; lon_min > lon_max crosses 180°) and a `length_km` or `area_km2` range bracket what the geometry measures now, about ±10%. They fail when a data update, a selector or a hand edit changes the shape noticeably. Where a published figure is close, the range is widened to include it and a comment cites it. Where Natural Earth's generalised shape can't reach the published value, the range stays around NE and a comment says how far off it is; the geometry is never stretched to match. `expect.mouth` is `sea` (default), `lake` or `none` (inland sinks).

**Frame options.** `min_span_km` (wider only); `centre: [lon, lat]`, so siblings share one frame (the Hindu Kush, Pamirs and Karakoram; Lake Chad); `context: [<id>]`, another line feature drawn faintly underneath (the Nile under its delta); `admin1: true`, state borders (used only by the retired Cumberland Gap); `former: <file>`, a past extent drawn as a dashed grey line (the Aral Sea's 1960 shore).

**Retirement.** To drop a card, set `retired: true` and keep the entry, so its uid is never reused. A retired entry is archived: it is validated against the schema only, not resolved, rendered, pair-checked or required to have a note. Un-retiring one needs a `make check-data` run. An active card may still reference a retired one; `make check-data` notes geometry and `frame.context` references and fails on an `allow_nested` that names one.

**Identity.** The uid is the note's identity, so `id`, `name`, tier and category can change without losing review history.

### Cards

Rendering, deckgen's output and the deck and package checks read `Card` (`card.py`), not `Feature` ([ADR 0005](adr/0005-card-sources-and-card-dto.md)). The study order, the PDF guide and `make pairs` still read `Feature` until P3. Each module in `src/geofeat/sources/` adapts one data file to Cards; today there is one, `sources/features.py`, giving one card per active feature. `sources.all_cards()` collects them and fails on a key or uid that repeats.

A `Card` is a frozen pydantic model:

- `uid`, `kind` (`feature` today; `country`, `capital`, `city`, `territory`, `dispute` and `continent` are reserved) and `id`, which is unique within its kind.
- `prompt`, the type word on the front, and `answer_lines`, which deckgen escapes and joins with `<br>`. Both reject markdown and HTML syntax, since ankc renders card text unsanitised.
- `tags`, `tier`, `region`, `anchor`, `parents` and `note`.
- `render`: a `RenderSpec` and a function that resolves the geometry only when called, so building cards doesn't load Natural Earth.

**`card.key` is `kind:id`,** for example `feature:nile`. Two kinds may share an id, so `build/media.json`, the render bookkeeping, the sheets and the guide key on `card.key`, not the id. A `media.json` written before cards had kinds, keyed by bare feature id, is read as `feature:<id>`.

### Positions

`data/positions.lock` gives every card its new-card position ([ADR 0006](adr/0006-positions-lock-and-pos-footnote.md)). The first line is `draft: true` or `draft: false`; each other line is `<uid>: <position>`, sorted by uid. Positions are unique and below 1,000,000.

`make positions` is the only writer. While the lock is a draft it is regenerated from the study order at a stride of 500, so retired uids drop out. Once it is frozen, locked entries never move. A new uid goes after `pred`, the nearest earlier card in the study order that is in the lock. It takes a slot between `lock[pred]` and the next locked value above it. New uids that share a gap are spread evenly (after the last locked value, at successive strides of 500), and the command fails when a gap is exhausted. A retired uid keeps its entry, so no position is reused.

### Type words and families

23 type words (`model.FeatureType`), 20 of them on active cards. Each word belongs to a family (`model.FAMILY`):

| Family | Words |
|---|---|
| water body | Ocean, Sea, Lake |
| river | River |
| sea passage | Strait, Canal, Sea route |
| land passage | Pass, Corridor |
| relief | Mountain range, Plateau |
| lowland | Plain, Desert, Valley, Delta |
| region | Region |
| landmass | Peninsula, Isthmus, Cape |
| island | Island |
| climate | Ocean current, Wind system, Climate belt |

- Every word covers at least 3 active cards except Isthmus, Valley, Cape, Climate belt (2 each), Sea route and Ocean current (1 each). [ADR 0001](adr/0001-type-vocabulary.md) gives the reason for each.
- Pass, Corridor and Island are used only by retired entries and stay so those entries validate.
- The pair check compares families, not words.
- `area` features in a land family (land passage, relief, lowland, region, landmass) are clipped to NE 10m land when resolved. Island is its own family and isn't clipped, because NE draws some island groups as sea envelopes.
- `qualifier` adds only the season a climate map shows. It never repeats part of the answer.

### Categories

`model.Category` has 10 values. Eight are used by active cards: Water Bodies, Straits & Chokepoints, Mountain Ranges, Rivers & Deltas, Deserts, Plateaus & Plains, Peninsulas & Isthmuses, Regions & Rifts, Climate Systems. Passes & Corridors and Islands are kept for retired entries only. A category sets the card's tag, its place in the PDF guide and the fill opacity of an area highlight (lighter for Water Bodies and Straits & Chokepoints); nothing else.

## Geometry and provenance

**Natural Earth v5.1.2,** public domain, pinned to commit `f1890d9f152c896d250a77557a5751a93d494776` of `nvkelso/natural-earth-vector`. Layers: 10m geography regions (polys, points, elevation points), marine polys, rivers, lakes, land, ocean, minor islands, admin_0 countries and land boundaries; 50m land, ocean, lakes, rivers, land boundaries and admin_1 lines. The shaded relief raster `GRAY_50M_SR` comes from `nvkelso/natural-earth-raster`, pinned in the same lock. `fetch.py` checks each file's sha256 and git blob sha and moves it into place atomically. Downloads go through `gh api` because the usual CDNs are blocked on some machines.

**Hand-authored geometry.** `geometry/` holds 53 files for shapes NE can't select. Every GeoJSON feature carries a provenance record ([ADR 0002](adr/0002-provenance-classes.md)):

- `source`: what was done, honest about approximation.
- `method`: `ne-derived` (5 features), `pd-dataset` (43), `reference-coords` (13) or `hand-drawn` (38). A feature takes the weakest class that honestly fits.
- `refs`: a non-empty list, including `tools/README.md` where a script was used.

The scripts behind the `pd-dataset` and derived shapes are in `tools/`; dataset versions, DOIs and access dates are in [tools/README.md](../tools/README.md).

**Licence rule.** Only public-domain sources. No OSM-derived or CC-BY-SA geometry, because ODbL and share-alike would bind the deck. Wikipedia and Britannica are used for facts and coordinates only, never traced. Shapes drawn from Britannica's text are `hand-drawn` and say so in `source`.

**Lakes that have changed.** The Aral Sea and Lake Chad are drawn as their present-day outlines. The Aral card also shows the 1960 shoreline as a dashed grey line (`frame.former`), never highlighted.

## Rendering

`render.py`, `frame.py` and `style.py`. `style.py` stores sizes for an 800 px card and the renderer doubles them; sizes below are at the rendered 1600 px.

**Image.** 1600 × 900, quantized to a 256-colour palette. The ocean colour fills the background, so there is no letterbox. The file name is `sha256(png)[:12].png`: it doesn't reveal the answer, and a re-rendered map changes the note text, so Anki picks up the new image.

**Projection** ([ADR 0003](adr/0003-projection-and-framing.md)). Cylindrical only, north up, meridians vertical on every card and in the inset.

- Regional frames: equirectangular in metres, central meridian and standard parallel at the frame centre. The frame is fitted round the feature (or `frame.centre`), then redrawn centred on that frame and refitted.
- A highlight wider than 10,000 km, or one a regional frame can't hold, goes on a plate carrée world map centred on the feature's longitude.
- No frame shows past a pole. A band round a pole (the Arctic Ocean) gets a frame the globe's full width with the pole as its top edge.
- Geometry is split at the frame's back meridian, so frames across 180° are continuous.
- Distances and areas in the checks are measured in a feature-centred Lambert azimuthal equal-area projection; no card is drawn in it.

**Framing.** The highlight fills 45% of the frame's long axis. Every regional frame is at least 2,600 km wide, so a recognisable coastline is always in view; small features are found by their ring. `min_span_km` only widens.

**Basemap** (unlabelled):

| Layer | Style |
|---|---|
| Land | `#E9E4D8`, NE 10m for frames up to 4,000 km wide, 50m otherwise |
| Shaded relief | `GRAY_50M_SR` split into a shadow layer (up to 55%) and a highlight layer (up to 35%), under the ocean and lakes |
| Ocean and lakes | `#C3D5E2` |
| Major rivers (scalerank ≤ 4) | `#9DB8CC`, 2 px, above borders so a border river still shows |
| Country borders | `#8E887E`, 2 px; 3 px on Lake frames under 3,000 km (the rule also covers Pass and Corridor, now retired). Cut out of lakes and straits. |
| State borders | `frame.admin1` only, NE 50m admin-1, 2 px |
| Coastline | `#7F8A93`, 2.4 px |

**Highlight.** Always `#B2182B`, the only saturated colour on the map.

| Style | Drawn as |
|---|---|
| `area` | 40% fill (30% for Water Bodies and Straits & Chokepoints) and a 5.5 px outline. A ring is added when the area is smaller than a 66 px disc (about 16 px on a 390 px phone) or under 100 px long. |
| `band` | 30% fill and a 4 px dashed edge. |
| `line` | 10 px with a white casing. |
| `strait` | A 12 px channel line with a casing. A polygon strait whose mean width (2 × area ÷ perimeter) is over 24 px is drawn as a sea instead: 30% fill and a 6 px outline. At the 2,600 km minimum the Bosporus, Dardanelles, Danish Straits and Magellan are lines; the English Channel, Korea, Taiwan, Luzon and Malacca are seas. |
| `point` | A 96 px hollow ring. |
| `flow-current` | A 10 px solid line with arrowheads along it. |
| `flow-wind` | A 9 px dashed line with chevrons. |

A strait or line shorter than 123 px also gets a ring. Seasonal climate systems are drawn for one season, named by the qualifier ("Wind system, July").

**Locator inset.** On regional frames under 8,000 km wide. The same 320 × 160 px plate carrée world map on every card, centred on 0° and never re-centred. It marks the frame as a `#333` box, or a 12 px dot when the box would be under 32 px or would cross 180°. Nothing in it is red. It sits bottom-left unless that covers the highlight, then moves to another corner.

**Render cache.** `build/render-cache.json` maps a cache key to a PNG. `jobs.py` turns each active card's `card.render` into a `RenderJob`: a `RenderSpec` (`spec.py`: style, frame options, fill opacity, close-up borders, and the country/dot/outline overlays), the geometry, the `frame.context` shapes and the `frame.former` outline. `render()` draws a job and reads nothing but the basemap. The key hashes:

- the geometry, each context shape and the former outline, rounded to 1e-7° and normalised with `shapely.normalize`, so float noise and vertex or part order don't count. Flow geometry isn't normalised, because its arrows follow the vertex order.
- the spec's fields, defaults included. Context ids and the former file name aren't in the spec; their shapes are hashed instead.
- the source of the modules `render()` runs, `render.py`, `frame.py`, `ne.py` (layer loading and flow lines), `style.py` and `spec.py`, and `uv.lock`.
- the sha256 pinned in `data/sources.lock` for each layer in `spec.BASEMAP_LAYERS` and for the relief raster. `render` first checks those files in `vendor/` against the lock.

Renaming, re-tiering or retyping a card, editing `model.py`, `resolve.py`, `jobs.py` or a selector, or pinning a layer the basemap doesn't draw re-renders a card only if its resolved shape or spec changes. Editing any of the five hashed modules re-renders everything (about 3 s per map). `JOBS=1` (the default) renders in-process; `JOBS=n` runs n workers at about 1.5 GB each. Every layer the hashed modules read must be in `BASEMAP_LAYERS`; a test checks this. `render` deletes PNGs no active card uses.

## Checks

**`check data`** (before rendering) fails on:

- a missing uid on an active card, or a duplicate id or uid;
- an active card without a `note`;
- a `geometry/` feature without a known `method`, with empty `refs`, or whose `source` contains "unverified" or "placeholder" (any case);
- a selector that matches the wrong number of rows, or an `expect` bbox or size range that doesn't hold;
- geometry types that don't fit the style;
- a `line` that is more than one piece after closing gaps under 20 km;
- a river with no true end (a source or mouth, not a junction) within 5 km of the sea, or of a lake with `expect.mouth: lake`;
- flow lines that don't chain head to tail (a piece drawn backwards), or a flow feature with a `subtract` part;
- an Ocean or Sea with a hole of open water over 10,000 km², which means a neighbouring sea was left out of the union;
- a `frame.context` that isn't another line feature, or an `allow_nested` naming an unknown or retired feature;
- a sibling pair that clashes (below);
- a cycle in the study-order dependencies.

It prints every trim, every `allow_nested` override, references to retired features, and each flagged or nested pair.

**Sibling pairs** (`pairs.py`). Features within 300 km of each other, or overlapping, are compared by their highlights as drawn on one map framing both. World-map features are compared only with each other.

- **Fail** if the highlights are near-identical (IoU ≥ 0.8), or if one covers the other (cover ≥ 0.9) and both types are in the same family. An override can't clear the IoU rule.
- **Nested** pairs from different families (a delta in its river's frame, a strait inside a cyclone belt) are allowed and reported.
- **Override policy.** Fix a same-family nesting in the data first: subtract the inner card when the outer shape shouldn't include it. Use `allow_nested: [{id, reason}]` only when the inner feature is a named part of the outer one and cutting it out would misdraw the outer shape. The reason must say why the cards still differ. Current overrides: Aegean/Mediterranean, Barents/Arctic Ocean, Levant/Fertile Crescent, Pontic–Caspian Steppe/Eurasian Steppe, Zagros/Iranian Plateau, and Arabian Desert/Arabian Peninsula (cross-family, so not required, but recorded because its IoU sits just under 0.8).

**`check deck`** (before `ankc build`): every active card has a render and an entry in `positions.lock`, ankc is `>=0.5,<0.7`, ankc is 0.6 when the lock is frozen, and `ankc check --deck "Geographic Features"` passes.

**`check package`** (after the build): exactly one `.apkg` in `dist/`, with one note per active card and no others, every card in the `Geographic Features` deck, every note carrying all its tags, every card new, packaged media equal to the rendered maps, and correct new-card positions. With ankc 0.6 or a frozen lock, each card's due must equal `positions.lock[uid]`; otherwise the dues must follow the study order.

## Deck and study order

**Card.** Front: the type word in bold above the map. Back: the name, with alternate names in brackets. The uid comes from `features.yaml`.

**One deck,** `Geographic Features`, with no subdecks ([ADR 0004](adr/0004-flat-deck-and-study-order.md)). Each card carries the tags `tier::<n>`, `category::<slug>`, `id_<feature-id>` and `kind::feature`. All cards go, in study order, into one file, `deck/geographic-features.md`.

**Study order** (`order.py`):

1. Tier 1, then 2, then 3. A parent in a later tier isn't promoted; `make deck` lists those cases.
2. Within a tier, a parent comes before its children. Edges come from the data: a `subtract` or `frame.context` reference makes the referenced feature the parent; an added `feature` part or an `allow_nested` makes the larger feature the parent; a nested pair from the pair check puts the outer first, unless that contradicts an edge above or only one of the two is a climate system.
3. Categories alternate, each spread evenly across the tier. Features within 300 km of each other are kept at least 3 cards apart where the other rules allow.
4. Ties go to `features.yaml` order, so the order is deterministic.

The order uses the pair results that `check data` caches in `build/siblings.json`, keyed by a hash of its inputs; deckgen refuses a stale copy. Anki keeps a new card's position on first import. With ankc 0.6 that position is the card's `[^pos]` from the lock; ankc 0.5 numbers new cards in source order, which is the study order.

**Known Anki behaviour.** Re-importing updates a note's fields and tags, but doesn't move its card to another deck or change its new-card position, and never deletes notes. The README covers what users do about each.

## PDF guide

`make guide` writes `build/guide.pdf` (A4, reportlab, in the optional `guide` dependency group). It holds every active card's map, name, type, tier and note, grouped by category, then tier, then name, with a linked table of contents and PDF bookmarks. It fails if a card is unrendered or has no note. The notes come from [docs/research/research-independent.md](research/research-independent.md) (as of 2026-10-12), without the figures its verify flags mark as unchecked.

## Review tools

| Target | Output |
|---|---|
| `make sheet [IDS="a b"]` | `build/sheet.png`, a grid of maps |
| `make phone [IDS=...]` | `build/phone-NN.png`, each map 390 px wide |
| `make pairs` | `build/pairs.log` (every pair), and `build/pairs-NN.png` with flagged, nested, allowed and near-limit pairs (IoU ≥ 0.5 or cover ≥ 0.7) side by side, 50 to a page |
| `make cvd [IDS=...]` | `build/cvd.png`, each map beside deuteranopia and protanopia simulations |
