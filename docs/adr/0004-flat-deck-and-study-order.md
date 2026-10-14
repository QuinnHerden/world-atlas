# 4. Flat deck and study order

Status: accepted, 2026-10-13. Still the rule for the current deck. The [World Atlas plan](../world-atlas-plan.md) has decided to replace the tier-first order with the atlas ring and the ≥ 3 card gap with a 3–10 card window; when that ships, a new curriculum ADR supersedes rules 1 and 3 here, and a stable-positions ADR supersedes the drift consequence below.

## Context

The deck had 23 subdecks, `Geographic Features::<Category>::Tier <n>`. By default Anki gathers new cards subdeck by subdeck, in alphabetical order. A learner studying the parent deck met every climate system, tier 3 included, before any tier 1 river or strait. Within a subdeck, order was arbitrary. ankc 0.4 gave every new card position 0 and read source files in directory-listing order.

## Decision

**One deck, with tags.** Every card is in `Geographic Features`. Each card has the tags `tier::<n>`, `category::<slug>` and `id_<feature-id>`. Tags do everything the subdecks did: filtered decks and Browse searches select by tag. Unlike a subdeck, a tag updates on re-import when a card's tier or category changes.

**A fixed study order** (`src/geofeat/order.py`), written into the package as each new card's position:

1. **Tier first.** All of tier 1, then tier 2, then tier 3. Tiers rank features by how much they explain, so a learner who stops early has the most useful ones.
2. **Prerequisites first.** Within a tier, a feature follows the features it depends on. A broad feature seen first gives the narrower one a frame: the Nile before the Nile Delta, the Mediterranean before the Aegean. Dependencies come from the data:
   - A feature subtracted from another, or drawn as its `frame.context`, is the parent: the Himalayas come before the Tibetan Plateau, which is drawn minus the ranges.
   - When a feature adds another into its geometry, or names it in `allow_nested`, the larger is the parent: the Arabian Peninsula comes before the Arabian Desert.
   - In a pair the pair check finds nested, the outer feature comes first, unless that contradicts a rule above. Pairs where only one is a climate system are ignored: a strait inside a cyclone belt isn't part of it.

   A parent in a later tier isn't promoted. Tier order wins, and `make deck` lists those cases.
3. **Interleaving.** Within a tier, categories alternate and each is spread evenly across the tier rather than used up early. Features closer than 300 km, the pair check's definition of a sibling pair, are kept at least three cards apart where the other rules allow. Learners tell similar items apart better when they meet them mixed with others (interleaving, or discrimination learning). Two nearby straits shown back to back get learned as "the other one", not by shape.

Ties go to `features.yaml` order, so the order is deterministic.

**Positions via ankc.** ankc 0.5 reads source files in sorted path order and numbers new cards sequentially in source order. Anki keeps a new card's position on first import: its apkg importer (`rslib/src/import_export/package/apkg/import/cards.rs`) shifts only review and day-learning due values. That is read from the desktop source; AnkiDroid and AnkiMobile weren't tested. deckgen writes all cards, in study order, to one file, and `make build` fails if the package's positions differ from the computed order.

## Consequences

- Re-importing doesn't change an existing card's deck or position. Anyone who imported an earlier build must move their cards to the one deck by hand (see the README). Only a fresh import gets the full study order.
- The order depends on the pair check, which takes about 40 s. `make check-data` caches its results in `build/siblings.json`, keyed by a hash of its inputs, and deckgen refuses a stale copy.
- A feature added later takes the position its place in the order implies, which can tie with an unstudied card already in a collection. The order drifts slightly with each addition.
- `make check-data` fails if the dependencies form a cycle.
- The build now needs ankc 0.5.x.
