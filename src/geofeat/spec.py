"""Everything that affects a card's pixels, apart from the geometry it is given and the renderer's own code."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from geofeat.model import LAND_FAMILIES, Feature, FrameOptions, Part, Style
from geofeat.resolve import features_by_id
from geofeat.style import AREA_ALPHA, WATER_AREA_ALPHA

WATER_CATEGORIES = frozenset({"Water Bodies", "Straits & Chokepoints"})
CLOSE_UP_TYPES = frozenset({"Pass", "Corridor", "Lake"})  # borders are a main landmark in these close-ups
# Natural Earth layers every card's basemap may read: land, ocean and borders at both scales, lakes, rivers and the
# locator inset's land. The shaded relief raster is read directly, not as a layer; RELIEF names its lock entry.
BASEMAP_LAYERS = frozenset({
    "10m_land", "50m_land", "10m_ocean", "50m_ocean", "50m_lakes", "50m_rivers_lake_centerlines",
    "10m_admin_0_boundary_lines_land", "50m_admin_0_boundary_lines_land",
})
ADMIN1_LAYER = "50m_admin_1_states_provinces_lines"
RELIEF = "GRAY_50M_SR.tif"


class RenderSpec(BaseModel):
    """A card's render inputs. `geometry` is the parts the caller resolves and passes to `render()` alongside this.

    Overlays: `country` draws the geometry as a country (the subject, outlined in red, or faint context) in place of
    the style's highlight; `dot` (lon, lat) marks a city on top. `outline` is reserved for territory and dispute
    outlines and isn't drawn yet.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    style: Style
    geometry: tuple[Part, ...]
    frame: FrameOptions = FrameOptions()
    trim_to_largest: bool = False
    fill_alpha: float = AREA_ALPHA  # of an area or band highlight
    land_clip: bool = False  # mirrors resolve.clip_to_land, which feature cards resolve through; hashed, not drawn
    close_up_borders: bool = False  # heavier country borders when the frame is a close-up
    country: Literal["subject", "context"] | None = None
    dot: tuple[float, float] | None = None
    outline: Literal["solid", "dashed"] | None = None

    @classmethod
    def from_feature(cls, feature: Feature) -> "RenderSpec":
        water = feature.style != "area" or feature.category in WATER_CATEGORIES
        return cls(
            style=feature.style,
            geometry=tuple(feature.geometry),
            frame=feature.frame,
            trim_to_largest=feature.trim_to_largest,
            fill_alpha=WATER_AREA_ALPHA if water else AREA_ALPHA,
            land_clip=feature.style == "area" and feature.family in LAND_FAMILIES,
            close_up_borders=feature.type in CLOSE_UP_TYPES,
        )

    def layers(self) -> frozenset[str]:
        """The Natural Earth layers this card reads: its own geometry's (through any features it references), its
        context features' geometry's, admin-1 lines if drawn, and the basemap's."""
        own = set(self._geometry_layers(()))
        for other in self.frame.context:
            own |= RenderSpec.from_feature(features_by_id()[other])._geometry_layers((other,))
        if self.frame.admin1:
            own.add(ADMIN1_LAYER)
        return frozenset(own) | BASEMAP_LAYERS

    def _geometry_layers(self, stack: tuple[str, ...]) -> set[str]:
        found = {p.layer for p in self.geometry if p.layer}
        for other in [p.feature for p in self.geometry if p.feature]:
            if other in stack:
                raise ValueError(f"feature reference cycle {' -> '.join((*stack, other))}")
            found |= RenderSpec.from_feature(features_by_id()[other])._geometry_layers((*stack, other))
        return found
