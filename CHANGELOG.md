# Changelog

All notable changes to this deck are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [3.0.1] - Unreleased

554 cards, against 607 in v3.0.0: 9 added and 62 retired. The disputed areas go from 15 to 9. A disputed area keeps a card only if it is a de facto separate entity or lies outside every recognised border or across several; a claim inside one state's recognised borders, or one a country note describes easily, moves into the country notes ([ADR 0008](docs/adr/0008-state-list-borders-adjacency.md#amendment-fewer-dispute-cards-v301)). Microstates and small island states lose their capital cards, the other cities go from 42 to 25, and a new kind of card covers part of a state.

### Added

- Kashmir: one dispute card for the whole former princely state, the Indian-, Pakistani- and Chinese-held parts together (India, Pakistan and China as parties). It replaces three cards; Natural Earth's Samdu, Tirpani and Bara Hotii slivers, outside the former state, are left out.
- Territory cards for the Cook Islands, self-governing in free association with New Zealand, placed after New Zealand on the Polynesia frame; and for Akrotiri and Dhekelia, the British base areas on Cyprus, placed after Cyprus with an inset at the island's scale.
- Subnational cards (`kind::subnational`), a new kind for part of a state: England, Scotland, Wales and Northern Ireland (front word "Constituent country", placed after the United Kingdom) and Kaliningrad Oblast ("Exclave", placed after Lithuania). They are in the `countries` block and their own category, `category::subnational`, drawn with a solid outline like a country, and have no capital cards. In `territories.yaml` they are `kind: subnational` entries with `type`, `state`, `status_line` and an optional `within` box that keeps only the outline's parts inside it; `curriculum.yaml` places them with `subnationals:` maps.
- Toronto, after Ottawa.
- A region can set its own frame margin, `frame_margin` in `curriculum.yaml` ([ADR 0010](docs/adr/0010-region-framing.md#decision)).
- Per-card `frame:` overrides `include` (the frame also holds other bodies), `ring: false` or `ring: oval`, and `inset_centre`. The Cook Islands and Akrotiri and Dhekelia use `ring: false`.
- `retired: true` on territory, subnational and dispute entries, on cities and on a country's `capital:`, as on features: the entry and its uid stay, but it makes no card and has no curriculum placement. `make check-data` fails if a tier-3 state's capital isn't retired.

### Removed

- 7 dispute cards: Kashmir (Indian-administered), Kashmir (Pakistani-administered) and Aksai Chin, merged into Kashmir; Arunachal Pradesh, the Golan Heights, the southern Kuril Islands and Essequibo, now in the country notes.
- 29 capital cards. A tier-3 state (a microstate or small island state) no longer gets a capital card, extending the rule for capitals that share their country's name and dot: Andorra la Vella, Vaduz, Valletta, Manama, Praia, São Tomé, Moroni, Port Louis, Victoria, Malé, Bandar Seri Begawan, Port Vila, Suva, Nuku'alofa, Apia, Funafuti, Tarawa, Yaren, Majuro, Palikir, Ngerulmud, Port of Spain, Saint George's, Kingstown, Bridgetown, Castries, Roseau, Saint John's and Basseterre. The country notes are unchanged.
- 18 city cards, of lower salience than the cities kept (no reason is recorded for each): Rotterdam, Seville, Hamburg, Frankfurt, Volgograd, Aleppo, Medina, Zanzibar, Johannesburg, Samarkand, Isfahan, Guangzhou, Xi'an, Osaka, Malacca, New Orleans, Potosí and Montreal. No facts from their notes moved to other notes.
- The Crimea feature card (Peninsula), which had the same outline and answer as the Crimea dispute card.
- 7 tier-3 feature cards: Pearl River, Mongolian Plateau, Isthmus of Kra, Lake Titicaca, Lake Chad, Lombok Strait and Sunda Strait.
- **The `tier::` tags.** No card carries one; the tier stays internal to the study order. Re-importing updates each note's tags, so existing notes lose theirs, and a filtered deck that searched `tier::` finds nothing.

Each retired entry keeps its uid, and `positions.lock` keeps its slot. Upgraded collections keep the 62 cards until they are deleted; [Retired cards](README.md#retired-cards) gives the Browse search that finds exactly those 62.

### Changed

- Country notes now carry the retired disputes: Syria and Israel the Golan; Russia and Japan the southern Kurils; India and China Arunachal Pradesh ("Zangnan"); India, Pakistan and China their parts of Kashmir; Guyana and Venezuela Essequibo. Three claims that never had a card are added too: Ukraine's note gives Russia's 2022 claim to annex four oblasts, rejected by UN General Assembly resolution ES-11/4, and the China and Japan notes give the Senkaku Islands.
- The Spratly Islands note adds the Paracels and Scarborough Shoal as part of the same South China Sea dispute. The Crimea dispute note adds the Crimean War (1853–56), from the retired feature's note.
- The British Indian Ocean Territory note: the 2025 treaty transferring sovereignty to Mauritius has not taken effect.
- Brussels, Amsterdam, Pretoria, Sucre, Kuala Lumpur, Doha, Barcelona and Kyoto lose their close-dot frame, because the nearby dot that caused it was retired; they are framed on their region with an inset. Retired disputes no longer count as region members, so the frames of regions 06 (slightly), 14 (South Asia, narrower in the east) and 16 (East Asia, narrower) change, for 47 cards.
- `positions.lock` (series 3) appends 9 uids and keeps every retired uid's slot: 616 uids for 554 cards.
- Card notes no longer refer to the deck or to other cards. Sentences that only pointed at other cards ("has no card of its own") are gone; where a sentence carried a real fact, such as which recognised borders include a disputed area, the fact stays as plain geography. The continent notes describe the usual Europe–Asia boundary and the usual extent of North America and Oceania without claiming them for the deck. Notes appear on card backs and in the study guide; re-importing the package updates them on existing cards and keeps scheduling.
- Horn & East Africa is framed wider (`frame_margin: 1.4`, 9,398 km, was 7,384 km), so Egypt, Libya, Malawi, Zambia and Mozambique show round it. Somalia now shares the region frame. Tanzania's frame and its cities' move south to take in Malawi, Zambia and Mozambique, and Sudan's move north to the Mediterranean, at the same width.
- New Zealand's and Papua New Guinea's maps, and their capitals', take in the whole of Australia.
- Micronesia, Kiribati and French Polynesia get one oval round the whole state instead of a ring per island group. Tonga is no longer ringed.
- Aruba's and Curaçao's insets show the ABC islands together.

## [3.0.0] - 2026-10-16

A new study order in four blocks, political and city maps redrawn on their curriculum regions, and Greenland in Nordic & Baltic. The new order reaches fresh imports only; see the upgrade notes.

### Added

- Detail insets: a small country, territory or disputed area gets a zoomed corner inset of its main body, joined to it by leader lines. Every capital and city card gets one round its dot ([ADR 0010](docs/adr/0010-region-framing.md)).
- Fixed sub-frames for Oceania (Melanesia, Micronesia, central Pacific, Polynesia) and the Lesser Antilles. The Lesser Antilles frame has a small Caribbean locator.
- Per-card `frame: {inset, inset_km}` overrides in `countries.yaml` and `territories.yaml`. Kuwait and the Spratly Islands use them.
- `block::` tags: `block::continents`, `block::countries`, `block::features` and `block::cities`.

### Changed

- **Breaking:** the study order is now four blocks ([ADR 0009](docs/adr/0009-curriculum-order.md#amendment-four-blocks-v300)): the 7 continents; then the 235 countries, territories and disputed areas, region by region round the ring; then the 132 physical features, oceans and planetary winds first and tier 3 last; then the 233 capitals and cities, region by region in the same country order, each capital before its country's other cities. v2 interleaved every kind in one pass round the ring, with a second pass for tier 3.
- **Breaking:** the `pass::` tags are replaced by `block::` tags. Filtered decks that search `pass::` find nothing. `region::` tags stay on political cards and cities.
- **Breaking:** `data/positions.lock` is re-frozen as series 3 ([ADR 0011](docs/adr/0011-refreezing-at-a-major-version.md)). Every card has a new position, regenerated at stride 500 (500 to 303,500). The lock declares its series, and entries record `block=` instead of `pass=`. The freeze guard compares the lock only with locks of the same series; a new series is allowed only as the next major version, and must keep every uid of the release before it.
- Greenland moves from North & Central America (region 19) to Nordic & Baltic (region 02), right after Iceland (card 23). It keeps its card and uid (`24rdGoHY6W`). It stays in North America on the continent cards.
- Country, territory and dispute cards are framed on their curriculum region: one frame round the region's members, at least 3,500 km wide, shared by the cards that fit it. States whose v2 frame was over 8,000 km wide keep it.
- Capital and city cards are framed on their country's region. A close-dot city shows its region, with the close-up in its inset; in a giant country (Kinshasa, Kyoto, Osaka) it keeps the 1,000 km close-dot frame.
- Country, territory, dispute, capital and city cards no longer show the world locator. Feature cards keep it.
- Political land is ringed only at microstate scale, per island group.
- The study guide is sectioned by block, then region.
- A release build names its version, `make all RELEASE=1 RELEASE_VERSION=vX.Y.Z`, whose major must equal the lock's series. Release tags are read with `git tag --merged HEAD` (exact `vX.Y.Z` only), and a release build fails on a shallow clone.
- Features no longer take an `anchor` override; the schema rejects one. Cities keep theirs.

### Upgrade notes

- Re-importing updates maps and tags (`block::`, `region::`) in place. Cards keep their review history.
- Re-importing never changes a card's queue position, so an upgraded collection keeps the v2 interleaved order. To get the v3 order, delete the deck and import fresh (losing review history), or reposition the unstudied cards block by block in **Browse**; see [Upgrading from v2](README.md#upgrading-from-v2). Repositioning keeps the v2 order within each block, which is close to v3's but not the same.
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

[3.0.1]: https://github.com/QuinnHerden/world-atlas/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/QuinnHerden/world-atlas/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/QuinnHerden/world-atlas/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/QuinnHerden/world-atlas/releases/tag/v1.0.0
