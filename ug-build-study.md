# Ultimate Geography: build pipeline study

Repo studied: `/home/dev/ultimate-geography` at `6725c0f` (read-only). Scope is process and architecture only. Paths below are relative to that repo unless absolute. The build was also run in a scratch clone (Brain Brew 0.3.11, Python 3.11 via `uv`) to verify the behaviour described here.

## TL;DR

- **Source of truth:** flat CSVs (one note per row, one CSV per translatable field, one column per language) plus YAML note models, HTML templates and a CSS file. Media files sit in the repo already optimised and are referenced by `<img>` tags inside the CSV cells.
- **Build:** a small Python templater expands per-language note models and templates. [Brain Brew](https://github.com/ohare93/brain-brew) then compiles CSV, YAML and media into **CrowdAnki JSON folders**, which are zipped for release. The repo never produces an `.apkg`. The AnkiWeb copy is shared by hand from the maintainer's own Anki.
- **Images:** there is **no image pipeline**. Maps are hand-made PNGs, exported from Wikimedia SVG locator maps in Inkscape. Flags are hand-optimised SVGs from Wikimedia. Size and optimisation rules exist only as prose in CONTRIBUTING.md, nothing enforces them, and the repo already breaks them.
- **CI:** one workflow that runs the build. It proves the recipes parse, and nothing about media.

---

## 1. Source of truth

### Layout

```
src/
  data/                 main.csv + per-field "derivative" CSVs + guid.csv
  note_models/
    translations.csv    per-language template strings, note-model IDs, text direction
    style.css, style_[Experimental].css
    templates/base/     note-model YAML + card HTML with __TOKEN__ placeholders
    templates/generated/  (gitignored) rendered output, one dir per language
  headers/              deck header YAML + per-language description HTML
  media/{maps,flags,experimental_assets}/
recipes/                Brain Brew recipes
sources.csv             media attribution
physical-entities.xlsx, political-entities.xlsx   inclusion-rule worksheets (binary)
```

### Notes: a main CSV plus "derivatives"

- `src/data/main.csv:1` has the columns `country,flag,map,region code,ISO,tags`. These are the non-translatable fields. Media cells hold raw HTML, e.g. `"<img src=""ug-map-england.png"" />"` (`main.csv:2`).
- Each translatable field gets its own CSV with one column per language: `country.csv`, `country_info.csv`, `capital.csv`, `capital_info.csv`, `capital_hint.csv`, `flag_similarity.csv`. Headers look like `capital,capital:de,capital:es,…` (`src/data/capital.csv:1`).
- Derivatives join to `main.csv` on the `country` key column, and a derivative can be **sparse**: a row that doesn't apply is simply left out (CONTRIBUTING.md:59). For example, `capital_hint.csv` has 7 lines against 324 in `main.csv`.
- `guid.csv` holds one stable Anki GUID **per language** (`guid`, `guid:de`, …). Brain Brew fills in missing GUIDs during the build (`recipes/source_to_anki.yaml:1-17`, `generate_guids_in_csv`). That means **the build writes to the source tree**, and contributors commit the generated GUIDs (e.g. commit `c2d0b42` adds a fully populated `guid.csv` row).
- Tags are a comma-joined string in `main.csv` (`brain_brew_config.yaml`: `join_values_with: ", "`), namespaced `UG::…`.

### Note models, templates, styling

- `src/note_models/templates/base/Ultimate_Geography_[__LANGUAGE_CODE__].yaml` defines the fields and lists the card templates by `html_file`. Note-model IDs and RTL flags are tokens (`__DECK_ID__`, `__IS_RIGHT_TO_LEFT__`).
- Variants are separate base YAMLs that add templates or fields: `…_[Extended].yaml` adds `Country - Flag` and `Country - Map`, and `…_[Experimental].yaml` adds a `Region code` field and a different CSS file.
- Each card template is one HTML file per direction, with the front and back separated by a line containing `--` (e.g. `templates/base/Map - Country [__LANGUAGE_CODE__].html`).
- All variants share one CSS file (`src/note_models/style.css`). The experimental CSS only adds an `@import` of the vendored map CSS.

### Languages

- `src/note_models/translations.csv` has one row per language. Its columns are the placeholder tokens (`__CAPITAL_TRANSLATION__`, `__TEXT_DIRECTION__`, the three note-model UUIDs, …).
- `utils/generate_and_build.py:43-75` does a naive string replace of every token into every base file and writes `templates/generated/<LANG>/`. It guards against one token being a substring of another (`validate_subtokens`, `:7-12`) and against empty cells (`:25-29`). It also hard-codes renaming `Ultimate Geography [EN]` to `Ultimate Geography` (`:57-58`, `:70`).
- Deck descriptions are separate hand-written HTML files per language (`src/headers/desc*.html`, 6 files). Languages without one fall back to English (`recipes/source_to_anki.yaml:119-155`).

### Deck variants

The variants are standard, extended and experimental, each in 16 languages. Every variant is a separate **note model** fed by the **same notes and the same GUIDs**. The recipe does this with `override: note_model: …` (`recipes/source_to_anki.yaml:701-708`). Because the GUIDs are shared, users can move up from standard to extended by re-importing, without losing progress.

## 2. Build tooling

### Dependencies

- `Pipfile:9,12`: `brain-brew==0.3.11` on Python 3.11, managed by Pipenv. No other runtime dependencies.
- End users need the **CrowdAnki** Anki add-on to import releases (README.md "Getting started").

### Commands (`Pipfile:15-19`)

| Command | What it does |
|---|---|
| `pipenv run generate_templates` | Renders `templates/base` × `translations.csv` → `templates/generated/` |
| `pipenv run build` | Above + `brain_brew run recipes/source_to_anki.yaml` (standard + extended, 32 deck folders) |
| `pipenv run build_experimental` | Above + experimental recipe (16 folders) |
| `pipenv run zip` | `utils/zip_decks.py`: zip each `build/*` folder as `Ultimate_Geography_v{X.Y}_{LANG}[_EXTENDED].zip`; version scraped from `desc.html` by regex (`zip_decks.py:44-50`) |
| `pipenv run flag_similarity a b` | Helper for comparing flag colours and aspect ratios (see §5) |

`generate_and_build.py:92` shells out to a bare `brain_brew`, so it only works inside an activated venv or `pipenv run`. Calling the venv's Python directly fails with `FileNotFoundError`.

### Flow

```
translations.csv ─┐
templates/base/* ─┴─ generate_and_build.py ──► templates/generated/<LANG>/*.yaml|*.html
                                                    │
src/data/*.csv ──┐                                  ▼
src/headers/* ───┼── brain_brew run recipes/source_to_anki.yaml
src/media/** ────┘      1. generate_guids_in_csv   (writes back into src/data/guid.csv)
                        2. build_parts: note models, headers, media groups, notes_from_csvs (per language)
                        3. generate_crowd_anki ×32 ──► build/Ultimate Geography [LANG] [Variant]/{deck.json, media/}
                                                                   │
                                          utils/zip_decks.py ──────┴─► build/*.zip  → GitHub release assets
```

- The recipe is about 860 lines of near-duplicate YAML (`recipes/source_to_anki.yaml`). It is one `note_model_from_yaml_part`, one `notes_from_csvs` and two `generate_crowd_anki` blocks per language, with YAML anchors (`&default_columns_to_fields` `:174`, `&file_mappings` `:190`, `&default_crowd_anki_gen` `:555`) cutting some of the repetition. Adding a language means hand-editing three recipe sections, `generate_guids_in_csv`, and every CSV.
- Each media group is declared once (`:157-163`, `media_group_from_folder` over `src/media/maps` and `src/media/flags`) and copied into **every** output deck. In the scratch build, each deck folder held all 550 files (about 17 MB).
- Full build time is about 3.4 s for 32 decks.

### Reverse direction (Anki → source)

`recipes/anki_to_source.yaml` and `anki_to_source_[extended].yaml` read a CrowdAnki export from `build/Ultimate Geography [EN]` and regenerate the CSVs, dumping media into `src/media`.

## 3. Image pipeline

**Nothing is scripted.** Images arrive as finished binaries in a PR, and the build copies them through unchanged. The rules exist only as prose.

### Maps (`CONTRIBUTING.md:330-341`)

| Step | Who/what | Evidence |
|---|---|---|
| Source | Wikimedia "SVG locator maps (16:9 regional location map scheme)", or a hand-made map "inspired" by them | CONTRIBUTING.md:334 |
| Edit (highlight, zoom box, recolour, remove grid) | Manual, Inkscape | `sources.csv` "Modifications" column: "zoom box added", "highlight changed", "grid removed", "colours adjusted for consistency" |
| Export to PNG | Manual (Inkscape) | 99 of 323 PNGs still carry an Inkscape `tEXt` chunk (`Software: www.inkscape.org`) |
| Resize to 500 px wide, about 281 px tall | Manual | CONTRIBUTING.md:339 |
| Optimise | Manual, "a tool like PNGGauntlet" (Windows GUI) | CONTRIBUTING.md:338 |
| Style consistency ("match existing maps; water bodies use a different style") | Reviewer's eye | CONTRIBUTING.md:340 |
| Attribution | Manual row in `sources.csv` | CONTRIBUTING.md:334 |

Observed state of `src/media/maps` (323 PNGs, 13 MB):

- Widths are 500 px except `ug-map-gulf_of_oman.png`, which is **508×281**. It was added in the latest map PR (`c2d0b42`, 2026-07-27), so the rule was broken recently and nothing caught it.
- Heights range from 276 to 318 px, with outliers at 421 px (the four UK constituent-country maps). PNG colour types are a mix of RGB and RGBA.
- Optimisation is inconsistent. Commit `700056f` ("[ImgBot] Optimize images", 2022) ran an external GitHub bot once, and nothing has run since.
- **The source SVGs are not kept.** Only the exported PNG is committed. A map can't be regenerated or restyled without starting again from the Wikimedia original and redoing every manual edit. The "Modifications" column is the only record of what was done.
- Filename suffixes carry rendering semantics. `-nobox` turns off the CSS drop shadow for maps or flags without a rectangular outline (`style.css:54`, `:97-98`).

### Flags (`CONTRIBUTING.md:274-290`)

| Step | Who/what |
|---|---|
| Source | Wikimedia SVG, chosen by a documented editorial rule (infobox vs flag article; lag edits by months) |
| Normalise | Manual: ensure `viewBox`/`width`/`height`, set `height="250"`, scale width proportionally |
| Optimise | Manual, the SVGOMG web UI |
| Blurred variant (name visible on flag) | Manual Inkscape Gaussian blur → `ug-flag-<x>-blur.svg`. The Flag field holds two `<img>` tags, and CSS hides one per side (`style.css:62-68`) |
| Attribution | Manual `sources.csv` row |

Observed: 226 of 227 flags meet the height and `viewBox` rule. `ug-flag-marshall_islands.svg` has no `viewBox`. Three flags still contain Inkscape or Sodipodi metadata (`aruba`, `haiti`, `vatican_city`), so they weren't run through SVGO.

### Experimental interactive map

The experimental `Country - Map` template (`templates/base/Country - Map [__LANGUAGE_CODE__] [Experimental].html`) drops the PNG on the front. Instead it renders a clickable vector world map with vendored jsVectorMap (`src/media/experimental_assets/_ug-jsvectormap.js`, `_ug-world.js` at 1.3 MB). Each note is keyed by a `Region code` column in `main.csv`, and the PNG is still shown on the back. This is the only data-driven map rendering in the repo. It works only for entities that exist as regions in the world shapefile, which is why the feature is limited to the experimental deck.

### Media attribution: `sources.csv`

Columns are `File,Source,License,Modifications` (`sources.csv:1`), all Wikimedia Commons URLs. The file is maintained by hand and nothing checks it. It has already drifted:

- `sources.csv:505-506` lists `ug-map-strait_of_hormuz` and `ug-map-strait_of_malacca` **without the `.png` extension**, so they don't match the files on disk.
- The "Modifications" column is free text and mostly empty (509 of 549 rows). For `-blur` flags it is inconsistent: some rows record the blur radius and others are blank.

## 4. Card generation

- There is one note type per variant and language, with 8 fields (9 in experimental). The standard model has 4 templates: `Country - Capital`, `Capital - Country`, `Flag - Country`, `Map - Country`. Extended adds the reverse image directions, `Country - Flag` and `Country - Map` (base YAML diff, §1).
- Each direction is its own template file. Templates are not parameterised by direction.
- **Optional fields use Anki's empty-card rule.** Every front side is wrapped in a section on the field it needs, e.g. `{{#Capital}}…{{/Capital}}` (`Country - Capital …html:2,10`) and `{{#Map}}…{{/Map}}`. When the field is empty the front renders empty, so Anki doesn't create the card. That's how a map-only note produces a single card.
- Supplementary fields render conditionally on the back (`{{#Country info}}<div class="info">…`). `Flag similarity` is interpolated into a translated sentence that itself contains a field reference (`translations.csv`: `Flag similar to {{Flag similarity}}.`).
- "Produce" directions (`Country - Map`, `Country - Flag`) show an inline SVG **placeholder silhouette** on the front, hinting at the expected answer type (`Country - Map …html:7-17`, `style.css:74-82`).
- Semantics come from CSS keyed on filenames (`-blur`, `-nobox`). Notes contain no layout markup beyond the `<img>` tag (README "Deck structure").

## 5. Quality and release

### Validation

- **CI** (`.github/workflows/integrity-check.yml:1-31`) runs on push and PR: `pipenv install`, then `pipenv run build` and `pipenv run build_experimental`. Line 31 is literally `# TODO: Validate the csv file structure`.
- What the build does catch, verified in scratch:
  - a derivative row with no matching `main.csv` row fails with `Cannot match derivative row … to parent`
  - empty translation cells fail
  - template token collisions fail
- What it **doesn't** catch (also verified):
  - an `<img src>` pointing at a non-existent file (build exits 0)
  - orphan media
  - image dimensions, format or optimisation
  - missing or malformed `sources.csv` rows
  - SVG `viewBox` problems
- There is no test suite, linter or pre-commit config.
- `utils/flag_similarity.py` is a **manual reviewer aid**, not a check. It parses flag SVG `fill` colours, buckets them by CIELAB ΔE, and compares aspect ratios from `viewBox`, supporting the editorial rule in CONTRIBUTING.md:292-328.

### Release (`CONTRIBUTING.md:386-421`)

The process is about 20 manual steps:

1. Bump the version **by hand** in `src/headers/desc.html`. The version string also appears in 5 other `desc_*.html` files, which the checklist doesn't mention.
2. Build, then upgrade the maintainer's own Anki collection. Read the note and card counts from Anki's browser and **hand-edit** them into `desc.html` and `README.md`. These counts already lag the CSVs: `desc.html` says 319 notes while `main.csv` has 323 rows.
3. Rebuild, run `pipenv run zip`, then draft a GitHub release, attach the zips and write release notes by hand following a detailed style guide (`CONTRIBUTING.md:423+`).
4. Re-share on AnkiWeb by hand and post to Reddit.

Versioning is `x.y`, with major bumps reserved for changes that lose user progress (`CONTRIBUTING.md:388-395`). There is no CHANGELOG file and no tags-driven automation. GitHub Releases are the changelog.

## 6. Contributor workflow

- Contributors edit CSVs directly (preferred) or edit in Anki and round-trip (`CONTRIBUTING.md:89-106`). The documented recipe is: CrowdAnki-export into `build/…[EN]`, run `anki_to_source.yaml`, then move any new media from `src/media/` into `maps/` or `flags/` by hand.
- The round trip is **English only**, and only covers note content, not models, templates or descriptions (`CONTRIBUTING.md:93`).
- It is **not idempotent**. Running `anki_to_source.yaml` on an untouched fresh build changed 4 CSVs (17 lines): it lowercased the `ISO` header, reordered rows in `flag_similarity.csv` and normalised some cells.
- Editorial rules are documented in detail (`CONTRIBUTING.md:216-347`), and inclusion criteria live in binary `.xlsx` worksheets that can't be diffed.
- Docs have drifted from config: CONTRIBUTING.md:66 says "Install Python 3.7" while `Pipfile:12` pins 3.11.
- History shows one big tooling migration, from anki-dm to Brain Brew in Dec 2020 (commit `7f93309` deletes `src/anki-dm-leftovers/`), plus the template generator added in Jan 2026 (`64ddd86`).

---

## Verdict

UG is a good model for **data and deck architecture**. It is not a model for **image production**: it has no image pipeline at all, only a style guide and reviewer vigilance. Copy the first half and build the second yourself.

### Patterns worth adopting

1. **Plain-text, diffable source with stable GUIDs committed to git.** One row per note, GUIDs generated once and then frozen. This is what makes upgrades preserve review history. Keep GUID generation, but as an explicit `ids` step rather than a side effect of `build`.
2. **One shared note set and GUIDs across variants, with variants as separate note models.** Variants only add or remove templates (`override: note_model`), so users can switch variants without losing progress. Use this if you ever ship "core" and "extended" decks.
3. **Optional-field gating with `{{#Field}}` on the front of each direction.** Card existence then becomes a property of the data: a note without a name-able label or without a reverse image just doesn't produce that card. No per-note card configuration is needed.
4. **Sparse per-field side tables joined on a key** (derivatives). Optional supplementary data stays out of the main table, and a missing parent is a hard error.
5. **A `sources.csv` attribution ledger** (file, source URL, licence, modifications). It is a must for Wikimedia CC BY-SA content. Adopt it, but generate and validate it (see below).
6. **Placeholder silhouettes on "produce" cards and CSS-only presentation.** Notes carry only `<img>` tags, and all layout and night-mode handling is in one stylesheet.
7. **Token-templated card HTML plus a translations table**, if you ever localise. Including the substring-collision guard costs about 30 lines.
8. **CI that runs the full build on every PR.** This is the minimum bar. Extend it (below).

### Patterns to avoid or improve on

1. **Committing only exported raster output.** UG keeps no source SVG and no record of the edit beyond a free-text "Modifications" cell, so maps can't be restyled or regenerated in bulk. Commit the *recipe* for each image (source geometry, highlight spec, extent, style) and treat the PNG/SVG as a build artifact.
2. **Image specs enforced only by prose.** The size, SVGO/PNGGauntlet and `viewBox` rules are already broken in the repo (the 508 px map from the latest PR, a flag with no `viewBox`, Inkscape metadata left behind). Put dimensions, format, colour type, max bytes and metadata stripping in a script, and fail CI on violations.
3. **GUI optimisation tools** (PNGGauntlet, SVGOMG) and one-off bots (ImgBot) are not reproducible. Use pinned CLI tools in the build (`oxipng`/`pngquant`, `svgo` with a committed config, or `resvg`/`cairosvg` for rasterising).
4. **A build that doesn't check media references.** A dangling `<img src>` builds green. Add a check that every referenced file exists, every file is referenced (UG currently has no orphans, by luck), and every file has a valid `sources.csv` row with a matching filename.
5. **Hand-maintained derived facts.** That covers the version string in 6 description files, note and card counts copied from Anki's browser, and `sources.csv`. Derive all of them at build time from the data, or from a single `VERSION` file or git tag.
6. **About 860 lines of copy-pasted recipe YAML.** UG already uses a Python templater, so it could generate the recipe too. If you use Brain Brew, generate the recipe from a small config. If you only ship one language, consider skipping Brain Brew entirely (below).
7. **A lossy, non-idempotent Anki → source round trip.** If you support editing in Anki, check that `export → import` of an untouched build is a no-op, or don't offer the round trip.
8. **Release as CrowdAnki zips plus a hand-shared AnkiWeb `.apkg`.** CrowdAnki gives in-place upgrades, which is worth it for a large shared deck, but it forces every user to install an add-on. For a personal or small deck, emit an `.apkg` directly (`genanki` with stable GUIDs and note-type IDs, or the `ankc` compiler) from the same pipeline, and attach it to a tag-triggered GitHub release.
9. **Binary `.xlsx` for inclusion rules.** Keep criteria next to the data as CSV or YAML so they can be diffed.
10. **The build mutating the source tree** (`guid.csv`). A build that silently rewrites tracked files makes CI and local results diverge. Fail when GUIDs are missing and provide a separate command to mint them.

### Gaps your image pipeline must fill that UG doesn't solve

1. **Rendering from geodata instead of hand-editing locator maps.** UG never renders a map. Every image is an artist-edited Wikimedia SVG. You need a renderer: geometry source → projection → basemap → highlight → raster. Typical sources are Natural Earth physical layers, OSM/Overpass, HydroSHEDS/HydroRIVERS for rivers, and GMBA mountain inventory or Natural Earth "geography regions" for ranges. Typical tools are GeoPandas with matplotlib or cartopy, or Mapnik/QGIS headless, or d3-geo in Node.
2. **Highlight types beyond "filled polygon".** UG's only highlight is a filled country or sea polygon plus a zoom box. Physical features need:
   - **lines** for rivers, with a stroke width that is visible at 500 px, optional tributary context, and source-to-mouth emphasis
   - **areas with fuzzy edges** for mountain ranges, deserts and plateaus, using a hatched or semi-transparent polygon or a hillshade-masked region
   - **points or small extents** for straits, capes and peaks, as markers or callouts, because a 10 km strait is invisible on a regional map
   - **water-body fills** that respect coastline detail
3. **Automatic extent and zoom selection.** UG hand-picks a frame per map and adds zoom boxes by hand for small things. You need rules: bounding box of the feature plus padding, a minimum context radius, an aspect ratio locked to your card size, and automatic inset or zoom-box generation when the feature's on-screen extent falls below a threshold.
4. **Consistent style as code.** "Match the existing maps" can't be reviewed by eye at scale. Define one style spec (palette, stroke widths per feature class, label policy, night-mode variant) that every map is rendered from, so a restyle is a single rebuild.
5. **Geometry provenance and licensing per derived image.** UG attributes the source image. You will attribute **datasets** (e.g. Natural Earth is public domain, OSM is ODbL and needs a notice, HydroSHEDS has its own licence). Generate `sources.csv` from the per-feature recipe rather than typing it.
6. **Disambiguating geometry.** Rivers and ranges have contested or fuzzy extents, multiple named segments, and transboundary names. You need a per-feature override layer (custom clip polygon, segment selection, "include tributary X") that UG never needed, because it edited the SVG by hand.
7. **Reverse-direction cards for line and area features.** UG's `Country - Map` asks for a mental picture of a filled region. For rivers and ranges, consider whether "name → draw or locate" is a useful card. If it is, you may need an unlabeled basemap variant per feature, or an interactive approach like UG's experimental jsVectorMap. That approach only works for features that exist as regions in a bundled shapefile, so line features would need a custom vector layer.
8. **Visual regression checks.** Because your images are generated, you can and should snapshot them (dimension and byte budgets, perceptual-diff against the previous release) so that a data or library update doesn't silently change hundreds of maps. UG has no equivalent because nothing is regenerated.
