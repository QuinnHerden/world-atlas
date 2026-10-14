# World Atlas plan

Status: in progress, 2026-10-14. P1 is done and the P2 data is in, apart from the continents; P3 is next (see [Build phases](#build-phases)). What is built is described in [architecture.md](architecture.md). This plan extends the current deck (described in [architecture.md](architecture.md)) with countries, capitals, cities and territories. This file merges three earlier planning documents (the curriculum proposal, the program architecture and the territories list); where they disagreed, the [Decisions so far](#decisions-so-far) table is the source of truth.

The design of the country cards comes from the 9-card proof of concept on branch `poc/countries` (`f4a3503`, documented in `docs/poc-countries.md` on that branch). **The PoC's de facto border view is superseded** by internationally recognised borders ([ADR 0008](adr/0008-state-list-borders-adjacency.md)); the rest of its card design stands.

## Vision

One deck, **World Atlas**, that teaches a total beginner the political and physical map of the world together.

**Curriculum.** The program is an **atlas ring**. It opens with a 1–2 day **orientation** (the oceans, the planetary wind belts and the seven continents). Then it makes **one complete pass round 21 regions** in a closed loop, and each region crossing goes over a border or a short stretch of sea. Inside a region, countries come **neighbour to neighbour**: each new country borders one already introduced, preferring the most recent. Each capital comes 2–3 cards after its country. A physical feature comes right after the countries that frame it, and a core city comes after its capital or its river. Pass 1 holds every country and capital, the territories and disputed areas, the tier 1–2 features and the core cities. A short **depth pass** then goes round the same ring again with the tier 3 features (and the secondary cities, all deferred for now). Look-alikes sit **near but not adjacent**, 3 to 10 cards apart. Suggested rate: **15 new cards a day**, about 6 weeks of new cards.

**System.** Keep one repo and one renderer. Add **card sources**: `features.yaml` (unchanged), `countries.yaml`, `territories.yaml` and `cities.yaml`. Each source has its own pydantic model and turns its entries into a plain `Card` DTO. Everything downstream works on `Card`: the order engine, deckgen, the package check and the guide. Each country/capital pair is **two notes** with two uids. `curriculum.yaml` places every country, territory and disputed area in a region; physical features get theirs from geometry. Adjacency is computed from the recognised-border outlines at build time and cached. `order.py` becomes a pipeline of pure functions: passes, then regions, then a neighbour walk, then anchored interleaving, then local repair rules. The structural change is that **positions become persisted data**: an append-only `data/positions.lock` maps uid to a sparse integer, and ankc writes it as the card's `due`. Adding a card never moves an existing card, and fresh and existing collections see the same order.

## Decisions so far

Decided 2026-10-14. The defaults still waiting for the user's confirmation are under [Open decisions](#open-decisions). The ADRs that record these decisions are listed under [ADRs](#adrs).

| Topic | Decision |
|---|---|
| Name | **World Atlas** |
| Structure | The atlas ring, starting in Western Europe. Home region first is available through a filtered deck, not a rotated build. |
| Global features | Go in the **orientation block** at the start. |
| Continents | **7 continent cards** in the orientation block. The seventh is named **"Oceania"**. They get a new `Continent` type word and family. Each continent is **composed from country outlines**; transcontinental states are split along NE's continent line. Oceania is complete (every Oceanian state and carded territory). |
| State list | **197 country cards:** the 193 UN members plus Vatican, Palestine, Kosovo and Taiwan. Northern Cyprus, Somaliland and Western Sahara get **dispute cards only**. |
| Borders | Internationally recognised borders. UN-assigned areas sit inside their sovereign: Crimea in Ukraine, Abkhazia and South Ossetia in Georgia, Transnistria in Moldova, Northern Cyprus in Cyprus, the Golan in Syria, Somaliland in Somalia. **Western Sahara is cut out of Morocco.** The Kashmir parts, Aksai Chin, Arunachal Pradesh and the Kurils follow the **administering power**. Disputed lines are drawn **dashed**. Disputed areas also get their own cards. **Israel/Golan area:** Shebaa Farms goes to Syria; East Jerusalem and the no-man's-land strips go to Palestine, and Mount Scopus goes with East Jerusalem. **Leases:** Baikonur goes to Kazakhstan, Guantánamo to Cuba. |
| Capitals | **2–3 cards after their country.** A state with several capitals gets **one card, for the official/constitutional capital**: Porto-Novo, Dodoma, Sri Jayewardenepura Kotte (that spelling), Sucre, Pretoria, Yamoussoukro, Naypyidaw. The seat of government is named in the blurb. Stale NE names are fixed (Astana, not Nur-Sultan). **No capital card** where the capital shares the country's name and dot: Monaco, Vatican, Singapore, San Marino, Luxembourg. **No capital card** for Palestine, territories or disputed areas. |
| Capital picks | **Burundi: Gitega.** **Equatorial Guinea: Malabo**; the blurb notes the announced move to Ciudad de la Paz. **Eswatini: Mbabane.** **Palau: Ngerulmud.** |
| Nauru | Capital **Yaren, hand-placed** from reference coordinates; NE has no populated_places row for Nauru. Alt name **Naoero**. |
| Names | **English exonyms** on every card. The **Gulf of Mexico** keeps that name. |
| Country tiers | **Tier 3 is microstates and small island states only.** Kosovo, Palestine and Cyprus are tier 1. Tier sets the `tier::` tag only: every country is in pass 1. |
| Cities | **42 core cities**, every one in pass 1. **No per-region minimum**: regions 2, 4, 12 and 21 have no city card. Every secondary city, Abidjan and Aden included, is deferred to the [revisit list](research/cities.md#deferred-cities-revisit-list) (user decision, 2026-10-14). **Cape Town stays a city card.** |
| Capital and city cards | Front type word: **"City"**, for capitals and other cities alike. Back: the city name, then on a second line "Capital of &lt;Country&gt;" for a capital or "&lt;Country&gt;" for any other city. Marker: a **36 px dot with no ring**. |
| Look-alikes | The **3–10 card window** plus a curated **confusable-country list**. |
| Microstates | Sit **with their neighbours** in the order, as pockets. Their capital cards follow the Capitals rule. |
| Country cards | Show the **mainland only**. Overseas territories are their own cards, per [Territories](#territories). Remote islands are cropped from the card by its `mainland` box: the Kermadecs, the Chathams and the NZ sub-Antarctic islands, Trindade, Minami-Torishima, Okinotorishima, the Prince Edward Islands and Macquarie. The crop is for the card only; adjacency and feature regions use the full outline. |
| Region and host | **`curriculum.yaml` is the one source** of region and pocket host for countries, territories and disputed areas. The entries in `countries.yaml` and `territories.yaml` carry no region. Cities take their country's region. |
| Territory placement | Geographic pockets (decision 5). **Greenland and Bermuda in region 19, the Kurils in 16, Aruba and Curaçao in 20.** `curriculum.yaml` records the alternatives, now decided, in a comment above `confusables`. |
| Dispute parties | **Claimants or administrators only.** A party that isn't one of the 197 states gets a **short label** (Transnistria, Northern Cyprus, Sahrawi Republic (Polisario Front)). |
| Feature regions | Derived by the [rules below](#assigning-physical-features-to-regions), with **overrides in `features.yaml`** (`region` plus `region_reason`): Nile 10, Karakoram 14, Danish Straits 2, Caucasus 6, Tian Shan 15, Amur 16, GIUK gap 2, Typhoon alley 17, and the Gulf Stream and Atlantic hurricane belt 21. |
| Climate | **6 active climate cards, 9 retired** (commit `41fdf95`): the pressure belts, the East Asian and West African monsoons, the Canary, Benguela, Humboldt and Kuroshio currents, and the Bay of Bengal cyclones. |
| Verify markers | Move out of the blurbs into a **structured verify field**. Release is gated on them (in progress). |
| Companion PDF guide | Follows the **new-card study order**, sectioned by **pass, then region**. Every card has a 1–3 sentence blurb, stored as `note` in the data. |
| Country design | **Split cards** (separate country outline and capital dot notes), as in the PoC on branch `poc/countries` (`f4a3503`). |
| Dependencies | The 23 **include** territories in [List 1](#appendix-b-list-1-dependent-and-autonomous-territories-inhabited) get cards. The 29 **exclude** territories stay on the [revisit list](#intentionally-excluded-revisit-list). |
| Disputed territories | The 15 **card** entries in [List 2](#appendix-c-list-2-disputed-and-occupied-territories) get cards. The 16 **no card** entries stay on the [revisit list](#intentionally-excluded-revisit-list). |

**Earlier proposals these decisions overrode:**

- **Global features:** the orientation block replaces the architecture proposal's D10, an interlude at the end of each pass.
- **Microstates:** keeping the country card (for a microstate, where it is *is* the knowledge) and dropping a same-name capital card replaces D11, a capital card only below a size threshold.
- **State list:** the 197-card list replaces D8's default of UN members and observers plus the partially recognised states in the ring.
- **Name:** "World Atlas" replaces D6's deck name `Geography`, so every filtered-deck search below uses `deck:"World Atlas"`.
- **Borders:** internationally recognised borders replace D8's default of NE's de facto admin_0 worldview. **The PoC's de facto border view is superseded.**

**Knock-on effects of the climate retirement:** orientation keeps two planetary bands (trade winds, westerlies) rather than four, and the region assignments for the retired climate cards no longer apply. The feature count is 132 active cards (49 tier 1, 73 tier 2, 10 tier 3), not 141.

## Curriculum

### Learning principles

| Principle | Source | What it decides here |
|---|---|---|
| Spatial knowledge grows from landmarks to routes to a survey of the whole | Siegel & White (1975) | Orientation gives the landmarks. The neighbour walk gives the routes. Anki's mixed reviews and the second pass build the survey. |
| Advance organisers: a general frame before the details | Ausubel (1960) | Orientation first. A region's frame feature (peninsula, named region) opens it. The existing broad-before-narrow rule stays. |
| Schemas and chunking | Miller (1956); Chase & Simon (1973) | Clusters of about 10 cards: 3–5 neighbouring countries with their capitals and features. Relations (shared borders, a range on a border) make the chunks. |
| Temporal contiguity: related items close in time | Mayer, multimedia principles | Features follow the countries they cross or divide. Capitals stay near their countries. |
| Spacing and lag | Cepeda et al. (2006) | Capitals come a few cards after their countries, not right after. Anki handles the spacing of reviews. |
| Interleaving helps discrimination; its benefit comes from contrast, and it depends on similarity | Kornell & Bjork (2008); Kang & Pashler (2012); Carvalho & Goldstone (2014) | First exposure is blocked by region. Retrieval is interleaved, because Anki mixes reviews from every region. Look-alikes sit near each other for contrast, but never back to back. |
| Novices need more structure than experts | Kalyuga et al. (2003), expertise reversal | The target is a total beginner, so the order is structured and predictable. Self-directed study is opt-in, through filtered decks. |
| Flow: challenge matched to skill | Csikszentmihalyi | Easy, distinctive shapes come first in each cluster. The learner sets the rate. Dense regions are flagged. |

### Why the atlas ring

Three structures were compared; (c) was chosen.

| | (a) Region-complete | (b) Tier spiral | **(c) Atlas ring + depth pass (chosen)** |
|---|---|---|---|
| Shape | One pass. Each region complete at every tier, cities included. | Orientation, then tier 1 world-wide by region, then later passes for tiers 2 and 3 | Orientation, then one pass with every country and capital plus tier 1–2 features, then a short depth pass with tier 3 (and secondary cities, if any are carded) |
| Neighbour chunks | Strong | **Broken:** countries have no tiers, so a tier-1 pass either includes every country or leaves holes in the jigsaw | Strong. Each region's political map is complete in one go. |
| Learner who stops early | Lopsided: knows Europe in depth and has never seen Asia | Best | Good. The world map is complete at the end of pass 1, and only the most expendable cards are deferred. |
| Contiguity of features and borders | Strong | Weak: the Pyrenees (tier 2) arrive weeks after France and Spain | Strong. The tier-2 features include most of the border-defining ones (Pyrenees, Carpathians, Urals, Zagros, Rio Grande, Amur), so they stay in pass 1. |
| Cost | Simplest | Needs country tiers | One extra pass tag |

(c) keeps complete neighbour chunks and holds back only the long tail. With every secondary city deferred, pass 2 is just the 10 tier-3 features, under 2% of the cards; its job is mainly to protect the early stopper. Going round the ring a second time also brings back each region's layout at a long interval.

### The ring (default start: Western Europe)

Regions are listed in study order, with countries in walk order. Counts follow the PoC's 200-row state list: the 197 country cards plus Northern Cyprus, Somaliland and Western Sahara, which now get dispute cards only and stay in the walk as pockets. Items in *italics* are pockets (see [Walking the countries](#walking-the-countries)).

| # | Region | Countries, in walk order | n | Way in |
|---|---|---|---|---|
| 1 | Western Europe | Portugal, Spain, *Andorra*, France, *Monaco*, Belgium, Luxembourg, Netherlands, UK, Ireland | 10 | Atlantic (from 21) |
| 2 | Nordic & Baltic | Iceland, Norway, Sweden, Denmark, Finland, Estonia, Latvia, Lithuania | 8 | North Sea |
| 3 | Central Europe & Italy | Poland, Germany, Czechia, Austria, Switzerland, *Liechtenstein*, Italy, *San Marino*, *Vatican*, *Malta*, Slovenia, Hungary, Slovakia | 13 | Lithuania → Poland |
| 4 | Balkans | Croatia, Bosnia and Herzegovina, Serbia, *Kosovo*, Montenegro, Albania, North Macedonia, Greece, Bulgaria, Romania | 10 | Hungary → Croatia |
| 5 | Eastern Europe | Moldova, Ukraine, Belarus, Russia | 4 | Romania → Moldova |
| 6 | Caucasus & Anatolia | Georgia, Azerbaijan, Armenia, Turkey, Cyprus, *Northern Cyprus* | 6 | Russia → Georgia |
| 7 | Levant & Mesopotamia | Syria, Lebanon, Israel, *Palestine*, Jordan, Iraq | 6 | Turkey → Syria |
| 8 | Arabian Peninsula | Kuwait, Saudi Arabia, Bahrain, Qatar, UAE, Oman, Yemen | 7 | Iraq → Kuwait |
| 9 | Horn & East Africa | Djibouti, Eritrea, Ethiopia, Somalia, *Somaliland*, Kenya, Tanzania, Burundi, Rwanda, Uganda, South Sudan, Sudan | 12 | Bab el-Mandeb |
| 10 | North Africa | Egypt, Libya, Tunisia, Algeria, Morocco, *Western Sahara* | 6 | Sudan → Egypt: the walk follows the Nile downstream |
| 11 | West Africa | Mauritania, Senegal, Gambia, Cabo Verde, Guinea-Bissau, Guinea, Sierra Leone, Liberia, Côte d'Ivoire, Mali, Burkina Faso, Ghana, Togo, Benin, Nigeria, Niger | 16 | Western Sahara → Mauritania |
| 12 | Central Africa | Chad, Cameroon, Central African Rep., Equatorial Guinea, São Tomé and Príncipe, Gabon, Congo, DR Congo | 8 | Niger → Chad |
| 13 | Southern Africa & Indian Ocean | Angola, Zambia, Malawi, Mozambique, Zimbabwe, Botswana, Namibia, South Africa, *Lesotho*, *Eswatini*, Madagascar, Comoros, Mauritius, Seychelles | 14 | DR Congo → Angola |
| 14 | South Asia | Maldives, Sri Lanka, India, Bangladesh, Bhutan, Nepal, Pakistan | 7 | Indian Ocean (the monsoon trade route) |
| 15 | Iran & Central Asia | Afghanistan, Iran, Turkmenistan, Uzbekistan, Tajikistan, Kyrgyzstan, Kazakhstan | 7 | Pakistan → Afghanistan |
| 16 | East Asia | China, Mongolia, North Korea, South Korea, Japan, *Taiwan* | 6 | Kazakhstan → China |
| 17 | Southeast Asia | Philippines, Malaysia, Brunei, Singapore, Thailand, Myanmar, Laos, Vietnam, Cambodia, Indonesia, Timor-Leste | 11 | Taiwan → Philippines |
| 18 | Oceania | Australia, Papua New Guinea, Solomon Islands, Vanuatu, New Zealand, Fiji, Tonga, Samoa, Tuvalu, Kiribati, Nauru, Marshall Islands, Micronesia, Palau | 14 | Timor-Leste → Australia |
| 19 | North & Central America | USA, Canada, Mexico, Guatemala, Belize, El Salvador, Honduras, Nicaragua, Costa Rica, Panama | 10 | Pacific crossing (the one long seam) |
| 20 | South America | Colombia, Ecuador, Peru, Chile, Bolivia, Argentina, Uruguay, Paraguay, Brazil, Suriname, Guyana, Venezuela | 12 | Panama → Colombia |
| 21 | Caribbean | Trinidad and Tobago, Grenada, St Vincent, Barbados, St Lucia, Dominica, Antigua and Barbuda, St Kitts and Nevis, Dominican Rep., Haiti, Jamaica, Cuba, Bahamas | 13 | Venezuela → Trinidad. Exit: Bahamas → Atlantic → Iberia, closing the ring (the 1492 route in reverse). |

That is 21 regions, one over the range originally asked for. Merging any two would break a seam or bury the Levant. Apart from those three dispute pockets, the table lists sovereign and partially recognised states only. Abkhazia, South Ossetia and Transnistria now get dispute cards ([Territories](#territories)), so they become pockets of Georgia and Moldova. The Cook Islands and Niue are on the revisit list; if added, they become pockets of New Zealand. Territory and dispute cards are placed as geographic pockets in `data/curriculum.yaml` (decision 5, now decided; see [Decisions so far](#decisions-so-far)).

**Why a ring.** Every crossing is a land border or a short sea, except the Pacific crossing into region 19. Because the loop is closed, a learner can start at **any region** and keep continuity everywhere except at the one cut. "Home region first" is therefore just a rotation, not a second design.

**Why Western Europe by default.** No start is culturally neutral, so the default is chosen on learning grounds:

1. **It starts in the middle of the familiar map.** The standard world map, and this deck's frames, are centred near 0°.
2. **The shapes are moderately sized and widely recognised,** so the first week builds the habit before the dense regions arrive.
3. **The first ten regions follow the Mediterranean–Middle East–Red Sea arc.** That arc holds 6 of the 11 tier-1 chokepoints and the river valleys of the earliest states. This is the deck's own "most explanatory first" rule from ADR 0004, applied to geography instead of tier.

North America is the strongest alternative start: three huge countries make the easiest first week. It's offered as a filtered-deck rotation (see [Practicalities](#practicalities)).

### Assigning physical features to regions

Apply these rules in order. The first rule that matches decides.

1. **Global features go to orientation:** the four oceans (Atlantic, Pacific, Indian, Arctic) and the two remaining planetary bands (trade winds; westerlies and Roaring Forties). They are pure frame, learnable before any country, and every regional climate card later hangs off them.
2. **Straits, canals and capes go to the later of the two shores' regions,** so both shores are known: Gibraltar → 10, Hormuz → 15, Bering → 19, Bab el-Mandeb → 9, Tiran → 10, Luzon → 17, GIUK → 2. Routes go to the region of their owner: Northern Sea Route → 5, Grand Canal → 16.
3. **Regional climate goes to the land it shapes:** the South Asian monsoon → 14; typhoon alley → 17. The Atlantic hurricane belt and the Gulf Stream go to 21, so the ring's last cards carry the learner across the Atlantic back to Europe.
4. **Everything else goes to the region with the largest share of its extent** (area, length or shoreline), derived from geometry. Examples: Danube → Balkans, Rhine → Central Europe, Himalayas → South Asia, Sahara → North Africa, Andes → South America, Great Rift Valley → Horn & East Africa.
5. **Parent before child overrides all of these** (ADR 0004 rule 2). A parent moves forward to just before its earliest child. For example, the Mediterranean must precede the Aegean in region 4.

An override in `features.yaml` (`region` plus `region_reason`) handles the rest; the ten in use are listed under [Decisions so far](#decisions-so-far). The Persian Gulf needed none: its shoreline already derives to 8 (56%, against 41% for 15). `uv run python -m geofeat.regions` prints every feature's assignment.

### Walking the countries

- **Frontier rule (connected growth).** Each new country borders a country already introduced in the region, by land or by ≤ 200 km of sea. The walk can step back to an earlier country without a jump, which removes dead ends: for example USA → Canada → Mexico.
- **Isolated islands** (Iceland, Cabo Verde, Madagascar, the Indian Ocean and Pacific states, part of the Antilles) attach to the nearest introduced country. Each one is reported as a jump, not hidden.
- **The walk itself.** Start at the region's entry country, the one adjacent to the previous region's exit. Among the countries that border one already introduced, prefer one that borders the most recent; then the one with the fewest unvisited neighbours (Warnsdorff's rule); then the larger one. End near the next region's entry.
- **Pockets.** Microstates, enclaves and disputed entities aren't nodes in the walk. Each one goes into its host's run, after the host's capital: Monaco after Paris, Lesotho after Pretoria, Kosovo after Belgrade, Somaliland after Mogadishu.
- **Freezing the walk.** Generate the walk once, review it by eye, and commit it as an explicit list in `curriculum.yaml`. The build then only **checks** the frontier rule and reports every jump. A walk that is generated and then frozen can be reviewed, and adding a country doesn't reshuffle it.

### Placing each card type

| Card | Placement | Why |
|---|---|---|
| Region frame feature (Iberian/Italian/Balkan/Arabian/Korean/Malay Peninsula, Anatolia, Levant) | **Opens** its region or cluster | Advance organiser. Shapes this large are easy to recall cold. |
| Country | Walk order | Route knowledge |
| **Capital** | **2–3 cards after its country**, after the next country, never in a later cluster | Some lag (spacing) while staying contiguous. Country and capital are separate notes, so Anki won't bury one as the other's sibling. The order does the spacing. |
| Physical feature | **Right after the country that completes its frame**, the last of its in-region countries to be introduced: Pyrenees after France, Danube after Romania, English Channel after the UK, Nile after Egypt | Contiguity: the border or valley is already on the map. |
| Core city (pass 1) | At least 2 cards after its country's capital. If it is tied to a feature, right after that feature: Alexandria after the Nile Delta, Istanbul after the Bosporus, New Orleans after the Mississippi, Shanghai after the Yangtze. | It's a dot in a known outline, so it shouldn't be read as "the other dot". |
| Tier-3 feature (and a secondary city, if one is carded later) | Pass 2, same ring, same within-region rules | Long tail |
| Pockets | After the host's capital | See the walk rules above |

A worked example, the start of region 1:

> Iberian Peninsula · Portugal · Spain · *Lisbon* · Andorra · *Madrid* · France · *Andorra la Vella* · Pyrenees · *Paris* · Monaco · Barcelona · Belgium · …

Capitals are in italics. Monaco has no capital card (the same-name rule under Capitals).

### Look-alikes: from a minimum gap to a window

ADR 0004 spreads nearby features at least 3 cards apart, while contiguity packs nearby items together on purpose. The tension resolves once the two jobs of the old rule are separated:

- **Mixing card kinds** (the old category alternation) now happens by itself: a cluster alternates countries, capitals, rivers, ranges and straits. Dropping deck-wide category alternation is the default awaiting confirmation (decision 8 under [Open decisions](#open-decisions)).
- **Separating look-alikes** still matters. Two look-alikes back to back get learned as "the other one", which is ADR 0004's own reason. But the benefit of interleaving comes from *contrast*, and contrast needs them close. **Decided: a window, 3 ≤ gap ≤ 10,** which keeps the pair in the same cluster and usually on the same day.
- **Who counts as look-alikes.** Features: the pair check's sibling pairs, as now (Bosporus/Dardanelles, Lombok/Sunda). Countries: a curated list of name or shape confusables: Niger/Nigeria, Guinea/Guinea-Bissau/Equatorial Guinea, Congo/DR Congo, Sudan/South Sudan, Slovakia/Slovenia, Rwanda/Burundi, Dominica/Dominican Rep., Somalia/Somaliland. A country and a feature with the same footprint, such as Italy and the Italian Peninsula, also count (the country × land-feature check below).
- **Precedence.** Frontier continuity, then parent before child, then the window. If a look-alike pair spans two regions (Guinea in 11, Equatorial Guinea in 12), the window is waived; region distance already separates them.

### Pacing

About 607 cards:

| Block | Cards |
|---|---|
| Orientation | 13: 4 oceans, 2 planetary wind bands, 7 continents (in progress) |
| Pass 1 | 584: 197 countries, 191 capitals, 23 territories, 15 disputed areas, 116 tier 1–2 features, 42 core cities |
| Pass 2 | 10 tier-3 features |

Territories and disputed areas get no capital cards. The 132 active features split 6 orientation, 116 pass 1 and 10 pass 2.

| New cards a day | New cards finish | Notes |
|---|---|---|
| 10 | ~8½ weeks | About one cluster a day. Gentlest in the dense regions. |
| **15 (suggested)** | **~6 weeks** | A cluster and a half a day. A typical region takes 2–3 days. |
| 20 (Anki default) | ~4½ weeks | Fine for regions 1–10. Watch the load at West Africa and the Caribbean. |
| 30 | ~3 weeks | Dense regions put about 30 look-alike outlines into learning at once. Only for someone with prior map knowledge. |

Pass 2 is 10 cards, so pass 1 ends within a day of the last new card at every rate. Review load grows with the rate and keeps running after the last new card, so the program doesn't end when the new cards do. The README should say: *raise the rate while your daily reviews fit your time; lower it before West Africa (11) and the Caribbean (21).*

**Chunks don't need to align with daily batches.** Rates vary and skipped days shift every boundary, so alignment can't be held. Clusters are at most about 10 cards, so any rate of 10 or more covers whole clusters most days. Every crossing between regions is continuous, so a day that ends mid-region still ends on known ground. A capital that rolls into the next day is just a little more spacing.

### Practicalities

**Tags,** added to the existing `tier::`, `category::` and `id_` tags:

- `kind::<k>` (feature, country, capital, city, territory, dispute, continent);
- `region::NN`, the region number zero-padded, so the tag sidebar lists regions in ring order. Country, capital, territory, dispute and city cards carry it; feature cards don't yet;
- `pass::orientation`, `pass::1` or `pass::2`.

[architecture.md](architecture.md#tags) lists every tag as built.

**What the learner does:**

| Goal | How |
|---|---|
| Follow the program | Study the deck. In deck options, keep the new-card **sort order on "order gathered"** (the default) and never use random. A random order deletes the curriculum. |
| Learn one region now | Make a filtered deck: `deck:"World Atlas" tag:region::14 is:new`, order **"Order due"** (for new cards, due is the position; *verify on AnkiDroid and AnkiMobile*). Cards studied there go back to the main deck as reviews. Unstudied cards go back to their old positions. |
| Home region first | The same filtered deck, for your home region, on day 1. Then continue the main deck. That costs one break in continuity and needs no special build. It also stays compatible with `positions.lock`, which a rotated build would not be. |
| Revise a region | `deck:"World Atlas" tag:region::04 -is:new`, ordered by due or at random. |
| See the map | The PDF guide, in new-card study order, sectioned by pass and then by region in ring order. It's an atlas to keep beside the deck. |

**Finishing a region** is the natural progress milestone. A count such as "region 7 of 21" in the README's study notes costs nothing.

**Existing users.** Re-import keeps each card's new-card position. Builds since the flat deck numbered the feature cards from 0 (141 cards, now 132); the earlier subdeck builds gave every card position 0. Either way, an existing user's unstudied features come before every country. No repositioning tool is planned. These users aren't total beginners, and they finish the features they started before going round the ring. The README should say:

- **Studied little or nothing:** delete the deck and import fresh to get the full program order.
- **Mid-way:** keep going. The ring starts once your earlier features are done, or run region filtered decks in parallel.

## Architecture plan

### Data model

| Question | Plan | Why |
|---|---|---|
| Same file or separate | **Separate**: `countries.yaml` (one entry per state, with nested capital), `territories.yaml` (territory and dispute entries, told apart by `kind`) and `cities.yaml` (city plus `country:` ref). This keeps the PoC's shape. | `Feature` carries physical-only policy: `FeatureType`/`FAMILY`, land clipping, `expect` size ranges, `allow_nested`, the pair check. Stretching it to countries would drag them into rules that don't apply to them. |
| Shared model | **No shared entity, but a shared DTO.** A `Card` ([ADR 0005](adr/0005-card-sources-and-card-dto.md)) with `uid`, `kind`, `id`, `prompt`, `answer_lines`, `tags`, `region`, `tier`, `anchor`, `parents`, `note`, `host`, `orientation` and `render` (a `RenderSpec` plus lazy geometry). Each source exposes `cards() -> list[Card]`. | The order engine and deckgen depend on `Card`, not on three models. Adding a fourth kind (rivers-by-country, flags) is an extension, not an edit. |
| Renderer input | **Extract `RenderSpec`** (style, geometry parts, frame options, context overlays) from `Feature`. The PoC already reaches into `Feature` with its `outline`/`context` styles. | The old render cache hashed the *source* of `model.py`, so adding a `region` field would have re-rendered every map (~2 h at 700). Done in P1 (WS2): the key hashes the resolved geometry, the dumped `RenderSpec` and the render-code files, not the schema module. |
| One note or two | **Two notes**, `uids: {country, capital}`, as the PoC has (decided: split cards). | ankc "reversed" swaps one front/back pair. Country (outline → name) and capital (dot → capital) differ on both sides, so reversed can't express them. Cloze can't hide one image per card. Two notes also give independent tags, tiers, positions and retirement (for example, dropping the capital card for city-states). The cost is that Anki won't bury them as siblings, so the order engine has to space them. |
| Id namespace | **Kind-prefixed id tags for new kinds**: `id_country_niger`, `id_capital_niger`, `id_city_istanbul`. Existing feature tags stay `id_<id>`. | Real collisions exist: the rivers Niger, Congo and Jordan, and retired island ids such as cyprus and taiwan. A check enforces global uniqueness across sources. |
| New tags | `kind::<k>`, `region::NN`, `pass::<p>`. Keep `tier::` and `category::`; countries get `category::countries`, capitals and cities `category::cities`, territories and disputes `category::territories`. | Filtered decks keep working. |
| Region membership | **Countries, territories and disputed areas: placed by `data/curriculum.yaml`**, the one source of region and pocket host; their own yaml entries carry neither. Cities inherit their country's region. **Features: derived** by `regions.py` from the region with the largest share (a region's outline is the union of its members' full outlines, before any `mainland` crop). A `region` override with a `region_reason` in `features.yaml` covers the exceptions, and the orientation features go to the orientation block. | Region membership is curricular, not geometric (Egypt, Turkey, Russia, Kazakhstan). For 132 features, derivation is cheap and the override handles the exceptions. |
| Adjacency | **Computed at build time** (`make adjacency`) from the recognised-border outlines composed from the `geometry` in `countries.yaml`, uncropped. Touching is `intersects` after a 1 km buffer, to absorb 10m slivers. Sea edges link countries within 200 km, so island states aren't isolated (UK–France, Japan–Korea, Sri Lanka–India). Hand edits go in `data/adjacency.yaml` (`add`/`remove`, each with a `reason`). Results are cached in `build/adjacency.json`, keyed by an inputs hash, as `siblings.json` is. | Deterministic and reviewable. ~200 outlines with an STRtree index takes seconds. |

### Ordering engine

`order.py` becomes a package of pure functions over `Card`s. Policy lives in `data/curriculum.yaml`, which holds the pass definitions, the region sequence, a start country per region, the frozen walks, and where the orientation cards go. The engine is the mechanism.

```
cards ─▶ passes (from curriculum.yaml)
      ─▶ per pass: orientation, then regions in ring order
      ─▶ per region: the frozen neighbour walk over countries  → backbone
      ─▶ anchor: capital → its country; city → its capital or feature; feature → country that completes its frame (or `anchor:` override)
      ─▶ splice anchored cards after their anchor, then local repair:
         parent before child, look-alikes 3–10 apart, country → capital gap 2–3
      ─▶ ideal order
```

- **Generating the walk** (before it is frozen): a deterministic search from the region's entry country, following the frontier rule above. Among candidates, prefer one bordering the most recent country, then the fewest unvisited neighbours (Warnsdorff's rule), then size, then id. When the walk is stuck it jumps to the nearest unvisited country by centroid distance, and the jump is counted. A disconnected region subgraph is bridged by its shortest component-to-component edge. `make deck` prints the jumps for each region, and a test caps them per region.
- **Determinism:** no set iteration order and no floats in tie-breaks. Every comparator ends in an id. Golden-file tests use a small fixture world (about 12 countries, 2 regions, 4 features).
- **Stability: the main change.** The ideal order is used **only to place new uids**. Positions are kept in `data/positions.lock` (uid → int). It is committed, append-only, and a retired uid keeps its slot.
  - A new uid gets the midpoint between the locked positions of its neighbours in the ideal order.
  - The initial assignment uses a stride of 500: about 600 cards end near 300,000, leaving room for about 1,400 more at the end and about 8 midpoint inserts at any one spot.
  - Stay below 1,000,000. Anki 26.09.3 desktop's Check Database rewrites new-card dues of 2,000,000 or more (P1 spike, [ADR 0006](adr/0006-positions-lock-and-pos-footnote.md)); 1,000,000 leaves a margin.
  - Exhausting a gap fails the build. A deliberate `reflow` can renumber, but only cards no user has imported yet; in practice, only before release.
  - The lock is the log, and the order a user sees is that log. Today's behaviour (positions shift on every addition, plus README instructions to Reposition by hand) puts the burden on the user; the lock removes the drift at its source.
- **Mechanism (built in P1):** ankc 0.5 numbers cards 0..N by source order and can't set `due` directly. ankc 0.6, released on PyPI, reads a per-card `[^pos]: <int>` footnote beside `[^uid]`/`[^type]`. `check package` asserts `due == positions.lock[uid]` with 0.6 or a frozen lock. The rejected fallback was rewriting `cards.due` in the `.apkg` after the build.

### Migration and identity

- **Uids:** unchanged. Feature notes keep their GUIDs and are updated in place. **Don't change the ankc note type (model id or fields) for basic cards.** A notetype mismatch on import is the one way existing notes get duplicated instead of updated.
- **Deck rename** to World Atlas: ankc derives the deck id from the name, and Anki doesn't move existing cards between decks on re-import. Renaming puts the 132 existing cards in the old deck and every new card in the new one. Users fix that by hand with **Change Deck**, as in the flat-deck migration. The first World Atlas release is the cheapest point to rename, because every card added after it would also need moving.
- **Positions for existing users:** see [Practicalities](#practicalities). Don't build anything to reposition old cards.
- **Retirement:** unchanged (`retired: true`, keep the entry and its lock slot).

### Build cost and scale

| Item | Today | At ~700 cards | Action |
|---|---|---|---|
| Cold render | 132 × 10 s | ~7,000 s ≈ 2 h at JOBS=1. JOBS=2 needs ~3 GB, which is the whole machine. | **Share frames.** A country, its capital and its cities use one frame, so render the basemap once per frame and composite the overlays. That leaves ~350 distinct frames, about 1 h cold. Measure first to confirm the basemap dominates. Loading the NE layers before forking would let workers share pages copy-on-write. |
| Render cache | Keyed by the resolved geometry, the dumped `RenderSpec`, the source of render/frame/ne/style/spec, `uv.lock` and the basemap layers' pinned sha256s ([architecture](architecture.md)). Edits to `model.py`, `resolve.py` or selectors don't re-render unless the geometry changes. Lives in gitignored `build/`. | Any edit to the renderer modules (including a country style in `style.py`) invalidates everything. | Split the code hash so changing a country style doesn't re-render features. Optional: restore the cache in CI with `actions/cache`. |
| Pair check | ~40 s; bbox prefilter, then a full comparison on near pairs | Don't add countries or cities to it. Country outlines don't overlap and capitals are distinct points. | Keep the pair check to features. Add two cheap checks: **country × land-family features** with an STRtree, report-only, because "Country: Italy" against "Peninsula: Italian" differ only in the prompt word; and **dot spacing**, which fails when two city/capital rings in the same frame overlap. |
| `.apkg` | about 150 KB a card | ~100 MB | Acceptable for import. Verify AnkiWeb's sync and shared-deck limits if the deck will be distributed. Levers: 1200 px renders, or WebP (check AnkiMobile and AnkiDroid support first). |
| Guide PDF | 12 MB | ~60 MB | Downsample the embedded images (62% of the page width doesn't need 1600 px) and section it by pass and region. Optionally `make guide REGION=…`. |

### Repo and naming

- **One repo.** One order needs every card in one process, and the renderer, NE vendoring, framing and checks are shared. Splitting would turn an in-process function call into a cross-repo contract. Draw the boundaries inside the repo instead: `sources/` (features, countries, cities) → `Card` → `order/` → `deckgen`/`guide`/`check`.
- **Rename the deck** to World Atlas once (see Migration). Rename `deck/geographic-features.md`, `dist/*.apkg` and the Makefile `DECK` with it. **Keep the package name `geofeat`**: it's internal, and renaming it is churn no user sees. Renaming the repo to `world-atlas` is the default awaiting confirmation (decision 11).

### Risks

1. **No stable positions without an ankc change.** *Resolved in P1:* `positions.lock` and ankc 0.6's `[^pos]`. The lock stays a draft until P7, so freeze it before the countries ship, not after.
2. **Political edge cases in the data:** disputed states (Kosovo, Taiwan, Western Sahara, Palestine, Somaliland), dependencies, and whether the target is ~200 or ~215 states. *Decided* ([ADR 0008](adr/0008-state-list-borders-adjacency.md)) and in the P2 data; the time-sensitive items are under [Territories](#territories).
3. **Microstates at the 2,600 km minimum frame** ([ADR 0003](adr/0003-projection-and-framing.md)): an outline card for Vatican City, Monaco or Nauru is just a ring, so "outline → name" teaches the frame, not the shape. 38 of the PoC's 200 states get a ring. The decision keeps their country cards; a smaller minimum frame for small outline cards is still an option.
4. **Wide or split countries:** Russia, Fiji and Kiribati cross the antimeridian, and France and the USA have overseas parts. The `mainland` box handles this; a box with `lon_min > lon_max` crosses 180°, and every outline has an `expect` bbox.
5. **Walk quality on archipelago regions** (Caribbean, Oceania, Southeast Asia): jumps are unavoidable there. Report them rather than hiding them.
6. **The render invalidation footgun** in `_code_hash`. *Resolved in P1 (WS2):* the cache key hashes resolved geometry and the `RenderSpec`, not `model.py`.
7. **Anki behaviour assumptions:** new-card `due` preserved on import, and Check Database leaving dues under 2,000,000 alone. Both were measured on Anki 26.09.3 desktop only. Test on AnkiDroid and AnkiMobile (P6) before relying on the lock.

## Territories

Country cards use internationally recognised borders and show the mainland only. Overseas territories and disputed areas get their own cards with their own outlines. The full tables are in [Appendix B](#appendix-b-list-1-dependent-and-autonomous-territories-inhabited) and [Appendix C](#appendix-c-list-2-disputed-and-occupied-territories); sources and method are in [Appendix A](#appendix-a-territories-sources-and-method).

**Summary** (checked 2026-10-14)

1. **Counts:** List 1 has 52 inhabited dependent or autonomous territories: **23 include**, 29 exclude. 13 of the 52 are integral parts of their state. A further 9 uninhabited entries (US Minor Outlying Islands counted as one) are listed in one line. List 2 has 31 disputed or occupied areas: **15 card**, 16 no card.
2. **Include (23):** Greenland, Faroe Islands, Svalbard, Hong Kong, Macau, Puerto Rico, Guam, Gibraltar, Falkland Islands, Bermuda, Cayman Islands, British Indian Ocean Territory, Isle of Man, Jersey, Guernsey, New Caledonia, French Polynesia, French Guiana, Réunion, Guadeloupe, Martinique, Aruba, Curaçao.
3. **Card (15):** Crimea, Kashmir (Indian-administered), Kashmir (Pakistani-administered), Aksai Chin (Chinese-administered, with Shaksgam), Arunachal Pradesh, Western Sahara, Golan Heights, Abkhazia, South Ossetia, Transnistria, Northern Cyprus, Somaliland, Kuril Islands (southern four), Spratly Islands, Essequibo.
4. **NE polygon gaps:** The French overseas departments, Caribbean Netherlands, Svalbard, Åland, Tokelau, Christmas Island and Cocos have no row of their own in `admin_0_countries`; they need `ne_10m_admin_0_map_units` (vendored in P1, WS4). The Canary Islands have no polygon in either layer. Every List 2 card except Northern Cyprus, Somaliland and Spratly needs `ne_10m_admin_0_disputed_areas` (vendored in P1, WS4). NE has no polygon at all for the post-2022 occupation of Ukraine. Its Donetsk and Luhansk shapes are the 2014–22 lines, its Artsakh shape is stale since 2023, and its Hans Island note has been stale since 2022.
5. **Verify (time-sensitive):** the Chagos handover (the treaty was not ratified and shelved as of May 2026), New Caledonia's Bougival status, US–Greenland talks, Somaliland recognition (only Israel so far), the Ukraine front and any deal, the ICJ Essequibo judgment (expected Nov 2026 to Jan 2027), Western Sahara after UNSC resolution 2797 (Oct 2025), and Israel's post-2024 zone beyond the Golan.

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

### States handled as countries, not here

Taiwan, Kosovo and Palestine (including Gaza, the West Bank and East Jerusalem) get country cards. Western Sahara, Northern Cyprus and Somaliland get dispute cards only ([ADR 0008](adr/0008-state-list-borders-adjacency.md)).

### Data gaps for the 15 dispute cards

- **Disputed-areas layer:** 12 cards need `ne_10m_admin_0_disputed_areas.geojson` (701 KB at commit `f1890d9f`), vendored in P1 (WS4). Northern Cyprus, Somaliland and Spratly need it too only if you use the disputed-areas shapes rather than their admin_0 rows.
- **Somaliland:** NE's polygon includes the Las Anod / SSC-Khatumo area that Somaliland lost in 2023. Flag this on the back or trim the shape.
- **Western Sahara:** the admin_0 row alone is the east-of-berm strip. Union both DA parts.
- **Recognised-border country outlines:** to show Ukraine with Crimea, Georgia with Abkhazia and South Ossetia, and so on, you have to add DA parts back. Otherwise the de facto admin_0 shapes contradict the "recognised borders" rule.

### Intentionally excluded (revisit list)

Excluded by decision on 2026-10-14 and kept on file to revisit: 29 dependencies (List 1 "exclude"), 16 disputed areas (List 2 "no card") and 9 uninhabited territories. Reasons for dependencies and disputed areas are as given in Appendices B and C; the uninhabited entries are not tabled there. Ceuta and Melilla appear twice: as integral Spanish cities in List 1 and as Morocco's claim in List 2.

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

## Open decisions

These defaults are waiting for the user's confirmation. Numbers follow the build plan; decisions 1–3 (borders, state list, capitals), 5 (territory placement) and 7 (continents) are decided and recorded above. Work proceeds on the default until the user overrides it.

| # | Decision | Default | Blocks |
|---|---|---|---|
| 4 | Territory and dispute cards | Front word `Territory` or `Disputed territory`. Back line 2 gives the status, or `Disputed: <parties>` (the parties rule itself is decided). Dashed red outline. The P2 sources already write the front words and back lines; the outline is drawn solid until P4. | P4 rendering |
| 6 | Close dots (Tel Aviv/Jerusalem, Dubai/Abu Dhabi) | A **tighter frame, at least 1,000 km wide,** when another dot is within 150 km. Amends [ADR 0003](adr/0003-projection-and-framing.md)'s 2,600 km minimum. | P4 rendering |
| 8 | Curriculum defaults | **21 regions** (check Turkey with the Caucasus, Sudan in East Africa, Mexico with Central America, Iran with Central Asia). **Pass 1** = tiers 1–2 plus the 42 core cities; pass 2 = tier 3 (the secondary cities are deferred). **Drop deck-wide category alternation.** **15 new cards a day**, stated in the README with a warning before regions 11 and 21. **No repositioning tool** for existing users. | P3 order engine |
| 9 | Scattered states (Kiribati, Micronesia, Tuvalu) | **The whole spread, plus a ring.** | P4 rendering |
| 10 | Somaliland's outline | **NE's outline as is,** with the Las Anod area mentioned in the blurb. | P2 blurbs, P4 rendering |
| 11 | Repo name | **Rename to `world-atlas`;** keep the `geofeat` package. | P5 rename |
| 12 | Distribution | **GitHub release only:** the `.apkg` (about 100 MB) and the guide PDF. | P7 release |

**Where the earlier open items went.** The curriculum items (region list, pass 1 features, city tiers, category alternation, rate, existing users) are all in decision 8; orientation contents is decided (Continents). Architecture defaults D2–D5 and D9 are now the build plan and are proposed in ADRs [0005](adr/0005-card-sources-and-card-dto.md), [0006](adr/0006-positions-lock-and-pos-footnote.md) and [0009](adr/0009-curriculum-order.md). D7 is decision 11, and D8 is decided. Of the territory items, Western Sahara, territory capitals, multiple capitals and Palestine's capital are decided; placement (decision 5) is now decided too; scattered states are decision 9 and Somaliland 10. The NE layers are vendored in P1 (WS4).

## ADRs

| ADR | Topic | Status |
|---|---|---|
| [0005](adr/0005-card-sources-and-card-dto.md) | Card sources and the `Card` DTO | Proposed |
| [0006](adr/0006-positions-lock-and-pos-footnote.md) | `positions.lock` and the ankc `[^pos]` footnote; supersedes the drift consequence in ADR 0004 | Proposed |
| [0007](adr/0007-rename-and-migration.md) | Rename to World Atlas, and migration | Proposed |
| [0008](adr/0008-state-list-borders-adjacency.md) | State list, borders worldview and adjacency | Accepted |
| [0009](adr/0009-curriculum-order.md) | Curriculum order; supersedes ADR 0004's tier-first rule and ≥ 3 gap | Proposed |

Specialist reviews to run: `data-engineer` on the adjacency and region-derivation rules, and `technical-writer` on the README's migration section.

## Build phases

Summary of the 2026-10-14 build plan. Each workstream runs in its own git worktree off `main`, and only one render runs on the machine at a time.

| Phase | Work | Exit or user gate | Status |
|---|---|---|---|
| P0 | Decisions and ADRs 0005–0009 (WS6), alongside P1. | ADRs drafted. | Done |
| P1 | Foundations, in parallel. WS1: ankc 0.6 `[^pos]`. WS2: render core and `RenderSpec`. WS3: `Card` DTO and `positions.lock`. WS4: NE political layers. WS5: cities and continents research. WS6: docs. WS2 merges before WS4; WS3 merges after the ankc 0.6 release. | `make all` passes with ankc 0.6. `media.json` has the same 132 PNG names. `check package` asserts due == `positions.lock`. `make fetch` verifies the new layers. The cities and NE political layers research notes are done. **User gate:** merge the ankc 0.6 release. | Done. ankc 0.6.0 is on PyPI. |
| P2 | Data and content, in parallel: the political model (`src/geofeat/sources/`), `countries.yaml` (197), `territories.yaml` (23 + 15), `cities.yaml`, `curriculum.yaml` and `adjacency.py`, `regions.py` and the continents. About 530 blurbs, written in 4 regional research streams and fact-checked by a second researcher. | Data validates. | Data done except the continents (in progress) and the verify field (in progress). |
| P3 | Order engine (`order/` package): passes, regions, frozen walks, anchoring, repair rules, golden tests. Walk maps for review, political checks, notes merged into the data. | **User gate:** sign off the walk maps. | Next |
| P4 | Rendering treatments: dashed dispute and territory outlines, the recognised-border basemap, close-dot frames, scattered states, a shared basemap if it is over half the render time. Review tooling by region. Cold render of about 560 maps (35–95 min). | **User gate:** sign off the region sheets. | |
| P5 | The guide in study order (pass, then region, then position; under 80 MB), in parallel with the rename to World Atlas ([ADR 0007](adr/0007-rename-and-migration.md)). | Uid freeze test passes. | |
| P6 | QA: phone sheets, pair check (features and continents only), CVD on the new treatments. | **User gate:** device tests (fresh import order, a filtered "Order due" deck, Check Database with high dues, the v1 to World Atlas upgrade). | |
| P7 | Multi-lens review and three-agent review. Freeze `positions.lock`. Clean-clone build, tag v2.0.0, GitHub release. Archive `poc/countries` as a tag. Release is gated on the verify markers. | Released. | |

## Appendix A: territories sources and method

- **Natural Earth v5.1.2**, commit `f1890d9f` (as pinned in `data/sources.lock`). `vendor/ne_10m_admin_0_countries.geojson` was read field by field (`TYPE`, `SOVEREIGNT`, `ADMIN`, `NOTE_ADM0`, `NOTE_BRK`). For checking only, `ne_10m_admin_0_disputed_areas` and `ne_10m_admin_0_map_units` were fetched at the same commit into a scratch directory; they were not vendored then; WS4 has since pinned both. Location tests used point-in-polygon checks. The areas quoted from NE were measured on NE's generalised polygons (LAEA), so treat them as approximate.
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

## Appendix B: List 1: dependent and autonomous territories (inhabited)

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

## Appendix C: List 2: disputed and occupied territories

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
