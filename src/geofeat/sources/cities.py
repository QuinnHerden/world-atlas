"""data/cities.yaml: one city card per entry, a dot inside its country, which it names on the back."""

from typing import Literal

from shapely.errors import GEOSException
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from geofeat.card import PASS_ORDER, Card, Geometry, Note, RenderRef, Text, card_key, study_pass
from geofeat.model import ROOT, Strict, active, load_features
from geofeat.resolve import features_by_id, resolve
from geofeat.sources.features import orientation
from geofeat.sources.political import (
    BBox, Country, Id, Uid, answer, coordinates, dot_spec, load_countries, outside_country, place, read_entries, require_uid, tags, unique,
)

PATH = ROOT / "data/cities.yaml"
# Pass 1 holds the core cities, pass 2 the secondary ones, with the tier 1-2 and tier 3 features respectively.
TIER = {"core": 2, "secondary": 3}


class City(Strict):
    id: Id
    name: Text
    alt_names: list[Text] = []
    uid: Uid | None = None
    country: Id  # a country id in countries.yaml
    tier: Literal["core", "secondary"]
    ne_id: int  # populated_places
    expect: BBox  # a box round the point
    anchor: Id | None = None  # an active feature it comes right after: Alexandria after the Nile Delta (P3)
    note: Note | None = None

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
            tags=tags("city", self.id, TIER[self.tier], "cities", country.region), region=f"{country.region:02d}",
            tier=TIER[self.tier], anchor=card_key("feature", self.anchor) if self.anchor else None, parents=parents,
            note=self.note, render=RenderRef(spec=dot_spec(), geometry=geometry, dot=lambda: coordinates(self.point())),
        )]


def load_cities() -> list[City]:
    cities = [City.model_validate(e) for e in read_entries(PATH)]
    unique(cities, "city")
    return cities


def _countries() -> dict[str, Country]:
    return {c.id: c for c in load_countries()}


def unknown_countries(cities: list[City], countries: set[str]) -> list[str]:
    return [f"{c.id}: country {c.country!r} is not in countries.yaml" for c in cities if c.country not in countries]


def feature_region(feature_id: str) -> int:
    """The ring region a feature is assigned (regions.py: derived, or its `region:` override)."""
    from geofeat import regions  # regions -> countries_ne -> sources.political: importing at the top is a cycle

    feature = features_by_id()[feature_id]
    return regions.derive(feature, resolve(feature), regions.region_outlines()).region


def anchor_errors(cities: list[City], countries: dict[str, Country]) -> list[str]:
    """A city comes right after its anchor, so the anchor must be an active feature introduced no later than the
    city's own pass, not in orientation, which the ring doesn't revisit, and in the region of the city's country."""
    passes = {f.id: study_pass("feature", f.tier, orientation(f)) for f in active(load_features())}
    errors = []
    for city in (c for c in cities if c.anchor):
        own = study_pass("city", TIER[city.tier])
        if city.anchor not in passes:
            errors.append(f"{city.id}: anchor {city.anchor!r} is not an active feature")
        elif passes[city.anchor] == "orientation" or PASS_ORDER[passes[city.anchor]] > PASS_ORDER[own]:
            errors.append(f"{city.id}: anchor {city.anchor!r} is in pass {passes[city.anchor]}, the city in pass {own}")
        elif city.country in countries and (region := feature_region(city.anchor)) != countries[city.country].region:
            errors.append(f"{city.id}: anchor {city.anchor!r} is in region {region}, "
                          f"{city.country} in region {countries[city.country].region}")
    return errors


def cards() -> list[Card]:
    cities = load_cities()
    if not cities:
        return []
    countries = _countries()
    if errors := unknown_countries(cities, set(countries)):
        raise ValueError("; ".join(errors))
    return [card for city in cities for card in city.cards(countries[city.country])]


def check(outlines: dict[str, BaseGeometry]) -> list[str]:
    """Each city's country and anchor feature exist, the anchor is in the country's region, the city isn't its capital, and its point resolves and lies inside that country's outline. `outlines` are the
    country outlines political.check() resolved; a country missing there already has an error of its own."""
    try:
        cities = load_cities()
        countries = _countries() if cities else {}
    except ValueError as exc:
        return [str(exc)]
    errors = unknown_countries(cities, set(countries))
    errors += anchor_errors(cities, countries)
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
