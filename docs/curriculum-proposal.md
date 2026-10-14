# Curriculum: the order of the geography program

Status: proposal, 2026-10-14. Covers the teaching sequence only. `docs/program-architecture.md` covers the machinery and reads this design as data (`data/curriculum.yaml`).

## Decisions so far (2026-10-14)

Recorded in both `docs/curriculum-proposal.md` and `docs/program-architecture.md`. Where this header and the body disagree, the header wins.

| Topic | Decision |
|---|---|
| Name | **World Atlas** |
| Structure | The atlas ring, starting in Western Europe. Home region first is available through a filtered deck, not a rotated build. |
| Global features | Go in the **orientation block** at the start. |
| Capitals | **2–3 cards after their country.** |
| Look-alikes | The **3–10 card window** plus a curated **confusable-country list**. |
| Microstates | Sit with their neighbours in the order (as pockets). **No separate capital card** when the capital shares the country's name and dot (Monaco, Vatican, Singapore). |
| Country cards | Show the **mainland only**. Overseas territories are their own cards, per `docs/territories-list.md`. |
| Borders | Internationally recognised borders; disputed areas get their own cards and outlines (`docs/territories-list.md`). |
| Climate | **9 climate cards retired** (commit `41fdf95`): the pressure belts, the East Asian and West African monsoons, the Canary, Benguela, Humboldt and Kuroshio currents, and the Bay of Bengal cyclones. |
| Companion PDF guide | Follows the **study order**. Every card gets a 1–3 sentence blurb, stored as `note` in the data. |
| Country design | **Split cards** (separate country outline and capital dot notes), as in the PoC on branch `poc/countries` (`f4a3503`). |

**Where the two docs conflicted:**

- **Global features:** the curriculum's orientation block was chosen over the architecture doc's D10 (an interlude at the end of each pass).
- **Microstates:** the curriculum's decision 6 was chosen (keep the country card, drop a same-name capital card) over the architecture doc's D11 (capital card only below a size threshold).
- **Name:** "World Atlas" replaces the architecture doc's D6 deck name `Geography`, and the `deck:"Geography"` filtered-deck searches in the curriculum doc.
- **Borders:** internationally recognised borders replace the architecture doc's D8 default of NE's de facto admin_0 worldview.

**Knock-on effects of the climate retirement:** the curriculum's orientation keeps only two planetary bands (trade winds, westerlies) rather than four, and its region-assignment examples for retired cards (East Asian and West African monsoons, Humboldt, Benguela, Canary and Kuroshio currents, Bay of Bengal cyclones) no longer apply. The feature count is 132 active cards, not 141.

All other items under "Decisions needed" remain open.

## Recommendation in one paragraph

Build the program as an **atlas ring**. It opens with a 1–2 day **orientation** (oceans, the planetary wind belts and, optionally, continents). Then it makes **one complete pass round 21 regions** in a closed loop, and each region crossing goes over a border or a short stretch of sea. Inside a region, countries come **neighbour to neighbour**: each new country borders one already introduced, preferring the most recent. Each capital comes 2–3 cards after its country. A physical feature comes right after the countries that frame it, and a core city comes after its capital or its river. Pass 1 holds every country and capital and the tier 1–2 features. A short **depth pass** then goes round the same ring again with the tier 3 features and the secondary cities. The current anti-confusion rule becomes a window: look-alikes are **near but not adjacent**, 3 to 10 cards apart. Default rate: **15 new cards a day**, about 7 weeks of new cards.

## Learning principles behind it

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

## 1. Overall structure

| | (a) Region-complete | (b) Tier spiral | **(c) Atlas ring + depth pass (recommended)** |
|---|---|---|---|
| Shape | One pass. Each region complete at every tier, cities included. | Orientation, then tier 1 world-wide by region, then later passes for tiers 2 and 3 | Orientation, then one pass with every country and capital plus tier 1–2 features, then a short depth pass with tier 3 and secondary cities |
| Neighbour chunks (your requirement) | Strong | **Broken:** countries have no tiers, so a tier-1 pass either includes every country or leaves holes in the jigsaw | Strong. Each region's political map is complete in one go. |
| Learner who stops early | Lopsided: knows Europe in depth and has never seen Asia | Best | Good. The world map is complete at the end of pass 1, and only the most expendable cards are deferred. |
| Contiguity of features and borders | Strong | Weak: the Pyrenees (tier 2) arrive weeks after France and Spain | Strong. The tier-2 features include most of the border-defining ones (Pyrenees, Carpathians, Urals, Zagros, Rio Grande, Amur), so they stay in pass 1. |
| Cost | Simplest | Needs country tiers | One extra pass tag |

**(c)** keeps what made your earlier deck work, complete neighbour chunks, and holds back only the long tail (14 tier-3 features and roughly half the cities). Pass 2 is short, about 10% of the cards, and its job is mainly to protect the early stopper. Going round the ring a second time also brings back each region's layout at a long interval.

## 2. Regions

### The ring (default start: Western Europe)

Regions are listed in study order, with countries in walk order. Counts follow the PoC's 200-row state list. Items in *italics* are pockets (§3).

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

That is 21 regions, one over your range. Merging any two of them would break a seam or bury the Levant. Abkhazia, South Ossetia, Transnistria, the Cook Islands and Niue need extra layers (see the PoC doc). If they're added, they become pockets of Georgia, Moldova and New Zealand.

**Why a ring.** Every crossing is a land border or a short sea, except the Pacific crossing into region 19. Because the loop is closed, a learner can start at **any region** and keep continuity everywhere except at the one cut. "Home region first" is therefore just a rotation, not a second design.

**Why Western Europe by default.** No start is culturally neutral, so the default is chosen on learning grounds:

1. **It starts in the middle of the familiar map.** The standard world map, and this deck's frames, are centred near 0°.
2. **The shapes are moderately sized and widely recognised,** so the first week builds the habit before the dense regions arrive.
3. **The first ten regions follow the Mediterranean–Middle East–Red Sea arc.** That arc holds 6 of the 11 tier-1 chokepoints and the river valleys of the earliest states. This is the deck's own "most explanatory first" rule from ADR 0004, applied to geography instead of tier.

North America is the strongest alternative start: three huge countries make the easiest first week. It's offered as a rotation (§5).

### Assigning physical features to regions

Apply these rules in order. The first rule that matches decides.

1. **Global features go to orientation:** the oceans (Atlantic, Pacific, Indian, Arctic) and the planetary bands (trade winds, westerlies and Roaring Forties, ITCZ and doldrums, subtropical highs). They are pure frame, learnable before any country, and every regional climate card later hangs off them. ⚠ This departs from the architecture doc's D10 default, an interlude at the end of each pass.
2. **Straits, canals and capes go to the later of the two shores' regions,** so both shores are known: Gibraltar → 10, Hormuz → 15, Bering → 19, Bab el-Mandeb → 9, Tiran → 10, Luzon → 17, GIUK → 2. Routes go to the region of their owner: Northern Sea Route → 5, Grand Canal → 16.
3. **Regional climate goes to the land it shapes.** Monsoons go to their continent (South Asian → 14, East Asian → 16, West African → 11). Currents go to the coast they run along (Humboldt → 20, Benguela → 13, Canary → 10, Kuroshio → 16). Storm belts go to the coast they hit (typhoons → 17, Bay of Bengal → 14). The Atlantic hurricane belt and the Gulf Stream go to 21, so the ring's last cards carry the learner across the Atlantic back to Europe.
4. **Everything else goes to the region with the largest share of its extent** (area, length or shoreline), as the architecture doc already derives it. Examples: Danube → Balkans, Rhine → Central Europe, Himalayas → South Asia, Sahara → North Africa, Andes → South America, Great Rift Valley → Horn & East Africa.
5. **Parent before child overrides all of these** (ADR 0004 rule 2). A parent moves forward to just before its earliest child. For example, the Mediterranean must precede the Aegean in region 4.

A `region:` override with a `reason` handles the rest. The Persian Gulf is the likely first case, pinned to 8 rather than 15.

## 3. Within a region

### Walking the countries

- **Frontier rule (connected growth).** Each new country borders a country already introduced in the region, by land or by ≤ 200 km of sea. The walk can step back to an earlier country without a jump, which removes dead ends: for example USA → Canada → Mexico.
- **Isolated islands** (Iceland, Cabo Verde, Madagascar, the Indian Ocean and Pacific states, part of the Antilles) attach to the nearest introduced country. Each one is reported as a jump, not hidden.
- **The walk itself.** Start at the region's entry country, the one adjacent to the previous region's exit. Among the countries that border one already introduced, prefer one that borders the most recent; then the one with the fewest unvisited neighbours (Warnsdorff's rule, as in the architecture doc), then the larger one. End near the next region's entry.
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
| Secondary city, tier-3 feature | Pass 2, same ring, same within-region rules | Long tail |
| Pockets | After the host's capital | See the walk rules above |

A worked example, the start of region 1:

> Iberian Peninsula · Portugal · Spain · *Lisbon* · Andorra · *Madrid* · France · *Andorra la Vella* · Pyrenees · *Paris* · Monaco · Barcelona · Belgium · …

Capitals are in italics. Monaco has no capital card (decision 6).

### The anti-confusion rule: from a minimum gap to a window

There's a tension. ADR 0004 spreads nearby same-family features at least 3 cards apart, and contiguity now packs nearby items together on purpose. It resolves once you separate the two things the old rule was doing:

- **Mixing card kinds** (the old category alternation) now happens by itself. A cluster alternates countries, capitals, rivers, ranges and straits. **Drop deck-wide category alternation.**
- **Separating look-alikes** still matters. Two look-alikes back to back get learned as "the other one", which is the ADR's own reason. But the benefit of interleaving comes from *contrast*, and contrast needs them close together. **Replace "≥ 3 apart" with a window: 3 ≤ gap ≤ 10**, which keeps the pair in the same cluster and usually on the same day.
- **Who counts as look-alikes.** Features: the pair check's sibling pairs, as now (Bosporus/Dardanelles, Lombok/Sunda). Countries: a short curated list of name or shape confusables: Niger/Nigeria, Guinea/Guinea-Bissau/Equatorial Guinea, Congo/DR Congo, Sudan/South Sudan, Slovakia/Slovenia, Rwanda/Burundi, Dominica/Dominican Rep., Somalia/Somaliland. A country and a feature with the same footprint, such as Italy and the Italian Peninsula, also count (the architecture doc's country × land-feature check).
- **Precedence.** Frontier continuity, then parent before child, then the window. If a look-alike pair spans two regions (Guinea in 11, Equatorial Guinea in 12), the window is waived. Region distance already separates them.

## 4. Pacing

About 700 cards: roughly 15 orientation, 400 countries and capitals, 127 tier 1–2 features, 55 core cities, then about 70 in pass 2.

| New cards a day | New cards finish | Pass 1 complete | Notes |
|---|---|---|---|
| 10 | ~10 weeks | ~9 weeks | About one cluster a day. Gentlest in the dense regions. |
| **15 (suggested)** | **~7 weeks** | ~6½ weeks | A cluster and a half a day. A typical region takes 2–3 days. |
| 20 (Anki default) | ~5 weeks | ~4½ weeks | Fine for regions 1–10. Watch the load at West Africa and the Caribbean. |
| 30 | ~3½ weeks | ~3 weeks | Dense regions put about 30 look-alike outlines into learning at once. Only for someone with prior map knowledge. |

Review load grows with the rate and keeps running after the last new card, so the program doesn't end when the new cards do. The README should put it this way: *raise the rate while your daily reviews fit your time; lower it before West Africa (11) and the Caribbean (21).*

**Should chunks align with daily batches? No.** Rates vary and skipped days shift every boundary, so alignment can't be held. The design doesn't need it either:

- Clusters are at most about 10 cards, so any rate of 10 or more covers whole clusters most days.
- Every crossing between regions is continuous, so a day that ends mid-region or mid-crossing still ends on known ground.
- A capital that rolls into the next day is just a little more spacing.

## 5. Practicalities

**Tags.** These are added to the architecture doc's `kind::` and `region::`:

- `region::NN-<slug>`, zero-padded in ring order, so the tag sidebar lists regions in study order.
- `pass::1` or `pass::2`.

**What the learner does:**

| Goal | How |
|---|---|
| Follow the program | Study the deck. In deck options, keep the new-card **sort order on "order gathered"** (the default) and never use random. A random order deletes the curriculum. |
| Learn one region now | Make a filtered deck: `deck:"Geography" tag:region::14-* is:new`, order **"Order due"** (for new cards, due is the position. *Verify on AnkiDroid and AnkiMobile.*) Cards studied there go back to the main deck as reviews. Unstudied cards go back to their old positions. |
| Home region first | The same filtered deck, for your home region, on day 1. Then continue the main deck. That costs one break in continuity and needs no special build. It also stays compatible with `positions.lock`, which a rotated build would not be. |
| Revise a region | `tag:region::04-* -is:new`, ordered by due or at random. |
| See the map | The PDF guide, sectioned by region in ring order (the architecture doc already proposes sectioning it by region). It's an atlas to keep beside the deck, so the knowledge is in the world as well as in the cards. |

**Finishing a region** is the natural progress milestone. A count such as "region 7 of 21" in the README's study notes costs nothing.

**Existing users** (the 141 feature cards imported with v1 positions 0–140). Re-import keeps those positions, so a v1 user's unstudied features come before every country. The architecture doc decides not to build any repositioning. From the curriculum side that's acceptable: these users aren't total beginners, and they finish the features they started before going round the ring. The README should say:

- **Studied little or nothing:** delete the deck and import fresh to get the full program order.
- **Mid-way:** keep going. The ring starts once your v1 features are done, or run region filtered decks in parallel.

## Decisions needed (recommended default in bold)

1. **Structure:** **(c) atlas ring with a short depth pass**, against (a) region-complete or (b) tier spiral.
2. **Default start:** **Western Europe.** Home region first through a filtered deck rather than rotated builds.
3. **Region list and ring:** **the 21 regions above.** Check in particular Turkey with the Caucasus, Sudan in East Africa, Mexico with Central America, and Iran with Central Asia.
4. **Capital placement:** **2–3 cards after its country**, against immediately after.
5. **Pass 1 features:** **tiers 1 and 2**, with only tier 3 in pass 2.
6. **Microstates:** **keep the country card** (for a microstate, where it is *is* the knowledge). Drop the capital card where the capital shares the country's name and dot (Monaco, Vatican, Singapore). ⚠ This differs from the architecture doc's D11, which is capital card only.
7. **City tiers:** **split the 80–150 cities into core (pass 1, about 55) and secondary (pass 2).** That needs a `tier` on each city.
8. **Orientation contents:** **4 oceans and 4 planetary bands, plus 7 new continent cards.** ⚠ This replaces D10's end-of-pass interlude.
9. **Anti-confusion rule:** **a 3–10 window, a curated list of confusable countries, and no deck-wide category alternation.**
10. **Suggested rate:** **15 a day**, stated in the README, with a warning before regions 11 and 21.
11. **Existing users:** **no repositioning tool.** README guidance only, consistent with the architecture doc.

If these are accepted, write ADR 0009 (curriculum order), superseding ADR 0004's tier-first rule and category-alternation rule.
