import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator
from ruamel.yaml import YAML

from geofeat.decks import WORLD

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ROOT / "data/features.yaml"
LOCK = ROOT / "data/sources.lock"
GEOMETRY = ROOT / "geometry"
VENDOR = ROOT / "vendor"
DECK = ROOT / "deck"
BUILD = ROOT / "build"
MEDIA_INDEX = BUILD / "media.json"  # card key (kind:id, e.g. feature:nile) -> rendered PNG name
ROOT_DECK = WORLD.name

Category = Literal[
    "Continents",
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
# The type word shown on the card. Each covers 3+ active cards, except Isthmus, Valley, Cape and Climate belt (2 each)
# and Sea route and Ocean current (1 each); Pass, Corridor and Island are kept only for retired entries; Continent is
# the orientation block's 7 continent cards, composed in continents.py. See docs/adr/0001-type-vocabulary.md for the
# reason behind each.
FeatureType = Literal[
    "Ocean", "Sea", "Lake",
    "River", "Delta",
    "Strait", "Canal", "Sea route", "Pass", "Corridor",
    "Mountain range", "Plateau",
    "Plain", "Desert", "Valley",
    "Region",
    "Peninsula", "Isthmus", "Island", "Cape",
    "Ocean current", "Wind system", "Climate belt",
    "Continent",
]
# A coarse grouping of type words. The pair check treats one highlight covering another as a clash when both share
# a family, whatever their words; area features of a land family are clipped to land.
Family = Literal[
    "water body", "river", "sea passage", "land passage", "relief", "lowland", "region", "landmass", "island", "climate",
    "continent",
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
    "Continent": "continent",  # own family: a continent covers its peninsulas, and that is not a clash
}
LAND_FAMILIES: frozenset[Family] = frozenset({"land passage", "relief", "lowland", "region", "landmass"})
# How a hand-authored GeoJSON feature was made; every feature in geometry/ carries one, plus `refs`.
Method = Literal["ne-derived", "pd-dataset", "reference-coords", "hand-drawn"]
Style = Literal["area", "line", "point", "strait", "flow-current", "flow-wind", "band"]

# Control characters (\r included) and Unicode line breaks, which ankc reads as new lines; zero-width and direction
# characters, which make text display other than it reads; and `{{`, which ankc reads as cloze. Banned from all card
# text, here and in card.py.
NOT_ONE_LINE = r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202e\u2060-\u2069\ufeff]|\{\{"
_UNSAFE_TEXT = re.compile(NOT_ONE_LINE + r"|[<>]|:::|\[\^|^-{3}")
# A note goes, escaped, under the answer on the card back, so keep it as inert as card text:
# no HTML, links, images, code, math (`$`) or ankc syntax. Emphasis is allowed.
_UNSAFE_NOTE = re.compile(NOT_ONE_LINE + r"|[<>\[\]`\\$]|:::|^-{3}|^#")


def _card_text(value: str) -> str:
    """Card text is pasted into markdown that Anki renders as HTML, so keep it inert."""
    if _UNSAFE_TEXT.search(value):
        raise ValueError(f"{value!r} contains characters not allowed on a card")
    return value


CardText = Annotated[str, AfterValidator(_card_text)]


def _note(value: str) -> str:
    if _UNSAFE_NOTE.search(value):
        raise ValueError(f"{value!r} contains characters not allowed in a note")
    return value


Note = Annotated[str, AfterValidator(_note)]

# Research markers a note must not carry onto the card; the claim goes in the entry's `verify` list instead.
# "as of" alone is ordinary prose ("as of 2014 it hosted..."); an "(as of" or an "as of" a 2020s-or-later year is a
# marker. Trade-offs: genuine 2020s prose ("as of 2021 the city had") must be reworded, and "as of October 2026" passes.
NOTE_MARKER = re.compile(r"\(as of|as of 20[2-9]\d|verify|\[v\]|\[s\]|tbd", re.IGNORECASE)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _one_line(value: str) -> str:
    if re.search(NOT_ONE_LINE, value):
        raise ValueError(f"{value!r} must be one line of plain text")
    return value


OneLine = Annotated[str, Field(min_length=1), AfterValidator(_one_line)]


class Verify(Strict):
    """A claim in a note that must be rechecked before release, kept out of the note so a card never shows a
    research marker. Never displayed; `make verify-report` lists them and `make check-data RELEASE=1` fails on any."""

    claim: OneLine
    as_of: Annotated[str, Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])(-(0[1-9]|[12]\d|3[01]))?$")]  # quote it in YAML
    source: OneLine | None = None


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


# Why a data override of a computed default exists: a per-card `frame:`, a country's `mainland` crop, a region's
# `frame` pin or `frame_margin`. `make check-data` fails on an override without one (check.override_reason_errors).
OverrideReason = Annotated[str, Field(min_length=10), AfterValidator(_one_line)]


class FrameOptions(Strict):
    min_span_km: float | None = None
    centre: tuple[float, float] | None = None  # lon, lat; siblings sharing a centre and span share a frame
    context: list[str] = []  # ids of line features drawn faintly underneath, e.g. a delta's river
    admin1: bool = False  # draw first-level (state/province) borders, where one locates the feature
    # a geometry/ file outlining a past extent, drawn as a dashed grey line (the Aral Sea's 1960 shore)
    former: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*\.geojson$")] | None = None
    reason: OverrideReason | None = Field(None, exclude=True)  # out of the render spec's cache key


class AllowNested(Strict):
    """Accept that this feature and `id` nest despite sharing a type, e.g. a sub-range inside its range."""

    id: str
    reason: Annotated[str, Field(min_length=10)]


Reason = Annotated[str, Field(min_length=10), AfterValidator(_card_text)]


class Feature(Strict):
    id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]
    uid: Annotated[str, Field(pattern=r"^[A-Za-z0-9]{10}$")] | None = None
    name: CardText
    alt_names: list[CardText] = []
    type: FeatureType
    qualifier: CardText | None = None  # the season a climate map shows, after the type word: "Wind system, July"
    note: Note | None = None  # why it matters, 1-3 sentences; shown on the card back, required on active cards
    verify: list[Verify] = []
    category: Category
    tier: Literal[1, 2, 3]
    style: Style
    geometry: list[Part]
    expect: Expect
    frame: FrameOptions = FrameOptions()
    allow_nested: list[AllowNested] = []
    trim_to_largest: bool = False  # after subtracting, keep only the largest polygon (drops cut-off scraps)
    retired: bool = False
    # A curriculum override, for where regions.py's derivation gets it wrong; it needs a reason.
    region: Annotated[int, Field(ge=1, le=21)] | None = None  # ring region, see docs/world-atlas-plan.md
    region_reason: Reason | None = None

    @model_validator(mode="after")
    def _override_has_a_reason(self) -> "Feature":
        if (self.region is None) != (self.region_reason is None):
            raise ValueError("`region` and `region_reason` go together")
        return self

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


ORIENTATION_TYPES = frozenset({"Ocean", "Continent"})
PLANETARY_WINDS = frozenset({"trade-winds", "westerlies"})


def orientation(feature: Feature) -> bool:
    """The oceans, the planetary wind belts and the continents open the deck, before the ring."""
    return feature.type in ORIENTATION_TYPES or feature.id in PLANETARY_WINDS
