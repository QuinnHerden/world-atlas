"""The Card DTO: what every source turns its entries into, and all that ordering, deckgen, the checks and the guide
read. See docs/adr/0005-card-sources-and-card-dto.md."""

import fnmatch
import json
import re
from collections.abc import Callable
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator
from shapely.geometry.base import BaseGeometry

from geofeat.model import MEDIA_INDEX, NOT_ONE_LINE, Note  # noqa: F401  Note re-exported for the sources
from geofeat.spec import RenderSpec

Kind = Literal["feature", "country", "capital", "city", "subnational", "territory", "dispute", "continent"]
# What render() draws besides the basemap: the geometry, the shapes drawn faintly under it, and a former extent.
Geometry = tuple[BaseGeometry, tuple[BaseGeometry, ...], BaseGeometry | None]
# Card text goes into markdown that ankc renders, unsanitised, to HTML in Anki. deckgen HTML-escapes it, which
# leaves markdown: an image or link (`![](path)` would package a local file, or fetch a URL on every phone), emphasis,
# code, or ankc's own `:::`, `[^` and `---` syntax. None has a place on a card, so reject them all.
_UNSAFE = re.compile(NOT_ONE_LINE + r"|[<>\[\]`\\*_#!]|:::|^-{3}")


def _plain(value: str) -> str:
    if _UNSAFE.search(value):
        raise ValueError(f"{value!r} contains characters not allowed on a card")
    return value


Text = Annotated[str, AfterValidator(_plain)]
Tag = Annotated[str, Field(pattern=r"^[A-Za-z0-9_:\-]+$")]


class Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)


class RenderRef(Frozen):
    """How to draw a card: its visual treatment, and a provider that resolves its geometry only when called, so
    building cards stays cheap and only the render step loads Natural Earth layers."""

    spec: RenderSpec
    geometry: Callable[[], Geometry]
    dot: Callable[[], tuple[float, float]] | None = None  # a city's point, resolved with the geometry into spec.dot
    # A political subject's region (geofeat.framing), resolved into spec.framing and the region's member points
    region: Callable[[], tuple[str, BaseGeometry, tuple[float, float, float, float] | None, float | None,
                                      tuple[float, float, float, float] | None]] | None = None

    def resolve(self) -> tuple[RenderSpec, BaseGeometry, tuple[BaseGeometry, ...], BaseGeometry | None]:
        """What render() takes: the spec, with its dot filled in, and the geometry."""
        spec = self.spec.model_copy(update={"dot": self.dot()}) if self.dot else self.spec
        return spec, *self.geometry()

    def resolve_framed(self) -> tuple[RenderSpec, BaseGeometry, tuple[BaseGeometry, ...], BaseGeometry | None,
                                      BaseGeometry | None]:
        """resolve(), plus the region a political subject is framed on, with spec.framing filled in."""
        spec, geometry, context, former = self.resolve()
        if self.region is None:
            return spec, geometry, context, former, None
        framing, region, locator, margin, hold = self.region()
        update = {"framing": framing, "locator": locator, "region_margin": margin, "hold": hold}
        return spec.model_copy(update=update), geometry, context, former, region


class Card(Frozen):
    uid: Annotated[str, Field(pattern=r"^[A-Za-z0-9]{10}$")]
    kind: Kind
    id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]  # unique within a kind, not across kinds
    prompt: Text  # the type text, shown in bold above the map
    answer_lines: tuple[Text, ...]  # plain text; deckgen escapes each line and joins them with <br>
    tags: tuple[Tag, ...]
    region: str | None = None
    tier: int
    anchor: str | None = None  # key of the card this one is placed after in the curriculum (P3)
    parents: tuple[str, ...] = ()  # keys of cards that must come first (P3; order.py derives feature edges itself)
    note: Note | None = None  # why it matters; the PDF guide and the card back
    host: str | None = None  # key of the country whose run this pocket sits in, after its capital (P3)
    orientation: bool = False  # in the orientation block that opens the deck (oceans, planetary winds, continents)
    render: RenderRef

    @model_validator(mode="after")
    def _block_tag(self) -> "Card":
        if [t for t in self.tags if t.startswith(("block::", "pass::"))] != [block_tag(self.block)]:
            raise ValueError(f"{self.kind}:{self.id}: needs exactly the tag {block_tag(self.block)}, and no pass:: tag")
        return self

    @property
    def block(self) -> "Block":
        return block_of(self.kind)

    @property
    def study_pass(self) -> "Pass":
        """The pass of the ring order the engine builds first (order.engine); the study blocks are cut from it."""
        return study_pass(self.kind, self.tier, self.orientation)

    @property
    def key(self) -> str:
        """Unique across all sources: what media.json, the render bookkeeping, the sheets and the guide key on."""
        return card_key(self.kind, self.id)


Pass = Literal["orientation", 1, 2]
PASS_ORDER: dict[Pass, int] = {"orientation": 0, 1: 1, 2: 2}  # sort by this; the labels themselves don't sort
ALWAYS_PASS_1: frozenset[Kind] = frozenset({"country", "capital", "subnational", "territory", "dispute"})


def study_pass(kind: Kind, tier: int, orientation: bool = False) -> Pass:
    """Which pass round the ring a card is introduced in. Orientation opens the deck. Pass 1 holds every country,
    capital, territory and dispute (tier-3 microstates included, beside their neighbours), the tier 1-2 features and
    the core cities (tier 2); pass 2 the tier-3 features and the secondary cities (tier 3)."""
    if orientation or kind == "continent":
        return "orientation"
    return 1 if kind in ALWAYS_PASS_1 or tier <= 2 else 2


# The study order's four blocks (ADR 0009): the continents, the political map (countries, territories and disputed
# areas), the physical features, then the capitals and cities.
Block = Literal["continents", "countries", "features", "cities"]
BLOCKS: tuple[Block, ...] = ("continents", "countries", "features", "cities")
_BLOCK_OF: dict[Kind, Block] = {"continent": "continents", "country": "countries", "subnational": "countries",
                                "territory": "countries", "dispute": "countries", "feature": "features", "capital": "cities", "city": "cities"}


def block_of(kind: Kind) -> Block:
    return _BLOCK_OF[kind]


def block_tag(block: Block) -> str:
    return f"block::{block}"


def card_key(kind: Kind, id: str) -> str:
    return f"{kind}:{id}"


def id_tag(kind: Kind, id: str) -> str:
    """Lets Anki find a card again once it is retired; see "Retired cards" in the README. Feature tags stay
    id_<id>, because ankc before 0.5 cut a footnote tag at its first colon and imported cards carry that form.
    Other kinds are prefixed, since two kinds may share an id (Georgia the country, Georgia the feature)."""
    return f"id_{id}" if kind == "feature" else f"id_{kind}_{id}"


def migrate_media(media: dict[str, str]) -> dict[str, str]:
    """media.json was keyed by bare feature id before cards had kinds; read such a key as feature:<id>."""
    return {key if ":" in key else card_key("feature", key): file for key, file in media.items()}


MEDIA_NAME = re.compile(r"[A-Za-z0-9_-]+\.png")  # a bare file name, so `deck/<name>` can't leave deck/


def load_media() -> dict[str, str]:
    """build/media.json: card key -> rendered PNG name, written by `make render`. Every name must be a bare PNG name:
    the sheets, the guide and the checks open deck/<name>."""
    media = migrate_media(json.loads(MEDIA_INDEX.read_text())) if MEDIA_INDEX.exists() else {}
    if bad := sorted(key for key, name in media.items() if not isinstance(name, str) or not MEDIA_NAME.fullmatch(name)):
        raise ValueError(f"{MEDIA_INDEX.name}: not a bare PNG file name for {bad}; delete it and run `make render`")
    return media


def match_keys(patterns: list[str], keys: list[str]) -> list[str]:
    """The keys each pattern names, in pattern order and each once: a key, a glob over keys, or a bare feature id.
    Raises on a pattern that matches nothing, so a typo isn't silently dropped."""
    out: dict[str, None] = {}
    for pattern in patterns:
        matched = sorted(fnmatch.filter(keys, pattern if ":" in pattern else card_key("feature", pattern)))
        if not matched:
            raise ValueError(f"no card matches {pattern!r}")
        out |= dict.fromkeys(matched)
    return list(out)
