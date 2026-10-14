# 8. State list, borders worldview and adjacency

Status: accepted, 2026-10-14 (decided by the user; build plan decisions 1–3). Supersedes the PoC's de facto border view and the plan's earlier D8 default. Built in P1 (WS4 layers), P2 (data, adjacency) and P4 (rendering).

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

Disputed areas also get their own cards: the 15 "card" entries in the plan's [List 2](../world-atlas-plan.md#appendix-c-list-2-disputed-and-occupied-territories). The 23 "include" dependent territories in [List 1](../world-atlas-plan.md#appendix-b-list-1-dependent-and-autonomous-territories-inhabited) get cards too. Everything else stays on the [revisit list](../world-atlas-plan.md#intentionally-excluded-revisit-list).

**Capital cards.**

- A state with several capitals gets one card, for the official/constitutional capital (Porto-Novo, Dodoma, Sri Jayawardenepura Kotte, Sucre, Pretoria, Yamoussoukro, Naypyidaw), not necessarily NE's `Admin-0 capital` row. The blurb names the seat of government. Stale NE names are fixed (Astana).
- Nauru's capital, Yaren, is hand-placed from reference coordinates; NE has no row for it.
- No capital card where the capital shares the country's name and dot: Monaco, Vatican, Singapore, San Marino, Luxembourg.
- No capital card for Palestine, the territories or the disputed areas.

That gives 191 capital cards.

**Layers.** WS4 pins `populated_places`, `admin_0_map_units`, `admin_0_disputed_areas` and `boundary_lines_disputed_areas`, and records how each outline is composed in `docs/research/ne-political-layers.md`.

**Adjacency** is computed at build time from the same recognised-border outlines the country cards draw.

- Two countries touch when their outlines intersect after a 1 km buffer, which absorbs 10m slivers.
- Countries within 200 km across water are linked by a sea edge, so island states aren't isolated (UK–France, Japan–Korea, Sri Lanka–India).
- Hand edits go in `data/adjacency.yaml` as `add` or `remove` entries, each with a `reason`.
- The result is cached in `build/adjacency.json`, keyed by a hash of its inputs, as `build/siblings.json` is.

## Consequences

- The basemap changes to recognised borders, so all 132 feature maps re-render once (P4).
- Outlines for Ukraine, Georgia, Moldova, Cyprus, Syria and Somalia need disputed-area parts added back, and Morocco's needs Western Sahara removed. Each composition is a reviewable table row in the research note.
- Cutting Western Sahara out of Morocco removes the Morocco–Mauritania land border. The region 10 to 11 crossing then rests on a distance edge or an `adjacency.yaml` entry. The P3 walk review should confirm it.
- Several dispute cards are time-sensitive: Somaliland recognition, the Chagos handover, Essequibo after the ICJ judgment, Western Sahara after UNSC resolution 2797, and the Golan beyond the 1974 line. The [Territories](../world-atlas-plan.md#territories) section lists what to verify before each release.
- The Russian-occupied areas of Ukraine since 2022 get no card, because NE has no line for them.
