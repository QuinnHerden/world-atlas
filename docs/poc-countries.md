# Countries PoC

A 9-card proof of concept for extending this pipeline to countries, capitals and major cities. It lives on the `poc/countries` branch, apart from the main deck, with its own data file, deck and package.

## What was built

Two cards per country, and one card for a major city:

| Card | Front (prompt + map) | Back |
|---|---|---|
| Country | **Country**: the country in a crisp 6 px `#B2182B` outline with a white casing, over a faint 12% red fill. Neighbours stay neutral. | `France` |
| Capital | **City**: the capital as a 36 px `#B2182B` dot (about 9 px on a phone) in a 3 px white casing with a dark hairline outside it, and no ring. The country is context only: washed lighter, edged in dark grey, no red. | `Paris`<br>`Capital of France` |
| City | **City**: as the capital card. | `Lagos`<br>`Nigeria` |

Sizes are for a map 1,600 px wide. The dot has no locating ring, so it is drawn larger to compensate. The casing and hairline keep it legible on land, water and the washed country alike.

### Labelling

Capital and major-city cards both say **City** on the front. The type word must not give the answer away: a front saying "Capital" tells you the answer is the country's capital before you've placed the dot, which turns a recall card into a recognition one. The back says whether it is a capital: the city, then `Capital of <Country>` on a second line. A major city's back is the city, then the country. Country cards are unchanged.

Names on the back are HTML-escaped, as in `deckgen.py`. The `<br>` between the two lines is the only literal markup.

The deck **Geography PoC — Countries** has 9 notes: France/Paris, Brazil/Brasília, Japan/Tokyo and Switzerland/Bern (two cards each), plus Lagos (one card). Each note is tagged `kind::country`, `kind::capital` or `kind::city`, plus `id_<entry-id>`. The tag keeps capitals and cities apart, though their fronts don't.

The maps use the main renderer unchanged except for the highlight. Framing (north-up equirectangular, 2,600 km minimum), basemap, relief, inset and small-area ring are all the same. `render()` gained two optional arguments: `country` (`subject` for the outline, `context` for the wash behind a dot) and `dot`.

### Build

```sh
make poc     # test → fetch → render 9 maps → ankc check → ankc build
```

Output:

- `dist/poc-countries.apkg`
- `build/poc-sheet.png`: every card front at 960 px wide
- `build/poc-phone.png`: every card front at 390 px wide, as on a phone

`make all` clears `dist/*.apkg` before building the main deck, so run `make poc` after it.

### Files

- `data/poc-countries.yaml`: the entries. A country is selected by `ne_id` from `10m_admin_0_countries`, a city by `ne_id` from `10m_populated_places`. Each has an `expect` bbox it must fall in. `mainland` keeps only the polygons inside a box, dropping overseas departments and remote islands (French Guiana, Trindade, Minami-Torishima).
- `src/geofeat/poc.py`: selects, renders, and writes `build/poc/poc-countries.md` and the contact sheets.
- `src/geofeat/render.py`, `style.py`: the country treatments and the dot.
- `data/sources.lock`: adds `ne_10m_populated_places.geojson` at the existing pinned commit.

## Data and licences

- **Natural Earth** v5.1.2, commit `f1890d9f`, public domain. `ne_10m_admin_0_countries` gives the country shapes and `ne_10m_populated_places` the cities, alongside the main deck's basemap layers.
- **Borders view:** Natural Earth's default de facto view (`ne_10m_admin_0_countries` and `ne_10m_admin_0_boundary_lines_land`), not a point-of-view variant.

## Decided policy

### Disputed and partially recognised states: included

Under the default de facto view these are already rows in `ne_10m_admin_0_countries`, marked by their `TYPE` and `SOVEREIGNT` fields:

| Entity | Row | `TYPE` | Note |
|---|---|---|---|
| Taiwan | Taiwan | Sovereign country | Capital Taipei is an `Admin-0 capital`. |
| Kosovo | Kosovo | Disputed | Pristina is an `Admin-0 capital`. |
| Palestine | Palestine (`SOVEREIGNT` Israel) | Indeterminate | West Bank and Gaza. No capital row is tagged for it. The capital needs a decision (East Jerusalem as claimed, or Ramallah as the seat) and a hand-picked `populated_places` row. |
| Western Sahara | W. Sahara | Indeterminate | Only the zone east of the berm, about 90,000 km² of 266,000; the de facto view draws the rest inside Morocco. A whole-territory outline needs a point-of-view variant that draws it (not checked) or a hand-authored part. Bir Lehlou is an `Admin-0 capital alt`. |
| Northern Cyprus, Somaliland | own rows | Sovereign country | Present if wanted. Hargeisa is a capital row; North Nicosia needs checking. |
| Israel | Israel | Disputed | Jerusalem is the `Admin-0 capital`, Tel Aviv the `capital alt`. |

The de facto view resolves other disputes rather than showing them as their own areas:

- **Crimea** is drawn inside Russia, so Russia's outline includes it and Ukraine's doesn't.
- **Kashmir** is split along the Line of Control into India, Pakistan and China (Aksai Chin). Siachen is a separate `Indeterminate` row.
- **Abkhazia, South Ossetia, Transnistria** are not separate rows. Natural Earth draws them in `ne_10m_admin_0_disputed_areas` (dashed lines in `..._boundary_lines_disputed_areas`), which would need vendoring.

To draw a dispute differently, do one of:

- switch layers to a point-of-view variant (`ne_10m_admin_0_countries_ukr`, `_ind`, and so on);
- add the disputed-areas layer;
- subtract and add parts with the existing `geometry` selectors.

### Microstates and small island states: included

At the 2,600 km minimum frame, a country gets the small-area ring if it is smaller than a 66 px disc (about 9,000 km²) or under 100 px long. Of the 200 state rows (see [Replacing a country and capital deck](#replacing-a-country-and-capital-deck)), **38** get a ring. Rings carry them, as they already do for small features in the main deck.

- Andorra, Bahrain, Barbados, Brunei, Cabo Verde, Comoros, Cyprus, Dominica, Grenada, Kosovo, Liechtenstein, Luxembourg, Malta, Monaco, Nauru, Northern Cyprus, Palestine, Saint Lucia, San Marino, Singapore, São Tomé and Príncipe, St Kitts and Nevis, St Vincent and the Grenadines, Trinidad and Tobago, Vatican
- Scattered archipelagos, whose frame widens to hold every island: Antigua and Barbuda, Fiji, Kiribati (9,600 km frame), Maldives, Marshall Islands, Mauritius, Micronesia, Palau, Samoa, Seychelles, Tonga, Tuvalu, Vanuatu

France, the Netherlands, New Zealand and Norway are also ringed, but not once a `mainland` box drops their overseas parts. Kiribati, Micronesia and Tuvalu need a framing decision: the whole spread with a ring, or the main island group.

## Open questions

- **Major cities.** Recommendation: pick 80–150 cities for historical or economic significance, not population alone. Population-only picks fill the list with metropolitan areas nobody needs to place; significance keeps cities like Venice, Geneva, Jerusalem and Timbuktu.
- **Deck name.** The PoC uses "Geography PoC — Countries". A full build needs a permanent name before its first import, because renaming a deck doesn't carry over to existing cards.
- **Several capitals.** Bolivia (Sucre, La Paz), South Africa (Pretoria, Cape Town, Bloemfontein), the Netherlands (Amsterdam, The Hague) and a few more have more than one. Either one card answering all of them, or one dot per seat.
- **Country front framing.** Large countries with remote parts (France, the US, Norway, Chile's Easter Island) each need a `mainland` box, or a switch to `ne_10m_admin_0_map_units`, which splits most overseas parts into their own rows.

## Replacing a country and capital deck

A full replacement set needs:

- **Every sovereign state:** the 193 UN members, plus Vatican City.
- **Partially recognised and disputed states:** Palestine, Taiwan, Kosovo, Western Sahara, and optionally Northern Cyprus and Somaliland. That makes 200 rows in `ne_10m_admin_0_countries` under the default view. Abkhazia, South Ossetia and Transnistria would need the disputed-areas layer.
- **Their capitals:** `ne_10m_populated_places` has 202 `Admin-0 capital` and 13 `Admin-0 capital alt` rows, covering almost all of them. Palestine and Northern Cyprus need checking by hand.
- **Major cities,** as an optional layer: 80–150.
- **Optionally, dependencies and territories** (Greenland, Puerto Rico, Hong Kong, New Caledonia…): about 50 more rows, typed `Dependency`, or `Country` with a different `SOVEREIGNT`.

| Set | Notes |
|---|---|
| 200 states × (country + capital) | ~400 |
| + major cities | +80–150 |
| + ~50 dependencies × (country + capital), optional | +~100 |
| **Total** | **~480–550**, or ~580–650 with dependencies |

**Render time:** one map per card. At about 10 s per map and `JOBS=1`, 480–550 maps take 80–90 minutes, or about 1 h 45 min with dependencies. The PoC's 9 maps took 33 s in all, layer loading included (about 3.5 s each), so the real figure is likely lower. `poc.py` doesn't use the main render cache; a full build should go through `input_hash` and the cache so only changed maps re-render.

## Known limits of the PoC

- **Main-deck re-render.** The shared edits (`render.py`, `style.py`, `sources.lock`) change the main render cache key, so the first `make all` on this branch re-renders all 141 maps. It did, and every PNG came out byte-identical, so the main package is unchanged. Any later change to the PoC treatments in those files costs the same full re-render.
- **`make fetch` now pulls `ne_10m_populated_places`** (19 MB) for the main deck too.
- **No bbox across 180°.** `expect` and `mainland` here are plain boxes, unlike `features.yaml`. Fiji, Kiribati and Tuvalu would need the main deck's wrap-aware check.
