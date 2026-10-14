# 5. Card sources and the Card DTO

Status: proposed, 2026-10-14. Implements the [World Atlas plan](../world-atlas-plan.md#data-model)'s data model. Built in P1 (WS2 `RenderSpec`, WS3 `Card`) and P2 (the new sources).

## Context

Every card today comes from `data/features.yaml` through one pydantic model, `Feature`. That model carries policy that only fits physical features: the type vocabulary and families ([ADR 0001](0001-type-vocabulary.md)), the land clip, `expect` size ranges, `allow_nested` and the pair check.

World Atlas adds countries, capitals, cities, territories, disputed areas and continents. Pushing them through `Feature` would drag them into rules that don't apply: country outlines never overlap, and capitals are distinct points. Letting the order engine, deckgen, the package check and the guide each read several models would spread the same branching across four modules.

The render cache also hashes the source of `model.py`. Adding a field such as `region` would re-render every map.

## Decision

**One model per source, one DTO downstream.**

| Source | Model | Cards |
|---|---|---|
| `data/features.yaml` | `Feature` (unchanged); continents are added here with a new `Continent` type word and family | feature |
| `data/countries.yaml` | one entry per state, with its capital nested | country, capital |
| `data/cities.yaml` | one entry per city, with a `country:` reference | city |
| `data/territories.yaml` | the 23 dependent territories and 15 disputed areas | territory and dispute cards |

Source modules live in `src/geofeat/sources/`. Each exposes `cards() -> list[Card]`.

**`Card`** (`card.py`) is a plain DTO with these fields: `uid`, `kind`, `key`, `prompt`, `answer`, `tags`, `render: RenderSpec`, `region`, `tier`, `anchor`, `parents`. The order engine, deckgen, `check package` and the guide read only `Card`.

- **`kind`** is `feature`, `country`, `capital` or `city`. Territory and dispute cards get a kind when `territories.yaml` lands; their front words are open decision 4.
- **`answer`** is a list of lines. deckgen joins them with `<br>`, so a capital's back reads "Paris", then "Capital of France".
- **Tags:** every card gets `kind::<kind>`, existing feature cards included (`kind::feature`). Countries get `category::countries`, cities `category::cities`. `tier::` and `category::` stay.

**Two notes per state.** A country and its capital are separate notes with separate uids (`uids: {country, capital}`). The PoC's split cards showed why: the two cards differ on both sides, so ankc's reversed cards can't express them, and cloze can't hide one image per card. Two notes also give each card its own tags, position and retirement. That is how a same-name microstate drops its capital card.

**Ids.** New kinds use kind-prefixed id tags: `id_country_niger`, `id_capital_niger`, `id_city_lagos`. Feature tags stay `id_<id>`. `ids.py` mints uids for every source, and a check fails on a uid or id tag that repeats across sources. Niger, Congo, Jordan and Georgia are real collisions.

**`RenderSpec`** (`spec.py`) is extracted from `Feature`. It holds the style, geometry parts, frame options and context overlays: everything the renderer needs and nothing else. The render cache key becomes the dumped spec, plus the renderer code (not `model.py`), plus `uv.lock`, plus only the `sources.lock` entries for the layers that card uses.

## Consequences

- Adding a kind (flags, rivers by country) means a new source and a `kind` value. The order engine and deckgen don't change.
- Editing `model.py` or any source schema no longer re-renders the deck. A new NE layer re-renders only the cards that use it.
- Anki won't bury a country and its capital as siblings, because they're different notes. The order engine spaces them instead ([ADR 0009](0009-curriculum-order.md)).
- The 166 feature uids and the note model id don't change. Existing notes update in place on re-import ([ADR 0007](0007-rename-and-migration.md)).
- WS2's exit check is that the 132 feature PNG names are identical before and after the extraction.
