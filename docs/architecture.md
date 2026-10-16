# Architecture

How the World Atlas deck is built. This describes the system as it is now; the reasons for the larger choices are in the [ADRs](adr/), and the plan for the extension beyond the original feature deck is in the [World Atlas plan](world-atlas-plan.md).

The deck is 561 cards from four sources: 138 active entries in `data/features.yaml` (131 physical features, 6 of them climate systems, and the 7 continents), 197 countries and 162 capitals from `data/countries.yaml`, 5 subdivisions, 25 territories and 9 disputed areas from `data/territories.yaml`, and 25 cities from `data/cities.yaml`. Retired entries stay in the files: 35 in `data/features.yaml` (7 passes, 3 corridors, 15 islands, 9 climate systems and 1 peninsula), 29 capitals in `data/countries.yaml`, 7 disputed areas in `data/territories.yaml` and 18 cities in `data/cities.yaml`. The physical features were first released as the Geographic Features deck (v1); the curriculum order engine (`order/`) orders every kind, and one command turns the data into an `.apkg`, with no manual step per build.

## Pipeline

```
data/features.yaml ─────┐
data/countries.yaml ────┤
data/territories.yaml ──┼─> sources/ ─> Card ─┐
data/cities.yaml ───────┤                     │
data/curriculum.yaml ───┘                     │
geometry/*.geojson ─┐                         │
vendor/ (NE, pinned)┴─> resolve ──────────────┴─> render ─> deck/<sha256[:12]>.png + build/media.json ─┐
                        check data ─> build/siblings.json ───────────────────────────────────────┼─> deckgen ─> deck/world-atlas.md ─> ankc check ─> ankc build ─> dist/world-atlas.apkg
                        data/positions.lock (written by `make positions`) ───────────────────────┘
```

The diagram is simplified: deckgen also reads the Cards and the study order, and `make positions` reads the study order too. `curriculum.yaml` places each country, subdivision, territory and dispute in a region; `make adjacency` and the region derivation read it beside the outlines.

`make all` runs `test → fetch → check-data → render → deck → check → build`. Each step is a module in `src/geofeat/`:

| Target | Module | Does |
|---|---|---|
| `make ids` | `ids.py` | Mints a uid for each entry in every card source that lacks one, with `ankc gen chunk`, and writes it into the source's YAML file. Not part of `make all`. |
| `make fetch` | `fetch.py` | Downloads the pinned Natural Earth files through `gh api` and verifies their checksums against `data/sources.lock`. `--relock` re-pins. |
| `make check-data` | `check.py data` | Schema, geometry, provenance and sibling-pair checks. Caches the pair results in `build/siblings.json`. |
| `make positions` | `positions.py` | Places new uids in `data/positions.lock` (below). The lock's only writer; commit the result. Not part of `make all`. |
| `make adjacency` | `adjacency.py` | Builds the country adjacency graph ([ADR 0008](adr/0008-state-list-borders-adjacency.md)), caches it in `build/adjacency.json` and prints the report: edge counts, isolated states, hand edits, each region's connectivity and each ring seam. Fails if a state is isolated or a region is disconnected. Not part of `make all`. |
| `make render` | `jobs.py`, `render.py` | One PNG per active card, cached by its cache key (below). Writes `build/media.json` (`card.key` → file name). `IDS="country:france city:*"` renders only the matching cards and deletes nothing, for a pilot. |
| `make deck` | `deckgen.py` | Writes every card, in study order, to `deck/world-atlas.md`, with a `[^pos]` footnote from the lock when ankc is 0.6. Prints each region's walk jumps and waivers. Fails on a card with no map. |
| `make check` | `check.py deck` | Every card rendered and in the lock; a draft lock matches the current order (a frozen card whose block or region changed only warns; every locked uid belongs to a source entry); ankc `>=0.5,<0.7`; `ankc check` passes. |
| `make build` | `ankc build`, then `check.py package` | Builds `dist/world-atlas.apkg` and checks it. |
| `make guide` | `guide.py` | The PDF guide (below). |
| `make import-test` | `tools/import_test.py` | Imports the package into fresh collections with the official `anki` library and checks the study order, a region filtered deck, Check Database and the upgrade from v1 (below). Not part of `make all`. |

`deck/`, `build/`, `dist/` and `vendor/` are gitignored. `deck/` is pure output: nothing reads it back.

`uv run python -m geofeat.regions` prints every active feature's region, the rule that decided it and the runner-up. It has no make target.

**ankc.** `ankc.py` runs the compiler named by `$ANKC`. The Makefile sets it (default `ankc`); it may be a full command line such as `uv run --with ../ankcompiler ankc`. `ids.py`, the checks and `make build` all go through it. `ankc.py` also reads `ankc --version`; `writes_pos()` is true from 0.6, the first version that reads `[^pos]`. ankc 0.6.0 is on PyPI. The build accepts `>=0.5,<0.7`; a frozen lock requires 0.6.

## Repo layout

```
data/features.yaml     the physical features
data/countries.yaml    the 197 states, each with its capital nested (29 retired)
data/territories.yaml  the 5 subdivisions, 25 territories and 9 disputed areas (and 7 retired disputed areas)
data/cities.yaml       the 25 core cities (and 18 retired ones)
data/curriculum.yaml   passes, the ring of 21 regions, walk lists, pockets and placements, confusables
data/adjacency.yaml    hand edits to the computed adjacency graph, each with a reason
data/positions.lock    the lock's series, and each card's new-card position, block and region, keyed by uid; written only by `make positions`
data/sources.lock      Natural Earth repo, commit, path, sha256 and git blob sha per file
geometry/*.geojson     hand-authored or derived shapes, each with provenance
src/geofeat/           the pipeline (modules below)
tests/                 unit tests (`make test`)
tools/                 scripts that made the derived geometry; not part of the build (tools/README.md)
docs/                  this file, the ADRs, the World Atlas plan, historical research
```

Python 3.12, managed with uv. `uv.lock` pins the geo stack so renders are byte-stable.

## Modules

| Module | Does |
|---|---|
| `model.py` | The `Feature` schema, type words, families, categories and shared paths. |
| `card.py` | The `Card` DTO and `RenderRef`, the four study blocks (`BLOCKS`, `block_of`), the ring order's pass rule (`study_pass`), and the `block::` and `id_` tag formats. |
| `sources/` | One adapter per data file: `features.py`, `political.py` (countries, capitals, subdivisions, territories, disputes) and `cities.py`. `all_cards()` collects them. |
| `polities.py` | The political entities: `Country` (with `Capital`), `Subdivision`, `Territory` and `Dispute`, and `FrameOverride`. Loads `countries.yaml` and `territories.yaml`, places each active entry from `curriculum.yaml`, and composes outlines from their `geometry` parts, cropped to `mainland` (or, for a subdivision, `within`) for the card. |
| `framing.py` | The frame each political card is drawn on: its curriculum region's member points, or a fixed sub-frame's box and its regional locator; and `CITY_REGION_FRAMING`, which puts capitals and cities on their host's ([ADR 0010](adr/0010-region-framing.md)). |
| `countries_ne.py` | Each state's, subdivision's, territory's and dispute's full outline (active entries only), never cropped, read from the yaml `geometry`. What the adjacency graph and the region outlines use. |
| `curriculum.py` | The `curriculum.yaml` schema and its checks: every state in exactly one region, regions numbered in ring order, entry, exit and hosts being walk nodes, confusables naming known cards. |
| `adjacency.py` | The country adjacency graph: land edges (1 km buffer), sea edges (200 km), the `adjacency.yaml` edits, the cache and the report. |
| `regions.py` | Each feature's ring region by the plan's rules and the `region` override check. |
| `continents.py` | The 7 continents' geometry: member states' and territories' outlines by UN geoscheme, transcontinental states split on Natural Earth's line. A feature part `{layer: continent, select: {id: …}}` draws one. |
| `resolve.py` | Resolves a feature's geometry parts: Natural Earth rows, `geometry/` files, other features. |
| `ne.py` | Natural Earth layer loading (only layers pinned in `sources.lock`) and flow-line helpers. The renderer reads it, so it is in the render cache key. |
| `spec.py` | `RenderSpec`, the visual treatment of a card, and `BASEMAP_LAYERS`. |
| `jobs.py` | Turns cards into render jobs, keys them, and renders what the cache lacks. Not in the cache key. |
| `render.py`, `frame.py`, `style.py` | Drawing, framing (region frames and detail insets included) and the style constants. |
| `positions.py` | Reads, places and writes `positions.lock`; the freeze guard against `origin/main` and the newest release tag of the lock's series, and the series check against the release tags. |
| `order/` | The curriculum order (ADR 0009): `engine.py` (pure: passes, regions, walks, anchoring, repair, report, then the four blocks cut from that ring order), `walk.py`, `frames.py` (geometry facts cached in `build/frames.json`), `inputs.py` (real-data wiring and policy), `legacy.py` (ADR 0004's feature order and the sibling cache). |
| `deckgen.py` | The deck markdown. |
| `ankc.py` | Runs the configured ankc and reads its version. |
| `check.py` | `check data`, `check deck`, `check package`. |
| `pairs.py`, `fetch.py`, `ids.py`, `guide.py`, `sheet.py`, `cvd.py` | Pair check, Natural Earth download, uid minting, PDF guide, review sheets, colour-blindness simulation. |

## Data model

`src/geofeat/model.py` defines the feature schema (pydantic, unknown keys rejected).

```yaml
- id: nile                    # slug; free to change
  uid: w5NtfRCzSA             # Anki note GUID; minted once by `make ids`, never edited or reused
  name: Nile
  alt_names: []               # shown in brackets after the name
  type: River                 # the word on the card front; one of 23
  qualifier: null             # optional detail after the type word, e.g. the season: "Wind system, July"
  category: Rivers & Deltas   # category::<slug> tag and area highlight opacity
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
  region: null                # optional ring-region override; needs region_reason
```

**Geometry parts.** Each part has exactly one source:

- `layer` + `select`: rows of a vendored Natural Earth layer matching every key in `select` (`ne_id` by default; rivers have no ids, so `{name, rivernum}`). `rows` (default 1) is the exact number of rows that must match. This catches wrong-river matches.
- `file`: a file in `geometry/`.
- `feature`: another card's resolved geometry. With `subtract: true` it cuts that card out (the ranges out of the Tibetan Plateau, the Nile Delta out of the Indo-Gangetic Plain). Prefer a reference to copying another card's selector.

`trim_to_largest: true` keeps only the largest polygon left after a cut; `make check-data` reports the area dropped.

**`expect` is a drift check, not a fact check.** `bbox` (lon_min, lat_min, lon_max, lat_max; lon_min > lon_max crosses 180°) and a `length_km` or `area_km2` range bracket what the geometry measures now, about ±10%. They fail when a data update, a selector or a hand edit changes the shape noticeably. Where a published figure is close, the range is widened to include it and a comment cites it. Where Natural Earth's generalised shape can't reach the published value, the range stays around NE and a comment says how far off it is; the geometry is never stretched to match. `expect.mouth` is `sea` (default), `lake` or `none` (inland sinks).

**Frame options.** `min_span_km` (wider only); `centre: [lon, lat]`, so siblings share one frame (the Hindu Kush, Pamirs and Karakoram; Lake Chad); `context: [<id>]`, another line feature drawn faintly underneath (the Nile under its delta); `admin1: true`, state borders (used only by the retired Cumberland Gap); `former: <file>`, a past extent drawn as a dashed grey line (the Aral Sea's 1960 shore).

**Retirement.** To drop a card, set `retired: true` and keep the entry, so its uid is never reused. A retired entry is archived: it is validated against the schema only, not resolved, rendered, pair-checked or required to have a note. Un-retiring one needs a `make check-data` run. Political entries, cities and capitals retire the same way; see [Political data](#political-data).

For features only: an active feature may still reference a retired one; `make check-data` notes geometry and `frame.context` references and fails on an `allow_nested` that names one.

**Identity.** The uid is the note's identity, so `id`, `name`, tier and category can change without losing review history.

### Political data

`polities.py` defines and loads the political entities; `sources/cities.py` the cities. All reject unknown keys.

- **`countries.yaml`:** `id`, `name`, `alt_names`, `uids: {country, capital}`, `tier` (1, or 3 for microstates and small island states), `note`, `geometry`, `mainland`, `expect`, an optional `frame` override, and a nested `capital` (`name`, `alt_names`, one of `ne_id` or `file`, `expect`, `note`). `capital: null` (Monaco, Luxembourg, San Marino, Vatican, Palestine, Singapore) means no capital card and no capital uid. A tier-3 state's capital is retired (`retired: true` under `capital`), so it keeps its uid but has no card; `check data` fails on a tier-3 state with an un-retired capital.
- **`territories.yaml`:** entries with `kind: subdivision` (`type`, the front word, such as `Constituent country` or `Exclave`; `state`; `status_line`; an optional `within` box), `kind: territory` (`sovereign`, `status_line`) or `kind: dispute` (`parties`: country ids, or `{label: ...}` for a party that isn't a state). All have `uid`, `name`, `alt_names`, `geometry`, `expect`, `note` and an optional `frame` override. `within` keeps only the outline's parts wholly inside the box: Kaliningrad is Russia's row cut this way. The four UK constituent countries are `admin_0_map_units` rows, which tile the United Kingdom's `admin_0` row exactly.
- **`cities.yaml`:** `id`, `name`, `alt_names`, `uid`, `country`, `tier` (`core` or `secondary`; all 25 are core), `ne_id` (populated places), `expect`, an optional `anchor` feature, `note` and `retired`.

**Geometry** uses the feature grammar: Natural Earth rows, a `geometry/` file or a feature's shape, with `subtract` parts cut out. The first part is the base; `make check-data` fails unless every added part lies outside the base and every subtracted part inside it, so no sliver hides in the result. That is how recognised borders are composed (Crimea added to Ukraine, Western Sahara cut from Morocco).

**`mainland`** is a display crop for the card only. It keeps the outline's parts wholly inside the box and drops remote islands (the Kermadecs, Chathams, NZ sub-Antarctic islands, Trindade, Minami-Torishima, Okinotorishima, the Prince Edward Islands, Macquarie). `countries_ne.py` gives the adjacency graph and the region derivation the full, uncropped outline.

**`frame`** is a card's own exception to the framing rules ([ADR 0010](adr/0010-region-framing.md#decision)): `{inset: true|false}` forces its detail inset on or off, `inset_km` sets the inset's width and `inset_centre` its centre, and `ring: false` draws no ring round the subject, or `ring: oval` one oval round all its parts. These apply to the country card only. `include: [ids]` makes the frame hold other bodies too, moving before it widens (Tanzania: its southern neighbours; New Zealand: Australia); its capital and cities follow that frame. ADR 0010 lists the cards that use them.

**Retirement.** Subdivision, territory, dispute and city entries, and a country's `capital`, take `retired: true`. A retired one keeps its uid and its lock slot, is validated against the schema only and makes no card. A retired subdivision, territory or dispute also gives the adjacency graph no outline, no longer counts as a region member for framing, and must not be placed in `curriculum.yaml`.

**Region and host** are not in these files. `curriculum.yaml` is the one source of both for countries, subdivisions, territories and disputes (subdivisions in its `subdivisions:` maps, as pockets right after their host): the loaders place each entry from it and fail on an entry it doesn't place, or places as another kind. A host is a placement anchor only, never a statement of sovereignty. Cities take their country's region.

### Cards

Rendering, deckgen's output and the deck and package checks read `Card` (`card.py`), not `Feature` ([ADR 0005](adr/0005-card-sources-and-card-dto.md)). The study order and the PDF guide work on Cards too, but the order engine still takes its feature facts (frames and parent edges) from `Feature`, and the pair check and `make pairs` read `Feature` only. Each module in `src/geofeat/sources/` adapts one data file to Cards: `features.py` (one card per active feature), `political.py` (a country card, a capital card unless `capital: null` or retired, and the subdivision, territory and dispute cards) and `cities.py`. `sources.all_cards()` collects them and fails on a key or uid that repeats.

A `Card` is a frozen pydantic model:

- `uid`, `kind` and `id`, which is unique within its kind. Kinds: `feature`, `country`, `capital`, `city`, `subdivision`, `territory`, `dispute`, and `continent`.
- `prompt`, the type word on the front, and `answer_lines`, which deckgen escapes and joins with `<br>`. Both reject markdown and HTML syntax, since ankc renders card text unsanitised.
- `tags`, `tier`, `region` (`"NN"` for political and city cards; unset on features) and `note`. The note is printed in the PDF guide and, on the card, under the answer: deckgen appends `<hr>` and the HTML-escaped note in a `<div>` styled smaller and muted by opacity (`NOTE_STYLE`), so it reads in light and night mode. It goes into the existing answer field, so the note type is unchanged; `answer_lines` stays the name alone. The note validator keeps it inert (no HTML, links, images, code, `$` math or ankc syntax), allowing only emphasis, which ankc renders as `<em>`.
- Curriculum links for P3: `host`, the country key a pocket sits after; `anchor`, the key of the card this one comes right after in the ring order (a city's feature); `parents`, keys that must come first (a capital's country, a city's country and capital); `orientation`, true for the orientation block.
- `render`: a `RenderRef` holding the `RenderSpec`, a `geometry` provider, for capitals and cities a `dot` provider, and for political, capital and city cards a `region` provider (`framing.py`). They resolve only when called, so building cards doesn't load Natural Earth.

| Kind | Front | Back | Drawn as |
|---|---|---|---|
| feature | its type word | name | the feature's style |
| country | Country | name | the country outlined as subject |
| capital | City | name; "Capital of &lt;country&gt;" | a dot over its country |
| city | City | name; its country | a dot over its country |
| subdivision | its `type` (Constituent country, Exclave) | name; its `status_line` | its outline, solid, as a country |
| territory | Territory | name; its `status_line` | its outline (dashed from P4) |
| dispute | Disputed territory | name; "Disputed: &lt;parties&gt;", alphabetical | its outline (dashed from P4) |

Alternate names follow the name in brackets.

**Block and pass.** `card.block_of` gives a card's study block from its kind, and it isn't stored: `continents` (continents, 7 cards), `countries` (countries, subdivisions, territories and disputes, 236), `features` (131) or `cities` (capitals and cities, 187). The pass belongs to the ring order that the engine builds before it cuts the blocks; learners no longer see it. `card.study_pass` derives it from kind, tier and orientation flag. Continents and orientation features (the 4 oceans, the 2 planetary wind bands) are `orientation`. Countries, capitals, subdivisions, territories and disputes are always pass 1, tier-3 microstates included. Any other card is pass 1 at tier 1–2 and pass 2 at tier 3. Cities map `core` to tier 2 and `secondary` to tier 3; subdivisions, territories and disputes are tier 2. Today: 13 orientation, 538 pass 1 and 10 pass 2 cards.

### Tags

| Tag | On | Value |
|---|---|---|
| `kind::<kind>` | every card | the card's kind |
| `block::<b>` | every card | `continents`, `countries`, `features` or `cities`; validated against `card.block`. Replaced `pass::` in v3.0.0 |
| `tier::<n>` | every card | the tier |
| `category::<slug>` | every card | a feature's category; `countries`, `cities` (capitals and cities) or `territories` (subdivisions, territories and disputes) |
| `region::NN` | political and city cards | the ring region, zero-padded; features don't carry it yet |
| `id_<id>` / `id_<kind>_<id>` | every card | `id_nile` for features (kept for cards imported under ankc before 0.5); kind-prefixed for the rest, since kinds share ids (`id_country_niger`) |

**`card.key` is `kind:id`,** for example `feature:nile`. Two kinds may share an id, so `build/media.json`, the render bookkeeping, the sheets and the guide key on `card.key`, not the id. A `media.json` written before cards had kinds, keyed by bare feature id, is read as `feature:<id>`.

### Positions

`data/positions.lock` gives every card its new-card position ([ADR 0006](adr/0006-positions-lock-and-pos-footnote.md), [ADR 0011](adr/0011-refreezing-at-a-major-version.md)). The first line is `draft: true` or `draft: false`, the second `series: N`, the major version whose order the lock freezes (3 since v3.0.0). Each other line is `<uid>: <position> block=<continents|countries|features|cities> region=<NN|->`, sorted by uid. Positions are unique and below 1,000,000. The block and region are where the order engine placed the card when it was locked (a feature's region is its frame region; a continent, an ocean or a planetary wind has none). The guide sections by them, deckgen writes each card's `block::` and `region::` tags from them, and `check package` holds the packaged tags to them, so a filtered deck and a region's guide hold the cards their slots say.

`make positions` is the only writer. While the lock is a draft it is regenerated from the study order at a stride of 500, so retired uids drop out. Once it is frozen, locked entries never move. A new uid goes after `pred`, the nearest earlier card in the study order that is in the lock. It takes a slot between `lock[pred]` and the next locked value above it. New uids that share a gap are spread evenly (after the last locked value, at successive strides of 500), and the command fails when a gap is exhausted. A retired uid keeps its entry, so no position is reused, and `check deck` fails on a locked uid that no source entry, active or `retired: true`, holds.

The series-3 lock was regenerated for v3.0.0 and frozen: 607 entries from 500 to 303,500 (v3.0.1 appended 9 and keeps every retired uid's slot: 616 uids for 561 cards), with the blocks starting at 500 (continents), 4,000 (countries), 121,500 (features) and 187,500 (cities). The freeze guard in `check data` and `make positions` reads the lock committed on `origin/main` (`POSITIONS_BASE` overrides the ref) and the one on the newest release tag of the lock's series (`v3.*`) reachable from `HEAD`. Against a frozen base of the same series, the working lock must stay frozen and keep every one of its entries unchanged; it may only add uids. A base of an earlier series (v2.0.0's lock, which has no `series:` line) is only checked to be well formed; one of a later series is an error. The series itself must equal the major version of the newest `v*` tag reachable from `HEAD`, or be the next one, and a release tag on `HEAD` must be of the lock's series. Release tags are found with `git tag --merged HEAD`, keeping only exact `vX.Y.Z` tags (prereleases and other `v*` tags are ignored); the newest is by version, not by commit distance. A fresh freeze (a lock whose series is ahead of the newest release) may reorder, but must keep every uid of that release, since users hold those notes; a uid that was only ever on main or a branch may go. A release build (`make all RELEASE=1 RELEASE_VERSION=vX.Y.Z`; `RELEASE_VERSION` is exported to `check data`, which reads it only in a release build) fails without a version or with a draft lock, unless a release tag is on `HEAD`, and fails when the version's major, or any release tag on `HEAD`, isn't the lock's series. A non-release build with a lock ahead of the newest release warns that the next release must be vN.0.0. Without a readable base ref, a full clone or a tag list (a source archive, a shallow CI checkout), `check data` warns and skips those checks; under `RELEASE=1`, and always in `make positions`, a frozen lock fails instead. A frozen card whose block or region changes in the data keeps its locked slot, section and tags; `check deck` and `make positions` print a warning.

**Re-freezing** at a new major version N ([ADR 0011](adr/0011-refreezing-at-a-major-version.md)): replace the lock with the two lines `draft: true` and `series: N`, run `make positions` (it regenerates the lock at stride 500), set `draft: false`, commit, and release as vN.0.0.

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

`model.Category` has 10 values. Eight are used by active cards: Water Bodies, Straits & Chokepoints, Mountain Ranges, Rivers & Deltas, Deserts, Plateaus & Plains, Peninsulas & Isthmuses, Regions & Rifts, Climate Systems. Passes & Corridors and Islands are kept for retired entries only. A category sets the card's tag and the fill opacity of an area highlight (lighter for Water Bodies and Straits & Chokepoints); nothing else.

## Geometry and provenance

**Natural Earth v5.1.2,** public domain, pinned to commit `f1890d9f152c896d250a77557a5751a93d494776` of `nvkelso/natural-earth-vector`. Layers: 10m geography regions (polys, points, elevation points), marine polys, rivers, lakes, land, ocean, minor islands, admin_0 countries and land boundaries; 50m land, ocean, lakes, rivers, land boundaries and admin_1 lines. For the political cards: 10m populated places, admin_0 map units, admin_0 disputed areas and disputed boundary lines. The shaded relief raster `GRAY_50M_SR` comes from `nvkelso/natural-earth-raster`, pinned in the same lock. `fetch.py` checks each file's sha256 and git blob sha and moves it into place atomically. Downloads go through `gh api` because the usual CDNs are blocked on some machines.

**Hand-authored geometry.** `geometry/` holds 54 files for shapes NE can't select, including the hand-placed Yaren point. Every GeoJSON feature carries a provenance record ([ADR 0002](adr/0002-provenance-classes.md)):

- `source`: what was done, honest about approximation.
- `method`: `ne-derived` (5 features), `pd-dataset` (43), `reference-coords` (14) or `hand-drawn` (38). A feature takes the weakest class that honestly fits.
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

**Framing.** The highlight fills 45% of the frame's long axis. Every regional frame is at least 2,600 km wide, so a recognisable coastline is always in view; small features are found by their ring. `min_span_km` only widens. This is the rule for features and for giant political subjects; other political cards use region framing.

**Region framing** ([ADR 0010](adr/0010-region-framing.md)). A country, territory or dispute card is drawn on its curriculum region's frame: the box round the members' main bodies (`framing.py` passes their hull points), 10% larger (or the region's `frame_margin`: 1.4 for Horn & East Africa) and at least 3,500 km wide, shared by every card whose subject fits it. A subject that doesn't fit moves or widens its frame, and one that would fill more than 35% widens it to that fill. A giant, whose v2.0 frame was over 8,000 km wide, keeps that frame. Oceania's cards are on four fixed lon/lat sub-frames (Melanesia, Micronesia, central Pacific, Polynesia), and the Lesser Antilles on a fifth, which has a small Caribbean regional locator. Capitals and cities are drawn on their host's frame (`framing.CITY_REGION_FRAMING`). `RenderSpec.framing` (`region` or `fixed`) carries the choice; the region's points travel in the render job.

**Detail insets.** A political subject whose main body is smaller than a 56 px disc gets a corner inset, 35% of the card's width, that draws it at least twice as large; leader lines run from the subject to the inset. Every capital and city gets one round its dot, with no 2× rule: its host's main body whole if that fits in 1,200 km, else a 1,200 km window that keeps the dot well inside, and at most 1,000 km for a close dot. A `frame` override in the data forces the inset or sets its width. Frames under 400 km (insets) leave out the shaded relief.

**Basemap** (unlabelled):

| Layer | Style |
|---|---|
| Land | `#E9E4D8`, NE 10m for frames up to 4,000 km wide, 50m otherwise |
| Shaded relief | `GRAY_50M_SR` split into a shadow layer (up to 55%) and a highlight layer (up to 35%), under the ocean and lakes |
| Ocean and lakes | `#C3D5E2` |
| Major rivers (scalerank ≤ 4) | `#9DB8CC`, 2 px, above borders so a border river still shows |
| Country borders | Recognised borders ([ADR 0008](adr/0008-state-list-borders-adjacency.md)). `#8E887E`, 2 px; 3 px on Lake frames under 3,000 km (the rule also covers Pass and Corridor, now retired). Cut out of lakes and straits. Lease and overlay limits (Baikonur, Guantánamo, buffer zones) are left out. |
| Disputed borders | The same colour and width, dashed 8 px on, 6 px off: every line of NE's `boundary_lines_disputed_areas` except the reference lines and the stale Nagorno-Karabakh and 2014–22 Donbas lines, and the land-boundary segments the outline composition makes disputed or internal (Crimea's isthmus, Somaliland–Somalia, the Western Sahara berm, the Cyprus Green Line, the Golan line, Siachen–India; `render.DASHED_LAND`). On a country card, and on a capital or city card's context country, the borders inside that country are left out. |
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

**Political overlays** (`RenderSpec.country`, `dot`, `outline`).

| Card | Drawn as |
|---|---|
| country, subdivision | Its outline (`mainland` or `within` crop) as the subject: a 6 px red outline in a white casing over a 12% red fill. Neighbours stay neutral. |
| territory, dispute | The same, with the red edge dashed (`outline: dashed`, 24 px on, 14 px off, over the solid white casing). |
| capital, city | Its country as context (a 45% white wash, edged in a dark neutral, nothing red), and a 36 px red dot in a 3 px white casing with a dark hairline. No ring. |
| continent | Its area (40% fill, 5.5 px outline) on the world map, whatever its size (`RenderSpec.world`). Antarctica is the band along the bottom. |

**Rings on political cards.** A subject smaller than a 66 px disc, or under 100 px long, may be ringed. Its parts within 160 px of each other form a group, and a group is ringed only if its land is smaller than a 24 px disc (microstate scale), so Slovenia, Montenegro and Uruguay get no ring while a state scattered across an ocean (Kiribati, Tuvalu, the Marshall Islands) gets one round each island group. A group the detail inset's leader lines point at gets none. A large state's small remote islands are never ringed: the test is on the whole outline first (the US card's Northwestern Hawaiian Islands show as specks, unringed).

**Close dots** ([ADR 0003](adr/0003-projection-and-framing.md)). A capital or city whose dot has another carded dot within 150 km (geodesic) is a close dot: Kyoto and Osaka, Dubai and Abu Dhabi, Vienna and Bratislava. It keeps its host's frame, and its detail inset is at most 1,000 km wide round the dot. In a giant host it is instead framed 1,000 km wide round its dot, with no inset (Kinshasa, Kyoto, Osaka). `jobs.py` finds them over every card, so a filtered render frames them the same way, and `make render` lists them.

**Locator inset.** Feature cards only, on regional frames under 8,000 km wide. No political, capital or city card has it. The same 320 × 160 px plate carrée world map on every card, centred on 0° and never re-centred. It marks the frame as a `#333` box, or a 12 px dot when the box would be under 32 px or would cross 180°. Nothing in it is red. It sits bottom-left unless that covers the highlight, then moves to another corner.

**Render cache.** `build/render-cache.json` maps a cache key to a PNG. `jobs.py` turns each active card's `card.render` into a `RenderJob`: a `RenderSpec` (`spec.py`: style, frame options, fill opacity, close-up borders, and the country/dot/outline overlays), the geometry, the `frame.context` shapes and the `frame.former` outline. `render()` draws a job and reads nothing but the basemap. A political, capital or city job also carries its region's points. The key hashes:

- the geometry, each context shape, the former outline and the region's points, rounded to 1e-7° and normalised with `shapely.normalize`, so float noise and vertex or part order don't count. Flow geometry isn't normalised, because its arrows follow the vertex order.
- the spec's fields, defaults included. Context ids and the former file name aren't in the spec; their shapes are hashed instead.
- the source of the modules `render()` runs, `render.py`, `frame.py`, `ne.py` (layer loading and flow lines), `style.py` and `spec.py`, and `uv.lock`.
- the sha256 pinned in `data/sources.lock` for each layer in `spec.BASEMAP_LAYERS` and for the relief raster. `render` first checks those files in `vendor/` against the lock.

Renaming, re-tiering or retyping a card, editing `model.py`, `resolve.py`, `jobs.py` or a selector, or pinning a layer the basemap doesn't draw re-renders a card only if its resolved shape or spec changes. Editing any of the five hashed modules re-renders everything (about 3 s per map, under an hour for the ~610 cards). `JOBS=1` (the default) renders in-process; `JOBS=n` runs n workers at about 1.5 GB each. Every layer the hashed modules read must be in `BASEMAP_LAYERS`; a test checks this. `render` deletes PNGs no active card uses.

## Checks

**`check data`** (before rendering) fails on:

- a missing uid on an active card, or a duplicate id or uid;
- an active card of any kind without a `note` (every card's back shows it);
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

It also fails on political and city data:

- an active entry `curriculum.yaml` doesn't place, a state in no region or two, a host that isn't a walk node of its region, or a placement the territory file has no active entry for;
- an outline that doesn't compose exactly, falls outside its `expect`, or isn't a polygon; a capital or city point outside its country;
- a territory's `sovereign`, a subdivision's `state` or a dispute's party that isn't a country, or party names that repeat;
- a tier-3 state whose capital isn't retired;
- a city whose country is unknown, which is its country's capital, or whose `anchor` isn't an active feature, is in orientation or a later pass, or **derives to a different region from the city's country** (the anchor-region check: a city comes right after its anchor, so both must be in one region);
- a feature `region` override outside 1–21, or one without its `region_reason` (schema). Features take no `anchor`; the schema rejects one. `regions.py` also checks overrides against the ring whenever it derives a region.
- a ring region's or a composed continent's outline that is more than 0.5% sea (`SEA_SHARE_MAX` in `regions.py`). The real outlines are all land; the check catches a dispute whose outline takes in sea leaking into them, as the Spratly envelope once made region 17 4.1% sea. It runs wherever the outlines are built (`regions.region_outlines`, `continents.geometry`).

It prints every trim, every `allow_nested` override, references to retired features, and each flagged or nested pair.

**Sibling pairs** (`pairs.py`). Features within 300 km of each other, or overlapping, are compared by their highlights as drawn on one map framing both. World-map features are compared only with each other.

- **Fail** if the highlights are near-identical (IoU ≥ 0.8), or if one covers the other (cover ≥ 0.9) and both types are in the same family. An override can't clear the IoU rule.
- **Nested** pairs from different families (a delta in its river's frame, a strait inside a cyclone belt) are allowed and reported.
- **Override policy.** Fix a same-family nesting in the data first: subtract the inner card when the outer shape shouldn't include it. Use `allow_nested: [{id, reason}]` only when the inner feature is a named part of the outer one and cutting it out would misdraw the outer shape. The reason must say why the cards still differ. Current overrides: Aegean/Mediterranean, Barents/Arctic Ocean, Levant/Fertile Crescent, Pontic–Caspian Steppe/Eurasian Steppe, Zagros/Iranian Plateau, and Arabian Desert/Arabian Peninsula (cross-family, so not required, but recorded because its IoU sits just under 0.8).

**`check deck`** (before `ankc build`): every active card has a render and an entry in `positions.lock`, a draft lock still matches the current study order (`make positions` would leave it unchanged) (a frozen card whose block or region changed is a warning, not an error), every locked uid belongs to an active or `retired: true` source entry, ankc is `>=0.5,<0.7`, ankc is 0.6 when the lock is frozen, and `ankc check --deck "World Atlas"` passes.

**`check package`** (after the build): exactly one `.apkg` in `dist/`, with one note per active card and no others, every card in the `World Atlas` deck, every note carrying all its tags, `block::` and `region::` tags equal to the note's lock entry, every card new, packaged media equal to the rendered maps, and correct new-card positions. With ankc 0.6 or a frozen lock, each card's due must equal `positions.lock[uid]`; otherwise the dues must follow the study order.

## Deck and study order

**Card.** Front: the type word in bold above the map. Back: the answer lines (see [Cards](#cards)). The uid comes from the card's source YAML.

**One deck,** `World Atlas`, with no subdecks ([ADR 0004](adr/0004-flat-deck-and-study-order.md)). Each card carries the [tags](#tags) above. All cards go, in study order, into one file, `deck/world-atlas.md`.

**Study order** (`order/`, [ADR 0009](adr/0009-curriculum-order.md)):

1. The engine first builds the ring order: orientation (continents, oceans, planetary winds), then pass 1, then pass 2; within a pass, the 21 regions in ring order.
2. Within a region, countries follow the frozen `walk:` in `curriculum.yaml`, or a generated neighbour walk (most recent neighbour, then Warnsdorff, then id). A capital comes 2–3 cards after its country; pockets, subdivisions, territories and disputes after the host's capital; a feature right after the last country of its region it touches, or before the first country it mostly covers if it is the region's `opener:`; a city right after its `anchor` feature, else after its capital. Greenland is hosted by Iceland in region 02, so it comes right after Iceland.
3. Repair, in precedence order: parent before child (a `frame.context` reference, an added part, an `allow_nested` or a nested pair; never a `subtract`); the capital gap; no two cards with the same id side by side; look-alikes 3–10 cards apart within a region (curated confusables, same-family features within 50 km that don't contain one another, and a feature and a country with outline IoU ≥ 0.6). Walk countries never move. What can't be repaired is a waiver, printed per region with the walk's jumps.
4. Every tie-break ends in an id, so the order is deterministic.
5. `engine.blocks` cuts the study order from the ring order in four blocks: the continents; the countries, subdivisions, territories and disputes, region by region on the frozen walks, each walk node followed by its pocket countries and then the subdivisions, territories and disputes it hosts; the physical features in ring order (oceans and planetary winds, then pass 1, then the tier-3 features of pass 2); then the capitals and cities, region by region in the same country order, each capital followed by its country's other cities (a city's `anchor` now only orders it among its own country's cities). Cutting out the countries closes up gaps between features, so within each ring segment (pass and region) the features are repaired again for the look-alike window, parent before child first. Pairs that repair can't fix, and look-alike country pairs (the walk doesn't move), are printed as `study order:` waivers in the deckgen report. `Ordering.cards` is the study order; `Ordering.ring` keeps the ring order.

The order uses the pair results that `check data` caches in `build/siblings.json`, keyed by a hash of its inputs; deckgen refuses a stale copy. Anki keeps a new card's position on first import. With ankc 0.6 that position is the card's `[^pos]` from the lock; ankc 0.5 numbers new cards in source order, which is the study order.

**Known Anki behaviour.** Re-importing updates a note's fields and tags, but doesn't move its card to another deck or change its new-card position, and never deletes notes. The README covers what users do about each.

## PDF guide

`make guide` writes `build/world-atlas-guide.pdf` (A4, reportlab, in the optional `guide` dependency group). The name comes from the deck name. It holds every active card, of every kind, in the new-card study order from `data/positions.lock`, so entry N is the Nth new card Anki shows. Each entry gives the card number, the prompt, the answer lines, the map and the note.

Sections: the four blocks (Continents; Countries, territories and disputed areas; Physical features; Capitals and cities), each by ring region in ring order. The features block opens with the oceans and planetary winds, which have no region, and ends with the tier-3 features in their own run of regions. A section's block and region are the ones `positions.lock` records for its cards (the order engine's `region_of` at the time each was locked). A card can sit outside its own region's run: the engine moves a parent feature to just before its child. The guide shows such a card where Anki shows it, and prints a line for each. To do that, it takes the heaviest chain of (block, tier-3 run, region) runs that never goes back as the sections; every other run joins the section after it. A linked contents page and PDF bookmarks cover each block, each region and each card.

`make guide REGION=NN` writes `build/world-atlas-guide-NN.pdf` with only that region's sections, in every block. These hold the region's political cards, capitals and cities, the same ones a `tag:region::NN` filtered deck holds, plus the features the study order places in the region's run; features carry no region tag, so the filtered deck has none.

The build fails if a card is unrendered, has no note, or has a note carrying a research marker (`NOTE_MARKER` in `model.py`). It also fails if the lock is a draft that `make positions` would rewrite. Sections come from the block and region the lock records. It warns if the PDF is over the 80 MB budget. The notes come from [docs/research/research-independent.md](research/research-independent.md) (as of 2026-10-12).

## Review tools

| Target | Output |
|---|---|
| `make sheet [IDS="a b"] [OUT=x.png]` | `build/sheet.png`, a grid of maps |
| `make phone [IDS=...] [OUT=x.png]` | `build/phone-NN.png`, each map 390 px wide |
| `make review` | `build/review-NN.png` per ring region and `build/review-orientation.png`: every card 390 px wide in study order, labelled with its position, key and answer |
| `make pairs` | `build/pairs.log` (every pair), and `build/pairs-NN.png` with flagged, nested, allowed and near-limit pairs (IoU ≥ 0.5 or cover ≥ 0.7) side by side, 50 to a page |
| `make cvd [IDS=...] [OUT=x.png]` | `build/cvd.png`, each map beside deuteranopia and protanopia simulations, after the contrast of each mark |

`IDS` takes card keys or globs over them (`country:france`, `city:*`, `*:georgia`); a bare id is a feature.

**Import test.** `make import-test` builds the package, then runs `tools/import_test.py` with the official `anki` library, pinned to 26.09.3 (`uv run --with anki==26.09.3`) and the desktop import dialog's default options. A fresh import must give one note per lock entry, all in `World Atlas`, each back carrying its note (emphasis as `<em>`), with each due equal to its lock position and the first 40 new cards queued in lock order. A `tag:region::05 is:new` filtered deck ordered by due must give region 05's cards in lock order, and Check Database must change no card. The upgrade check imports the v1 Geographic Features package (built from commit `b63bf0e` by `git archive` with v1's locked environment, placeholder maps and the current ankc, backdated to the commit so that "Update notes: If newer" applies as it would for a real v1 user, checked against the shipped v1's guids and note type in `tests/fixtures/`, and cached in `build/import-test/` per ankc version; `--v1 PATH` uses a real v1 package instead) and studies three cards. Importing World Atlas must then update the feature notes in place (their backs gain the note), keep every v1 card's deck and scheduling, and let Change Deck move them with their scheduling intact. [device-test-checklist.md](device-test-checklist.md) is the same ground, checked by hand on Anki desktop, AnkiDroid and AnkiMobile.
