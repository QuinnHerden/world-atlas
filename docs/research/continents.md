# Continent polygons in Natural Earth: do they match a standard convention?

Prepared 2026-10-14 for the orientation block's 7 continent cards ([world-atlas-plan.md](../world-atlas-plan.md), open decision 4). Source keys follow the convention of [research-independent.md](research-independent.md): **[V]** means I opened the page and read the claim there; **[S]** means I confirmed it from search-indexed text only. **GEOM** means I computed it from the vendored data (scripts not committed; method given inline).

Data: `vendor/ne_10m_geography_regions_polys.geojson`, Natural Earth v5.1.2 as pinned in [architecture.md](../architecture.md). NE's download page lists this layer as version 5.0.0, so it appears unchanged since then (NE-LABELS [V]).

## Verdict

**The 7 `Continent` polygons can't be used as continent cards as they stand.** Each is the continental **mainland plus attached or near-shore islands**. Large islands are separate features (`Island`, `Island group`, `Isthmus`) that share the same `REGION` attribute. On their own, the polygons leave out Great Britain, Ireland, Iceland, Madagascar, New Guinea, New Zealand, Borneo, Sumatra, Java, the Philippines, the West Indies and **all of Central America**.

**The `REGION` attribute does follow a standard convention, but only through the landmass features.** Take the union of the polygons with a given `REGION` value **and** `FEATURECLA` in {`Continent`, `Island`, `Island group`, `Isthmus`}. That gives a near-complete continental partition. Its Europe/Asia line is the National Geographic convention: Urals, Ural River, Caspian, Caucasus, Black Sea, Turkish Straits (NG-MAP [V]). It departs from that convention in three ways (Sinai, Cyprus, mid-ocean islands; see [Deviations](#deviations-from-the-standard-convention)).

**Don't union every polygon of a `REGION` value.** Some `REGION == "Europe"` features lie inside ASIA:

| Feature | Overlap with ASIA (sq. degrees, GEOM) |
|---|---|
| `ANATOLIA` (Geoarea) | 77.2 |
| `URAL MOUNTAINS` | 11.3 |
| `CASPIAN DEPRESSION` | 10.1 |
| `CAUCASUS MTS.` | 7.1 |
| `PONTIC STEPPE` | 1.4 |
| `Absheron Pen.` | 0.14 |

The Africa-tagged `Negev Desert` also lies inside ASIA. Unioning everything would put Anatolia, Sochi and Baku in Europe. This was caught in fact-check.

**Overlaps remain even with the `FEATURECLA` filter:**
- `MOLUCCAS` (`Island group`, 1159104143, REGION Oceania) overlaps `MALAY ARCHIPELAGO` (REGION Asia), about 5.7 sq. degrees. **The Moluccas, Taliabu and Wetar would be on both the Asia and Oceania cards.** Drop `MOLUCCAS` from Oceania; M49 and the usual convention put them in Asia (Indonesia).
- The `AFRICA` and `ASIA` Continent rows overlap slightly (about 0.6 sq. degrees, near Sinai/Negev).
- The `EUROPE` and `ASIA` Continent rows overlap by about 0.3 sq. degrees along the shared line.
- Clip the two Continent-row overlaps by a fixed precedence, e.g. take the overlap away from the larger continent.

**NE has no polygon named Oceania.** The `AUSTRALIA` polygon is the Australian mainland and Tasmania only. An "Oceania" card needs the filtered union for `REGION == "Oceania"` (minus `MOLUCCAS`), or the four polygons listed under [Oceania](#oceania).

**Recommendation:** for each continent card, take the union of `REGION == <name>` restricted to those four `FEATURECLA` values, not the bare `Continent` row. Then:
- resolve the overlaps above;
- hand-assign the few `Seven seas (open ocean)` islands, or accept their absence (see [Gaps](#gaps)).

## The 7 Continent polygons

From `FEATURECLA == "Continent"` (GEOM).

| NAME | `NE_ID` | WIKIDATAID | REGION attr | Parts | Bounds (lon, lat) |
|---|---|---|---|---|---|
| AFRICA | 1159104365 | Q15 | Africa | 14 | −17.5…51.4, −34.8…37.3 |
| ANTARCTICA | 1159104367 | Q51 | Antarctica | 100 | −180…180, −90…−61.1 |
| ASIA | 1159104597 | Q48 | Asia | 188 | −180…180, 1.3…81.3 |
| AUSTRALIA | 1159104363 | Q3960 ("Australian continent") | Oceania (SUBREGION Australasia) | 41 | 112.9…153.6, −43.6…−10.1 |
| EUROPE | 1159104603 | Q46 | Europe | 128 | −9.5…66.4, 34.9…71.1 |
| NORTH AMERICA | 1159104607 | Q49 | North America | 271 | −178.2…179.8, 15.7…83.6 |
| SOUTH AMERICA | 1159104361 | Q18 | South America | 46 | −81.3…−34.9, −55.7…12.2 |

The Wikidata labels were resolved through the Wikidata API (WD-API [V]).

## Europe/Asia boundary

**What NE draws** (GEOM: the shared edge of EUROPE and ASIA, sampled by latitude and longitude):

- **Urals:** the crest at about 59–60°E from the Kara Sea (about 68.5°N, 66.3°E) south to about 52°N. Vorkuta, Perm and Ufa fall in Europe; Yekaterinburg falls in Asia.
- **Ural River:** from about 51.3°E, 51°N down to the Caspian at about 51.8°E, 47°N. Orenburg and Oral fall in Europe; Atyrau, at the mouth, falls in Asia.
- **Caspian Sea.**
- **Caucasus:** a near-straight generalised line from the Absheron peninsula (about 50.3°E, 40.4°N) to the Black Sea near Anapa (about 37.0°E, 45.0°N). It runs about 42.7°N at 44°E and about 43.4°N at 42°E, so it tracks the Greater Caucasus crest. Elbrus, Kazbek, Grozny, Makhachkala, Derbent, Quba and Sumqayit fall in Europe. Tbilisi, Baku, Yerevan, Sochi and Novorossiysk fall in Asia. Crimea, Kerch and Taman fall in Europe.
- **Black Sea, Bosporus, Sea of Marmara, Dardanelles, Aegean.** On the bare Continent rows, Istanbul's European side falls in EUROPE and Üsküdar in ASIA, both within about 0.03° of the coast.

**The standard conventions:**

| Convention | Line | Source |
|---|---|---|
| **National Geographic** ("commonly accepted division") | Urals, **Ural River**, Caspian, **Caucasus Mountains**, Black Sea, Bosporus and Dardanelles | NG-MAP [V] |
| Greater Caucasus watershed as the traditional line, though "the subject of much debate" | Caucasus segment only | BRIT-CAUCASUS [S] |
| **Britannica's Eurasia article** ("most geographers") | Urals, **Emba River**, Caspian, **Kuma–Manych Depression**, Sea of Azov, Kerch Strait. This puts the whole Caucasus isthmus in Asia. | BRIT-EURASIA [S] |

**Finding:** NE matches the National Geographic convention. It uses the Ural River, not the Emba, and the Caucasus crest, not the Kuma–Manych Depression. The two are tied in practice. Under the Britannica line, Elbrus is in Asia, so "Europe's highest peak" depends on which convention you pick. NG's Europe page calls Elbrus Europe's highest peak (NG-EUROPE [S]). **Use NE's line and say on the card back that the line is a convention.** Every source above calls it one.

**Caveat:** NE's Caucasus segment is a generalised straight line, not the true watershed, so places right on the crest are unreliable. At 10m/50m continent scale this doesn't show.

## Oceania

**What NE has:**

- `AUSTRALIA` (1159104363): the Australian mainland, Tasmania, Kangaroo Island and the Torres Strait islands. It **excludes** New Guinea, New Zealand and every Pacific island (GEOM: point tests at Port Moresby, Auckland, Wellington, Suva and Nouméa all fall outside every Continent polygon).
- Three `Island group` polygons with `REGION == "Oceania"`:

| NAME | `NE_ID` | WIKIDATAID | Covers (GEOM point tests) |
|---|---|---|---|
| MELANESIA | 1159104353 | Q37394 | New Guinea (**the whole island, including Indonesian Papua**), Bismarck Archipelago, Bougainville, Solomons, Vanuatu, New Caledonia, Fiji, Norfolk |
| MICRONESIA | 1159104355 | Q3359409 | Palau, Guam and the Marianas, FSM, Marshalls, Nauru, Kiribati (Gilberts) |
| POLYNESIA | 1159104359 | Q35942 | **New Zealand** (North and South Islands; NE also has a `NEW ZEALAND` island-group row, 1159104631), Samoa, Tonga, Tahiti, **Hawaii**, **Easter Island** |

**The conventions:**

- **National Geographic** counts 7 continents, with "Australia" the seventh. Oceania "is considered a region, associated with Australia, rather than a continent" (NG-MAP [V]). Its education encyclopedia adds that the continent "is sometimes called Oceania, to include the thousands of tiny islands of the Central and South Pacific" (NG-CONT [V]).
- **UN M49** (statistical, country-level) defines Oceania (009) as four subregions. **Australia and New Zealand** covers Australia, NZ, Norfolk, Christmas, Cocos and Heard/McDonald. **Melanesia** covers Fiji, New Caledonia, PNG, Solomons and Vanuatu. **Micronesia** covers Guam, Kiribati, the Marshalls, FSM, Nauru, the N. Marianas, Palau and the US Minor Outlying Islands. **Polynesia** covers American Samoa, the Cook Islands, French Polynesia, Niue, Pitcairn, Samoa, Tokelau, Tonga, Tuvalu, and Wallis and Futuna. Indonesia, including Papua, is in South-eastern Asia, and the US (Hawaii) is in Northern America (UN-M49 [V]).
- **Britannica:** Oceania is the collective name for the islands of most of the Pacific. Whether it includes Australia, and its exact scope, vary by usage; the most popular usage leaves out Indonesia, Taiwan, the Philippines and Japan (BRIT-OCEANIA [S]).

**Finding:** the user's "Oceania" (Australia plus NZ plus the Pacific islands) is a standard convention, and M49 uses it, but it is **not what NE's continent row is**. To build it:

- **Recommended:** the union of `REGION == "Oceania"` polygons restricted to `FEATURECLA` in {Continent, Island, Island group, Isthmus}, minus `MOLUCCAS` (1159104143). This adds about 10 small pieces that the four-polygon union misses: Rowley Shoals, the Whitsundays, the Auckland Islands, parts of the Chatham Islands, Sala y Gómez and antimeridian slivers of Fiji (GEOM).
- **Alternative:** AUSTRALIA ∪ MELANESIA ∪ MICRONESIA ∪ POLYNESIA (1159104363, 1159104353, 1159104355, 1159104359).

**Three places where NE and M49 disagree on the Oceania edge. Decide each one:**

1. **Indonesian Papua (western New Guinea):** NE puts it in Oceania (Melanesia); M49 puts it in Asia. Geographically New Guinea is on the Australian continental shelf, so NE's choice is defensible for a physical card. Recommend keeping it.
2. **Hawaii:** NE puts it in Oceania (Polynesia); M49 puts it in Northern America. The ring puts the USA in region 19. Recommend including it (physical Polynesia). The card shows land, not sovereignty.
3. **Easter Island:** NE puts it in Oceania; Chile is in South America. Same reasoning: include it.

Also outside NE's Oceania: **Lord Howe Island and Macquarie Island** are in no region polygon (GEOM). **Christmas and Cocos Islands** are M49 Oceania, but NE has no region polygon for them. Both are invisible at continent scale.

## Deviations from the standard convention

| Issue | NE | National Geographic / usual convention | Impact |
|---|---|---|---|
| **Sinai** | **Africa** (`AFRICA`'s edge with `ASIA` runs along the Egypt–Israel border: 34.25–35.27°E, 29.5–31.4°N) | Africa joins Asia at the **Isthmus of Suez** (NG-CONT [V]). Sinai is conventionally Asian. | Visible at continent scale. **Fix:** clip AFRICA at the Suez Canal and move Sinai to Asia, or note it on the back. |
| **Cyprus** | Asia | NG: "Cyprus marks the southeastern extent of Europe" (NG-MAP [V]). M49 puts it in Western Asia (UN-M49 [V]). | The conventions disagree; NE follows the geographic one. Keep it, and note it on the back. |
| **North/South America seam** | `CENTRAL AMERICA` (`Isthmus`, 1159104347, REGION North America) is a separate polygon. The `NORTH AMERICA` Continent row stops at the Isthmus of Tehuantepec (about 95°W). Panama is North America, and the seam is near the Panama–Colombia border. | NG: the continents are connected by the Isthmus of Panama (NG-CONT [V]). The usual convention puts the seam at the Panama–Colombia border. | Matches the convention, but only through the REGION union. The bare `NORTH AMERICA` row is wrong for a card. |
| **Trinidad** | North America (West Indies) | Usually counted as Caribbean, so North America | Matches |
| **Greenland** | North America | Geographically North America | Matches |
| **Iceland, Svalbard, Malta, Crimea** | Europe | Europe | Matches |
| **Madagascar, Zanzibar, Canaries** | Africa | Africa | Matches |
| **Socotra, Bahrain, Sri Lanka, Japan, Taiwan** | Asia | Asia | Matches |
| **Falklands, Galápagos, Tierra del Fuego** | South America | South America | Matches |

## Gaps

These are islands that no continent's filtered REGION union covers, because NE tags them `Seven seas (open ocean)` (GEOM). None changes a continent's silhouette at the plan's continent-card scale. List them on the back or ignore them.

- **Indian Ocean:** Maldives, Laccadives, Chagos, Andaman and Nicobar Islands, Mascarenes (Mauritius, Réunion), Seychelles, Kerguelen, Crozet, Heard, Prince Edward Is.
- **Atlantic:** Azores, South Georgia, South Sandwich and South Orkney Islands.
- **Pacific off the Americas:** Revillagigedo, Juan Fernández, Desventuradas.
- **No landmass polygon at all** (GEOM; land pieces of 400–1,000 km² from `ne_10m_land` that are less than 50% covered):
  - Bermuda, Cocos (Keeling), Lord Howe and Macquarie;
  - Coiba (Panama), Cozumel (Mexico) and Santa Catarina Island (Brazil);
  - islands in the Amazon mouth, near Marajó;
  - Orinoco delta land;
  - Isla de los Estados;
  - some southern Chilean archipelago islands, which are only partly covered.

The Andamans and Nicobars (India) and the Maldives are the only ones a learner might notice missing from Asia. Mauritius and the Seychelles might be noticed missing from Africa.

## Sources

- **NE-LABELS** [V]: Natural Earth, "1:10m Physical Vectors: Label Areas" download page (version 5.0.0; "boundaries of physical regions should be taken with a grain of salt… roughly accurate to 50m scale"). https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-physical-labels/
- **NG-MAP** [V]: National Geographic Society, "National Geographic Map Policy" (Europe/Asia division; seven continents; Oceania as a region; Cyprus). https://www.nationalgeographic.org/society/national-geographic-map-policy/
- **NG-CONT** [V]: National Geographic Education, "Continent" (encyclopedic entry; Isthmus of Suez; Isthmus of Panama; "sometimes called Oceania"). https://education.nationalgeographic.org/resource/Continent/. Read through a summarising fetch, so re-read the exact wording before quoting it on a card.
- **NG-EUROPE** [S]: National Geographic Education, "Europe: Physical Geography" (Elbrus as Europe's highest peak). https://education.nationalgeographic.org/resource/europe-physical-geography/
- **UN-M49** [V]: UN Statistics Division, *Standard country or area codes for statistical use (M49)*, Oceania (009) and subregions. https://unstats.un.org/unsd/methodology/m49/
- **BRIT-EURASIA** [S]: Encyclopaedia Britannica, "Eurasia" (Urals, Emba, Kuma–Manych, Kerch line). https://www.britannica.com/place/Eurasia. britannica.com returned 403.
- **BRIT-CAUCASUS** [S]: Encyclopaedia Britannica, "Caucasus" (watershed as traditional line; debated). https://www.britannica.com/place/Caucasus
- **BRIT-OCEANIA** [S]: Encyclopaedia Britannica, "What does the term Oceania refer to?" https://www.britannica.com/question/What-does-the-term-Oceania-refer-to
- **WD-API** [V]: Wikidata API `wbgetentities` lookups of each WIKIDATAID label, 2026-10-14. https://www.wikidata.org/w/api.php
