# Blurbs: regions 14–18 (South Asia to Oceania)

> **World Atlas P2.7c, 2026-10-14.** Grounding blurbs for every country card and every capital card in regions 14–18, in ring order. Each capital row follows its country; the order engine applies the 2–3-card lag. Region 17 has no capital row for Singapore (same-name rule). Nauru's capital, Yaren, is hand-placed. These rows feed the `note` field in `countries.yaml`.

**Keys.**
- **[V]** means verified at a primary source that was opened: a Factbook mirror file, a UN page, or an official government page.
- **[S]** means confirmed through search results only (mostly Britannica, whose pages return 403 to direct fetches).
- The key ids resolve in [Sources](#sources).
- No figure appears unless it is [V].
- Time-sensitive items carry "(as of 2026-10, verify)".

**Disputes.** Country blurbs take no side. Kashmir, Aksai Chin, Arunachal Pradesh and the Kurils follow the administering power in the outline and have their own dispute cards, which another stream writes.

**Factbook caveat.** The `fb:` keys cite the community mirror `factbook/factbook.json` on its `master` branch. The plan pins commit `144d6977`, which GitHub doesn't resolve, so the files weren't read at that commit. The mirror's last data update predates the CIA's retirement of the Factbook (2026-02-04). Check any figure against an archived cia.gov copy before release.

## 14 South Asia

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| maldives | country | Maldives | A chain of low-lying coral atolls in the Indian Ocean, south-southwest of India. It is the smallest country in Asia, and its islands are so low-lying that even the highest point is only a few metres above the sea. | [V] fb:mv; [S] brit:maldives |
| male | capital | Malé | The capital and largest city, covering almost all of Malé island in the Malé Atoll. Its name may come from the Sanskrit for "garland". | [V] fb:mv; [S] brit:male |
| sri-lanka | country | Sri Lanka | A teardrop-shaped island in the Indian Ocean, just south of India. A chain of shoals called Adam's Bridge almost links it to the Indian coast. | [V] fb:ce |
| sri-jayewardenepura-kotte | capital | Sri Jayewardenepura Kotte | The official (legislative) capital, a suburb just southeast of Colombo where the parliament sits on an island in a lake. Colombo, the largest city and port, is the commercial capital and still holds the president's and prime minister's offices. | [V] fb:ce; [V] lk:parliament; [S] brit:kotte |
| india | country | India | It fills most of the South Asian subcontinent, a peninsula between the Arabian Sea and the Bay of Bengal, with the Himalayas along its northern edge. Its outline follows the areas it administers in Kashmir; the disputed areas have their own cards. | [V] fb:in; [V] plan:borders |
| new-delhi | capital | New Delhi | A planned capital built by the British just south of Old Delhi, on the west bank of the Yamuna River. It was built as the capital of British India and stayed the capital after independence. | [V] fb:in; [S] brit:new-delhi |
| bangladesh | country | Bangladesh | Almost wholly surrounded by India, it touches Myanmar in the southeast and opens south onto the Bay of Bengal. Most of the country lies on the delta where the Ganges, Brahmaputra and Meghna rivers meet. | [V] fb:bg |
| dhaka | capital | Dhaka | The capital and largest city, on the Buriganga River in the middle of the great delta. It became a national capital when Bangladesh became independent. | [V] fb:bg; [S] brit:dhaka |
| bhutan | country | Bhutan | A landlocked Himalayan kingdom between China and India that controls several key mountain passes. It is a constitutional monarchy. | [V] fb:bt |
| thimphu | capital | Thimphu | A small capital high in a Himalayan river valley in western Bhutan. Its name is traditionally explained as "dissolving rock", after a local deity said to have merged into the rock where the city stands. | [V] fb:bt; [S] brit:thimphu |
| nepal | country | Nepal | A landlocked country on the Himalayan slope between China and India. It holds several of the world's highest peaks, including Mount Everest on its border with China. | [V] fb:np |
| kathmandu | capital | Kathmandu | The capital sits in the Kathmandu Valley in the centre of the country, near where the Bagmati and Vishnumati rivers meet. Its name is said to mean "wooden temple". | [V] fb:np; [S] brit:kathmandu |
| pakistan | country | Pakistan | It runs from the Arabian Sea north to the high mountains, between India to the east and Iran and Afghanistan to the west. It holds the Khyber and Bolan passes, old routes from Central Asia into India; its outline follows the areas it administers in Kashmir, and the disputed areas have their own cards. | [V] fb:pk; [V] plan:borders |
| islamabad | capital | Islamabad | A planned capital built on the Potwar Plateau beside the older city of Rawalpindi, in the north. It replaced Karachi, the coastal port that was the first capital. | [V] fb:pk; [S] brit:islamabad |

## 15 Iran & Central Asia

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| afghanistan | country | Afghanistan | A landlocked, mountainous country between Pakistan and Iran, split by the Hindu Kush; its thin Wakhan Corridor reaches east to touch China. The Taliban took back control when US-led forces withdrew, and very few states formally recognise their government (as of 2026-10, verify). | [V] fb:af; [S] brit:afghanistan; [S] brit:taliban-2021 |
| kabul | capital | Kabul | The capital and largest city, in a mountain valley on the Kabul River, south of the Hindu Kush. It commands routes north and south, and east to Pakistan through the Khyber Pass. | [V] fb:af; [S] brit:kabul |
| iran | country | Iran | A large country between Iraq and Pakistan, with the Caspian Sea to the north and the Persian Gulf and Gulf of Oman to the south. It was long known to outsiders as Persia, and it holds the north shore of the Strait of Hormuz. | [V] fb:ir |
| tehran | capital | Tehran | The capital lies at the southern foot of the Elburz (Alborz) Mountains, in the north of the country. It has been the capital since the late 1700s, under the Qajar dynasty. | [V] fb:ir; [S] brit:tehran |
| turkmenistan | country | Turkmenistan | A Central Asian country on the east shore of the Caspian Sea, between Iran and Kazakhstan. Most of it is the Karakum desert. | [V] fb:tx; [S] brit:ashgabat |
| ashgabat | capital | Ashgabat | The capital sits in an oasis at the northern foot of the Kopet Dag mountains, on the edge of the Karakum desert and close to the Iranian border. It began as a Russian fort in the 19th century. | [V] fb:tx; [S] brit:ashgabat |
| uzbekistan | country | Uzbekistan | The central country of Central Asia, north of Turkmenistan and south of Kazakhstan. It is one of only two doubly landlocked countries in the world; the other is Liechtenstein. | [V] fb:uz |
| tashkent | capital | Tashkent | Uzbekistan's capital and the largest city in Central Asia, in the Chirchiq River valley in the northeast of the country. Its name is usually read as "stone town". | [V] fb:uz; [S] brit:tashkent |
| tajikistan | country | Tajikistan | A small, landlocked, very mountainous country west of China and south of Kyrgyzstan, with the Pamirs in its east. Its highest peak, Ismoil Somoni, was once the tallest mountain in the Soviet Union. | [V] fb:ti; [S] brit:pamirs |
| dushanbe | capital | Dushanbe | The capital lies in the Gissar (Hisor) valley on the Varzob River, in the southwest of the country. Its name means "Monday" in Persian, after a Monday bazaar held at the site. | [V] fb:ti; [S] brit:dushanbe |
| kyrgyzstan | country | Kyrgyzstan | A landlocked country west of China and south of Kazakhstan, entirely mountainous and dominated by the Tien Shan range. | [V] fb:kg |
| bishkek | capital | Bishkek | The capital lies in the Chüy (Chu) valley near the Kyrgyz Range of the Tien Shan. It was called Frunze in Soviet times and took back the name Bishkek in 1991. | [V] fb:kg; [S] brit:bishkek |
| kazakhstan | country | Kazakhstan | The world's largest landlocked country, a vast steppe between Russia and China with a small part west of the Ural River in Europe. Russia leases the Baikonur Cosmodrome inside it; the card's outline includes Baikonur. | [V] fb:kz; [V] plan:borders |
| astana | capital | Astana | A planned capital on the Ishim River in the steppe of north-central Kazakhstan, which replaced Almaty as capital. Its name means "capital"; it was briefly renamed Nur-Sultan and then went back to Astana. | [V] fb:kz; [S] brit:astana |

## 16 East Asia

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| china | country | China | China fills much of eastern Asia, with coasts on the Yellow, East China and South China seas and, with Russia, it borders more countries than any other. Its great rivers, the Yangtze and the Huang He (Yellow River), run east to the Pacific, and Mount Everest stands on its border with Nepal. Recorded Chinese civilisation reaches back to the Shang dynasty, and emperors ruled until the early 20th century. | [V] fb:ch; [V] fb:rs; [S] brit:north-china-plain |
| beijing | capital | Beijing | China's capital, on the northwest edge of the North China Plain. Its name means "northern capital", and it has been China's capital for most of the last six centuries. | [V] fb:ch; [S] brit:north-china-plain; [S] brit:beijing |
| mongolia | country | Mongolia | A landlocked country sandwiched between Russia to the north and China to the south. Most of it is steppe, semidesert and mountains, with the Gobi Desert in the south. It was the homeland of Genghis Khan, whose Mongol Empire stretched across much of Eurasia. | [V] fb:mg |
| ulaanbaatar | capital | Ulaanbaatar | Mongolia's capital and largest city, on the Tuul River on a windswept plateau. | [V] fb:mg; [S] brit:ulaanbaatar |
| north-korea | country | North Korea | The northern half of the Korean Peninsula, bordering China and, for a short stretch, Russia, with the Yellow Sea's Korea Bay to the west and the Sea of Japan to the east. Korea was divided after the Second World War, and since the Korean War a demilitarised zone has separated North from South. It is a single-party communist state. | [V] fb:kn; [S] brit:korean-war |
| pyongyang | capital | Pyongyang | North Korea's capital, in the west of the country on the Taedong River, inland from Korea Bay. | [V] fb:kn; [S] brit:pyongyang |
| south-korea | country | South Korea | The southern half of the Korean Peninsula, between the Yellow Sea and the Sea of Japan. Its only land border is the demilitarised zone with North Korea, which roughly follows the 38th parallel. | [V] fb:ks; [S] brit:korean-war |
| seoul | capital | Seoul | South Korea's capital, on the Han River in the northwest of the country, not far south of the border with North Korea. Some ministries have moved to the planned city of Sejong, which serves as an administrative capital. | [V] fb:ks; [S] brit:seoul |
| japan | country | Japan | An island chain off the east coast of mainland Asia, between the Sea of Japan and the Pacific Ocean. Its four main islands, from north to south, are Hokkaido, Honshu, Shikoku and Kyushu, and the country is mostly rugged mountains. It sits on the Pacific Ring of Fire and has frequent earthquakes. | [V] fb:ja |
| tokyo | capital | Tokyo | Japan's capital, on the Pacific coast of central Honshu at the head of Tokyo Bay. It was called Edo until the emperor moved there from Kyoto and renamed it Tokyo, "eastern capital". | [V] fb:ja; [S] brit:tokyo |
| taiwan | country | Taiwan | A mountainous island off the southeast coast of China, across the Taiwan Strait, north of the Philippines. It has been governed from Taipei under the name Republic of China since the Nationalist government withdrew there at the end of the Chinese civil war; the People's Republic of China claims it. Only a small number of states recognise it diplomatically (as of 2026-10, verify). | [V] fb:tw; [V] mofa-tw-allies; [S] brit:taiwan |
| taipei | capital | Taipei | Taiwan's seat of government, in a river basin near the island's northern tip. Its name means "northern Taiwan". | [V] fb:tw; [S] brit:taipei |

## 17 Southeast Asia

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| philippines | country | Philippines | An archipelago of thousands of islands between the Philippine Sea and the South China Sea, east of Vietnam and south of Taiwan. It lies on the Ring of Fire and in the Pacific typhoon belt. A Spanish colony for over three centuries, it passed to the United States after the Spanish-American War. | [V] fb:rp |
| manila | capital | Manila | The Philippines' capital, on Luzon, the largest island, on the eastern shore of Manila Bay at the mouth of the Pasig River. | [V] fb:rp; [S] brit:manila |
| malaysia | country | Malaysia | Malaysia is in two parts: the southern Malay Peninsula, bordering Thailand, and the northern third of Borneo, which it shares with Indonesia and Brunei. The South China Sea separates the two halves. The Strait of Malacca, along its west coast, has carried trade between the Indian Ocean and East Asia for centuries. | [V] fb:my |
| kuala-lumpur | capital | Kuala Lumpur | Malaysia's capital, on the Malay Peninsula, where the Kelang and Gombak rivers meet; the name means "muddy confluence". Parliament meets here, but most federal government offices have moved to Putrajaya, a planned administrative centre to the south. | [V] fb:my; [S] brit:kuala-lumpur; [S] brit:putrajaya |
| brunei | country | Brunei | A small sultanate on the north coast of Borneo, facing the South China Sea and otherwise surrounded by Malaysia. Malaysian territory splits it into two parts. | [V] fb:bx |
| bandar-seri-begawan | capital | Bandar Seri Begawan | Brunei's capital, on the Brunei River near Brunei Bay. Kampong Ayer, a village of houses on stilts over the river, faces the city. | [V] fb:bx; [S] brit:bandar-seri-begawan |
| singapore | country | Singapore | A city-state on islands off the southern tip of the Malay Peninsula, between Malaysia and Indonesia, at the focus of Southeast Asia's sea routes. The British founded the modern port. The city is the whole country, so it has no separate capital card. | [V] fb:sn |
| thailand | country | Thailand | Thailand is at the heart of mainland Southeast Asia, between the Andaman Sea and the Gulf of Thailand. It borders Myanmar, Laos, Cambodia and Malaysia, and a long narrow arm runs south down the Malay Peninsula. It is a constitutional monarchy. | [V] fb:th |
| bangkok | capital | Bangkok | Thailand's capital and chief port, on the Chao Phraya River delta, a short distance inland from the Gulf of Thailand. Thais call it Krung Thep. | [V] fb:th; [S] brit:bangkok |
| myanmar | country | Myanmar | The westernmost country of mainland Southeast Asia, on the Bay of Bengal and Andaman Sea between Bangladesh and India to the west and China, Laos and Thailand to the east. It is also called Burma, and it was under British rule until independence. Its armed forces have dominated government for most of the time since, including after a 2021 coup (as of 2026-10, verify). | [V] fb:bm |
| naypyidaw | capital | Naypyidaw | Myanmar's capital, a planned city built in the interior; the government moved there from Yangon in the mid-2000s. Yangon (Rangoon), on the coast, was the capital before that and is still the largest city. | [V] fb:bm; [S] brit:nay-pyi-taw; [S] brit:yangon |
| laos | country | Laos | The only landlocked country in Southeast Asia, mountainous and thickly forested, between Thailand and Vietnam. The Mekong River forms much of its western border with Thailand. | [V] fb:la |
| vientiane | capital | Vientiane | Laos's capital, on the Mekong River, across from Thailand. | [V] fb:la; [S] brit:mekong |
| vietnam | country | Vietnam | A long, narrow country on the eastern edge of mainland Southeast Asia, facing the South China Sea and bordering China, Laos and Cambodia. Its two great deltas are the Red River in the north and the Mekong in the south. | [V] fb:vm; [V] fb:ch |
| hanoi | capital | Hanoi | Vietnam's capital, in the north on the Red River; the name means roughly "inside the river". It was the capital of the first independent Vietnamese state, Dai Viet, under the name Thang Long. | [V] fb:vm |
| cambodia | country | Cambodia | Cambodia lies on the Gulf of Thailand, between Thailand, Laos and Vietnam. Its lowland of rice paddies and forest is dominated by the Mekong and the Tonle Sap, Southeast Asia's largest freshwater lake. It is the heart of the old Khmer (Angkor) Empire. | [V] fb:cb |
| phnom-penh | capital | Phnom Penh | Cambodia's capital, in the south-central lowland where the Mekong meets the river from the Tonle Sap. | [V] fb:cb; [S] brit:phnom-penh |
| indonesia | country | Indonesia | The world's largest country made up only of islands, an archipelago straddling the equator between the Indian and Pacific oceans. Its main islands include Sumatra, Java, part of Borneo, Sulawesi and the western half of New Guinea. It shares land borders with Malaysia, Papua New Guinea and Timor-Leste. | [V] fb:id |
| jakarta | capital | Jakarta | Indonesia's capital, on the northwest coast of Java on the Java Sea; under Dutch rule it was called Batavia. A new capital, Nusantara, is being built on Borneo, but Jakarta stays the legal capital until a presidential decree makes the move (as of 2026-10, verify). | [V] fb:id; [V] mkri-71-ikhtisar; [S] brit:jakarta; [S] mkri-2026-05-12 |
| timor-leste | country | Timor-Leste | Timor-Leste, also called East Timor, covers the eastern half of the island of Timor, at the eastern end of the Indonesian archipelago, northwest of Australia. It also holds the exclave of Oecussi, surrounded by Indonesian territory. A former Portuguese colony, it was occupied by Indonesia and became independent after a UN-run vote and transition. | [V] fb:tt; [S] brit:dili |
| dili | capital | Dili | Timor-Leste's capital, largest city and main port, on the north coast of Timor. | [V] fb:tt; [S] brit:dili |

## 18 Oceania

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| australia | country | Australia | A country that occupies a whole continent, between the Indian Ocean and the South Pacific. Aboriginal Australians have lived there for many millennia; Dutch navigators were the first Europeans to land. It is a federal parliamentary democracy and a Commonwealth realm. | [V] fb:as |
| canberra | capital | Canberra | Australia's capital, a purpose-built city in the southeast, inland between the two rival cities of Sydney and Melbourne. It was chosen as a compromise site and designed by Walter Burley Griffin after an international competition; Parliament moved there from Melbourne. | [V] fb:as; [S] brit:canberra |
| papua-new-guinea | country | Papua New Guinea | Occupies the eastern half of the island of New Guinea, plus many smaller islands, between the Coral Sea and the South Pacific. Its only land border is with Indonesia, which holds the western half of the island. It is part of Melanesia. | [V] fb:pp; [S] brit:pacific-islands |
| port-moresby | capital | Port Moresby | Papua New Guinea's capital, on the southeast coast of New Guinea facing the Gulf of Papua and the Coral Sea. It became the national capital at independence. | [V] fb:pp; [S] brit:png-capitals |
| solomon-islands | country | Solomon Islands | A Melanesian island chain in the South Pacific, east of Papua New Guinea. Its largest island, Guadalcanal, is named by Spanish explorers after a town in Spain. | [V] fb:bp; [S] brit:guadalcanal; [S] brit:pacific-islands |
| honiara | capital | Honiara | Capital of the Solomon Islands, on the north coast of Guadalcanal. It replaced Tulagi as the capital; its name comes from a local phrase meaning "facing the trade winds". | [V] fb:bp; [S] brit:png-capitals |
| vanuatu | country | Vanuatu | A chain of Melanesian islands in the South Pacific, about three-quarters of the way from Hawaii to Australia, first settled from the Solomon Islands. Before independence it was the New Hebrides, ruled jointly by Britain and France as a condominium. | [V] fb:nh; [S] brit:vanuatu |
| port-vila | capital | Port Vila | Vanuatu's capital and largest town, a port on the island of Efate. Locally it is often just called Vila. | [V] fb:nh; [S] brit:png-capitals |
| new-zealand | country | New Zealand | Two main islands, North Island and South Island, in the South Pacific, southeast of Australia. Polynesians settled it in the late Middle Ages and called it Aotearoa. It is a parliamentary democracy and a Commonwealth realm. | [V] fb:nz; [S] brit:wellington |
| wellington | capital | Wellington | New Zealand's capital, at the southern tip of the North Island on a sheltered harbour opening onto Cook Strait. The seat of government moved there from Auckland; Auckland remains the largest city. | [V] fb:nz; [S] brit:wellington |
| fiji | country | Fiji | A Melanesian island group in the South Pacific, roughly two-thirds of the way from Hawaii to New Zealand. Two large islands, Viti Levu and Vanua Levu, hold most of its land. | [V] fb:fj; [S] brit:fiji-land; [S] brit:pacific-islands |
| suva | capital | Suva | Fiji's capital and main port, on the southeast coast of Viti Levu, the largest island. Its name means "little hill" in Fijian. | [V] fb:fj; [S] brit:polynesian-capitals |
| tonga | country | Tonga | A Polynesian archipelago in the South Pacific, east of Fiji. It is a kingdom: it was a British protected state for a time but never lost its own monarchy. | [V] fb:tn; [S] brit:tonga; [S] brit:pacific-islands |
| nukualofa | capital | Nuku'alofa | Tonga's capital and chief port, on the northern shore of Tongatapu, the main island. Its harbour is sheltered by reefs. | [V] fb:tn; [S] brit:polynesian-capitals |
| samoa | country | Samoa | A Polynesian island group in the South Pacific, about halfway between Hawaii and New Zealand. Its two main islands are Upolu and Savai'i, and traditional family chiefs (matai) dominate its politics. | [V] fb:ws; [S] brit:fiji-land |
| apia | capital | Apia | Samoa's capital and port, on the north coast of Upolu. | [V] fb:ws; [S] brit:polynesian-capitals |
| tuvalu | country | Tuvalu | A chain of low coral islands and atolls in the South Pacific, about halfway from Hawaii to Australia, settled by Polynesian voyagers from Samoa or Tonga. It is a parliamentary democracy and a Commonwealth realm. | [V] fb:tv; [S] brit:pacific-islands |
| funafuti | capital | Funafuti | Tuvalu's capital is Funafuti, a ring-shaped atoll of many islets. Government offices sit in Vaiaku village on Fongafale, its largest islet. | [V] fb:tv; [S] brit:funafuti |
| kiribati | country | Kiribati | Coral atolls scattered across the central Pacific, straddling the Equator, in three groups: the Gilbert, Phoenix and Line Islands. Its people are mostly Micronesian. | [V] fb:kr; [S] brit:pacific-islands |
| tarawa | capital | Tarawa | Kiribati's capital, an atoll in the Gilbert Islands. Government is spread across islets of South Tarawa: Bairiki (executive), Ambo (parliament) and Betio (courts and port). | [V] fb:kr; [S] brit:kiribati |
| nauru | country | Nauru | A single raised coral island in the central Pacific, south of the Marshall Islands, one of the world's smallest states. Its economy was built on phosphate mining. In 2026 it told the UN that it had changed its name to the Republic of Naoero (as of 2026-10, verify). | [V] fb:nr; [V] un:naoero; [S] brit:naoero |
| yaren | capital | Yaren | Nauru has no official capital; Yaren district, on the island's south coast, holds Parliament House and most government offices. | [V] fb:nr; [S] brit:yaren |
| marshall-islands | country | Marshall Islands | Two parallel chains of coral atolls in the North Pacific, part of Micronesia, in free association with the United States (as of 2026-10, verify). Bikini and Enewetak atolls were US nuclear test sites after the Second World War. | [V] fb:rm; [S] brit:marshall-tests |
| majuro | capital | Majuro | The Marshall Islands' capital, an atoll in the eastern (Ratak) chain. Government offices are in the town of Delap-Uliga-Djarrit. | [V] fb:rm; [S] brit:majuro |
| micronesia | country | Micronesia | The Federated States of Micronesia: four island states (Yap, Chuuk, Pohnpei and Kosrae) spread across the Caroline Islands in the North Pacific, north of New Guinea. It is in free association with the United States (as of 2026-10, verify). | [V] fb:fm; [S] brit:fsm |
| palikir | capital | Palikir | Capital of the Federated States of Micronesia, on Pohnpei. It replaced Kolonia, which still hosts most embassies. | [V] fb:fm; [S] brit:fsm |
| palau | country | Palau | The westernmost Caroline Islands, in the North Pacific southeast of the Philippines. A Micronesian republic in free association with the United States (as of 2026-10, verify). | [V] fb:ps; [S] brit:palau |
| ngerulmud | capital | Ngerulmud | Palau's capitol complex, in Melekeok State on the large island of Babeldaob. It replaced Koror as the seat of government. | [V] fb:ps; [S] brit:palau |

## Flags

1. **Card name: Nauru vs Naoero.** UN page confirms Nauru notified the UN on 26 June 2026 of the name "Republic of Naoero" (un:naoero [V]). Decide whether the country card shows Naoero, Nauru, or "Naoero (Nauru)". Britannica coverage of the rename is [S] only.
2. **Card name: Ngerulmud vs Melekeok.** Factbook gives the capital as Ngerulmud (fb:ps [V]); Natural Earth labels it Melekeok (the state the capitol complex sits in). Decide which name the card shows; the blurb names both.
3. **Card name: Sri Jayewardenepura Kotte spelling.** Factbook (fb:ce) and the Parliament of Sri Lanka site (lk:parliament, opened) both spell it **Jayewardenepura**, after President J.R. Jayewardene. The plan's "Jayawardenepura" is the variant; recommend changing the plan and card to the official spelling.
4. **Sri Lanka executive offices.** "Colombo ... still holds the president's and prime minister's offices" rests on brit:kotte [S] only; the president.gov.lk and pmoffice.gov.lk pages did not return an address. Confirm or cut.
5. **Afghanistan recognition (time-sensitive).** Blurb now says "very few states formally recognise their government". Russia formally recognised the Taliban government in early July 2025, and an August 2026 report says it is still the only one; both are news leads only (the mid.ru statement could not be opened). The Factbook mirror still says "no country has recognized", so it is stale on this point. Don't name a count until a primary (Russian MFA) is opened.
6. **Myanmar government (time-sensitive).** After the military-run elections of Dec 2025–Jan 2026, parliament elected Min Aung Hlaing, the former commander-in-chief, as president on 3 April 2026 (news leads only). The blurb's "armed forces have dominated government ... including after a 2021 coup" is [V] from fb:bm and stays true under that change. fb:bm still lists him as Acting President (Factbook data predates the elections).
7. **Naypyidaw status.** The Factbook mirror (fb:bm) says the US government still recognises Rangoon/Yangon as the primary capital and calls Nay Pyi Taw the "administrative capital". The blurb follows Myanmar's own designation; decide whether the card needs that caveat.
8. **Jakarta / Nusantara (time-sensitive).** Decision 71/PUU-XXIV/2026 (12 May 2026) is now [V] at the court's own case summary: Jakarta stays the capital until the presidential decree is issued. No decree was found as of 2026-10-14 (search leads only; last reports date from 2025). Recheck before release.
9. **Taiwan recognition count (time-sensitive).** The MOFA page listed 12 allies as of 2026-10-01; the blurb deliberately gives no number.
10. **Free association (time-sensitive, low risk).** Marshall Islands, Micronesia and Palau compacts are [V] in the Factbook mirror's government type; tags kept.
11. **Factbook source.** All `fb:` reads are from `master`, not the pinned commit `144d6977` (unresolvable). At fact-check, raw.githubusercontent.com returned 403, so the checks used a local copy of the same `master` files fetched earlier on 2026-10-14. The mirror predates the CIA's retirement of the Factbook (2026-02-04); it is already stale on Afghanistan recognition and Myanmar leadership.
12. **[S]-only claims that remain.** All `brit:` keys. The ones carrying the most weight: Thimphu's river valley; New Delhi "built as the capital of British India" (rewritten at fact-check, not reconfirmed because the search budget ran out); Tehran "capital since the late 1700s"; Beijing "capital for most of the last six centuries"; Kotte's lake/island; Tarawa islet roles (Bairiki, Ambo, Betio); Tonga "alone among Pacific island groups ... never a colony" (the Factbook supports only "protectorate ... never completely lost its indigenous governance"); Apia on Upolu's north coast; Guadalcanal's naming; Ngerulmud in Melekeok State.
13. **Resolved after fact-check.** Vietnam's unkeyed "S-shaped" was dropped. Tonga's "alone among Pacific island groups ... never a colony" was softened to "a British protected state ... never lost its own monarchy", which the Factbook supports.

### Fact-check log

Fact-checked 2026-10-14.

**Rows checked (44).**
- Sample: male, new-delhi, thimphu, islamabad, tehran, tashkent, bishkek, kazakhstan, beijing, pyongyang, tokyo, manila, bandar-seri-begawan, myanmar, vietnam, indonesia, australia, solomon-islands, new-zealand, tonga, tuvalu, nauru, micronesia.
- Flagged: afghanistan, sri-lanka, sri-jayewardenepura-kotte, astana, uzbekistan, maldives, nepal, taiwan, china, seoul, laos, jakarta, naypyidaw, yaren, ngerulmud, tarawa, funafuti, marshall-islands, palau, apia.

**Rows changed (15).**
- maldives: "no island rises more than a couple of metres" contradicted fb:mv, whose highest point is 5 m. Now "even the highest point is only a few metres above the sea".
- male: the sentence was garbled (the island was called "the country's largest city"). Rewritten as "The capital and largest city, covering almost all of Malé island".
- sri-jayewardenepura-kotte: lk:parliament upgraded from [S] to [V], since parliament.lk was opened and confirms Parliament is in Kotte. Spelling confirmed as Jayewardenepura.
- new-delhi: "capital since independence" implied it became capital in 1947. Rewritten to say it was built as British India's capital and stayed the capital ([S], see flag 12).
- thimphu: "replaced Paro" was unverifiable (Britannica returned 403; other leads point to Punakha). Replaced with the Factbook etymology, which is [V].
- islamabad: "in the far north" became "in the north"; the far north is Gilgit-Baltistan.
- afghanistan: "few states recognise" became "very few states formally recognise", which stays true with Russia's July 2025 recognition.
- tashkent: "stone village" became "stone town", per fb:uz. The ambiguous "capital and largest city of Central Asia" was clarified.
- bishkek: "at independence" became "in 1991", per fb:kg. The rename came months before independence.
- china: "more neighbours than almost any other" became "with Russia, borders more countries than any other". Both have 14 in fb:ch and fb:rs [V].
- myanmar: the military-dominance sentence now covers "most of the time since [independence], including after a 2021 coup" (fb:bm [V]). It stays neutral and survives the April 2026 presidential vote.
- jakarta: added mkri-71-ikhtisar as [V], because the court's own case summary was opened. The en.mkri.id releases still return 403.
- nauru: the wording now matches the UN page: "had changed its name to the Republic of Naoero".
- palau: cut "most people live on Koror", because fb:ps places most of the population on southern Babelthuap. The sources conflict and the clause isn't needed.

**Confirmed unchanged.**
- uzbekistan: doubly landlocked with Liechtenstein, fb:uz [V].
- astana: rename chain Akmola → Astana → Nur-Sultan (2019) → Astana (2022), fb:kz [V].
- laos: landlocked, Mekong as the western border, fb:la [V].
- vietnam: Mekong and Red River deltas, fb:vm [V].
- seoul: Sejong as administrative capital, fb:ks [V].
- funafuti: Vaiaku on Fongafale, fb:tv [V].
- yaren: no official capital, fb:nr [V].
- ngerulmud: name, fb:ps [V].
- marshall-islands, micronesia, palau: free association, Factbook [V].
- taiwan: wording is neutral.
- nepal, kazakhstan, australia, tuvalu, new-zealand, micronesia (four states; Carolines north of New Guinea per fb:ps): consistent with the Factbook.

**Could not verify.**
- Russian MFA recognition statement (mid.ru connection failed).
- Indonesian presidential decree status after May 2026.
- Thimphu's predecessor capital.
- Colombo's executive offices.
- Tarawa islet roles.
- Tonga's "alone ... never a colony".

The web-search budget ran out mid-check, so these stay [S] or open (see flag 12).

## Sources

All sources accessed 2026-10-14.

### Regions 14–15

- fb:<code> — CIA World Factbook, community mirror `factbook/factbook.json`, **master branch** (the pinned commit 144d6977 did not resolve via the GitHub API or raw URLs). https://raw.githubusercontent.com/factbook/factbook.json/master/<path>, where <path> is: mv, ce, in, bg, bt, np, pk, af → `south-asia/<code>.json`; ir → `middle-east/ir.json`; tx, uz, ti, kg, kz → `central-asia/<code>.json`.
- lk:parliament — Parliament of Sri Lanka, "How to Get Here" and "Evolution of the Parliamentary System" (search snippets of the official site; parliament sits in Sri Jayewardenepura Kotte, opened 1982 on an island in the Diyawanna Oya). https://www.parliament.lk/en/visit-parliament/visiting-parliament/how-to-get-here ; https://parliament.lk/en/handbook-of-parliament/evolution-of-the-parliamentary-system — both opened at fact-check (2026-10-14): "Sri Lanka Parliament is located in the center of Sri Jayewardenepura Kotte"; the new Parliament at Sri Jayewardenepura Kotte was built 1979–82. Neither page mentions the lake/island; that detail rests on brit:kotte [S].
- fb:rs — https://raw.githubusercontent.com/factbook/factbook.json/master/central-asia/rs.json (Land boundaries: Russia, like China, lists 14 neighbouring countries; used only for the China "borders more countries" claim).
- plan:borders — `docs/world-atlas-plan.md`, Decisions table, "Borders" row (Kashmir parts follow the administering power; Baikonur goes to Kazakhstan).
- brit:maldives — https://www.britannica.com/place/Maldives
- brit:male — https://kids.britannica.com/students/article/Male/328949
- brit:kotte — https://kids.britannica.com/students/article/Sri-Jayewardenepura-Kotte/277197 ; https://www.britannica.com/place/Colombo
- brit:new-delhi — https://www.britannica.com/place/New-Delhi
- brit:dhaka — https://www.britannica.com/place/Dhaka
- brit:thimphu — https://kids.britannica.com/kids/article/Thimphu/346047 ; https://www.britannica.com/place/Paro
- brit:kathmandu — https://www.britannica.com/place/Kathmandu
- brit:islamabad — https://www.britannica.com/place/Islamabad ; https://www.britannica.com/place/Potwar-Plateau
- brit:afghanistan — https://www.britannica.com/place/Afghanistan
- brit:taliban-2021 — https://www.britannica.com/topic/How-did-the-Taliban-regain-control-of-Afghanistan-in-2021
- brit:kabul — https://www.britannica.com/summary/Kabul
- brit:tehran — https://www.britannica.com/place/Tehran
- brit:ashgabat — https://www.britannica.com/place/Ashgabat
- brit:tashkent — https://www.britannica.com/place/Tashkent
- brit:pamirs — https://www.britannica.com/place/Pamirs
- brit:dushanbe — https://kids.britannica.com/students/article/Dushanbe/274088
- brit:bishkek — https://www.britannica.com/place/Bishkek
- brit:astana — https://www.britannica.com/place/Astana-Kazakhstan ; https://www.britannica.com/topic/history-of-Kazakhstan

### Regions 16–17

- fb:ch, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/ch.json
- fb:mg, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/mg.json
- fb:kn, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/kn.json
- fb:ks, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/ks.json
- fb:ja, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/ja.json
- fb:tw, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/tw.json
- fb:rp, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/rp.json
- fb:my, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/my.json
- fb:bx, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/bx.json
- fb:sn, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/sn.json
- fb:th, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/th.json
- fb:bm, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/bm.json
- fb:la, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/la.json
- fb:vm, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/vm.json
- fb:cb, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/cb.json
- fb:id, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/id.json
- fb:tt, https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/tt.json
- mofa-tw-allies, Taiwan (ROC) Ministry of Foreign Affairs, diplomatic allies page, "Last Updated 2026-10-01": https://en.mofa.gov.tw/AlliesIndex.aspx?n=1294&sms=1007 (opened; it listed 12 allies; the blurb deliberately gives no number)
- mkri-2026-05-12, Constitutional Court of Indonesia, Decision 71/PUU-XXIV/2026 news release: https://en.mkri.id/news/details/2026-05-12/Capital_Relocation_Depends_on_Issuance_of_Presidential_Decree (direct fetch 403; search-only. A follow-up release: https://en.mkri.id/news/details/2026-06-17/Court_Declares_Petition_to_Review_DKJ_Law_Legally_Unfounded)
- mkri-71-ikhtisar, Constitutional Court of Indonesia, case summary (ikhtisar) of Decision 71/PUU-XXIV/2026, opened at fact-check: https://s.mkri.id/public/content/persidangan/sinopsis/ikhtisar_4913_2971_ikhtisar%20Put%2071_2026%20(sudah%20koreksi).pdf ("Amar Putusan: Menolak permohonan Pemohon untuk seluruhnya"; "Tanggal Putusan: Selasa, 12 Mei 2026"; the capital's position, function and role stay in DKI Jakarta until the presidential decree on relocation is issued)
- brit:north-china-plain, https://www.britannica.com/place/North-China-Plain (search only)
- brit:beijing, https://www.britannica.com/place/Beijing (search only)
- brit:korean-war, https://www.britannica.com/event/Korean-War/Armistice (search only)
- brit:ulaanbaatar, https://www.britannica.com/place/Ulaanbaatar (search only)
- brit:pyongyang, https://www.britannica.com/place/Pyongyang (search only)
- brit:seoul, https://www.britannica.com/place/Seoul (search only)
- brit:tokyo, https://www.britannica.com/place/Tokyo (search only)
- brit:taiwan, https://www.britannica.com/place/Taiwan (search only)
- brit:taipei, https://www.britannica.com/place/Taipei (search only)
- brit:manila, https://www.britannica.com/place/Manila (search only)
- brit:kuala-lumpur, https://www.britannica.com/facts/Kuala-Lumpur (search only)
- brit:putrajaya, https://www.britannica.com/place/Putrajaya (search only)
- brit:bandar-seri-begawan, https://kids.britannica.com/students/article/Bandar-Seri-Begawan/316949 and https://www.britannica.com/place/Kampong-Ayer (search only)
- brit:bangkok, https://www.britannica.com/place/Bangkok (search only)
- brit:nay-pyi-taw, https://www.britannica.com/place/Nay-Pyi-Taw (search only)
- brit:yangon, https://www.britannica.com/place/Yangon (search only)
- brit:mekong, https://www.britannica.com/place/Mekong-River (search only)
- brit:phnom-penh, https://www.britannica.com/place/Phnom-Penh (search only)
- brit:jakarta, https://www.britannica.com/place/Jakarta (search only)
- brit:dili, https://www.britannica.com/place/Dili (search only)

### Region 18

- fb:as — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/as.json
- fb:pp — https://raw.githubusercontent.com/factbook/factbook.json/master/east-n-southeast-asia/pp.json (PNG sits in the East & Southeast Asia folder of the mirror)
- fb:bp — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/bp.json
- fb:nh — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/nh.json
- fb:nz — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/nz.json
- fb:fj — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/fj.json
- fb:tn — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/tn.json
- fb:ws — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/ws.json
- fb:tv — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/tv.json
- fb:kr — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/kr.json
- fb:nr — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/nr.json
- fb:rm — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/rm.json
- fb:fm — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/fm.json
- fb:ps — https://raw.githubusercontent.com/factbook/factbook.json/master/australia-oceania/ps.json
- un:naoero — https://www.un.org/en/about-us/member-states/naoero ("On 26 June 2026, Nauru informed the United Nations that it had changed its name to Republic of Naoero.")
- brit:canberra — https://www.britannica.com/place/Canberra (search-only)
- brit:png-capitals — https://www.britannica.com/place/Papua-New-Guinea, https://www.britannica.com/place/Honiara, https://www.britannica.com/place/Vanuatu (search-only)
- brit:guadalcanal — https://www.britannica.com/place/Guadalcanal-Island (search-only)
- brit:vanuatu — https://www.britannica.com/place/Vanuatu/History (search-only)
- brit:wellington — https://www.britannica.com/place/Wellington-New-Zealand (search-only)
- brit:fiji-land — https://www.britannica.com/place/Fiji-republic-Pacific-Ocean/Land, https://www.britannica.com/science/list-of-islands-2041456 (search-only)
- brit:polynesian-capitals — https://www.britannica.com/place/Suva, https://www.britannica.com/place/Nukualofa, https://kids.britannica.com/kids/article/Samoa/117375/related/main?page=1 (search-only; Apia only via Britannica Kids)
- brit:tonga — https://www.britannica.com/place/Tonga/History (search-only)
- brit:pacific-islands — https://www.britannica.com/place/Pacific-Islands, https://www.britannica.com/place/Pacific-Islands/Colonial-rule (search-only; Melanesia/Micronesia/Polynesia groupings; Tonga as the exception to colonisation)
- brit:funafuti — https://www.britannica.com/place/Funafuti-Atoll, https://www.britannica.com/place/Fongafale (search-only)
- brit:kiribati — https://www.britannica.com/place/Kiribati (search-only)
- brit:naoero — https://www.britannica.com/place/Naoero (direct fetch 403; search-only)
- brit:yaren — https://www.britannica.com/place/Yaren (search-only)
- brit:marshall-tests — https://www.britannica.com/event/Marshall-Islands-atomic-bomb-tests (search-only)
- brit:majuro — https://www.britannica.com/place/Majuro-atoll-Marshall-Islands (search-only)
- brit:fsm — https://www.britannica.com/place/Micronesia-republic-Pacific-Ocean (search-only)
- brit:palau — https://www.britannica.com/place/Palau, https://www.britannica.com/place/Koror-island-Palau (search-only)
- Leads only (not cited): Al Jazeera 2026-07-31, ConstitutionNet 2026-08-03 and PINA reports on the Naoero amendment.
