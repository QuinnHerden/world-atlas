"""The political entities: data/countries.yaml (one entry per state) and data/territories.yaml (territory and
dispute entries, told apart by `kind`), their outlines, and their place in the ring, which comes from
data/curriculum.yaml. The entity layer: sources/political.py adapts these to Cards, and countries_ne.py reads their
geometry. See docs/adr/0005 and 0008."""

import unicodedata
from pathlib import Path
from typing import Annotated, Literal, NamedTuple

import shapely
from pydantic import Field, PrivateAttr, model_validator
from ruamel.yaml import YAML, YAMLError
from shapely import unary_union
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from geofeat.card import Text
from geofeat.curriculum import CURRICULUM, load_curriculum
from geofeat.model import ROOT, Note, Part, Strict, Verify
from geofeat.resolve import area_km2, custom, features_by_id, layer, resolve, select_rows

COUNTRIES = ROOT / "data/countries.yaml"
TERRITORIES = ROOT / "data/territories.yaml"
PATHS = (COUNTRIES, TERRITORIES)
PLACES = "10m_populated_places"
# How exactly an outline must compose, as in docs/research/ne-political-layers.md (c): a subtracted row lies inside
# the base, an added row lies outside it.
INSIDE_SHARE = 0.999
OUTSIDE_SHARE = 0.001
Id = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]
Uid = Annotated[str, Field(pattern=r"^[A-Za-z0-9]{10}$")]
GeojsonFile = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*\.geojson$")]
Lon = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
Lat = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
# lon_min, lat_min, lon_max, lat_max; lon_min > lon_max means the box crosses 180°
BBox = tuple[Lon, Lat, Lon, Lat]


def in_bbox(geometry: BaseGeometry, bbox: BBox) -> bool:
    lon_min, lat_min, lon_max, lat_max = bbox
    coords = shapely.get_coordinates(geometry)
    lons, lats = coords[:, 0], coords[:, 1]
    in_lon = (lons >= lon_min) & (lons <= lon_max) if lon_min <= lon_max else (lons >= lon_min) | (lons <= lon_max)
    return bool((in_lon & (lats >= lat_min) & (lats <= lat_max)).all())


def part_geometry(owner: str, part: Part) -> BaseGeometry:
    """One part, by the same grammar as features.yaml: Natural Earth rows, a geometry/ file, or a feature's shape."""
    if part.file:
        return custom(part.file)
    if part.feature:
        if part.feature not in features_by_id():
            raise ValueError(f"{owner}: references unknown feature {part.feature!r}")
        return resolve(features_by_id()[part.feature])
    return select_rows(owner, part)


def compose(owner: str, parts: list[Part]) -> BaseGeometry:
    """The union of the added parts less the subtracted ones: the full outline, which the adjacency graph and the
    region outlines use (countries_ne.py)."""
    keep = unary_union([part_geometry(owner, p) for p in parts if not p.subtract])
    if cut := [part_geometry(owner, p) for p in parts if p.subtract]:
        keep = shapely.make_valid(keep.difference(unary_union(cut)))
    return keep


def outline(owner: str, parts: list[Part], expect: BBox, mainland: BBox | None = None) -> BaseGeometry:
    """A card's outline: the full outline cut to the `mainland` box when there is one, checked against `expect`."""
    keep = compose(owner, parts)
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


class Capital(Strict):
    name: Text
    alt_names: list[Text] = []
    ne_id: int | None = None
    file: GeojsonFile | None = None
    expect: BBox
    note: Note | None = None
    verify: list[Verify] = []

    @model_validator(mode="after")
    def _one_source(self) -> "Capital":
        if (self.ne_id is None) == (self.file is None):
            raise ValueError("a capital needs exactly one of `ne_id` or `file`")
        return self


class RingPlace(NamedTuple):
    region: int  # ring order, as numbered in data/curriculum.yaml
    host: str | None  # the walk node a pocket sits beside (P3), never a statement of sovereignty
    kind: Literal["country", "territory", "dispute"]  # the curriculum map that places it


class FrameOverride(Strict):
    """A card's own exception to the political framing rules: `inset` forces its detail inset on or off, and
    `inset_km` sets the inset's width (the Spratlys, zoomed in past the default so the island group reads);
    `inset_centre` centres the inset on a point instead of the subject, so it takes in the neighbours it is told apart
    from (the ABC islands). `ring: false` draws no ring round the subject, on the map or in the inset; `ring: single`
    draws one on the main map round all its parts (a state scattered over an ocean), and none in the inset. On a country
    these apply to the country card only; its capital card always has an inset by the city rule, and no ring.
    `include` names countries or territories whose main bodies the frame holds too, moving before it widens (Australia,
    for New Zealand). It moves the frame itself, so the capital and city cards drawn on it follow."""

    inset: bool | None = None
    inset_km: Annotated[float, Field(gt=0, le=5000)] | None = None
    inset_centre: tuple[Lon, Lat] | None = None
    ring: bool | Literal["single"] = True
    include: list[Id] = []


class Placed(Strict):
    """An entry whose region and host come from data/curriculum.yaml, the one place placement is decided. The loaders
    place it; read unplaced, it has only its own data (countries_ne.py needs no more)."""

    id: Id
    frame: FrameOverride = FrameOverride()
    _place: RingPlace | None = PrivateAttr(default=None)

    @property
    def region(self) -> int:
        return self._placed().region

    @property
    def host(self) -> str | None:
        return self._placed().host

    def place(self, place: RingPlace) -> None:
        if place.kind != (kind := getattr(self, "kind", "country")):
            raise ValueError(f"{self.id}: a {kind} that {CURRICULUM.name} places as a {place.kind}")
        self._place = place

    def _placed(self) -> RingPlace:
        if self._place is None:
            raise ValueError(f"{self.id}: not placed (region and host come from {CURRICULUM.name}, set by the loaders)")
        return self._place


class Country(Placed):
    name: Text
    alt_names: list[Text] = []
    uids: dict[Literal["country", "capital"], Uid | None]
    tier: Literal[1, 2, 3]  # microstates and small island states are 3; every country is in pass 1 all the same
    note: Note | None = None
    verify: list[Verify] = []
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


class Territory(Placed):
    kind: Literal["territory"]
    name: Text
    alt_names: list[Text] = []
    uid: Uid | None = None
    sovereign: Id  # a country id
    status_line: Text  # back line 2, e.g. "Overseas department of France"
    geometry: Annotated[list[Part], Field(min_length=1)]
    expect: BBox
    note: Note | None = None
    verify: list[Verify] = []

    def outline(self) -> BaseGeometry:
        return outline(self.id, self.geometry, self.expect)


def _alphabetical(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().casefold()


class PartyLabel(Strict):
    """A party that isn't one of the 197 states, e.g. Polisario Front / SADR."""

    label: Text


Party = Id | PartyLabel  # a country id, or an explicit label


class Dispute(Placed):
    kind: Literal["dispute"]
    name: Text
    alt_names: list[Text] = []
    uid: Uid | None = None
    parties: Annotated[list[Party], Field(min_length=2)]
    geometry: Annotated[list[Part], Field(min_length=1)]  # disputed-areas rows
    expect: BBox
    note: Note | None = None
    verify: list[Verify] = []

    @model_validator(mode="after")
    def _distinct_parties(self) -> "Dispute":
        if len(set(self.parties)) != len(self.parties):
            raise ValueError(f"{self.id}: parties repeat")
        return self

    def party_names(self, countries: dict[str, str]) -> list[str]:
        """Each party's display name: a country's name from countries.yaml, or the label as written."""
        if unknown := [p for p in self.parties if isinstance(p, str) and p not in countries]:
            raise ValueError(f"{self.id}: parties {unknown} are not countries (use `{{label: ...}}` for a non-state party)")
        names = [countries[p] if isinstance(p, str) else p.label for p in self.parties]
        if len({_alphabetical(n) for n in names}) != len(names):
            raise ValueError(f"{self.id}: party names repeat: {names}")
        return names

    def parties_line(self, countries: dict[str, str]) -> str:
        return f"Disputed: {', '.join(sorted(self.party_names(countries), key=_alphabetical))}"

    def outline(self) -> BaseGeometry:
        return outline(self.id, self.geometry, self.expect)


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


def curriculum_placements(states: list[str]) -> dict[str, RingPlace]:
    """Where data/curriculum.yaml places every state, territory and dispute. A state's host is its pocket host, if it
    is a pocket. The curriculum is checked against `states` first (each state in exactly one region, every host a walk
    node of its region), so a host is a country, one level deep, in the same region."""
    placements = {}
    for r in load_curriculum(states).regions:
        placements |= {c: RingPlace(r.number, r.pockets.get(c), "country") for c in r.countries}
        placements |= {c: RingPlace(r.number, host, "territory") for c, host in r.territories.items()}
        placements |= {c: RingPlace(r.number, host, "dispute") for c, host in r.disputes.items()}
    return placements


def placed[P: Placed](entries: list[P], path: Path, placements: dict[str, RingPlace]) -> list[P]:
    """Place each entry; an entry the curriculum doesn't place, or places as another kind, is an error."""
    if missing := [e.id for e in entries if e.id not in placements]:
        raise ValueError(f"{path.name}: not placed in any region of {CURRICULUM.name}: {', '.join(missing)}")
    for entry in entries:
        entry.place(placements[entry.id])
    return entries


def read_countries() -> list[Country]:
    """data/countries.yaml's entries, unplaced."""
    countries = [Country.model_validate(e) for e in read_entries(COUNTRIES)]
    unique(countries, "country")
    return countries


def read_territory_file() -> list[Territory | Dispute]:
    """data/territories.yaml's entries in file order, unplaced."""
    models = {"territory": Territory, "dispute": Dispute}
    entries = read_entries(TERRITORIES)
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("kind") not in models:
            raise ValueError(f"{TERRITORIES.name} entry {i}: `kind` must be territory or dispute")
    loaded = [models[e["kind"]].model_validate(e) for e in entries]
    unique(loaded, "territory or dispute")
    return loaded


def load_countries() -> list[Country]:
    """The countries, each placed by data/curriculum.yaml."""
    countries = read_countries()
    return placed(countries, COUNTRIES, curriculum_placements([c.id for c in countries])) if countries else countries


def load_political() -> tuple[list[Country], list[Territory | Dispute]]:
    """The countries, and the territories and disputes in file order, each placed by data/curriculum.yaml. A territory
    or dispute the curriculum places must have an entry."""
    countries, others = read_countries(), read_territory_file()
    if not countries and not others:
        return [], []
    placements = curriculum_placements([c.id for c in countries])
    known = {o.id for o in others}
    if orphans := sorted(i for i, p in placements.items() if p.kind != "country" and i not in known):
        raise ValueError(f"{CURRICULUM.name}: places what {TERRITORIES.name} has no entry for: {', '.join(orphans)}")
    return placed(countries, COUNTRIES, placements), placed(others, TERRITORIES, placements)


def load_territories() -> list[Territory]:
    return [t for t in load_political()[1] if isinstance(t, Territory)]


def load_disputes() -> list[Dispute]:
    return [d for d in load_political()[1] if isinstance(d, Dispute)]


def outside_country(owner: str, point: Point, country: str, shape: BaseGeometry) -> list[str]:
    return [] if shape.covers(point) else [f"{owner}: point ({point.x:.3f}, {point.y:.3f}) is outside {country}'s outline"]
