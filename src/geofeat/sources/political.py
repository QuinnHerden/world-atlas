"""Political card sources: a country card and, unless `capital: null`, a capital card per state, and the territory and
dispute cards. The entries, their outlines and their placement are geofeat.polities'. See docs/adr/0005 and 0008."""

from shapely.errors import GEOSException
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from geofeat import framing
from geofeat.card import Card, Geometry, Kind, RenderRef, card_key, id_tag, block_of, block_tag
from geofeat.polities import (  # noqa: F401  re-exported for cities.py and the tests
    COUNTRIES, PATHS, PLACES, TERRITORIES, BBox, Capital, Subnational, Country, Dispute, FrameOverride, Id, Territory, Uid,
    OUTSIDE_SHARE, area_km2, compose, composition_errors,
    in_bbox, load_countries, load_political, outline, outside_country, place, read_entries, unique,
)
from geofeat.spec import RenderSpec

TERRITORY_TIER = 2  # territory and dispute entries carry no tier of their own; their pass is 1 by kind


def answer(name: str, alt_names: list[str]) -> str:
    return f"{name} ({', '.join(alt_names)})" if alt_names else name


def _overrides(frame: FrameOverride) -> dict:
    return {"inset": frame.inset, "inset_km": frame.inset_km, "inset_centre": frame.inset_centre, "ring": frame.ring}


def country_spec(frame: FrameOverride = FrameOverride()) -> RenderSpec:
    return RenderSpec(style="area", country="subject", **_overrides(frame))


def dot_spec() -> RenderSpec:
    """A city's dot over its country; RenderRef.dot fills in the point when the card is rendered."""
    return RenderSpec(style="area", country="context")


def outline_spec(frame: FrameOverride = FrameOverride()) -> RenderSpec:
    """Territories and disputes: the subject outline, dashed."""
    return RenderSpec(style="area", country="subject", outline="dashed", **_overrides(frame))


def tags(kind: Kind, id: str, category: str, region: int) -> tuple[str, ...]:
    """No tier tag: the tier is internal to the study order."""
    return (f"category::{category}", id_tag(kind, id), f"kind::{kind}", f"region::{region:02d}",
            block_tag(block_of(kind)))


def coordinates(point: Point) -> tuple[float, float]:
    return point.x, point.y


def host_key(host: str | None) -> str | None:
    """A pocket's host: its host country's card. P3 places the pocket in the host's run, after its capital."""
    return card_key("country", host) if host else None


def require_uid(owner: str, uid: str | None) -> str:
    if uid is None:
        raise ValueError(f"{owner}: no uid (run `make ids` and commit)")
    return uid


def country_cards(country: Country) -> list[Card]:
    def geometry() -> Geometry:
        return country.outline(), (), None

    region = f"{country.region:02d}"
    out = [Card(
        uid=require_uid(country.id, country.uids["country"]), kind="country", id=country.id, prompt="Country",
        answer_lines=(answer(country.name, country.alt_names),),
        tags=tags("country", country.id, "countries", country.region), region=region, tier=country.tier,
        host=host_key(country.host), note=country.note, render=RenderRef(spec=country_spec(country.frame), geometry=geometry,
                                                                     region=lambda: framing.region(country.id)),
    )]
    if c := country.carded_capital:
        out.append(Card(
            uid=require_uid(f"{country.id} capital", country.uids["capital"]), kind="capital", id=country.id, prompt="City",
            answer_lines=(answer(c.name, c.alt_names), f"Capital of {country.name}"),
            tags=tags("capital", country.id, "cities", country.region), region=region, tier=country.tier,
            parents=(out[0].key,), note=c.note,
            render=RenderRef(spec=dot_spec(), geometry=geometry, dot=lambda: coordinates(country.capital_point()),
                             region=framing.city_region(country.id)),
        ))
    return out


def subnational_cards(subnational: Subnational) -> list[Card]:
    """A constituent country or an exclave: its outline drawn solid, like a country's, since its border with the rest
    of its state is not in dispute."""
    return [Card(
        uid=require_uid(subnational.id, subnational.uid), kind="subnational", id=subnational.id, prompt=subnational.type,
        answer_lines=(answer(subnational.name, subnational.alt_names), subnational.status_line),
        tags=tags("subnational", subnational.id, "subnational", subnational.region),
        region=f"{subnational.region:02d}", tier=TERRITORY_TIER, host=host_key(subnational.host), note=subnational.note,
        render=RenderRef(spec=country_spec(subnational.frame), geometry=lambda: (subnational.outline(), (), None),
                         region=lambda: framing.region(subnational.id)),
    )]


def territory_cards(territory: Territory) -> list[Card]:
    return [Card(
        uid=require_uid(territory.id, territory.uid), kind="territory", id=territory.id, prompt="Territory",
        answer_lines=(answer(territory.name, territory.alt_names), territory.status_line),
        tags=tags("territory", territory.id, "territories", territory.region), region=f"{territory.region:02d}",
        tier=TERRITORY_TIER, host=host_key(territory.host), note=territory.note,
        render=RenderRef(spec=outline_spec(territory.frame), geometry=lambda: (territory.outline(), (), None),
                         region=lambda: framing.region(territory.id)),
    )]


def dispute_cards(dispute: Dispute, countries: dict[str, str]) -> list[Card]:
    """`countries` maps each country id to its name, for the parties line."""
    return [Card(
        uid=require_uid(dispute.id, dispute.uid), kind="dispute", id=dispute.id, prompt="Disputed territory",
        answer_lines=(answer(dispute.name, dispute.alt_names), dispute.parties_line(countries)),
        tags=tags("dispute", dispute.id, "territories", dispute.region), region=f"{dispute.region:02d}",
        tier=TERRITORY_TIER, host=host_key(dispute.host), note=dispute.note,
        render=RenderRef(spec=outline_spec(dispute.frame), geometry=lambda: (dispute.outline(), (), None),
                         region=lambda: framing.region(dispute.id)),
    )]


def cards() -> list[Card]:
    """Each country's card and its capital's, then the subnationals, territories and disputes, in file
    order."""
    countries, others = load_political()
    names = {c.id: c.name for c in countries}

    def other_cards(other: Subnational | Territory | Dispute) -> list[Card]:
        if isinstance(other, Dispute):
            return dispute_cards(other, names)
        return subnational_cards(other) if isinstance(other, Subnational) else territory_cards(other)

    return [card for country in countries for card in country_cards(country)] + [
        card for other in others for card in other_cards(other)]


def reference_errors(countries: list[Country], others: list[Subnational | Territory | Dispute]) -> list[str]:
    """Every country id a source names must exist: sovereigns, states and parties. Hosts come from the curriculum, which checks
    its own (curriculum_placements)."""
    names = {c.id: c.name for c in countries}
    errors = []
    for other in others:
        if isinstance(other, Territory) and other.sovereign not in names:
            errors.append(f"{other.id}: sovereign {other.sovereign!r} is not a country")
        if isinstance(other, Subnational) and other.state not in names:
            errors.append(f"{other.id}: state {other.state!r} is not a country")
        if isinstance(other, Dispute):
            try:
                other.party_names(names)
            except ValueError as exc:
                errors.append(str(exc))
    return errors


def check() -> tuple[list[str], dict[str, BaseGeometry]]:
    """Errors from resolving every outline and point, and the country outlines that resolved, for the city check.
    Each capital must lie inside its country, and every sovereign and party must be a country; hosts are the
    curriculum's."""
    try:
        countries, others = load_political()
    except ValueError as exc:
        return [str(exc)], {}
    errors, outlines = [], {}
    for country in countries:
        try:
            errors += composition_errors(country.id, country.geometry)
            outlines[country.id] = country.outline()
        except (ValueError, OSError, GEOSException) as exc:
            errors.append(str(exc))
            continue
        if country.capital and (country.tier == 3) != country.capital.retired:
            errors.append(f"{country.id} capital: a tier-3 state's capital, and only one, is retired (`retired: true` "
                          f"under `capital`); tier {country.tier}, retired: {country.capital.retired}")
        if country.capital:
            try:
                errors += outside_country(f"{country.id} capital", country.capital_point(), country.id, outlines[country.id])
            except (ValueError, OSError, GEOSException) as exc:
                errors.append(str(exc))
    errors += reference_errors(countries, others)
    states = {c.id: c for c in countries}
    for other in others:
        try:
            errors += composition_errors(other.id, other.geometry)
            shape = other.outline()
            if isinstance(other, Subnational) and other.state in states:
                state = compose(other.state, states[other.state].geometry)  # uncropped: an exclave lies outside `mainland`
                if area_km2(shape.difference(state)) > OUTSIDE_SHARE * area_km2(shape):
                    errors.append(f"{other.id}: outline is not inside its state {other.state!r}")
        except (ValueError, OSError, GEOSException) as exc:
            errors.append(str(exc))
    return errors, outlines
