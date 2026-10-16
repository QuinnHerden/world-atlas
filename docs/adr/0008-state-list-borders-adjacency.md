# 8. State list, borders worldview and adjacency

Status: accepted, 2026-10-14 (decided by the user; build plan decisions 1–3). Supersedes the PoC's de facto border view and the plan's earlier D8 default. Built in P1 (WS4 layers), P2 (data, adjacency) and P4 (rendering). Amended for v3.0.1: 9 dispute cards, not 15; 25 territories, not 23; 5 subdivision cards; and 162 capital cards, not 191 (see [the amendment](#amendment-fewer-dispute-cards-v301)).

## Context

The PoC on `poc/countries` used a 200-row state list and Natural Earth's default `admin_0_countries` layer. That layer is **de facto**: it draws Crimea in Russia, the Golan in Israel, Kashmir split along the Line of Control and the Line of Actual Control, and the Kurils in Russia. It gives Northern Cyprus, Somaliland and part of Western Sahara rows of their own.

Which states get cards, and whose borders they show, fixes the card count, the outlines, the adjacency graph and so the walk. It has to be settled before the data is written.

## Decision

**State list: 197 country cards.** The 193 UN members, plus Vatican, Palestine, Kosovo and Taiwan. Northern Cyprus, Somaliland and Western Sahara get **dispute cards only**.

**Borders: internationally recognised.**

| Case | Drawn |
|---|---|
| Areas the UN assigns to a sovereign | Inside that sovereign: Crimea in Ukraine; Abkhazia and South Ossetia in Georgia; Transnistria in Moldova; Northern Cyprus in Cyprus; the Golan in Syria; Somaliland in Somalia. Essequibo is already in Guyana. |
| Western Sahara | Cut out of Morocco. |
| Kashmir parts, Aksai Chin, Arunachal Pradesh, the Kurils | With the administering power. |
| Disputed boundary lines | Dashed, from NE's `boundary_lines_disputed_areas`. |

Disputed areas also get their own cards: the 15 "card" entries in the plan's [List 2](../world-atlas-plan.md#appendix-c-list-2-disputed-and-occupied-territories). The 23 "include" dependent territories in [List 1](../world-atlas-plan.md#appendix-b-list-1-dependent-and-autonomous-territories-inhabited) get cards too. Everything else stays on the [revisit list](../world-atlas-plan.md#intentionally-excluded-revisit-list). A dispute card's parties are the claimants or administrators only; a party that isn't one of the 197 states gets a short label (Transnistria, Northern Cyprus).

**Capital cards.**

- A state with several capitals gets one card, for the official/constitutional capital (Porto-Novo, Dodoma, Sri Jayewardenepura Kotte, Sucre, Pretoria, Yamoussoukro, Naypyidaw), not necessarily NE's `Admin-0 capital` row. The blurb names the seat of government. Stale NE names are fixed (Astana).
- Nauru's capital, Yaren, is hand-placed from reference coordinates; NE has no row for it.
- No capital card where the capital shares the country's name and dot: Monaco, Vatican, Singapore, San Marino, Luxembourg.
- No capital card for Palestine, the territories or the disputed areas.

That gives 191 capital cards.

**Layers.** WS4 pins `populated_places`, `admin_0_map_units`, `admin_0_disputed_areas` and `boundary_lines_disputed_areas`. `docs/research/ne-political-layers.md` worked out how each outline is composed; the composition now lives in the `geometry` of each entry in `countries.yaml` and `territories.yaml`, and `make check-data` checks that it is exact.

**Adjacency** is computed at build time from the same recognised-border outlines the country cards draw, before the card's `mainland` display crop: the graph and the region outlines use every part of a state, including the remote islands a card leaves out (`countries_ne.py`). The crop changes no edge and no feature region today.

- Two countries touch when their outlines intersect after a 1 km buffer, which absorbs 10m slivers.
- Countries within 200 km across water are linked by a sea edge, so island states aren't isolated (UK–France, Japan–Korea, Sri Lanka–India).
- Hand edits go in `data/adjacency.yaml` as `add` or `remove` entries, each with a `reason`.
- The result is cached in `build/adjacency.json`, keyed by a hash of its inputs, as `build/siblings.json` is.

## Consequences

- The basemap changes to recognised borders, so all 132 feature maps re-render once (P4).
- Outlines for Ukraine, Georgia, Moldova, Cyprus, Syria and Somalia need disputed-area parts added back, and Morocco's needs Western Sahara removed. Each composition is a reviewable table row in the research note.
- Cutting Western Sahara out of Morocco removes the Morocco–Mauritania land border. The outlines are still 42 km apart across it, so the computed sea edge carries the region 10 to 11 crossing with no `adjacency.yaml` entry. The P3 walk review should confirm it.
- Several dispute cards are time-sensitive: Somaliland recognition, the Chagos handover, Essequibo after the ICJ judgment, Western Sahara after UNSC resolution 2797, and the Golan beyond the 1974 line. The [Territories](../world-atlas-plan.md#territories) section lists what to verify before each release.
- The Russian-occupied areas of Ukraine since 2022 get no card, because NE has no line for them.

## Amendment: fewer dispute cards (v3.0.1)

Decided by the user, 2026-10-16. The user asked for as few dispute cards as possible.

**Rule.** A disputed area gets a card only if no country card can show it: it is a de facto separate entity, or it lies outside every recognised border or across several. A claim that lies inside one state's recognised borders, or that a country note can describe in a clause, goes into the notes of the countries involved.

**9 dispute cards.**

- **Kept:** Crimea, Transnistria, Abkhazia, South Ossetia, Northern Cyprus and Somaliland (de facto separate entities), Western Sahara (outside every recognised border), and the Spratly Islands (several claimants; the note now also covers the Paracels and Scarborough Shoal).
- **New:** Kashmir, one card for the former princely state, made from 7 `admin_0_disputed_areas` rows: Jammu and Kashmir with Ladakh, Siachen, Demchok, Azad Kashmir, Gilgit-Baltistan, Aksai Chin and Shaksgam. It replaces the three Kashmir-part cards and has a new uid (`LkpDqNGUZb`); the three part cards keep theirs as retired entries. Reusing the Indian-administered card's uid was considered, since it would keep one card's review history, and rejected: the card's answer changes meaning, from one side's part to the whole disputed area. Samdu, Tirpani and Bara Hotii lie outside the former state and are left out. The Line of Control and the Line of Actual Control are already dashed on the basemap.
- **Retired:** Kashmir (Indian-administered), Kashmir (Pakistani-administered) and Aksai Chin, merged into Kashmir; and the Golan Heights, Arunachal Pradesh, the southern Kurils and Essequibo, each a claim on land one state's recognised borders already include. The Syria, Israel, India, China, Japan, Russia, Guyana and Venezuela notes carry them.

Northern Cyprus, Somaliland and Western Sahara still get **dispute cards only**. Borderline cuts to revisit first, if the set shrinks again: Crimea, then Somaliland.

**Territories: 25.** The Cook Islands (in free association with New Zealand) and Akrotiri and Dhekelia (the UK base areas on Cyprus) join the 23. They had been left out for size or nuance; detail insets now make small places readable, and the cut is about importance, not rendering. Niue was considered on the same grounds and left out: about 1,800 people, low salience. It stays on the revisit list.

**Subdivisions: 5.** A new card kind for part of a state, with its own front word: England, Scotland, Wales and Northern Ireland ("Constituent country") and Kaliningrad Oblast ("Exclave"). They are drawn with a solid outline, as countries, since the border with the rest of the state isn't disputed, and have no capital cards. The four UK `admin_0_map_units` rows tile the United Kingdom's `admin_0` row exactly. Kaliningrad is Russia's row cut to a box (`within`); its Natural Earth land area is 13,421 km², against the official 15,125 km², which includes lagoon water. `curriculum.yaml` places them as pockets: the UK's four after the United Kingdom in region 01, Kaliningrad after Lithuania in region 02.

**Capital cards: 162.** The rule that drops a same-name microstate's capital now covers every tier-3 state (microstates and small island states): 29 more capital cards are retired, from Andorra la Vella to Basseterre. Djibouti and Kuwait City, capitals of small states that are not tier 3, keep theirs. `make check-data` fails on a tier-3 state with an un-retired capital.

**Retirement.** Subdivision, territory and dispute entries, cities and a country's capital take `retired: true`, as features do. A retired entry keeps its uid and its lock slot and makes no card; a retired political entry must not be placed in `curriculum.yaml`. With 18 cities and the duplicate Crimea feature also retired, the card count is 561: 607 − 55 + 9.
