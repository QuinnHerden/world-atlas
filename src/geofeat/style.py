"""Map colours and mark sizes, shared by the renderer and the checks that reason about how a card looks.

Pixel sizes are for an 800 px wide card; the renderer doubles them at 1600 px.
"""

CARD_PX = 800

LAND = "#E9E4D8"
OCEAN = "#C3D5E2"
BORDER = "#8E887E"
FORMER_SHORE = "#A39E94"  # a lake's past shoreline, dashed (the Aral Sea in 1960)
COAST = "#7F8A93"
CONTEXT_RIVER = "#9DB8CC"
HIGHLIGHT = "#B2182B"
CASING = "#FFFFFF"
CONTEXT_EDGE = "#4A463F"  # a country drawn as context for a city dot
INSET_LAND = "#BDB6A8"
INSET_OCEAN = "#DCE7EF"
INSET_FRAME = "#333333"

AREA_ALPHA = 0.40
WATER_AREA_ALPHA = 0.30
OUTLINE_ALPHA = 0.12  # fill under an "outline" highlight
CONTEXT_TINT_ALPHA = 0.45  # white wash over a "context" country

STROKE_PX = {"line": 5, "strait": 6, "flow-current": 5, "flow-wind": 4.5}
CASING_PX = 1.5  # per side
RING_PX = 48
OUTLINE_PX = 3
CONTEXT_EDGE_PX = 1.25
DOT_PX = 18  # a city, with no ring: 36 px at 1600 wide, ~9 px on a phone
CONTEXT_RIVER_PX = 1.0
COAST_PX = 1.2
BORDER_PX = 1.0
CLOSE_UP_BORDER_PX = 1.5  # Pass, Corridor and Lake close-ups, where borders are the main landmark
FORMER_SHORE_PX = 1.0
STRAIT_OUTLINE_PX = 3  # a strait wide enough to be drawn as a sea
INSET_FRAME_PX = 1.25
INSET_FRAME_MIN_PX = 16  # a smaller frame rectangle is drawn as a dot
INSET_DOT_PX = 6
PARENT_RIVER_PX = 1.5

CURRENT_HEAD_PX = (20, 22)  # length, width: over 4x the shaft, so direction reads on a phone
CURRENT_HEAD_EVERY_PX = 250
WIND_CHEVRON_ARM_PX = 20
WIND_CHEVRON_PX = 4
WIND_CASING_PX = 0.5  # per side; thinner than the current casing so winds read lighter
WIND_GLYPH_PX = 90
WIND_DASH_PX = (8, 5)
