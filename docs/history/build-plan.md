> Archived 2026-10-15 after the v2.0.0 release. This is the PM working copy of the build plan; paths refer to the original dev machine. The maintained plan is [world-atlas-plan.md](../world-atlas-plan.md).

# World Atlas build plan (saved 2026-10-14, from the Plan agent; PM copy)

## Ground rules (every workstream)
- **Worktrees:** each workstream gets its own git worktree off main (`git worktree add ../gf-<ws> -b ws/<ws> main`). The primary checkout stays on `poc/countries`.
- **Shared inputs:**
  - Symlink `vendor/` from /home/dev/geography-features/vendor.
  - Before rendering, copy `build/render-cache.json` and `deck/*.png` from the latest main build.
- **Rendering:** one render at a time on the machine (a render token; JOBS=1; `make test` counts as a render). Budget 3.5–10 s per map.
- **Data:** Natural Earth only via `make fetch` (`gh api`). Never use /home/dev/ultimate-geography.
- **Reviews:**
  - Code and pipeline-data commits: code-reviewer, system-architect and security-analyst in parallel; fix critical and high findings first.
  - Docs-only commits: technical-writer.
  - No AI attribution in commits, and none in PR bodies (memory rule).
- **ankc:** PRs go to `dev`; the user merges and releases to main.
- **File ownership:** exclusive within a phase.

## Open decisions (default; blocks)
1. **Disputes without a UN sovereign** (blocks P2 and P4):
   - UN-assigned areas go inside their sovereign: Crimea→Ukraine, Abkhazia and South Ossetia→Georgia, Transnistria→Moldova, N. Cyprus→Cyprus, Golan→Syria, Somaliland→Somalia; Essequibo is already in Guyana.
   - Western Sahara is cut out of Morocco.
   - Kashmir parts, Aksai Chin, Arunachal and the Kurils stay with their administrators.
   - Disputed basemap lines are dashed (NE boundary_lines_disputed_areas).
   - The basemap change re-renders all 132 feature maps once.
2. **State list** (blocks P2): 197 country cards (193 UN members + Vatican, Palestine, Kosovo, Taiwan). N. Cyprus, Somaliland and W. Sahara get dispute cards only.
3. **Capitals** (blocks P2):
   - Multi-capital states get one card, using NE's `Admin-0 capital`.
   - No capital card for the same-name microstates: Monaco, Vatican, Singapore, San Marino?, Luxembourg?
   - No capital card for Palestine, territories or disputes.
4. **Territory/dispute cards:** front `Territory` / `Disputed territory`; back line 2 gives the status or `Disputed: parties`; dashed red outline.
5. **Territory placement:** geographic pockets, with a manual look at Greenland, the Kurils and Bermuda.
6. **Close dots** (Tel Aviv/Jerusalem, Dubai/Abu Dhabi): a tighter frame (≥1,000 km) when another dot is within 150 km.
7. **Continents:** 7 cards from NE region polys; new `Continent` type and family; shown in orientation.
8. **Curriculum defaults:** 21 regions; pass 1 = tier 1–2 + core cities; drop category alternation; 15/day; no repositioning tool.
9. **Scattered states:** the whole spread plus a ring.
10. **Somaliland:** NE outline, with Las Anod in the blurb.
11. **Repo name:** rename to `world-atlas`; keep the `geofeat` package.
12. **Distribution:** GitHub release only (.apkg ~100 MB + guide PDF).

User gates: merge the ankc 0.6 release; sign off the walk maps (P3) and region sheets (P4); device tests (P6).

## Phases
- **P0** Decisions and ADRs 0005–0009 (WS6, alongside P1).
- **P1** Foundations, WS1–WS6 in parallel:
  - **Merge order:** WS2 before WS4; WS3 after the ankc 0.6 release.
  - **Exit:**
    - `make all` passes with ankc 0.6.
    - `media.json` has the same 132 PNG names.
    - `check package` asserts due == positions.lock.
    - `make fetch` verifies the new layers.
    - cities.md and ne-political-layers.md are done.
- **P2** Data and content, in parallel:
  - 2.1 political model (`src/geofeat/sources/`)
  - 2.2 countries.yaml (197)
  - 2.3 territories.yaml (23 + 15)
  - 2.4 cities.yaml
  - 2.5 curriculum.yaml + adjacency.py (1 km buffer, 200 km sea edges, cached)
  - 2.6 regions.py + continents in features.yaml (`model.py` edit is safe after WS2)
  - 2.7a–d blurbs: ~530, in 4 regional researcher streams; [V]/[S] keys, no unverified figures, plus a second-researcher fact check
- **P3** Order engine (`order/` package: passes, regions, frozen walks, anchoring, repair rules, golden tests), walks + walk maps for the user, political checks, notes merged into the data.
- **P4** Rendering treatments (dispute/territory dashed, recognised-border basemap, close-dot frames, scattered states, shared basemap if >50% of render time), review tooling by region; cold render of ~560 maps (35–95 min); region sheet sign-off.
- **P5** Guide in study order (pass → region → order; <80 MB) ∥ rename to World Atlas (deck file, README migration, uid freeze test of the 166 feature uids, note model id unchanged).
- **P6** QA: phone sheets, pairs (features + continents only), CVD on the new treatments, device tests (fresh import order, filtered "Order due", due ≥1M, v1→WA upgrade path).
- **P7** multi-lens-review + 3-agent review; freeze positions.lock (append-only check against origin/main); clean-clone build; tag v2.0.0; GitHub release; archive poc/countries as a tag.
  - Release assets MUST include dist/world-atlas.apkg and build/world-atlas-guide.pdf (user requirement).

## P1 briefs (condensed)
- **WS1 ankc 0.6 `[^pos]`** (/home/dev/ankcompiler, `feature/card-positions` → dev)
  - Optional `[^pos]: <int>` footnote sets the new-card due.
  - Rules: all-or-none per package; 0 ≤ pos < 1e6; unique; every card of a note shares the due.
  - No `[^pos]` builds exactly as 0.5.
  - `ankc check` validates; `uid --fix` keeps it; note model ids unchanged.
  - Version 0.6.0; README; `make check`.
- **WS2 render core** (`ws/render-core`)
  - Promote the PoC render/style hunks (`git diff cf89ef5 68a356b -- render.py style.py`).
  - New `spec.py` with `RenderSpec`.
  - Cache key = spec + renderer code (not `model.py`) + uv.lock + only the lock entries for the layers the card uses.
  - Exit: identical 132 PNG names. Merge before WS4.
- **WS3 Card DTO + positions** (`ws/card-positions`)
  - `card.py` (Card DTO); deckgen emits Cards with `<br>`-joined answers, `kind::feature` and `[^pos]`.
  - `positions.py` with `data/positions.lock`: uid→int, stride 500, midpoint inserts, `draft: true` until P7, under 1e6.
  - check: ankc 0.6.x, due == lock.
  - `ids.py` generic across sources, with uid uniqueness across sources.
  - Makefile `positions` target.
- **WS4 NE political layers** (`ws/ne-layers`)
  - Pin populated_places, admin_0_map_units, admin_0_disputed_areas, boundary_lines_disputed_areas.
  - `docs/research/ne-political-layers.md`: state→row/ne_id + capital ne_id; territory/dispute composition; recognised-border composition table; POV layers; stale shapes.
  - Optional `tools/ne_survey.py`.
- **WS5 cities + continents research** (`ws/content-cities`, researcher)
  - 80–150 cities: core ~55 / secondary, all 21 regions, ne_id + wikidata.
  - Flag dots within 150 km and cities in disputed areas.
  - Continents: NE ne_ids + convention.
  - Second-researcher fact check; user confirms the list.
- **WS6 docs** (`ws/docs-adrs`, technical-writer)
  - Update world-atlas-plan.md with the 2026-10-14 decisions; mark the PoC de facto border view as superseded.
  - ADRs 0005–0009 as Proposed.
  - Status lines on 0003 and 0004.

## Architect review of the plan (2026-10-14)
- **C1:** run a headless Anki import spike before WS1/WS3. Does re-import keep the package's `due` values on new notes and leave existing cards untouched? Does Check Database renumber due values ≥1e6? If not, switch to an apkg-rewrite design or drop the lock.
- **H1:** merge order is WS2 → {WS3, WS4}. WS2 owns `model.py`, `spec.py` and `render.py`. WS3 puts the Feature→Card adapter in `sources/features.py`.
- **H2:** one owner per file. WS3 owns `check.py` and the Makefile. WS4 owns only `fetch.py`, `sources.lock` and its docs, and hands over a Makefile diff.
- **H3:** midpoint rule. `pred` = the nearest earlier card in the ideal order that is in the lock; insert between `lock[pred]` and the next locked value above it; spread several inserts evenly through a gap; fail when a gap is exhausted; property test.
- **H4:** the uid-freeze golden test (all 166 feature uids) moves into WS3.
- **H5:** WS1 adds a golden test of the note model (id, fields, templates, CSS). Feature cards keep their current type and fields.
- **H6:** WS3 first relaxes the ankc version gate to `>=0.5,<0.7`; don't install 0.6 globally before then (pin per worktree via uv).
- **M1:** declared layer set comes from `RenderSpec.layers()` plus BASEMAP_LAYERS; the loader raises on any undeclared layer.
- **M2:** WS2 exit requires a pixel diff of the 132 maps, not just matching names.
- **M3:** `make positions` is the only writer of the lock; draft mode regenerates it with stride 500; no `reflow`.
- **M4:** the `<br>` answer format rewrites all 132 existing notes on re-import; note this in the README.
- **Low:** P1 needs only the lock format, stride, draft flag, the due==lock check and the H3 rule; `ids.py` becomes a simple `mint_missing(paths)`.

## Spike result (2026-10-14): the sparse lock works
- Tested with anki 26.09.3 in 9 cases.
- Import stores new notes' `due` exactly as packaged and never changes existing cards; other decks' new cards cause no shift.
- Hard limit: due < 1,000,000. Check DB rewrites values ≥2,000,000 to `1e6 + due % 1e6`.
- Spike files: /tmp/claude-1000/anki-spike/ (spike.py, RESULTS.md).
