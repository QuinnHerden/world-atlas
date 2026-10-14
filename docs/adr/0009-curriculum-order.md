# 9. Curriculum order

Status: proposed, 2026-10-14. When accepted, supersedes rules 1 (tier first) and 3 (category alternation and the ≥ 3 card gap) of [ADR 0004](0004-flat-deck-and-study-order.md). ADR 0004's rule 2 (prerequisites first) stays. The design and its reasons are in the [World Atlas plan](../world-atlas-plan.md#curriculum); several parameters are defaults under decision 8 ([open decisions](../world-atlas-plan.md#open-decisions)). Built in P3.

## Context

ADR 0004 orders new cards tier first: all of tier 1, then 2, then 3. Countries have no tiers, so a tier-first order either puts every country in tier 1 or leaves holes in the political map. World Atlas is for a total beginner, who learns a map best as landmarks, then routes between them, then the whole.

ADR 0004 also keeps features within 300 km at least 3 cards apart. Contiguity now packs neighbours together on purpose, and the benefit of interleaving comes from contrast, which needs look-alikes close.

## Decision

**Shape: orientation, then an atlas ring, then a depth pass.**

1. **Orientation** (1–2 days): the 4 oceans, the 2 planetary wind bands and the 7 continents.
2. **Pass 1:** one loop round the ring of regions, starting in Western Europe. Each crossing between regions is a land border or a short sea, except the one Pacific crossing. Pass 1 holds every country, capital, territory and disputed area, the tier 1–2 features and the core cities.
3. **Pass 2:** the same ring again, with the tier 3 features and any secondary cities (all deferred for now, so pass 2 is the 10 tier-3 features).

A card's pass is derived, not stored: `card.study_pass` follows from its kind, tier and orientation flag, and its `pass::` tag must match.

The ring has 21 regions by default (decision 8).

**Within a region:**

- **Countries** follow a neighbour walk. Each new country borders one already introduced, by land or by a sea edge ([ADR 0008](0008-state-list-borders-adjacency.md)), preferring the most recent. The walk is generated once, reviewed, and frozen as an explicit list in `data/curriculum.yaml`. The build checks it and reports every jump.
- **Pockets** are microstates, enclaves and disputed areas. They aren't nodes in the walk. Each sits in its host's run, after the host's capital. Territory cards go in geographic pockets too (decision 5, decided: Greenland and Bermuda in 19, the Kurils in 16, Aruba and Curaçao in 20).
- **Capitals** come 2–3 cards after their country, and never in a later cluster.
- **Physical features** come right after the country that completes their frame (Pyrenees after France), unless a region frame feature opens the region (Iberian Peninsula).
- **Core cities** come at least 2 cards after their country's capital, or right after the feature they hang on (Alexandria after the Nile Delta).
- **Parent before child** stays, from ADR 0004 rule 2.
- **Look-alikes** sit 3 to 10 cards apart. They are the pair check's sibling pairs, a curated confusable-country list (Niger/Nigeria, Congo/DR Congo, Slovakia/Slovenia and others), and a country beside a feature with the same footprint. The window is waived when the pair spans two regions.
- **Category alternation is dropped** (default, decision 8). Clusters already mix card kinds.

Precedence: frontier continuity, then parent before child, then the look-alike window.

**Region membership.** `data/curriculum.yaml` is the one source of region and pocket host for countries, territories and disputed areas; their entries in `countries.yaml` and `territories.yaml` carry neither. Cities inherit their country's region, and a city's anchor feature must derive to that same region (`make check-data`). Features are assigned by rule in `regions.py`: global features go to orientation, straits to the later of their two shores, regional climate to the land it shapes, and everything else to the region holding the largest share of it. A `region` override with a `region_reason` in `features.yaml` covers the rest. Region outlines use each state's full outline; the `mainland` box only crops its card.

**Engine.** `order/` is a package of pure functions over `Card`s ([ADR 0005](0005-card-sources-and-card-dto.md)): passes, then regions, then the frozen walk, then anchoring, then local repair. Policy lives in `data/curriculum.yaml`; the code is the mechanism. No tie-break depends on set order or floats, and every comparator ends in an id. Golden-file tests use a small fixture world.

**Output.** The engine produces the ideal order. It places only new uids; [ADR 0006](0006-positions-lock-and-pos-footnote.md) keeps every placed card where it is. The PDF guide follows the same order, sectioned by pass and then region.

## Consequences

- A learner who stops after pass 1 has the whole political map and the most useful features. Only the long tail waits for pass 2.
- Because the ring is closed, any region can be a start. Home region first is a filtered deck, not a rotated build.
- Tier no longer decides order across the deck, but it still decides which pass a feature is in.
- The walk in archipelago regions (Caribbean, Oceania, Southeast Asia) has jumps. They are reported, not hidden.
- At 15 new cards a day (default, decision 8), the 607 new cards take about 6 weeks.
