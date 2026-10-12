"""Map colours and mark sizes, shared by the renderer and the checks that reason about how a card looks.

Pixel sizes are for an 800 px wide card; the renderer doubles them at 1600 px.
"""

CARD_PX = 800

LAND = "#E9E4D8"
OCEAN = "#C3D5E2"
BORDER = "#A39E94"
COAST = "#7F8A93"
CONTEXT_RIVER = "#9DB8CC"
HIGHLIGHT = "#B2182B"
CASING = "#FFFFFF"
INSET_LAND = "#BDB6A8"
INSET_OCEAN = "#DCE7EF"
INSET_FRAME = "#3A3A3A"

AREA_ALPHA = 0.40
WATER_AREA_ALPHA = 0.30

STROKE_PX = {"line": 5, "strait": 6, "flow-current": 5, "flow-wind": 3}
CASING_PX = 1.5  # per side
RING_PX = 48
CONTEXT_RIVER_PX = 1.0
PARENT_RIVER_PX = 1.5

CURRENT_HEAD_PX = (20, 22)  # length, width: over 4x the shaft, so direction reads on a phone
CURRENT_HEAD_EVERY_PX = 250
WIND_CHEVRON_ARM_PX = 10
WIND_CHEVRON_PX = 2
WIND_CASING_PX = 0.5  # per side; thinner than the current casing so winds read lighter
WIND_GLYPH_PX = 90
WIND_DASH_PX = (8, 5)
