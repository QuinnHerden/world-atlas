# 5. Card sources and the Card DTO

Status: proposed, 2026-10-14. Implements the [World Atlas plan](../world-atlas-plan.md#data-model)'s data model. Built in P1 (WS2 `RenderSpec`, WS3 `Card`) and P2 (the new sources and the continents). Amended 2026-10-16 for v3.0.1: a `subdivision` kind, and no capital card for a tier-3 state (see [the amendment](#amendment-subdivisions-and-tier-3-capitals-v301)).

## Context

Every card today comes from `data/features.yaml` through one pydantic model, `Feature`. That model carries policy that only fits physical features: the type vocabulary and families ([ADR 0001](0001-type-vocabulary.md)), the land clip, `expect` size ranges, `allow_nested` and the pair check.

World Atlas adds countries, capitals, cities, territories, disputed areas and continents. Pushing them through `Feature` would drag them into rules that don't apply: country outlines never overlap, and capitals are distinct points. Letting the order engine, deckgen, the package check and the guide each read several models would spread the same branching across four modules.

Before WS2, the render cache hashed the source of `model.py`, so adding a field such as `region` would have re-rendered every map.

## Decision

**One model per source, one DTO downstream.**

| Source | Model | Cards |
|---|---|---|
| `data/features.yaml` | `Feature` (`model.py`), unchanged apart from an optional `region` override with a reason (a feature `anchor` override existed until v3.0.0) | feature |
| `data/countries.yaml` | `Country`, with its `Capital` nested (`polities.py`) | country, capital |
| `data/territories.yaml` | `Territory` and `Dispute`, told apart by `kind` (`polities.py`): the 23 dependent territories and 15 disputed areas | territory, dispute |
| `data/cities.yaml` | `City`, with a `country:` reference (`sources/cities.py`) | city |
| continents | `data/features.yaml` entries of type `Continent`, emitted by `sources/features.py`; geometry composed from country outlines (`continents.py`, through the `continent` part) | continent |

The political entities, their outlines and their placement in the ring load in `polities.py`. Region and pocket host for countries, territories and disputes come from `data/curriculum.yaml`, not from the entries ([ADR 0009](0009-curriculum-order.md)).

Source modules live in `src/geofeat/sources/`: `features.py`, `political.py` (countries, capitals, territories, disputes) and `cities.py`. Each exposes `cards() -> list[Card]`, and `sources.all_cards()` fails on a key or uid that repeats across them.

**`Card`** (`card.py`) is a frozen pydantic DTO with these fields: `uid`, `kind`, `id`, `prompt`, `answer_lines`, `tags`, `region`, `tier`, `anchor`, `parents`, `note`, `host`, `orientation` and `render`. The order engine, deckgen, `check package` and the guide read only `Card`.

- **`kind`** is `feature`, `country`, `capital`, `city`, `territory`, `dispute` or `continent`. `id` is unique within a kind; **`key`** is `kind:id` and unique across sources.
- **`prompt`** is the front's type word: the feature's type, "Country", "City" for capitals and cities alike, and "Territory" or "Disputed territory" (the decision 4 default).
- **`answer_lines`** is a tuple of plain-text lines. deckgen escapes each one and joins them with `<br>`, so a capital's back reads "Paris", then "Capital of France". A city's second line is its country; a territory's is its status; a dispute's is `Disputed: <parties>`.
- **`host`** is the key of the country whose run a pocket sits in, after its capital. **`anchor`** is the key of the card a card comes right after in the ring order: a city's feature (Alexandria after the Nile Delta). Since v3.0.0 features take no anchor. **`parents`** must come first: a capital's country, a city's country and capital.
- **`render`** is a `RenderRef`: the `RenderSpec`, plus a `geometry` provider (and a `dot` provider for capitals and cities) that resolves only when called, so building cards doesn't load Natural Earth.
- **Tags:** every card gets `kind::<kind>` and a `block::` tag (`pass::` until v3.0.0), which must match `card.block` (derived from its kind). Political and city cards also get `region::NN`. Countries get `category::countries`, capitals and cities `category::cities`, territories and disputes `category::territories`. `category::` stays; `tier::` was dropped in v3.0.1 (the tier is internal to the study order).

**Two notes per state.** A country and its capital are separate notes with separate uids (`uids: {country, capital}`). The PoC's split cards showed why: the two cards differ on both sides, so ankc's reversed cards can't express them, and cloze can't hide one image per card. Two notes also give each card its own tags, position and retirement. That is how a same-name microstate drops its capital card.

**Ids.** New kinds use kind-prefixed id tags: `id_country_niger`, `id_capital_niger`, `id_city_istanbul`, `id_territory_gibraltar`, `id_dispute_crimea`. Feature tags stay `id_<id>`. `ids.py` mints uids for every source, and a check fails on a uid or id tag that repeats across sources. Real collisions exist: the rivers Niger, Congo and Jordan, and retired island ids such as cyprus and taiwan.

**`RenderSpec`** (`spec.py`) is extracted from `Feature`. It holds the style, frame options, fill opacity, close-up borders and the country/dot/outline overlays: the visual treatment and nothing else. `jobs.py` calls `card.render.resolve()` for the spec (with its dot filled in), the geometry, the context shapes and the former outline, and passes them to `render()`. The render cache key hashes the resolved geometry (rounded and normalised), the dumped spec, the renderer code (not `model.py`), `uv.lock`, and the pinned sha256s of the basemap layers and relief raster. See [architecture](../architecture.md) for the full key.

## Consequences

- Adding a kind (flags, rivers by country) means a new source and a `kind` value. The order engine and deckgen don't change.
- Editing `model.py`, a selector or any source schema doesn't re-render a card unless its resolved geometry or spec changes. Pinning a new NE layer re-renders nothing; changing a basemap layer's bytes re-renders every card.
- Anki won't bury a country and its capital as siblings, because they're different notes. The order engine spaces them instead ([ADR 0009](0009-curriculum-order.md)).
- The 166 feature uids and the note model id don't change. Existing notes update in place on re-import ([ADR 0007](0007-rename-and-migration.md)).
- WS2's exit check is that the 132 feature PNG names are identical before and after the extraction.

## Amendment: subdivisions and tier-3 capitals (v3.0.1)

2026-10-16. The table above gives the counts at the time: v3.0.1 has 5 subdivisions, 25 dependent territories and 9 disputed areas in `data/territories.yaml`, 162 capitals and 25 cities.

- **New kind, `subdivision`:** a part of a state, `Subdivision` in `polities.py`, an entry in `data/territories.yaml` with `kind: subdivision`. Its `prompt` is its own `type` ("Constituent country" for England, Scotland, Wales and Northern Ireland; "Exclave" for Kaliningrad Oblast), and its `answer_lines` are its name and `status_line` ("Country of the United Kingdom"). It is drawn with a solid outline, as a country, takes `category::territories` and `block::countries`, and has no capital card. Its tag is `id_subdivision_<id>`.
- **Capitals:** the same-name rule now extends to every tier-3 state (microstates and small island states): its capital has no card. The capital stays in `countries.yaml` with `retired: true`, so its uid is kept, as the two-notes design allows.
- **Retirement** reaches every source: subdivision, territory, dispute and city entries, and a country's `capital`, take `retired: true`.
