# Major cities: a selection for the World Atlas deck

Prepared 2026-10-14 for the city cards in [world-atlas-plan.md](../world-atlas-plan.md) (open decision 3; pass placement in "Placing each card type"). It follows the lens of [research-independent.md](research-independent.md): significance first, population never on its own. No existing deck or list was consulted.

**Source tags** (same scheme as research-independent.md):
- **[V]**: the page was opened and the claim read there.
- **[S]**: confirmed from search-indexed text of the named source only. britannica.com and whc.unesco.org returned HTTP 403 to every direct fetch this session, so every Britannica and UNESCO key is [S].
- **NE** and **WD**: the `NE_ID` and `WIKIDATAID` columns were read from the vendored `ne_10m_populated_places.geojson` (Natural Earth v5.1.2). Every WIKIDATAID was resolved through the Wikidata API on 2026-10-14, and each label matched the city (WD-API [V]).

**No figures.** No population, tonnage or ranking number appears in any row. Where a row makes a ranking claim without a number ("Germany's largest port"), the source key carries it, and the claim is listed in [Verify before carding](#verify-before-carding) when it rests on [S] or on an organisation's description of itself.

## Criteria

A city qualifies if it meets at least one of these:

1. **History:** it shaped trade, war, religion or settlement. Examples: a capital of a historic empire, a decisive siege or battle, a trade-route terminus, a holy city.
2. **Economy now:** it is a top-tier commercial, financial or port hub of its country or continent.

**Rules:**
- **Population alone never qualifies a city.**
- **Current national capitals are excluded**, because they already have cards. This includes every seat that the plan's "several capitals" decision might card, apart from the exceptions in [Held out](#held-out-pending-plan-decisions).
- **Former capitals are eligible:** Lagos, Istanbul, Rio, Kyoto, Almaty, Karachi, Kolkata, Yangon, Melbourne, Auckland, Salvador, Dar es Salaam, Ho Chi Minh City.
- **Territory capitals are excluded** (San Juan, Willemstad, Nouméa and so on), as are the SAR cities (Hong Kong, Macau). They belong with the territory cards.

**Tiering.** Core (pass 1) means the city is indispensable to the region's story or a world-scale hub today. Secondary (pass 2) means real but narrower.

The core set aims for spread rather than equal shares. Every region except 2, 12 and 21 has at least one core city. Those three get secondary cities only:
- **Region 2 (Nordic & Baltic):** Bergen and Gothenburg matter regionally, and none of the region's world-tier cities (Stockholm, Copenhagen, Helsinki, Oslo, the Baltic capitals) is eligible, because all are capitals.
- **Region 12 (Central Africa):** most of the region's most significant cities are capitals (Kinshasa, Brazzaville, Yaoundé). Douala and Lubumbashi are important but national, not world, hubs.
- **Region 21 (Caribbean):** the main city of every sovereign state is its capital (Havana, Kingston, Santo Domingo, Port-au-Prince). The other major cities are territory capitals (San Juan, Willemstad, Fort-de-France), which are excluded. Cap-Haïtien and Santiago de Cuba carry the Haitian Revolution and 1898 and 1953 history.

No region is empty.

## Counts

| # | Region | Core | Secondary | Total |
|---|---|---|---|---|
| 1 | Western Europe | 3 | 6 | 9 |
| 2 | Nordic & Baltic | 0 | 2 | 2 |
| 3 | Central Europe & Italy | 5 | 7 | 12 |
| 4 | Balkans | 1 | 1 | 2 |
| 5 | Eastern Europe | 3 | 5 | 8 |
| 6 | Caucasus & Anatolia | 1 | 2 | 3 |
| 7 | Levant & Mesopotamia | 1 | 2 | 3 |
| 8 | Arabian Peninsula | 2 | 3 | 5 |
| 9 | Horn & East Africa | 2 | 1 | 3 |
| 10 | North Africa | 2 | 4 | 6 |
| 11 | West Africa | 2 | 3 | 5 |
| 12 | Central Africa | 0 | 2 | 2 |
| 13 | Southern Africa & Indian Ocean | 2 | 1 | 3 |
| 14 | South Asia | 4 | 7 | 11 |
| 15 | Iran & Central Asia | 3 | 5 | 8 |
| 16 | East Asia | 7 | 9 | 16 |
| 17 | Southeast Asia | 3 | 6 | 9 |
| 18 | Oceania | 3 | 2 | 5 |
| 19 | North & Central America | 7 | 11 | 18 |
| 20 | South America | 4 | 6 | 10 |
| 21 | Caribbean | 0 | 2 | 2 |
| | **Total** | **55** | **87** | **142** |

The plan's pacing table assumed 55 core cities, so the count matches. With 87 secondary cities, pass 2 is larger than the plan's "about 65" for features plus secondary cities. To trim, cut secondary rows from the densest regions first (19, 16, 3, 14).

## Flags

Flag codes in the table:
- **P:** within about 150 km of a national capital (any NE `populated_places` row with `ADM0CAP = 1` or `FEATURECLA` starting "Admin-0 capital").
- **N:** within about 150 km of another listed city.
- **T:** within about 150 km of a territory or SAR dot (Hong Kong, Macau, Gibraltar, Douglas). These are NE "Admin-0 region capital" rows of carded territories.
- **D:** in a disputed area.
- **(edge):** 150–165 km, included so the dot-spacing check sees it.

Distances are great-circle distances between NE point coordinates (computed). **The plan's dot-spacing check must handle every P, N and T pair.**

**Disputed:**
- **Sevastopol** is in Crimea, internationally recognised as Ukraine and occupied by Russia since 2014. It is one of the plan's 15 dispute cards. NE's `populated_places` row puts it under `ADM0NAME = Russia` (de facto). Under the plan's recognised-borders rule, the card back should say "Ukraine (Russian-occupied)".
- **Not flagged, with reasons:**
  - **Antakya** is in Hatay. Syria's historic claim is not on the plan's List 2.
  - **Lhasa** is in Tibet, which is not on List 2.
  - **Odesa and Lviv** are in Ukrainian-controlled territory as of the research date. The front is not checked.

**NE capital markers that collide with listed cities:** Dar es Salaam (`ADM0CAP = 1`), Cape Town (`ADM0CAP = 1`), Johannesburg (`FEATURECLA` "Admin-0 capital"), Yangon (`FEATURECLA` "Admin-0 capital"), and Lagos, Kyoto and Valparaíso ("Admin-0 capital alt"). The country/capital build must not pick these rows as the capital dot:
- **Tanzania:** Dodoma is the official capital (BRIT-DODOMA, BRIT-TANZANIA-FACTS [S]). NE's Dodoma row is `FEATURECLA` "Admin-0 capital alt", `ADM0CAP = 0`.
- **Côte d'Ivoire:** Yamoussoukro is the official capital, named in 1983 (BRIT-YAMOUSSOUKRO [S]). NE marks both Yamoussoukro and Abidjan `ADM0CAP = 1`.
- **Myanmar:** Naypyidaw has been capital since 2006 (BRIT-YANGON, BRIT-MYANMAR [S]).
- **Chile:** Santiago is the capital. Congress has sat in Valparaíso since 1990 (SENADO-CONGRESO [V], BCN-EDIFICIO [V]).

## Held out pending plan decisions

- **Cape Town** is listed as core but is South Africa's legislative capital (ZAGOV-CAPITALS [V]). **Resolved (PM decision, 2026-10-14):** South Africa's capital card is Pretoria only, so Cape Town stays a city card.
- **Not listed because they are capitals, or may become capital dots:**
  - **Jerusalem:** Israel's claimed capital; East Jerusalem is Palestine's claimed capital.
  - **Amsterdam and The Hague** (Netherlands).
  - **La Paz** (Bolivia's seat of government: BRIT-LAPAZ [S]; Sucre is the constitutional capital: CPE-BOLIVIA [V], Art. 6.I).
  - **Colombo:** Sri Jayawardenepura Kotte is the official capital (KOTTE-MC [V]); Britannica calls Colombo the executive and judicial capital (BRIT-COLOMBO [S]).
  - **Jakarta:** still the legal capital until a presidential decree moves it to Nusantara. The Constitutional Court ruled this on 12 May 2026, and no decree was found through mid-October 2026 (MKRI-CAPITAL [S], Decision 71/PUU-XXIV/2026). **Re-check before shipping.**
  - If the plan settles any of these on a single other dot (for example Colombo not carded as capital), the city becomes a candidate here.
- **Hong Kong and Macau** go with the territory cards, per the plan.
- **Removed after fact-check, because each is a current seat of government, then re-added** (see the rows in regions 8 and 11):
  - **Aden** is the internationally recognised government's declared temporary or interim capital of Yemen. Wikidata Q131694 describes it as "temporary capital of Yemen", and the Presidential Leadership Council's site calls it the "interim capital" (PLC-ADEN [S]). Sanaa is the constitutional capital. **Re-added as a secondary city by PM decision (2026-10-14):** the Yemen capital card is Sanaa, the constitutional capital.
  - **Abidjan** remains the administrative capital and seat of government (BRIT-COTEDIVOIRE [S]; CIA-CI [S]). **Re-added as a secondary city by PM decision (2026-10-14):** the Côte d'Ivoire capital card is Yamoussoukro only.
- **Valparaíso stays** as a secondary city. It hosts Congress (SENADO-CONGRESO [V]) but is not a capital: Santiago is. Cape Town is different, because it is constitutionally one of South Africa's three capitals. Treat them alike only if the plan decides that seats of a branch count as capitals.

## The list

Within each region, core rows come first; the in-region order is set later by the walk and anchoring rules, not here. "Why it matters" is 12 words or fewer.

### 1. Western Europe

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Barcelona | Spain | core | Catalan Mediterranean port; medieval Crown of Aragon trading hub | 1159151261 | Q1492 | BRIT-BARCELONA [S]; BRIT-SPAIN-ARAGON [S] | P: Andorra la Vella (NE: Andorra) 136 km |
| Marseille | France | core | Greek-founded Massalia; France's main Mediterranean port | 1159150037 | Q23482 | BRIT-MARSEILLE [S] |  |
| Rotterdam | Netherlands | core | Europe's largest port at the Rhine–Maas mouth | 1159146435 | Q34370 | PORT-ROTTERDAM [V]; BRIT-ROTTERDAM [S] | P: The Hague 23 km, Amsterdam 56 km, Brussels 121 km; N: Antwerp 78 km |
| Antwerp (NE: Antwerpen) | Belgium | secondary | 16th-century commercial and financial capital of Europe, on the Scheldt | 1159147705 | Q12892 | BRIT-ANTWERP [S] | P: Brussels 43 km, The Hague 96 km, Amsterdam 130 km; N: Rotterdam 78 km |
| Seville | Spain | secondary | Held the Crown's monopoly on Americas trade | 1159150601 | Q8717 | BRIT-CASA-CONTRATACION [S]; BRIT-SEVILLA [S] | T (edge): Gibraltar 151 km |
| Porto | Portugal | secondary | Port-wine city on the Douro; gave Portugal its name | 1159146429 | Q36433 | BRIT-PORTO [S]; BRIT-PORT-WINE [S] |  |
| Lyon | France | secondary | Roman Lugdunum; silk capital at Rhône–Saône confluence | 1159150845 | Q456 | BRIT-LYON [S]; BRIT-TEXTILE [S] | N: Geneva 112 km |
| Manchester | United Kingdom | secondary | Cotton mills of the Industrial Revolution | 1159149119 | Q18125 | BRIT-MANCHESTER [S] | N: Liverpool 45 km; T (edge): Douglas (Isle of Man) 163 km |
| Liverpool | United Kingdom | secondary | Atlantic slave-trade and emigration port | 1159146371 | Q24826 | BRIT-LIVERPOOL [S] | N: Manchester 45 km; T: Douglas (Isle of Man) 131 km |

### 2. Nordic & Baltic

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Bergen | Norway | secondary | Hanseatic League stockfish kontor | 1159150643 | Q26793 | UNESCO-BRYGGEN [S]; BRIT-HANSEATIC [S] |  |
| Gothenburg (NE: Göteborg) | Sweden | secondary | Sweden's chief seaport, on the Kattegat | 1159148253 | Q25287 | BRIT-GOTHENBURG [S]; PORT-GOTHENBURG [V] |  |

### 3. Central Europe & Italy

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Hamburg | Germany | core | Hanseatic port on the Elbe; Germany's largest port | 1159151353 | Q1055 | BRIT-HAMBURG [S] |  |
| Frankfurt | Germany | core | Imperial coronation city; continental finance hub, ECB seat | 1159151351 | Q1794 | BRIT-FRANKFURT [S]; BRIT-ECB [S] |  |
| Milan | Italy | core | Lombardy's capital; Italy's finance and industry hub | 1159151315 | Q490 | BRIT-MILAN [S] | N: Genoa 120 km |
| Venice | Italy | core | Maritime republic that dominated Levant trade | 1159150277 | Q641 | BRIT-VENICE [S] |  |
| Florence | Italy | core | Medici banking; cradle of the Renaissance | 1159149751 | Q2044 | UNESCO-FLORENCE [S]; BRIT-FLORENCE [S] | P: San Marino 97 km |
| Naples | Italy | secondary | Capital of the Kingdom of Naples; below Vesuvius | 1159151313 | Q2634 | BRIT-NAPLES [S]; BRIT-KINGDOM-NAPLES [S] |  |
| Genoa | Italy | secondary | Maritime republic; Columbus's birthplace; northern Italy's chief sea outlet | 1159148297 | Q1449 | BRIT-GENOA [S]; BRIT-COLUMBUS [S] | P: Monaco 143 km; N: Milan 120 km |
| Kraków | Poland | secondary | Former royal capital of Poland | 1159149709 | Q31487 | UNESCO-KRAKOW [S]; BRIT-KRAKOW [S] |  |
| Gdańsk | Poland | secondary | Hanseatic Danzig; WWII's first shots at Westerplatte; Solidarity's birthplace | 1159149707 | Q1792 | BRIT-GDANSK [S]; BRIT-INVASION-POLAND [S] |  |
| Geneva | Switzerland | secondary | Calvinist Reformation; seat of UN and Red Cross bodies | 1159151505 | Q71 | BRIT-GENEVA [S]; ICRC-STATUTES [S] | P: Bern 128 km; N: Lyon 112 km |
| Zürich | Switzerland | secondary | Swiss finance hub; Zwingli's Reformation | 1159151271 | Q72 | BRIT-ZURICH [S] | P: Vaduz 78 km, Bern 97 km |
| Munich | Germany | secondary | Bavarian capital; Munich Agreement 1938 | 1159151357 | Q1726 | BRIT-MUNICH-AGREEMENT [S] |  |

### 4. Balkans

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Thessaloniki | Greece | core | Byzantine–Ottoman Salonica; Aegean port of the Balkans | 1159150955 | Q17151 | BRIT-THESSALONIKI [S]; UNESCO-THESSALONIKI [S] |  |
| Dubrovnik | Croatia | secondary | Ragusa, the Adriatic merchant republic | 1159140359 | Q1722 | BRIT-DUBROVNIK [S]; UNESCO-DUBROVNIK [S] | P: Podgorica 99 km, Sarajevo 134 km |

### 5. Eastern Europe

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Saint Petersburg (NE: St. Petersburg) | Russia | core | Peter the Great's Baltic capital; 1917 revolutions | 1159151291 | Q656 | BRIT-STPETERSBURG [S] |  |
| Odesa (NE: Odessa) | Ukraine | core | Black Sea grain port founded by Catherine II | 1159149325 | Q1874 | UNESCO-ODESA [S] | P (edge): Chișinău 152 km |
| Volgograd | Russia | core | Stalingrad, WWII turning point on the Volga | 1159150697 | Q914 | BRIT-STALINGRAD [S] |  |
| Vladivostok | Russia | secondary | Pacific naval port; Trans-Siberian terminus | 1159150739 | Q959 | BRIT-VLADIVOSTOK [S] |  |
| Sevastopol | Ukraine (Russian-occupied since 2014) | secondary | Black Sea Fleet base; Crimean War siege | 1159150561 | Q7525 | BRIT-SIEGE-SEVASTOPOL [S] | D: Crimea (dispute card) |
| Yekaterinburg | Russia | secondary | Urals industrial hub; Romanovs killed here | 1159150701 | Q887 | BRIT-YEKATERINBURG [S] |  |
| Murmansk | Russia | secondary | Ice-free Arctic port; WWII Allied convoy destination | 1159150691 | Q1763 | BRIT-MURMANSK [S] |  |
| Lviv | Ukraine | secondary | Habsburg Lemberg; Galicia's cultural capital | 1159149323 | Q36036 | BRIT-LVIV [S]; UNESCO-LVIV [S] |  |

### 6. Caucasus & Anatolia

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Istanbul | Turkey | core | Byzantium/Constantinople; capital of two empires on the Bosporus | 1159151579 | Q406 | BRIT-ISTANBUL [S] |  |
| Izmir (NE: İzmir) | Turkey | secondary | Smyrna; cosmopolitan Ottoman trading port; burned 1922 | 1159149371 | Q35997 | BRIT-IZMIR [S] |  |
| Antakya | Turkey | secondary | Antioch, Seleucid capital and early Christian centre | 1159113499 | Q80561 | BRIT-ANTIOCH [S] | N: Aleppo 94 km |

### 7. Levant & Mesopotamia

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Aleppo | Syria | core | Ancient caravan-route trade city; Old City ruined in civil war | 1159151267 | Q41183 | UNESCO-ALEPPO [S]; BRIT-ALEPPO [S] | N: Antakya 94 km |
| Mosul | Iraq | secondary | Opposite Nineveh; held by ISIS 2014–17 | 1159150087 | Q83317 | BRIT-MOSUL [S]; BRIT-NINEVEH [S] |  |
| Basra | Iraq | secondary | Iraq's port on the Shatt al-Arab | 1159150127 | Q48195 | BRIT-BASRA [S] | P: Kuwait City 128 km |

### 8. Arabian Peninsula

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Mecca (NE: Makkah) | Saudi Arabia | core | Islam's holiest city; Hajj destination | 1159151279 | Q5806 | BRIT-MECCA [S] | N: Jeddah 63 km |
| Dubai | United Arab Emirates | core | Gulf trade, aviation and finance hub | 1159151497 | Q612 | BRIT-DUBAI [S] | P: Abu Dhabi 125 km |
| Medina | Saudi Arabia | secondary | Muhammad's city after the Hijra; Islam's second holiest city | 1159149443 | Q35484 | BRIT-MEDINA [S] |  |
| Jeddah | Saudi Arabia | secondary | Red Sea gateway for Mecca pilgrims | 1159151277 | Q374365 | UNESCO-JEDDAH [S] | N: Mecca 63 km |
| Aden | Yemen | secondary | Historic Gulf of Aden port; Yemen government's interim seat | 1159150595 | Q131694 | BRIT-ADEN [S]; PLC-ADEN [S] | Re-added by PM decision; NE `Admin-1 capital` |

### 9. Horn & East Africa

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Mombasa | Kenya | core | Swahili coast port; Fort Jesus; East Africa's gateway | 1159150829 | Q225641 | UNESCO-FORTJESUS [S]; KPA-GATEWAY [S] |  |
| Zanzibar | Tanzania | core | Omani sultanate's capital; slave and clove trade | 1159150789 | Q2222874 | BRIT-ZANZIBAR [S]; UNESCO-STONETOWN [S] | P: Dar es Salaam 71 km (NE ADM0CAP=1; Dodoma is the capital); N: Dar es Salaam 71 km |
| Dar es Salaam | Tanzania | secondary | Former capital; Tanzania's main port and city | 1159151305 | Q1960 | BRIT-DARESSALAAM [S]; BRIT-DODOMA [S] | N: Zanzibar 71 km; NE marks it ADM0CAP=1 (Dodoma is "capital alt") |

### 10. North Africa

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Alexandria | Egypt | core | Alexander's city; the Library and Pharos | 1159151349 | Q87 | BRIT-ALEXANDRIA [S] |  |
| Casablanca | Morocco | core | Morocco's economic capital and main port | 1159151521 | Q7903 | BRIT-CASABLANCA [S] | P: Rabat 86 km |
| Luxor | Egypt | secondary | Ancient Thebes; Valley of the Kings | 1159150871 | Q130514 | UNESCO-THEBES [S] |  |
| Marrakesh | Morocco | secondary | Almoravid capital; market for High Atlas and Saharan trade | 1159150675 | Q101625 | BRIT-MARRAKECH [S]; UNESCO-MARRAKESH [S] |  |
| Fez | Morocco | secondary | Idrisid capital; al-Qarawiyyin university | 1159150669 | Q80985 | UNESCO-FEZ [S]; BRIT-QARAWIYYIN [S] |  |
| Tangier | Morocco | secondary | Strait of Gibraltar port; former international zone | 1159148063 | Q126148 | BRIT-TANGIER [S] | T: Gibraltar 59 km |

### 11. West Africa

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Lagos | Nigeria | core | Former capital; Nigeria's largest city and commercial centre | 1159151591 | Q8673 | BRIT-LAGOS [S] | P: Porto-Novo 86 km, Cotonou 96 km; NE marks it "Admin-0 capital alt" |
| Timbuktu | Mali | core | Trans-Saharan trade and Islamic learning centre | 1159150921 | Q9427 | UNESCO-TIMBUKTU [S]; BRIT-TIMBUKTU [S] |  |
| Kano | Nigeria | secondary | Ancient Hausa city-state; major trans-Saharan trading centre | 1159151297 | Q182984 | BRIT-KANO [S] |  |
| Kumasi | Ghana | secondary | Capital of the Asante Empire | 1159148507 | Q182059 | BRIT-GHANA-HIST [S] |  |
| Abidjan | Côte d'Ivoire | secondary | Côte d'Ivoire's economic hub, main port and seat of government | 1159151439 | Q1515 | BRIT-COTEDIVOIRE [S]; CIA-CI [S] | Re-added by PM decision; NE marks it ADM0CAP=1 (Yamoussoukro is the capital) |

### 12. Central Africa

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Douala | Cameroon | secondary | Cameroon's chief port; gateway for Chad and CAR | 1159149365 | Q132830 | BRIT-DOUALA [S]; PAD-HINTERLAND [S] | P: Malabo 108 km |
| Lubumbashi | Congo (Kinshasa) | secondary | Katanga copper-belt mining capital | 1159150903 | Q187593 | BRIT-LUBUMBASHI [S] |  |

### 13. Southern Africa & Indian Ocean

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Johannesburg | South Africa | core | Witwatersrand gold-rush city; South Africa's financial capital | 1159151515 | Q34647 | BRIT-JOHANNESBURG [S] | P: Pretoria 55 km; NE FEATURECLA "Admin-0 capital" |
| Cape Town | South Africa | core | VOC Cape station; legislative capital of South Africa | 1159151583 | Q5465 | BRIT-CAPETOWN [S]; ZAGOV-CAPITALS [V] | Legislative capital: NE ADM0CAP=1; see note |
| Durban | South Africa | secondary | South Africa's main container port | 1159151289 | Q5468 | TRANSNET-DCT [S] |  |

### 14. South Asia

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Mumbai | India | core | Bombay; India's finance and film capital | 1159151611 | Q1156 | BRIT-MUMBAI [S] |  |
| Kolkata | India | core | Calcutta; capital of British India until 1911–12 | 1159151617 | Q1348 | BRIT-KOLKATA [S] |  |
| Karachi | Pakistan | core | Former capital; Pakistan's port and largest city | 1159151287 | Q8660 | BRIT-KARACHI [S] |  |
| Lahore | Pakistan | core | Mughal royal city; Ranjit Singh's Sikh capital of the Punjab | 1159151285 | Q11739 | BRIT-LAHORE [S]; BRIT-INDIA-SIKHS [S] |  |
| Bengaluru | India | secondary | India's IT and technology hub | 1159151543 | Q1355 | BRIT-BENGALURU [S] |  |
| Chennai | India | secondary | Madras; Fort St George, the EIC's first major Indian fortress | 1159151431 | Q1352 | BRIT-FORTSTGEORGE [S] |  |
| Varanasi | India | secondary | One of Hinduism's seven sacred cities, on the Ganges | 1159150979 | Q79980 | BRIT-VARANASI [S] |  |
| Agra | India | secondary | Mughal capital; Taj Mahal | 1159149175 | Q42941 | BRIT-AGRA [S] |  |
| Hyderabad | India | secondary | Nizams' capital; Golconda diamonds; tech hub | 1159151407 | Q1361 | BRIT-HYDERABAD [S]; BRIT-GOLCONDA [S] |  |
| Peshawar | Pakistan | secondary | Frontier city near the Khyber Pass, gateway from Afghanistan | 1159150651 | Q1113311 | BRIT-PESHAWAR [S]; BRIT-KHYBER [S] | P (edge): Islamabad 154 km |
| Chittagong (NE: Chattogram) | Bangladesh | secondary | Bangladesh's main seaport on the Bay of Bengal | 1159151473 | Q376749 | BRIT-CHITTAGONG [S] |  |

### 15. Iran & Central Asia

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Samarkand | Uzbekistan | core | Silk Road hub; Timur's capital | 1159150569 | Q5753 | UNESCO-SAMARKAND [S]; BRIT-SAMARKAND [S] |  |
| Isfahan | Iran | core | Safavid capital: "Isfahan is half the world" | 1159150971 | Q42053 | BRIT-ISLAMIC-SAFAVIDS [S]; UNESCO-ISFAHAN [S] |  |
| Almaty | Kazakhstan | core | Former capital; Kazakhstan's largest city and economic centre | 1159150969 | Q35493 | BRIT-ALMATY [S] |  |
| Bukhara | Uzbekistan | secondary | Silk Road city; Samanid capital of Islamic learning | 1159149337 | Q5764 | BRIT-BUKHARA [S]; UNESCO-BUKHARA [S] |  |
| Herat | Afghanistan | secondary | Timurid cultural capital under Shah Rokh | 1159150319 | Q45313 | BRIT-SHAHROKH [S]; BRIT-HERATSCHOOL [S] |  |
| Tabriz | Iran | secondary | Ilkhanid capital; Silk Road bazaar | 1159150135 | Q80053 | BRIT-TABRIZ [S]; UNESCO-TABRIZ [S] |  |
| Shiraz | Iran | secondary | City of Hafez and Saadi, near Persepolis | 1159150973 | Q6397066 | BRIT-SHIRAZ [S]; BRIT-PERSEPOLIS [S] |  |
| Mashhad | Iran | secondary | Imam Reza shrine; Iran's chief pilgrimage city | 1159151421 | Q121157 | BRIT-MASHHAD [S] |  |

### 16. East Asia

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Shanghai | China | core | Treaty port at the Yangtze mouth; China's finance hub | 1159151605 | Q8686 | BRIT-SHANGHAI [S] | N (edge): Hangzhou 162 km |
| Guangzhou | China | core | Canton; sole Western trade port 1757–1842 | 1159151331 | Q16572 | BRIT-CANTONSYS [S] | N: Shenzhen 105 km; T: Macau 107 km, Hong Kong 128 km |
| Xi'an (NE: Xian) | China | core | Chang'an, Tang capital; eastern Silk Road terminus | 1159151363 | Q5826 | BRIT-XIAN [S]; UNESCO-SILKROADS [S] |  |
| Kyoto | Japan | core | Imperial capital for over a thousand years | 1159149967 | Q34600 | BRIT-KYOTO [S] | N: Osaka 41 km; NE marks it "Admin-0 capital alt" |
| Osaka (NE: Ōsaka) | Japan | core | Japan's merchant city and Kansai hub | 1159151537 | Q35765 | BRIT-OSAKA [S] | P: Kyoto 41 km (NE "Admin-0 capital alt"); N: Kyoto 41 km |
| Hiroshima | Japan | core | First city destroyed by an atomic bomb, 1945 | 1159151389 | Q34664 | BRIT-HIROSHIMA [S]; UNESCO-HIROSHIMA [S] |  |
| Busan | South Korea | core | Korea's main port; Pusan Perimeter of 1950 | 1159149599 | Q16520 | BRIT-BUSAN [S]; BRIT-KOREANWAR [S] |  |
| Shenzhen | China | secondary | Among China's first Special Economic Zones (1980); high-tech hub | 1159151215 | Q15174 | BRIT-SEZ [S] | N: Guangzhou 105 km; T: Hong Kong 28 km, Macau 71 km |
| Nanjing | China | secondary | Ming and Nationalist capital; 1937 massacre | 1159151385 | Q16666 | BRIT-NANJING [S]; BRIT-NANJINGMASSACRE [S] |  |
| Chongqing | China | secondary | Wartime Nationalist capital on the upper Yangtze | 1159151327 | Q11725 | BRIT-CHONGQING [S] |  |
| Wuhan | China | secondary | Yangtze–Han hub; 1911 Wuchang uprising | 1159151367 | Q11746 | BRIT-WUHAN [S]; BRIT-1911REV [S] |  |
| Tianjin | China | secondary | Beijing's port; treaty port concessions | 1159151381 | Q11736 | BRIT-TIANJIN [S] | P: Beijing 113 km |
| Hangzhou | China | secondary | Southern Song capital; Grand Canal southern end | 1159151387 | Q4970 | BRIT-HANGZHOU [S] | N (edge): Shanghai 162 km |
| Kashgar | China | secondary | Silk Road oasis at the western end of the Tarim Basin | 1159150885 | Q170521 | BRIT-KASHGAR [S] |  |
| Lhasa | China | secondary | Seat of the Dalai Lamas; Potala Palace | 1159150879 | Q5869 | UNESCO-POTALA [S]; BRIT-POTALA [S] |  |
| Nagasaki | Japan | secondary | Japan's only Western window under sakoku; atomic bomb | 1159150893 | Q38234 | BRIT-SAKOKU [S]; BRIT-ATOMICBOMBINGS [S] |  |

### 17. Southeast Asia

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Ho Chi Minh City | Vietnam | core | Saigon; capital of South Vietnam until 1975 | 1159151253 | Q1854 | BRIT-HCMC [S] |  |
| Malacca | Malaysia | core | Sultanate's Strait entrepôt; Portuguese conquest 1511 | 1159148319 | Q61089 | BRIT-MELAKA [S]; UNESCO-MELAKA-GEORGETOWN [S] | P: Putrajaya 99 km, Kuala Lumpur 123 km |
| Yangon | Myanmar | core | Rangoon; former capital and main port | 1159151477 | Q37995 | BRIT-YANGON [S] | NE FEATURECLA "Admin-0 capital" (former); ADM0CAP=0 |
| Surabaya | Indonesia | secondary | East Java's chief port; 1945 Battle of Surabaya | 1159151339 | Q11462 | BRIT-SURABAYA [S] |  |
| Mandalay | Myanmar | secondary | Last royal capital of Burma | 1159150423 | Q185518 | BRIT-MANDALAY [S] |  |
| Cebu | Philippines | secondary | Magellan reached it 1521; first permanent Spanish settlement 1565 | 1159150721 | Q1467 | BRIT-LEGAZPI [S]; BRIT-CEBU [S] |  |
| George Town | Malaysia | secondary | Penang, British free port of 1786 | 1159149765 | Q61092 | UNESCO-MELAKA-GEORGETOWN [S]; BRIT-PENANG [S] |  |
| Huế | Vietnam | secondary | Nguyen dynasty imperial capital | 1159147549 | Q36167 | UNESCO-HUE [S] |  |
| Siem Reap | Cambodia | secondary | Gateway to Angkor, the Khmer capital | 1159150325 | Q11711 | BRIT-ANGKOR [S]; UNESCO-ANGKOR [S] |  |

### 18. Oceania

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Sydney | Australia | core | Founded 1788 as Britain's first Australian penal colony | 1159151623 | Q3130 | BRIT-SYDNEY [S] |  |
| Melbourne | Australia | core | Gold-rush city; seat of federal government 1901–27 | 1159151565 | Q3141 | BRIT-MELBOURNE [S] |  |
| Auckland | New Zealand | core | Former capital; New Zealand's largest city | 1159151703 | Q37100 | BRIT-AUCKLAND [S] |  |
| Perth | Australia | secondary | Indian Ocean capital of Western Australia | 1159151475 | Q3183 | BRIT-PERTH [S] |  |
| Brisbane | Australia | secondary | Queensland's capital and port | 1159151169 | Q34932 | BRIT-BRISBANE [S] |  |

### 19. North & Central America

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| New York | United States of America | core | Leading US financial centre; UN headquarters; immigrant gateway | 1159151575 | Q60 | BRIT-NYC [S]; BRIT-UN [S] | N: Philadelphia 131 km |
| Los Angeles | United States of America | core | Pacific port; Hollywood film industry | 1159151569 | Q65 | BRIT-LA [S] |  |
| Chicago | United States of America | core | Rail and grain hub linking Great Lakes and Mississippi | 1159151491 | Q1297 | BRIT-CHICAGO [S] |  |
| New Orleans | United States of America | core | Lower Mississippi port; key prize of 1803 Louisiana Purchase | 1159151233 | Q34404 | BRIT-NEWORLEANS [S]; BRIT-LAPURCHASE [S] |  |
| San Francisco | United States of America | core | Port transformed by the 1849 California Gold Rush | 1159151479 | Q62 | BRIT-SF [S]; BRIT-GOLDRUSH [S] |  |
| Montreal (NE: Montréal) | Canada | core | New France fur-trade hub on the St Lawrence | 1159151457 | Q340 | BRIT-MONTREAL [S] |  |
| Toronto | Canada | core | Canada's largest city and financial centre | 1159151557 | Q172 | BRIT-TORONTO [S] |  |
| Houston | United States of America | secondary | Oil and petrochemical hub; NASA mission control | 1159151485 | Q16555 | BRIT-HOUSTON [S] |  |
| Boston | United States of America | secondary | Boston Massacre and Tea Party; early flashpoint of the Revolution | 1159151239 | Q100 | BRIT-BOSTONMASSACRE [S]; BRIT-BOSTONTEA [S] |  |
| Philadelphia | United States of America | secondary | Declaration of Independence and Constitution signed here | 1159151243 | Q1345 | UNESCO-PHILADELPHIA [S]; NPS-INDEPENDENCEHALL [V] | N: New York 131 km |
| Miami | United States of America | secondary | Gateway between the US and Latin America | 1159151487 | Q8652 | BRIT-MIAMI [S] |  |
| Detroit | United States of America | secondary | Motor City of mass auto production | 1159151245 | Q12439 | BRIT-DETROIT [S]; BRIT-FORDLINE [S] |  |
| Vancouver | Canada | secondary | Canada's Pacific port; CPR terminus | 1159151555 | Q24639 | BRIT-VANCOUVER [S] |  |
| Quebec City (NE: Québec) | Canada | secondary | Champlain's 1608 founding; Plains of Abraham 1759 | 1159151065 | Q2145 | BRIT-QUEBEC [S]; UNESCO-QUEBEC [S] |  |
| Honolulu | United States of America | secondary | Hawaiian kingdom capital; Pearl Harbor attacked nearby, 1941 | 1159151221 | Q18094 | BRIT-HONOLULU [S] |  |
| Monterrey | Mexico | secondary | Mexico's main iron-and-steel centre, near the Texas border | 1159151527 | Q81033 | BRIT-MONTERREY [S] |  |
| Guadalajara | Mexico | secondary | Jalisco's capital; heart of the mariachi and tequila region | 1159151293 | Q9022 | BRIT-GUADALAJARA [S]; BRIT-JALISCO [S] |  |
| Veracruz | Mexico | secondary | Founded by Cortés 1519; New Spain's chief link to Spain | 1159150763 | Q173270 | BRIT-VERACRUZ [S] |  |

### 20. South America

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| São Paulo | Brazil | core | Coffee-boom city; Latin America's foremost industrial centre | 1159151621 | Q174 | BRIT-SAOPAULO [S] |  |
| Rio de Janeiro | Brazil | core | Capital of Portugal's empire, then Brazil until 1960 | 1159151619 | Q8678 | BRIT-LISBON [S]; BRIT-BRAZILHIST [S] |  |
| Potosí | Bolivia | core | Cerro Rico silver; once the world's largest industrial complex | 1159144841 | Q35045 | UNESCO-POTOSI [S] | P: Sucre 78 km |
| Cusco | Peru | core | Inca imperial capital | 1159150611 | Q5582862 | UNESCO-CUSCO [S] |  |
| Salvador | Brazil | secondary | Brazil's first capital; Atlantic slave-trade port | 1159151453 | Q36947 | UNESCO-SALVADOR [S] |  |
| Manaus | Brazil | secondary | Amazon rubber-boom city | 1159151005 | Q40236 | BRIT-MANAUS [S] |  |
| Valparaíso | Chile | secondary | Chief Pacific port on Strait of Magellan route before Panama Canal | 1159150931 | Q33986 | UNESCO-VALPARAISO [S]; SENADO-CONGRESO [V] | P: Santiago 99 km; NE "Admin-0 capital alt" (seat of Congress) |
| Guayaquil | Ecuador | secondary | Ecuador's main port and largest city | 1159151341 | Q43509 | BRIT-GUAYAQUIL [S]; INEC-GUAYAQUIL [V] |  |
| Cartagena | Colombia | secondary | Fortified Spanish treasure-fleet port | 1159150857 | Q657461 | UNESCO-CARTAGENA [S]; BRIT-TREASUREFLEET [S] |  |
| Medellín | Colombia | secondary | Colombia's industrial city in the Andes | 1159151343 | Q48278 | BRIT-COLHIST [S] |  |

### 21. Caribbean

| City | Country | Tier | Why it matters | `NE_ID` | WIKIDATAID | Sources | Flags |
|---|---|---|---|---|---|---|---|
| Cap-Haïtien | Haiti | secondary | Cap-Français; revolution began nearby; Citadelle Laferrière | 1159146363 | Q216835 | BRIT-CAPHAITIEN [S]; UNESCO-CITADELLE [S] | P: Port-au-Prince 136 km |
| Santiago de Cuba | Cuba | secondary | 1898 Spanish–American War battles; Castro's revolution began | 1159149835 | Q117040 | BRIT-SANJUANHILL [S]; BRIT-CUBANREV [S] |  |

## Verify before carding

These rest on [S] text, on a source's description of itself, or on a judgement call:

1. **Rotterdam, "Europe's largest port":** this is the Port of Rotterdam's own claim (PORT-ROTTERDAM [V]). Independent confirmation, e.g. Eurostat port statistics, was not checked.
2. **Hamburg, "Germany's largest port":** Britannica [S] only.
3. **Gothenburg:** "Scandinavia's largest port" was dropped as a self-claim. "Chief seaport" is Britannica [S].
4. **Durban:** reduced to "South Africa's main container port". Transnet's "Africa's biggest and busiest container terminal" was not used; it is probably out of date.
5. **Kolkata:** the move was announced on 12 Dec 1911 and took effect in 1912, so the row says "1911–12".
6. **Guangzhou, "1757–1842":** Britannica dates the Canton system to 1757 in one article and 1759/1760 elsewhere.
7. **Zanzibar:** the year the Omani capital moved there is 1832 in one Britannica entry and 1824 in another. No year is used in the row.
8. **Veracruz:** "Founded by Cortés 1519" is safe. Britannica disagrees with itself on where Cortés first landed, so the row avoids "landing".
9. **Sydney:** "largest city" was dropped. ABS figures show Melbourne's urban area ahead since 2018, while Sydney leads on the wider metro measure (ABS-POP [V]).
10. **Yekaterinburg, "Urals industrial hub":** not seen verbatim in a source snippet. Low risk.
11. **Herat:** "Silk Road crossroads" was dropped as unconfirmed. The row now rests on the Timurid capital (Shah Rokh).
12. **Malacca, Medellín, Siem Reap:** the wording is supported by inference, not verbatim. "Gateway to Angkor" rests on Britannica placing Angkor just north of the town.
13. **Sevastopol, Crimea:** the status is as of the research date. Re-check before shipping.
14. **Every date in a row is [S] (Britannica or UNESCO search text).** Fact-check re-confirmed 1519, 1565, 1901–27, 2014–17, 1845/1850 and 1960. The others still want a [V] pass, e.g. from a library Britannica login or the *Oxford Atlas of World History*. Examples: 1757–1842, 1788, 1511, 1786, 1945, 1980, 1608/1759, 1849, 1803, 1938, 1922.
15. **Chennai, Cebu, Gdańsk, Potosí** were reworded after fact-check:
    - Chennai: Armagaon (1626) predates Fort St George as an English fortified post.
    - Cebu: Magellan's first Philippine landfall was Homonhon.
    - Gdańsk: Wieluń was bombed minutes before Westerplatte.
    - Potosí: the UNESCO text supports "largest industrial complex", not "biggest silver lodes".
16. **Proximity distances** are haversine distances between the NE `populated_places` points used in the table. An independent fact-check run differed by up to 13 km on some pairs (Lagos–Cotonou, Peshawar–Islamabad), probably because it used different NE rows for the same name. Recompute in the build's dot-spacing check rather than trusting these numbers.

**Deep source worth acquiring:** the *Oxford Atlas of World History* (ed. O'Brien). It would give page-level citations for the historical "why" claims in place of the current Britannica search-text confirmations.

## Sources

- **PLC-ADEN** [S]: Presidential Leadership Council of Yemen, news item referring to Aden as "interim capital". https://www.presidentalalimi.net/en/news1392.html
- **CIA-CI** [S]: CIA World Factbook, Côte d'Ivoire summary (Abidjan as administrative capital). https://www.cia.gov/the-world-factbook/countries/cote-divoire/summaries
- **BCN-EDIFICIO** [V]: Biblioteca del Congreso Nacional de Chile, Edificio Congreso Nacional (Valparaíso), https://www.bcn.cl/historiapolitica/congreso_nacional/edificios/detalle?sel=Edificio_Congreso_Nacional_(Valpara%C3%ADso)
- **BRIT-1911REV** [S]: Chinese Revolution 1911–12, https://www.britannica.com/event/Chinese-Revolution-1911-1912
- **BRIT-ADEN** [S]: Aden, https://www.britannica.com/place/Aden
- **BRIT-AGRA** [S]: Agra, https://www.britannica.com/place/Agra
- **BRIT-ALEPPO** [S]: Aleppo, https://www.britannica.com/place/Aleppo
- **BRIT-ALEXANDRIA** [S]: Alexandria, https://www.britannica.com/place/Alexandria-Egypt
- **BRIT-ALMATY** [S]: Almaty, https://www.britannica.com/place/Almaty-Kazakhstan
- **BRIT-ANGKOR** [S]: Angkor, https://www.britannica.com/place/Angkor
- **BRIT-ANTIOCH** [S]: Antioch, https://www.britannica.com/place/Antioch-modern-and-ancient-city-south-central-Turkey
- **BRIT-ANTWERP** [S]: Antwerp – History, https://www.britannica.com/place/Antwerp-Belgium/History
- **BRIT-ATOMICBOMBINGS** [S]: Atomic bombings of Hiroshima and Nagasaki, https://www.britannica.com/event/atomic-bombings-of-Hiroshima-and-Nagasaki
- **BRIT-AUCKLAND** [S]: Auckland, https://www.britannica.com/place/Auckland-New-Zealand
- **BRIT-BARCELONA** [S]: Barcelona – History, https://www.britannica.com/place/Barcelona/History
- **BRIT-BASRA** [S]: Basra, https://www.britannica.com/place/Basra
- **BRIT-BENGALURU** [S]: Bengaluru, https://www.britannica.com/place/Bangalore-India
- **BRIT-BOSTONMASSACRE** [S]: Boston Massacre, https://www.britannica.com/event/Boston-Massacre
- **BRIT-BOSTONTEA** [S]: Boston Tea Party, https://www.britannica.com/event/Boston-Tea-Party
- **BRIT-BRAZILHIST** [S]: History of Brazil, https://www.britannica.com/topic/history-of-Brazil
- **BRIT-BRISBANE** [S]: Brisbane, https://www.britannica.com/place/Brisbane
- **BRIT-BUKHARA** [S]: Bukhara, https://www.britannica.com/place/Bukhara
- **BRIT-BUSAN** [S]: Busan, https://www.britannica.com/place/Busan
- **BRIT-CANTONSYS** [S]: Canton system, https://www.britannica.com/event/Canton-system
- **BRIT-CAPETOWN** [S]: Cape Town, https://www.britannica.com/place/Cape-Town
- **BRIT-CAPHAITIEN** [S]: Cap-Haïtien, https://www.britannica.com/place/Cap-Haitien
- **BRIT-CASA-CONTRATACION** [S]: Casa de Contratación, https://www.britannica.com/topic/Casa-de-Contratacion
- **BRIT-CASABLANCA** [S]: Casablanca, https://www.britannica.com/place/Casablanca-Morocco
- **BRIT-CEBU** [S]: Cebu, https://www.britannica.com/place/Cebu
- **BRIT-CHICAGO** [S]: Chicago – History, https://www.britannica.com/place/Chicago/History
- **BRIT-CHITTAGONG** [S]: Chittagong, https://www.britannica.com/place/Chittagong
- **BRIT-CHONGQING** [S]: Chongqing – History, https://www.britannica.com/place/Chongqing/History
- **BRIT-COLHIST** [S]: History of Colombia, https://www.britannica.com/topic/history-of-Colombia
- **BRIT-COLOMBO** [S]: Colombo, https://www.britannica.com/place/Colombo
- **BRIT-COLUMBUS** [S]: Christopher Columbus, https://www.britannica.com/biography/Christopher-Columbus
- **BRIT-COTEDIVOIRE** [S]: Côte d'Ivoire, https://www.britannica.com/place/Cote-dIvoire
- **BRIT-CUBANREV** [S]: Cuban Revolution – Rise of Castro, https://www.britannica.com/event/Cuban-Revolution/The-rise-of-Castro-and-the-outbreak-of-revolution
- **BRIT-DARESSALAAM** [S]: Dar es Salaam, https://www.britannica.com/place/Dar-es-Salaam
- **BRIT-DETROIT** [S]: Detroit, https://www.britannica.com/place/Detroit
- **BRIT-DODOMA** [S]: Dodoma, https://www.britannica.com/place/Dodoma
- **BRIT-DOUALA** [S]: Douala, https://www.britannica.com/place/Douala
- **BRIT-DUBAI** [S]: Dubai (city), https://www.britannica.com/place/Dubai-United-Arab-Emirates
- **BRIT-DUBROVNIK** [S]: Dubrovnik, https://www.britannica.com/place/Dubrovnik
- **BRIT-ECB** [S]: European Central Bank, https://www.britannica.com/money/European-Central-Bank
- **BRIT-FLORENCE** [S]: Florence, https://www.britannica.com/place/Florence
- **BRIT-FORDLINE** [S]: Automotive industry – Ford and the assembly line, https://www.britannica.com/technology/automotive-industry/Ford-and-the-assembly-line
- **BRIT-FORTSTGEORGE** [S]: Fort Saint George, https://www.britannica.com/topic/Fort-Saint-George
- **BRIT-FRANKFURT** [S]: Frankfurt am Main, https://www.britannica.com/place/Frankfurt-am-Main
- **BRIT-GDANSK** [S]: Gdańsk, https://www.britannica.com/place/Gdansk
- **BRIT-GENEVA** [S]: Geneva, https://www.britannica.com/place/Geneva-Switzerland
- **BRIT-GENOA** [S]: Genoa, https://www.britannica.com/place/Genoa-Italy
- **BRIT-GHANA-HIST** [S]: History of Ghana, https://www.britannica.com/topic/history-of-Ghana
- **BRIT-GOLCONDA** [S]: Golconda, https://www.britannica.com/place/Golconda-historical-city-India
- **BRIT-GOLDRUSH** [S]: California Gold Rush, https://www.britannica.com/event/California-Gold-Rush
- **BRIT-GOTHENBURG** [S]: Gothenburg, https://www.britannica.com/place/Gothenburg-Sweden
- **BRIT-GUADALAJARA** [S]: Guadalajara, https://www.britannica.com/place/Guadalajara-Mexico
- **BRIT-GUAYAQUIL** [S]: Guayaquil, https://www.britannica.com/place/Guayaquil
- **BRIT-HAMBURG** [S]: Hamburg, https://www.britannica.com/place/Hamburg-Germany
- **BRIT-HANGZHOU** [S]: Hangzhou, https://www.britannica.com/place/Hangzhou
- **BRIT-HANSEATIC** [S]: Hanseatic League, https://www.britannica.com/topic/Hanseatic-League
- **BRIT-HCMC** [S]: Ho Chi Minh City, https://www.britannica.com/place/Ho-Chi-Minh-City
- **BRIT-HERATSCHOOL** [S]: Herāt school, https://www.britannica.com/art/Herat-school
- **BRIT-HIROSHIMA** [S]: Hiroshima, https://www.britannica.com/place/Hiroshima-Japan
- **BRIT-HONOLULU** [S]: Honolulu, https://www.britannica.com/place/Honolulu
- **BRIT-HOUSTON** [S]: Houston, https://www.britannica.com/place/Houston
- **BRIT-HYDERABAD** [S]: Hyderabad (historical state), https://www.britannica.com/place/Hyderabad-historical-state-India
- **BRIT-INDIA-SIKHS** [S]: India: The Sikhs in the Punjab, https://www.britannica.com/place/India/The-Sikhs-in-the-Punjab
- **BRIT-INVASION-POLAND** [S]: Invasion of Poland (1939), https://www.britannica.com/event/Invasion-of-Poland
- **BRIT-ISLAMIC-SAFAVIDS** [S]: Islamic world: Safavids, https://www.britannica.com/topic/Islamic-world/Safavids
- **BRIT-ISTANBUL** [S]: Istanbul, https://www.britannica.com/place/Istanbul
- **BRIT-IZMIR** [S]: İzmir, https://www.britannica.com/summary/Izmir
- **BRIT-JALISCO** [S]: Jalisco, https://www.britannica.com/place/Jalisco
- **BRIT-JOHANNESBURG** [S]: Johannesburg, https://www.britannica.com/place/Johannesburg-South-Africa
- **BRIT-KANO** [S]: Kano summary, https://www.britannica.com/summary/Kano-Nigeria
- **BRIT-KARACHI** [S]: Karachi, https://www.britannica.com/place/Karachi
- **BRIT-KASHGAR** [S]: Kashgar, https://www.britannica.com/place/Kashgar
- **BRIT-KHYBER** [S]: Khyber Pass, https://www.britannica.com/place/Khyber-Pass
- **BRIT-KINGDOM-NAPLES** [S]: Kingdom of Naples, https://www.britannica.com/place/Kingdom-of-Naples
- **BRIT-KOLKATA** [S]: Kolkata, https://www.britannica.com/place/Kolkata
- **BRIT-KOREANWAR** [S]: Korean War – Invasion and counterinvasion 1950–51, https://www.britannica.com/event/Korean-War/Invasion-and-counterinvasion-1950-51
- **BRIT-KRAKOW** [S]: Krakow, https://www.britannica.com/place/Krakow
- **BRIT-KYOTO** [S]: Kyoto – History, https://www.britannica.com/place/Kyoto-Japan/History
- **BRIT-LA** [S]: Los Angeles – Entertainment industry, https://www.britannica.com/place/Los-Angeles-California/The-entertainment-industry
- **BRIT-LAGOS** [S]: Lagos, https://www.britannica.com/place/Lagos-Nigeria
- **BRIT-LAHORE** [S]: Lahore, https://www.britannica.com/place/Lahore
- **BRIT-LAPAZ** [S]: La Paz, https://www.britannica.com/place/La-Paz-Bolivia
- **BRIT-LAPURCHASE** [S]: Louisiana (state), https://www.britannica.com/place/Louisiana-state
- **BRIT-LEGAZPI** [S]: Miguel López de Legazpi, https://www.britannica.com/biography/Miguel-Lopez-de-Legazpi
- **BRIT-LISBON** [S]: Lisbon – Evolution of the modern city, https://www.britannica.com/place/Lisbon/Evolution-of-the-modern-city
- **BRIT-LIVERPOOL** [S]: Liverpool, https://www.britannica.com/place/Liverpool-England
- **BRIT-LUBUMBASHI** [S]: Lubumbashi, https://www.britannica.com/place/Lubumbashi
- **BRIT-LVIV** [S]: Lviv, https://www.britannica.com/place/Lviv-Ukraine
- **BRIT-LYON** [S]: Lyon summary, https://www.britannica.com/summary/Lyon-France
- **BRIT-MANAUS** [S]: Manaus, https://www.britannica.com/place/Manaus
- **BRIT-MANCHESTER** [S]: Manchester – Evolution of the modern city, https://www.britannica.com/place/Manchester-England/Evolution-of-the-modern-city
- **BRIT-MANDALAY** [S]: Mandalay, https://www.britannica.com/place/Mandalay-Myanmar
- **BRIT-MARRAKECH** [S]: Marrakech, https://www.britannica.com/place/Marrakech
- **BRIT-MARSEILLE** [S]: Marseille, https://www.britannica.com/place/Marseille
- **BRIT-MASHHAD** [S]: Mashhad: History, https://www.britannica.com/place/Mashhad/History
- **BRIT-MECCA** [S]: Mecca, https://www.britannica.com/place/Mecca
- **BRIT-MEDINA** [S]: Medina, https://www.britannica.com/place/Medina-Saudi-Arabia
- **BRIT-MELAKA** [S]: Melaka, https://www.britannica.com/place/Melaka-Malaysia
- **BRIT-MELBOURNE** [S]: Melbourne – History, https://www.britannica.com/place/Melbourne/History
- **BRIT-MIAMI** [S]: Miami, https://www.britannica.com/place/Miami-Florida
- **BRIT-MILAN** [S]: Milan – Finance and other services, https://www.britannica.com/place/Milan-Italy/Finance-and-other-services
- **BRIT-MONTERREY** [S]: Monterrey, https://www.britannica.com/place/Monterrey-Mexico
- **BRIT-MONTREAL** [S]: Montreal – History, https://www.britannica.com/place/Montreal/History
- **BRIT-MOSUL** [S]: Mosul, https://www.britannica.com/place/Mosul
- **BRIT-MUMBAI** [S]: Mumbai, https://www.britannica.com/place/Mumbai
- **BRIT-MUNICH-AGREEMENT** [S]: Munich Agreement, https://www.britannica.com/event/Munich-Agreement
- **BRIT-MURMANSK** [S]: Murmansk, https://www.britannica.com/place/Murmansk-Russia
- **BRIT-MYANMAR** [S]: Myanmar, https://www.britannica.com/place/Myanmar
- **BRIT-NANJING** [S]: Nanjing, https://www.britannica.com/place/Nanjing-China
- **BRIT-NANJINGMASSACRE** [S]: Nanjing Massacre, https://www.britannica.com/event/Nanjing-Massacre
- **BRIT-NAPLES** [S]: Naples – History, https://www.britannica.com/place/Naples-Italy/History
- **BRIT-NEWORLEANS** [S]: New Orleans, https://www.britannica.com/place/New-Orleans-Louisiana
- **BRIT-NINEVEH** [S]: Nineveh, https://www.britannica.com/place/Nineveh-ancient-city-Iraq
- **BRIT-NYC** [S]: New York City summary, https://www.britannica.com/summary/New-York-City
- **BRIT-OSAKA** [S]: Osaka, https://www.britannica.com/place/Osaka-Japan
- **BRIT-PENANG** [S]: Penang, https://www.britannica.com/place/Penang
- **BRIT-PERSEPOLIS** [S]: Persepolis, https://www.britannica.com/place/Persepolis
- **BRIT-PERTH** [S]: Perth, https://www.britannica.com/place/Perth-Western-Australia
- **BRIT-PESHAWAR** [S]: Peshawar, https://www.britannica.com/place/Peshawar
- **BRIT-PORT-WINE** [S]: Port (wine), https://www.britannica.com/topic/port-wine
- **BRIT-PORTO** [S]: Porto, https://www.britannica.com/place/Porto-Portugal
- **BRIT-POTALA** [S]: Potala Palace, https://www.britannica.com/topic/Potala-Palace
- **BRIT-QARAWIYYIN** [S]: Qarawiyyin, https://www.britannica.com/topic/Qarawiyin
- **BRIT-QUEBEC** [S]: Quebec (city), https://www.britannica.com/place/Quebec
- **BRIT-ROTTERDAM** [S]: Rotterdam, https://www.britannica.com/place/Rotterdam-Netherlands
- **BRIT-SAKOKU** [S]: Sakoku, https://www.britannica.com/topic/sakoku
- **BRIT-SAMARKAND** [S]: Samarkand, https://www.britannica.com/place/Samarkand-Uzbekistan
- **BRIT-SANJUANHILL** [S]: Battle of San Juan Hill, https://www.britannica.com/event/Battle-of-San-Juan-Hill
- **BRIT-SAOPAULO** [S]: São Paulo, https://www.britannica.com/place/Sao-Paulo-Brazil
- **BRIT-SEVILLA** [S]: Sevilla, https://www.britannica.com/place/Sevilla-Spain
- **BRIT-SEZ** [S]: Special economic zone, https://www.britannica.com/money/special-economic-zone
- **BRIT-SF** [S]: San Francisco, https://www.britannica.com/place/San-Francisco-California
- **BRIT-SHAHROKH** [S]: Shāh Rokh, https://www.britannica.com/biography/Shah-Rokh-Timurid-ruler-of-Iran-and-Turkistan
- **BRIT-SHANGHAI** [S]: Shanghai – History, https://www.britannica.com/place/Shanghai/History
- **BRIT-SHIRAZ** [S]: Shiraz, https://www.britannica.com/place/Shiraz
- **BRIT-SIEGE-SEVASTOPOL** [S]: Siege of Sevastopol, https://www.britannica.com/event/Siege-of-Sevastopol
- **BRIT-SPAIN-ARAGON** [S]: Spain – Aragon, Catalonia, and Valencia, 1276–1479, https://www.britannica.com/place/Spain/Aragon-Catalonia-and-Valencia-1276-1479
- **BRIT-STALINGRAD** [S]: Battle of Stalingrad, https://www.britannica.com/event/Battle-of-Stalingrad
- **BRIT-STPETERSBURG** [S]: St. Petersburg, https://www.britannica.com/place/St-Petersburg-Russia
- **BRIT-SURABAYA** [S]: Surabaya, https://www.britannica.com/place/Surabaya
- **BRIT-SYDNEY** [S]: Sydney, https://www.britannica.com/place/Sydney-New-South-Wales
- **BRIT-TABRIZ** [S]: Tabriz, https://www.britannica.com/place/Tabriz
- **BRIT-TANGIER** [S]: Tangier, https://www.britannica.com/place/Tangier-Morocco
- **BRIT-TANZANIA-FACTS** [S]: Tanzania Facts, https://www.britannica.com/facts/Tanzania
- **BRIT-TEXTILE** [S]: Textile, https://www.britannica.com/topic/textile
- **BRIT-THESSALONIKI** [S]: Thessaloniki, https://www.britannica.com/place/Thessaloniki
- **BRIT-TIANJIN** [S]: Tianjin – History, https://www.britannica.com/place/Tianjin-China/History
- **BRIT-TIMBUKTU** [S]: Timbuktu, https://www.britannica.com/place/Timbuktu-Mali
- **BRIT-TORONTO** [S]: Toronto – History, https://www.britannica.com/place/Toronto/History
- **BRIT-TREASUREFLEET** [S]: Spanish treasure fleet, https://www.britannica.com/topic/Spanish-treasure-fleet
- **BRIT-UN** [S]: United Nations, https://www.britannica.com/topic/United-Nations
- **BRIT-VANCOUVER** [S]: Vancouver, https://www.britannica.com/place/Vancouver
- **BRIT-VARANASI** [S]: Varanasi, https://www.britannica.com/place/Varanasi
- **BRIT-VENICE** [S]: Venice – History, https://www.britannica.com/place/Venice/History
- **BRIT-VERACRUZ** [S]: Veracruz, https://www.britannica.com/place/Veracruz-Mexico
- **BRIT-VLADIVOSTOK** [S]: Vladivostok, https://www.britannica.com/place/Vladivostok
- **BRIT-WUHAN** [S]: Wuhan, https://www.britannica.com/place/Wuhan
- **BRIT-XIAN** [S]: Xi'an, https://www.britannica.com/place/Xian-China
- **BRIT-YAMOUSSOUKRO** [S]: Yamoussoukro, https://www.britannica.com/place/Yamoussoukro
- **BRIT-YANGON** [S]: Yangon, https://www.britannica.com/place/Yangon
- **BRIT-YEKATERINBURG** [S]: Yekaterinburg, https://www.britannica.com/place/Yekaterinburg
- **BRIT-ZANZIBAR** [S]: Zanzibar, https://www.britannica.com/place/Zanzibar-island-Tanzania
- **BRIT-ZURICH** [S]: Zurich, https://www.britannica.com/place/Zurich
- **CPE-BOLIVIA** [V]: Constitución Política del Estado (2009), Art. 6.I, https://www.bcb.gob.bo/webdocs/NUEVA_CONSTITUCION_POLITICA_DEL_ESTADO.pdf
- **ICRC-STATUTES** [S]: Statutes of the ICRC, extract (seat in Geneva), https://international-review.icrc.org/sites/default/files/S0020860400022130a.pdf
- **INEC-GUAYAQUIL** [V]: INEC Ecuador, Estimaciones y Proyecciones de Población, https://www.ecuadorencifras.gob.ec/proyecciones-poblacionales/
- **KOTTE-MC** [V]: Sri Jayawardenepura Kotte Municipal Council, Overview, https://www.kotte.mc.gov.lk/index.php?option=com_content&view=article&id=25&Itemid=175&lang=en
- **KPA-GATEWAY** [S]: Kenya Ports Authority, Ports & Terminals, https://kpa.co.ke/Ports
- **MKRI-CAPITAL** [S]: Constitutional Court of Indonesia, "Capital Relocation Depends on Issuance of Presidential Decree" (12 May 2026), https://en.mkri.id/news/details/2026-05-12/Capital_Relocation_Depends_on_Issuance_of_Presidential_Decree
- **NPS-INDEPENDENCEHALL** [V]: National Park Service, Independence Hall, https://www.nps.gov/inde/learn/historyculture/places-independencehall.htm
- **PAD-HINTERLAND** [S]: Port Autonome de Douala, services, https://pad.cm/services-du-port-autonome-de-douala/ (404 when opened; claim seen in search text only)
- **PORT-GOTHENBURG** [V]: Port of Gothenburg – Facts and Figures, https://www.portofgothenburg.com/about/figures/
- **PORT-ROTTERDAM** [V]: Port of Rotterdam, home page ("largest port in Europe" is the port authority's own claim), https://www.portofrotterdam.com/en
- **SENADO-CONGRESO** [V]: Senado de Chile, Congreso Nacional de Valparaíso, https://www.senado.cl/ciudadania/patrimonio-del-senado/congreso-nacional-de-valparaiso
- **TRANSNET-DCT** [S]: Transnet, Durban Container Terminal, https://www.transnet.net/SubsiteRender.aspx?id=7401981 (its "Africa's Biggest and Busiest" self-description is not used)
- **UNESCO-ALEPPO** [S]: Ancient City of Aleppo, Five Years of Conflict, https://whc.unesco.org/en/activities/946/
- **UNESCO-ANGKOR** [S]: Angkor, https://whc.unesco.org/en/list/668/
- **UNESCO-BRYGGEN** [S]: Bryggen, https://whc.unesco.org/en/list/59/
- **UNESCO-BUKHARA** [S]: Historic Centre of Bukhara, https://whc.unesco.org/en/list/602/
- **UNESCO-CARTAGENA** [S]: Port, Fortresses and Group of Monuments, Cartagena, https://whc.unesco.org/en/list/285/
- **UNESCO-CITADELLE** [S]: National History Park – Citadel, Sans Souci, Ramiers, https://whc.unesco.org/en/list/180/
- **UNESCO-CUSCO** [S]: City of Cuzco, https://whc.unesco.org/en/list/273/
- **UNESCO-DUBROVNIK** [S]: Old City of Dubrovnik, https://whc.unesco.org/en/list/95/
- **UNESCO-FEZ** [S]: Medina of Fez, https://whc.unesco.org/en/list/170/
- **UNESCO-FLORENCE** [S]: Historic Centre of Florence, https://whc.unesco.org/en/list/174/
- **UNESCO-FORTJESUS** [S]: Fort Jesus, Mombasa, https://whc.unesco.org/en/list/1295/
- **UNESCO-HIROSHIMA** [S]: Hiroshima Peace Memorial (Genbaku Dome), https://whc.unesco.org/en/list/775/
- **UNESCO-HUE** [S]: Complex of Hué Monuments, https://whc.unesco.org/en/list/678/
- **UNESCO-ISFAHAN** [S]: Meidan Emam, Esfahan, https://whc.unesco.org/en/list/115/
- **UNESCO-JEDDAH** [S]: Historic Jeddah, the Gate to Makkah, https://whc.unesco.org/en/list/1361/
- **UNESCO-KRAKOW** [S]: Historic Centre of Kraków, https://whc.unesco.org/en/list/29/
- **UNESCO-LVIV** [S]: L'viv – the Ensemble of the Historic Centre, https://whc.unesco.org/en/list/865/
- **UNESCO-MARRAKESH** [S]: Medina of Marrakesh, https://whc.unesco.org/en/list/331/
- **UNESCO-MELAKA-GEORGETOWN** [S]: Melaka and George Town, Historic Cities of the Straits of Malacca, https://whc.unesco.org/en/list/1223/
- **UNESCO-ODESA** [S]: The Historic Centre of Odesa, https://whc.unesco.org/en/list/1703/
- **UNESCO-PHILADELPHIA** [S]: Independence Hall, https://whc.unesco.org/en/list/78/
- **UNESCO-POTALA** [S]: Historic Ensemble of the Potala Palace, Lhasa, https://whc.unesco.org/en/list/707/
- **UNESCO-POTOSI** [S]: City of Potosí, https://whc.unesco.org/en/list/420/
- **UNESCO-QUEBEC** [S]: Historic District of Old Québec, https://whc.unesco.org/en/list/300/
- **UNESCO-SALVADOR** [S]: Historic Centre of Salvador de Bahia, https://whc.unesco.org/en/list/309/
- **UNESCO-SAMARKAND** [S]: Samarkand – Crossroad of Cultures, https://whc.unesco.org/en/list/603
- **UNESCO-SILKROADS** [S]: Silk Roads: Chang'an-Tianshan Corridor, https://whc.unesco.org/en/list/1442/
- **UNESCO-STONETOWN** [S]: Stone Town of Zanzibar, https://whc.unesco.org/en/list/173/
- **UNESCO-TABRIZ** [S]: Tabriz Historic Bazaar Complex, https://whc.unesco.org/en/list/1346/ (its "Safavid ... 13th century" wording is wrong; not used for the capital claim)
- **UNESCO-THEBES** [S]: Ancient Thebes with its Necropolis, https://whc.unesco.org/en/list/87/
- **UNESCO-THESSALONIKI** [S]: Paleochristian and Byzantine Monuments of Thessalonika, https://whc.unesco.org/en/list/456/
- **UNESCO-TIMBUKTU** [S]: Timbuktu, https://whc.unesco.org/en/list/119/
- **UNESCO-VALPARAISO** [S]: Historic Quarter of the Seaport City of Valparaíso, https://whc.unesco.org/en/list/959/
- **ZAGOV-CAPITALS** [V]: South African Government, "South Africa at a glance", https://www.gov.za/about-sa/south-africa-glance
- **WD-API** [V]: Wikidata API `wbgetentities`, labels for all WIKIDATAIDs, queried 2026-10-14. https://www.wikidata.org/w/api.php
- **NE-PP**: Natural Earth v5.1.2 `ne_10m_populated_places` (vendored; pinned commit in [architecture.md](../architecture.md)). Source of `NE_ID`, `WIKIDATAID`, coordinates and capital markers.
