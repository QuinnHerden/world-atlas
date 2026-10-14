# Grounding blurbs, regions 1–7 (P2.7a)

Prepared 2026-10-14 for the `note` field of the country and capital cards in [world-atlas-plan.md](../../world-atlas-plan.md) (Decisions: "Companion PDF guide"; "Capitals"). It covers ring regions 1–7, from Western Europe to the Levant and Mesopotamia. Countries are in walk order, and each country's capital row follows it. The ordering engine places the capital card 2–3 cards later.

**Scope.** 56 country rows and 51 capital rows, 107 in all.
- **No capital card:** Monaco, Luxembourg, San Marino and Vatican (the capital shares the country's name and dot), and Palestine.
- **Out of scope:** Northern Cyprus is a pocket in region 6, and Abkhazia, South Ossetia and Transnistria become pockets of Georgia and Moldova. All four get dispute cards only, so they have no rows here.

**Source tags** (same scheme as [cities.md](../cities.md)):
- **[V]**: the page or file was opened and the claim read there.
- **[S]**: confirmed from search-indexed text only.
- **FB-xx**: the World Factbook profile with GEC code `xx`, read from a local clone of the community mirror `github.com/factbook/factbook.json` at commit `144d697` (2026-09-11). The CIA retired the Factbook site in February 2026 (mirror README), and the mirror's newest notes are dated 2025. Fields used: Introduction/Background, Geography (Location, Land boundaries, Geography - note, Major rivers, Elevation), Government (Country name, Capital name, note and etymology, National heritage), Military - note. Every FB key is [V].
- The ring table, capital picks and border decisions come from the plan and [ne-political-layers.md](../ne-political-layers.md).

**Rules applied.**
- **No statistics.** No population, area or length appears. Dates are kept only where the source states them.
- **Hedging is kept.** When a source says a city's name "may" derive from something, the blurb says so too.
- **Self-descriptions are attributed** ("regards itself as", "claims").
- **Disputes** are worded to match ADR 0008: the card shows the internationally recognised border, and the blurb says who controls or claims what.
- **Time-sensitive items** are marked *(as of 2026-10; verify)* and listed under [Flagged items](#flagged-items).

**Fact-check.** A second researcher checked a random 25% sample (27 rows, seed 20261014) plus every flagged row against the opened sources: 37 rows in all. 31 passed. Five were fixed (country-swe, country-che, capital-che-bern, country-cyp, country-syr), and the resolution 478 sentence was cut from capital-isr-jerusalem.

**Web-search note.** The session's shared web-search budget ran out early in this task. After that, every claim was grounded in an opened file or page ([V]). Claims that could not be grounded that way were cut, not marked [S].

## 1. Western Europe

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| country-prt | country | Portugal | In southwestern Europe on the North Atlantic, west of Spain, its only land neighbour. A global maritime power in the 15th and 16th centuries, it lost much of its wealth after the 1755 earthquake that destroyed Lisbon. | FB-po [V] |
| capital-prt-lisbon | capital | Lisbon | Portugal's capital is a coastal city on the Atlantic side of the country. It was largely destroyed by the 1755 earthquake. Its Monastery of the Hieronymites and Tower of Belém are World Heritage sites. | FB-po [V] |
| country-esp | country | Spain | In southwestern Europe between the Atlantic and the Mediterranean. It borders Portugal, and France and Andorra across the Pyrenees; its North African enclaves of Ceuta and Melilla border Morocco. Its 16th–17th-century empire was a world power; after the civil war of 1936–39, Franco's dictatorship lasted until his death in 1975. | FB-sp [V] |
| capital-esp-madrid | capital | Madrid | Spain's capital lies in the interior, unlike most of Spain's largest cities, which are on the coasts. It grew from a small Moorish fort first recorded as Majerit in 932. | FB-sp [V] |
| country-and | country | Andorra | A tiny landlocked principality high in the Pyrenees between France and Spain. Its heads of state are two co-princes, the French head of state and the Bishop of Urgell, an arrangement dating back to 1278. | FB-an [V] |
| capital-and-andorra-la-vella | capital | Andorra la Vella | Andorra's capital. The Catalan name means "Andorra the Old". | FB-an [V] |
| country-fra | country | France | The largest country in Western Europe, with coasts on the Bay of Biscay, the English Channel and the Mediterranean. It borders Belgium, Luxembourg, Germany, Switzerland, Italy, Monaco, Andorra and Spain. A permanent member of the UN Security Council. | FB-fr [V] |
| capital-fra-paris | capital | Paris | Named after the Parisii, a Celtic tribe; the Roman town on the site was Lutetia. The banks of the Seine through the city are a World Heritage site. | FB-fr [V] |
| country-mco | country | Monaco | A principality on the Mediterranean, surrounded on land by France near the Italian border. It is the world's second-smallest state, after the Vatican, and the smallest with a coastline. The Grimaldi family has ruled it since the Middle Ages, and a 19th-century casino made it famous. | FB-mn [V] |
| country-bel | country | Belgium | On the North Sea between France and the Netherlands, also bordering Germany and Luxembourg. It became independent from the Netherlands in 1830 and is divided between Dutch-speaking Flemings in the north and French-speaking Walloons in the south. | FB-be [V] |
| capital-bel-brussels | capital | Brussels | Belgium's capital is the seat of both the EU and NATO. The Grand Place is a World Heritage site. | FB-be [V] |
| country-lux | country | Luxembourg | A landlocked grand duchy between Belgium, France and Germany. Its name probably means "little fortress", and it was one of the six founders of the EEC, now the EU, in 1957. The capital shares the country's name and has no card of its own. | FB-lu [V] |
| country-nld | country | Netherlands | On the North Sea between Belgium and Germany, at the mouths of the Rhine, Meuse and Scheldt. The name means "the lowlands", and much of the land lies below or barely above sea level. It was a leading seafaring and trading power in the 17th century. | FB-nl [V] |
| capital-nld-amsterdam | capital | Amsterdam | The constitutional capital: Article 32 requires the monarch to be sworn in "in the capital city", Amsterdam. Parliament and the government sit in The Hague. The name comes from a dam on the Amstel river, and its 17th-century canal ring is a World Heritage site. | SG-NL [V]; FB-nl [V] |
| country-gbr | country | United Kingdom | Islands off northwest Europe between the North Atlantic and the North Sea: Great Britain and the northeast of the island of Ireland. Its only land border is with Ireland, and the Channel Tunnel links it to France. It left the EU in 2020. | FB-uk [V] |
| capital-gbr-london | capital | London | Founded as the Roman settlement of Londinium around AD 43. The Tower of London and Maritime Greenwich are World Heritage sites. | FB-uk [V] |
| country-irl | country | Ireland | Occupies most of the island of Ireland, west of Great Britain; its only land border is with Northern Ireland (UK). The 1921 Anglo-Irish Treaty brought independence from the UK but left six northern counties in the UK. | FB-ei [V] |
| capital-irl-dublin | capital | Dublin | Ireland's capital and a major port. The name comes from Irish *dubh linn*, "black pool", after the dark water of the River Liffey. | FB-ei [V] |

## 2. Nordic & Baltic

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| country-isl | country | Iceland | An island in the North Atlantic between Greenland and Europe, northwest of the UK, and the westernmost European country. Its parliament, the Althingi, dates from 930. Glaciers cover more of it than of all continental Europe. | FB-ic [V] |
| capital-isl-reykjavik | capital | Reykjavík | The world's northernmost national capital. The name means "smoky bay", after the steam from nearby hot springs. | FB-ic [V] |
| country-nor | country | Norway | A long, mountainous country on the North Sea and the Atlantic, west of Sweden, with Finland and Russia on its far northern border. It has one of the world's longest and most rugged coastlines. Independent from its union with Sweden since 1905, it rejected EU membership in referendums in 1972 and 1994. | FB-no [V] |
| capital-nor-oslo | capital | Oslo | Norway's capital, a port on a fjord. The name may come from Old Norwegian *os*, "estuary". | FB-no [V] |
| country-swe | country | Sweden | Between Norway and Finland on the Baltic Sea and the Gulf of Bothnia. A military power in the 17th century, it has fought no war in two centuries. It kept a policy of military non-alignment until it applied to join NATO in 2022, and it became a member in 2024. | FB-sw [V]; NATO-SE [V] |
| capital-swe-stockholm | capital | Stockholm | Sweden's capital, a port, built in the mid-13th century on the site of a fishing village. The name probably joins *stock* ("stake" or "pole") or *stak* ("bay") with *holm* ("island"). | FB-sw [V] |
| country-dnk | country | Denmark | The Jutland peninsula north of Germany, its only land neighbour, plus hundreds of islands. It controls the straits between the North Sea and the Baltic. Once home to Viking raiders. | FB-da [V] |
| capital-dnk-copenhagen | capital | Copenhagen | Denmark's capital. The name means "merchants' harbour", and the city holds a large share of the country's people. | FB-da [V] |
| country-fin | country | Finland | Between Sweden and Russia on the Gulf of Bothnia and the Gulf of Finland, with a long border with Russia; it also borders Norway. Ruled by Sweden and then Russia, it became independent in 1917 and joined NATO in 2023. | FB-fi [V] |
| capital-fin-helsinki | capital | Helsinki | The northernmost capital on the European continent. Swedish King Gustav Vasa founded it in 1550 as Helsingfors. | FB-fi [V] |
| country-est | country | Estonia | The northernmost Baltic state, on the Baltic Sea and the Gulf of Finland between Latvia and Russia, with many offshore islands. The USSR annexed it in 1940. It regained independence in 1991 and joined NATO and the EU in 2004. | FB-en [V] |
| capital-est-tallinn | capital | Tallinn | The name derives from "Danish fort": Danish King Valdemar II founded the city in 1219. Its Old Town is a World Heritage site. | FB-en [V] |
| country-lva | country | Latvia | The middle Baltic state, between Estonia and Lithuania, with Russia and Belarus to the east. Mostly low, fertile plains. Independent after World War I, annexed by the USSR in 1940, and independent again in 1991. | FB-lg [V] |
| capital-lva-riga | capital | Riga | Latvia's capital and a port, on the Western Dvina river. Its historic centre is a World Heritage site. | FB-lg [V] |
| country-ltu | country | Lithuania | The southernmost Baltic state, bordering Latvia, Belarus, Poland and Russia's Kaliningrad exclave. By the end of the 14th century it was the largest state in Europe, and in 1569 it united with Poland. In 1990 it was the first Soviet republic to declare independence. | FB-lh [V] |
| capital-ltu-vilnius | capital | Vilnius | Named after the Vilnia river. Its historic centre is a World Heritage site. | FB-lh [V] |

## 3. Central Europe & Italy

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| country-pol | country | Poland | On the flat North European Plain east of Germany, a corridor long fought over. The Vistula is its longest river. Russia, Prussia and Austria partitioned it out of existence in 1772–95, and in 1989 the Solidarity movement helped end communist rule. | FB-pl [V] |
| capital-pol-warsaw | capital | Warsaw | Poland's capital. Warszawa was the name of a fishing village, several legends link the founding to a man named Wars or Warsz, and the historic centre is a World Heritage site. | FB-pl [V] |
| country-deu | country | Germany | In Central Europe between the Netherlands and Poland, south of Denmark, with coasts on the North Sea and the Baltic. The Danube rises here. Divided into West and East Germany in 1949, it was reunified in 1990. | FB-gm [V] |
| capital-deu-berlin | capital | Berlin | Germany's capital, on the Spree. The name may come from a Slavic word for "swamp". Museum Island is a World Heritage site. | FB-gm [V] |
| country-cze | country | Czechia | Landlocked between Germany, Poland, Slovakia and Austria; the Elbe rises here. Czechoslovakia split peacefully into two states in 1993, the "velvet divorce". The short name Czechia was added in 2016. | FB-ez [V] |
| capital-cze-prague | capital | Prague | Czechia's capital. The name may come from Old Slavic *prah*, "threshold", and historic Prague is a World Heritage site. | FB-ez [V] |
| country-aut | country | Austria | A landlocked Alpine country north of Italy and Slovenia; the Danube is its major river. It was the centre of the Austro-Hungarian Empire, and it has been neutral by law since 1955. | FB-au [V] |
| capital-aut-vienna | capital | Vienna | Austria's capital. The name may come from the Roman Vindobona, and historic Vienna is a World Heritage site. | FB-au [V] |
| country-che | country | Switzerland | A landlocked Alpine country between France, Germany, Austria, Liechtenstein and Italy; the Rhine rises here. It has long kept its neutrality, was not involved in either World War, and joined the UN only in 2002. | FB-sz [V] |
| capital-che-bern | capital | Bern | Switzerland has no official capital. Bern holds the title "federal city" and is home to the government and parliament. Its Old City is a World Heritage site. | SWI-BE [V]; FB-sz [V] |
| country-lie | country | Liechtenstein | An Alpine principality between Switzerland and Austria. It is one of only two doubly landlocked countries, with Uzbekistan, and has a customs and monetary union with Switzerland. | FB-ls [V] |
| capital-lie-vaduz | capital | Vaduz | Liechtenstein's capital. The name may come from Latin *vallis* and Old German, together meaning "German valley". | FB-ls [V] |
| country-ita | country | Italy | A peninsula reaching into the central Mediterranean, with Sicily and Sardinia. It borders France, Switzerland, Austria and Slovenia and surrounds San Marino and the Vatican. The peninsula's states were united into one nation in 1861. | FB-it [V] |
| capital-ita-rome | capital | Rome | By tradition named after Romulus, a legendary founder, though the name may come from an Etruscan name for the Tiber. Its historic centre is a World Heritage site, and Vatican City is an enclave within it. | FB-it [V]; FB-vt [V] |
| country-smr | country | San Marino | A small enclave in central Italy, in the Apennines. It claims to be the world's oldest republic, founded by tradition in 301. The capital shares the country's name and has no card of its own. | FB-sm [V] |
| country-vat | country | Vatican | The world's smallest state, an enclave in Rome. Popes ruled much of the Italian peninsula until Italy took the Papal States and then Rome (1870); the 1929 Lateran Treaties created the independent Vatican City. The capital shares the state's name and has no card of its own. | FB-vt [V] |
| country-mlt | country | Malta | An archipelago in the central Mediterranean, south of Sicily. Its megalithic sites are among the oldest in the world. It was a British colony until independence in 1964. | FB-mt [V] |
| capital-mlt-valletta | capital | Valletta | Malta's capital, founded in 1566 by Jean de la Valette, Grand Master of the Order of Saint John. The whole city is a World Heritage site. | FB-mt [V] |
| country-svn | country | Slovenia | In the Julian Alps between Austria and Croatia, also bordering Italy and Hungary. It left Yugoslavia in 1991 after a short war. | FB-si [V] |
| capital-svn-ljubljana | capital | Ljubljana | By tradition the name is linked to *ljubljena*, "beloved", but its origin is probably pre-Slavic. The city's works by architect Jože Plečnik are a World Heritage site. | FB-si [V] |
| country-hun | country | Hungary | Landlocked in Central Europe, divided into three regions by the Danube and the Tisza. A Christian kingdom from 1000, it later became part of Austria-Hungary. A revolt in 1956 was crushed by Soviet forces. | FB-hu [V] |
| capital-hun-budapest | capital | Budapest | Formed in 1873 when Buda, on the west bank of the Danube, merged with Pest on the east bank. The Danube banks and the Buda Castle Quarter are a World Heritage site. | FB-hu [V] |
| country-svk | country | Slovakia | Landlocked and mountainous, south of Poland, with the Tatra Mountains in the north. It was part of the Hungarian kingdom for centuries and then of Czechoslovakia, and it became independent in 1993. | FB-lo [V] |
| capital-svk-bratislava | capital | Bratislava | Slovakia's capital. The name was adopted in 1919, replacing the older Slovak name Prešporok. | FB-lo [V] |

## 4. Balkans

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| country-hrv | country | Croatia | On the Adriatic between Slovenia and Bosnia and Herzegovina, also bordering Hungary, Serbia and Montenegro. Most Adriatic islands lie off its coast. It declared independence from Yugoslavia in 1991 and joined the eurozone and Schengen in 2023. | FB-hr [V] |
| capital-hrv-zagreb | capital | Zagreb | The name means "beyond the bank (or ditch)", from the city's original site above the Sava river. | FB-hr [V] |
| country-bih | country | Bosnia and Herzegovina | Bordered by Croatia, Serbia and Montenegro, touching the Adriatic Sea. The 1992–95 war ended with the Dayton Accords, which split the country into two entities: the Federation and the Bosnian Serb-led Republika Srpska. | FB-bk [V] |
| capital-bih-sarajevo | capital | Sarajevo | The name comes from Turkish *saray*, "palace". | FB-bk [V] |
| country-srb | country | Serbia | A landlocked country on the main land route from Western Europe to Turkey, with the Danube flowing through it. When Yugoslavia broke up, Serbia and Montenegro stayed together until Montenegro left in 2006. Serbia rejects Kosovo's 2008 declaration of independence *(as of 2026-10; verify)*. | FB-ri [V]; FB-kv [V] |
| capital-srb-belgrade | capital | Belgrade | Capital of Serbia and formerly of Yugoslavia. The name means "white city", probably after the white stone of its fortress. | FB-ri [V]; FB-kv [V] |
| country-kos | country | Kosovo | Landlocked between Serbia, Montenegro, Albania and North Macedonia. It declared independence from Serbia in 2008. Serbia does not recognise it, and it is not a UN member *(as of 2026-10; verify)*. In 2010 the International Court of Justice found the declaration did not violate international law. | FB-kv [V]; ICJ-141 [V] |
| capital-kos-pristina | capital | Pristina | Kosovo's capital, also spelled Prishtina. The town takes its name from a river whose name may be pre-Slavic. | FB-kv [V] |
| country-mne | country | Montenegro | On the Adriatic between Croatia and Albania, with Bosnia and Herzegovina, Serbia and Kosovo inland. Its name means "Black Mountain". It voted to restore its independence in 2006 and joined NATO in 2017. | FB-mj [V] |
| capital-mne-podgorica | capital | Podgorica | The name means "under the mountain". | FB-mj [V] |
| country-alb | country | Albania | On the Adriatic and Ionian Seas at the Strait of Otranto, between Montenegro and Kosovo to the north and Greece to the south, with North Macedonia to the east. Independent from the Ottoman Empire since 1912, it was ruled by communists from 1944 until the early 1990s. | FB-al [V] |
| capital-alb-tirana | capital | Tirana | Albania's capital. The name first appears in a Venetian document of 1418, and its origin is unclear. | FB-al [V] |
| country-mkd | country | North Macedonia | Landlocked, north of Greece, also bordering Albania, Kosovo, Serbia and Bulgaria; it shares the Lake Ohrid region with Albania. Independent from Yugoslavia in 1991, it took its current name under the 2018 Prespa Agreement with Greece, in force since 2019. | FB-mk [V]; FB-al [V] |
| capital-mkd-skopje | capital | Skopje | North Macedonia's capital. In the Roman era it was Scupi. | FB-mk [V] |
| country-grc | country | Greece | A peninsular country with an archipelago of islands, on the Aegean, Ionian and Mediterranean Seas between Albania and Turkey. It won independence from the Ottoman Empire in 1830. | FB-gr [V] |
| capital-grc-athens | capital | Athens | By tradition named after the goddess Athena, though the name is probably pre-Hellenic. The Acropolis is a World Heritage site. | FB-gr [V] |
| country-bgr | country | Bulgaria | On the Black Sea between Romania and Turkey, also bordering Serbia, North Macedonia and Greece. The first Bulgarian state formed in the late 7th century. After centuries of Ottoman rule, it became fully independent in 1908. | FB-bu [V] |
| capital-bgr-sofia | capital | Sofia | Named after the city's Church of Saint Sofia, parts of which may date to the 4th century. | FB-bu [V] |
| country-rou | country | Romania | On the Black Sea between Bulgaria and Ukraine, with the Carpathians in its centre. The Danube forms much of its southern border and ends in the Danube Delta. The country was formed by uniting Wallachia and Moldavia in 1859–62. | FB-ro [V] |
| capital-rou-bucharest | capital | Bucharest | Romania's capital. Its name is said to come from a shepherd, Bucur, reputed to have founded the town, though a settlement probably existed earlier. | FB-ro [V] |

## 5. Eastern Europe

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| country-mda | country | Moldova | Landlocked between Romania and Ukraine. Russian forces remain in the breakaway region of Transnistria, east of the Nistru (Dniester); the card shows Moldova's internationally recognised borders, which include it *(as of 2026-10; verify)*. | FB-md [V] |
| capital-mda-chisinau | capital | Chișinău | Moldova's capital. The name may come from an Old Moldovan word for "spring" or "well". | FB-md [V] |
| country-ukr | country | Ukraine | On the Black Sea, the second-largest country in Europe after Russia. It borders Russia, Belarus, Poland, Slovakia, Hungary, Romania and Moldova. Russia seized Crimea in 2014 and launched a full-scale invasion in 2022. The card shows Ukraine's internationally recognised borders *(as of 2026-10; verify)*. | FB-up [V]; FB-rs [V] |
| capital-ukr-kyiv | capital | Kyiv | Centre of Kyivan Rus, the first eastern Slavic state. By tradition it was founded by Prince Kiy. Saint Sophia Cathedral and the Kyiv Pechersk Lavra are World Heritage sites. | FB-up [V] |
| country-blr | country | Belarus | Landlocked and flat, with many glacial lakes, between Poland, Lithuania, Latvia, Russia and Ukraine. Of the former Soviet republics, it has kept the closest ties to Russia, and Russia's 2022 invasion of Ukraine was launched partly from its territory *(as of 2026-10; verify)*. | FB-bo [V] |
| capital-blr-minsk | capital | Minsk | Belarus's capital. The name may come from the Menka river. Its liberation from German troops on 3 July 1944 is marked by the national holiday. | FB-bo [V] |
| country-rus | country | Russia | The world's largest country, stretching from Eastern Europe across northern Asia to the Pacific, with the exclave of Kaliningrad. Mount Elbrus is Europe's highest peak, and Lake Baikal is the world's deepest lake. Crimea is shown in Ukraine, per the recognised-borders rule. | FB-rs [V] |
| capital-rus-moscow | capital | Moscow | Named after the Moskva river. The Kremlin and Red Square are a World Heritage site. | FB-rs [V] |

## 6. Caucasus & Anatolia

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| country-geo | country | Georgia | On the Black Sea between Russia and Turkey, also bordering Armenia and Azerbaijan, and controlling routes through the Caucasus. It made Christianity its state religion in the 330s. After the 2008 war, Russia recognised the breakaway regions of Abkhazia and South Ossetia and keeps forces there. The card shows Georgia's recognised borders, which include both *(as of 2026-10; verify)*. | FB-gg [V] |
| capital-geo-tbilisi | capital | Tbilisi | The name comes from Georgian *tbili*, "warm", after the area's hot sulphur springs. | FB-gg [V] |
| country-aze | country | Azerbaijan | On the Caspian Sea between Russia and Iran, also bordering Georgia and Armenia, with the exclave of Naxçıvan touching Turkey. It fought Armenia over Nagorno-Karabakh from 1988 and retook the whole region in 2023. | FB-aj [V] |
| capital-aze-baku | capital | Baku | On the Apsheron Peninsula, which juts into the Caspian Sea. Below sea level, it is the lowest capital city in the world. Its walled city is a World Heritage site. | FB-aj [V] |
| country-arm | country | Armenia | Landlocked in the Lesser Caucasus, home to Lake Sevan, between Georgia, Azerbaijan, Iran and Turkey. It regards itself as the first state to formally adopt Christianity, in the early 4th century. Turkey has kept their border closed since 1993 *(as of 2026-10; verify)*. | FB-am [V] |
| capital-arm-yerevan | capital | Yerevan | The name may derive from the fortress of Erebuni, built on the site in 782 BC. | FB-am [V] |
| country-tur | country | Turkey | Mostly Anatolia in Asia, with a small European part, Eastern Thrace, across the Bosporus, the Sea of Marmara and the Dardanelles. It has coasts on the Black, Aegean and Mediterranean Seas, and the Tigris and Euphrates rise here. It was founded in 1923 from the remnants of the Ottoman Empire by Mustafa Kemal Atatürk. Türkiye is an approved English short-form name. | FB-tu [V] |
| capital-tur-ankara | capital | Ankara | Long known as Angora, the city was officially renamed Ankara in 1923, when the Republic of Turkey was founded. The name probably refers to a bend, after its original site in a winding gorge. | FB-tu [V] |
| country-cyp | country | Cyprus | The third-largest island in the Mediterranean, south of Turkey; it also contains two British sovereign base areas, Akrotiri and Dhekelia. Since 1974 a UN buffer zone has divided the island. The Turkish Cypriot-administered north declared itself the "Turkish Republic of Northern Cyprus", which only Turkey recognises. The card shows the whole island as Cyprus *(as of 2026-10; verify)*. | FB-cy [V]; FB-tu [V]; FB-ax [V]; UNFICYP [V] |
| capital-cyp-nicosia | capital | Nicosia | A city divided by the UN buffer zone, which in parts of old Nicosia is only a few metres wide; crossing points opened from 2003 *(as of 2026-10; verify)*. Its Greek name Lefkosia and Turkish name Lefkoşa both mean "white city". | UNFICYP [V]; FB-cy [V] |

## 7. Levant & Mesopotamia

| slug | kind | name | blurb | keys |
|---|---|---|---|---|
| country-syr | country | Syria | On the Mediterranean between Lebanon and Turkey, also bordering Iraq, Jordan and Israel; the Euphrates crosses it on its way from Turkey to Iraq, and it shares the Tigris. A French mandate until independence in 1946, it fell into civil war from 2011. Israel has controlled the Golan Heights since 1967, and the card shows them in Syria, per the recognised borders *(as of 2026-10; verify)*. | FB-sy [V] |
| capital-syr-damascus | capital | Damascus | Built at an oasis fed by the Barada River, it is thought to be one of the world's oldest continuously inhabited cities. The Ancient City is a World Heritage site. | FB-sy [V] |
| country-lbn | country | Lebanon | On the Mediterranean between Israel and Syria, the smallest country in continental Asia. France drew its borders in 1920 out of the former Ottoman province of Syria. It became independent in 1943, and a civil war lasted from 1975 to 1990. | FB-le [V] |
| capital-lbn-beirut | capital | Beirut | Lebanon's capital. The name comes from a Phoenician or Hebrew word for "the wells". | FB-le [V] |
| country-isr | country | Israel | On the Mediterranean between Egypt and Lebanon, also bordering Syria, Jordan, the West Bank and the Gaza Strip; the Dead Sea lies on its eastern edge. The State of Israel was established in 1948. The card shows its internationally recognised borders, without the Golan Heights or East Jerusalem. | FB-is [V]; plan Borders row |
| capital-isr-jerusalem | capital | Jerusalem | Israel designates Jerusalem as its capital, but this status is disputed internationally *(as of 2026-10; verify)*. Israel took the city's eastern part in 1967 and has administered it since. The ancient name appears in Egyptian texts of the 14th century BC. | FB-is [V]; NE note |
| country-pse | country | Palestine | Two separate areas: the West Bank, including East Jerusalem, between Israel and Jordan; and the Gaza Strip on the Mediterranean, between Israel and Egypt. The UN General Assembly granted Palestine non-member observer State status in 2012 *(as of 2026-10; verify)*. Under the deck's rules Palestine has no capital card. | FB-we [V]; FB-gz [V]; UN-NMS [V]; plan Borders row |
| country-jor | country | Jordan | Nearly landlocked: its only port, Aqaba, sits at the head of the Gulf of Aqaba. The Dead Sea, the lowest point in Asia, lies on its western border with Israel and the West Bank. Syria, Iraq and Saudi Arabia surround the rest. A Hashemite kingdom, independent since 1946; Petra is a World Heritage site. | FB-jo [V] |
| capital-jor-amman | capital | Amman | Jordan's capital. The Ammonites called the city Rabbath Ammon, "capital of the Ammonites", in the 13th century BC; the name was later shortened to Amman. | FB-jo [V] |
| country-irq | country | Iraq | At the head of the Persian Gulf between Iran and Kuwait, also bordering Turkey, Syria, Jordan and Saudi Arabia. The Tigris and Euphrates flow through it and join as the Shatt al Arab. Ancient Babylon is a World Heritage site. | FB-iz [V] |
| capital-irq-baghdad | capital | Baghdad | Iraq's capital. The name's origin is unclear; it may mean "gift of God". | FB-iz [V] |

## Flagged items

| # | slug | why | what to verify |
|---|---|---|---|
| 1 | country-srb | Kosovo recognition is ongoing | Serbia's position on Kosovo |
| 2 | country-kos | Recognition and UN membership can change | Kosovo still not a UN member; Serbia's non-recognition |
| 3 | country-mda | Military presence | Russian forces still in Transnistria |
| 4 | country-ukr | Active war | Wording on Crimea and the 2022 invasion; check any ceasefire or settlement |
| 5 | country-blr | Political alignment | Belarus's role in Russia's war |
| 6 | country-geo | Breakaway regions | Russian recognition of and forces in Abkhazia and South Ossetia |
| 7 | country-arm | Border status | Turkey–Armenia border still closed (normalisation talks were under way) |
| 8 | country-cyp | Division of the island | No reunification; TRNC recognised only by Turkey |
| 9 | capital-cyp-nicosia | Crossing points | Buffer zone and crossings unchanged |
| 10 | country-syr | Golan; Syrian politics | Golan control. The FB military note (2025) says the government does not control all of Syria; the blurb avoids naming any government. |
| 11 | capital-isr-jerusalem | Contested capital | The sentence on UNSC resolution 478 (1980) was cut: undocs.org, documents.un.org, digitallibrary.un.org and refworld all failed to return the operative text, and UNISPAL showed only the headline ("Measures null and void"). To restore the sentence, read S/RES/478(1980) in a browser first. |
| 12 | country-pse | Status | Observer State status unchanged. The fact-check noted, from memory and unverified, a vetoed Security Council admission draft (April 2024) and GA resolution ES-10/23 (May 2024) adding participation rights; check at press.un.org before relying on it. |
| 13 | country-isr | Recognised-border statement | Matches the plan's Borders row (Golan to Syria; East Jerusalem to Palestine) |
| 14 | capital-dnk-copenhagen | Data | NE's row is named `København`; the card should read "Copenhagen" |
| 15 | capital-che-bern | Source tier | SWI-BE is swissinfo.ch (SRG SSR's public international service), a secondary source. The admin.ch page was not reachable (404). FB-sz labels Bern "capital", so the two sources differ on the label. |

## Sources

| key | source | location | accessed | tier |
|---|---|---|---|---|
| FB-xx | World Factbook profile, community mirror `factbook/factbook.json`, commit `144d697` (2026-09-11). Codes: ax (Akrotiri), po, sp, an, fr, mn, be, lu, nl, uk, ei, ic, no, sw, da, fi, en, lg, lh, pl, gm, ez, au, sz, ls, it, sm, vt, mt, si, hu, lo, hr, bk, ri, kv, mj, al, mk, gr, bu, ro, md, up, bo, rs, gg, aj, am, tu, cy, sy, le, is, we, gz, jo, iz | `<region>/<code>.json`, fields listed above. https://github.com/factbook/factbook.json | 2026-10-14 | [V] |
| SG-NL | States General of the Netherlands, "Five questions for Fred de Graaf and Anouchka van Miltenburg" (quotes Constitution Art. 32) | https://staten-generaal.nl/9370000/1/j9vvki6nu91atr6/vj8igzwtnew8 | 2026-10-14 | [V] |
| SWI-BE | swissinfo.ch, "Why Switzerland hasn't got a capital city", 2025-03-29 | https://www.swissinfo.ch/eng/swiss-oddities/why-switzerland-hasnt-got-a-capital-city/89071876 | 2026-10-14 | [V] (secondary) |
| NATO-SE | NATO, news item on Sweden's accession, 7 March 2024 | https://www.nato.int/cps/en/natohq/news_223446.htm | 2026-10-14 | [V] |
| ICJ-141 | International Court of Justice, *Accordance with international law of the unilateral declaration of independence in respect of Kosovo*, advisory opinion of 22 July 2010 | https://www.icj-cij.org/case/141 | 2026-10-14 | [V] |
| UNFICYP | UN Peacekeeping Force in Cyprus, "About the buffer zone" | https://unficyp.unmissions.org/about-buffer-zone | 2026-10-14 | [V] |
| UN-NMS | United Nations, "Non-member States" (cites A/RES/67/19 of 29 Nov 2012) | https://www.un.org/en/about-us/non-member-states | 2026-10-14 | [V] |
| UN-478 | UN Security Council resolution 478 (1980), UNISPAL record. Not cited in any row (see flag 11). | https://www.un.org/unispal/document/auto-insert-187506/ | 2026-10-14 | headline only |
| NE note | [ne-political-layers.md](../ne-political-layers.md), Israel row: Jerusalem is NE's tagged capital, and its status is contested | repo | 2026-10-14 | internal |

**Excluded:** Wikipedia (used for leads only, and not cited) and `/home/dev/ultimate-geography` (never opened). whc.unesco.org returned 403, so every World Heritage claim rests on the Factbook's "National heritage" field.
