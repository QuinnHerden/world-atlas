"""Political card sources: a country card and, unless `capital: null`, a capital card per state, and the territory and
dispute cards. The entries, their outlines and their placement are geofeat.polities'. See docs/adr/0005 and 0008."""

from shapely.errors import GEOSException
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from geofeat import framing
from geofeat.card import Card, Geometry, Kind, RenderRef, card_key, id_tag, pass_tag, study_pass
from geofeat.polities import (  # noqa: F401  re-exported for cities.py and the tests
    COUNTRIES, PATHS, PLACES, TERRITORIES, BBox, Capital, Country, Dispute, Id, Territory, Uid, composition_errors,
    in_bbox, load_countries, load_political, outline, outside_country, place, read_entries, unique,
)
from geofeat.spec import RenderSpec

TERRITORY_TIER = 2  # territory and dispute entries carry no tier of their own; their pass is 1 by kind


def answer(name: str, alt_names: list[str]) -> str:
    return f"{name} ({', '.join(alt_names)})" if alt_names else name


def country_spec() -> RenderSpec:
    return RenderSpec(style="area", country="subject")


def dot_spec() -> RenderSpec:
    """A city's dot over its country; RenderRef.dot fills in the point when the card is rendered."""
    return RenderSpec(style="area", country="context")


def outline_spec() -> RenderSpec:
    """Territories and disputes: the subject outline, dashed."""
    return RenderSpec(style="area", country="subject", outline="dashed")


def tags(kind: Kind, id: str, tier: int, category: str, region: int) -> tuple[str, ...]:
    return (f"tier::{tier}", f"category::{category}", id_tag(kind, id), f"kind::{kind}", f"region::{region:02d}",
            pass_tag(study_pass(kind, tier)))


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
        tags=tags("country", country.id, country.tier, "countries", country.region), region=region, tier=country.tier,
        host=host_key(country.host), note=country.note, render=RenderRef(spec=country_spec(), geometry=geometry,
                                                                     region=lambda: framing.region(country.id)),
    )]
    if c := country.capital:
        out.append(Card(
            uid=require_uid(f"{country.id} capital", country.uids["capital"]), kind="capital", id=country.id, prompt="City",
            answer_lines=(answer(c.name, c.alt_names), f"Capital of {country.name}"),
            tags=tags("capital", country.id, country.tier, "cities", country.region), region=region, tier=country.tier,
            parents=(out[0].key,), note=c.note,
            render=RenderRef(spec=dot_spec(), geometry=geometry, dot=lambda: coordinates(country.capital_point()),
                             region=framing.city_region(country.id)),
        ))
    return out


def territory_cards(territory: Territory) -> list[Card]:
    return [Card(
        uid=require_uid(territory.id, territory.uid), kind="territory", id=territory.id, prompt="Territory",
        answer_lines=(answer(territory.name, territory.alt_names), territory.status_line),
        tags=tags("territory", territory.id, TERRITORY_TIER, "territories", territory.region), region=f"{territory.region:02d}",
        tier=TERRITORY_TIER, host=host_key(territory.host), note=territory.note,
        render=RenderRef(spec=outline_spec(), geometry=lambda: (territory.outline(), (), None),
                         region=lambda: framing.region(territory.id)),
    )]


def dispute_cards(dispute: Dispute, countries: dict[str, str]) -> list[Card]:
    """`countries` maps each country id to its name, for the parties line."""
    return [Card(
        uid=require_uid(dispute.id, dispute.uid), kind="dispute", id=dispute.id, prompt="Disputed territory",
        answer_lines=(answer(dispute.name, dispute.alt_names), dispute.parties_line(countries)),
        tags=tags("dispute", dispute.id, TERRITORY_TIER, "territories", dispute.region), region=f"{dispute.region:02d}",
        tier=TERRITORY_TIER, host=host_key(dispute.host), note=dispute.note,
        render=RenderRef(spec=outline_spec(), geometry=lambda: (dispute.outline(), (), None),
                         region=lambda: framing.region(dispute.id)),
    )]


def cards() -> list[Card]:
    """Each country's card and its capital's, then the territories and disputes, in file order."""
    countries, others = load_political()
    names = {c.id: c.name for c in countries}
    return [card for country in countries for card in country_cards(country)] + [
        card for other in others
        for card in (dispute_cards(other, names) if isinstance(other, Dispute) else territory_cards(other))]


def reference_errors(countries: list[Country], others: list[Territory | Dispute]) -> list[str]:
    """Every country id a source names must exist: sovereigns and parties. Hosts come from the curriculum, which checks
    its own (curriculum_placements)."""
    names = {c.id: c.name for c in countries}
    errors = []
    for other in others:
        if isinstance(other, Territory) and other.sovereign not in names:
            errors.append(f"{other.id}: sovereign {other.sovereign!r} is not a country")
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
        if country.capital:
            try:
                errors += outside_country(f"{country.id} capital", country.capital_point(), country.id, outlines[country.id])
            except (ValueError, OSError, GEOSException) as exc:
                errors.append(str(exc))
    errors += reference_errors(countries, others)
    for other in others:
        try:
            errors += composition_errors(other.id, other.geometry)
            other.outline()
        except (ValueError, OSError, GEOSException) as exc:
            errors.append(str(exc))
    return errors, outlines
