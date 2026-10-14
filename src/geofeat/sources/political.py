"""Political card sources: data/countries.yaml (a country card and, unless `capital: null`, a capital card per state)
and data/territories.yaml (territory and dispute cards, told apart by `kind`). See docs/adr/0005 and 0008."""

import re
import unicodedata
from pathlib import Path
from typing import Annotated, Literal

import shapely
from pydantic import AfterValidator, Field, model_validator
from ruamel.yaml import YAML, YAMLError
from shapely import unary_union
from shapely.errors import GEOSException
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from geofeat.card import Card, Geometry, RenderRef, Text, id_tag
from geofeat.model import ROOT, CardText, Part, Strict
from geofeat.resolve import area_km2, custom, features_by_id, layer, resolve
from geofeat.spec import RenderSpec

COUNTRIES = ROOT / "data/countries.yaml"
TERRITORIES = ROOT / "data/territories.yaml"
PATHS = (COUNTRIES, TERRITORIES)
PLACES = "10m_populated_places"
# How exactly an outline must compose, as in docs/research/ne-political-layers.md (c): a subtracted row lies inside
# the base, an added row lies outside it.
INSIDE_SHARE = 0.999
OUTSIDE_SHARE = 0.001
TERRITORY_TIER = 2  # pass 1; territory and dispute entries carry no tier of their own

Id = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]
Uid = Annotated[str, Field(pattern=r"^[A-Za-z0-9]{10}$")]
Region = Annotated[int, Field(ge=1, le=21)]  # ring order; the slugs live in data/curriculum.yaml (P3)
GeojsonFile = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*\.geojson$")]
Lon = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
Lat = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
# lon_min, lat_min, lon_max, lat_max; lon_min > lon_max means the box crosses 180°
BBox = tuple[Lon, Lat, Lon, Lat]
# card.Text bans \n but not \r or Unicode line breaks, which ankc reads as new lines; and `{{` reads as cloze. Remove
# once card.py bans them itself.
_NOT_ONE_LINE = re.compile(r"[\x00-\x1f\x7f\u0085\u2028\u2029]|\{\{")


def _one_line(value: str) -> str:
    if _NOT_ONE_LINE.search(value):
        raise ValueError(f"{value!r} contains a control character, line break or `{{{{`")
    return value


Line = Annotated[Text, AfterValidator(_one_line)]


def in_bbox(geometry: BaseGeometry, bbox: BBox) -> bool:
    lon_min, lat_min, lon_max, lat_max = bbox
    coords = shapely.get_coordinates(geometry)
    lons, lats = coords[:, 0], coords[:, 1]
    in_lon = (lons >= lon_min) & (lons <= lon_max) if lon_min <= lon_max else (lons >= lon_min) | (lons <= lon_max)
    return bool((in_lon & (lats >= lat_min) & (lats <= lat_max)).all())


def answer(name: str, alt_names: list[str]) -> str:
    return f"{name} ({', '.join(alt_names)})" if alt_names else name


def _select(owner: str, part: Part) -> BaseGeometry:
    """resolve.py's row selection, which takes a Feature; keep the two in step."""
    if not part.select:
        raise ValueError(f"{owner}: {part.layer} has an empty select")
    gdf = layer(part.layer)
    if unknown := {k.lower() for k in part.select} - set(gdf.columns):
        raise ValueError(f"{owner}: {part.layer} has no column(s) {sorted(unknown)}")
    mask = True
    for key, value in part.select.items():
        mask = mask & (gdf[key.lower()] == value)
    matched = gdf[mask]
    if len(matched) != part.rows:
        raise ValueError(f"{owner}: {part.layer} {part.select} matched {len(matched)} rows, expected {part.rows}")
    return unary_union(matched.geometry.values)


def part_geometry(owner: str, part: Part) -> BaseGeometry:
    """One part, by the same grammar as features.yaml: Natural Earth rows, a geometry/ file, or a feature's shape."""
    if part.file:
        return custom(part.file)
    if part.feature:
        if part.feature not in features_by_id():
            raise ValueError(f"{owner}: references unknown feature {part.feature!r}")
        return resolve(features_by_id()[part.feature])
    return _select(owner, part)


def outline(owner: str, parts: list[Part], expect: BBox, mainland: BBox | None = None) -> BaseGeometry:
    """The union of the added parts less the subtracted ones, cut to the `mainland` box when there is one."""
    keep = unary_union([part_geometry(owner, p) for p in parts if not p.subtract])
    if cut := [part_geometry(owner, p) for p in parts if p.subtract]:
        keep = shapely.make_valid(keep.difference(unary_union(cut)))
    if mainland:
        kept = [p for p in shapely.get_parts(keep) if in_bbox(p, mainland)]
        if not kept:
            raise ValueError(f"{owner}: no part of the outline lies inside mainland {mainland}")
        keep = unary_union(kept)
    if keep.is_empty or keep.geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError(f"{owner}: outline is {'empty' if keep.is_empty else keep.geom_type}, not a polygon")
    if not in_bbox(keep, expect):
        raise ValueError(f"{owner}: outline {tuple(round(b, 2) for b in keep.bounds)} falls outside expected bbox {expect}")
    return keep


def composition_errors(owner: str, parts: list[Part]) -> list[str]:
    """A composed outline must be exact: every added part after the first lies outside the base (the first part),
    every subtracted part inside it, so no sliver or overlap is hidden in the result."""
    if parts[0].subtract:
        return [f"{owner}: the first part is the base and can't be subtracted"]
    base = part_geometry(owner, parts[0])
    errors = []
    for part in parts[1:]:
        geometry = part_geometry(owner, part)
        if (area := area_km2(geometry)) == 0:
            errors.append(f"{owner}: part {part.select or part.file or part.feature} has no area")
            continue
        share = area_km2(geometry.intersection(base)) / area
        if part.subtract and share < INSIDE_SHARE:
            errors.append(f"{owner}: subtracted part {part.select or part.file or part.feature} is only {share:.2%} inside the base")
        elif not part.subtract and share > OUTSIDE_SHARE:
            errors.append(f"{owner}: added part {part.select or part.file or part.feature} overlaps the base by {share:.2%}")
    return errors


def place(owner: str, ne_id: int | None, file: str | None, expect: BBox) -> Point:
    """A city's point: a populated_places row, or a hand-placed point in geometry/ (Yaren)."""
    if file:
        geometry = custom(file)
    else:
        rows = layer(PLACES)
        matched = rows[rows["ne_id"] == ne_id]
        if len(matched) != 1:
            raise ValueError(f"{owner}: {PLACES} ne_id {ne_id} matched {len(matched)} rows, expected 1")
        geometry = matched.geometry.iloc[0]
    if geometry.geom_type != "Point":
        raise ValueError(f"{owner}: {geometry.geom_type} is not a point")
    if not in_bbox(geometry, expect):
        raise ValueError(f"{owner}: point ({geometry.x:.3f}, {geometry.y:.3f}) falls outside expected bbox {expect}")
    return geometry


def country_spec() -> RenderSpec:
    return RenderSpec(style="area", country="subject")


def dot_spec(point: Point) -> RenderSpec:
    return RenderSpec(style="area", country="context", dot=(point.x, point.y))


def outline_spec() -> RenderSpec:
    """Territories and disputes: the subject outline. `outline: dashed` is theirs once P4 draws it; solid until then."""
    return RenderSpec(style="area", country="subject")


def tags(kind: str, id: str, tier: int, category: str) -> tuple[str, ...]:
    return (f"tier::{tier}", f"category::{category}", id_tag(kind, id), f"kind::{kind}")


def require_uid(owner: str, uid: str | None) -> str:
    if uid is None:
        raise ValueError(f"{owner}: no uid (run `make ids` and commit)")
    return uid


class Capital(Strict):
    name: Line
    alt_names: list[Line] = []
    ne_id: int | None = None
    file: GeojsonFile | None = None
    expect: BBox
    note: CardText | None = None

    @model_validator(mode="after")
    def _one_source(self) -> "Capital":
        if (self.ne_id is None) == (self.file is None):
            raise ValueError("a capital needs exactly one of `ne_id` or `file`")
        return self


class Country(Strict):
    id: Id
    name: Line
    alt_names: list[Line] = []
    uids: dict[Literal["country", "capital"], Uid | None]
    region: Region
    tier: Literal[1, 2, 3]  # microstates and small island states are 3
    note: CardText | None = None
    geometry: Annotated[list[Part], Field(min_length=1)]
    mainland: BBox | None = None  # keep only the outline's parts inside this box (drops overseas parts)
    expect: BBox
    capital: Capital | None  # null: no capital card (same-name microstates, Palestine)

    @model_validator(mode="after")
    def _uid_slots(self) -> "Country":
        needed = {"country", "capital"} if self.capital else {"country"}
        if set(self.uids) != needed:
            raise ValueError(f"{self.id}: needs uids for exactly {sorted(needed)}"
                             + (" (capital is null)" if not self.capital else "; add `capital: null` under uids and run `make ids`"))
        return self

    def outline(self) -> BaseGeometry:
        return outline(self.id, self.geometry, self.expect, self.mainland)

    def capital_point(self) -> Point:
        c = self.capital
        return place(f"{self.id} capital", c.ne_id, c.file, c.expect)

    def cards(self) -> list[Card]:
        def geometry() -> Geometry:
            return self.outline(), (), None

        region = f"{self.region:02d}"
        out = [Card(
            uid=require_uid(self.id, self.uids["country"]), kind="country", id=self.id, prompt="Country",
            answer_lines=(answer(self.name, self.alt_names),), tags=tags("country", self.id, self.tier, "countries"),
            region=region, tier=self.tier, note=self.note,
            render=RenderRef(spec=country_spec(), geometry=geometry),
        )]
        if c := self.capital:
            out.append(Card(
                uid=require_uid(f"{self.id} capital", self.uids["capital"]), kind="capital", id=self.id, prompt="City",
                answer_lines=(answer(c.name, c.alt_names), f"Capital of {self.name}"),
                tags=tags("capital", self.id, self.tier, "cities"), region=region, tier=self.tier,
                parents=(out[0].key,), note=c.note,
                render=RenderRef(spec=dot_spec(self.capital_point()), geometry=geometry),
            ))
        return out


class Territory(Strict):
    kind: Literal["territory"]
    id: Id
    name: Line
    alt_names: list[Line] = []
    uid: Uid | None = None
    sovereign: Id  # a country id
    status_line: Line  # back line 2, e.g. "Overseas department of France"
    region: Region
    geometry: Annotated[list[Part], Field(min_length=1)]
    expect: BBox
    note: CardText | None = None

    def outline(self) -> BaseGeometry:
        return outline(self.id, self.geometry, self.expect)

    def cards(self) -> list[Card]:
        return [Card(
            uid=require_uid(self.id, self.uid), kind="territory", id=self.id, prompt="Territory",
            answer_lines=(answer(self.name, self.alt_names), self.status_line),
            tags=tags("territory", self.id, TERRITORY_TIER, "territories"), region=f"{self.region:02d}",
            tier=TERRITORY_TIER, note=self.note,
            render=RenderRef(spec=outline_spec(), geometry=lambda: (self.outline(), (), None)),
        )]


def _alphabetical(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().casefold()


class Dispute(Strict):
    kind: Literal["dispute"]
    id: Id
    name: Line
    alt_names: list[Line] = []
    uid: Uid | None = None
    parties: Annotated[list[Line], Field(min_length=2)]
    region: Region
    geometry: Annotated[list[Part], Field(min_length=1)]  # disputed-areas rows
    expect: BBox
    note: CardText | None = None

    @model_validator(mode="after")
    def _distinct_parties(self) -> "Dispute":
        if len({_alphabetical(p) for p in self.parties}) != len(self.parties):
            raise ValueError(f"{self.id}: parties repeat")
        return self

    @property
    def parties_line(self) -> str:
        return f"Disputed: {', '.join(sorted(self.parties, key=_alphabetical))}"

    def outline(self) -> BaseGeometry:
        return outline(self.id, self.geometry, self.expect)

    def cards(self) -> list[Card]:
        return [Card(
            uid=require_uid(self.id, self.uid), kind="dispute", id=self.id, prompt="Disputed territory",
            answer_lines=(answer(self.name, self.alt_names), self.parties_line),
            tags=tags("dispute", self.id, TERRITORY_TIER, "territories"), region=f"{self.region:02d}",
            tier=TERRITORY_TIER, note=self.note,
            render=RenderRef(spec=outline_spec(), geometry=lambda: (self.outline(), (), None)),
        )]


def read_entries(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return YAML(typ="safe").load(path) or []
    except YAMLError as exc:
        raise ValueError(f"{path.name}: {exc}") from exc


def unique(models: list, label: str) -> None:
    ids = [m.id for m in models]
    if duplicates := sorted({i for i in ids if ids.count(i) > 1}):
        raise ValueError(f"duplicate {label} id: {duplicates}")


def load_countries() -> list[Country]:
    countries = [Country.model_validate(e) for e in read_entries(COUNTRIES)]
    unique(countries, "country")
    return countries


def _load_territory_file() -> list[Territory | Dispute]:
    models = {"territory": Territory, "dispute": Dispute}
    entries = read_entries(TERRITORIES)
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("kind") not in models:
            raise ValueError(f"{TERRITORIES.name} entry {i}: `kind` must be territory or dispute")
    loaded = [models[e["kind"]].model_validate(e) for e in entries]
    unique(loaded, "territory or dispute")
    return loaded


def load_territories() -> list[Territory]:
    return [t for t in _load_territory_file() if isinstance(t, Territory)]


def load_disputes() -> list[Dispute]:
    return [d for d in _load_territory_file() if isinstance(d, Dispute)]


def cards() -> list[Card]:
    """Each country's card and its capital's, then the territories and disputes, in file order."""
    return [card for source in (*load_countries(), *_load_territory_file()) for card in source.cards()]


def check() -> tuple[list[str], dict[str, BaseGeometry]]:
    """Errors from resolving every outline and point, and the country outlines that resolved, for the city check.
    Each capital must lie inside its country; each territory's sovereign must be a country."""
    try:
        countries, others = load_countries(), _load_territory_file()
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
    known = {c.id for c in countries}
    for other in others:
        if isinstance(other, Territory) and other.sovereign not in known:
            errors.append(f"{other.id}: sovereign {other.sovereign!r} is not a country")
        try:
            errors += composition_errors(other.id, other.geometry)
            other.outline()
        except (ValueError, OSError, GEOSException) as exc:
            errors.append(str(exc))
    return errors, outlines


def outside_country(owner: str, point: Point, country: str, shape: BaseGeometry) -> list[str]:
    return [] if shape.covers(point) else [f"{owner}: point ({point.x:.3f}, {point.y:.3f}) is outside {country}'s outline"]
