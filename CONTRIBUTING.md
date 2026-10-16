# Contributing

How to change the World Atlas deck and how to release it. The build itself is described in [docs/architecture.md](docs/architecture.md), and the reasons behind it in the [ADRs](docs/adr/). This file links to them rather than repeating them.

## Setup

You need:

- [uv](https://docs.astral.sh/uv/). `uv run` creates the environment from `uv.lock` (Python 3.12) on first use.
- An authenticated `gh` CLI (`gh auth login`). Natural Earth downloads go through the GitHub API.
- `ankc` 0.6.x, from PyPI as `ankcompiler`.

```sh
git clone https://github.com/QuinnHerden/world-atlas.git
cd world-atlas
uv tool install 'ankcompiler==0.6.*'   # provides ankc
make fetch                             # vendors Natural Earth into vendor/, checked against data/sources.lock
make test
```

`make fetch` skips any file in `vendor/` whose checksum already matches the lock. To build with a local ankc checkout, set `ANKC`, e.g. `make all ANKC="uv run --with ../ankcompiler ankc"`.

**What a build costs.** A map takes about 3.5 s to render, and maps are cached, so only changed ones re-render. A full build from cold takes about 40 minutes and about 3 GB of RAM. `JOBS` is read from the environment (`src/geofeat/jobs.py`); the default, 1, renders in-process. `JOBS=2 make render` runs two workers, each loading its own basemap at about 1.5 GB. Editing any module in the render cache key (`render.py`, `frame.py`, `ne.py`, `style.py`, `spec.py`) or `uv.lock` re-renders every map.

## Recipes

Card keys are `kind:id`: `nile` (a bare id is a feature), `country:france`, `capital:france`, `city:alexandria`, `territory:gibraltar`, `subnational:scotland`, `dispute:crimea`. `IDS` takes keys or globs (`"country:france city:*"`).

### Edit a note

Notes are the text under the answer on each card back. They live in the data files: `note:` on entries in `data/features.yaml`, `data/countries.yaml` (and on the nested `capital:`), `data/territories.yaml` and `data/cities.yaml`.

1. Edit the `note:`. It is one to three sentences on why the place matters.
2. Run `make check-data`. It fails on a missing note on an active card, on characters a note can't carry (HTML, links, brackets, backticks, `\`, `$`, ankc syntax; emphasis is allowed), and on a research marker (below).

Notes are plain geography. They never mention cards, the deck, maps or other cards ("this card", "has no card of its own", "the map shows"). State the fact itself: say where the border runs, not that a map draws it.

A note change doesn't re-render maps. Re-importing a release updates the note on existing cards and keeps their scheduling.

### Fix a fact

A claim that may go stale or that you couldn't confirm goes in the entry's `verify` list, never in the note:

```yaml
  note: Plain prose, with no marker in it.
  verify:
  - claim: The treaty is not yet in force.
    as_of: "2026-10"            # YYYY-MM or YYYY-MM-DD, quoted
    source: https://example.org/page   # optional
```

`NOTE_MARKER` in `src/geofeat/model.py` fails `make check-data` on a note containing `(as of`, `as of 202x` (or a later decade), `verify`, `[v]`, `[s]` or `tbd`, in any case. "As of 2014 it hosted…" is fine; recent "as of" prose must be reworded.

To close verify items:

1. `make verify-report` lists every open item by card.
2. Recheck each claim. Prefer the primary source.
3. Fix the note if needed, and delete the `verify` item.
4. Add a row to [docs/research/verify-log.md](docs/research/verify-log.md) under a dated section for the data file: the card key, the outcome (**Corrected.** when the note changed) and the sources opened, each graded **[P]** primary (an official text or the body itself), **[S]** secondary reporting or **[T]** tertiary, used only to find the trail. A gap you couldn't close goes in that section's "Still to recheck at the primary" line.
5. Run `make check-data`.

Open items don't fail an ordinary build. They fail a release build (`RELEASE=1`).

### Add a card

Every card needs an entry in its data file, a `uid` from `make ids` and a slot in `data/positions.lock` from `make positions`. Field details are in [Data model](docs/architecture.md#data-model) and [Political data](docs/architecture.md#political-data). Every source rejects unknown keys.

| Card | File | Required fields | Also |
|---|---|---|---|
| Feature | `data/features.yaml` | `id`, `name`, `type` (a type word from `model.py`), `category`, `tier`, `style`, `geometry`, `expect`, `note` | Region is derived; `region` and `region_reason` override it together. |
| Country | `data/countries.yaml` | `id`, `name`, `uids: {country: null, capital: null}`, `tier`, `geometry`, `expect`, `note`, `capital` (`name`, one of `ne_id` or `file`, `expect`, `note`) | No capital card: `capital: null` and `uids: {country: null}`. Add the id to its region's `countries` in `data/curriculum.yaml`, to `pockets` if it isn't a walk node, and to `walk` if the region has one. |
| Territory | `data/territories.yaml` | `kind: territory`, `id`, `name`, `sovereign` (a country id), `status_line`, `geometry`, `expect`, `note` | Place it in its region's `territories: {id: host}`; the host must be a walk node. |
| Subnational | `data/territories.yaml` | `kind: subnational`, `id`, `type` (`Constituent country` or `Exclave`), `name`, `state` (a country id), `status_line`, `geometry`, `expect`, `note` | Optional `within` box. Place it in its region's `subnationals: {id: host}`. |
| Disputed area | `data/territories.yaml` | `kind: dispute`, `id`, `name`, `parties` (two or more country ids or `{label: …}`), `geometry`, `expect`, `note` | Place it in its region's `disputes: {id: host}`. |
| City | `data/cities.yaml` | `id`, `name`, `country`, `tier` (`core` or `secondary`), `ne_id` (populated places), `expect`, `note` | Optional `anchor`: an active feature in the city's region that it follows. |

Then:

1. `make ids`. It mints a uid for each entry that lacks one (it calls `ankc gen chunk`) and writes it into the YAML.
2. `make positions`. It runs `make check-data` first, then gives each new uid a slot in the lock. It needs a full clone with `origin/main` and the tags (see [Release](#release)).
3. Commit the data file(s) and `data/positions.lock` together.

The lock is frozen, so no existing entry moves. A new uid goes after the nearest earlier card in the study order that is already locked, in the gap up to the next locked position. New uids sharing a gap are spread evenly across it; `make positions` fails if the gap runs out. A fresh import and an upgraded collection then see the same order. See [Positions](docs/architecture.md#positions).

A new political card changes the adjacency graph and possibly the region's walk: run `make adjacency`, and `make walks` to review the walk before freezing it with `uv run python tools/freeze_walks.py`.

Never edit or reuse a uid. `id`, `name`, tier and category can change freely; the uid carries the review history.

### Retire a card

Never delete an entry. Users hold the note, and the lock keeps its slot.

1. Set `retired: true` on the entry: a feature in `data/features.yaml`, a territory, subnational or dispute in `data/territories.yaml`, a city in `data/cities.yaml`, or a country's `capital:` in `data/countries.yaml`. Keep every other field, the uid included.
2. Remove a retired territory, subnational or dispute from its region's placement in `data/curriculum.yaml`; a retired entry has no placement.
3. Leave `data/positions.lock` alone. `make check` fails on a locked uid that no entry holds, or one whose entry isn't `retired: true` (`retired_lock_errors` in `src/geofeat/check.py`).

A country entry has no `retired` field: a country card can't be retired without a schema change. A tier-3 state's capital must be retired (`make check-data` enforces it).

To un-retire, remove `retired: true` and run `make check-data`.

### Fix a map's framing

Feature frames are set by the entry's `frame:` in `data/features.yaml`: `min_span_km` (only widens), `centre: [lon, lat]` (siblings sharing a centre and span share a frame), `context: [ids]`, `admin1: true` and `former: <file>.geojson`.

Country, territory and dispute cards are drawn on their region's frame ([ADR 0010](docs/adr/0010-region-framing.md)). An entry in `countries.yaml` or `territories.yaml` can override it with `frame:`:

| Key | Values | Does |
|---|---|---|
| `include` | list of country or territory ids | The frame also holds their main bodies, moving before it widens. The capital and city cards drawn on it follow. |
| `ring` | `true` (default), `false`, `oval` | `false`: no ring round the subject. `oval`: one oval round all its parts on the main map. |
| `inset` | `true`, `false` | Forces the detail inset on or off. |
| `inset_km` | over 0, up to 5000 | The inset's width. |
| `inset_centre` | `[lon, lat]` | Centres the inset on a point instead of the subject. |

`ring`, `inset`, `inset_km` and `inset_centre` apply to the country card only, never its capital. City and subdivision entries take no `frame:`.

Every override, feature or political, carries a `reason:`: one line saying why the card is an exception, as `allow_nested` does. Start it with `user review:` when the user asked for it. `make check-data` fails on an override without a reason, and on a reason with no override:

```yaml
  frame:
    include: [australia]
    reason: "user review: show all of Australia for context, across the Tasman; the Polynesia box cuts it off"
```

The other overrides of a computed frame need one too:

- a country's `mainland` crop, with `mainland_reason:` saying what it drops;
- a region's pinned `frame` in `data/curriculum.yaml`, with `frame_reason:`;
- a region's `frame_margin` (1.0 to 2.0; default 1.1), for a region whose frame clips its neighbours, with `frame_margin_reason:`. It changes every card on the region's frame.

To preview:

1. `make render IDS="country:tanzania capital:tanzania"`. This renders only those cards and deletes nothing.
2. `make sheet IDS="country:tanzania capital:tanzania"` writes `build/sheet.png`, or `make phone IDS=…` writes `build/phone-NN.png` at phone width (390 px). Add `OUT=name.png` for a named file.

`make sheet` and `make phone` only read already rendered maps (`build/media.json`), so render first.

### Add a Natural Earth layer

1. Add an entry to `data/sources.lock` with `repo`, `commit` (a full sha on upstream history) and `path`. Use the commit the other entries pin unless you mean to move.
2. Run `uv run python -m geofeat.fetch --relock`. It downloads every pinned file, checks each commit is on upstream, checks each download against GitHub's blob sha and records `sha256` and `blob`. Review the diff: only your entry should change.
3. Select from it in a geometry part as `layer: <name>`, where the file is `ne_<name>.geojson`. `ne.layer` refuses any layer not in the lock.
4. If the renderer draws it, add it to `BASEMAP_LAYERS` in `src/geofeat/spec.py`. Its checksum is then in every card's cache key, so every map re-renders.
5. Commit `data/sources.lock` with the change that uses the layer.

## Before a pull request

Work on a branch named `ws/<topic>` and open the pull request against `main`.

| Change | Run |
|---|---|
| Anything | `make test`, `make check-data` |
| Maps, geometry, framing or render code | `make check` (renders every map, writes the deck, runs `ankc check`), and look at the cards with `make sheet` or `make phone` |
| New or retired cards, the study order, the lock, deckgen or tags | `make all`, then `make import-test` |
| Political geometry or `curriculum.yaml` regions | `make adjacency` |

`make import-test` builds the packages and imports them into fresh collections with the official `anki` library. It checks World Atlas's study order, a region filtered deck, Check Database and the upgrade from Geographic Features, then that each companion package lands in its own deck, at its lock positions, on World Atlas's note type.

Add a line to the `Unreleased` section of [CHANGELOG.md](CHANGELOG.md) for anything a user would notice.

## Maintainers

### Release

1. Work from a clean, full clone of `main`: full history and every tag, including `archive/*`. The freeze guard fails on a shallow clone, without the tags, or without a readable `origin/main`.

   ```sh
   git fetch --prune --prune-tags origin       # also drops stale local tags, e.g. an old v1.0.0-v3.0.0
   git status                                  # clean, on main
   git rev-parse --is-shallow-repository       # false
   ```

   The `archive/*` tags point into `main`'s history, so this fetch brings them; never build a release with `--no-tags`. A clone that still holds the deleted `v1.0.0`-`v3.0.0` tags fails the guard ("older than release v3.0.0") until it prunes them.

2. In CHANGELOG.md, change the version's heading from `Unreleased` to today's date. Commit and push it to `main`, so the tag carries the date.
3. Build: `make all RELEASE=1 RELEASE_VERSION=vX.Y.Z`. A release build also fails while any verify item is open, with a draft lock, or when the version's major isn't the lock's `series:`. With no `vX.Y.Z` tag yet, the first release must be v1.x.
4. `make import-test`. It covers World Atlas and the four companion packages.
5. Tag and push:

   ```sh
   git tag -a vX.Y.Z -m "World Atlas vX.Y.Z"
   git push origin vX.Y.Z
   ```

6. Publish the five packages, World Atlas and the four companion decks, with a `SHA256SUMS` over them written in `dist/`. Save the version's CHANGELOG section as `build/notes.md` (`build/` is ignored):

   ```sh
   (cd dist && sha256sum *.apkg > SHA256SUMS)
   gh release create vX.Y.Z dist/*.apkg dist/SHA256SUMS --verify-tag --repo QuinnHerden/world-atlas --title "World Atlas vX.Y.Z" --notes-file build/notes.md
   ```

The releases before v1.0.0 are archived as the tags `archive/v1.0.0`, `archive/v2.0.0` and `archive/v3.0.0`, with no GitHub releases; never create a release for an `archive/*` tag. Series 1 continues archived v3.0.0's order entry for entry, except the four oceans, moved to just after the continents before v1.0.0. Every lock must keep every uid of every archived release. See [ADR 0011's amendment](docs/adr/0011-refreezing-at-a-major-version.md#amendment-versioning-restarted-at-v100).

### Frozen order

`data/positions.lock` gives each card its new-card position. Within a major version (the lock's `series:`), it is append-only: entries are only added, never moved or removed. `make positions` is its only writer.

The reason is Anki's import. Re-importing a note never changes an existing card's `due`. If a release moved cards, an upgraded collection would keep the old order while a fresh import got the new one, and the two would diverge with no way for the deck to fix it.

Changing the order of existing cards needs a re-freeze: a new major version with a new `series:`, following the "To re-freeze" steps in [ADR 0011](docs/adr/0011-refreezing-at-a-major-version.md#decision). Upgraded users keep the old order unless they reposition by hand, so re-freeze rarely. The lock's format and guard are in [ADR 0006](docs/adr/0006-positions-lock-and-pos-footnote.md).

### Retired cards

A retired card's entry and uid stay in the data, and its lock entry keeps its slot, so no position or uid is ever reused. The build drops it from the package, but importing never deletes notes: users who have it keep it, and it keeps coming up for review.

### Companion decks

Italian Regions, US States, Brazilian States and Canadian Provinces and Territories are separate decks built from this repo, each its own package ([ADR 0012](docs/adr/0012-companion-decks.md)). Their maps are [ADR 0013](docs/adr/0013-subdivision-framing.md)'s.

- **Data.** `data/subdivisions.yaml`, one entry per subdivision, each country's in study order. An id starts with its deck's prefix (`it-`, `us-`, `br-`, `ca-`). Italian and Brazilian names are Italian and Portuguese only. Every entry needs a note.
- **Order.** The file order must be a neighbour walk: `make companion-walks` prints a generated one, and `make check-data` fails on an avoidable jump.
- **Positions.** Each deck has its own range of `positions.lock` (`src/geofeat/decks.py`), and a card's `deck=` is frozen like its position. Never move a card between decks.
- **Maps.** Check them with `make companion-sheets` (`build/framing/subdiv/`).
- **A new deck** needs a registry entry with an unused range in `decks.py`, a frame in `country_map.FRAMES`, and its entries.
