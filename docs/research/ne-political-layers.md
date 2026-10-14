# Natural Earth political layers

> **Research for World Atlas P1 (WS4), 2026-10-14.** Maps each country, territory and dispute card to the Natural Earth rows that draw it, under the decisions recorded in [world-atlas-plan.md](../world-atlas-plan.md). Nothing here is built yet. Phase P2 (2.1 political model, 2.2 countries, 2.3 territories, 2.6 continents) consumes it.

Every table below is printed by `uv run python tools/ne_survey.py`. The script is read-only and uses only the pinned `vendor/` files. Re-run it after a re-pin and diff its tables against these.

## Layers and conventions

The four new layers are pinned in `data/sources.lock` at `nvkelso/natural-earth-vector@f1890d9f` (Natural Earth v5.1.2), the same commit as the existing vector layers. `make fetch` verifies them.

| Layer | Bytes | Rows | Used for |
|---|---|---|---|
| `ne_10m_populated_places` | 19,359,003 | 7,342 | capital points |
| `ne_10m_admin_0_map_units` | 13,526,439 | 298 | mainland France, Netherlands, Norway and New Zealand; Svalbard and the French overseas departments |
| `ne_10m_admin_0_disputed_areas` | 701,323 | 99 | dispute outlines; recognised-border composition |
| `ne_10m_admin_0_boundary_lines_disputed_areas` | 183,831 | 75 | dashed disputed lines |

All four files are well under the GitHub contents API's 100 MB limit for raw downloads, so `fetch.py` handles them as it does the existing pins, and no `_simple` variant is needed. Three of them are over the 1 MB limit for inline JSON content, as are most existing pins; `fetch.py` downloads the raw media type and reads only the blob sha from the JSON response.

- **Layer tags:** `A0` = `ne_10m_admin_0_countries` (already vendored), `MU` = `ne_10m_admin_0_map_units`, `DA` = `ne_10m_admin_0_disputed_areas`.
- **Always cite an `ne_id` with its layer.** NE reuses an `ne_id` across layers for the same entity. For example, `1159321259` is Somaliland in both A0 and DA, and `1159321135` is New Zealand in both A0 and MU, with different geometry.
- **Join on `ne_id` plus layer, never on names or codes.** Name columns show NE's own spellings (Bogota, København, Kingdom of eSwatini). ADM0_A3 matching already breaks for South Sudan (`SSD` in populated_places, `SDS` in A0) and Palestine (`PSX`).
- **Areas** are geodesic (WGS84) on NE's 10m polygons. They are approximate and are meant for comparing rows, not for card backs.

## (a) States

There are 197 country cards: the 193 UN members plus Vatican, Palestine, Kosovo and Taiwan.

**Outline source.** Each state uses its A0 row, except in two cases:

- **Map unit instead of A0.** The A0 rows for France, the Netherlands, Norway and New Zealand carry overseas parts:
  - France: the five overseas departments, including Mayotte.
  - Netherlands: the Caribbean Netherlands.
  - Norway: Svalbard, Jan Mayen and Bouvet Island.
  - New Zealand: Tokelau.

  Country cards show the mainland only, so these four states use their core map unit.
- **Composed outline.** A `+`/`-` in the source column means the outline is composed per [(c)](#c-recognised-border-composition).

**Rule: a country card's outline is exactly its source column.** Nothing else is added or removed.

Portugal (Azores, Madeira), Spain (Canaries, Ceuta, Melilla), Ecuador (Galápagos) and Chile (Easter Island) keep their A0 rows, because those parts are integral and get no card of their own. If P4 needs mainland Portugal alone for framing, MU `1159321193` (`PRX`) is available.

**Capital.** The capital is the `populated_places` row with `FEATURECLA = Admin-0 capital` whose `ADM0_A3` matches the state. NE tags more than one `Admin-0 capital` row for four states. For those the table picks one official seat; the others are listed in the Note column:

| State | Pick | Others |
|---|---|---|
| Bolivia | Sucre (constitutional) | La Paz |
| South Africa | Pretoria (executive) | Cape Town, Bloemfontein; Johannesburg is mis-tagged |
| Côte d'Ivoire | Yamoussoukro | Abidjan |
| Myanmar | Naypyidaw | Yangon is a former capital, still tagged |

**Gaps and flags:**

- **Two capital gaps.**
  - **Nauru** has no `populated_places` row of any kind. Yaren is missing, and Nauru has no official capital. Hand-placing a point would break the plan's Natural-Earth-only data rule, so this is a user decision: drop Nauru's capital card, or allow one hand-placed point.
  - **Palestine** has no `Admin-0 capital` row. Ramallah is `Admin-0 region capital` `1159121947`, and East Jerusalem has no point of its own (Jerusalem `1159151203` is tagged to Israel). This doesn't block anything, because the plan gives Palestine no capital card.
- **The tag differs from the constitutional capital** (user decision):
  - Benin: Cotonou is tagged; Porto-Novo is `1159150345`.
  - Tanzania: Dar es Salaam is tagged; Dodoma is `1159149731`.
  - Sri Lanka: Colombo is tagged; Sri Jayawardenepura Kotte is `1159149593`.

  The table follows the tag, as the brief requires. See [Open decisions](#open-decisions) before using these three rows.
- **Data quirks.**
  - Kazakhstan's capital is still named `Nur-Sultan`; it was renamed Astana in 2022.
  - South Sudan's Juba carries `ADM0CAP 0` and the code `SSD`, while A0 uses `SDS`.
  - Israel's Jerusalem is NE's "de facto" capital and its status is contested; Tel Aviv `1159151417` is `Admin-0 capital alt`.
- **Not used:** the Admin-0 capital rows for Hargeisa (Somaliland `1159151189`) and the `Admin-0 capital alt` row for Bir Lehlou (Western Sahara `1159149075`). Both places have dispute cards only.

| # | State | ISO | Outline source | Capital | populated_places `ne_id` | Note |
|---|---|---|---|---|---|---|
| 1 | Afghanistan | AFG | A0 `1159320319` | Kabul | 1159151561 |  |
| 2 | Albania | ALB | A0 `1159320325` | Tirana | 1159151117 |  |
| 3 | Algeria | DZA | A0 `1159320565` | Algiers | 1159151471 |  |
| 4 | Andorra | AND | A0 `1159320327` | Andorra | 1159149089 |  |
| 5 | Angola | AGO | A0 `1159320323` | Luanda | 1159151469 |  |
| 6 | Antigua and Barbuda | ATG | A0 `1159320345` | Saint John's | 1159150457 |  |
| 7 | Argentina | ARG | A0 `1159320331` | Buenos Aires | 1159151559 |  |
| 8 | Armenia | ARM | A0 `1159320333` | Yerevan | 1159151119 |  |
| 9 | Australia | AUS | A0 `1159320355` | Canberra | 1159151161 |  |
| 10 | Austria | AUT | A0 `1159320379` | Vienna | 1159151563 |  |
| 11 | Azerbaijan | AZE | A0 `1159320381` | Baku | 1159151123 |  |
| 12 | Bahamas | BHS | A0 `1159320415` | Nassau | 1159151207 |  |
| 13 | Bahrain | BHR | A0 `1159320413` | Manama | 1159150451 |  |
| 14 | Bangladesh | BGD | A0 `1159320407` | Dhaka | 1159151467 |  |
| 15 | Barbados | BRB | A0 `1159320449` | Bridgetown | 1159150339 |  |
| 16 | Belarus | BLR | A0 `1159320427` | Minsk | 1159151149 |  |
| 17 | Belgium | BEL | A0 `1159320389` | Brussels | 1159151465 |  |
| 18 | Belize | BLZ | A0 `1159320431` | Belmopan | 1159151109 |  |
| 19 | Benin | BEN | A0 `1159320399` | Cotonou | 1159151141 | tag is Cotonou (seat of government); constitutional capital Porto-Novo is `Admin-0 capital alt` 1159150345 |
| 20 | Bhutan | BTN | A0 `1159320453` | Thimphu | 1159151151 |  |
| 21 | Bolivia | BOL | A0 `1159320439` | Sucre | 1159151095 | Sucre (constitutional); La Paz 1159151133 is the seat of government |
| 22 | Bosnia and Herzegovina | BIH | A0 `1159320417` | Sarajevo | 1159151177 |  |
| 23 | Botswana | BWA | A0 `1159320461` | Gaborone | 1159151153 |  |
| 24 | Brazil | BRA | A0 `1159320441` | Brasília | 1159151443 |  |
| 25 | Brunei Darussalam | BRN | A0 `1159320451` | Bandar Seri Begawan | 1159151083 |  |
| 26 | Bulgaria | BGR | A0 `1159320409` | Sofia | 1159151147 |  |
| 27 | Burkina Faso | BFA | A0 `1159320405` | Ouagadougou | 1159151173 |  |
| 28 | Burundi | BDI | A0 `1159320387` | Bujumbura | 1159150427 |  |
| 29 | Cambodia | KHM | A0 `1159320979` | Phnom Penh | 1159151127 |  |
| 30 | Cameroon | CMR | A0 `1159320509` | Yaoundé | 1159151115 |  |
| 31 | Canada | CAN | A0 `1159320467` | Ottawa | 1159151059 |  |
| 32 | Central African Republic | CAF | A0 `1159320463` | Bangui | 1159151111 |  |
| 33 | Chad | TCD | A0 `1159321301` | N'Djamena | 1159150863 |  |
| 34 | Chile | CHL | A0 `1159320493` | Santiago | 1159151615 |  |
| 35 | China | CHN | A0 `1159320471` | Beijing | 1159151595 |  |
| 36 | Colombia | COL | A0 `1159320517` | Bogota | 1159151601 |  |
| 37 | Comoros | COM | A0 `1159320521` | Moroni | 1159149083 |  |
| 38 | Costa Rica | CRI | A0 `1159320525` | San José | 1159150849 |  |
| 39 | Croatia | HRV | A0 `1159320833` | Zagreb | 1159150875 |  |
| 40 | Cuba | CUB | A0 `1159320527` + A0 `1159320529` | Havana | 1159151347 |  |
| 41 | Cyprus | CYP | A0 `1159320533` + A0 `1159320531` + A0 `1159320511` | Nicosia | 1159151209 |  |
| 42 | Czech Republic | CZE | A0 `1159320535` | Prague | 1159151359 |  |
| 43 | Côte d'Ivoire | CIV | A0 `1159320507` | Yamoussoukro | 1159150999 | Yamoussoukro (official); Abidjan 1159151439 is de facto |
| 44 | Dem. Rep. Korea | PRK | A0 `1159321181` | Pyongyang | 1159151303 |  |
| 45 | Democratic Republic of the Congo | COD | A0 `1159320513` | Kinshasa | 1159151539 |  |
| 46 | Denmark | DNK | A0 `1159320547` | København | 1159151437 |  |
| 47 | Djibouti | DJI | A0 `1159320541` | Djibouti | 1159149869 |  |
| 48 | Dominica | DMA | A0 `1159320543` | Roseau | 1159149847 |  |
| 49 | Dominican Republic | DOM | A0 `1159320563` | Santo Domingo | 1159151401 |  |
| 50 | Ecuador | ECU | A0 `1159320567` | Quito | 1159150847 |  |
| 51 | Egypt | EGY | A0 `1159320575` | Cairo | 1159151603 |  |
| 52 | El Salvador | SLV | A0 `1159321253` | San Salvador | 1159150853 |  |
| 53 | Equatorial Guinea | GNQ | A0 `1159320801` | Malabo | 1159150867 |  |
| 54 | Eritrea | ERI | A0 `1159320581` | Asmara | 1159150873 |  |
| 55 | Estonia | EST | A0 `1159320615` | Tallinn | 1159150877 |  |
| 56 | Ethiopia | ETH | A0 `1159320617` | Addis Ababa | 1159151549 |  |
| 57 | Federated States of Micronesia | FSM | A0 `1159320691` | Palikir | 1159149061 |  |
| 58 | Fiji | FJI | A0 `1159320625` | Suva | 1159150917 |  |
| 59 | Finland | FIN | A0 `1159320623` | Helsinki | 1159151419 |  |
| 60 | France | FRA | MU `1159320651` | Paris | 1159151613 |  |
| 61 | Gabon | GAB | A0 `1159320693` | Libreville | 1159150913 |  |
| 62 | Georgia | GEO | A0 `1159320779` | Tbilisi | 1159150961 |  |
| 63 | Germany | DEU | A0 `1159320539` | Berlin | 1159151529 |  |
| 64 | Ghana | GHA | A0 `1159320793` | Accra | 1159151403 |  |
| 65 | Greece | GRC | A0 `1159320811` | Athens | 1159151545 |  |
| 66 | Grenada | GRD | A0 `1159320813` | Saint George's | 1159150447 |  |
| 67 | Guatemala | GTM | A0 `1159320815` | Guatemala City | 1159150909 |  |
| 68 | Guinea | GIN | A0 `1159320795` | Conakry | 1159150997 |  |
| 69 | Guinea-Bissau | GNB | A0 `1159320799` | Bissau | 1159150803 |  |
| 70 | Guyana | GUY | A0 `1159320817` | Georgetown | 1159150585 |  |
| 71 | Haiti | HTI | A0 `1159320839` | Port-au-Prince | 1159150589 |  |
| 72 | Honduras | HND | A0 `1159320827` | Tegucigalpa | 1159150583 |  |
| 73 | Hungary | HUN | A0 `1159320841` | Budapest | 1159151257 |  |
| 74 | Iceland | ISL | A0 `1159320917` | Reykjavík | 1159150587 |  |
| 75 | India | IND | A0 `1159320847` + A0 `1159320963` | New Delhi | 1159151541 |  |
| 76 | Indonesia | IDN | A0 `1159320845` | Jakarta | 1159151599 |  |
| 77 | Iran | IRN | A0 `1159320881` | Tehran | 1159151551 |  |
| 78 | Iraq | IRQ | A0 `1159320887` | Baghdad | 1159151547 |  |
| 79 | Ireland | IRL | A0 `1159320877` | Dublin | 1159151309 |  |
| 80 | Israel | ISR | A0 `1159320895` - DA `1159320905` | Jerusalem | 1159151203 | Jerusalem: NE notes de facto capital; status contested. Tel Aviv is `Admin-0 capital alt` 1159151417 |
| 81 | Italy | ITA | A0 `1159320919` | Rome | 1159151593 |  |
| 82 | Jamaica | JAM | A0 `1159320931` | Kingston | 1159150855 |  |
| 83 | Japan | JPN | A0 `1159320937` | Tokyo | 1159151609 |  |
| 84 | Jordan | JOR | A0 `1159320935` | Amman | 1159150807 |  |
| 85 | Kazakhstan | KAZ | A0 `1159320967` + A0 `1159320965` | Nur-Sultan | 1159150965 | NE name `Nur-Sultan` is stale: renamed Astana in 2022 |
| 86 | Kenya | KEN | A0 `1159320971` | Nairobi | 1159151597 |  |
| 87 | Kingdom of eSwatini | SWZ | A0 `1159321289` | Mbabane | 1159149413 | Mbabane (administrative); Lobamba is `Admin-0 capital alt` 1159146343 |
| 88 | Kiribati | KIR | A0 `1159320981` | Tarawa | 1159149079 |  |
| 89 | Kosovo | KOS | A0 `1159321007` | Pristina | 1159149757 |  |
| 90 | Kuwait | KWT | A0 `1159321009` | Kuwait City | 1159151361 |  |
| 91 | Kyrgyzstan | KGZ | A0 `1159320977` | Bishkek | 1159150813 |  |
| 92 | Lao PDR | LAO | A0 `1159321011` | Vientiane | 1159150991 |  |
| 93 | Latvia | LVA | A0 `1159321033` | Riga | 1159150811 |  |
| 94 | Lebanon | LBN | A0 `1159321013` | Beirut | 1159150957 |  |
| 95 | Lesotho | LSO | A0 `1159321027` | Maseru | 1159150831 |  |
| 96 | Liberia | LBR | A0 `1159321015` | Monrovia | 1159151311 |  |
| 97 | Libya | LBY | A0 `1159321017` | Tripoli | 1159151415 |  |
| 98 | Liechtenstein | LIE | A0 `1159321021` | Vaduz | 1159146061 |  |
| 99 | Lithuania | LTU | A0 `1159321029` | Vilnius | 1159150809 |  |
| 100 | Luxembourg | LUX | A0 `1159321031` | Luxembourg | 1159146437 |  |
| 101 | Madagascar | MDG | A0 `1159321051` | Antananarivo | 1159150835 |  |
| 102 | Malawi | MWI | A0 `1159321081` | Lilongwe | 1159150907 |  |
| 103 | Malaysia | MYS | A0 `1159321083` | Kuala Lumpur | 1159151317 |  |
| 104 | Maldives | MDV | A0 `1159321053` | Malé | 1159151201 |  |
| 105 | Mali | MLI | A0 `1159321063` | Bamako | 1159150945 |  |
| 106 | Malta | MLT | A0 `1159321065` | Valletta | 1159151199 |  |
| 107 | Marshall Islands | MHL | A0 `1159321057` | Majuro | 1159149063 |  |
| 108 | Mauritania | MRT | A0 `1159321075` | Nouakchott | 1159150943 |  |
| 109 | Mauritius | MUS | A0 `1159321079` | Port Louis | 1159150443 |  |
| 110 | Mexico | MEX | A0 `1159321055` | Mexico City | 1159151587 |  |
| 111 | Moldova | MDA | A0 `1159321045` | Chișinău | 1159150677 |  |
| 112 | Monaco | MCO | A0 `1159321043` | Monaco | 1159149077 |  |
| 113 | Mongolia | MNG | A0 `1159321071` | Ulaanbaatar | 1159150781 |  |
| 114 | Montenegro | MNE | A0 `1159321069` | Podgorica | 1159149511 |  |
| 115 | Morocco | MAR | A0 `1159321035` - DA `1159321037` | Rabat | 1159150673 |  |
| 116 | Mozambique | MOZ | A0 `1159321073` | Maputo | 1159150683 |  |
| 117 | Myanmar | MMR | A0 `1159321067` | Naypyidaw | 1159151179 | Naypyidaw; Yangon 1159151477 is the former capital (tagged, ADM0CAP 0) |
| 118 | Namibia | NAM | A0 `1159321085` | Windhoek | 1159150785 |  |
| 119 | Nauru | NRU | A0 `1159321123` |  | — | no populated_places row for Nauru at all (Yaren, the seat of government, is missing) |
| 120 | Nepal | NPL | A0 `1159321121` | Kathmandu | 1159150655 |  |
| 121 | Netherlands | NLD | MU `1159321105` | Amsterdam | 1159151519 |  |
| 122 | New Zealand | NZL | MU `1159321135` | Wellington | 1159151699 |  |
| 123 | Nicaragua | NIC | A0 `1159321091` | Managua | 1159150623 |  |
| 124 | Niger | NER | A0 `1159321087` | Niamey | 1159150605 |  |
| 125 | Nigeria | NGA | A0 `1159321089` | Abuja | 1159150799 |  |
| 126 | North Macedonia | MKD | A0 `1159321061` | Skopje | 1159150073 |  |
| 127 | Norway | NOR | MU `1159321117` | Oslo | 1159151281 |  |
| 128 | Oman | OMN | A0 `1159321151` | Muscat | 1159150717 |  |
| 129 | Pakistan | PAK | A0 `1159321153` | Islamabad | 1159150645 |  |
| 130 | Palau | PLW | A0 `1159321171` | Melekeok | 1159149073 |  |
| 131 | Palestine | PSE | A0 `1159320899` |  | — | no `Admin-0 capital` row; Ramallah is `Admin-0 region capital` 1159121947; East Jerusalem has no point |
| 132 | Panama | PAN | A0 `1159321161` | Panama City | 1159150667 |  |
| 133 | Papua New Guinea | PNG | A0 `1159321173` | Port Moresby | 1159150663 |  |
| 134 | Paraguay | PRY | A0 `1159321195` | Asunción | 1159150621 |  |
| 135 | Peru | PER | A0 `1159321163` | Lima | 1159151511 |  |
| 136 | Philippines | PHL | A0 `1159321169` | Manila | 1159151525 |  |
| 137 | Poland | POL | A0 `1159321179` | Warsaw | 1159151299 |  |
| 138 | Portugal | PRT | A0 `1159321187` | Lisbon | 1159151273 |  |
| 139 | Qatar | QAT | A0 `1159321197` | Doha | 1159149469 |  |
| 140 | Republic of Cabo Verde | CPV | A0 `1159320523` | Praia | 1159151205 |  |
| 141 | Republic of Korea | KOR | A0 `1159320985` | Seoul | 1159151523 |  |
| 142 | Republic of the Congo | COG | A0 `1159320515` | Brazzaville | 1159150993 |  |
| 143 | Romania | ROU | A0 `1159321199` | Bucharest | 1159151263 |  |
| 144 | Russian Federation | RUS | A0 `1159321201` - DA `1159321217` | Moscow | 1159151585 |  |
| 145 | Rwanda | RWA | A0 `1159321219` | Kigali | 1159149385 |  |
| 146 | Saint Kitts and Nevis | KNA | A0 `1159320983` | Basseterre | 1159150435 |  |
| 147 | Saint Lucia | LCA | A0 `1159321019` | Castries | 1159150433 |  |
| 148 | Saint Vincent and the Grenadines | VCT | A0 `1159321409` | Kingstown | 1159150431 |  |
| 149 | Samoa | WSM | A0 `1159321423` | Apia | 1159151197 |  |
| 150 | San Marino | SMR | A0 `1159321255` | San Marino | 1159146051 |  |
| 151 | Saudi Arabia | SAU | A0 `1159321225` | Riyadh | 1159151581 |  |
| 152 | Senegal | SEN | A0 `1159321243` | Dakar | 1159151513 |  |
| 153 | Serbia | SRB | A0 `1159321267` | Belgrade | 1159151079 |  |
| 154 | Seychelles | SYC | A0 `1159321291` | Victoria | 1159151191 |  |
| 155 | Sierra Leone | SLE | A0 `1159321251` | Freetown | 1159150625 |  |
| 156 | Singapore | SGP | A0 `1159321247` | Singapore | 1159151627 |  |
| 157 | Slovakia | SVK | A0 `1159321283` | Bratislava | 1159149463 |  |
| 158 | Slovenia | SVN | A0 `1159321285` | Ljubljana | 1159149461 |  |
| 159 | Solomon Islands | SLB | A0 `1159321249` | Honiara | 1159150665 |  |
| 160 | Somalia | SOM | A0 `1159321261` + A0 `1159321259` | Mogadishu | 1159150715 |  |
| 161 | South Africa | ZAF | A0 `1159321431` | Pretoria | 1159150661 | Pretoria (executive); Cape Town 1159151583, Bloemfontein 1159150659; Johannesburg 1159151515 is mis-tagged |
| 162 | South Sudan | SSD | A0 `1159321235` | Juba | 1159149449 | Juba is tagged `Admin-0 capital` but ADM0CAP 0; code SSD in populated_places |
| 163 | Spain | ESP | A0 `1159320587` | Madrid | 1159151503 |  |
| 164 | Sri Lanka | LKA | A0 `1159321025` | Colombo | 1159150719 | tag is Colombo; official capital Sri Jayawardenepura Kotte is `Admin-0 capital alt` 1159149593 |
| 165 | Sudan | SDN | A0 `1159321229` | Khartoum | 1159151275 |  |
| 166 | Suriname | SUR | A0 `1159321281` | Paramaribo | 1159150597 |  |
| 167 | Sweden | SWE | A0 `1159321287` | Stockholm | 1159151507 |  |
| 168 | Switzerland | CHE | A0 `1159320491` | Bern | 1159149737 |  |
| 169 | Syria | SYR | A0 `1159321295` + DA `1159320905` | Damascus | 1159151269 |  |
| 170 | São Tomé and Principe | STP | A0 `1159321273` | São Tomé | 1159151195 |  |
| 171 | Taiwan | TWN | A0 `1159321335` | Taipei | 1159151567 |  |
| 172 | Tajikistan | TJK | A0 `1159321307` | Dushanbe | 1159150609 |  |
| 173 | Tanzania | TZA | A0 `1159321337` | Dar es Salaam | 1159151305 | tag is Dar es Salaam; official capital Dodoma is `Admin-0 capital alt` 1159149731 |
| 174 | Thailand | THA | A0 `1159321305` | Bangkok | 1159151509 |  |
| 175 | The Gambia | GMB | A0 `1159320797` | Banjul | 1159149997 |  |
| 176 | Timor-Leste | TLS | A0 `1159321313` | Dili | 1159150577 |  |
| 177 | Togo | TGO | A0 `1159321303` | Lomé | 1159150535 |  |
| 178 | Tonga | TON | A0 `1159321319` | Nuku'alofa | 1159151187 |  |
| 179 | Trinidad and Tobago | TTO | A0 `1159321321` | Port-of-Spain | 1159149307 |  |
| 180 | Tunisia | TUN | A0 `1159321327` | Tunis | 1159150537 |  |
| 181 | Turkey | TUR | A0 `1159321331` | Ankara | 1159151255 |  |
| 182 | Turkmenistan | TKM | A0 `1159321309` | Ashgabat | 1159150567 |  |
| 183 | Tuvalu | TUV | A0 `1159321333` | Funafuti | 1159149071 |  |
| 184 | Uganda | UGA | A0 `1159321343` | Kampala | 1159150593 |  |
| 185 | Ukraine | UKR | A0 `1159321345` + DA `1159321217` | Kyiv | 1159151495 |  |
| 186 | United Arab Emirates | ARE | A0 `1159320329` | Abu Dhabi | 1159150565 |  |
| 187 | United Kingdom | GBR | A0 `1159320713` | London | 1159151577 |  |
| 188 | United States | USA | A0 `1159321369` | Washington,  D.C. | 1159151573 |  |
| 189 | Uruguay | URY | A0 `1159321353` | Montevideo | 1159150469 |  |
| 190 | Uzbekistan | UZB | A0 `1159321405` | Tashkent | 1159151501 |  |
| 191 | Vanuatu | VUT | A0 `1159321421` | Port Vila | 1159150579 |  |
| 192 | Vatican | VAT | A0 `1159321407` | Vatican City | 1159127243 |  |
| 193 | Venezuela | VEN | A0 `1159321411` | Caracas | 1159151493 |  |
| 194 | Vietnam | VNM | A0 `1159321417` | Hanoi | 1159151251 |  |
| 195 | Yemen | YEM | A0 `1159321425` | Sanaa | 1159151259 |  |
| 196 | Zambia | ZMB | A0 `1159321439` | Lusaka | 1159150571 |  |
| 197 | Zimbabwe | ZWE | A0 `1159321441` | Harare | 1159150573 |  |

197 states; 2 without a capital `ne_id`: NRU: no populated_places row for Nauru at all (Yaren, the seat of government, is missing); PSE: no `Admin-0 capital` row; Ramallah is `Admin-0 region capital` 1159121947; East Jerusalem has no point

## (b) Territory and dispute outlines

Each card's outline is the union of the rows listed. All 23 territories are single rows. Svalbard and the four French overseas departments exist only in MU. Notes on the disputes:

- **Indian-administered Kashmir** combines three rows:
  - the DA *Jammu and Kashmir* row, which includes Ladakh;
  - DA *Demchok* (India-held and claimed by China), which touches it;
  - the A0 *Siachen Glacier* row, folded in as the plan's revisit list says.

  The other India-held rows that China claims (Samdu `1159320867`, Tirpani `1159320859`, Bara Hotii `1159320863`, Near Om Parvat `1159320873`) lie outside both Kashmir and Arunachal and get no card.
- **Aksai Chin** includes the Shaksgam tract, which NE spells "Shaksam Valley".
- **Western Sahara** combines the Moroccan-held DA row `1159321037` with the Polisario-held A0 row `1159321223`. The A0 row's `ne_id` also appears in DA, as a copy of the same eastern part.
- **Northern Cyprus, Somaliland and Spratly** use their A0 rows. Their DA rows share the same `ne_id`. Northern Cyprus and Somaliland differ by under 0.01% in area; Spratly differs by about 0.5 km² of 12.
- **Golan** is the DA row alone. The adjacent Shebaa Farms (DA `1159320907`, 18 km²) is open; see (c).
- **Enclosed claims that get no card.** These lie inside a card's host and are not separate cards:
  - French Guiana's MU contains Suriname's Lawa Headwaters claim (DA `1159320683`, 3,495 km²).
  - Guyana's A0 contains Suriname's Courantyne Headwaters claim (DA `1159320819`, 14,319 km²).

### Territories

| Card | Rows (union) | NE names | Area km² |
|---|---|---|---|
| Greenland | A0 `1159320551` | Greenland | 2,154,381 |
| Faroe Islands | A0 `1159320549` | Faeroe Is. | 1,329 |
| Svalbard | MU `1159321119` | Svalbard Is. | 62,081 |
| Hong Kong | A0 `1159320473` | Hong Kong | 1,036 |
| Macau | A0 `1159320475` | Macao | 30 |
| Puerto Rico | A0 `1159321363` | Puerto Rico | 9,006 |
| Guam | A0 `1159321359` | Guam | 564 |
| Gibraltar | A0 `1159320719` | Gibraltar | 4 |
| Falkland Islands | A0 `1159320711` | Falkland Is. | 11,597 |
| Bermuda | A0 `1159320705` | Bermuda | 62 |
| Cayman Islands | A0 `1159320707` | Cayman Is. | 309 |
| British Indian Ocean Territory | A0 `1159320723` | Br. Indian Ocean Ter. | 49 |
| Isle of Man | A0 `1159320721` | Isle of Man | 575 |
| Jersey | A0 `1159320725` | Jersey | 119 |
| Guernsey | A0 `1159320715` | Guernsey | 74 |
| New Caledonia | A0 `1159320641` | New Caledonia | 18,841 |
| French Polynesia | A0 `1159320643` | Fr. Polynesia | 3,337 |
| French Guiana | MU `1159320655` | French Guiana | 83,184 |
| Réunion | MU `1159320661` | Réunion | 2,582 |
| Guadeloupe | MU `1159320653` | Guadeloupe | 1,657 |
| Martinique | MU `1159320657` | Martinique | 1,097 |
| Aruba | A0 `1159321097` | Aruba | 170 |
| Curaçao | A0 `1159321099` | Curaçao | 463 |

### Disputes

| Card | Rows (union) | NE names | Area km² |
|---|---|---|---|
| Crimea | DA `1159321217` | Crimea | 27,096 |
| Kashmir: Indian-administered | DA `1159320869` + DA `1159320865` + A0 `1159320963` | Jammu and Kashmir + Demchok + Siachen Glacier | 108,896 |
| Kashmir: Pakistani-administered | DA `1159321157` + DA `1159321155` | Azad Kashmir + Gilgit-Baltistan | 77,207 |
| Aksai Chin | DA `1159320487` + DA `1159320485` | Aksai Chin + Shaksam Valley | 36,320 |
| Arunachal Pradesh | DA `1159320857` | Arunachal Pradesh | 67,967 |
| Western Sahara | DA `1159321037` + A0 `1159321223` | W. Sahara + W. Sahara | 268,344 |
| Golan Heights | DA `1159320905` | Golan Heights | 1,194 |
| Abkhazia | DA `1159320785` | Abkhazia | 8,638 |
| South Ossetia | DA `1159320787` | South Ossetia | 4,465 |
| Transnistria | DA `1159321047` | Transnistria | 3,052 |
| Northern Cyprus | A0 `1159320531` | N. Cyprus | 3,320 |
| Somaliland | A0 `1159321259` | Somaliland | 167,407 |
| Kuril Islands | DA `1159321213` | Kuril Is. | 4,970 |
| Spratly Islands | A0 `1159321165` | Spratly Is. | 12 |
| Essequibo | DA `1159320821` | West of Essequibo River | 142,396 |

Adjacency checks: Demchok touches J&K True; Siachen touches J&K True; Tirpani touches Arunachal False.

## (c) Recognised-border composition

Composition is exact add/subtract. The survey asserts it for every row used:

- each `-` row lies more than 99.9% inside its base;
- each `+` row lies less than 0.1% inside its base;
- each result's area equals base ± rows to within 1 km², so there are no slivers or overlaps.

82 of the 99 DA rows lie at least 99.9% inside a single A0 row. The other 17 are islands and specks that NE draws slightly off the A0 coastline (the list is under the table), and none of them is used in a composition. P2.1 should carry the same assertions into `check.py data`.

The decision needs eight row operations:

- Crimea moves from Russia to Ukraine.
- Northern Cyprus and the UN buffer zone join Cyprus.
- The Golan moves from Israel to Syria.
- Western Sahara's Moroccan-held part leaves Morocco.
- Somaliland joins Somalia.

Siachen joins India under the "Kashmir stays with its administrators" rule. Two more operations follow the same recognised-sovereignty logic but go beyond the recorded decision, so they are **defaults to confirm**: Baikonur joins Kazakhstan and Guantanamo Bay joins Cuba.

Abkhazia, South Ossetia, Transnistria, the Donetsk and Luhansk shapes, and the Kurils are already inside the A0 row of the state the decision assigns them to. The table lists them with a `0` and changes nothing.

| State | Base row | Base km² | Change | Row km² | Result km² |
|---|---|---|---|---|---|
| Ukraine | A0 `1159321345` | 571,999 | + DA `1159321217` Crimea | 27,096 |  |
|  |  |  | 0 DA `1763286545` Donetsk People's Republic (no change; 100.0% inside base) | 9,451 |  |
|  |  |  | 0 DA `1763286547` Luhansk People's Republic (no change; 100.0% inside base) | 8,306 | 599,095 |
| Russia | A0 `1159321201` | 16,980,200 | - DA `1159321217` Crimea | 27,096 |  |
|  |  |  | 0 DA `1159321213` Kuril Is. (no change; 99.2% inside base) | 4,970 | 16,953,104 |
| Georgia | A0 `1159320779` | 69,571 | 0 DA `1159320785` Abkhazia (no change; 100.0% inside base) | 8,638 |  |
|  |  |  | 0 DA `1159320787` South Ossetia (no change; 100.0% inside base) | 4,465 | 69,571 |
| Moldova | A0 `1159321045` | 33,206 | 0 DA `1159321047` Transnistria (no change; 100.0% inside base) | 3,052 | 33,206 |
| Cyprus | A0 `1159320533` | 5,395 | + A0 `1159320531` N. Cyprus | 3,320 |  |
|  |  |  | + A0 `1159320511` Cyprus U.N. Buffer Zone | 341 | 9,056 |
| Syria | A0 `1159321295` | 185,939 | + DA `1159320905` Golan Heights | 1,194 | 187,133 |
| Israel | A0 `1159320895` | 22,101 | - DA `1159320905` Golan Heights | 1,194 |  |
|  |  |  | ? DA `1159320907` Shebaa Farms (open; 100.0% inside base) | 18 |  |
|  |  |  | ? DA `1746265961` East Jerusalem (open; 100.0% inside base) | 67 |  |
|  |  |  | ? DA `1159320911` No Man's Land (Jerusalem) (open; 100.0% inside base) | 3 |  |
|  |  |  | ? DA `1159320909` No Man's Land (Fort Latrun) (open; 100.0% inside base) | 51 |  |
|  |  |  | ? DA `1746265963` Mount Scopus (open; 100.0% inside base) | 1 | 20,907 |
| Morocco | A0 `1159321035` | 591,745 | - DA `1159321037` W. Sahara | 177,849 | 413,896 |
| Somalia | A0 `1159321261` | 471,815 | + A0 `1159321259` Somaliland | 167,407 | 639,222 |
| India | A0 `1159320847` | 3,150,747 | + A0 `1159320963` Siachen Glacier | 2,086 | 3,152,833 |
| Kazakhstan | A0 `1159320967` | 2,714,263 | + A0 `1159320965` Baikonur | 6,501 | 2,720,765 |
| Cuba | A0 `1159320527` | 109,929 | + A0 `1159320529` USNB Guantanamo Bay | 65 | 109,995 |

DA rows at least 99.9% inside one A0 row: 82 of 99. The rest, with their best share: Belize `1159320433` 99.8%; Halayib Triangle `1729635095` 99.9%; North Borneo `1763510959` 99.8%; Taiwan `1159321335` 99.7%; Kuril Is. `1159321213` 99.2%; S. Georgia `1159320765` 99.0%; Falkland Is. `1159320711` 99.4%; Paracel Is. `1159320477` 92.7%; Spratly Is. `1159321165` 95.6%; Korean islands under UN jurisdiction `1159320989` 84.4%; Bassas da India `1159320665` 27.1%; Pinnacle Is. `1159320959` 70.3%; Bajo Nuevo Bank (Petrel Is.) `1159320425` 8.3%; Sapodilla Cayes `1159320435` 0.0%; Islas Chafarinas `1159320607` 46.9%; Matthew and Hunter Is. `1159320687` 45.7%; Doumera Island `1159320583` 0.0%.

- A0 `1159320963`: Siachen Glacier: administered by India; Kashmir parts stay with administrators
- A0 `1159320965`: Baykonur: leased to Russia, Kazakh sovereignty
- A0 `1159320529`: Guantanamo Bay: leased to the US, Cuban sovereignty

Land-boundary segments touching composed rows (`ne_10m_admin_0_boundary_lines_land`):

| `ne_id` | Class | Left / right | km |
|---|---|---|---|
| 1746705341 | Line of control (please verify) | SYR / ISR | 89 |
| 1746705343 | Disputed (please verify) | SOL / SOM | 391 |
| 1746705351 | Line of control (please verify) | SAH / MAR | 1,319 |
| 1746705895 | International boundary (verify) | DJI / SOL | 64 |
| 1746706735 | Lease limit | CUB / USG | 13 |
| 1746708139 | International boundary (verify) | SOL / ETH | 761 |
| 1746708483 | Line of control (please verify) | CNM / CYN | 10 |
| 1746708491 | Line of control (please verify) | CNM / CYN | 130 |
| 1746708497 | Unrecognized | CNM / CYN | 6 |
| 1746708503 | International boundary (verify) | CYN / ESB | 45 |
| 1746708511 | International boundary (verify) | CNM / ESB | 9 |
| 1746708517 | International boundary (verify) | CYN / ESB | 0 |
| 1746708533 | International boundary (verify) | CNM / ESB | 1 |
| 1746708539 | International boundary (verify) | CYN / ESB | 0 |
| 1746708577 | Lease limit | CUB / USG | 13 |
| 1746708603 | Indeterminant frontier | PAK / KAS | 64 |
| 1746708607 | Indeterminant frontier | KAS / IND | 81 |
| 1746708621 | Lease limit | KAZ / KAB | 286 |
| 1746708639 | Overlay limit | CNM / CYP | 140 |
| 1746708645 | Overlay limit | CNM / CYP | 10 |
| 1746708649 | Overlay limit | CNM / CYP | 12 |
| 1746708655 | International boundary (verify) | KAS / CHN | 27 |
| 1746708661 | Indefinite (please verify) | KAS / CHN | 75 |
| 1746708721 | Line of control (please verify) | SAH / MAR | 13 |
| 1746708787 | Disputed (please verify) | RUS / UKR | 147 |

**Open rows inside Israel's A0 row** (`?` above). The decision names only the Golan:

- **Shebaa Farms** (18 km²): the UN treats it as part of the occupied Golan, and Lebanon claims it. To follow the Golan decision, move it to Syria with the Golan.
- **East Jerusalem, the two no-man's-land strips and Mount Scopus** (122 km² together): the UN treats these as occupied Palestinian territory. To follow the UN, move them to Palestine (A0 `1159320899`).

Neither choice changes either state's outline visibly at country scale. Both are listed under [Open decisions](#open-decisions).

**Rows left unassigned.**

- **UK sovereign base areas:** Dhekelia (A0 `1159320709`) and Akrotiri (A0 `1159320741`). Default: they stay as UK holes in Cyprus, since UK sovereignty there is recognised.
- **Indeterminate or terra nullius rows**, which stay neutral land with no card:
  - Bir Tawil `1729635091`
  - Brazilian Island `1729632181`
  - Southern Patagonian Ice Field `1729635141`
  - Bajo Nuevo `1159320425`
  - Serranilla `1159321245`
  - Scarborough Reef `1159321227`

**Dashed lines.** Draw these dashed:

- every row of `boundary_lines_disputed_areas`, except the stale rows in (e);
- the `boundary_lines_land` segments whose sides are merged by the composition: Crimea isthmus, Somaliland–Somalia, the berm, the Green Line and buffer-zone limits, the Golan Line of Control, and the Siachen frontiers.

The land-boundary table above lists those segments. Classes for the rest:

- **Stay solid:** Somaliland's borders with Ethiopia and Djibouti, which become Somalia's, and the limits of the UK sovereign base areas.
- **Drop:** the Guantanamo and Baikonur lease limits, once those rows merge into Cuba and Kazakhstan.

## (d) Point-of-view layers

**Recommendation: composition.** It makes six explicit row operations on the default A0 layer we already pin; P2 can review them in one table, and the dispute cards need the DA rows anyway. A POV layer would add another 13 MB pin. It would also bring in a third country's position on areas the decision doesn't cover, and that position can drift between NE releases. Use the KO layer only as a cross-check, as was done here.

At the pinned commit NE ships 31 point-of-view layers (`ne_10m_admin_0_countries_<pov>.geojson`, about 13 MB each, built from the `ADM0_A3_<pov>` fields). I scored each POV on the 23 contested units the decision assigns (table below).

- **South Korea (`KO`) is the only full match**, 23/23. I also made a one-off geometric check against the KO layer, fetched to a scratch directory and not pinned; the survey script does not repeat it. Eight of the nine composed states had a symmetric difference of 0 km². Israel differs by 18 km², because KO gives Shebaa Farms to Lebanon.
- **KO also differs from NE's default elsewhere:**
  - Abu Musa goes to the UAE.
  - Bajo Nuevo and Serranilla go to Colombia.
  - The Paracels are split from China.
  - Abyei and Ilemi stay detached.

  None of these is ours to decide.
- **No UN or World Bank view.** NE leaves `ADM0_A3_UN` and `ADM0_A3_WB` at `-99`.

| POV | Matches | Mismatches (unit → POV owner) |
|---|---|---|
| KO | 23/23 |  |
| AR | 22/23 | A0 `1159321007` Kosovo → SRB |
| BD | 22/23 | A0 `1159321335` Taiwan → CHN |
| BR | 22/23 | DA `1159320905` Golan Heights → B16 |
| DE | 22/23 | DA `1159320905` Golan Heights → B16 |
| EG | 22/23 | A0 `1159321335` Taiwan → CHN |
| IL | 22/23 | DA `1159320905` Golan Heights → ISR |
| IT | 22/23 | DA `1159320905` Golan Heights → B16 |
| PT | 22/23 | DA `1159320905` Golan Heights → B16 |
| SE | 22/23 | DA `1159320905` Golan Heights → B16 |
| VN | 22/23 | A0 `1159321007` Kosovo → SRB |
| ES | 21/23 | DA `1159320905` Golan Heights → B16; A0 `1159321007` Kosovo → SRB |
| GR | 21/23 | DA `1159320905` Golan Heights → B16; A0 `1159321007` Kosovo → SRB |
| JP | 21/23 | DA `1159320905` Golan Heights → B16; DA `1159321213` Kuril Is. → JPN |
| SA | 21/23 | DA `1159321037` W. Sahara → MAR; A0 `1159321223` W. Sahara → MAR |
| UA | 21/23 | DA `1159320905` Golan Heights → B16; A0 `1159321007` Kosovo → SRB |
| FR | 20/23 | DA `1159320905` Golan Heights → B16; DA `1159321037` W. Sahara → MAR; A0 `1159321223` W. Sahara → MAR |
| NL | 20/23 | DA `1159320905` Golan Heights → B16; DA `1159321037` W. Sahara → MAR; A0 `1159321223` W. Sahara → MAR |
| PK | 20/23 | DA `1159320869` Jammu and Kashmir → PAK; A0 `1159321335` Taiwan → CHN; A0 `1159320963` Siachen Glacier → PAK |
| PL | 20/23 | DA `1159320905` Golan Heights → B16; DA `1159321037` W. Sahara → MAR; A0 `1159321223` W. Sahara → MAR |
| PS | 20/23 | DA `1159321037` W. Sahara → MAR; A0 `1159321223` W. Sahara → MAR; A0 `1159321007` Kosovo → SRB |
| CN | 19/23 | DA `1159321213` Kuril Is. → JPN; DA `1159320857` Arunachal Pradesh → CHN; A0 `1159321007` Kosovo → SRB; A0 `1159321335` Taiwan → CHN |
| GB | 19/23 | DA `1159320785` Abkhazia → B35; DA `1159320787` South Ossetia → B37; DA `1159320905` Golan Heights → B16; A0 `1159321007` Kosovo → SRB |
| ID | 19/23 | DA `1159321037` W. Sahara → MAR; A0 `1159321223` W. Sahara → MAR; A0 `1159321007` Kosovo → SRB; A0 `1159321335` Taiwan → CHN |
| MA | 19/23 | DA `1159321037` W. Sahara → MAR; A0 `1159321223` W. Sahara → MAR; A0 `1159321007` Kosovo → SRB; A0 `1159321335` Taiwan → CHN |
| NP | 19/23 | DA `1159321157` Azad Kashmir → IND; DA `1159321155` Gilgit-Baltistan → IND; A0 `1159321007` Kosovo → SRB; A0 `1159321335` Taiwan → CHN |
| US | 19/23 | DA `1159320785` Abkhazia → B35; DA `1159320787` South Ossetia → B37; DA `1159320905` Golan Heights → ISR; A0 `1159320963` Siachen Glacier → B45 |
| TR | 18/23 | DA `1159320869` Jammu and Kashmir → PAK; DA `1159321037` W. Sahara → MAR; A0 `1159321223` W. Sahara → MAR; A0 `1159320531` N. Cyprus → CYN; A0 `1159320963` Siachen Glacier → PAK |
| TW | 18/23 | DA `1159321213` Kuril Is. → JPN; DA `1159320857` Arunachal Pradesh → TWN; DA `1159320487` Aksai Chin → TWN; DA `1159320485` Shaksam Valley → TWN; A0 `1159321259` Somaliland → SOL |
| IN | 16/23 | DA `1159321157` Azad Kashmir → IND; DA `1159321155` Gilgit-Baltistan → IND; DA `1159320487` Aksai Chin → IND; DA `1159320485` Shaksam Valley → IND; DA `1159321037` W. Sahara → MAR; A0 `1159321223` W. Sahara → MAR; A0 `1159321007` Kosovo → SRB |
| RU | 14/23 | DA `1159321217` Crimea → RUS; DA `1763286545` Donetsk People's Republic → C02; DA `1763286547` Luhansk People's Republic → C03; DA `1159320785` Abkhazia → B35; DA `1159320787` South Ossetia → B37; DA `1159321157` Azad Kashmir → IND; DA `1159321155` Gilgit-Baltistan → IND; A0 `1159321007` Kosovo → SRB; A0 `1159321335` Taiwan → CHN |
| UN | 0/23 | DA `1159321217` Crimea → -99; DA `1763286545` Donetsk People's Republic → -99; DA `1763286547` Luhansk People's Republic → -99; DA `1159320785` Abkhazia → -99; DA `1159320787` South Ossetia → -99; DA `1159321047` Transnistria → -99; DA `1159320905` Golan Heights → -99; DA `1159321213` Kuril Is. → -99; DA `1159320869` Jammu and Kashmir → -99; DA `1159320857` Arunachal Pradesh → -99; DA `1159321157` Azad Kashmir → -99; DA `1159321155` Gilgit-Baltistan → -99; DA `1159320487` Aksai Chin → -99; DA `1159320485` Shaksam Valley → -99; DA `1159321037` W. Sahara → -99; DA `1159320821` West of Essequibo River → -99; A0 `1159321223` W. Sahara → -99; A0 `1159320531` N. Cyprus → -99; A0 `1159321259` Somaliland → -99; A0 `1159321007` Kosovo → -99; A0 `1159321335` Taiwan → -99; A0 `1159320899` Palestine → -99; A0 `1159320963` Siachen Glacier → -99 |
| WB | 0/23 | DA `1159321217` Crimea → -99; DA `1763286545` Donetsk People's Republic → -99; DA `1763286547` Luhansk People's Republic → -99; DA `1159320785` Abkhazia → -99; DA `1159320787` South Ossetia → -99; DA `1159321047` Transnistria → -99; DA `1159320905` Golan Heights → -99; DA `1159321213` Kuril Is. → -99; DA `1159320869` Jammu and Kashmir → -99; DA `1159320857` Arunachal Pradesh → -99; DA `1159321157` Azad Kashmir → -99; DA `1159321155` Gilgit-Baltistan → -99; DA `1159320487` Aksai Chin → -99; DA `1159320485` Shaksam Valley → -99; DA `1159321037` W. Sahara → -99; DA `1159320821` West of Essequibo River → -99; A0 `1159321223` W. Sahara → -99; A0 `1159320531` N. Cyprus → -99; A0 `1159321259` Somaliland → -99; A0 `1159321007` Kosovo → -99; A0 `1159321335` Taiwan → -99; A0 `1159320899` Palestine → -99; A0 `1159320963` Siachen Glacier → -99 |

## (e) Stale shapes

None of the stale shapes changes a recognised-border country outline: each lies inside the A0 row of the state the decision assigns it to. They matter for dashed lines and blurbs.

- **Artsakh** (DA `1159320385`, 3,136 km²): Azerbaijan retook it in September 2023, and the de facto republic dissolved on 1 January 2024. `boundary_lines_disputed_areas` still has 22 Nagorno-Karabakh segments: the 2020 ceasefire line and the 1991 oblast reference lines. **Exclude them** from the dashed layer.
- **Donetsk and Luhansk** (DA `1763286545`, `1763286547`; 9,451 and 8,306 km²): these are the 2014–22 lines, while the full oblasts are about 26,500 km² each. Three line rows draw them: `1763286563`, `1763286519` and `1763286559`. **Exclude them** too. NE has no shape for the post-2022 occupation; the plan already leaves those areas off the cards.
- **Somaliland** (A0/DA `1159321259`): the outline still includes Las Anod (`populated_places` `1159121875` *Laascaanood*, tagged `SOL`), which SSC-Khatumo has held since August 2023 (**verify**). Erigavo (`1159121897`) also sits inside the outline in eastern Sanaag, an area SSC-Khatumo claims (**verify**). Per decision 10, keep NE's outline and mention Las Anod in the blurb.
- **Other:**
  - Hans Island (DA `1159320559`) is still drawn as a Canada–Denmark dispute, which the 2022 agreement settled. It has no card and no line.
  - Kazakhstan's capital is still named Nur-Sultan; see (a).

| Layer `ne_id` | NE name | Type | km² | NE note |
|---|---|---|---|---|
| DA `1159320385` | Artsakh | Breakaway | 3,136 | Self admin.; Claimed by Azer. |
| DA `1763286545` | Donetsk People's Republic | Breakaway | 9,451 | Self admin.; Claimed by Ukraine |
| DA `1763286547` | Luhansk People's Republic | Breakaway | 8,306 | Self admin.; Claimed by Ukraine |
| A0 `1159321259` | Somaliland | Sovereign country | 167,407 | Self admin.; Claimed by Somalia |

| Lines `ne_id` | Class | Name | km |
|---|---|---|---|
| 1746705365 | Reference line | Former USSR oblast in 1991 | 27 |
| 1746705369 | Reference line | Former USSR oblast in 1991 | 30 |
| 1746705489 | Breakaway | Ceasefire Line 2020 | 20 |
| 1746705567 | Reference line | Former USSR oblast in 1991 | 134 |
| 1746705575 | Reference line | Former USSR oblast in 1991 | 46 |
| 1746705583 | Reference line | Former USSR oblast in 1991 | 42 |
| 1746705589 | Breakaway | Ceasefire Line 2020 | 12 |
| 1746705599 | Reference line | Former USSR oblast in 1991 | 12 |
| 1763286563 | Breakaway | Donetsk claim | 191 |
| 1746705625 | Reference line | Former USSR oblast in 1991 | 185 |
| 1746705669 | Breakaway | Ceasefire Line 2020 | 11 |
| 1746705677 | Breakaway | Ceasefire Line 2020 | 10 |
| 1746705687 | Breakaway | Ceasefire Line 2020 | 5 |
| 1746705695 | Breakaway | Ceasefire Line 2020 | 52 |
| 1746705703 | Breakaway | Ceasefire Line 2020 | 16 |
| 1746705713 | Reference line | Former USSR oblast in 1991 | 7 |
| 1746705727 | Reference line | Former USSR oblast in 1991 | 49 |
| 1746705737 | Breakaway | Ceasefire Line 2020 | 134 |
| 1746705745 | Breakaway | Ceasefire Line 2020 | 46 |
| 1746705757 | Breakaway | Ceasefire Line 2020 | 49 |
| 1746705769 | Breakaway | Ceasefire Line 2020 | 12 |
| 1746705781 | Breakaway | Ceasefire Line 2020 | 28 |
| 1763286519 | Breakaway | Donbass claim | 115 |
| 1763286559 | Breakaway | Luhansk claim | 135 |

- populated_places `1159121875` Laascaanood: ADM0_A3 SOL, inside A0 Somaliland: True
- populated_places `1159121897` Ceerigaabo: ADM0_A3 SOL, inside A0 Somaliland: True

## (f) Continents

`ne_10m_geography_regions_polys` (already vendored) has exactly seven `FEATURECLA = Continent` rows. They are coarse landmass polygons, not unions of countries:

- **Most islands are missing:**
  - the British Isles, Iceland and Madagascar;
  - Indonesia south of about 1° N;
  - the Caribbean;
  - New Zealand and New Guinea.
- **Some islands are included:** Japan is in Asia and Greenland in North America.
- **Europe and Asia overlap** in the Caucasus (Baku falls in both).

**Oceania.** The `AUSTRALIA` row (`REGION` Oceania) covers Australia and Tasmania only, so an "Oceania" card drawn from it would outline Australia alone. Two options:

- **Option 1:** use this row as decision 7 says, and accept that the "Oceania" outline is Australia.
- **Option 2:** draw Oceania as the union of the 26 A0 rows with `CONTINENT = Oceania`, from PNG and New Zealand to the Pacific states and territories. This departs from decision 7 and mixes a political union with six landmass polygons, so it needs the user's sign-off (an ADR amendment), not a P2 call.

The other six continents can use their rows as they are; their missing islands are the usual convention for continent outlines. The Europe–Asia overlap in the Caucasus will trip the sibling and nesting checks in 2.6 and needs an owner (see below).

## Open decisions

None of these blocks P2 from starting; each blocks the rows it names.

| Item | Default in this doc | Decider |
|---|---|---|
| Benin, Tanzania, Sri Lanka capitals | NE tag (Cotonou, Dar es Salaam, Colombo) | user (P2.2 should not ship them before this) |
| Nauru capital | none | user: drop the card, or allow one hand-placed point |
| Shebaa Farms | stays with Israel | user; following the Golan decision would move it to Syria |
| East Jerusalem and the no-man's-land strips (122 km²) | stay with Israel | user |
| Baikonur → Kazakhstan, Guantanamo → Cuba | composed in | user to confirm |
| UK sovereign base areas | UK holes in Cyprus | user to confirm |
| Oceania outline | option 1 (Australia row) | user (ADR amendment for option 2) |
| Europe–Asia overlap in the Caucasus | unresolved | P2.6 |
| Adjacency geometry (P2.5) | card outlines (map units for France, Netherlands, Norway, New Zealand), so no France–Brazil or France–Suriname edge | P2.5, confirm with user |

After P2.1 lands, P2's data files (`countries.yaml`, `territories.yaml`, the political model) become the source of truth for these mappings. This doc and `tools/ne_survey.py` then serve as the record and a cross-check.

| `ne_id` | NAME | REGION | km² | bbox |
|---|---|---|---|---|
| 1159104361 | SOUTH AMERICA | South America | 17,538,460 | -81, -56, -35, 12 |
| 1159104363 | AUSTRALIA | Oceania | 7,691,184 | 113, -44, 154, -10 |
| 1159104365 | AFRICA | Africa | 29,262,690 | -17, -35, 51, 37 |
| 1159104367 | ANTARCTICA | Antarctica | 12,347,224 | -180, -90, 180, -61 |
| 1159104597 | ASIA | Asia | 41,623,127 | -180, 1, 180, 81 |
| 1159104603 | EUROPE | Europe | 9,394,151 | -9, 35, 66, 71 |
| 1159104607 | NORTH AMERICA | North America | 23,215,905 | -178, 16, 180, 84 |

- Hobart (`1159151171`) is in: AUSTRALIA
- Port Moresby (`1159150663`) is in: none
- Wellington (`1159151699`) is in: none
- London (`1159151577`) is in: none
- Dublin (`1159151309`) is in: none
- Reykjavík (`1159150587`) is in: none
- Tokyo (`1159151609`) is in: ASIA
- Jakarta (`1159151599`) is in: none
- Antananarivo (`1159150835`) is in: none
- Havana (`1159151347`) is in: none
- Nuuk (`1159150939`) is in: NORTH AMERICA
- Moscow (`1159151585`) is in: EUROPE
- Istanbul (`1159151579`) is in: EUROPE
- Tbilisi (`1159150961`) is in: ASIA
- Baku (`1159151123`) is in: ASIA, EUROPE
- Yerevan (`1159151119`) is in: ASIA
- Cairo (`1159151603`) is in: AFRICA
- Panama City (`1159150667`) is in: none
