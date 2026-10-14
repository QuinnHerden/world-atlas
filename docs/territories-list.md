# World Atlas: territories and disputed areas

## Decisions (2026-10-14)

- **Dependencies:** the 23 recommended **include** territories in List 1 get cards. The 29 **exclude** territories are intentionally excluded and kept on file to revisit later.
- **Disputed territories:** the 15 recommended **card** entries in List 2 get cards. The 16 **no card** entries are intentionally excluded and kept on file to revisit.
- **Border view:** country cards use internationally recognised borders. Disputed areas get their own cards with their own outlines.

Every excluded entry, with its reason, is gathered in [Intentionally excluded (revisit list)](#intentionally-excluded-revisit-list) at the end of this doc. The full tables below are unchanged.

---

**Summary** (checked 2026-10-14)

1. **Counts:** List 1 has 52 inhabited dependent or autonomous territories: **23 include**, 29 exclude. 13 of the 52 are integral parts of their state. A further 9 uninhabited entries (US Minor Outlying Islands counted as one) are listed in one line. List 2 has 31 disputed or occupied areas: **15 card**, 16 no card.
2. **Include (23):** Greenland, Faroe Islands, Svalbard, Hong Kong, Macau, Puerto Rico, Guam, Gibraltar, Falkland Islands, Bermuda, Cayman Islands, British Indian Ocean Territory, Isle of Man, Jersey, Guernsey, New Caledonia, French Polynesia, French Guiana, Réunion, Guadeloupe, Martinique, Aruba, Curaçao.
3. **Card (15):** Crimea, Kashmir (Indian-administered), Kashmir (Pakistani-administered), Aksai Chin (Chinese-administered, with Shaksgam), Arunachal Pradesh, Western Sahara, Golan Heights, Abkhazia, South Ossetia, Transnistria, Northern Cyprus, Somaliland, Kuril Islands (southern four), Spratly Islands, Essequibo.
4. **NE polygon gaps:** The French overseas departments, Caribbean Netherlands, Svalbard, Åland, Tokelau, Christmas Island and Cocos have no row of their own in the vendored `admin_0_countries`; they need `ne_10m_admin_0_map_units` (not vendored). The Canary Islands have no polygon in either layer. Every List 2 card except Northern Cyprus, Somaliland and Spratly needs `ne_10m_admin_0_disputed_areas` (not vendored). NE has no polygon at all for the post-2022 occupation of Ukraine. Its Donetsk and Luhansk shapes are the 2014–22 lines, its Artsakh shape is stale since 2023, and its Hans Island note has been stale since 2022.
5. **Verify (time-sensitive):** the Chagos handover (the treaty was not ratified and shelved as of May 2026), New Caledonia's Bougival status, US–Greenland talks, Somaliland recognition (only Israel so far), the Ukraine front and any deal, the ICJ Essequibo judgment (expected Nov 2026 to Jan 2027), Western Sahara after UNSC resolution 2797 (Oct 2025), and Israel's post-2024 zone beyond the Golan.

---

## Sources and method

- **Natural Earth v5.1.2**, commit `f1890d9f` (as pinned in `data/sources.lock`). `vendor/ne_10m_admin_0_countries.geojson` was read field by field (`TYPE`, `SOVEREIGNT`, `ADMIN`, `NOTE_ADM0`, `NOTE_BRK`). For checking only, `ne_10m_admin_0_disputed_areas` and `ne_10m_admin_0_map_units` were fetched at the same commit into a scratch directory; they are **not vendored**. Location tests used point-in-polygon checks. The areas quoted from NE were measured on NE's generalised polygons (LAEA), so treat them as approximate.
- **CIA World Factbook.** The CIA discontinued it on 2026-02-04, and cia.gov no longer serves the Dependencies page. I used the community mirror `factbook/factbook.json`, commit `144d6977`, whose last data update is 2026-01-22 (pre-retirement). Area, population and capital for every Factbook entity come from there. It is a scraped copy, not the CIA's own release: **verify** any figure you publish against an archived cia.gov copy.
- **UN M49** (unstats.un.org/unsd/methodology/m49). This was used to confirm which non-sovereign areas carry their own M49 code: Greenland, Hong Kong, Réunion, French Guiana, Guadeloupe, Martinique, Mayotte, Svalbard and Jan Mayen, Bonaire/Sint Eustatius/Saba, Tokelau, Åland, Western Sahara and others. Canary Islands, Azores, Madeira, Ceuta and Melilla have none.
- **Britannica:** not consulted row by row. This is a gap. Spot-check the List 2 dispute summaries there before you write card backs.
- **Figures not in the Factbook** (French departments, Caribbean Netherlands, Åland, Spanish and Portuguese regions) are approximate and from memory. They are marked † and must be checked against INSEE, CBS, ÅSUB, INE or INE-PT before use.
- NE `POP_EST` values are mostly 2019 and were not used.

**NE representation codes** (used in both tables):
- `A0:<TYPE>`: own row in `admin_0_countries` with that `TYPE`.
- `in <X>`: drawn inside X's polygon in admin_0.
- `MU`: own row in `admin_0_map_units`.
- `DA:<TYPE>`: own row in `admin_0_disputed_areas`.

---

## List 1: Dependent and autonomous territories (inhabited)

**Selection rule for integral parts:** a territory that is legally part of its state gets a row only if it has its own UN M49 code and its own NE map unit. That rule covers the French overseas departments, Caribbean Netherlands, Svalbard and Åland. It excludes the Canaries, Azores, Madeira, Ceuta and Melilla, which are listed below for completeness and marked exclude.

| Territory | Sovereign | Capital / main town | Area (km²) | Population (approx.) | NE representation | Rec. | Reason (≤12 words) |
|---|---|---|---|---|---|---|---|
| Greenland | Denmark | Nuuk | 2,166,086 | 57,800 | `A0:Country` (SOV Denmark) | **include** | World's largest island; Arctic strategy; US interest (verify) |
| Faroe Islands | Denmark | Tórshavn | 1,393 | 52,900 | `A0:Dependency` | **include** | Self-governing North Atlantic nation; commonly mapped separately |
| Svalbard ‡ | Norway | Longyearbyen | 62,045 | 2,600 | `in Norway`; `MU:Dependency` | **include** | Large Arctic archipelago; 1920 treaty regime; strategic |
| Åland ‡ | Finland | Mariehamn | 1,580 land † | 30,500 † | `A0:Country` (SOV Finland) | exclude | Small autonomous region; low learner salience |
| Hong Kong | China | — (SAR; no capital) | 1,108 | 7,306,000 | `A0:Country` (SOV China) | **include** | Global city; major political news |
| Macau | China | — (SAR; no capital) | 28 | 644,000 | `A0:Country` (SOV China) | **include** | Distinct SAR; former Portuguese colony; well known |
| Puerto Rico | USA | San Juan | 9,104 | 2,985,000 | `A0:Dependency` | **include** | Largest US territory; ~3M people |
| Guam | USA | Hagåtña | 544 | 169,500 | `A0:Dependency` | **include** | Key Pacific military hub; frequent news |
| Northern Mariana Islands | USA | Saipan | 464 | 51,100 | `A0:Dependency` | exclude | Small; overshadowed by neighbouring Guam |
| American Samoa | USA | Pago Pago | 224 | 43,300 | `A0:Dependency` | exclude | Small, remote; low salience |
| US Virgin Islands | USA | Charlotte Amalie | 346 land (1,910 incl. water) | 103,800 | `A0:Dependency` | exclude | Small Caribbean islands; low geographic weight |
| Gibraltar | UK | Gibraltar | 7 | 29,700 | `A0:Disputed` (Spain claim) | **include** | Strait of Gibraltar choke point; Spanish claim |
| Falkland Islands | UK | Stanley | 12,173 | 3,100 | `A0:Disputed` (Argentina claim) | **include** | 1982 war; enduring Argentine claim |
| Bermuda | UK | Hamilton | 54 | 72,800 | `A0:Dependency` | **include** | Oldest UK overseas territory; well-known name |
| Cayman Islands | UK | George Town | 264 | 66,700 | `A0:Dependency` | **include** | Globally known offshore financial centre |
| British Virgin Islands | UK | Road Town | 151 | 40,100 | `A0:Dependency` | exclude | Small; confusable with US Virgin Islands |
| Turks and Caicos Islands | UK | Cockburn Town | 948 | 60,400 | `A0:Dependency` | exclude | Small Caribbean territory; low salience |
| Anguilla | UK | The Valley | 91 | 19,400 | `A0:Dependency` | exclude | Small, obscure |
| Montserrat | UK | Plymouth (de jure, abandoned); Brades (de facto) | 102 | 5,500 | `A0:Dependency` | exclude | Small; tricky capital adds noise |
| Saint Helena, Ascension and Tristan da Cunha | UK | Jamestown | 394 | 7,900 | `A0:Dependency` (one row, all three) | exclude | Remote, tiny population; three scattered island groups |
| Pitcairn Islands | UK | Adamstown | 47 | 50 | `A0:Dependency` | exclude | ~50 people; Bounty trivia only |
| British Indian Ocean Territory | UK | — (Diego Garcia base) | 60 | ~3,000 military/contractors; no permanent residents | `A0:Disputed` (Mauritius claim); `DA` has Diego Garcia overlay | **include** | Diego Garcia base; Chagos sovereignty transfer pending (verify) |
| Akrotiri and Dhekelia | UK | Episkopi Cantonment | 254 | ~18,000 incl. Cypriots (2020) | `A0:Dependency` (two rows) | exclude | Military base areas; too small to read on map |
| Isle of Man | UK (Crown dependency) | Douglas | 572 | 92,700 | `A0:Country` (SOV UK) | **include** | Crown dependency; central Irish Sea; commonly mapped |
| Jersey | UK (Crown dependency) | Saint Helier | 116 | 103,900 | `A0:Country` (SOV UK) | **include** | Largest Channel Island; crown dependency; finance |
| Guernsey | UK (Crown dependency) | Saint Peter Port | 78 | 67,900 | `A0:Country` (SOV UK) | **include** | Pairs with Jersey; Channel Islands set |
| New Caledonia | France | Nouméa | 18,575 | 307,600 | `A0:Dependency` | **include** | Large; nickel; independence votes, 2024 unrest (verify) |
| French Polynesia | France | Papeete | 4,167 | 305,500 | `A0:Dependency` | **include** | Tahiti; vast Pacific spread; well known |
| Wallis and Futuna | France | Mata-Utu | 142 | 16,000 | `A0:Dependency` | exclude | Small, obscure |
| Saint Pierre and Miquelon | France | Saint-Pierre | 242 | 5,100 | `A0:Dependency` | exclude | Tiny; curiosity only |
| Saint Barthélemy | France | Gustavia | 25 | 7,100 | `A0:Dependency` | exclude | Tiny; unreadable at country scale |
| Saint Martin (French part) | France | Marigot | 50 | 33,100 | `A0:Dependency` | exclude | Half an island; tiny |
| French Guiana ‡ | France | Cayenne | 83,534 † | ~295,000 † | `in France`; `MU:Geo unit` | **include** | Only EU land in South America; spaceport |
| Réunion ‡ | France | Saint-Denis | 2,512 † | ~890,000 † | `in France`; `MU:Geo unit` | **include** | Most populous overseas department; Indian Ocean |
| Guadeloupe ‡ | France | Basse-Terre | 1,628 † | ~375,000 † | `in France`; `MU:Geo unit` | **include** | Populous Caribbean department; well known |
| Martinique ‡ | France | Fort-de-France | 1,128 † | ~345,000 † | `in France`; `MU:Geo unit` | **include** | Populous Caribbean department; Mont Pelée |
| Mayotte ‡ | France | Mamoudzou | 374 † | ~320,000 † (contested estimate) | `in France`; `MU:Disputed`; `DA:Disputed` (Comoros claim) | exclude | Small; low learner salience; Comoros claim |
| Aruba | Netherlands | Oranjestad | 180 | 125,100 | `A0:Country` (SOV Netherlands) | **include** | Constituent country of Kingdom; commonly mapped |
| Curaçao | Netherlands | Willemstad | 444 | 153,300 | `A0:Country` (SOV Netherlands) | **include** | Largest Dutch Caribbean island; constituent country |
| Sint Maarten | Netherlands | Philipsburg | 34 | 46,700 | `A0:Country` (SOV Netherlands) | exclude | Half an island; tiny |
| Caribbean Netherlands (Bonaire, Sint Eustatius, Saba) ‡ | Netherlands | Kralendijk | 322 † | ~32,000 † | `in Netherlands`; `MU:Geo unit` | exclude | Three scattered small islands; municipalities of Netherlands |
| Norfolk Island | Australia | Kingston | 36 | 1,700 | `A0:Dependency` | exclude | Tiny, remote |
| Christmas Island | Australia | Flying Fish Cove | 135 | 1,700 | `A0:Dependency` "Indian Ocean Ter." (merged with Cocos); `MU:Geo unit` | exclude | Tiny; NE merges it with Cocos |
| Cocos (Keeling) Islands | Australia | West Island | 14 | 600 | as Christmas Island | exclude | Tiny atolls |
| Cook Islands | New Zealand (free association) | Avarua | 236 | 7,600 | `A0:Dependency` | exclude | Small; association status nuanced for a card |
| Niue | New Zealand (free association) | Alofi | 260 | 1,800 | `A0:Dependency` | exclude | Tiny population |
| Tokelau | New Zealand | — (rotates among Atafu, Nukunonu, Fakaofo) | 12 | 2,500 | `in New Zealand`; `MU:Geo unit` | exclude | Tiny atolls; no capital |
| Canary Islands ‡ | Spain | Santa Cruz de Tenerife / Las Palmas (shared) | 7,447 † | ~2,250,000 † | `in Spain`; not in MU | exclude | Integral Spanish region; no M49 code or NE unit |
| Ceuta ‡ | Spain | Ceuta | 18.5 † | ~83,000 † | `in Spain`; `DA:Geo subunit` | exclude | Integral Spanish city; Moroccan claim; tiny |
| Melilla ‡ | Spain | Melilla | 12.3 † | ~85,000 † | `in Spain`; `DA:Geo subunit` | exclude | Integral Spanish city; Moroccan claim; tiny |
| Azores ‡ | Portugal | Ponta Delgada | 2,322 † | ~240,000 † | `in Portugal`; `MU:Geo unit` | exclude | Integral Portuguese region; no M49 code |
| Madeira ‡ | Portugal | Funchal | 801 † | ~255,000 † | `in Portugal`; `MU:Geo unit` | exclude | Integral Portuguese region; no M49 code |

‡ Integral part of its state, not a dependency.

† Not in the Factbook; approximate, **verify**.

**Counts:** 52 rows, **23 include**, 29 exclude.

### Integral parts, and whether they still get a card

- **French overseas departments and regions** (French Guiana, Réunion, Guadeloupe, Martinique, Mayotte) are legally France and part of the EU. **Yes, give cards** to the first four. Each has its own M49 and ISO code and its own NE map unit, learners treat them as places on the map, and France's country card will crop them out (PoC `mainland` box). Mayotte is excluded on salience, not status. Card back: "Overseas department of France (part of France)."
- **Caribbean Netherlands** consists of special municipalities of the Netherlands proper. Excluded on size, not status.
- **Svalbard** is part of the Kingdom of Norway under the Svalbard Treaty (1920), with treaty-guaranteed access for other parties. The Factbook nonetheless lists it as a Norwegian dependency. **Card yes.**
- **Åland** is an autonomous, demilitarised region of Finland. NE gives it its own admin_0 row. Excluded on salience.
- **Greenland and the Faroe Islands** are self-governing parts of the Kingdom of Denmark. The Factbook types them as "part of the Kingdom of Denmark", not as dependencies. **Cards yes.**
- **Hong Kong and Macau** are SARs and integral parts of the PRC. **Cards yes.** Neither has a capital, so the capital card needs special handling: skip it, or prompt for the city/SAR itself.
- **Canary Islands, Azores, Madeira, Ceuta, Melilla:** integral regions with no M49 code and, for the Canaries, no NE polygon. **No card.**
- **Not considered as territories:** autonomous regions inside sovereign states that are not mapped as separate units: Bougainville (PNG; independence targeted for 2027, verify), Zanzibar, Iraqi Kurdistan, Galápagos, Easter Island, Socotra.

**Uninhabited (not tabled):** Bouvet Island, Heard I. and McDonald Is., French Southern and Antarctic Lands, Clipperton I., South Georgia and the South Sandwich Is., Jan Mayen, Ashmore and Cartier Is., Coral Sea Is., and the US Minor Outlying Islands (Wake, Midway, Johnston, Baker, Howland, Jarvis, Kingman Reef, Palmyra, Navassa). Most have staff only.

---

## List 2: Disputed and occupied territories

Country cards use internationally recognised borders. NE's default admin_0 layer is **de facto**: it draws Crimea in Russia, the Golan in Israel, Kashmir split along the LoC/LAC, and the Kurils in Russia. Recognised-border outlines therefore need `disputed_areas` parts added or subtracted, or a point-of-view layer such as `_ukr` or `_ind`.

| Territory | Parties | Current control | NE representation | Importance | Rec. |
|---|---|---|---|---|---|
| Crimea | Ukraine vs Russia | Russia since 2014 (annexed; not recognised) | `in Russia`; `DA:Disputed` "Crimea" (~27,100 km²) | High | **card**: largest annexation in Europe since 1945; stable outline |
| Russian-occupied Donetsk, Luhansk, Zaporizhzhia, Kherson | Ukraine vs Russia | Mostly Russia since 2022; front still moving (**verify**) | `in Ukraine`; `DA:Breakaway` DPR (~9,450 km²) and LPR (~8,300 km²) at **2014–22 lines only**; nothing for Zaporizhzhia or Kherson | High | **no card**: control line unstable and NE lacks it. Revisit if a line freezes, or use oblast outlines from admin_1 (not vendored) |
| Kashmir: Indian-administered (J&K + Ladakh) | India vs Pakistan (China claims parts of Ladakh) | India | `in India`; `DA:Disputed` "Jammu and Kashmir" (~104,500 km², includes Ladakh); Siachen separate `A0:Indeterminate` | High | **card**: core of an enduring nuclear-armed dispute |
| Kashmir: Pakistani-administered (Azad Kashmir + Gilgit-Baltistan) | Pakistan vs India | Pakistan | `in Pakistan`; `DA:Disputed` "Azad Kashmir" (~12,000) + "Gilgit-Baltistan" (~65,200) | High | **card**: other half of the LoC; merge both polygons |
| Aksai Chin (Chinese-administered Kashmir, with Shaksgam) | China vs India | China since 1950s; 1962 war | `in China`; `DA:Disputed` "Aksai Chin" (~31,000) + "Shaksam Valley" (~5,300) | High | **card**: third Kashmir part; LAC flashpoint (2020 clashes) |
| Arunachal Pradesh | India vs China ("Zangnan") | India | `in India`; `DA:Disputed` (~68,000 km²) | High | **card**: large, enduring Chinese claim; mappable state outline |
| Western Sahara | Morocco vs Polisario/SADR | Morocco ~2/3 west of berm; Polisario east | `A0:Indeterminate` ESH = **only east of berm** (~90,500); `DA` has both parts (Morocco-administered ~177,800 + SADR ~90,500) | High | **card**: whole-territory outline from both DA parts. UNSC 2797 (Oct 2025) backs autonomy plan (**verify**) |
| Golan Heights | Syria vs Israel | Israel since 1967 (annexed 1981; US recognised 2019) | `in Israel`; `DA:Indeterminate` (~1,200 km²) + UNDOF Zone overlay | High | **card**: enduring; Israeli presence beyond line since Dec 2024 (**verify**) |
| Abkhazia | Georgia vs Abkhaz authorities / Russia | Russian-backed separatists since 1993 | `in Georgia`; `DA:Breakaway` (~8,600 km²) | Medium-high | **card**: 2008 war; recognised by Russia; stable outline |
| South Ossetia | Georgia vs separatists / Russia | Russian-backed separatists | `in Georgia`; `DA:Breakaway` (~4,500 km²) | Medium-high | **card**: 2008 war trigger; stable outline |
| Transnistria | Moldova vs separatists | Separatists; Russian troops present | `in Moldova`; `DA:Breakaway` (~3,050 km²) | Medium | **card**: frozen conflict; Russian troops; stable outline |
| Northern Cyprus | Cyprus vs TRNC / Turkey | TRNC since 1974 (recognised only by Turkey) | `A0:Sovereign country` (own row) + `DA:Disputed` (~3,300 km²); UN buffer zone `A0:Indeterminate` | High | **card**: divides an EU member; enduring since 1974 |
| Somaliland | Somalia vs Somaliland | Somaliland (Hargeisa); SSC-Khatumo holds Las Anod area since 2023 | `A0:Sovereign country` (own row, ~167,400 km², **includes Las Anod**) | Medium-high | **card**: de facto state since 1991; recognised by Israel Dec 2025 only (**verify**) |
| Kuril Islands (Iturup, Kunashir, Shikotan, Habomai) | Japan vs Russia | Russia since 1945 | `in Russia`; `DA:Disputed` "Kuril Is." (~5,000 km²) | Medium-high | **card**: blocks a Japan–Russia peace treaty; clear outline |
| Spratly Islands | China, Taiwan, Vietnam, Philippines, Malaysia, Brunei | Split; features held by five claimants | `A0:Indeterminate` own row (~13 km² of features) | High | **card**: centre of South China Sea dispute; ring-highlighted |
| Essequibo (Guayana Esequiba) | Venezuela vs Guyana | Guyana | `in Guyana`; `DA:Disputed` "West of Essequibo River" (~142,400 km²) | High | **card**: ~2/3 of Guyana; ICJ judgment pending (**verify**) |
| Senkaku / Diaoyu Islands | Japan vs China, Taiwan | Japan | `in Japan`; `DA:Disputed` "Pinnacle Is." (~5 km²) | Medium-high | **no card**: specks too small to outline; mention on Japan/China backs |
| Paracel Islands | China vs Vietnam, Taiwan | China since 1974 | `in China`; `DA:Geo unit` (~6 km²) | Medium | **no card**: tiny; Spratlys card covers the theme |
| Scarborough Shoal | China vs Philippines, Taiwan | China (de facto since 2012) | `A0:Indeterminate` own row | Medium | **no card**: reef, no land outline |
| Falkland Islands claim | Argentina vs UK | UK | `A0:Disputed` | Medium | **no card**: covered by Falklands territory card (List 1) |
| Gibraltar claim | Spain vs UK | UK | `A0:Disputed` | Low-medium | **no card**: covered by Gibraltar territory card |
| Chagos Archipelago (BIOT) | Mauritius vs UK | UK; treaty signed May 2025, ratification shelved (**verify**) | `A0:Disputed`; `DA:Disputed` | Medium | **no card**: covered by BIOT territory card; status in flux |
| Nagorno-Karabakh | Azerbaijan vs Armenian separatists | Azerbaijan since Sept 2023 offensive; the de facto republic formally dissolved 1 Jan 2024 | `in Azerbaijan`; `DA:Breakaway` "Artsakh" (~3,100 km², **stale**) | Historical | **no card**: dispute resolved by force; no longer contested territory |
| Siachen Glacier | India vs Pakistan | India since 1984 | `A0:Indeterminate` own row (~2,100 km²) | Medium | **no card**: fold into Indian-administered Kashmir card |
| Kalapani–Lipulekh | Nepal vs India | India | `in India`; `DA:Disputed` "Near Om Parvat" | Low | **no card**: small, minor |
| Abyei | Sudan vs South Sudan | Joint/UN (UNISFA) | `in Sudan`; `DA:Disputed` | Low-medium | **no card**: small, low salience |
| Hala'ib Triangle | Egypt vs Sudan | Egypt | `in Egypt`; `DA:Disputed` | Low | **no card**: low salience |
| Ilemi Triangle | Kenya vs South Sudan | Kenya | `in Kenya`; `DA:Disputed` | Low | **no card**: low salience |
| Dokdo / Takeshima | South Korea vs Japan | South Korea | `DA:Geo subunit` (speck) | Low-medium | **no card**: too small to map |
| Ceuta and Melilla | Spain vs Morocco claim | Spain | `DA:Geo subunit` (no claim note in NE) | Low | **no card**: dormant claim; tiny |
| Hans Island | Canada and Denmark | Split by 2022 agreement | `DA:Disputed` "claimed by Canada" (**stale**) | Resolved | **no card**: dispute resolved June 2022 |

**Counts:** 31 rows, **15 card**, 16 no card.

**Handled elsewhere, not here:** Taiwan, Kosovo and Palestine (including Gaza, the West Bank and East Jerusalem) get country cards per the PoC policy. Western Sahara could get both a country card and a dispute card. Pick one; I recommend the dispute card only, since its sovereignty is the question.

### Data gaps for the 15 cards

- **Not vendored:** 12 cards need `ne_10m_admin_0_disputed_areas.geojson` (701 KB at commit `f1890d9f`). Northern Cyprus, Somaliland and Spratly need it too only if you use the disputed-areas shapes rather than their admin_0 rows.
- **Somaliland:** NE's polygon includes the Las Anod / SSC-Khatumo area that Somaliland lost in 2023. Flag this on the back or trim the shape.
- **Western Sahara:** the admin_0 row alone is the east-of-berm strip. Union both DA parts.
- **Recognised-border country outlines:** to show Ukraine with Crimea, Georgia with Abkhazia and South Ossetia, and so on, you have to add DA parts back. Otherwise the de facto admin_0 shapes contradict the "recognised borders" rule.

---

## Intentionally excluded (revisit list)

Excluded by decision on 2026-10-14 and kept on file to revisit: 29 dependencies (List 1 "exclude"), 16 disputed areas (List 2 "no card") and 9 uninhabited territories. Reasons for dependencies and disputed areas are as given in the tables above; the uninhabited entries are not tabled there. Ceuta and Melilla appear twice: as integral Spanish cities in List 1 and as Morocco's claim in List 2.

| Territory | Source | Sovereign / parties | Reason |
|---|---|---|---|
| Abyei | Disputed (List 2) | Sudan vs South Sudan | Small, low salience |
| Akrotiri and Dhekelia | Dependency (List 1) | UK | Military base areas; too small to read on map |
| Åland | Dependency (List 1) | Finland | Small autonomous region; low learner salience |
| American Samoa | Dependency (List 1) | USA | Small, remote; low salience |
| Anguilla | Dependency (List 1) | UK | Small, obscure |
| Ashmore and Cartier Islands | Uninhabited | Australia | Uninhabited; no permanent population (staff at most) |
| Azores | Dependency (List 1) | Portugal | Integral Portuguese region; no M49 code |
| Bouvet Island | Uninhabited | Norway | Uninhabited; no permanent population (staff at most) |
| British Virgin Islands | Dependency (List 1) | UK | Small; confusable with US Virgin Islands |
| Canary Islands | Dependency (List 1) | Spain | Integral Spanish region; no M49 code or NE unit |
| Caribbean Netherlands (Bonaire, Sint Eustatius, Saba) | Dependency (List 1) | Netherlands | Three scattered small islands; municipalities of Netherlands |
| Ceuta | Dependency (List 1) | Spain | Integral Spanish city; Moroccan claim; tiny |
| Ceuta and Melilla claim | Disputed (List 2) | Spain vs Morocco | Dormant claim; tiny |
| Chagos Archipelago (BIOT) claim | Disputed (List 2) | Mauritius vs UK | Covered by BIOT territory card; status in flux |
| Christmas Island | Dependency (List 1) | Australia | Tiny; NE merges it with Cocos |
| Clipperton Island | Uninhabited | France | Uninhabited; no permanent population (staff at most) |
| Cocos (Keeling) Islands | Dependency (List 1) | Australia | Tiny atolls |
| Cook Islands | Dependency (List 1) | New Zealand | Small; association status nuanced for a card |
| Coral Sea Islands | Uninhabited | Australia | Uninhabited; no permanent population (staff at most) |
| Dokdo / Takeshima | Disputed (List 2) | South Korea vs Japan | Too small to map |
| Falkland Islands claim | Disputed (List 2) | Argentina vs UK | Covered by Falklands territory card (List 1) |
| French Southern and Antarctic Lands | Uninhabited | France | Uninhabited; no permanent population (staff at most) |
| Gibraltar claim | Disputed (List 2) | Spain vs UK | Covered by Gibraltar territory card |
| Hala'ib Triangle | Disputed (List 2) | Egypt vs Sudan | Low salience |
| Hans Island | Disputed (List 2) | Canada and Denmark | Dispute resolved June 2022 |
| Heard Island and McDonald Islands | Uninhabited | Australia | Uninhabited; no permanent population (staff at most) |
| Ilemi Triangle | Disputed (List 2) | Kenya vs South Sudan | Low salience |
| Jan Mayen | Uninhabited | Norway | Uninhabited; no permanent population (staff at most) |
| Kalapani–Lipulekh | Disputed (List 2) | Nepal vs India | Small, minor |
| Madeira | Dependency (List 1) | Portugal | Integral Portuguese region; no M49 code |
| Mayotte | Dependency (List 1) | France | Small; low learner salience; Comoros claim |
| Melilla | Dependency (List 1) | Spain | Integral Spanish city; Moroccan claim; tiny |
| Montserrat | Dependency (List 1) | UK | Small; tricky capital adds noise |
| Nagorno-Karabakh | Disputed (List 2) | Azerbaijan vs Armenian separatists | Dispute resolved by force; no longer contested territory |
| Niue | Dependency (List 1) | New Zealand | Tiny population |
| Norfolk Island | Dependency (List 1) | Australia | Tiny, remote |
| Northern Mariana Islands | Dependency (List 1) | USA | Small; overshadowed by neighbouring Guam |
| Paracel Islands | Disputed (List 2) | China vs Vietnam, Taiwan | Tiny; Spratlys card covers the theme |
| Pitcairn Islands | Dependency (List 1) | UK | ~50 people; Bounty trivia only |
| Russian-occupied Donetsk, Luhansk, Zaporizhzhia, Kherson | Disputed (List 2) | Ukraine vs Russia | Control line unstable and NE lacks it; revisit if a line freezes |
| Saint Barthélemy | Dependency (List 1) | France | Tiny; unreadable at country scale |
| Saint Helena, Ascension and Tristan da Cunha | Dependency (List 1) | UK | Remote, tiny population; three scattered island groups |
| Saint Martin (French part) | Dependency (List 1) | France | Half an island; tiny |
| Saint Pierre and Miquelon | Dependency (List 1) | France | Tiny; curiosity only |
| Scarborough Shoal | Disputed (List 2) | China vs Philippines, Taiwan | Reef, no land outline |
| Senkaku / Diaoyu Islands | Disputed (List 2) | Japan vs China, Taiwan | Specks too small to outline; mention on Japan/China backs |
| Siachen Glacier | Disputed (List 2) | India vs Pakistan | Fold into Indian-administered Kashmir card |
| Sint Maarten | Dependency (List 1) | Netherlands | Half an island; tiny |
| South Georgia and the South Sandwich Islands | Uninhabited | UK | Uninhabited; no permanent population (staff at most) |
| Tokelau | Dependency (List 1) | New Zealand | Tiny atolls; no capital |
| Turks and Caicos Islands | Dependency (List 1) | UK | Small Caribbean territory; low salience |
| US Minor Outlying Islands (Wake, Midway, Johnston, Baker, Howland, Jarvis, Kingman Reef, Palmyra, Navassa) | Uninhabited | USA | Uninhabited; no permanent population (staff at most) |
| US Virgin Islands | Dependency (List 1) | USA | Small Caribbean islands; low geographic weight |
| Wallis and Futuna | Dependency (List 1) | France | Small, obscure |
