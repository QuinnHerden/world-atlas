# 10. Region framing for political and city cards

Status: accepted, 2026-10-15 (v3.0.0). Amends [ADR 0003](0003-projection-and-framing.md) for country, territory, dispute, capital and city cards: their frame, the locator inset and the ring. Feature and continent cards are unchanged. The projection rule (cylindrical, north up) holds for every card. The constants are in `src/geofeat/frame.py` and `src/geofeat/framing.py`, with comments that explain each rule; sizes in px are at the rendered 1600 px width.

## Context

In v2.0.0 each political card was framed round its own subject, at 45% fill and at least 2,600 km wide. Neighbouring countries therefore came up on frames of different sizes and centres. A learner saw each state alone, not its place among the states studied with it. Small states were rings on a frame with no local detail, and the world locator was the only clue to where a frame was.

The study order already groups states by curriculum region ([ADR 0009](0009-curriculum-order.md)). Drawing a region's cards on one shared frame lets the learner build that region's map card by card.

## Decision

**Political cards are framed on their curriculum region** (`framing.py`, `frame._political`). A country, territory or dispute card is drawn on its region's frame:

- **The region box** is the box round its members' main bodies. Each member is passed as the hull points of its main body, so overseas parts and outlying islands don't stretch it. Giant members don't count. In a region with 4 or more such members, a member whose centre is more than 2.5 times the median member's distance from the region's centre is left out too (the Falklands).
- **Size:** that box, 10% larger (`REGION_MARGIN`), and at least 3,500 km wide (`REGION_MIN_M`), at 16:9. A region may set its own margin, `frame_margin` in `curriculum.yaml` (see [Region margins](#region-margins)).
- **Shared frame:** every card whose subject fits 4% of the frame's width in from its edges (`SUBJECT_MARGIN`) uses the region frame as it is. A subject that doesn't fit moves the frame, or widens it if moving isn't enough.
- **Fill cap:** a subject that would still fill more than 35% of the frame (`REGION_FILL_MAX`) widens its frame to that fill, on the subject's side.
- **Giants:** a subject whose v2.0 frame was over 8,000 km wide (`GIANT_FRAME_M`) keeps its v2.0 frame. They are Russia, Canada, the United States, Greenland, China, India, Japan, Myanmar, Indonesia, Australia, DR Congo, Brazil, Argentina, Chile and Peru. Myanmar and Peru sit near the line.

**Main body.** Parts of a subject within 300 km of each other form a group (`GROUP_GAP_M`); the largest is the main body. A state whose main body holds less than 65% of its land (`MAIN_GROUP_DETAIL`) is scattered (Kiribati, French Polynesia). A scattered state is never a giant and gets no detail inset unless its data forces one.

**Fixed sub-frames** (`framing.SUB_FRAMES`). Two regions don't suit one frame: Oceania is too vast, and the Lesser Antilles are too fine for the Caribbean frame. Their cards are drawn on a fixed lon/lat box instead. A box takes in the land each island group is read against. The fit and fill rules above apply, but a box has no margin and no minimum width. A subject that lies inside its box is never a giant, so it keeps the box (French Polynesia's main body holds 65.0% of its land, just enough to measure as a giant); one that overflows it, Australia on the Melanesia box, keeps its v2.0 frame as a giant.

| Sub-frame | Box (W, S, E, N) | Cards |
|---|---|---|
| Melanesia | 128°E, 34°S, 178°W, 2°N | Australia, Papua New Guinea, Solomon Islands, Vanuatu, New Caledonia |
| Micronesia | 112°E, 12°S, 178°E, 26°N | Palau, Micronesia, Guam, Marshall Islands, Nauru |
| Central Pacific | 145°E, 25°S, 132°W, 28°N | Kiribati |
| Polynesia | 148°E, 48°S, 132°W, 2°S | New Zealand, Fiji, Tonga, Samoa, Tuvalu, French Polynesia |
| Lesser Antilles | 64°W, 11.6°N, 58.8°W, 18.3°N | Antigua and Barbuda, Saint Kitts and Nevis, Dominica, Saint Lucia, Saint Vincent and the Grenadines, Grenada, Barbados, Guadeloupe, Martinique |

Every Oceania card (region 18) must be on a sub-frame; the build fails on one that isn't. The rest of the Caribbean, Trinidad and Tobago included, keeps the region frame.

The Lesser Antilles box is too tight to place on its own, so it gets a **regional locator**: a small plate carrée map of the Caribbean basin (88°W to 56°W, 7°N to 28°N; Florida and Cuba to the coast of South America), 200 px high, with the frame marked as a box. It is styled as the old world locator. It sits top left unless that comes near the subject, then in the next clear corner.

**Detail insets.** A small subject gets a picture-in-picture inset of its main body:

- **Trigger:** the subject's main body, as drawn, is smaller in area than a 56 px disc (`DETAIL_DISC_PX`; 14 px on a 390 px phone). Area alone decides, so a long, thin but sizeable state (Tajikistan, Malawi, Chile) gets none, and states of a size are treated alike.
- **The 2× rule:** the inset must draw the subject at least twice as large as the main map does (`DETAIL_ZOOM`). Otherwise there is no inset.
- **Inset frame:** the main body at 80% fill (`DETAIL_FILL`), at least 200 km wide (`DETAIL_MIN_M`), so a microstate's inset still shows the coast or valley round it. Outlying specks (Rodrigues, Rotuma) neither size nor fill it.
- **Placement:** 35% of the card's width (`DETAIL_SHARE`), 24 px in from a corner. Bottom right, unless that comes near the subject or covers more than 35% land; then the clear corner covering least land.
- **Leader lines** run from the subject (its hull) to the inset. The inset's frame and the lines are one dark stroke with a white halo. Nothing is drawn round the subject, so no small neighbour is covered (Rwanda and Burundi). A subject under 16 px on the main map also gets a 24 px red dot.
- Shaded relief is left out of frames under 400 km, where it blurs to blobs.

**Capitals and cities** are drawn on their host country's frame: the region frame, a sub-frame, or a giant's v2.0 frame (`framing.CITY_REGION_FRAMING`; `False` reverts them to v2.0 framing without touching the political cards). Every capital and city card gets a detail inset round its dot, and the 2× rule doesn't apply to it:

- **Inset frame:** the host's main body whole, at 80% fill, if that fits in 1,200 km (`CITY_DETAIL_MAX_M`); else 1,200 km. It is centred on the host unless the dot would fall outside the middle 80% of the inset, in which case it is centred on the dot. It is never under 200 km.
- **Close dots** ([ADR 0003](0003-projection-and-framing.md#amendment-political-cards-2026-10-14)): the inset is at most 1,000 km round the dot (`CLOSE_DOT_DETAIL_M`), or 17.5% of the main frame's width if that is less. It replaces the v2.0 1,000 km close-dot frame as the main map.
- **Giant hosts:** a city in a giant host gets its inset on the host's v2.0 frame. A close-dot city in a giant host gets no inset: its main map is still the 1,000 km close-dot frame (Kinshasa, Kyoto, Osaka).
- The leader lines run from the dot.

**No world locator** on country, territory, dispute, capital or city cards, giants' v2.0 frames included. A region frame shows enough of the map to place itself, and the Lesser Antilles has its regional locator. Feature cards keep the world locator under ADR 0003's rule (regional frames under 8,000 km).

**Rings.** A country, territory or dispute is ringed only at microstate scale. The whole outline must first pass ADR 0003's small-area test (a 66 px disc, or under 100 px long). Then each island group (parts within 160 px of each other) is ringed only if its land is smaller than a 24 px disc (`render.COUNTRY_RING_DISC_PX`; 6 px on a phone). Slovenia, Montenegro and Uruguay are read by their outline. A group the leader lines already point at gets no ring. In the detail inset, only a subject shorter than 48 px keeps its ring.

**Region margins.** A region in `curriculum.yaml` may set `frame_margin` (1 to 2), used in place of `REGION_MARGIN`. It is for a tall region. Its box is bound north to south at 16:9, so at 1.1 the frame stops just past its northernmost and southernmost members, and the neighbours there are cut off. The margin travels in the spec (`RenderSpec.region_margin`), so it is in the cache key. One region sets it:

| Region | `frame_margin` | Frame | Why |
|---|---|---|---|
| 09 Horn & East Africa | 1.4 | 9,398 km (was 7,384 km) | At 1.1 the frame ran from 13.4°S to 23.9°N, ending at Egypt's border and just past Tanzania's south coast. Sudan and Somalia filled more than 35% and widened their own frames, and Tanzania moved its frame south. At 1.4 the frame runs from 18.5°S to 29°N, takes in southern Egypt and Libya, Malawi, Zambia and northern Mozambique, and every card in the region but Tanzania and Sudan shares it. Those two `include` their neighbours and move the frame at the same width (below). |

**Per-card overrides.** An entry in `countries.yaml` or `territories.yaml` may carry `frame:` (`polities.FrameOverride`):

- `inset: true` or `false` forces the detail inset on or off, scattered states included.
- `inset_km` sets the inset's width (over 0, at most 5,000).
- `inset_centre: [lon, lat]` centres the inset on that point, not on the subject, so it takes in the neighbours the subject is told apart from. The leader lines still run from the subject.
- `ring: false` draws no ring round the subject, on the main map or in the inset. `ring: oval` draws one ring on the main map round all the subject's parts: their minimum-area enclosing ellipse (Khachiyan's algorithm), which may be rotated, computed in the frame's projection and padded 24 px (`SMALL_RING_CLEAR_PX`), in the rings' line style. None is drawn in the inset.
- `include: [ids]` makes the frame also hold the lon/lat box round those countries' or territories' main bodies (giants included; not across 180°). The frame holds the box as it holds the subject, `SUBJECT_MARGIN` in from its edges: it moves first, and widens only if the box doesn't fit. The box travels in the spec (`RenderSpec.hold`).

`inset`, `inset_km`, `inset_centre` and `ring` apply to the country card only. The capital card follows the city rule, and a city's host is never ringed. `include` changes the host's frame, so its capital and city cards follow it. Each override has a comment giving its reason. These are in use:

| Card | Override | Why |
|---|---|---|
| Kuwait | `inset: true` | Just over the size cut at the Arabian Peninsula's scale. |
| Spratly Islands | `inset: true, inset_km: 900` | A sea area of reefs; zoomed in past the default so the island group reads. |
| Tanzania | `include: [malawi, zambia, mozambique]` | Its southern neighbours, which the region frame cut off. The frame keeps the region's 9,398 km and moves south: 30.2°S to 17.3°N. |
| Sudan | `include: [egypt, libya]` | Its northern neighbours to the Mediterranean. The frame keeps 9,398 km and moves north: 11°S to 36.6°N. |
| New Zealand, Papua New Guinea | `include: [australia]` | Each is read against Australia, which the Polynesia and Melanesia boxes cut off. New Zealand's frame is 9,093 km wide, Papua New Guinea's 9,373 km. |
| Micronesia, Kiribati, French Polynesia | `ring: oval` | A ring round each island group cluttered the map, and with none their atolls were specks: they are scattered, so they have no inset. A circle round all of them took in too much sea and too many neighbours. Micronesia's oval holds no other state; Kiribati's takes in Tuvalu and the southern Marshall Islands, and French Polynesia's touches Kiribati's southern Line Islands. |
| Tonga | `ring: false` | Its inset shows it; the ring round the Niuas cluttered the map. |
| Aruba, Curaçao | `inset_centre: [-69.12, 12.35], inset_km: 250` | One inset of the ABC islands (Aruba, Curaçao and Bonaire), so the two are told apart. |

**Render cache.** The region's points travel in the render job and are in its cache key (`jobs.RenderJob.region`). A change to a region's membership re-renders that region's cards. An `include` box and a region's `frame_margin` travel in the spec (`RenderSpec.hold`, `region_margin`), so they are keyed too.

## Consequences

- Cards studied together share a frame, so the learner sees each region's map built up card by card. A giant's card still looks as it did in v2.0, minus the locator.
- Every political, capital and city map changed in v3.0.0, so re-importing replaces those images.
- A card's frame depends on its region's other members. Moving a card between regions, or editing a member's outline, can change its neighbours' maps.
- Close-dot pairs outside giant hosts (Vienna and Bratislava, Dubai and Abu Dhabi) now show their region, with the close-up in the inset instead of on the main map.
- With no world locator, a frame must be recognisable from its own coastlines. The 3,500 km minimum and the sub-frame boxes, chosen round known anchors (New Guinea, eastern Australia, New Zealand, Hawaii, the Philippines), are what make that hold. The Lesser Antilles needed its regional locator.
- Two corner elements can now share a card: the regional locator takes its corner first, and the detail inset avoids it.
