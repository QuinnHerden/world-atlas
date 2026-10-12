# Geographic Features

Builds an Anki deck of the physical features that shaped settlement, trade and war. Each card shows an unlabelled map with one feature highlighted; you recall its name. Maps are rendered from Natural Earth data. The deck is compiled with [ankcompiler](https://github.com/QuinnHerden/ankcompiler) 0.4.x.

## Build

Requires [uv](https://docs.astral.sh/uv/), `ankc` 0.4.x and an authenticated `gh` CLI (Natural Earth downloads go through the GitHub API).

```sh
make ids        # mint uids for new entries, then commit features.yaml
make all        # fetch → check-data → render → deck → check → build
```

Rendering takes about 10 s per map and is cached by input hash, so only changed maps re-render. `JOBS=2 make all` renders in parallel; each worker needs about 1.5 GB of RAM.

Output: `dist/geographic-features.apkg`. Import it in Anki with **File → Import**.

## Edit

- `data/features.yaml`: the feature list. Each entry has geometry selectors, `expect` sanity bounds, a style, a category and a tier.
- `geometry/*.geojson`: hand-drawn geometry for anything Natural Earth lacks. Every feature in a file needs a `source` property.

`make ids` gives each new entry a permanent `uid` (the Anki note GUID); `make all` refuses to build while any is missing. Never edit or reuse a uid. To retire a feature, set `retired: true` and keep the rest of the entry. A feature's `id`, `name` and tier can change freely without losing review history.

`make sheet` writes `build/sheet.png`, a grid of every map for visual review.

## Notes

- **Tier changes:** re-importing a changed note leaves its card in the old deck. After moving a feature to a new tier, move the card with **Change Deck** in Anki, or filter by its `tier::N` tag.
- **Old maps:** a re-rendered map gets a new file name, so the old image stays in Anki's media folder until you run **Tools → Check Media**.
- **Data source:** Natural Earth is public domain, pinned by commit and checksum in `data/sources.lock`. To update, change the commit there and run `uv run python -m geofeat.fetch --relock`.
