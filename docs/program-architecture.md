# Program architecture: one deck for features and countries

Status: proposal, 2026-10-14. Covers the system's structure only. The teaching sequence is in `docs/curriculum-proposal.md`, which is being written separately; this design reads it as data.

## Decisions so far (2026-10-14)

Recorded in both `docs/curriculum-proposal.md` and `docs/program-architecture.md`. Where this header and the body disagree, the header wins.

| Topic | Decision |
|---|---|
| Name | **World Atlas** |
| Structure | The atlas ring, starting in Western Europe. Home region first is available through a filtered deck, not a rotated build. |
| Global features | Go in the **orientation block** at the start. |
| Capitals | **2–3 cards after their country.** |
| Look-alikes | The **3–10 card window** plus a curated **confusable-country list**. |
| Microstates | Sit with their neighbours in the order (as pockets). **No separate capital card** when the capital shares the country's name and dot (Monaco, Vatican, Singapore). |
| Country cards | Show the **mainland only**. Overseas territories are their own cards, per `docs/territories-list.md`. |
| Borders | Internationally recognised borders; disputed areas get their own cards and outlines (`docs/territories-list.md`). |
| Climate | **9 climate cards retired** (commit `41fdf95`): the pressure belts, the East Asian and West African monsoons, the Canary, Benguela, Humboldt and Kuroshio currents, and the Bay of Bengal cyclones. |
| Companion PDF guide | Follows the **study order**. Every card gets a 1–3 sentence blurb, stored as `note` in the data. |
| Country design | **Split cards** (separate country outline and capital dot notes), as in the PoC on branch `poc/countries` (`f4a3503`). |

**Where the two docs conflicted:**

- **Global features:** the curriculum's orientation block was chosen over the architecture doc's D10 (an interlude at the end of each pass).
- **Microstates:** the curriculum's decision 6 was chosen (keep the country card, drop a same-name capital card) over the architecture doc's D11 (capital card only below a size threshold).
- **Name:** "World Atlas" replaces the architecture doc's D6 deck name `Geography`, and the `deck:"Geography"` filtered-deck searches in the curriculum doc.
- **Borders:** internationally recognised borders replace the architecture doc's D8 default of NE's de facto admin_0 worldview.

**Knock-on effects of the climate retirement:** the curriculum's orientation keeps only two planetary bands (trade winds, westerlies) rather than four, and its region-assignment examples for retired cards (East Asian and West African monsoons, Humboldt, Benguela, Canary and Kuroshio currents, Bay of Bengal cyclones) no longer apply. The feature count is 132 active cards, not 141.

All other items under "Decisions needed" remain open.

## Recommendation in one paragraph

Keep one repo and one renderer. Add **card sources**: `features.yaml` (unchanged), `countries.yaml` and `cities.yaml`. Each source has its own pydantic model and turns its entries into a plain `Card` DTO. Everything downstream works on `Card`: the order engine, deckgen, the package check and the guide. Make each country/capital pair **two notes** with two uids. Give countries an explicit `region`; physical features get theirs from geometry. Compute adjacency from NE admin_0 at build time and cache it. Rebuild `order.py` as a pipeline of pure functions: passes, then regions, then a neighbour walk, then anchored interleaving, then the existing ADR 0004 local rules. The structural change is that **positions become persisted data**. An append-only `data/positions.lock` maps uid to a sparse integer, and ankc writes it as the card's `due`. Adding a card never moves an existing card, and fresh and existing collections see the same order.

## 1. Data model

| Question | Decision | Why |
|---|---|---|
| Same file or separate | **Separate**: `countries.yaml` (one entry per state, with nested capital) and `cities.yaml` (city plus `country:` ref). This keeps the PoC's shape. | `Feature` carries physical-only policy: `FeatureType`/`FAMILY`, land clipping, `expect` size ranges, `allow_nested`, the pair check. Stretching it to countries would break SRP and drag countries into rules that don't apply to them. |
| Shared model | **No shared entity, but a shared DTO.** Add a `Card` with `uid`, `kind` (feature/country/capital/city), `key`, `prompt`, `answer`, `tags`, `render: RenderSpec`, `region`, `tier`, `anchor`, `parents`. Each source exposes `cards() -> list[Card]`. | DIP: the order engine and deckgen depend on `Card`, not on three models. Adding a fourth kind (rivers-by-country, flags) is an extension, not an edit. |
| Renderer input | **Extract `RenderSpec`** (style, geometry parts, frame options, context overlays) from `Feature`. The PoC already reaches into `Feature` with the new `outline`/`context` styles. | The render cache currently hashes the *source* of `model.py` (`render._code_hash`), so adding a `region` field re-renders all ~700 maps (~2 h). Hash the dumped `RenderSpec` and the render-code files, not the schema module. |
| One note or two | **Two notes**, `uids: {country, capital}`, as the PoC has. | ankc "reversed" swaps one front/back pair. Country (outline → name) and capital (dot → capital) differ on both sides, so reversed can't express them. Cloze can't hide one image per card. Two notes also give independent tags, tiers, positions and retirement (for example, dropping the capital card for city-states). The cost is that Anki won't bury them as siblings, so the order engine has to space them (see §2). |
| Id namespace | **Kind-prefixed id tags for new kinds**: `id_country_niger`, `id_capital_niger`, `id_city_lagos`. Existing feature tags stay `id_<id>`. | Real collisions exist: Niger, Congo, Jordan, Georgia. A check enforces global uniqueness across sources. |
| New tags | `kind::<k>`, `region::<slug>`. Keep `tier::` and `category::`; countries get `category::countries` and cities `category::cities`. | Filtered decks keep working. |
| Region membership | **Countries: an explicit `region:` field**, validated against `data/curriculum.yaml`. Cities inherit their country's region. **Features: derived** from the region with the largest overlap with the feature (a region's polygon is the union of its countries' polygons). An optional `region:` override covers ambiguous cases, and `global` covers oceans and climate belts. | Region membership is curricular, not geometric (Egypt, Turkey, Russia, Kazakhstan). For 141 features, derivation is cheap and the override handles the exceptions. |
| Adjacency | **Computed at build time** from the same NE 10m admin_0 layer the country cards use. Touching is `intersects` after a ~1 km buffer, to absorb 10m slivers. Sea edges link countries within ~200 km, so island states aren't isolated (UK–France, Japan–Korea, Sri Lanka–India). Hand edits go in `data/adjacency.yaml` (`add`/`remove`, each with a `reason`). Results are cached in `build/adjacency.json`, keyed by an inputs hash, the way `siblings.json` is. | Deterministic and reviewable. ~250 polygons with an STRtree index takes seconds. |

## 2. Ordering engine

`order.py` becomes a package of pure functions over `Card`s. Policy lives in `data/curriculum.yaml`, which the curriculum designer owns: the pass definitions, the region sequence, a start country per region, and where global cards go. The engine is the mechanism.

```
cards ─▶ passes (tier bands; one pass if the curriculum isn't a spiral)
      ─▶ per pass: regions in curriculum order
      ─▶ per region: neighbour walk over countries  → backbone
      ─▶ anchor: capital → its country; city → its country; feature → country of max overlap (or `anchor:` override)
      ─▶ splice anchored cards after their anchor, then run the ADR 0004 local repair:
         parent before child, NEAR_GAP for siblings, category alternation, country→capital gap ≥ 2
      ─▶ ideal order
```

- **Neighbour walk:** a deterministic DFS from the region's start country.
  - The next country is the unvisited neighbour with the fewest unvisited neighbours (Warnsdorff's rule, a good heuristic for Hamiltonian paths). Ties go to the country id.
  - When the walk is stuck, it jumps to the nearest unvisited country by centroid distance, and the jump is counted.
  - A disconnected region subgraph is bridged by its shortest component-to-component edge.
  - `make deck` prints the jumps for each region. A test caps them for each region.
- **Determinism:** no set iteration order and no floats in tie-breaks. Every comparator ends in an id. Golden-file tests use a small fixture world (about 12 countries, 2 regions, 4 features).
- **Stability: the main change.** The ideal order is used **only to place new uids**. Positions are kept in `data/positions.lock` (uid → int). It is committed, append-only, and a retired uid keeps its slot.
  - A new uid gets the midpoint between the locked positions of its neighbours in the ideal order.
  - The initial assignment uses a stride of 500: 700 cards end near 350,000, and there's room for about 1,900 cards and about 8 midpoint inserts at any one spot.
  - Stay below 1,000,000. Anki's Check Database renumbers new cards whose due is ≥ 1,000,000 (*verify*).
  - Exhausting a gap fails the build. A deliberate `reflow` can renumber, but only cards no user has imported yet. In practice that means only before release.
  - DDIA's point that state is a materialization of a log applies: the lock is the log, and the order a user sees is that log. Today's ADR 0004 behaviour (positions shift on every addition, plus README instructions to Reposition by hand) is *shifting the burden*. The lock removes the drift at its source.
- **Mechanism:** ankc numbers cards 0..N by source order and has no way to set `due` directly. Add a per-card `[^pos]: <int>` footnote to ankc 0.6, beside `[^uid]`/`[^type]`. The fallback is to rewrite `cards.due` in the `.apkg` after the build. That's possible because `check_package` already opens the sqlite, but it puts a packaging concern in this repo. `check_package` then asserts `due == positions.lock[uid]` instead of sequential order.

## 3. Migration and identity

- **Uids:** unchanged. Feature notes keep their GUIDs and are updated in place. **Don't change the ankc note type (model id or fields) for basic cards.** A notetype mismatch on import is the one way existing notes get duplicated instead of updated.
- **Deck rename:** ankc derives the deck id from the name, and Anki doesn't move existing cards between decks on re-import. Renaming puts the 141 existing cards in the old deck and every new card in the new one. Users fix that by hand with **Change Deck**, as in the flat-deck migration. This release is the cheapest point to rename, because every card added to the deck after it would also need moving.
- **Positions for existing users:** an imported feature card keeps its v1 `due` (0–140). Re-import never repositions it, as required. Under the lock, a v1 user's unstudied features come before all countries. A fresh import gets the interleaved order. Document this, and offer "delete and re-import" to anyone who hasn't started. Don't build anything to reposition old cards.
- **Retirement:** unchanged (`retired: true`, keep the entry and its lock slot).

## 4. Build cost and scale

| Item | Today | At ~700 cards | Action |
|---|---|---|---|
| Cold render | 141 × 10 s | ~7,000 s ≈ 2 h at JOBS=1. JOBS=2 needs ~3 GB, which is the whole machine. | **Share frames.** A country, its capital and its cities use one frame, so render the basemap once per frame and composite the overlays. That leaves ~350 distinct frames, about 1 h cold. Measure first to confirm the basemap dominates. Loading the NE layers before forking would let workers share pages copy-on-write. |
| Render cache | Keyed by input hash plus the source of render/frame/resolve/model/style. Lives in gitignored `build/`. | Any edit to `model.py` invalidates everything. | Hash `RenderSpec` (see §1). Split the code hash so changing a country style doesn't re-render features. Optional: restore the cache in CI with `actions/cache`. |
| Pair check | ~40 s; O(n²) bbox prefilter, then `compare()` on near pairs | Don't add countries or cities to it. Country outlines don't overlap and capitals are distinct points. | Keep the pair check to features. Add two cheap checks: **country × land-family features** with an STRtree, report-only, because "Country: Italy" against "Peninsula: Italian" differ only in the prompt word; and **dot spacing**, which fails when two city/capital rings in the same frame overlap. |
| `.apkg` | 21 MB (~150 KB/card) | ~100 MB | Acceptable for import. Verify AnkiWeb's sync and shared-deck limits if the deck will be distributed. Levers: 1200 px renders, or WebP (check that AnkiMobile and AnkiDroid support it first). |
| Guide PDF | 12 MB | ~60 MB | Downsample the embedded images (62% of the page width doesn't need 1600 px) and section it by region. Optionally, `make guide REGION=…`. |

## 5. Repo and naming

- **One repo.** One order needs every card in one process, and the renderer, NE vendoring, framing and checks are shared. Splitting the repo would turn an in-process function call into a cross-repo contract. Draw the boundaries inside the repo instead: `sources/` (features, countries, cities) → `Card` → `order/` → `deckgen`/`guide`/`check`.
- **Rename the repo** (GitHub redirects the old URL; update the remote and README links). **Rename the deck** once (see §3). **Keep the package name `geofeat`.** It's internal, and renaming it is churn that no user sees. Rename `deck/geographic-features.md`, `dist/*.apkg` and the Makefile `DECK`.

## Risks

1. **No stable positions without an ankc change.** Without `[^pos]` or an apkg rewrite, every country added reshuffles positions for fresh imports and ties with existing ones. Do the lock before the countries ship, not after.
2. **Political edge cases in the data:** NE's de facto worldview, disputed states (Kosovo, Taiwan, Western Sahara, Palestine, Somaliland), dependencies, and whether the target is ~200 or ~215 states. These decide card count, adjacency and regions.
3. **Micro-states at the 2,600 km minimum frame** (ADR 0003): an outline card for Vatican City, Monaco or Nauru is just a ring, so "outline → name" teaches the frame, not the shape. Consider a smaller minimum frame for small `outline` cards, or capital-only cards for micro-states.
4. **Wide or split countries:** Russia, Fiji and Kiribati cross the antimeridian, and France and the USA have overseas parts. The PoC's `mainland` box handles this, but every case needs `expect` coverage.
5. **Walk quality on archipelago regions** (Caribbean, Oceania, Southeast Asia): jumps are unavoidable there. Report them rather than hiding them.
6. **The render invalidation footgun** in `_code_hash` (see §4). Fix it before scaling past 141.
7. **Anki behaviour assumptions:** new-card `due` preserved on import, and the 1,000,000 cap. Both were read from desktop sources only. Test on AnkiDroid and AnkiMobile before relying on the lock.

## Decisions needed (defaults in bold)

| # | Decision | Default |
|---|---|---|
| D1 | Card shape for a state | **Two notes (country, capital)** |
| D2 | Data layout | **`countries.yaml` + `cities.yaml`, separate models, shared `Card` DTO** |
| D3 | Region source | **Explicit for countries; derived for features, with an override** |
| D4 | Stable positions | **`positions.lock` + ankc 0.6 `[^pos]`**. Fallback: apkg rewrite. |
| D5 | Position stride and cap | **500, assert < 1,000,000** |
| D6 | Deck name | **`Geography`, renamed once in this release** |
| D7 | Repo name / package | **Rename the repo (e.g. `geography`); keep `geofeat`** |
| D8 | State list and worldview | **NE default (de facto) admin_0, UN members + observers; others as `retired`/opt-in.** The curriculum designer confirms. |
| D9 | Spiral passes | **Taken from `curriculum.yaml`; one pass if the curriculum doesn't define any** |
| D10 | Global features (oceans, climate) | **Their own interlude at the end of each pass** (or wherever the curriculum puts them) |
| D11 | Micro-state outline cards | **Capital card only below a size threshold** |

## ADRs to write

- 0005 card sources and the `Card` DTO
- 0006 stable positions via `positions.lock`, superseding the "drift" consequence in 0004
- 0007 deck and repo rename, with migration steps
- 0008 state list, worldview and adjacency rules

Specialist follow-ups: `data-engineer` for the adjacency and region-derivation rules, and `technical-writer` for the migration section of the README.
