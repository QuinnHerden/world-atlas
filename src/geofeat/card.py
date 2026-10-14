"""The Card DTO: what every source turns its entries into, and all that ordering, deckgen, the checks and the guide
read. See docs/adr/0005-card-sources-and-card-dto.md."""

import json
import re
from collections.abc import Callable
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from shapely.geometry.base import BaseGeometry

from geofeat.model import MEDIA_INDEX
from geofeat.spec import RenderSpec

Kind = Literal["feature", "country", "capital", "city", "territory", "dispute", "continent"]
# What render() draws besides the basemap: the geometry, the shapes drawn faintly under it, and a former extent.
Geometry = tuple[BaseGeometry, tuple[BaseGeometry, ...], BaseGeometry | None]
# Card text goes into markdown that ankc renders, unsanitised, to HTML in Anki. deckgen HTML-escapes it, which
# leaves markdown: an image or link (`![](path)` would package a local file, or fetch a URL on every phone), emphasis,
# code, or ankc's own `:::`, `[^` and `---` syntax. None has a place on a card, so reject them all.
_UNSAFE = re.compile(r"[\n<>\[\]`\\*_#!]|:::|^-{3}")


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
    note: str | None = None  # why it matters; PDF guide only
    render: RenderRef

    @property
    def key(self) -> str:
        """Unique across all sources: what media.json, the render bookkeeping, the sheets and the guide key on."""
        return card_key(self.kind, self.id)


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


def load_media() -> dict[str, str]:
    """build/media.json: card key -> rendered PNG name, written by `make render`."""
    return migrate_media(json.loads(MEDIA_INDEX.read_text())) if MEDIA_INDEX.exists() else {}
