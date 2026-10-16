# 13. Subdivision framing

Status: accepted, 2026-10-16. Amends [ADR 0003](0003-projection-and-framing.md) for the companion decks ([ADR 0012](0012-companion-decks.md)): one fixed frame per country, Alaska and Hawaii moved into boxes, and a conic projection for Canada. World Atlas's cards keep ADR 0003 and [ADR 0010](0010-region-framing.md).

## Context

A companion deck teaches where each of a country's subdivisions lies within that country. The learner should see the same map on every card, so the country's shape and internal borders become familiar and only the red subject changes. World Atlas's framing doesn't do this: it fits each frame to its subject or its region, and it draws no internal borders.

Five problems are particular to these maps:

- **Small subjects.** Rhode Island, Delaware, DC, the Distrito Federal, Molise and Valle d'Aosta are a few pixels across on a phone at their country's scale.
- **Alaska and Hawaii.** A true-position frame for the US is mostly Pacific Ocean and Canada, with the contiguous states small.
- **Lakes and bays.** Natural Earth's admin-1 polygons include the US and Canadian parts of the Great Lakes. A 50m coastline closes Chesapeake Bay, Delaware Bay and Long Island Sound.
- **Canada's Arctic.** On an equirectangular frame centred at 62°N, Ellesmere Island is drawn about twice as wide as it is.
- **Large subjects.** Texas, Amazonas or Quebec can't be shown whole with their neighbours in an inset that also magnifies them.

## Decision

**One fixed frame per country** (`framing: country`, drawn by `src/geofeat/country_map.py`). `FRAMES` gives each country a projection, a lon/lat box the 16:9 frame is fitted round, and the corner for its detail inset. Every card of a deck shares the same main frame, identical to the pixel. The frame doesn't depend on the subject: nothing is fitted or widened, and there is no giant rule.

| Country | Projection | Frame holds | Detail inset |
|---|---|---|---|
| Italy | Equirectangular, 12.6°E, true at 41.5°N | 6–19.2°E, 35.2–47.4°N | Top right, over the Balkans. Bottom right would cover the toe of Calabria, bottom left the south of Sardegna. |
| United States | Equirectangular, 89°W, true at 37°N | 126–52°W, 17.2–50.4°N | Bottom right, over the Gulf and the Atlantic. The frame reaches 52°W and 17°N so the inset's left edge is east of Florida and its top south of Cape Hatteras. |
| Brazil | Equirectangular, 54°W, true at 14°S | 75–33°W, 34.6°S–6.2°N | Bottom left, over the Pacific, Bolivia and Argentina. Every other corner covers part of Brazil. |
| Canada | Lambert conformal conic, 96°W, standard parallels 49°N and 77°N | 141–40°W, 41.5–83.2°N | Top right, over Greenland and Baffin Bay. The frame reaches 40°W so the inset clears Baffin Island. |

A test holds every country to its plan: the country lies wholly inside the frame, and neither the inset nor a box covers any of it. So the inset never covers the subject (Texas, Amazonas, Pará and Sicilia included).

**Canada is conic.** ADR 0003 allows only cylindrical projections, so that north is straight up everywhere. On Canada's frame that would stretch the Arctic islands east to west by up to 2.7 times at 80°N. A conformal conic keeps their shapes true at phone size, as Statistics Canada's own maps do. North is straight up on the central meridian (96°W) and leans about 40° at Yukon and at Newfoundland, as on any map of Canada. That is the trade the user accepted for Canada only.

**Alaska and Hawaii in boxes** (amends ADR 0003's rule that every map shows places in their true position). Each is drawn in a box in the bottom left, over Mexico and the Pacific. Each box is north up, on its own equirectangular projection, with a thin grey frame (`BOX_FRAME`) and no leader lines. Alaska's box is at about half the main map's scale, and Hawaii's at about 1.3 times it, as on most US maps. Alaska is cut at 180°: the Near and Rat Islands, the Aleutians west of the antimeridian, are left out. On the Alaska and Hawaii cards the leader lines run from the box to the inset, and the inset shows the subject in its true position with its neighbours.

**What is drawn:**

- **Basemap.** World Atlas's basemap at 10m at every width, so bays, sounds and straits keep their shape at the US scale.
- **The country.** Relief is toned down under a wash of the land colour (`RELIEF_TONE`), so the borders read. Lakes over 1,000 km² (`10m_lakes`) are cut out of every subdivision, so the Great Lakes and Lake Winnipeg are water.
- **Other countries** are an opaque grey-blue (`FOREIGN`, `#C9D0D4`), a step off the ocean's value, with no relief, rivers or borders, and only a faint half line of coast. The country's warm land is the lightest land on the map, so it stands apart from its neighbours by value, not hue alone, and in a deuteranopia simulation too. San Marino and the Vatican show as holes in Italy, and Corsica stays grey.
- **Internal borders.** The admin-1 outlines' shared edges, and the country's land border with its neighbours (US–Canada, Italy–France), on land only, in dark grey `#5F5A52`, solid, 2 px at 1600 px wide (about 0.5 px on a phone). That is lighter and thinner than the coast's 2.4 px.
- **The subject.** World Atlas's country highlight, as on a country card (`render._country`): a faint red fill (`HIGHLIGHT` at `OUTLINE_ALPHA`, 12%) under a 3 px red outline with a white casing (`OUTLINE_PX`, `CASING_PX`, at an 800 px card). The internal borders and relief read through the fill. A subdivision's islands (Elba, Pantelleria, Lampedusa) are part of it and outlined with it. A hole in the subject, the Distrito Federal in Goiás, stays unfilled, with its own border.
- **Small subjects.** A subject under 33 px across (8 px on a 390 px phone) also gets a red ring with a white halo on the main map.

**A detail inset on every card but the largest.** It takes 35% of the card's width, in the country's corner. It is north up, on an equirectangular projection centred on the subject, so the subject keeps its shape and true position.

- **Size.** The subject's main body fills 45% of the inset on the 16:9 measure (its width, or its height times 16/9, whichever is larger), which leaves room for neighbours. A small subject gets more context: the inset widens until the subject is 18% of its width, but not past 250 km. DC fills 18% of the width. Rhode Island, which is tall, fills 45% on the 16:9 measure and 16% of the width.
- **Zoom.** The inset is at least 1.5 times the scale of the main map (or the subject's box), compared on the ground at the subject. A subject whose whole body can't fit an inset at 1.5 times has no inset at all (below).
- **Leader lines.** Only the inset has the dark frame and leader lines, which run from the subject (or its ring).
- **Named exceptions** (`Inset.fit`).
  - **No inset** ("cropped"): the rule is that a card has no inset when one at 1.5 times the main map's scale can't hold the whole subject. These subjects are large enough to read on the main map, and an inset would only show their middle. The rule gives exactly these 14: Idaho, California, Texas; Amazonas, Pará, Mato Grosso, Bahia; Saskatchewan, Manitoba, Ontario, Quebec, Newfoundland and Labrador, Northwest Territories, Nunavut;
  - **Tight**, which keep their inset: the subject fills over 80% of it, leaving little room for neighbours: Piemonte, Sardegna; Michigan, Minnesota, Nevada, Alaska; Minas Gerais, Tocantins, Maranhão, Piauí; British Columbia, Alberta.

**Resolution stays 1600 × 900.** That is already 4.1 times a 390 px phone's width, over the 3 times needed to keep a 1 px phone hairline crisp (4 px at 1600). Going higher would double the deck's size for no visible gain.

**Cache.** A companion card's key adds `country_map.py` to the renderer's code hash and `10m_lakes` to the basemap layers. World Atlas's keys don't hold either, so tuning the companion maps never re-renders World Atlas. A card's job carries its subject, and its country's other subdivisions as context, so a change to any outline re-renders that deck. Context is hashed in sorted order, so reordering `data/subdivisions.yaml` re-renders nothing.

## Consequences

- A learner sees one map per deck, which builds the country's internal map as World Atlas's region frames build the world's.
- Every companion card but the 14 largest has an inset. Those 14 are large enough to read on the main map, where an inset would only have shown their middle.
- The US main map is not true-position: Alaska and Hawaii are moved, Alaska at a smaller scale. That is the convention of US maps, and each card's inset shows the subject in its true place.
- Canada's map leans meridians at its edges. It is the only map in the project that isn't north-up everywhere.
- Adding a country means a `FRAMES` entry, and checking its inset corner against the test above.
