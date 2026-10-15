# World Atlas

An Anki deck of 607 map cards that teaches the political and physical map of the world together: 197 countries, 191 capitals, 42 other cities, 23 territories, 15 disputed areas, the 7 continents and 132 physical features that shaped settlement, trade and war (oceans and seas, straits, rivers, mountain ranges, plains, peninsulas and six climate systems). Each card front shows an unlabelled map with one place highlighted in red and its type ("Country", "City", "Strait") above it. The back gives its name, and under a thin rule, in smaller muted text, a short note on why it matters (the same note the study guide prints).

World Atlas grew out of the **Geographic Features** deck (v1), which held physical features alone. Its 132 active feature notes carry over, with their review history; see [Upgrading from Geographic Features](#upgrading-from-geographic-features).

Current release: [v2.1.0](https://github.com/QuinnHerden/world-atlas/releases/tag/v2.1.0) (2026-10-15), which redraws the political and city maps on their regions and moves Greenland to the Nordic & Baltic region; see [Upgrading from v2.0](#upgrading-from-v20). Changes by release are in [CHANGELOG.md](CHANGELOG.md).

Maps are rendered from [Natural Earth](https://www.naturalearthdata.com/) data. The deck is compiled with [ankcompiler](https://github.com/QuinnHerden/ankcompiler) 0.6.

- How the build works: [docs/architecture.md](docs/architecture.md)
- Why it works that way: [docs/adr/](docs/adr/)
- The plan behind World Atlas (curriculum, decisions, build phases): [docs/world-atlas-plan.md](docs/world-atlas-plan.md)

## Download and import

Download two files from the [latest release](https://github.com/QuinnHerden/world-atlas/releases/latest):

- `world-atlas.apkg`: the deck.
- `world-atlas-guide.pdf`: the printable study guide.

**New to the deck.** In Anki, choose **File → Import** and pick `world-atlas.apkg`. Every card lands in one deck, `World Atlas`, in the study order described under [Study](#study).

**Upgrading from v2.0.** Import it the same way. Your cards are updated in place; [Upgrading from v2.0](#upgrading-from-v20) covers what changes and the one new card, Greenland.

**Upgrading from Geographic Features.** Follow [Upgrading from Geographic Features](#upgrading-from-geographic-features) instead. It covers keeping your review history and moving the old cards into `World Atlas`.

**The guide** prints every card in the order Anki shows new cards: entry N is the Nth new card, with its map, its answer and its note. It is sectioned into orientation, then pass 1 and pass 2 by region. For a single region, build it yourself with `make guide REGION=NN` (see [Build](#build)).

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

Rendering takes about 10 s per map and is cached, so only changed maps re-render. `JOBS=2 make all` renders in parallel; each worker needs about 1.5 GB of RAM.

`make guide` writes `build/world-atlas-guide.pdf`, a printable guide to every card in the order Anki shows new cards: entry N is the Nth new card, with its map, answer and a short note on why it matters. It is sectioned into orientation, then pass 1 and pass 2 by region. `make guide REGION=NN` writes `build/world-atlas-guide-NN.pdf` with one region only: that region's countries, capitals, cities, territories and disputed areas, plus the features the study order places in its run. The `tag:region::NN` filtered deck (see **Pacing**) holds the same political cards but no features, because features have no region tag. It uses the optional `guide` dependency group (reportlab).

## Study

Every card is in one deck, `World Atlas`, with no subdecks. Each card has these tags:

- `kind::<kind>`: `country` (197), `capital` (191), `city` (42), `territory` (23), `dispute` (15), `continent` (7) or `feature` (132)
- `pass::orientation`, `pass::1` or `pass::2` (13, 584 and 10 cards)
- `region::01` to `region::21`: the region of a country, capital, city, territory or disputed area (features have none)
- `tier::1`, `tier::2` or `tier::3` (381, 153 and 73 cards)
- `category::<slug>`: `countries`, `cities` (capitals and other cities), `territories` (territories and disputed areas), `continents`, or a feature category: `water-bodies`, `straits-chokepoints`, `mountain-ranges`, `rivers-deltas`, `deserts-plateaus-plains`, `peninsulas-isthmuses`, `regions-rifts` or `climate-systems`
- `id_<id>` for a feature, e.g. `id_nile`, or `id_<kind>_<id>` for any other kind, e.g. `id_country_france`

New cards come up in a fixed order. An orientation block (the continents, the oceans and the planetary winds) comes first. Pass 1 then goes once round a ring of 21 regions, starting in Western Europe, country by neighbouring country, with each capital 2–3 cards after its country and each feature after the countries around it. Pass 2 goes round the ring again with the tier 3 features. `data/curriculum.yaml` names the regions. [ADR 0009](docs/adr/0009-curriculum-order.md) explains the design.

To study a subset, make a filtered deck (**Tools → Create Filtered Deck**) with a search such as `deck:"World Atlas" tag:region::04` or `tag:kind::capital`.

**Re-importing a new build** updates each note's text (every card's back, its note included), map and tags, but not its card's deck or new-card position, and it never deletes notes:

- **New cards:** a later release slots its new cards in between existing ones. No existing card moves, so a fresh import and an updated collection see the same order.
- **Moved tier or category:** the card keeps its place in the queue. To move it anyway, select it in **Browse** and use **Cards → Reposition**.
- **Moved region:** a political card that moves to another region comes as a new card, and the old one is retired (see [Retired cards](#retired-cards)). Greenland in v2.1 is the only one so far.
- **Old maps:** a re-rendered map gets a new file name. Run **Tools → Check Media** to delete the old image.
- **Older imports:** cards imported from v1 or from a pre-release build keep the positions they had then. If you haven't started studying, delete the deck and import the new package to get the full study order.

### Upgrading from v2.0

**What changed in v2.1:**

- Country, territory and disputed-area maps are drawn on their region's map, so cards you study together share one frame. The largest states (Russia, Canada, Brazil and the like) keep their v2.0 framing.
- Capital and city maps use their country's region map too.
- Small places get a zoomed detail inset in a corner, joined to them by leader lines. Every capital and city card gets one round its dot.
- Country, territory, disputed-area, capital and city cards no longer show the small world map. Feature cards still do.
- Greenland moved from North & Central America (region 19) to Nordic & Baltic (region 02). It now comes right after Iceland and before the GIUK Gap.

**Importing.** Import `world-atlas.apkg` with **File → Import**, keeping the default **Update notes: If newer**.

- **Existing cards** get their new maps and tags in place. They keep their review history and their place in the queue.
- **Greenland is a new card**, a new note. It lands in the queue between Iceland and the GIUK Gap. If you are already past that point, it comes up among your next new cards.
- **The old Greenland card stays** in your collection, with its review history, until you delete it. Its history does not carry over to the new card: if you had learned Greenland, you learn it again from scratch. To delete the old card, search for it in **Browse**, check that it finds one card, select it and delete the note:

  ```
  deck:"World Atlas" tag:id_territory_greenland tag:region::19
  ```

  Both cards carry `id_territory_greenland`. The old one is tagged `region::19`, the new one `region::02`.
- **Old maps** stay in your media folder. Run **Tools → Check Media** to delete them.

### Upgrading from Geographic Features

World Atlas v2.0.0 replaces the **Geographic Features** deck (v1), which held the physical features alone. World Atlas has 607 cards: the same 132 features, plus countries, capitals, cities, territories, disputed areas and continents. Pick one of the two paths below.

**Fresh start.** Use this if you haven't studied much. You get the full study order.

1. Delete the `Geographic Features` deck. Anki deletes its cards and their review history with it.
2. Import `world-atlas.apkg` with **File → Import**.

**Keep your review history.** Your feature cards keep their scheduling. The import matches each feature note by its note ID (GUID) and updates it in place. Anki doesn't move existing cards on import, so the matched cards stay in `Geographic Features`. The new cards land in `World Atlas`. Keep the import's default **Update notes: If newer**; if you edited the `AnkCompiler-Question_Answer` note type, tick **Merge notetypes** too.

1. Import `world-atlas.apkg` with **File → Import**.
2. In **Browse**, search `deck:"Geographic Features"` and select all cards. The search also finds cards in old subdecks (`Geographic Features::<Category>::Tier <n>`), so builds that used subdecks are covered too.
3. Choose **Cards → Change Deck** and pick `World Atlas`.
4. Delete the empty `Geographic Features` deck and any subdecks under it.

The moved cards keep their old queue positions (0 to 131), ahead of every new card, so any unstudied features come up before the first country. Only the new cards follow the new order. To start the ring alongside them, use a region filtered deck (see **Pacing**). If you skip steps 2 to 4, you end up with two decks. The old cards still work under the old name.

**Retired cards.** Importing never deletes notes, so the 34 cards World Atlas retired from v1 stay in your collection and keep coming up. The searches in [Retired cards](#retired-cards) find them in any deck.

**Card content.** The import updates each feature note's fields where they changed: most fronts point to a re-rendered map, the hidden Source field names the new deck file, and answers are now built from lines joined with `<br>` (a feature's answer text is unchanged). Every back also gains the card's note under the answer. It also adds the `kind::`, `pass::` and other new tags. The notes stay the same notes, with the same history. Afterwards, run **Tools → Check Media** to delete the old maps.

**Pacing.** At 15 new cards a day, the 607 cards take about 6 weeks. Set this under **New cards/day** in the deck's options. To work through one region alongside the main order, make a filtered deck (**Tools → Create Filtered Deck**) with this search, where `NN` is `01` to `21`:

```
deck:"World Atlas" tag:region::NN is:new
```

Set its order to "Order due". Features have no region tag, so this deck holds only countries, capitals, cities, territories and disputed areas.

## Edit the data

- **`data/features.yaml`** is the feature list. Each entry has a name, a type word, a category, a tier, a `note`, geometry selectors and `expect` bounds that catch accidental changes to the shape. The note is one to three plain sentences on why the feature matters; it appears on the card back and in the PDF guide, and `make check-data` fails if an active card lacks one.
- **`geometry/*.geojson`** holds shapes Natural Earth lacks. Every feature in a file needs `source`, `method` and `refs`. The scripts that made the derived shapes are in `tools/` ([tools/README.md](tools/README.md)).
- **Type words:** `type` must be one of the 23 words in `src/geofeat/model.py`.
- **World Atlas data:** `data/countries.yaml`, `data/territories.yaml` and `data/cities.yaml` hold the political cards; `data/curriculum.yaml` places each country, territory and disputed area in a region. See [Political data](docs/architecture.md#political-data).

[docs/architecture.md](docs/architecture.md) covers the selectors, frame options, nesting overrides and every check.

**Uids.** `make ids` gives each new entry a permanent `uid`, the Anki note GUID, and `make positions` gives it a new-card position; `make all` refuses to build while either is missing. Never edit or reuse a uid. A feature's `id`, `name`, tier and category can change freely without losing review history.

**Retiring a card.** Set `retired: true` and keep the rest of the entry. After un-retiring one, run `make check-data`.

**Reviewing maps.** `make sheet` writes a grid of every map to `build/sheet.png`; `make phone` writes each map 390 px wide, as on a phone; `make pairs` shows neighbouring features side by side; `make cvd` simulates colour blindness. Each except `pairs` takes `IDS="bosporus country:france city:*"` to limit it to the maps you name (a bare id is a feature); `make review` writes one phone-size sheet per region in study order. `make import-test` imports the package into fresh Anki collections and checks the study order, a region filtered deck, Check Database and the upgrade from v1; [docs/device-test-checklist.md](docs/device-test-checklist.md) repeats those checks by hand on Anki desktop, AnkiDroid and AnkiMobile.

## Retired cards

35 cards have been retired: from v1, all 10 passes and corridors, all 15 islands and 9 climate systems; in v2.1, the v2.0 Greenland card, replaced by a new one. Re-importing never deletes notes, so a retired card stays in your collection and keeps coming up for review. Delete it by hand: in **Browse**, search for it, check the count, select all and delete the notes.

The v2.0 Greenland card shares its `id_` tag with the new one, but only it has the region 19 tag:

```
deck:"World Atlas" tag:id_territory_greenland tag:region::19
```

The 9 climate cards carry an `id_` tag, so this search finds them:

```
tag:id_subtropical-highs OR tag:id_itcz OR tag:id_east-asian-monsoon OR tag:id_west-african-monsoon OR tag:id_canary-current OR tag:id_benguela-current OR tag:id_kuroshio OR tag:id_humboldt-current OR tag:id_bay-of-bengal-cyclones
```

The 25 passes, corridors and islands were retired in the build that added the `id_` tag, so the copies in your collection don't have it. Their type words, Pass, Corridor and Island, appear on no active card, so this search finds exactly those 25:

```
"Question:*Island*" OR "Question:*Pass*" OR "Question:*Corridor*"
```

## License

The code and the generated deck are under the [MIT License](LICENSE). Natural Earth data is public domain, pinned by commit and checksum in `data/sources.lock`. The NOAA datasets used for the climate geometry (IBTrACS, ICOADS and the Global Drifter Program climatology) are US government data in the public domain; [tools/README.md](tools/README.md) gives versions and citations.
