# 3. Projection and framing

Status: accepted, 2026-10-13. Amended on 2026-10-13 (`cf89ef5`) to note the retired passes, islands and Cumberland Gap. Still the current rule; the summary is in [architecture.md](../architecture.md#rendering). The inset's 160 × 80 px is at an 800 px-wide card (320 × 160 at 1600 px); the other sizes are at 1600 px as stated.

Amended on 2026-10-14 (World Atlas P4) by the [World Atlas plan](../world-atlas-plan.md)'s decisions 6, 7 and 9: the close-dot exception to the **Minimum frame**, continents on the world map, and scattered states (see [Amendment: political cards](#amendment-political-cards-2026-10-14)).

Amended on 2026-10-15 (v2.1.0) by [ADR 0010](0010-region-framing.md): country, territory, dispute, capital and city cards are framed on their curriculum region, with detail insets, and show no world locator; their rings are limited to microstate scale. Feature and continent cards keep this ADR's rules. The close-dot frame below survives only for close-dot cities in giant hosts.

## Context

Phone QA at 390 px wide found three problems:

- Close-up frames of 400–800 km showed no recognisable coastline.
- The per-card orthographic locator globe changed on every card.
- Feature-centred Lambert azimuthal frames twisted wide maps: north leaned at the edges of the Gulf Stream and Kuroshio frames. A first fix with Albers conics still fanned the meridians and was rejected.

## Decision

**North up, cylindrical only.** All maps are north-up with vertical meridians: on every card and in the inset, every meridian is a vertical line and every parallel a horizontal line, so due north is straight up everywhere in the image.

| Frame | Projection |
|---|---|
| Regional | Equirectangular (`+proj=eqc`) in metres, central meridian and standard parallel (`lat_ts`) at the frame centre, so shapes are true near the centre |
| Highlight wider than about 10,000 km, or one a regional frame can't hold | The same projection with `lat_ts` 0: a plate carrée world map, centred on the feature's longitude |

- **Fitting:** the frame is fitted in an equirectangular map around the feature (or `frame.centre`), then redrawn with the projection centred on that frame and refitted.
- **Poles:** a frame never shows past a pole; it is moved back from it. A band round a pole (the Arctic Ocean) gets a frame the globe's full width at its centre parallel, with the pole as the top edge. There is no polar exception.
- **Antimeridian:** the central meridian is the frame centre, and geometry is split at the opposite meridian, so frames across 180° (Bering, Kuroshio, Pacific) are continuous.
- **Rejected:** Albers, Mercator and polar azimuthal frames. Conic meridians fan out and Equal Earth's curve, so north isn't straight up at the edges; Mercator explodes near the poles.

**Minimum frame.** Every regional frame is at least 2,600 km wide, so a recognisable coastline is always in view. Small features are found by their ring. This replaces:

- the 400, 600 and 800 km minimums by style;
- the per-card close-up spans;
- weaker relief in frames under 800 km.

The rule that widened a frame until it showed sea, a lake or a major river is dropped; at 2,600 km every frame already shows one.

**Inset.** Every inset is the same 160 × 80 px plate carrée world map, centred on 0° and never re-centred.

- **Frame marker:** a `#333` box, or a 12 px `#333` dot (at 1600 px) when the box would be under 32 px or would cross 180°. Nothing in the inset is red.
- **Placement:** moves to another corner when it would cover the highlight.
- **Shown on:** regional frames under 8,000 km only. Wider frames already show whole continents.

**Highlight legibility.** Sizes are in pixels at 1600 px wide.

- **Strait width:** a polygon strait with mean width (2 × area ÷ perimeter) over 24 px gets the sea treatment: 30% fill, 6 px outline. A narrower one is a 12 px channel line with a casing.
- **Ring on small areas:** an area gets a ring when it is smaller in area than a 66 px disc (about 16 px on a phone) or under 100 px long.
- **Ring on short lines:** a strait or line under 123 px long also gets a ring.

## Consequences

- Nothing is rotated or fanned. The cost is east–west stretch away from the centre parallel: wide high-latitude frames (Gulf Stream, Greenland) widen northwards, and the Arctic Ocean's frame stretches the pole across the top edge.
- At 2,600 km, short straits and capes are found by their ring, with little local detail. This applied to passes and small islands too, until those cards were retired.
- The Danish Straits and the Strait of Magellan fall under 24 px mean width at this zoom, so they draw as channel lines.
- Lake Chad and the Hindu Kush/Pamirs/Karakoram trio keep a fixed `frame.centre`. Cumberland Gap (since retired) kept `admin1`, which draws state borders.

## Amendment: political cards (2026-10-14)

World Atlas adds country, territory, dispute, capital, city and continent cards. They keep the cylindrical, north-up rule and the 2,600 km minimum, with these exceptions and clarifications.

**Close dots (decision 6).** A capital or city card whose dot has another carded dot (a capital or a city) within 150 km, measured on the ellipsoid, is framed on its own dot: 1,000 km wide, centred on the dot, with the locator inset. Without it the two dots sit about 40–150 px apart at their country's frame and read as one place; at 1,000 km they are 65–240 px apart. Every other dot card keeps its country's frame, at least 2,600 km wide. The rule is symmetric, so both cards of a pair get the tight frame (Kyoto and Osaka; Dubai and Abu Dhabi), and it covers capitals of neighbouring states (Vienna and Bratislava, Kinshasa and Brazzaville). The tight frame is centred on the dot alone, not on the pair, and it is the only frame narrower than 2,600 km. Kinshasa and Brazzaville, 5 km apart, still overlap at 1,000 km; their context countries and the Congo between them tell them apart.

**Continents (decision 7).** A continent card is always drawn on the plate carrée world map, centred on its own longitude, whatever its size. Equal Earth was considered and rejected under this ADR: its meridians curve. Antarctica is the band along the bottom of the world map. A full-width polar band frame like the Arctic Ocean's was tried and rejected, because at Antarctica's centre parallel it shows only a third of the continent.

**Scattered states (decision 9).** A small subject (under the 66 px disc or 100 px long) is ringed per group of parts within 160 px of each other, not with one ring round its bounds. The frame holds the whole spread at the usual 45% fill, so Kiribati shows its Gilbert, Phoenix and Line groups, each ringed. The test is on the whole outline, so a large state never rings its remote specks.

**Microstates and small territories** keep the ring rule above: at 2,600 km, Vatican City, Monaco, Gibraltar and Macau are rings.

