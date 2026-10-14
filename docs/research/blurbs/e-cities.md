# Grounding blurbs, core cities (P2.7e)

Prepared 2026-10-14 for the `note` field of the city cards in [world-atlas-plan.md](../../world-atlas-plan.md). It covers the **42 core cities** in the final list in [cities.md](../cities.md), ordered by ring region (1–21). Regions 2, 4, 12 and 21 have no core city. Secondary cities are deferred, and their drafts are kept unpolished under [Deferred](#deferred-not-fact-checked).

**Scope changes during the task.**
- The brief was for 115 cities (55 core, 60 secondary). It was cut first to core only, and then to the final core list of 42.
- **Osaka** was added to the core list.
- **14 cities were demoted:** Marseille, Milan, Thessaloniki, Odesa, Mombasa, Casablanca, Lagos, Karachi, Almaty, Busan, Yangon, Melbourne, Auckland and Toronto. Drafts that already existed for 8 of them are in the Deferred section.

**Source tags** (same scheme as [cities.md](../cities.md)):
- **[V]**: the page or file was opened and the claim read there.
- **[S]**: confirmed from search-indexed text only. No core row has an [S] key after the fact-check. [S] keys remain only in the Deferred section.
- **FB-xx**: the World Factbook profile with GEC code `xx`, read from a local clone of the community mirror `github.com/factbook/factbook.json` at commit `144d697` (2026-09-11). Every FB key is [V].
- **UNESCO-\*** and some **BRIT-\*** keys are [V] because they were read from Wayback Machine snapshots (`web.archive.org/web/2025/<url>`). whc.unesco.org and britannica.com return HTTP 403 to direct fetches. The snapshot timestamp is given under [Sources](#sources).

**Rules applied.**
- **Blurb content:** where the city sits, then the hook that earned the card.
- **No statistics:** no population, area, tonnage or casualty figure appears. Dates are kept only where a [V] source states them.
- **Hedging and attribution:** where a source hedges, so does the blurb. Self-descriptions are attributed ("its port authority calls it…").
- **Time-sensitive items** are marked *(as of 2026-10; verify)*.
- **Grounding:** a claim that could not be grounded was cut, not guessed. Every cut is listed under [Cut claims](#cut-claims).
- **Slugs** follow the `capital-<iso3>-<name>` pattern of the other blurb files, as `city-<iso3>-<name>`. ADR 0005's id tag for a city is `id_city_<name>`.

**Retrieval limits.**
- The session's shared web-search budget ran out partway through.
- web.archive.org throttled requests and then refused connections for a time. UNESCO's Rio page never loaded, and Isfahan's loaded only at the fact-check.
- Chinese municipal sites, IBGE, the Ho Chi Minh City portal and several Brazilian archive pages returned 403, CAPTCHA pages or JS-only shells.
- **Wikipedia** was used for leads only and is never cited. `/home/dev/ultimate-geography` was not opened.

**Fact-check.** A second researcher checked 28 of the 42 rows against the opened sources: a random 25% sample of 11 rows (seed 20261014) plus every row flagged in the draft.

| Result | Rows |
|---|---|
| Passed as written | 12 |
| Keys upgraded only (Isfahan, Medina, Chicago, Ho Chi Minh City) | 4 |
| Text fixed | 12 (Guangzhou, Shanghai, Xi'an, Alexandria, Kolkata, Mumbai, Osaka, Mecca, Aleppo, Istanbul, Los Angeles, Johannesburg) |
| Cut as whole rows | 0 |

- **Claims removed:** eight, listed at the end of [Cut claims](#cut-claims).
- **Keys upgraded:** 16 [S] keys became [V], mostly Britannica pages opened through Wayback snapshots, plus the SurveyLA PDF. Every key on a core row is now [V].

## 1. Western Europe

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-esp-barcelona | 1 | core | Barcelona | Spain | A seaport in northeastern Spain on the Mediterranean, capital of Catalonia and Spain's major Mediterranean port. Founded as Roman Bàrcino, in the Middle Ages it became the seat of Old Catalonia's main political institutions, which favoured the trade behind its growth. | BRIT-BARCELONA [V]; BCN-HISTORY [V]; FB-sp [V] |
| city-nld-rotterdam | 1 | core | Rotterdam | Netherlands | On both banks of the New Meuse (Nieuwe Maas), a distributary of the Rhine, linked to the North Sea by the New Waterway. Its port authority calls it the largest port in Europe. The city was devastated by bombing in the Second World War and rebuilt. | BRIT-ROTTERDAM [V]; PORT-ROTTERDAM [V] |
| city-esp-seville | 1 | core | Seville | Spain | On the Guadalquivir River in southwestern Spain, inland from the Atlantic; it was once a capital of Muslim Spain. From 1503 its Casa de Contratación (House of Trade) regulated commerce with the New World, and for two centuries the city dominated Spain's American trade. Its Archivo de Indias holds the archives of Spain's American colonies. | BRIT-SEVILLA [V]; UNESCO-SEVILLE [V] |

## 3. Central Europe & Italy

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-deu-hamburg | 3 | core | Hamburg | Germany | On the Elbe River in northern Germany, a city that is also a federal state, officially the Free and Hanseatic City of Hamburg. Britannica calls it Germany's largest port. Its Speicherstadt, a port warehouse district on islands in the Elbe, is a World Heritage site. | BRIT-HAMBURG [V]; UNESCO-HAMBURG [V] |
| city-deu-frankfurt | 3 | core | Frankfurt | Germany | On the Main River in western Germany, upstream of its confluence with the Rhine at Mainz. The Golden Bull of 1356 made it the permanent site for electing German kings, and it has held trade fairs since the Middle Ages. Today it is a leading financial centre, with a stock exchange and the seat of the European Central Bank. | BRIT-FRANKFURT [V]; ECB-PREMISES [V] |
| city-ita-venice | 3 | core | Venice | Italy | An island city in a lagoon on the northern Adriatic, in northeastern Italy. Founded in the 5th century AD, it became a major maritime power in the 10th century, and as a republic it defended its trading markets against the Arabs, the Genoese and the Ottoman Turks until the republic fell in 1797. | UNESCO-VENICE [V]; BRIT-VENICE [V] |
| city-ita-florence | 3 | core | Florence | Italy | A Tuscan city on the Arno River, built on an Etruscan settlement and the Roman colony of Florentia. Under the early Medici, in the 15th and 16th centuries, it became a symbol of the Renaissance, with an overwhelming influence on architecture and the fine arts in Italy and then Europe. | UNESCO-FLORENCE [V] |

## 5. Eastern Europe

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-rus-saint-petersburg | 5 | core | Saint Petersburg | Russia | On the Neva River near the Baltic coast, built by Peter the Great from 1703 as Russia's "window on Europe". It was the capital of the Russian Empire from 1712 to 1918, saw both revolutions of 1917, and was besieged in the Second World War. | BRIT-STPETERSBURG [V]; UNESCO-STPETERSBURG [V] |
| city-rus-volgograd | 5 | core | Volgograd | Russia | On the Volga River in southwestern Russia, founded as the fortress of Tsaritsyn and named Stalingrad from 1925 to 1961. The Battle of Stalingrad in 1942–43 stopped the German advance into the Soviet Union and turned the tide of the war in the Allies' favour. | BRIT-VOLGOGRAD [V]; BRIT-STALINGRAD [V] |

## 6. Caucasus & Anatolia

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-tur-istanbul | 6 | core | Istanbul | Turkey | Straddles the Bosporus, part of the Turkish Straits between the Black Sea and the Aegean; the Factbook calls it the only metropolis in the world on two continents. Formerly Byzantium and then Constantinople, it was successively the capital of the Eastern Roman and Ottoman Empires. Its historic peninsula between the Golden Horn and the Sea of Marmara holds masterpieces such as Hagia Sophia and the Süleymaniye Mosque. | FB-tu [V]; UNESCO-ISTANBUL [V] |

## 7. Levant & Mesopotamia

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-syr-aleppo | 7 | core | Aleppo | Syria | A major Syrian city at the crossroads of several trade routes since the 2nd millennium BC; Hittites, Assyrians, Greeks, Romans, Umayyads, Ayyubids, Mamluks and Ottomans ruled it in turn. Its walled Old City, built round a citadel, has been on UNESCO's List of World Heritage in Danger since 2013 *(as of 2026-10; verify)*. | FB-sy [V]; UNESCO-ALEPPO [V] |

## 8. Arabian Peninsula

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-sau-mecca | 8 | core | Mecca | Saudi Arabia | In western Saudi Arabia, inland from the Red Sea coast. Birthplace of the Prophet Muhammad, it holds one of Islam's two holiest shrines and is the destination of the Hajj pilgrimage. | FB-sa [V]; BRIT-MECCA [V] |
| city-are-dubai | 8 | core | Dubai | United Arab Emirates | On the southwest corner of the Arabian (Persian) Gulf, divided by Dubai Creek, a natural harbour that made it a centre of fishing, pearling and sea trade. It was a successful port city by the early 20th century; its economy now rests heavily on trade, services and finance. | U-AE-DUBAI [V] |
| city-sau-medina | 8 | core | Medina | Saudi Arabia | In western Saudi Arabia near the Red Sea, the city to which Muhammad migrated from Mecca in the Hijrah, the event that begins the Muslim calendar. The Prophet's Mosque houses his tomb, and with Mecca the city holds Islam's two holiest shrines. | FB-sa [V]; BRIT-MEDINA [V]; BRIT-HIJRAH [V] |

## 9. Horn & East Africa

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-tza-zanzibar | 9 | core | Zanzibar | Tanzania | Stone Town, on the western side of Unguja island off the Tanzanian coast, is a Swahili trading town shaped by African, Arab, Indian and European influences. Zanzibar was a hub of Indian Ocean trade that fed the slave trade, and briefly the capital of the Sultanate of Oman before a separate Zanzibar Sultanate split off in 1856. Christ Church Cathedral stands on the site of its last slave market. | FB-tz [V]; UNESCO-STONETOWN [V] |

## 10. North Africa

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-egy-alexandria | 10 | core | Alexandria | Egypt | On the Mediterranean at the western edge of the Nile delta, founded by Alexander the Great. Under the Ptolemies it held the Library of Alexandria, the most famous library of classical antiquity. It is still one of Egypt's key ports. | FB-eg [V]; BRIT-ALEXANDRIA [V]; BRIT-LIBRARY-ALEXANDRIA [V] |

## 11. West Africa

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-mli-timbuktu | 11 | core | Timbuktu | Mali | At the gateway to the Sahara, near the river, it was a crossroads market where salt from the north met gold, cattle and grain from the south. Under Songhai rule in the 15th and 16th centuries it became a large commercial centre known for Islamic scholarship, and its great earthen mosques survive. | UNESCO-TIMBUKTU [V]; FB-ml [V] |

## 13. Southern Africa & Indian Ocean

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-zaf-johannesburg | 13 | core | Johannesburg | South Africa | Built on the gold of the Witwatersrand: the city says gold put it on the map after digging there was declared legal in 1886. It grew into South Africa's chief industrial and financial metropolis. | JOBURG-NEWS [V]; FB-sf [V]; BRIT-JOHANNESBURG [V] |
| city-zaf-cape-town | 13 | core | Cape Town | South Africa | Named for its site by the Cape of Good Hope, it was founded by Dutch traders in 1652 as a stopover on the spice route between the Netherlands and the Far East. It is South Africa's legislative capital *(as of 2026-10; verify)*; Pretoria is the administrative capital. | FB-sf [V] |

## 14. South Asia

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-ind-mumbai | 14 | core | Mumbai | India | Partly on Mumbai Island, between Mumbai Harbour and the Arabian Sea. It grew from a fortified trading outpost into the first city of India in the 19th and 20th centuries, and the Factbook calls it India's financial capital. It is also the headquarters of India's film industry. | UNESCO-MUMBAI-VG [V]; FB-in [V]; BRIT-MUMBAI [V] |
| city-ind-kolkata | 14 | core | Kolkata | India | On the east bank of the Hooghly, once the main channel of the Ganges, inland from the Bay of Bengal. It grew from an East India Company trading post into the capital of British India, until the capital moved to Delhi in the early 20th century. | FB-in [V]; BRIT-KOLKATA [V]; BRIT-KOLKATA-SUM [V] |

## 15. Iran & Central Asia

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-uzb-samarkand | 15 | core | Samarkand | Uzbekistan | In a large oasis in the Zerafshan River valley, Samarkand is described by UNESCO as a crossroads of world cultures. Its ancient city was destroyed by Genghis Khan in the 13th century, and it reached its height as capital of the Timurid realm in the 14th and 15th centuries. | UNESCO-SAMARKAND [V]; FB-uz [V] |
| city-irn-isfahan | 15 | core | Isfahan | Iran | Capital of Safavid Iran, whose ruler Shah Abbas I laid out its great square, Meidan Emam. The square and the city's Friday Mosque (Masjed-e Jāmé) are World Heritage sites. | FB-ir [V]; UNESCO-ISFAHAN [V] |

## 16. East Asia

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-chn-shanghai | 16 | core | Shanghai | China | Near the mouth of the Yangtze on China's east coast. The 1842 Treaty of Nanking opened it to British merchants as one of five treaty ports, and it grew into a major industrial and commercial centre. Today it is one of China's four municipalities and a key port. | TREATY-NANKING [V]; FB-ch [V]; BRIT-SHANGHAI [V] |
| city-chn-guangzhou | 16 | core | Guangzhou | China | Historic Canton, near the head of the Pearl River Delta in southern China. Before 1842 British merchants trading at Canton had to deal only through Hong merchants licensed by the Chinese government; the Treaty of Nanking abolished that practice and opened Canton with four other ports. It remains one of China's key ports. | TREATY-NANKING [V]; FB-ch [V]; BRIT-GUANGZHOU [V] |
| city-chn-xian | 16 | core | Xi'an | China | Capital of Shaanxi province, at the southern edge of the Loess Plateau. Chang'an, on and beside its site, was China's central capital under the Han and Tang dynasties and the start of the Silk Roads' Chang'an–Tianshan corridor to Central Asia. | UNESCO-SILKROADS [V]; FB-ch [V]; BRIT-XIAN [V] |
| city-jpn-kyoto | 16 | core | Kyoto | Japan | Set in a basin ringed by mountains on three sides. It was founded in 794 as the imperial capital Heian-kyō, on a grid modelled on the Tang capital Chang'an, and stayed Japan's imperial capital until the mid-19th century, when the capital moved to Tokyo, the "eastern capital". Its historic monuments are a World Heritage site. | KYOTO-CITY [V]; UNESCO-KYOTO [V]; FB-ja [V] |
| city-jpn-osaka | 16 | core | Osaka | Japan | A port city on Osaka Bay in south-central Honshu, close to Kyoto. Its tourism bureau describes "a long history of prosperity as an economic and cultural center", with the Yodoyabashi, Kitahama and Semba area long the heart of its commerce. Osaka Castle, built by Toyotomi Hideyoshi, stands on the site of the Ishiyama Honganji temple. | OCTB [V]; OSAKA-CASTLE [V]; FB-ja [V]; BRIT-OSAKA [V] |
| city-jpn-hiroshima | 16 | core | Hiroshima | Japan | Built on the broad delta where the Ota River splits into branches before reaching the Seto Inland Sea. On 6 August 1945 the first atomic bomb used in war exploded over the city. The Hiroshima Peace Memorial (Genbaku Dome), the only structure left standing near the hypocentre, is a World Heritage site. | MLIT-AKIOTA [V]; PREF-HIROSHIMA [V]; UNESCO-HIROSHIMA [V]; FB-ja [V] |

## 17. Southeast Asia

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-vnm-ho-chi-minh-city | 17 | core | Ho Chi Minh City | Vietnam | Formerly Saigon, in southern Vietnam on the Saigon River near the Mekong Delta. It was the capital of South Vietnam, which the 1954 Geneva Accords split from the communist North; after the war ended in 1975 with the North's victory it was renamed for Ho Chi Minh. | FB-vm [V]; BRIT-HCMC [V] |
| city-mys-malacca | 17 | core | Malacca | Malaysia | A port on the Strait of Malacca, the sea lane that separates the Malay Peninsula from the archipelago. At its height in the 15th century, as a Malay sultanate, it had a navy and hosted thousands of Chinese, Arab, Persian and Indian merchants. Portuguese and then Dutch rule followed from the early 16th century, and with George Town it is a World Heritage site. | FB-my [V]; UNESCO-MELAKA [V] |

## 18. Oceania

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-aus-sydney | 18 | core | Sydney | Australia | On Port Jackson (Sydney Harbour) on Australia's southeast coast. The settlement was founded in 1788, when Arthur Phillip led the First Fleet into Port Jackson, and the town that grew up around Sydney Cove was a convict colony. The Sydney Opera House is a World Heritage site. | SYD-COUNCIL-HIST [V]; SYD-ABORIGINAL [V]; FB-as [V] |

## 19. North & Central America

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-usa-new-york | 19 | core | New York | United States of America | A port on New York Harbor. The English took the Dutch colony of New Netherland in 1664 and renamed it New York. Millions of immigrants were inspected at Ellis Island in the harbor, and the city is home to the United Nations Headquarters. | NPS-ELIS-COLONIAL [V]; NPS-ELLIS [V]; UN-VISIT [V]; FB-us [V] |
| city-usa-los-angeles | 19 | core | Los Angeles | United States of America | Its port lies in San Pedro Bay, south of downtown, and describes itself as the busiest seaport in the Western Hemisphere. The motion picture industry, which arrived at the turn of the 20th century, helped transform Hollywood from a sleepy agricultural suburb into a vibrant commercial centre. | PORT-LA [V]; LACITY-SURVEYLA [V] |
| city-usa-chicago | 19 | core | Chicago | United States of America | Grew beside the Chicago Portage, a low divide between the Great Lakes and Mississippi River systems, long used by Native Americans and crossed by Marquette and Joliet in 1673. With the Illinois and Michigan Canal, opened in 1848, the portage became the transport link that spurred the city's growth. By the 1880s Chicagoans could claim their city was America's railroad hub. | NPS-CHPO [V]; NPS-ILMI [V]; ENC-CHICAGO-RAIL [V] |
| city-usa-new-orleans | 19 | core | New Orleans | United States of America | On the lower Mississippi, founded as La Nouvelle-Orléans by Jean-Baptiste Le Moyne de Bienville in 1718. In 1803 US negotiators sent to buy only the port of New Orleans and the Floridas instead agreed to buy the whole Louisiana territory from France. | NPS-JELA-EURO [V]; NPS-JELA [V]; NARA-LAPURCHASE [V] |
| city-usa-san-francisco | 19 | core | San Francisco | United States of America | A sleepy port town until gold was found in the Sierra Nevada foothills in January 1848. The gold rush turned it almost overnight into a booming city. | NPS-SFGOLD [V]; FB-us [V] |
| city-can-montreal | 19 | core | Montreal | Canada | On the St. Lawrence River, where the Sieur de Maisonneuve founded the French settlement of Ville-Marie in May 1642. The colony sat in a key region for farming and the fur trade, and grew into Montreal, one of Canada's great metropolitan centres. | PC-MTLBIRTH [V]; CE-VILLEMARIE [V] |

## 20. South America

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-bra-sao-paulo | 20 | core | São Paulo | Brazil | On the plateau above the Serra do Mar in southeastern Brazil, it grew from a college that Jesuits founded in 1554, the origin of the village of São Paulo de Piratininga. The state government credits coffee, and later industry, with São Paulo's growth into the country's largest industrial centre. It is Brazil's largest urban area *(as of 2026-10; verify)*. | SP-GOV-HIST [V]; FB-br [V] |
| city-bra-rio-de-janeiro | 20 | core | Rio de Janeiro | Brazil | Brazil's capital from 1763 to 1960, after Salvador and before Brasília. The national flag shows the sky over Rio on the morning of 15 November 1889, the day the republic was declared. Its Carioca landscapes between the mountain and the sea are a World Heritage site. | FB-br [V] |
| city-bol-potosi | 20 | core | Potosí | Bolivia | High in the Bolivian Andes below the Cerro Rico, whose silver made it the major colonial-era supplier of silver for Spain. It is reputed to have been the world's largest industrial complex in the 16th century, and Indigenous labourers were forced to work its mines under the mita. | UNESCO-POTOSI [V]; FB-bl [V] |
| city-per-cusco | 20 | core | Cusco | Peru | In the Peruvian Andes. Under Pachacuteq in the 15th century it became the capital of the Inca Empire; the Spanish who conquered it in the 16th century kept its plan but built Baroque churches and palaces over the Inca city. | UNESCO-CUSCO [V]; FB-pe [V] |

## Flagged items

After the fact-check, every key on a core row is [V]. The rows below are still time-sensitive, rest on a self-claim or a single source, or involve a source conflict.

| # | slug | why | what to verify |
|---|---|---|---|
| 1 | city-syr-aleppo | Time-sensitive | Still on the List of World Heritage in Danger (UNESCO 21 shows "2013 – Present" in the January 2026 snapshot). |
| 2 | city-nld-rotterdam | Self-claim | "Largest port in Europe" is the port authority's own claim, attributed as such. Not checked independently (for example against Eurostat). |
| 3 | city-deu-hamburg | Single-source ranking | "Germany's largest port" is credited to Britannica only. |
| 4 | city-rus-volgograd | Source conflict | Britannica's Volgograd article says the battle began in August 1942, and its battle article says 17 July 1942. The blurb says "1942–43". |
| 5 | city-are-dubai | Terminology | The UAE portal says "Arabian Gulf", and the blurb gives "Arabian (Persian) Gulf". |
| 6 | city-zaf-johannesburg | Source conflict | The city site says the main reef was found in June 1884 and digging was legalised on 4 October 1886, while FB-sf says gold was discovered in 1886. The blurb uses only the 1886 legalisation. |
| 7 | city-zaf-cape-town | Time-sensitive | Legislative capital, with Pretoria as the administrative capital (FB-sf). |
| 8 | city-ind-mumbai | Factbook wording | "India's financial capital" is the Factbook's phrase (2008 attacks background), attributed as such. |
| 9 | city-usa-los-angeles | Self-claim; time-sensitive | "Busiest seaport in the Western Hemisphere" is the port's own claim, attributed as such. |
| 10 | city-usa-chicago | Secondary source | The railroad-hub sentence rests on the Encyclopedia of Chicago, a scholarly secondary source. Its Wayback timestamp was read from rewritten links, not a server header. |
| 11 | city-bra-sao-paulo | Time-sensitive; attribution | "Brazil's largest urban area" comes from the FB-br 2023 urban-area list. The coffee-and-industry sentence is the São Paulo **state** government's account, which speaks of the state, and the blurb attributes it. The local copy of that page is only a JavaScript shell; the text was read through WebFetch twice, by two researchers. |
| 12 | city-bra-rio-de-janeiro | Thin hook | The 1808 transfer of the Portuguese court (the card's "capital of Portugal's empire" hook) is still cut, because UNESCO 1100 never loaded. |
| 13 | city-vnm-ho-chi-minh-city, city-ind-kolkata, city-sau-medina, city-egy-alexandria | Dates now available | Britannica [V] gives 30 April 1975 (the fall of Saigon), 1911 (Kolkata to Delhi), 622 CE (the Hijrah) and 332 BCE (Alexandria). The blurbs still leave these out; they can be added if wanted. |

## Cut claims

| slug | claim cut | why |
|---|---|---|
| city-esp-barcelona | "Medieval Crown of Aragon trading hub" | Not on any page opened. The blurb uses Barcelona City Council's wording on Old Catalonia's institutions and trade instead. |
| city-ita-florence | Medici banking | UNESCO names the Medici period but not banking. |
| city-deu-frankfurt | Imperial coronation city | Britannica places the coronation ceremonies at the Römer, which conflicts with the usual cathedral account. The 1356 election role is kept. |
| city-rus-saint-petersburg | "On the Gulf of Finland" | Not in the opened text. The blurb says "near the Baltic coast". |
| city-syr-aleppo | "Northern Syria" | No opened source states it for the city. |
| city-are-dubai | Aviation hub | Not on the UAE portal page. |
| city-sau-mecca | Wording of the Hajj obligation | Doctrine would have been stated from [S] only. |
| city-sau-medina | 622 date of the Hijrah | Only [S] when drafted. It is now [V] (BRIT-HIJRAH); see flag 13. |
| city-tza-zanzibar | Clove trade; the year the Omani capital moved | No source seen for the clove trade. Britannica gives both 1824 and 1832 for the move. |
| city-egy-alexandria | Founding year | Only [S] when drafted. It is now [V] (BRIT-ALEXANDRIA); see flag 13. |
| city-ind-kolkata | Year of the capital move | Search text gave both 1911 and 1912. The two Britannica pages opened at fact-check both say 1911; see flag 13. |
| city-chn-guangzhou | Canton system dates (1757–1842) | No [V] source reached, and Britannica's dates disagree. The blurb uses the treaty's Hong-merchant wording instead. |
| city-chn-xian | "Eastern Silk Road terminus" | UNESCO says the corridor *started* at Chang'an. |
| city-jpn-kyoto | "Capital for over a thousand years"; an end year | The city site says 1869 and the Factbook 1868. The blurb uses UNESCO's "until the middle of the 19th century". |
| city-jpn-osaka | "Kitchen of the nation"; castle year 1583 | Not on any opened page. |
| city-jpn-hiroshima | Casualty figures | Figures are excluded, and the sources differ. |
| city-vnm-ho-chi-minh-city | Date of the fall of Saigon | No [V] source when drafted. It is now available in BRIT-HCMC; see flag 13. |
| city-mys-malacca | Portuguese capture "in 1511" | [S] only. The blurb uses UNESCO's "Portuguese and Dutch periods beginning in the early 16th century". |
| city-aus-sydney | "Largest city" | FB lists Melbourne's urban area ahead (see cities.md, Verify item 9). |
| city-usa-new-york | "Leading US financial centre" | No official page opened states it. |
| city-usa-chicago | "On Lake Michigan" | No opened page states it outright. |
| city-usa-los-angeles | "Pacific" | Not stated in an opened source. San Pedro Bay is named instead. |
| city-usa-san-francisco | Population figures and ship counts | No figures. |
| city-bol-potosi | "Biggest silver lodes"; population and labour figures | No figures. UNESCO supports "largest industrial complex", attributed as "reputed". |
| city-bra-rio-de-janeiro | "Capital of Portugal's empire" (1808) | No [V] source reached. |
| city-sau-mecca | "Inland from the port of Jeddah" | No opened page calls Jeddah Mecca's port. The blurb says "inland from the Red Sea coast". |
| city-egy-alexandria | The Pharos lighthouse, one of the Seven Wonders | Fact-check: the Lighthouse article would not load, and the city article names only Pharos island. |
| city-ind-mumbai | "Nicknamed Bollywood" | Fact-check: not on any opened page. The blurb uses Britannica's "headquarters of its film industry". |
| city-zaf-johannesburg | "Home to the Johannesburg Stock Exchange" | Fact-check: jse.co.za returns 403 and has no Wayback copy, and the Britannica snapshot doesn't mention the JSE. |
| city-syr-aleppo | "Syria's largest city" | Fact-check: the Factbook contradicts itself, because its urban-area list puts Damascus ahead. |
| city-chn-shanghai | "China's leading … financial centre" | Fact-check: Britannica says "a major industrial and commercial centre". |
| city-jpn-osaka | "Kansai region" | Fact-check: not on any opened page. The blurb says "south-central Honshu". |
| city-usa-los-angeles | "Shaped the city's economy and culture" | Fact-check: not in the SurveyLA text, which says "helped transform Hollywood". |

## Sources

- **FB-xx** [V]: World Factbook profile, community mirror `factbook/factbook.json` at commit `144d697` (2026-09-11), local clone, `<region>/<code>.json`. Accessed 2026-10-14. Codes used in core rows: as, bl, br, ch, eg, in, ir, ja, ml, my, pe, sa, sf, sp, sy, tu, tz, us, uz, vm.

| key | source | location | accessed | tier |
|---|---|---|---|---|
| BCN-HISTORY | Barcelona City Council, Discover BCN: History | https://www.barcelona.cat/en/discoverbcn/history | 2026-10-14 | [V] |
| BRIT-ALEXANDRIA | Britannica, Alexandria (Wayback snapshot 20260106125639) | https://www.britannica.com/place/Alexandria-Egypt | 2026-10-14 | [V] |
| BRIT-BARCELONA | Britannica, Barcelona (Wayback snapshot of 20260216104746) | https://www.britannica.com/place/Barcelona | 2026-10-14 | [V] |
| BRIT-FRANKFURT | Britannica, Frankfurt am Main (Wayback snapshot of 20251222062619) | https://www.britannica.com/place/Frankfurt-am-Main | 2026-10-14 | [V] |
| BRIT-GUANGZHOU | Britannica, Guangzhou (Wayback snapshot 20251215193719) | https://www.britannica.com/place/Guangzhou | 2026-10-14 | [V] |
| BRIT-HAMBURG | Britannica, Hamburg (Wayback snapshot of 20251220004428) | https://www.britannica.com/place/Hamburg-Germany | 2026-10-14 | [V] |
| BRIT-HCMC | Britannica, Ho Chi Minh City (Wayback snapshot 20251128091639) | https://www.britannica.com/place/Ho-Chi-Minh-City | 2026-10-14 | [V] |
| BRIT-HIJRAH | Britannica, Hijrah (Wayback snapshot 20260114125700) | https://www.britannica.com/event/Hijrah-Islam | 2026-10-14 | [V] |
| BRIT-JOHANNESBURG | Britannica, Johannesburg (Wayback snapshot 20260105230548) | https://www.britannica.com/place/Johannesburg-South-Africa | 2026-10-14 | [V] |
| BRIT-KOLKATA | Britannica, Kolkata (Wayback snapshot 20260107103906) | https://www.britannica.com/place/Kolkata | 2026-10-14 | [V] |
| BRIT-KOLKATA-SUM | Britannica, Kolkata summary (Wayback snapshot 20250923105155) | https://www.britannica.com/summary/Kolkata | 2026-10-14 | [V] |
| BRIT-LIBRARY-ALEXANDRIA | Britannica, Library of Alexandria (Wayback snapshot 20251228085420) | https://www.britannica.com/topic/Library-of-Alexandria | 2026-10-14 | [V] |
| BRIT-MECCA | Britannica, Mecca (Wayback snapshot 20251230222150) | https://www.britannica.com/place/Mecca | 2026-10-14 | [V] |
| BRIT-MEDINA | Britannica, Medina (Wayback snapshot 20251228002223) | https://www.britannica.com/place/Medina-Saudi-Arabia | 2026-10-14 | [V] |
| BRIT-MUMBAI | Britannica, Mumbai (Wayback snapshot 20250908024500) | https://www.britannica.com/place/Mumbai | 2026-10-14 | [V] |
| BRIT-OSAKA | Britannica, Osaka (Wayback snapshot 20260104225047) | https://www.britannica.com/place/Osaka-Japan | 2026-10-14 | [V] |
| BRIT-ROTTERDAM | Britannica, Rotterdam (Wayback snapshot of 20251229203737) | https://www.britannica.com/place/Rotterdam-Netherlands | 2026-10-14 | [V] |
| BRIT-SEVILLA | Britannica, Sevilla (Wayback snapshot of 20251226000349) | https://www.britannica.com/place/Sevilla-Spain | 2026-10-14 | [V] |
| BRIT-SHANGHAI | Britannica, Shanghai (Wayback snapshot 20251221204759) | https://www.britannica.com/place/Shanghai | 2026-10-14 | [V] |
| BRIT-STALINGRAD | Britannica, Battle of Stalingrad (Wayback snapshot of 20260102154439) | https://www.britannica.com/event/Battle-of-Stalingrad | 2026-10-14 | [V] |
| BRIT-STPETERSBURG | Britannica, St. Petersburg (Wayback snapshot of 20251219230304) | https://www.britannica.com/place/St-Petersburg-Russia | 2026-10-14 | [V] |
| BRIT-VENICE | Britannica, Venice (Wayback snapshot of 20251217112640) | https://www.britannica.com/place/Venice | 2026-10-14 | [V] |
| BRIT-VOLGOGRAD | Britannica, Volgograd (Wayback snapshot of 20251203093224) | https://www.britannica.com/place/Volgograd-Russia | 2026-10-14 | [V] |
| BRIT-XIAN | Britannica, Xi'an (Wayback snapshot 20260104030104) | https://www.britannica.com/place/Xian-China | 2026-10-14 | [V] |
| CE-VILLEMARIE | The Canadian Encyclopedia, "Ville-Marie (Colony)", Dale Miquelon (last edited 2013-12-16) | https://www.thecanadianencyclopedia.ca/en/article/ville-marie-colony | 2026-10-14 | [V] (secondary) |
| ECB-PREMISES | European Central Bank, The ECB's main building | https://www.ecb.europa.eu/ecb/premises/html/index.en.html | 2026-10-14 | [V] |
| ENC-CHICAGO-RAIL | Encyclopedia of Chicago (Newberry Library), entry 1269 "Transportation" by H. Roger Grant (Wayback snapshot c. 20260102053057, timestamp read from rewritten links) | http://www.encyclopedia.chicagohistory.org/pages/1269.html | 2026-10-14 | [V] (secondary) |
| JOBURG-NEWS | City of Johannesburg newsroom, "Joburg still city of opportunities 135 years later" (Oct 2021) | https://joburg.org.za/media_/Newsroom/Pages/2021%20News%20Articles/October/Joburg-still-city-of-opportunities-135-years-later.aspx | 2026-10-14 | [V] (city's own account) |
| KYOTO-CITY | City of Kyoto official site, overview/history page (794 Heian-kyo; Chang'an model; capital relocated to Tokyo 1869; basin) | https://www.city.kyoto.lg.jp/sogo/page/0000305427.html | 2026-10-14 | [V] |
| LACITY-SURVEYLA | City of Los Angeles Planning, SurveyLA historic context 7.3, "Commercial Properties Associated with the Entertainment Industry, 1908-1980" (Jan 2020), p. 2; opened at fact-check | https://planning.lacity.gov/odocument/e212fb26-95d8-48e5-b7a9-a60958f33b09/7.3_Commercial_Properties_Associated_with_the_Entertainment_Industry_1908-1980.pdf | 2026-10-14 | [V] |
| MLIT-AKIOTA | Japan Tourism Agency/MLIT multilingual commentary database, 'Relations Between Akiota and the City of Hiroshima' (Ota River, alluvial delta, Seto Inland Sea, Atomic Bomb Dome) | https://www.mlit.go.jp/tagengo-db/common/001562233.pdf | 2026-10-14 | [V] |
| NARA-LAPURCHASE | US National Archives, Milestone Documents: Louisiana Purchase Treaty (1803) | https://www.archives.gov/milestone-documents/louisiana-purchase-treaty | 2026-10-14 | [V] |
| NPS-CHPO | National Park Service, Chicago Portage National Historic Site | https://www.nps.gov/places/chicago-portage.htm | 2026-10-14 | [V] |
| NPS-ELIS-COLONIAL | National Park Service, Ellis Island: Colonial and Early American New York | https://www.nps.gov/elis/learn/historyculture/places_colonial_early_american.htm | 2026-10-14 | [V] |
| NPS-ELLIS | National Park Service, Ellis Island (park home page) | https://www.nps.gov/elis/index.htm | 2026-10-14 | [V] |
| NPS-ILMI | National Park Service, Illinois & Michigan Canal National Heritage Area, History & Culture | https://www.nps.gov/ilmi/learn/historyculture/index.htm | 2026-10-14 | [V] |
| NPS-JELA | National Park Service, Jean Lafitte NHP, History & Culture (lower Mississippi River delta) | https://www.nps.gov/jela/learn/historyculture/index.htm | 2026-10-14 | [V] |
| NPS-JELA-EURO | National Park Service, Jean Lafitte NHP: Early Europeans in Louisiana | https://www.nps.gov/jela/learn/historyculture/early-europeans-in-louisiana.htm | 2026-10-14 | [V] |
| NPS-SFGOLD | National Park Service, Gold Rush Transforms San Francisco | https://www.nps.gov/places/000/gold-rush-transforms-san-francisco.htm | 2026-10-14 | [V] |
| OCTB | Osaka Convention & Tourism Bureau, Osaka official travel guide (home: 'long history of prosperity as an economic and cultural center'; Yodoyabashi/Kitahama/Semba 'heart of the commercial city'). Tourism body; self-description, attributed | https://osaka-info.jp/en/ | 2026-10-14 | [V] |
| OSAKA-CASTLE | Osaka Castle Tenshukaku (Osaka Castle Museum) official site; predecessor Osaka (Ishiyama) Honganji; construction by Toyotomi Hideyoshi (Japanese text) | https://www.osakacastle.net/english/ | 2026-10-14 | [V] |
| PC-MTLBIRTH | Parks Canada, Directory of Federal Heritage Designations: Montréal's Birthplace National Historic Site | https://www.pc.gc.ca/apps/dfhd/page_nhs_eng.aspx?id=652 | 2026-10-14 | [V] |
| PORT-LA | Port of Los Angeles, About (self-description: busiest seaport in the Western Hemisphere) | https://www.portoflosangeles.org/about | 2026-10-14 | [V] (self-claim) |
| PORT-ROTTERDAM | Port of Rotterdam Authority, home page (self-description) | https://www.portofrotterdam.com/en | 2026-10-14 | [V] |
| PREF-HIROSHIMA | Hiroshima Prefectural Government, 'The Atomic Bombing & Reconstruction of Hiroshima' ('first use of a nuclear weapon in war'; Hiroshima 6 Aug 1945, Nagasaki 9 Aug 1945) | https://www.pref.hiroshima.lg.jp/site/peace80-en/reconstruction-index.html | 2026-10-14 | [V] |
| SP-GOV-HIST | Governo do Estado de São Paulo, "História do Estado de São Paulo" (1554 Jesuit college; coffee; "maior centro industrial do país", said of the state) | https://www.sp.gov.br/sp?1dmy&urile=wcm%3apath%3a/wcm/connect/saopaulo_content/saopaulo/conheca+sp/historia | 2026-10-14 | [V] |
| SYD-ABORIGINAL | City of Sydney, "Aboriginal histories" (Port Jackson = Sydney Harbour) | https://www.cityofsydney.nsw.gov.au/history/aboriginal-histories | 2026-10-14 | [V] |
| SYD-COUNCIL-HIST | City of Sydney, "History of City of Sydney council" | https://www.cityofsydney.nsw.gov.au/history/history-city-sydney-council | 2026-10-14 | [V] |
| TREATY-NANKING | Treaty of Nanking (Treaty of Peace, Friendship, and Commerce), signed 29 Aug 1842, Arts 2 and 5; validated transcription of the UK ratified text on Wikisource (primary text, transcription host) | https://en.wikisource.org/wiki/Treaty_of_Nanking (oldid 15172278) | 2026-10-14 | [V] |
| U-AE-DUBAI | UAE Government portal, "Dubai" (the seven emirates) | https://u.ae/en/about-the-uae/the-seven-emirates/dubai | 2026-10-14 | [V] |
| UN-VISIT | United Nations Visitors Services New York (UN Headquarters address, 46th St & 1st Ave, New York) | https://visit.un.org/ | 2026-10-14 | [V] |
| UNESCO-ALEPPO | UNESCO WHC 21, Ancient City of Aleppo (Wayback snapshot of 20260107190453) | https://whc.unesco.org/en/list/21/ | 2026-10-14 | [V] |
| UNESCO-CUSCO | UNESCO World Heritage Centre, City of Cuzco (list 273), via Wayback snapshot 20260109093454 | https://web.archive.org/web/20260109093454/https://whc.unesco.org/en/list/273/ | 2026-10-14 | [V] |
| UNESCO-FLORENCE | UNESCO WHC 174, Historic Centre of Florence (Wayback snapshot of 20251230070943) | https://whc.unesco.org/en/list/174/ | 2026-10-14 | [V] |
| UNESCO-HAMBURG | UNESCO WHC 1467, Speicherstadt and Kontorhaus District with Chilehaus (Wayback snapshot of 20251204181704) | https://whc.unesco.org/en/list/1467/ | 2026-10-14 | [V] |
| UNESCO-HIROSHIMA | UNESCO WHC, Hiroshima Peace Memorial (Genbaku Dome), list/775 (Wayback snapshot 20260103034357) | https://whc.unesco.org/en/list/775/ | 2026-10-14 | [V] |
| UNESCO-ISFAHAN | UNESCO WHC 115, Meidan Emam, Esfahan (Wayback snapshot 20250111224101) | https://whc.unesco.org/en/list/115/ | 2026-10-14 | [V] |
| UNESCO-ISTANBUL | UNESCO WHC 356, Historic Areas of Istanbul (Wayback snapshot of 20251228090323) | https://whc.unesco.org/en/list/356 | 2026-10-14 | [V] |
| UNESCO-KYOTO | UNESCO WHC, Historic Monuments of Ancient Kyoto, list/688 (Wayback snapshot 20260104105456) | https://whc.unesco.org/en/list/688/ | 2026-10-14 | [V] |
| UNESCO-MELAKA | UNESCO WHC, Melaka and George Town, list/1223 (Wayback snapshot 20251231193358) | https://whc.unesco.org/en/list/1223/ | 2026-10-14 | [V] |
| UNESCO-MUMBAI-VG | UNESCO WHC, Victorian Gothic and Art Deco Ensembles of Mumbai (list 1480), Wayback 20260114004549 | https://whc.unesco.org/en/list/1480 | 2026-10-14 | [V] |
| UNESCO-POTOSI | UNESCO World Heritage Centre, City of Potosí (list 420), via Wayback snapshot 20251222122022 | https://web.archive.org/web/20251222122022/https://whc.unesco.org/en/list/420/ | 2026-10-14 | [V] |
| UNESCO-SAMARKAND | UNESCO WHC, Samarkand – Crossroad of Cultures (list 603), Wayback 20260113085920 | https://whc.unesco.org/en/list/603 | 2026-10-14 | [V] |
| UNESCO-SEVILLE | UNESCO WHC 383, Cathedral, Alcázar and Archivo de Indias in Seville (Wayback snapshot of 20251228065742) | https://whc.unesco.org/en/list/383 | 2026-10-14 | [V] |
| UNESCO-SILKROADS | UNESCO WHC, Silk Roads: the Routes Network of Chang'an-Tianshan Corridor (1442), description and brief synthesis, via Wayback snapshot 20260109105211 | https://whc.unesco.org/en/list/1442/ | 2026-10-14 | [V] |
| UNESCO-STONETOWN | UNESCO WHC, Stone Town of Zanzibar (list 173), Wayback 20251228030326 | https://whc.unesco.org/en/list/173 | 2026-10-14 | [V] |
| UNESCO-STPETERSBURG | UNESCO WHC 540, Historic Centre of Saint Petersburg (Wayback snapshot of 20260106200713) | https://whc.unesco.org/en/list/540/ | 2026-10-14 | [V] |
| UNESCO-TIMBUKTU | UNESCO WHC, Timbuktu (list 119), Wayback 20251228001713 | https://whc.unesco.org/en/list/119 | 2026-10-14 | [V] |
| UNESCO-VENICE | UNESCO WHC 394, Venice and its Lagoon (Wayback snapshot of 20260116090630) | https://whc.unesco.org/en/list/394 | 2026-10-14 | [V] |

## Deferred (not fact-checked)

Unpolished drafts for secondary and demoted cities, kept as written and **not fact-checked**. Some keys here point to cities.md's Sources list; others (for example BRIT-COPPERBELT and BRIT-KUMASI) are search-text keys that the region drafts did not record. Re-ground every row before use. Rows are ordered by region; `demoted` means the row was core before the final list.

| slug | region | tier | name | country | blurb | keys |
|---|---|---|---|---|---|---|
| city-yem-aden | 8 | secondary | Aden | Yemen | A port on the Gulf of Aden, its old quarter set in the crater of an extinct volcano. The British held a protectorate around it from the 19th century until 1967, after which it was the centre of South Yemen until unification in 1990. Yemen's Presidential Leadership Council calls it the "interim capital" *(as of 2026-10; verify)*. | FB-ym [V]; PLC-ADEN [V]; BRIT-ADEN [S] |
| city-tza-dar-es-salaam | 9 | secondary | Dar es Salaam | Tanzania | Tanzania's largest city and main port, on the Indian Ocean coast. It was the capital under German rule and after independence, until Dodoma was named the new capital; Dodoma is the capital today. | FB-tz [V]; BRIT-DARESSALAAM [S] |
| city-ken-mombasa | 9 | demoted | Mombasa | Kenya | Kenya's chief port on the Indian Ocean, one of the trade centres that have existed on this coast, once called the Land of Zanj, since at least the 2nd century. The Portuguese used it as a base to try to monopolise Indian Ocean trade and built Fort Jesus there at the end of the 16th century; the fort later passed to Arab, Swahili and English control. | FB-ke [V]; UNESCO-FORTJESUS [V] |
| city-egy-luxor | 10 | secondary | Luxor | Egypt | On the Nile far south of Cairo, on the site of ancient Thebes, the city of the god Amun and Egypt's capital in the Middle and New Kingdoms. The temples of Karnak and Luxor stand on the east bank; the Valley of the Kings and the Valley of the Queens lie on the west. | UNESCO-THEBES [V]; FB-eg [V] |
| city-mar-marrakesh | 10 | secondary | Marrakesh | Morocco | Founded by the Almoravids around 1070 and later capital of the Almohads, it was long a major political, economic and cultural centre of the western Muslim world, ruling across North Africa and Andalusia. The English name Morocco derives from Marrakesh, a former capital. | UNESCO-MARRAKESH [V]; FB-mo [V] |
| city-mar-casablanca | 10 | demoted | Casablanca | Morocco | Morocco's main port and economic capital, on the Atlantic coast. Its man-made harbour, protected by a breakwater, handles most of the country's foreign trade; it became the chief port under the French protectorate. | FB-mo [V]; BRIT-CASABLANCA [S] |
| city-nga-kano | 11 | secondary | Kano | Nigeria | In northern Nigeria, Kano was one of the large Islamic kingdoms that dominated the north, and one of the seven original Hausa states. Camel caravans of the trans-Saharan trade made it rich, and its old city is enclosed by a massive wall. | FB-ni [V]; BRIT-KANO [S] |
| city-gha-kumasi | 11 | secondary | Kumasi | Ghana | In the forested south of Ghana, Kumasi was the capital of the Asante Empire, which by the mid-18th century was a highly organised state of immense wealth. The Asante fought the British in a series of 19th-century wars, and Kumasi is still the seat of the Asantehene, the Asante king. | FB-gh [V]; BRIT-KUMASI [S] |
| city-civ-abidjan | 11 | secondary | Abidjan | Côte d'Ivoire | Côte d'Ivoire's main port and former capital, after which the national anthem, "L'Abidjanaise", is named. The Factbook lists it as the administrative and economic capital, with Yamoussoukro as the legislative capital *(as of 2026-10; verify)*. | FB-iv [V] |
| city-nga-lagos | 11 | demoted | Lagos | Nigeria | Built on islands and lagoon shores on the Bight of Benin. Nigeria's capital until Abuja replaced it in 1991, it remains the country's largest city, its leading commercial and industrial centre and a key port. | FB-ni [V]; BRIT-LAGOS [S] |
| city-cmr-douala | 12 | secondary | Douala | Cameroon | On the Wouri River estuary at the Atlantic coast, Cameroon's chief port and main industrial centre. Its deepwater port handles most of the country's overseas trade and much of the goods traded by landlocked Chad and the Central African Republic. | FB-cm [V]; BRIT-DOUALA [S]; BRIT-CAMEROON-TRANSPORT [S] |
| city-cod-lubumbashi | 12 | secondary | Lubumbashi | Congo (Kinshasa) | In the far southeast of the DR Congo, on the Copperbelt that runs into Zambia. Founded by Belgian colonists as the copper-mining town of Élisabethville, it is the industrial centre of the mining district and the headquarters of the state miner Gécamines. | GECAMINES [V]; FB-cg [V]; BRIT-LUBUMBASHI [S]; BRIT-COPPERBELT [S] |
| city-pak-lahore | 14 | secondary | Lahore | Pakistan | Its fort and Shalimar Gardens are outstanding examples of Mughal art at its height in the 16th and 17th centuries, built up under Akbar, Jahangir and Shah Jahan. | UNESCO-LAHORE [V]; FB-pk [V] |
| city-ind-bengaluru | 14 | secondary | Bengaluru | India | The capital of Karnataka, on a ridge of the Deccan plateau in southern India. It is India's centre of information-technology industry, nicknamed India's Silicon Valley, and Infosys and Wipro are headquartered there. | BRIT-BENGALURU [S] |
| city-ind-chennai | 14 | secondary | Chennai | India | On the Coromandel Coast of the Bay of Bengal. The English East India Company built Fort St George here, beside the fishing village of Madraspatnam; it was the company's first fortified settlement in India, and the city was long called Madras. | FB-in [V]; BRIT-CHENNAI [S]; BRIT-FORTSTGEORGE [S] |
| city-ind-varanasi | 14 | secondary | Varanasi | India | On the Ganges, also called Kashi or Benares. For Hindus it is the ultimate place of pilgrimage, and dying there is believed to bring salvation; the district administration calls it one of the oldest living cities in the world. | VARANASI-NIC [V] |
| city-ind-agra | 14 | secondary | Agra | India | On the Yamuna, Agra was the capital of the Mughal Empire under Akbar, Jahangir and Shah Jahan. Akbar raised its Red Fort, and Shah Jahan built the Taj Mahal on the river's right bank in memory of his wife Mumtaz Mahal. | AGRA-NIC [V]; UNESCO-TAJ [V]; UNESCO-AGRAFORT [V] |
| city-pak-peshawar | 14 | secondary | Peshawar | Pakistan | Near the eastern end of the Khyber Pass, one of the traditional invasion routes between Central Asia and India. It has long been a centre of caravan trade with Afghanistan and Central Asia. | FB-pk [V]; BRIT-PESHAWAR [S]; BRIT-KHYBER [S] |
| city-pak-karachi | 14 | demoted | Karachi | Pakistan | On the Arabian Sea coast just northwest of the Indus delta, Pakistan's largest city and main seaport. It was the national capital after independence, until the government chose to build Islamabad. | FB-pk [V]; BRIT-KARACHI [S]; BRIT-ISLAMABAD [S] |
| city-afg-herat | 15 | secondary | Herat | Afghanistan | In the Hari River valley in western Afghanistan. The Timurid ruler Shah Rokh made it his capital, and it became a centre of Persian culture, with a renowned library and its own school of miniature painting. | BRIT-SHAHROKH [S]; BRIT-TIMURID [S]; BRIT-HARIRUD [S]; BRIT-HERATSCHOOL [S] |
| city-irn-tabriz | 15 | secondary | Tabriz | Iran | Capital of Iran's East Azerbaijan province. The Mongol Il-Khan Ghazan made it his capital, and it was later the first Safavid capital. Its covered bazaar, on one of the most frequented east–west trade routes, was among Asia's most important trading centres between the 12th and 18th centuries. | UNESCO-TABRIZ [V]; FB-ir [V]; BRIT-TABRIZ [S] |
| city-irn-shiraz | 15 | secondary | Shiraz | Iran | The city of the Persian poets Hafez and Saadi. The ruins of Persepolis, founded by Darius I as the capital of the Achaemenid Empire, lie nearby. | UNESCO-PERSEPOLIS [V]; BRIT-SHIRAZ [S, carried]; BRIT-PERSEPOLIS [S, carried] |
| city-kaz-almaty | 15 | demoted | Almaty | Kazakhstan | In the northern foothills of the Trans-Ili Alatau in Kazakhstan's southeast. It was the capital of Soviet Kazakhstan and then of independent Kazakhstan until the capital moved to Astana, and it remains the country's largest city and its commercial and cultural centre. | FB-kz [V]; BRIT-ALMATY [S] |
| city-kor-busan | 16 | core (demoted) | Busan | South Korea | UNPOLISHED. Korea's main port, on the southeast coast. During the Korean War it served as the wartime capital of the Republic of Korea, and Pier 1 of Busan Port was the main gateway for goods and people. | BUSAN-WARTIME [V]; FB-ks [V]; BRIT-BUSAN [S] |
| city-aus-melbourne | 18 | core (demoted) | Melbourne | Australia | UNPOLISHED. Capital of Victoria, on Port Phillip Bay; it grew with the gold rushes that began in Victoria in the 1850s. The first Commonwealth Parliament opened in Melbourne's Exhibition Building on 9 May 1901, and the city was the seat of federal government until the move to Canberra. | APH-BRIEF2 [V]; FB-as [V]; BRIT-MELBOURNE [S] |
| city-usa-houston | 19 | secondary | Houston | United States of America | Port Houston runs public facilities along the Houston Ship Channel, opened in 1914. NASA's Johnson Space Center in Houston is home to Mission Control and the astronaut corps. | PORTHOU [V]; PORTHOU-HIST [V]; NASA-JSC [V] |
| city-usa-philadelphia | 19 | secondary | Philadelphia | United States of America | The Declaration of Independence and the US Constitution were both debated and signed in Independence Hall. | NPS-INDE [V]; FB-us [V] |
| city-usa-miami | 19 | secondary | Miami | United States of America | PortMiami brands itself the "Cargo Gateway of the Americas". | PORTMIAMI [V] |
| city-usa-detroit | 19 | secondary | Detroit | United States of America | The MotorCities National Heritage Area says Detroit earned the title Motor City, the auto capital of the world. | MOTORCITIES [V] |
| city-can-vancouver | 19 | secondary | Vancouver | Canada | Chosen as the western terminus of the Canadian Pacific Railway; the railway's link to a natural harbour made it a transshipment point. | VAN-HCS [S]; FB-ca [V] |
| city-usa-honolulu | 19 | secondary | Honolulu | United States of America | Iolani Palace in downtown Honolulu was the official residence of the Hawaiian monarchs. Pearl Harbor, attacked on 7 December 1941, is a short drive away. | IOLANI [V]; NPS-PERL [V]; NPS-PERL-DIR [V] |
| city-mex-veracruz | 19 | secondary | Veracruz | Mexico | Cortés's expedition founded Villa Rica de la Vera Cruz on 22 April 1519, at a site that differs from the present port. | NOTICONQ [V]; FB-mx [V] |
| city-can-toronto | 19 | core (demoted) | Toronto | Canada | Began in 1793, when British officials in Upper Canada built Fort York on Toronto Bay and moved the colonial capital there from Niagara. The city describes itself as Canada's largest financial centre and its banking and stock-exchange centre. | TOR-INST [V]; TOR-FIN [V] |
