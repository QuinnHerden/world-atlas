# World Atlas

An Anki deck of 561 map cards that teaches the political and physical map of the world together: 197 countries, 162 capitals, 25 other cities, 25 territories, 5 subdivisions (England, Scotland, Wales, Northern Ireland and Kaliningrad), 9 disputed areas, the 7 continents and 131 physical features that shaped settlement, trade and war (oceans and seas, straits, rivers, mountain ranges, plains, peninsulas and six climate systems). Each card front shows an unlabelled map with one place highlighted in red and its type ("Country", "City", "Strait") above it. The back gives its name, and under a thin rule, in smaller muted text, a short note on why it matters (the same note the study guide prints).

World Atlas grew out of the **Geographic Features** deck (v1), which held physical features alone. Its 131 active feature notes carry over, with their review history; see [Upgrading from Geographic Features](#upgrading-from-geographic-features).

Current release: [v3.0.0](https://github.com/QuinnHerden/world-atlas/releases/tag/v3.0.0) (2026-10-16). It studies the map in four blocks (continents, countries, physical features, then capitals and cities), redraws the political and city maps on their regions, and moves Greenland to the Nordic & Baltic region. An upgraded v2 collection keeps its old order unless you change it; see [Upgrading from v2](#upgrading-from-v2). Changes by release are in [CHANGELOG.md](CHANGELOG.md).

Maps are rendered from [Natural Earth](https://www.naturalearthdata.com/) data. The deck is compiled with [ankcompiler](https://github.com/QuinnHerden/ankcompiler) 0.6.

- How the build works: [docs/architecture.md](docs/architecture.md)
- Why it works that way: [docs/adr/](docs/adr/)
- The plan behind World Atlas (curriculum, decisions, build phases): [docs/world-atlas-plan.md](docs/world-atlas-plan.md)

## Download and import

Download two files from the [latest release](https://github.com/QuinnHerden/world-atlas/releases/latest):

- `world-atlas.apkg`: the deck.
- `world-atlas-guide.pdf`: the printable study guide.

**New to the deck.** In Anki, choose **File → Import** and pick `world-atlas.apkg`. Every card lands in one deck, `World Atlas`, in the study order described under [Study](#study).

**Upgrading from v2.** Import it the same way. Your cards are updated in place but keep their v2 order; [Upgrading from v2](#upgrading-from-v2) covers what changes and how to switch to the new order.

**Upgrading from Geographic Features.** Follow [Upgrading from Geographic Features](#upgrading-from-geographic-features) instead. It covers keeping your review history and moving the old cards into `World Atlas`.

**The guide** prints every card in the order Anki shows new cards: entry N is the Nth new card, with its map, its answer and its note. It is sectioned by the four blocks, then by region. For a single region, build it yourself with `make guide REGION=NN` (see [Build](#build)).

## Build

Requires [uv](https://docs.astral.sh/uv/), `ankc` 0.6.x (on PyPI as `ankcompiler`) and an authenticated `gh` CLI (Natural Earth downloads go through the GitHub API).

```sh
make ids        # mint uids for new entries, then commit features.yaml
make positions  # give new uids a place in data/positions.lock, then commit it
make all        # test → fetch → check-data → render → deck → check → build
make adjacency  # the country adjacency graph and its report
```

`ANKC` picks the compiler, e.g. `make all ANKC="uv run --with ../ankcompiler ankc"`. Every card gets its new-card position from `data/positions.lock` as a `[^pos]` footnote. The lock is frozen and append-only, so ankc 0.5, which can't write positions, fails the build.

Output: `dist/world-atlas.apkg`. Import it in Anki with **File → Import**.

A release build names its version: `make all RELEASE=1 RELEASE_VERSION=v3.0.0`. It fails without `RELEASE_VERSION` (unless a release tag is on `HEAD`), when the version's major isn't the lock's series, while a note has an open verify item, or when the freeze guard can't run: no readable `origin/main`, a shallow clone, or no tags. Fetch the full history and tags first.

Rendering takes about 10 s per map and is cached, so only changed maps re-render. `JOBS=2 make all` renders in parallel; each worker needs about 1.5 GB of RAM.

`make guide` writes `build/world-atlas-guide.pdf`, a printable guide to every card in the order Anki shows new cards: entry N is the Nth new card, with its map, answer and a short note on why it matters. It is sectioned by the four blocks, then by region. `make guide REGION=NN` writes `build/world-atlas-guide-NN.pdf` with one region only: that region's countries, capitals, cities, subdivisions, territories and disputed areas, plus the features the study order places in its run. The `tag:region::NN` filtered deck (see **Pacing**) holds the same political cards but no features, because features have no region tag. It uses the optional `guide` dependency group (reportlab).

## Study

Every card is in one deck, `World Atlas`, with no subdecks. Each card has these tags:

- `kind::<kind>`: `country` (197), `capital` (162), `city` (25), `territory` (25), `subdivision` (5), `dispute` (9), `continent` (7) or `feature` (131). A subdivision is a constituent country of the United Kingdom or an exclave (Kaliningrad)
- `block::continents`, `block::countries`, `block::features` or `block::cities` (7, 236, 131 and 187 cards): the study block. Countries, subdivisions, territories and disputed areas are in `countries`; capitals and other cities in `cities`
- `region::01` to `region::21`: the region of a country, capital, city, subdivision, territory or disputed area (features have none)
- `tier::1`, `tier::2` or `tier::3` (380, 137 and 44 cards)
- `category::<slug>`: `countries`, `cities` (capitals and other cities), `territories` (territories, subdivisions and disputed areas), `continents`, or a feature category: `water-bodies`, `straits-chokepoints`, `mountain-ranges`, `rivers-deltas`, `deserts-plateaus-plains`, `peninsulas-isthmuses`, `regions-rifts` or `climate-systems`
- `id_<id>` for a feature, e.g. `id_nile`, or `id_<kind>_<id>` for any other kind, e.g. `id_country_france`

New cards come up in a fixed order, in four blocks:

1. **Continents** (7 cards, about half a day at 15 a day): Europe first, Antarctica last.
2. **Countries, territories and disputed areas** (236 cards, about 16 days): once round a ring of 21 regions, starting in Western Europe with Portugal and ending in the Caribbean with the Bahamas. Within a region you go country by neighbouring country. Microstates and enclaves come right after a neighbour (Andorra after Spain, Monaco after France), and subdivisions, territories and disputed areas after the country they are placed with (England and Gibraltar after the United Kingdom, Kaliningrad after Lithuania, Greenland after Iceland).
3. **Physical features** (131 cards, about 9 days): the oceans and planetary winds first, then the rest round the ring, region by region. The 10 tier 3 features come last.
4. **Capitals and cities** (187 cards, about 12½ days): round the ring again, in the same country order. Each country's capital comes first, then its other cities. Microstates and small island states have no capital card.

At 15 new cards a day that is about 5½ weeks. `data/curriculum.yaml` names the regions. [ADR 0009](docs/adr/0009-curriculum-order.md) explains the design.

To study a subset, make a filtered deck (**Tools → Create Filtered Deck**) with a search and the order "Order due". Some searches:

| Search | Gives |
|---|---|
| `deck:"World Atlas" tag:region::05 is:new` | Region 05's countries, territories and disputed areas, then its capitals and cities |
| `deck:"World Atlas" tag:block::features is:new` | The physical features, in study order |
| `deck:"World Atlas" tag:block::cities tag:region::16` | East Asia's capitals and cities |
| `deck:"World Atlas" tag:kind::capital` | Every capital |

**Re-importing a new build** updates each note's text (every card's back, its note included), map and tags, but not its card's deck or new-card position, and it never deletes notes:

- **New cards:** a later release of the same major version slots its new cards in between existing ones. No existing card moves, so a fresh import and an updated collection see the same order. A new major version may change the order itself, as v3.0.0 did; existing cards then keep their old place (see [Upgrading from v2](#upgrading-from-v2)).
- **Moved tier or category:** the card keeps its place in the queue. To move it anyway, select it in **Browse** and use **Cards → Reposition**.
- **Old maps:** a re-rendered map gets a new file name. Run **Tools → Check Media** to delete the old image.
- **Older imports:** cards imported from v1, v2 or a pre-release build keep the positions they had then. If you haven't started studying, delete the deck and import the new package to get the full study order.

### Upgrading from v3.0.0

v3.0.1 has 561 cards against v3.0.0's 607. It adds 9 cards and retires 55:

- **New:** Kashmir, one disputed-area card for the whole former princely state (the Indian-, Pakistani- and Chinese-held parts); England, Scotland, Wales and Northern Ireland ("Constituent country") and Kaliningrad Oblast ("Exclave"), a new kind of card for part of a state; the Cook Islands and Akrotiri and Dhekelia, as territories; and Toronto.
- **Retired disputed areas (7):** Kashmir (Indian-administered), Kashmir (Pakistani-administered) and Aksai Chin, merged into Kashmir; Arunachal Pradesh, the Golan Heights, the southern Kuril Islands and Essequibo, now covered in the notes of the countries involved.
- **Retired capitals (29):** a microstate or small island state (tier 3) no longer has a capital card, for example Valletta, Manama or Suva.
- **Retired cities (18):** Rotterdam, Seville, Hamburg, Frankfurt, Volgograd, Aleppo, Medina, Zanzibar, Johannesburg, Samarkand, Isfahan, Guangzhou, Xi'an, Osaka, Malacca, New Orleans, Potosí and Montreal.
- **Retired feature (1):** Crimea (Peninsula). It showed the same outline and answer as the Crimea disputed-area card, which stays.

Some maps are redrawn. Brussels, Amsterdam, Pretoria, Sucre, Kuala Lumpur, Doha, Barcelona and Kyoto lost their close-up frame, because the nearby city that needed it was retired; they now show their region with an inset. The South Asia and East Asia region maps are narrower, and the Caucasus & Anatolia map changes slightly, because retired disputed areas no longer shape them.

Import the package as usual. The new cards slot in among the cards you haven't studied yet, and no existing card moves. The 55 retired cards stay in your collection until you delete them; see [Retired cards](#retired-cards).

### Upgrading from v2

**What changed in v3:**

- New cards come in four blocks: continents, countries, physical features, then capitals and cities (see [Study](#study)). v2 mixed them in one pass round the ring.
- The `pass::` tags are gone. Each card has a `block::` tag instead. A filtered deck that searched `pass::` needs a new search.
- Country, territory and disputed-area maps are drawn on their region's map, so cards you study together share one frame. The largest states (Russia, Canada, Brazil and the like) keep their v2 framing.
- Capital and city maps use their country's region map too.
- Small places get a zoomed detail inset in a corner, joined to them by leader lines. Every capital and city card gets one round its dot.
- Country, territory, disputed-area, capital and city cards no longer show the small world map. Feature cards still do.
- Greenland moved from North & Central America (region 19) to Nordic & Baltic (region 02), right after Iceland. It is the same card, with the same review history.

**Importing.** Import `world-atlas.apkg` with **File → Import**, keeping the default **Update notes: If newer**. Your cards get their new maps and tags (`block::`, `region::`) in place, and keep their review history.

Re-importing never changes a card's place in the new-card queue, so **an upgraded collection keeps the v2 order**. The new order applies to fresh imports only. To get it, pick one:

- **Start over.** Delete the `World Atlas` deck, then import `world-atlas.apkg`. You lose your review history.
- **Reposition the cards you haven't studied.** In **Browse**:
  1. Show cards, not notes, and sort by the **Due** column, ascending.
  2. Search `deck:"World Atlas" is:new tag:block::continents` and select all cards.
  3. Choose **Cards → Reposition**. Set **Start position** to 500 and **Step** to 1. Turn **Randomize order** and **Shift position of existing cards** off. Click **OK**.
  4. Repeat steps 2 and 3 for the other blocks, in order:

     | Search | Start position |
     |---|---|
     | `deck:"World Atlas" is:new tag:block::countries` | 4000 |
     | `deck:"World Atlas" is:new tag:block::features` | 121500 |
     | `deck:"World Atlas" is:new tag:block::cities` | 187500 |

  This moves only cards you haven't studied. It puts the blocks in v3 order, but within each block the cards keep their v2 order. That is close to v3's order but not the same. For example, Greenland stays among the North American countries instead of coming after Iceland.

**Old maps** stay in your media folder. Run **Tools → Check Media** to delete them.

### Upgrading from Geographic Features

World Atlas v2.0.0 replaces the **Geographic Features** deck (v1), which held the physical features alone. World Atlas has 561 cards: 131 of the same 132 features (Crimea was retired in v3.0.1), plus countries, capitals, cities, territories, subdivisions, disputed areas and continents. Pick one of the two paths below.

**Fresh start.** Use this if you haven't studied much. You get the full study order.

1. Delete the `Geographic Features` deck. Anki deletes its cards and their review history with it.
2. Import `world-atlas.apkg` with **File → Import**.

**Keep your review history.** Your feature cards keep their scheduling. The import matches each feature note by its note ID (GUID) and updates it in place. Anki doesn't move existing cards on import, so the matched cards stay in `Geographic Features`. The new cards land in `World Atlas`. Keep the import's default **Update notes: If newer**; if you edited the `AnkCompiler-Question_Answer` note type, tick **Merge notetypes** too.

1. Import `world-atlas.apkg` with **File → Import**.
2. In **Browse**, search `deck:"Geographic Features"` and select all cards. The search also finds cards in old subdecks (`Geographic Features::<Category>::Tier <n>`), so builds that used subdecks are covered too.
3. Choose **Cards → Change Deck** and pick `World Atlas`.
4. Delete the empty `Geographic Features` deck and any subdecks under it.

The moved cards keep their old queue positions (0 to 131), ahead of every new card, so any unstudied features come up before the first country. Only the new cards follow the new order. To move the unstudied feature cards into the features block, use the Reposition steps in [Upgrading from v2](#upgrading-from-v2) for `tag:block::features`. To start the ring alongside them, use a region filtered deck (see **Pacing**). If you skip steps 2 to 4, you end up with two decks. The old cards still work under the old name.

**Retired cards.** Importing never deletes notes, so the 34 cards World Atlas retired from v1, and the Crimea peninsula card retired in v3.0.1, stay in your collection and keep coming up. The searches in [Retired cards](#retired-cards) find them in any deck.

**Card content.** The import updates each feature note's fields where they changed: most fronts point to a re-rendered map, the hidden Source field names the new deck file, and answers are now built from lines joined with `<br>` (a feature's answer text is unchanged). Every back also gains the card's note under the answer. It also adds the `kind::`, `block::` and other new tags. The notes stay the same notes, with the same history. Afterwards, run **Tools → Check Media** to delete the old maps.

**Pacing.** At 15 new cards a day, the 561 cards take about 5½ weeks. Set this under **New cards/day** in the deck's options. To work through one region alongside the main order, make a filtered deck (**Tools → Create Filtered Deck**) with this search, where `NN` is `01` to `21`:

```
deck:"World Atlas" tag:region::NN is:new
```

Set its order to "Order due". Features have no region tag, so this deck holds only the region's countries, territories and disputed areas, then its capitals and cities.

## Edit the data

- **`data/features.yaml`** is the feature list. Each entry has a name, a type word, a category, a tier, a `note`, geometry selectors and `expect` bounds that catch accidental changes to the shape. The note is one to three plain sentences on why the feature matters; it appears on the card back and in the PDF guide, and `make check-data` fails if an active card lacks one.
- **`geometry/*.geojson`** holds shapes Natural Earth lacks. Every feature in a file needs `source`, `method` and `refs`. The scripts that made the derived shapes are in `tools/` ([tools/README.md](tools/README.md)).
- **Type words:** `type` must be one of the 23 words in `src/geofeat/model.py`.
- **World Atlas data:** `data/countries.yaml`, `data/territories.yaml` and `data/cities.yaml` hold the political cards; `data/curriculum.yaml` places each country, subdivision, territory and disputed area in a region. See [Political data](docs/architecture.md#political-data).

[docs/architecture.md](docs/architecture.md) covers the selectors, frame options, nesting overrides and every check.

**Uids.** `make ids` gives each new entry a permanent `uid`, the Anki note GUID, and `make positions` gives it a new-card position; `make all` refuses to build while either is missing. Never edit or reuse a uid. A feature's `id`, `name`, tier and category can change freely without losing review history.

**Retiring a card.** Set `retired: true` and keep the rest of the entry. This works on a feature, city, territory, subdivision or disputed area, and on a country's `capital:` for its capital card. A retired territory, subdivision or disputed area also comes out of `data/curriculum.yaml`. A tier 3 state's capital must stay retired; `make check-data` fails otherwise. After un-retiring one, run `make check-data`.

**Reviewing maps.** `make sheet` writes a grid of every map to `build/sheet.png`; `make phone` writes each map 390 px wide, as on a phone; `make pairs` shows neighbouring features side by side; `make cvd` simulates colour blindness. Each except `pairs` takes `IDS="bosporus country:france city:*"` to limit it to the maps you name (a bare id is a feature); `make review` writes one phone-size sheet per region in study order. `make import-test` imports the package into fresh Anki collections and checks the study order, a region filtered deck, Check Database and the upgrade from v1; [docs/device-test-checklist.md](docs/device-test-checklist.md) repeats those checks by hand on Anki desktop, AnkiDroid and AnkiMobile.

## Retired cards

89 cards have been retired: 34 from v1 (all 10 passes and corridors, all 15 islands and 9 climate systems) and 55 in v3.0.1 (7 disputed areas, 29 capitals, 18 cities and the Crimea peninsula). Re-importing never deletes notes, so a retired card stays in your collection and keeps coming up for review. Delete it by hand: in **Browse**, search for it, check the count, select all and delete the notes.

The 9 climate cards carry an `id_` tag, so this search finds them:

```
tag:id_subtropical-highs OR tag:id_itcz OR tag:id_east-asian-monsoon OR tag:id_west-african-monsoon OR tag:id_canary-current OR tag:id_benguela-current OR tag:id_kuroshio OR tag:id_humboldt-current OR tag:id_bay-of-bengal-cyclones
```

The 55 cards retired in v3.0.1 carry an `id_` tag, so this search finds them:

```
tag:id_dispute_golan-heights OR tag:id_dispute_kashmir-indian-administered OR tag:id_dispute_kashmir-pakistani-administered OR tag:id_dispute_arunachal-pradesh OR tag:id_dispute_aksai-chin OR tag:id_dispute_kuril-islands OR tag:id_dispute_essequibo OR tag:id_crimea OR tag:id_city_rotterdam OR tag:id_city_seville OR tag:id_city_hamburg OR tag:id_city_frankfurt OR tag:id_city_volgograd OR tag:id_city_aleppo OR tag:id_city_medina OR tag:id_city_zanzibar OR tag:id_city_johannesburg OR tag:id_city_samarkand OR tag:id_city_isfahan OR tag:id_city_guangzhou OR tag:id_city_xian OR tag:id_city_osaka OR tag:id_city_malacca OR tag:id_city_new-orleans OR tag:id_city_montreal OR tag:id_city_potosi OR tag:id_capital_andorra OR tag:id_capital_liechtenstein OR tag:id_capital_malta OR tag:id_capital_bahrain OR tag:id_capital_cabo-verde OR tag:id_capital_sao-tome-and-principe OR tag:id_capital_comoros OR tag:id_capital_mauritius OR tag:id_capital_seychelles OR tag:id_capital_maldives OR tag:id_capital_brunei OR tag:id_capital_vanuatu OR tag:id_capital_fiji OR tag:id_capital_tonga OR tag:id_capital_samoa OR tag:id_capital_tuvalu OR tag:id_capital_kiribati OR tag:id_capital_nauru OR tag:id_capital_marshall-islands OR tag:id_capital_micronesia OR tag:id_capital_palau OR tag:id_capital_trinidad-and-tobago OR tag:id_capital_grenada OR tag:id_capital_saint-vincent-and-the-grenadines OR tag:id_capital_barbados OR tag:id_capital_saint-lucia OR tag:id_capital_dominica OR tag:id_capital_antigua-and-barbuda OR tag:id_capital_saint-kitts-and-nevis
```

In a search, `_` matches any single character. Check that **Browse** shows exactly 55 notes before you delete them.

The 25 passes, corridors and islands were retired in the build that added the `id_` tag, so the copies in your collection don't have it. Their type words, Pass, Corridor and Island, appear on no active card, so this search finds exactly those 25:

```
"Question:*Island*" OR "Question:*Pass*" OR "Question:*Corridor*"
```

## License

The code and the generated deck are under the [MIT License](LICENSE). Natural Earth data is public domain, pinned by commit and checksum in `data/sources.lock`. The NOAA datasets used for the climate geometry (IBTrACS, ICOADS and the Global Drifter Program climatology) are US government data in the public domain; [tools/README.md](tools/README.md) gives versions and citations.
