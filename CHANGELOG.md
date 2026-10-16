# Changelog

All notable changes to this deck are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

Pre-release history: the builds before v1.0.0 (Geographic Features, then two World Atlas pre-releases) are archived as the tags `archive/v1.0.0`, `archive/v2.0.0` and `archive/v3.0.0`; their changelog is in `CHANGELOG.md` at `archive/v3.0.0`.

## [1.0.0] - 2026-10-16

The first release of **World Atlas**: 554 map cards for the political and physical map of the world, studied in four blocks (continents, then the oceans; countries, territories, subnationals and disputed areas; physical features; capitals and cities), each round a ring of 21 regions ([ADR 0009](docs/adr/0009-curriculum-order.md)). Versioning restarted here.

Since the v3.0.0 pre-release (607 cards): 9 added and 62 retired. The disputed areas go from 15 to 9. A disputed area keeps a card only if it is a de facto separate entity or lies outside every recognised border or across several; a claim inside one state's recognised borders, or one a country note describes easily, moves into the country notes ([ADR 0008](docs/adr/0008-state-list-borders-adjacency.md#amendment-fewer-dispute-cards-v301)). Microstates and small island states lose their capital cards, the other cities go from 42 to 25, and a new kind of card covers part of a state.

### Added

- Four companion decks, each its own package: Italian Regions (20 cards), US States (50 states and DC), Brazilian States (26 states and the Distrito Federal) and Canadian Provinces and Territories (13). Every card shows its country on one fixed map with internal borders, and all but the 14 largest a zoomed inset, and the back has a short note. Italian and Brazilian cards use the Italian and Portuguese names only. They don't change World Atlas ([ADR 0012](docs/adr/0012-companion-decks.md), [ADR 0013](docs/adr/0013-subdivision-framing.md)).
- `positions.lock` entries name their deck (`deck=`). Each deck has its own position range, and a card's deck is frozen like its position.
- Kashmir: one dispute card for the whole former princely state, the Indian-, Pakistani- and Chinese-held parts together (India, Pakistan and China as parties). It replaces three cards; Natural Earth's Samdu, Tirpani and Bara Hotii slivers, outside the former state, are left out.
- Territory cards for the Cook Islands, self-governing in free association with New Zealand, placed after New Zealand on the Polynesia frame; and for Akrotiri and Dhekelia, the British base areas on Cyprus, placed after Cyprus with an inset at the island's scale.
- Subnational cards (`kind::subnational`), a new kind for part of a state: England, Scotland, Wales and Northern Ireland (front word "Constituent country", placed after the United Kingdom) and Kaliningrad Oblast ("Exclave", placed after Lithuania). They are in the `countries` block and their own category, `category::subnational`, drawn with a solid outline like a country, and have no capital cards. In `territories.yaml` they are `kind: subnational` entries with `type`, `state`, `status_line` and an optional `within` box that keeps only the outline's parts inside it; `curriculum.yaml` places them with `subnationals:` maps.
- Toronto, after Ottawa.
- A region can set its own frame margin, `frame_margin` in `curriculum.yaml` ([ADR 0010](docs/adr/0010-region-framing.md#decision)).
- Per-card `frame:` overrides `include` (the frame also holds other bodies), `ring: false` or `ring: oval`, and `inset_centre`. The Cook Islands and Akrotiri and Dhekelia use `ring: false`.
- [CONTRIBUTING.md](CONTRIBUTING.md): setup, recipes for common changes, the checks before a pull request, and the release process.
- Every per-card frame override carries a `reason:`, as do a country's `mainland` crop (`mainland_reason:`) and a region's pinned frame and margin (`frame_reason:`, `frame_margin_reason:`). `make check-data` fails without one ([CONTRIBUTING.md](CONTRIBUTING.md)).
- `retired: true` on territory, subnational and dispute entries, on cities and on a country's `capital:`, as on features: the entry and its uid stay, but it makes no card and has no curriculum placement. `make check-data` fails if a tier-3 state's capital isn't retired.

### Removed

- 7 dispute cards: Kashmir (Indian-administered), Kashmir (Pakistani-administered) and Aksai Chin, merged into Kashmir; Arunachal Pradesh, the Golan Heights, the southern Kuril Islands and Essequibo, now in the country notes.
- 29 capital cards. A tier-3 state (a microstate or small island state) no longer gets a capital card, extending the rule for capitals that share their country's name and dot: Andorra la Vella, Vaduz, Valletta, Manama, Praia, São Tomé, Moroni, Port Louis, Victoria, Malé, Bandar Seri Begawan, Port Vila, Suva, Nuku'alofa, Apia, Funafuti, Tarawa, Yaren, Majuro, Palikir, Ngerulmud, Port of Spain, Saint George's, Kingstown, Bridgetown, Castries, Roseau, Saint John's and Basseterre. The country notes are unchanged.
- 18 city cards, of lower salience than the cities kept (no reason is recorded for each): Rotterdam, Seville, Hamburg, Frankfurt, Volgograd, Aleppo, Medina, Zanzibar, Johannesburg, Samarkand, Isfahan, Guangzhou, Xi'an, Osaka, Malacca, New Orleans, Potosí and Montreal. No facts from their notes moved to other notes.
- The Crimea feature card (Peninsula), which had the same outline and answer as the Crimea dispute card.
- 7 tier-3 feature cards: Pearl River, Mongolian Plateau, Isthmus of Kra, Lake Titicaca, Lake Chad, Lombok Strait and Sunda Strait.
- **The `tier::` tags.** No card carries one; the tier stays internal to the study order. Re-importing updates each note's tags, so existing notes lose theirs, and a filtered deck that searched `tier::` finds nothing.
- The PDF study guide (`world-atlas-guide.pdf`, `make guide` and the optional `guide` dependency group). Notes are on the card backs; a release carries the five `.apkg` packages and `SHA256SUMS`.

Each retired entry keeps its uid, and `positions.lock` keeps its slot.

### Changed

- The four oceans (Atlantic, Indian, Pacific, Arctic) come straight after the seven continents, as new cards 8 to 11, instead of opening the physical features. They keep `block::features` ([ADR 0009](docs/adr/0009-curriculum-order.md)).
- Country notes now carry the retired disputes: Syria and Israel the Golan; Russia and Japan the southern Kurils; India and China Arunachal Pradesh ("Zangnan"); India, Pakistan and China their parts of Kashmir; Guyana and Venezuela Essequibo. Three claims that never had a card are added too: Ukraine's note gives Russia's 2022 claim to annex four oblasts, rejected by UN General Assembly resolution ES-11/4, and the China and Japan notes give the Senkaku Islands.
- The Spratly Islands note adds the Paracels and Scarborough Shoal as part of the same South China Sea dispute. The Crimea dispute note adds the Crimean War (1853–56), from the retired feature's note.
- The British Indian Ocean Territory note: the 2025 treaty transferring sovereignty to Mauritius has not taken effect.
- Brussels, Amsterdam, Pretoria, Sucre, Kuala Lumpur, Doha, Barcelona and Kyoto lose their close-dot frame, because the nearby dot that caused it was retired; they are framed on their region with an inset. Retired disputes no longer count as region members, so the frames of regions 06 (slightly), 14 (South Asia, narrower in the east) and 16 (East Asia, narrower) change, for 47 cards.
- `data/positions.lock` is `series: 1` (it was series 3 in the pre-releases), with every entry of the v3.0.0 pre-release unchanged but the four oceans, moved from 121,500-123,000 to 3,600-3,900 (`positions.RESTART_MOVES`). It appends 9 uids and keeps every retired uid's slot: 616 uids for 554 cards. The freeze guard also reads the `archive/vX.Y.Z` tags: every lock keeps every uid the pre-releases shipped, and series 1 extends archived v3.0.0's lock, but for those four moves ([ADR 0011](docs/adr/0011-refreezing-at-a-major-version.md#amendment-versioning-restarted-at-v100)).
- Card notes no longer refer to the deck or to other cards. Sentences that only pointed at other cards ("has no card of its own") are gone; where a sentence carried a real fact, such as which recognised borders include a disputed area, the fact stays as plain geography. The continent notes describe the usual Europe–Asia boundary and the usual extent of North America and Oceania without claiming them for the deck. Re-importing the package updates them on existing cards and keeps scheduling.
- Horn & East Africa is framed wider (`frame_margin: 1.4`, 9,398 km, was 7,384 km), so Egypt, Libya, Malawi, Zambia and Mozambique show round it. Somalia now shares the region frame. Tanzania's frame and its cities' move south to take in Malawi, Zambia and Mozambique, and Sudan's move north to the Mediterranean, at the same width.
- New Zealand's and Papua New Guinea's maps, and their capitals', take in the whole of Australia.
- Micronesia, Kiribati and French Polynesia get one oval round the whole state instead of a ring per island group. Tonga is no longer ringed.
- Aruba's and Curaçao's insets show the ABC islands together.

[1.0.0]: https://github.com/QuinnHerden/world-atlas/releases/tag/v1.0.0
