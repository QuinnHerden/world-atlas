import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator
from ruamel.yaml import YAML

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ROOT / "data/features.yaml"
LOCK = ROOT / "data/sources.lock"
GEOMETRY = ROOT / "geometry"
VENDOR = ROOT / "vendor"
DECK = ROOT / "deck"
BUILD = ROOT / "build"
MEDIA_INDEX = BUILD / "media.json"  # feature id -> rendered PNG name
ROOT_DECK = "Geographic Features"

Category = Literal[
    "Water Bodies",
    "Straits & Chokepoints",
    "Mountain Ranges",
    "Passes & Corridors",  # retired entries only
    "Rivers & Deltas",
    "Deserts, Plateaus & Plains",
    "Peninsulas & Isthmuses",
    "Islands",  # retired entries only
    "Regions & Rifts",
    "Climate Systems",
]
# The type word shown on the card. Each covers 3+ active cards, except Isthmus (tells Kra from the Malay Peninsula),
# Valley and Sea route (the user's merges) and Cape (no honest merge); Pass, Corridor and Island are kept only for
# retired entries. See docs/adr/0001-type-vocabulary.md.
FeatureType = Literal[
    "Ocean", "Sea", "Lake",
    "River", "Delta",
    "Strait", "Canal", "Sea route", "Pass", "Corridor",
    "Mountain range", "Plateau",
    "Plain", "Desert", "Valley",
    "Region",
    "Peninsula", "Isthmus", "Island", "Cape",
    "Ocean current", "Wind system", "Climate belt",
]
# A coarse grouping of type words. The pair check treats one highlight covering another as a clash when both share
# a family, whatever their words; area features of a land family are clipped to land.
Family = Literal[
    "water body", "river", "sea passage", "land passage", "relief", "lowland", "region", "landmass", "island", "climate",
]
FAMILY: dict[str, Family] = {
    "Ocean": "water body", "Sea": "water body", "Lake": "water body",
    "River": "river",
    "Strait": "sea passage", "Canal": "sea passage", "Sea route": "sea passage",
    "Pass": "land passage", "Corridor": "land passage",
    "Mountain range": "relief", "Plateau": "relief",
    "Plain": "lowland", "Desert": "lowland", "Valley": "lowland", "Delta": "lowland",
    "Region": "region",
    "Peninsula": "landmass", "Isthmus": "landmass", "Cape": "landmass",
    "Island": "island",  # own family: NE draws some island groups (Spratlys) as a sea-area envelope, so never land-clipped
    "Ocean current": "climate", "Wind system": "climate", "Climate belt": "climate",
}
LAND_FAMILIES: frozenset[Family] = frozenset({"land passage", "relief", "lowland", "region", "landmass"})
# How a hand-authored GeoJSON feature was made; every feature in geometry/ carries one, plus `refs`.
Method = Literal["ne-derived", "pd-dataset", "reference-coords", "hand-drawn"]
Style = Literal["area", "line", "point", "strait", "flow-current", "flow-wind", "band"]

_UNSAFE_TEXT = re.compile(r"[\n<>]|:::|\[\^|^-{3}")


def _card_text(value: str) -> str:
    """Card text is pasted into markdown that Anki renders as HTML, so keep it inert."""
    if _UNSAFE_TEXT.search(value):
        raise ValueError(f"{value!r} contains characters not allowed on a card")
    return value


CardText = Annotated[str, AfterValidator(_card_text)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Part(Strict):
    """One piece of a feature's geometry: rows from a Natural Earth layer, a hand-authored file, or another feature.

    A `subtract` part is cut out of the others, e.g. a sibling range out of a plateau that contains it.
    """

    layer: str | None = None
    select: dict[str, str | int] | None = None
    rows: int = 1
    file: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*\.geojson$")] | None = None
    feature: str | None = None
    subtract: bool = False

    @model_validator(mode="after")
    def _one_source(self) -> "Part":
        sources = [self.file is not None, self.feature is not None, self.layer is not None or self.select is not None]
        if sum(sources) != 1 or (sources[2] and (self.layer is None or self.select is None)):
            raise ValueError("a part needs exactly one of `file`, `feature`, or both `layer` and `select`")
        return self


class Expect(Strict):
    # lon_min, lat_min, lon_max, lat_max; lon_min > lon_max means the box crosses 180°
    bbox: tuple[float, float, float, float]
    length_km: tuple[float, float] | None = None
    area_km2: tuple[float, float] | None = None
    mouth: Literal["sea", "lake", "none"] = "sea"  # where a river must end; "none" for inland sinks like the Okavango


class FrameOptions(Strict):
    min_span_km: float | None = None
    centre: tuple[float, float] | None = None  # lon, lat; siblings sharing a centre and span share a frame
    context: list[str] = []  # ids of line features drawn faintly underneath, e.g. a delta's river
    admin1: bool = False  # draw first-level (state/province) borders, where one locates the feature
    # a geometry/ file outlining a past extent, drawn as a dashed grey line (the Aral Sea's 1960 shore)
    former: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*\.geojson$")] | None = None


class AllowNested(Strict):
    """Accept that this feature and `id` nest despite sharing a type, e.g. a sub-range inside its range."""

    id: str
    reason: Annotated[str, Field(min_length=10)]


class Feature(Strict):
    id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]
    uid: Annotated[str, Field(pattern=r"^[A-Za-z0-9]{10}$")] | None = None
    name: CardText
    alt_names: list[CardText] = []
    type: FeatureType
    qualifier: CardText | None = None  # e.g. the season a climate map shows: "Monsoon, July"
    note: CardText | None = None  # why it matters, 1-3 sentences; shown in the PDF guide, required on active cards
    category: Category
    tier: Literal[1, 2, 3]
    style: Style
    geometry: list[Part]
    expect: Expect
    frame: FrameOptions = FrameOptions()
    allow_nested: list[AllowNested] = []
    trim_to_largest: bool = False  # after subtracting, keep only the largest polygon (drops cut-off scraps)
    retired: bool = False

    @property
    def family(self) -> Family:
        return FAMILY[self.type]

    @property
    def type_text(self) -> str:
        return f"{self.type}, {self.qualifier}" if self.qualifier else self.type


def load_features() -> list[Feature]:
    features = [Feature.model_validate(entry) for entry in YAML(typ="safe").load(FEATURES)]
    for key in ("id", "uid"):
        values = [getattr(f, key) for f in features if getattr(f, key) is not None]
        duplicates = {v for v in values if values.count(v) > 1}
        if duplicates:
            raise ValueError(f"duplicate {key}: {sorted(duplicates)}")
    return features


def active(features: list[Feature]) -> list[Feature]:
    return [f for f in features if not f.retired]
