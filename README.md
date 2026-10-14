# Geographic Features

An Anki deck of 132 physical features that shaped settlement, trade and war: oceans and seas, straits, rivers, mountain ranges, plains, peninsulas and six climate systems. Each card front shows an unlabelled map with one feature highlighted in red and its type ("Strait", "River") above it. The back gives its name.

Maps are rendered from [Natural Earth](https://www.naturalearthdata.com/) data. The deck is compiled with [ankcompiler](https://github.com/QuinnHerden/ankcompiler) 0.5.x.

- How the build works: [docs/architecture.md](docs/architecture.md)
- Why it works that way: [docs/adr/](docs/adr/)
- The planned extension to countries, capitals and territories: [docs/world-atlas-plan.md](docs/world-atlas-plan.md)

## Build

Requires [uv](https://docs.astral.sh/uv/), `ankc` 0.5.x and an authenticated `gh` CLI (Natural Earth downloads go through the GitHub API).

```sh
make ids        # mint uids for new entries, then commit features.yaml
make all        # test → fetch → check-data → render → deck → check → build
```

Output: `dist/geographic-features.apkg`. Import it in Anki with **File → Import**.

Rendering takes about 10 s per map and is cached, so only changed maps re-render. `JOBS=2 make all` renders in parallel; each worker needs about 1.5 GB of RAM.

`make guide` writes `build/guide.pdf`, a printable guide to the active cards: each map with its name, type, tier and a short note on why it matters, grouped by category. It uses the optional `guide` dependency group (reportlab).

## Study

Every card is in one deck, `Geographic Features`, with no subdecks. Each card has three tags:

- `tier::1`, `tier::2` or `tier::3` (49, 73 and 10 cards)
- `category::<slug>`: `water-bodies`, `straits-chokepoints`, `mountain-ranges`, `rivers-deltas`, `deserts-plateaus-plains`, `peninsulas-isthmuses`, `regions-rifts` or `climate-systems`
- `id_<feature-id>`, e.g. `id_nile`

New cards come up in a fixed order: all of tier 1, then tier 2, then tier 3. Within a tier, a broad feature comes before the features inside it (the Nile before the Nile Delta, the Himalayas before the Tibetan Plateau). Categories alternate, and features close together on the map are kept at least three cards apart where possible. [ADR 0004](docs/adr/0004-flat-deck-and-study-order.md) explains the design.

To study a subset, make a filtered deck (**Tools → Create Filtered Deck**) with a search such as `deck:"Geographic Features" tag:tier::1` or `tag:category::rivers-deltas`.

**Re-importing a new build** updates each note's text, map and tags, but not its card's deck or new-card position, and it never deletes notes:

- **Moved tier or category:** an unstudied card keeps its old place in the queue. To move it, select it in **Browse** and use **Cards → Reposition**.
- **Old maps:** a re-rendered map gets a new file name. Run **Tools → Check Media** to delete the old image.
- **Fresh order:** only a fresh import gets the full study order. If you haven't started studying, delete the deck and import the new package.

### Upgrading from a version with subdecks

Builds before the flat deck put cards in `Geographic Features::<Category>::Tier <n>`. Re-importing leaves each card in its old subdeck, so move them by hand:

1. In **Browse**, search `deck:"Geographic Features"` and select all cards.
2. Choose **Cards → Change Deck** and pick `Geographic Features`.
3. Delete the empty subdecks.

## Edit the data

- **`data/features.yaml`** is the feature list. Each entry has a name, a type word, a category, a tier, a `note`, geometry selectors and `expect` bounds that catch accidental changes to the shape. The note is one to three plain sentences on why the feature matters; it appears only in the PDF guide, and `make check-data` fails if an active card lacks one.
- **`geometry/*.geojson`** holds shapes Natural Earth lacks. Every feature in a file needs `source`, `method` and `refs`. The scripts that made the derived shapes are in `tools/` ([tools/README.md](tools/README.md)).
- **Type words:** `type` must be one of the 23 words in `src/geofeat/model.py`.

[docs/architecture.md](docs/architecture.md) covers the selectors, frame options, nesting overrides and every check.

**Uids.** `make ids` gives each new entry a permanent `uid`, the Anki note GUID; `make all` refuses to build while one is missing. Never edit or reuse a uid. A feature's `id`, `name`, tier and category can change freely without losing review history.

**Retiring a card.** Set `retired: true` and keep the rest of the entry. After un-retiring one, run `make check-data`.

**Reviewing maps.** `make sheet` writes a grid of every map to `build/sheet.png`; `make phone` writes each map 390 px wide, as on a phone; `make pairs` shows neighbouring features side by side; `make cvd` simulates colour blindness. Each except `pairs` takes `IDS="bosporus kerch-strait"` to limit it to the maps you name.

## Retired cards

34 cards have been retired: all 10 passes and corridors, all 15 islands, and 9 climate systems. Re-importing never deletes notes, so a retired card stays in your collection and keeps coming up for review. Delete it by hand: in **Browse**, search for it, check the count, select all and delete the notes.

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
