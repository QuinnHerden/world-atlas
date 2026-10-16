"""data/subdivisions.yaml: a country's first-level subdivisions (Italy's regions, the US states and DC, Brazil's states
and Distrito Federal, Canada's provinces and territories), one card each, in the country's companion deck
(geofeat.decks). The file lists each country's subdivisions in study order: a neighbour walk (geofeat.order.companions),
checked by `make check-data`."""

from functools import cache
from typing import Annotated, Literal

from pydantic import Field, model_validator
from shapely import unary_union
from shapely.errors import GEOSException
from shapely.geometry.base import BaseGeometry

from geofeat.card import Card, RenderRef, Text, block_of, block_tag, id_tag
from geofeat.decks import BY_COUNTRY, COMPANIONS, DeckInfo
from geofeat.model import ROOT, Note, Part, Strict, Verify
from geofeat.resolve import area_km2
from geofeat.polities import BBox, Id, Uid, composition_errors, outline, read_entries, unique
from geofeat.sources.political import answer, require_uid
from geofeat.spec import RenderSpec

PATH = ROOT / "data/subdivisions.yaml"
SUBDIVISION_TIER = 1  # not tagged: a companion deck has no tiers
TILE_KM2 = 1.0


class Subdivision(Strict):
    id: Annotated[str, Field(pattern=r"^[a-z]{2}-[a-z0-9][a-z0-9-]*$")]  # the deck's prefix, then a slug: it-sicilia
    uid: Uid | None = None
    name: Text
    alt_names: list[Text] = []
    country: Id  # a countries.yaml id with a companion deck
    type: Literal["Region", "State", "Federal district", "Province", "Territory"]  # the prompt
    geometry: Annotated[list[Part], Field(min_length=1)]
    expect: BBox
    note: Note | None = None
    verify: list[Verify] = []
    retired: bool = False

    @model_validator(mode="after")
    def _in_a_deck(self) -> "Subdivision":
        deck = BY_COUNTRY.get(self.country)
        if deck is None:
            raise ValueError(f"{self.id}: no companion deck for {self.country!r}")
        if not self.id.startswith(f"{deck.prefix}-"):
            raise ValueError(f"{self.id}: a {deck.name} id starts with {deck.prefix}-")
        return self

    @property
    def deck(self) -> DeckInfo:
        return BY_COUNTRY[self.country]

    def outline(self) -> BaseGeometry:
        return outline(self.id, self.geometry, self.expect)


@cache
def load_subdivisions() -> tuple[Subdivision, ...]:
    """Every entry, retired ones included, in file order."""
    entries = [Subdivision.model_validate(e) for e in read_entries(PATH)]
    unique(entries, "subdivision")
    return tuple(entries)


def active() -> list[Subdivision]:
    return [s for s in load_subdivisions() if not s.retired]


def of_country(country: str) -> list[Subdivision]:
    """A country's active subdivisions, in study order."""
    return [s for s in active() if s.country == country]


@cache
def outlines(country: str) -> dict[str, BaseGeometry]:
    return {s.id: s.outline() for s in of_country(country)}


def tags(s: Subdivision) -> tuple[str, ...]:
    return (id_tag("subdivision", s.id), "kind::subdivision", block_tag(block_of("subdivision")), f"country::{s.country}")


def spec(s: Subdivision) -> RenderSpec:
    return RenderSpec(style="area", country="subject", framing="country", country_frame=s.country)


def card(s: Subdivision) -> Card:
    def geometry():
        siblings = outlines(s.country)
        return siblings[s.id], tuple(g for i, g in siblings.items() if i != s.id), None

    return Card(
        uid=require_uid(s.id, s.uid), kind="subdivision", id=s.id, prompt=s.type,
        answer_lines=(answer(s.name, s.alt_names),), tags=tags(s), tier=SUBDIVISION_TIER, note=s.note,
        deck=s.deck.name, render=RenderRef(spec=spec(s), geometry=geometry),
    )


def cards() -> list[Card]:
    """One card per active subdivision, in file order."""
    return [card(s) for s in active()]


def tiling_errors(country: str, parts: dict[str, BaseGeometry], whole: BaseGeometry) -> list[str]:
    """A country's subdivisions must tile its full outline: no two overlap, and together they cover it, each within
    TILE_KM2 (Natural Earth's admin-0 and admin-1 edges differ by slivers)."""
    errors = []
    ids = sorted(parts)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if parts[a].intersects(parts[b]) and (km2 := area_km2(parts[a].intersection(parts[b]))) > TILE_KM2:
                errors.append(f"{a} and {b} overlap by {km2:,.1f} km²")
    union = unary_union(list(parts.values()))
    if (missed := area_km2(whole.difference(union))) > TILE_KM2:
        errors.append(f"{country}: its subdivisions leave {missed:,.1f} km² of it uncovered")
    if (spill := area_km2(union.difference(whole))) > TILE_KM2:
        errors.append(f"{country}: its subdivisions spill {spill:,.1f} km² outside it")
    return errors


def check(countries: set[str]) -> list[str]:
    """Each country must have a countries.yaml entry and a companion deck's count of subdivisions, each outline must
    resolve inside its `expect` box, and together they must tile the country's full outline."""
    from geofeat.countries_ne import outline as full_outline

    try:
        entries = load_subdivisions()
    except ValueError as exc:
        return [str(exc)]
    errors = [f"{s.id}: country {s.country!r} is not in countries.yaml" for s in entries if s.country not in countries]
    for deck in COMPANIONS:
        if (n := len(of_country(deck.country))) != deck.cards:
            errors.append(f"{deck.name}: {n} active subdivisions, expected {deck.cards}")
    for country in sorted({s.country for s in active()} & countries):
        parts = {}
        for s in of_country(country):
            try:
                errors += composition_errors(s.id, s.geometry)
                parts[s.id] = s.outline()
            except (ValueError, OSError, GEOSException) as exc:
                errors.append(str(exc))
        if len(parts) == len(of_country(country)):
            errors += tiling_errors(country, parts, full_outline(country))
    return errors
