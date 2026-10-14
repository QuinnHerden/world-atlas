"""How a card is drawn: everything that affects its pixels apart from the geometry it is given and the renderer's code."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from geofeat.model import Feature, FrameOptions, Style
from geofeat.style import AREA_ALPHA, WATER_AREA_ALPHA

WATER_CATEGORIES = frozenset({"Water Bodies", "Straits & Chokepoints"})
CLOSE_UP_TYPES = frozenset({"Pass", "Corridor", "Lake"})  # borders are a main landmark in these close-ups
# Natural Earth layers the basemap and locator inset may draw. Their pinned sha256s, and the relief raster's (read
# directly, not as a layer), are in every card's cache key; a layer read during a render must be listed here.
BASEMAP_LAYERS = frozenset({
    "10m_land", "50m_land", "10m_ocean", "50m_ocean", "50m_lakes", "50m_rivers_lake_centerlines",
    "10m_admin_0_boundary_lines_land", "50m_admin_0_boundary_lines_land", "50m_admin_1_states_provinces_lines",
    "10m_admin_0_boundary_lines_disputed_areas",
})
RELIEF = "GRAY_50M_SR.tif"


class RenderSpec(BaseModel):
    """The visual treatment of a card's geometry. The geometry itself, and the context and former-extent shapes that
    `frame.context` and `frame.former` name, are resolved by the caller and passed to `render()` alongside.

    Overlays: `country` draws the geometry as a country (the subject, outlined in red, or faint context) in place of
    the style's highlight; `dot` (lon, lat) marks a city on top. `outline: dashed` draws a subject's red edge dashed
    (territories and disputes); a state's overlay (`outline` unset) also clears the basemap's borders inside it.

    Framing: `world` puts the card on the world map whatever its size (continents); `close_dot` frames the dot
    itself, tighter than the minimum frame, because another carded dot lies close by (ADR 0003's close-dot rule).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    style: Style
    frame: FrameOptions = FrameOptions()
    fill_alpha: float = AREA_ALPHA  # of an area or band highlight
    close_up_borders: bool = False  # heavier country borders when the frame is a close-up
    country: Literal["subject", "context"] | None = None
    dot: tuple[float, float] | None = None
    outline: Literal["dashed"] | None = None
    world: bool = False
    close_dot: bool = False

    @classmethod
    def from_feature(cls, feature: Feature) -> "RenderSpec":
        water = feature.style != "area" or feature.category in WATER_CATEGORIES
        return cls(
            style=feature.style,
            frame=feature.frame.model_copy(update={"context": [], "former": None}),  # resolved into the job
            fill_alpha=WATER_AREA_ALPHA if water else AREA_ALPHA,
            close_up_borders=feature.type in CLOSE_UP_TYPES,
            world=feature.type == "Continent",
        )
