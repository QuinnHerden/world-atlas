# Changelog

All notable changes to this deck are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [2.1.0] - 2026-10-15

Political and city maps are redrawn on their curriculum regions, and Greenland moves to Nordic & Baltic.

### Added

- Detail insets: a small country, territory or disputed area gets a zoomed corner inset of its main body, joined to it by leader lines. Every capital and city card gets one round its dot ([ADR 0010](docs/adr/0010-region-framing.md)).
- Fixed sub-frames for Oceania (Melanesia, Micronesia, central Pacific, Polynesia) and the Lesser Antilles. The Lesser Antilles frame has a small Caribbean locator.
- Per-card `frame: {inset, inset_km}` overrides in `countries.yaml` and `territories.yaml`. Kuwait and the Spratly Islands use them.
- `anchor` overrides for features and territories, each with an `anchor_reason`: the card comes right after its anchor in the same pass and region ([ADR 0009](docs/adr/0009-curriculum-order.md)).
- Retired territories (`retired: true`), kept with their uid and lock entry, so a political card can move region by retire and replace ([ADR 0006](docs/adr/0006-positions-lock-and-pos-footnote.md)).

### Changed

- Country, territory and dispute cards are framed on their curriculum region: one frame round the region's members, at least 3,500 km wide, shared by the cards that fit it. States whose v2.0 frame was over 8,000 km wide keep it.
- Capital and city cards are framed on their country's region. A close-dot city shows its region, with the close-up in its inset; in a giant country (Kinshasa, Kyoto, Osaka) it keeps the 1,000 km close-dot frame.
- Country, territory, dispute, capital and city cards no longer show the world locator. Feature cards keep it.
- Political land is ringed only at microstate scale, per island group.
- Greenland moves from North & Central America (region 19) to Nordic & Baltic (region 02), right after Iceland. The GIUK Gap now follows Greenland. Greenland stays in North America on the continent cards.

### Removed

- The v2.0 Greenland card (`24rdGoHY6W`) is retired and replaced by a new card (`zjAlvxD9jl`). The deck still has 607 active cards and 23 territories.

### Upgrade notes

- Re-importing updates the maps and tags of existing cards in place. They keep their review history and queue position.
- Greenland is a new note. It arrives as a new card between Iceland and the GIUK Gap.
- The old Greenland card stays in an upgraded collection, with its review history, until you delete it. Its history does not carry over to the new card. Find it with `deck:"World Atlas" tag:id_territory_greenland tag:region::19`; see [Upgrading from v2.0](README.md#upgrading-from-v20).
- Run **Tools → Check Media** afterwards to delete the old maps.

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

[2.1.0]: https://github.com/QuinnHerden/world-atlas/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/QuinnHerden/world-atlas/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/QuinnHerden/world-atlas/releases/tag/v1.0.0
