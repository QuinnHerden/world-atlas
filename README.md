# Geographic Features

Builds an Anki deck of the physical features that shaped settlement, trade and war. Each card shows an unlabelled map with one feature highlighted; you recall its name. Maps are rendered from Natural Earth data. The deck is compiled with [ankcompiler](https://github.com/QuinnHerden/ankcompiler) 0.5.x.

## Build

Requires [uv](https://docs.astral.sh/uv/), `ankc` 0.5.x and an authenticated `gh` CLI (Natural Earth downloads go through the GitHub API).

```sh
make ids        # mint uids for new entries, then commit features.yaml
make all        # test → fetch → check-data → render → deck → check → build
```

Rendering takes about 10 s per map and is cached by input hash, so only changed maps re-render. `JOBS=2 make all` renders in parallel; each worker needs about 1.5 GB of RAM.

Output: `dist/geographic-features.apkg`. Import it in Anki with **File → Import**.

`make guide` writes `build/guide.pdf`, a printable guide to the active cards: each map with its name, type, tier and note, plus a linked table of contents and PDF bookmarks. It renders first if needed and uses the optional `guide` dependency group (reportlab).

## Deck structure

Every card is in one deck, `Geographic Features`, with no subdecks. Each card has three tags:

- `tier::1`, `tier::2` or `tier::3`
- `category::<slug>`, e.g. `category::water-bodies`, `category::rivers-deltas`, `category::straits-chokepoints`
- `id_<feature-id>`, e.g. `id_nile`

New cards come up in a fixed study order: all of tier 1, then tier 2, then tier 3. Within a tier, a broad feature comes before the features inside it or drawn against it (the Nile before the Nile Delta, the Himalayas before the Tibetan Plateau). Categories alternate, and features close together on the map are kept at least three cards apart where possible. [ADR 0004](docs/adr/0004-flat-deck-and-study-order.md) explains why.

To study a subset, make a filtered deck (**Tools → Create Filtered Deck**) with a search such as `deck:"Geographic Features" tag:tier::1` or `tag:category::rivers-deltas`. `tag:tier::*` matches every tier.

### Upgrading from a version with subdecks

Builds before the flat deck put cards in `Geographic Features::<Category>::Tier <n>`. Re-importing updates each note but leaves its card in the old subdeck, so move the cards by hand:

1. In **Browse**, search `deck:"Geographic Features"` and select all cards.
2. Choose **Cards → Change Deck** and pick `Geographic Features`.
3. Delete the empty subdecks.

Re-importing also keeps each existing card's queue position, so the full study order applies only to a fresh import. If you haven't started studying, delete the deck and import the new package instead.

## Edit

- `data/features.yaml`: the feature list. Each entry has geometry selectors, `expect` bounds, a style, a category, a tier and a `note`: one to three plain sentences on why the feature matters, taken from `research-independent.md` without the figures its verify flags mark as unchecked. The note appears only in the PDF guide, and `make check-data` fails if an active card lacks one. `expect` is a drift check, not a fact check: its bbox and size range bracket what the geometry measures now. Where Natural Earth's generalised shape can't reach a published value, a comment notes it.
- `geometry/*.geojson`: geometry for anything Natural Earth lacks. Every feature in a file needs a `source`, a `method` (`ne-derived`, `pd-dataset`, `reference-coords` or `hand-drawn`) and a list of `refs`. `make check-data` fails if any is missing, or if `source` says the shape is unverified or a placeholder. The scripts that made the derived shapes are in `tools/`.
- **Type words:** `type` must be one of the 23 words in `src/geofeat/model.py`. Each word belongs to a family (a Pass and a Corridor are both land passages). Area features in a land family are clipped to land. Add a `qualifier` only for a detail that doesn't give the answer away, such as a season: the card shows "Wind system, July".
- **Feature references:** a geometry part can be `{feature: <id>, subtract: true}`, which cuts a sibling out of a feature (e.g. the ranges out of the Tibetan Plateau). Add `trim_to_largest: true` to keep only the largest piece left by the cut; `make check-data` reports how much it dropped.
- **Nesting overrides:** first try subtracting the inner card. If the inner feature is a named part of the outer one and cutting it out would misdraw the outer shape, `allow_nested: [{id: <sibling>, reason: <why>}]` accepts one same-family pair that nests. A reason is required, and `make check-data` lists every override. See PLAN.md for the policy.
- **Framing:** `frame` takes `min_span_km`; `centre: [lon, lat]`, which lets siblings share one frame; `context: [<id>]`, which draws a parent river faintly underneath; `admin1: true`, which adds state borders; and `former: <file>.geojson`, a past extent drawn as a dashed line. Regional frames are north-up and at least 2,600 km wide; small features get a ring.

`make ids` gives each new entry a permanent `uid` (the Anki note GUID); `make all` refuses to build while any is missing. Never edit or reuse a uid. To retire a feature, set `retired: true` and keep the rest of the entry. A retired entry is archived: it is validated against the schema only and needs no note, so after un-retiring one run `make check-data`. A feature's `id`, `name` and tier can change freely without losing review history.

`make sheet` writes `build/sheet.png`, a grid of every map for visual review, and `make phone` writes `build/phone-NN.png` with each map 390 px wide, as on a phone; `make sheet IDS="bosporus kerch-strait"` limits it to the maps you name. `make pairs` writes every neighbouring pair to `build/pairs.log`. It draws the ones worth a look (flagged, nested, allowed, or near a limit) side by side in `build/pairs-NN.png`, 50 to a page. `make cvd` (which also takes `IDS`) writes `build/cvd.png`, showing each map beside its deuteranopia and protanopia simulations.

`make check-data` also compares sibling pairs, meaning features within 300 km of each other or overlapping. It fails if two highlights are near-identical, or if one covers another and both types are in the same family. Nested features from different families are reported but allowed. It also fails if an ocean or sea has a hole of open water over 10,000 km², which means a neighbouring sea was left out. A river must have an end within 5 km of the sea; set `expect.mouth: lake` or `none` for rivers that end in a lake or an inland sink.

## Retired cards

Re-importing the package never deletes notes, so a retired card stays in your collection and keeps coming up for review. Delete it by hand: in **Browse**, search for it, check the count, select all and delete the notes.

Each card carries an `id_<feature-id>` tag. To find cards retired after this tag was added, search for their tags, e.g. `tag:id_khyber-pass OR tag:id_malta`.

The 9 climate cards retired after v1 carry the tag, so this search finds them:

```
tag:id_subtropical-highs OR tag:id_itcz OR tag:id_east-asian-monsoon OR tag:id_west-african-monsoon OR tag:id_canary-current OR tag:id_benguela-current OR tag:id_kuroshio OR tag:id_humboldt-current OR tag:id_bay-of-bengal-cyclones
```

The 25 cards retired after v1 (the passes, corridors and islands) were imported without that tag. Their type words, Pass, Corridor and Island, are used by no active card, so this search finds exactly those 25:

```
"Question:*Island*" OR "Question:*Pass*" OR "Question:*Corridor*"
```

## Notes

- **Tier and category changes:** re-importing updates a note's tags but not an unstudied card's place in the new-card queue. To move it, select it in **Browse** and use **Cards → Reposition**.
- **Old maps:** a re-rendered map gets a new file name, so the old image stays in Anki's media folder until you run **Tools → Check Media**.
- **Data source:** Natural Earth is public domain, pinned by commit and checksum in `data/sources.lock`. To update, change the commit there and run `uv run python -m geofeat.fetch --relock`.

## License

The code and the generated deck are under the [MIT License](LICENSE). The Natural Earth data is public domain. The NOAA datasets used for the climate geometry (IBTrACS, ICOADS and the Global Drifter Program climatology) are US government data in the public domain; see `tools/README.md` for versions and citations.
