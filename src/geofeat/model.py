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
    "Oceans & Seas",
    "Straits & Chokepoints",
    "Mountain Ranges",
    "Passes & Corridors",
    "Rivers",
    "Deserts, Plateaus & Plains",
    "Peninsulas & Islands",
    "Lakes",
    "Regions, Rifts & Deltas",
    "Climate Systems",
]
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
    """One piece of a feature's geometry: rows from a Natural Earth layer, or a hand-authored file."""

    layer: str | None = None
    select: dict[str, str | int] | None = None
    rows: int = 1
    file: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*\.geojson$")] | None = None

    @model_validator(mode="after")
    def _one_source(self) -> "Part":
        if (self.file is None) == (self.layer is None or self.select is None):
            raise ValueError("a part needs either `file`, or both `layer` and `select`")
        return self


class Expect(Strict):
    # lon_min, lat_min, lon_max, lat_max; lon_min > lon_max means the box crosses 180°
    bbox: tuple[float, float, float, float]
    length_km: tuple[float, float] | None = None
    area_km2: tuple[float, float] | None = None


class FrameOptions(Strict):
    min_span_km: float | None = None


class Feature(Strict):
    id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]
    uid: Annotated[str, Field(pattern=r"^[A-Za-z0-9]{10}$")] | None = None
    name: CardText
    alt_names: list[CardText] = []
    type: CardText
    category: Category
    tier: Literal[1, 2, 3]
    style: Style
    geometry: list[Part]
    expect: Expect
    frame: FrameOptions = FrameOptions()
    retired: bool = False

    @property
    def subdeck(self) -> str:
        return f"{ROOT_DECK}::{self.category}::Tier {self.tier}"


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
