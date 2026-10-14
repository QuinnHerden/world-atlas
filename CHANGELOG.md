# Changelog

All notable changes to this deck are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-10-14

The first **World Atlas** release. It replaces the Geographic Features deck (v1) and adds the political map.

### Added

- 607 cards: 197 countries, 191 capitals, 42 other cities, 23 territories, 15 disputed areas, 7 continents and 132 physical features.
- A fixed study order: an orientation block, then pass 1 once round a ring of 21 regions, then pass 2 round the ring again with the tier 3 features ([ADR 0009](docs/adr/0009-curriculum-order.md)).
- A short note on every card back, under the answer.
- `world-atlas-guide.pdf`, a printable study guide in the same order: entry N is the Nth new card. `make guide REGION=NN` builds one region.
- Tags on every card: `kind::`, `pass::`, `region::` (political cards), `tier::`, `category::` and `id_`.
- `data/positions.lock`, which fixes each card's new-card position and records its pass and region. It is frozen and append-only: cards added in later releases never move an existing card, so fresh and existing collections see the same order ([ADR 0006](docs/adr/0006-positions-lock-and-pos-footnote.md)).
- A freeze guard: every build checks the lock against the ones on `origin/main` and the newest release tag, and fails if an existing entry changed.
- `make import-test`, which checks a fresh import, a region filtered deck, Check Database and the upgrade from v1 on Anki 26.09.3.

### Changed

- Renamed from Geographic Features to World Atlas. The package is now `world-atlas.apkg` ([ADR 0007](docs/adr/0007-rename-and-migration.md)).
- One flat deck, `World Atlas`, replaces the tier subdecks.
- The build requires ankc 0.6. ankc 0.5 can't write positions, so it fails against the frozen lock.
- Renders are reproducible: a cold build from a clean clone gives byte-identical maps.
- Equatorial Guinea's capital card is Ciudad de la Paz (decree of 2 January 2026). The back names Malabo as the former capital.
- All 73 fact-check items were closed before release. Sources are in [docs/research/verify-log.md](docs/research/verify-log.md).

### Removed

- 34 v1 cards are retired: all 10 passes and corridors, all 15 islands and 9 climate systems. Importing never deletes notes, so they stay in an upgraded collection until you delete them. The README's [Retired cards](README.md#retired-cards) section has searches that find them.

### Upgrade notes

- Upgrading from v1 keeps review history. Notes are matched by GUID and updated in place.
- The matched cards stay in `Geographic Features` and keep their old queue positions (0 to 131). Move them to `World Atlas` with **Change Deck**; see [Upgrading from Geographic Features](README.md#upgrading-from-geographic-features).
- Run **Tools → Check Media** afterwards to delete the old maps.

## [1.0.0] - 2026-10-13

The **Geographic Features** deck. Tagged retrospectively at commit `b63bf0e`.

### Added

- 166 physical-feature cards, including 102 Natural Earth features, 31 hand-authored places and 15 climate systems.
- Tier subdecks: `Geographic Features::<Category>::Tier <n>`.
- A controlled type vocabulary grouped into families.
- Structured provenance for hand-authored geometry, with checks.
- North-up framing with a 2,600 km minimum width, and a fixed world inset.
- Built with ankc 0.4. Output: `geographic-features.apkg`.

[2.0.0]: https://github.com/QuinnHerden/world-atlas/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/QuinnHerden/world-atlas/releases/tag/v1.0.0
