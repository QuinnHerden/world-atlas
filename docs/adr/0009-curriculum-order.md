# 9. Curriculum order

Status: proposed, 2026-10-14. When accepted, supersedes rules 1 (tier first) and 3 (category alternation and the ≥ 3 card gap) of [ADR 0004](0004-flat-deck-and-study-order.md). ADR 0004's rule 2 (prerequisites first) stays. The design and its reasons are in the [World Atlas plan](../world-atlas-plan.md#curriculum); several parameters are defaults under decision 8 ([open decisions](../world-atlas-plan.md#open-decisions)). Built in P3.

Amended on 2026-10-16 (v3.0.0): the study order is cut from the ring order in four blocks, and Greenland moves to region 02 (see [Amendment: four blocks](#amendment-four-blocks-v300) and [ADR 0011](0011-refreezing-at-a-major-version.md)).

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
- **Pockets** are microstates, enclaves and disputed areas. They aren't nodes in the walk. Each sits in its host's run, after the host's capital. Territory cards go in geographic pockets too (decision 5, decided: Bermuda in 19, the Kurils in 16, Aruba and Curaçao in 20; Greenland in 19 in v2, in 02 since v3.0.0, see the amendment).
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

## Amendment: four blocks (v3.0.0)

The interleaved ring order above proved harder to follow than learning the map in layers (the user's decision; [ADR 0011](0011-refreezing-at-a-major-version.md)). The engine still builds the ring order as described, with every rule above. `order.engine.blocks` then cuts the study order from it in four blocks:

1. **Continents** (7 cards), in ring order: Europe … Antarctica.
2. **Countries, territories and disputed areas** (235 cards), region by region round the ring, on the frozen walks. Each walk node is followed by its pocket countries, then by the territories and disputed areas it hosts. Capitals aren't here.
3. **Physical features** (132 cards), in their ring order: the oceans and planetary winds first, then pass 1's features round the ring, then the 10 tier-3 features. Parent before child holds. Cutting out the countries closes up gaps, so within each ring segment (pass and region) the look-alike window (3 to 10 cards) is repaired again in the study order. Pairs that repair can't fix, and look-alike country pairs (the walk doesn't move), are reported as `study order:` waivers.
4. **Capitals and cities** (233 cards), region by region in the same country order: each country's capital, then its other cities (core before secondary). A city's `anchor` feature now only orders it among its own country's cities.

At 15 new cards a day the continents take about half a day, the countries 16 days, the features 9 and the capitals and cities 16: still about 6 weeks for all 607.

The passes now exist only inside the engine. A card's block follows from its kind (`card.block_of`), and its `block::` tag (`block::continents`, `block::countries`, `block::features` or `block::cities`) replaces the `pass::` tag. Political cards and cities keep their `region::NN` tag, so a region filtered deck gives that region's countries, then its capitals and cities. The guide is sectioned by block, then region.

**Greenland is in region 02, Nordic & Baltic, hosted by Iceland**, not in 19. A host is a placement anchor, not a statement of sovereignty: hosting it by Iceland puts it right after Iceland in the countries block (card 23). Sovereignty (the Kingdom of Denmark, beside Iceland and the Faroes) outweighs geography (the North American plate, 19 km from Canada). It stays in North America on the continent cards. `data/curriculum.yaml` records the decision and the v2 placement in its placements comment. Greenland keeps its v2 card and uid: the re-freeze places every card afresh, so no card has to be retired to move.

The consequences above change with it. A learner who stops early has the political map, not the political map plus the most useful features. The ring still makes any region a valid start through a region filtered deck.

## Amendment: subnationals and the v3.0.1 card set

v3.0.1 adds a `subnational` kind (England, Scotland, Wales, Northern Ireland; Kaliningrad Oblast; see [ADR 0008](0008-state-list-borders-adjacency.md#amendment-fewer-dispute-cards-v301)). A subnational is placed like a territory, as a pocket of its host from `curriculum.yaml`'s `subnationals:` map, and comes in the countries block after the host's pocket countries and before its territories and disputes. A pocket whose host's capital card is retired still hangs on the host: the order is unchanged. The counts above are v3.0.0's; v3.0.1 has 554 cards (blocks of 7, 236, 124 and 187), just over 5 weeks at 15 new cards a day; pass 2 is the 3 remaining tier-3 features. The `tier::` tag is gone; the tier stays internal to the order.
