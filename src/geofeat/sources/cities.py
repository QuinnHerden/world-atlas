"""data/cities.yaml: one city card per entry, a dot inside its country, which it names on the back."""

from typing import Literal

from shapely.errors import GEOSException
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from geofeat.card import Card, Geometry, RenderRef, card_key
from geofeat.model import ROOT, CardText, Strict
from geofeat.sources.political import (
    BBox, Country, Id, Line, Uid, read_entries, require_uid, answer, dot_spec, load_countries, outside_country, place, tags, unique,
)

PATH = ROOT / "data/cities.yaml"
# Pass 1 holds the core cities, pass 2 the secondary ones, with the tier 1-2 and tier 3 features respectively.
TIER = {"core": 2, "secondary": 3}


class City(Strict):
    id: Id
    name: Line
    alt_names: list[Line] = []
    uid: Uid | None = None
    country: Id  # a country id in countries.yaml
    tier: Literal["core", "secondary"]
    ne_id: int  # populated_places
    expect: BBox  # a box round the point
    note: CardText | None = None

    def point(self) -> Point:
        return place(self.id, self.ne_id, None, self.expect)

    def cards(self, country: Country) -> list[Card]:
        if country.id != self.country:
            raise ValueError(f"{self.id}: is in {self.country!r}, not {country.id!r}")

        def geometry() -> Geometry:
            return country.outline(), (), None

        parents = (card_key("country", country.id), *((card_key("capital", country.id),) if country.capital else ()))
        return [Card(
            uid=require_uid(self.id, self.uid), kind="city", id=self.id, prompt="City",
            answer_lines=(answer(self.name, self.alt_names), country.name),
            tags=tags("city", self.id, TIER[self.tier], "cities"), region=f"{country.region:02d}",
            tier=TIER[self.tier], parents=parents, note=self.note,
            render=RenderRef(spec=dot_spec(self.point()), geometry=geometry),
        )]


def load_cities() -> list[City]:
    cities = [City.model_validate(e) for e in read_entries(PATH)]
    unique(cities, "city")
    return cities


def _countries() -> dict[str, Country]:
    return {c.id: c for c in load_countries()}


def unknown_countries(cities: list[City], countries: set[str]) -> list[str]:
    return [f"{c.id}: country {c.country!r} is not in countries.yaml" for c in cities if c.country not in countries]


def cards() -> list[Card]:
    cities = load_cities()
    if not cities:
        return []
    countries = _countries()
    if errors := unknown_countries(cities, set(countries)):
        raise ValueError("; ".join(errors))
    return [card for city in cities for card in city.cards(countries[city.country])]


def check(outlines: dict[str, BaseGeometry]) -> list[str]:
    """Each city's country exists, the city isn't its capital, and its point resolves and lies inside that country's outline. `outlines` are the
    country outlines political.check() resolved; a country missing there already has an error of its own."""
    try:
        cities = load_cities()
        countries = _countries() if cities else {}
    except ValueError as exc:
        return [str(exc)]
    errors = unknown_countries(cities, set(countries))
    errors += [f"{c.id}: is {c.country}'s capital, which has a capital card" for c in cities
               if c.country in countries and (cap := countries[c.country].capital) and cap.ne_id == c.ne_id]
    for city in cities:
        try:
            point = city.point()
        except (ValueError, OSError, GEOSException) as exc:
            errors.append(str(exc))
            continue
        if city.country in outlines:
            errors += outside_country(city.id, point, city.country, outlines[city.country])
    return errors
