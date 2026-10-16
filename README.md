# World Atlas

An Anki deck of 554 map cards that teaches the political and physical map of the world together: 197 countries, 162 capitals, 25 other cities, 25 territories, 5 subnationals (England, Scotland, Wales, Northern Ireland and Kaliningrad), 9 disputed areas, the 7 continents and 124 physical features that shaped settlement, trade and war (oceans and seas, straits, rivers, mountain ranges, plains, peninsulas and six climate systems). Each card front shows an unlabelled map with one place highlighted in red and its type ("Country", "City", "Strait") above it. The back gives its name, and under a thin rule, in smaller muted text, a short note on why it matters.

World Atlas grew out of the **Geographic Features** deck, which held physical features alone.

The first release is v1.0.0. Earlier builds were pre-releases, archived as the `archive/v1.0.0` to `archive/v3.0.0` tags. Changes are in [CHANGELOG.md](CHANGELOG.md).

Four **companion decks** go deeper on single countries: Italy's 20 regions, the 50 US states and DC, Brazil's 26 states and the Distrito Federal, and Canada's 10 provinces and 3 territories. Each is a separate deck and download; see [Companion decks](#companion-decks).

Maps are rendered from [Natural Earth](https://www.naturalearthdata.com/) data. The deck is compiled with [ankcompiler](https://github.com/QuinnHerden/ankcompiler) 0.6.

- How the build works: [docs/architecture.md](docs/architecture.md)
- Why it works that way: [docs/adr/](docs/adr/)
- The plan behind World Atlas (curriculum, decisions, build phases): [docs/world-atlas-plan.md](docs/world-atlas-plan.md)
- Contributing and releasing: [CONTRIBUTING.md](CONTRIBUTING.md)

## Download and import

The [latest release](https://github.com/QuinnHerden/world-atlas/releases/latest) has five packages: `world-atlas.apkg` (554 cards) and the four companion decks (see [Companion decks](#companion-decks)). Download the ones you want. `SHA256SUMS` lists their checksums; `sha256sum -c --ignore-missing SHA256SUMS` in the download folder checks them.

In Anki, choose **File → Import** and pick `world-atlas.apkg`. Every card lands in one deck, `World Atlas`, in the study order described under [Study](#study).

## Companion decks

Each companion deck teaches one country's first-level subdivisions. Each is its own deck in Anki and its own package, and none touches World Atlas. Import only the ones you want, in any order.

| Package | Deck | Cards |
|---|---|---|
| `italian-regions.apkg` | Italian Regions | 20: the regions |
| `us-states.apkg` | US States | 51: 50 states and the District of Columbia |
| `brazilian-states.apkg` | Brazilian States | 27: 26 states and the Distrito Federal |
| `canadian-provinces.apkg` | Canadian Provinces and Territories | 13: 10 provinces and 3 territories |

**Importing.** In Anki, choose **File → Import** and pick the package. Its cards land in a new top-level deck named in the table, beside `World Atlas`. The decks use World Atlas's note type, so importing one into a collection that has World Atlas adds no note type and changes no World Atlas card.

**The cards.** Every card shows the same map of the country, with its internal borders and the other countries faded. One subdivision is in red, and a small one is also ringed. A zoomed inset in a corner shows it with its neighbours, except on the largest (Texas, Amazonas, Quebec and the like), which read well enough on the main map. Alaska and Hawaii are drawn in boxes in the bottom left of the US map, as on most US maps. The front says "Region", "State", "Province", "Territory" or "Federal district". The back gives the name and a short note. Italian regions are named in Italian and Brazilian states in Portuguese, with no English forms: Puglia, Sicilia, Distrito Federal.

**Study order.** New cards come up in a walk from neighbour to neighbour. Italy starts at Valle d'Aosta, the US at Maine (Alaska and Hawaii last) and Brazil at Roraima in the north. Canada runs east from British Columbia, taking in the territories among the provinces from west to east. A deck takes 1 to 4 days at 15 new cards a day. Each card is tagged `kind::subdivision`, `block::subdivisions` and `country::<country>` (for example `country::united-states`).

## Build

Requires [uv](https://docs.astral.sh/uv/), `ankc` 0.6.x (on PyPI as `ankcompiler`) and an authenticated `gh` CLI (Natural Earth downloads go through the GitHub API).

```sh
make ids        # mint uids for new entries, then commit features.yaml
make positions  # give new uids a place in data/positions.lock, then commit it
make all        # test → fetch → check-data → render → deck → check → build
make adjacency  # the country adjacency graph and its report
```

`ANKC` picks the compiler, e.g. `make all ANKC="uv run --with ../ankcompiler ankc"`. Every card gets its new-card position from `data/positions.lock` as a `[^pos]` footnote. The lock is frozen and append-only, so ankc 0.5, which can't write positions, fails the build.

Output: `dist/world-atlas.apkg` and one package per companion deck (`dist/italian-regions.apkg`, `dist/us-states.apkg`, `dist/brazilian-states.apkg`, `dist/canadian-provinces.apkg`). Import any of them in Anki with **File → Import**.

A release build names its version: `make all RELEASE=1 RELEASE_VERSION=v1.0.0`. It fails without `RELEASE_VERSION` (unless a release tag is on `HEAD`), when the version's major isn't the lock's series, while a note has an open verify item, or when the freeze guard can't run: no readable `origin/main`, a shallow clone, or no tags (the `archive/*` tags included). Fetch the full history and tags first. [CONTRIBUTING.md](CONTRIBUTING.md#release) has the release steps.

Rendering takes about 3.5 s per map, so a full build takes about 40 minutes; renders are cached, so only changed maps re-render. The default, one render worker (`JOBS=1`), needs about 3 GB of RAM in all; `JOBS=2 make all` renders in parallel, each worker loading its own basemap at about 1.5 GB.

## Study

Every card is in one deck, `World Atlas`, with no subdecks. Each card has these tags:

- `kind::<kind>`: `country` (197), `capital` (162), `city` (25), `territory` (25), `subnational` (5), `dispute` (9), `continent` (7) or `feature` (124). A subnational is a constituent country of the United Kingdom or an exclave (Kaliningrad)
- `block::continents`, `block::countries`, `block::features` or `block::cities` (7, 236, 124 and 187 cards): the study block. Countries, subnationals, territories and disputed areas are in `countries`; capitals and other cities in `cities`
- `region::01` to `region::21`: the region of a country, capital, city, subnational, territory or disputed area (features have none)
- `category::<slug>`: `countries`, `cities` (capitals and other cities), `territories` (territories and disputed areas), `subnational` (England, Scotland, Wales, Northern Ireland and Kaliningrad Oblast), `continents`, or a feature category: `water-bodies`, `straits-chokepoints`, `mountain-ranges`, `rivers-deltas`, `deserts-plateaus-plains`, `peninsulas-isthmuses`, `regions-rifts` or `climate-systems`
- `id_<id>` for a feature, e.g. `id_nile`, or `id_<kind>_<id>` for any other kind, e.g. `id_country_france`

New cards come up in a fixed order, in four blocks:

1. **Continents and oceans** (11 cards, under a day at 15 a day): the 7 continents, Europe first and Antarctica last, then the 4 oceans (Atlantic, Indian, Pacific, Arctic). The oceans are tagged `block::features`, so a features filtered deck still finds them.
2. **Countries, territories and disputed areas** (236 cards, about 16 days): once round a ring of 21 regions, starting in Western Europe with Portugal and ending in the Caribbean with the Bahamas. Within a region you go country by neighbouring country. Microstates and enclaves come right after a neighbour (Andorra after Spain, Monaco after France), and subnationals, territories and disputed areas after the country they are placed with (England and Gibraltar after the United Kingdom, Kaliningrad after Lithuania, Greenland after Iceland).
3. **Physical features** (the other 120 cards, about 8 days): the planetary winds first, then the rest round the ring, region by region. The 3 tier 3 features come last.
4. **Capitals and cities** (187 cards, about 12½ days): round the ring again, in the same country order. Each country's capital comes first, then its other cities. Microstates and small island states have no capital card.

At 15 new cards a day that is just over 5 weeks. `data/curriculum.yaml` names the regions. [ADR 0009](docs/adr/0009-curriculum-order.md) explains the design.

To study a subset, make a filtered deck (**Tools → Create Filtered Deck**) with a search and the order "Order due". Some searches:

| Search | Gives |
|---|---|
| `deck:"World Atlas" tag:region::05 is:new` | Region 05's countries, territories and disputed areas, then its capitals and cities |
| `deck:"World Atlas" tag:block::features is:new` | The physical features, in study order |
| `deck:"World Atlas" tag:block::cities tag:region::16` | East Asia's capitals and cities |
| `deck:"World Atlas" tag:kind::capital` | Every capital |

**Re-importing a new build** updates each note's text (every card's back, its note included), map and tags, but not its card's deck or new-card position, and it never deletes notes:

- **New cards:** a later release of the same major version slots its new cards in between existing ones. No existing card moves, so a fresh import and an updated collection see the same order. A new major version may change the order itself; existing cards then keep their old place.
- **Moved tier or category:** the card keeps its place in the queue. To move it anyway, select it in **Browse** and use **Cards → Reposition**.
- **Old maps:** a re-rendered map gets a new file name. Run **Tools → Check Media** to delete the old image.

**Pacing.** At 15 new cards a day, the 554 cards take just over 5 weeks. Set this under **New cards/day** in the deck's options. To work through one region alongside the main order, make a filtered deck (**Tools → Create Filtered Deck**) with this search, where `NN` is `01` to `21`:

```
deck:"World Atlas" tag:region::NN is:new
```

Set its order to "Order due". Features have no region tag, so this deck holds only the region's countries, territories and disputed areas, then its capitals and cities.

## Edit the data

- **`data/features.yaml`** is the feature list. Each entry has a name, a type word, a category, a tier, a `note`, geometry selectors and `expect` bounds that catch accidental changes to the shape. The note is one to three plain sentences on why the feature matters; it appears on the card back, and `make check-data` fails if an active card lacks one.
- **`geometry/*.geojson`** holds shapes Natural Earth lacks. Every feature in a file needs `source`, `method` and `refs`. The scripts that made the derived shapes are in `tools/` ([tools/README.md](tools/README.md)).
- **Type words:** `type` must be one of the 23 words in `src/geofeat/model.py`.
- **World Atlas data:** `data/countries.yaml`, `data/territories.yaml` and `data/cities.yaml` hold the political cards; `data/curriculum.yaml` places each country, subnational, territory and disputed area in a region. See [Political data](docs/architecture.md#political-data).
- **Companion decks:** `data/subdivisions.yaml` holds the subdivisions, each country's in study order. See [Companion decks](docs/architecture.md#companion-decks).

[docs/architecture.md](docs/architecture.md) covers the selectors, frame options, nesting overrides and every check.

**Uids.** `make ids` gives each new entry a permanent `uid`, the Anki note GUID, and `make positions` gives it a new-card position; `make all` refuses to build while either is missing. Never edit or reuse a uid. A feature's `id`, `name`, tier and category can change freely without losing review history.

**Retiring a card.** Set `retired: true` and keep the rest of the entry. This works on a feature, city, territory, subnational or disputed area, and on a country's `capital:` for its capital card. A retired territory, subnational or disputed area also comes out of `data/curriculum.yaml`. A tier 3 state's capital must stay retired; `make check-data` fails otherwise. After un-retiring one, run `make check-data`.

**Reviewing maps.** `make sheet` writes a grid of every map to `build/sheet.png`; `make phone` writes each map 390 px wide, as on a phone; `make pairs` shows neighbouring features side by side; `make cvd` simulates colour blindness. Each except `pairs` takes `IDS="bosporus country:france city:*"` to limit it to the maps you name (a bare id is a feature); `make review` writes one phone-size sheet per region in study order. `make import-test` imports the package into fresh Anki collections and checks the study order, a region filtered deck, Check Database and the upgrade from Geographic Features; [docs/device-test-checklist.md](docs/device-test-checklist.md) repeats those checks by hand on Anki desktop, AnkiDroid and AnkiMobile.

## License

The code and the generated deck are under the [MIT License](LICENSE). Natural Earth data is public domain, pinned by commit and checksum in `data/sources.lock`. The NOAA datasets used for the climate geometry (IBTrACS, ICOADS and the Global Drifter Program climatology) are US government data in the public domain; [tools/README.md](tools/README.md) gives versions and citations.
