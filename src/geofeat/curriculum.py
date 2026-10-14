"""data/curriculum.yaml's schema and the runtime check of the parts the adjacency graph, the region derivation and
P3's order engine rely on. Policy lives in the data; this module only reads and checks it."""

from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from ruamel.yaml import YAML

from geofeat.model import ROOT

CURRICULUM = ROOT / "data/curriculum.yaml"


class Placement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    region: str
    host: str


class Ambiguous(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card: str
    default: Placement
    alternative: Placement
    reason: str = Field(min_length=1)


class Pass(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    ring: bool
    kinds: list[Literal["feature", "continent", "country", "capital", "territory", "dispute", "city"]]
    feature_tiers: list[int] = []
    city_tiers: list[Literal["core", "secondary"]] = []
    global_features: bool = False


class Region(BaseModel):
    model_config = ConfigDict(extra="forbid")
    number: int
    slug: str
    name: str
    entry: str
    exit: str
    way_in: str = ""
    countries: list[str]
    pockets: dict[str, str] = {}
    territories: dict[str, str] = {}
    disputes: dict[str, str] = {}
    walk: list[str] = []  # the frozen neighbour walk over the walk nodes (P3); empty: the order engine generates one
    opener: str | None = None  # a region frame feature opening the region; geofeat.order.inputs checks it

    def placed(self) -> dict[str, str]:
        return self.territories | self.disputes


class Curriculum(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passes: list[Pass]
    start: str
    regions: list[Region]
    ambiguous: list[Ambiguous] = []
    confusables: list[list[str]]

    def check(self, states: Iterable[str]) -> list[str]:
        """Errors: every state in exactly one region, regions numbered in ring order, entry and exit walk nodes, hosts
        walk nodes of the region, ambiguous cards at their default, confusables naming known cards."""
        errors = []
        states = set(states)
        slugs = [r.slug for r in self.regions]
        if [r.number for r in self.regions] != list(range(1, len(self.regions) + 1)):
            errors.append("regions must be numbered 1..n in ring order")
        if len(set(slugs)) != len(slugs) or self.start not in slugs:
            errors.append("region slugs must be unique and `start` one of them")
        members = [c for r in self.regions for c in r.countries]
        if dupes := sorted({c for c in members if members.count(c) > 1}):
            errors.append(f"in more than one region: {', '.join(dupes)}")
        if extra := sorted(set(members) - states):
            errors.append(f"unknown states: {', '.join(extra)}")
        if unplaced := sorted(states - set(members)):
            errors.append(f"states in no region: {', '.join(unplaced)}")
        cards = [c for r in self.regions for c in r.placed()]
        if dupes := sorted({c for c in cards if cards.count(c) > 1} | (set(cards) & states)):
            errors.append(f"territory or dispute placed twice or clashing with a state: {', '.join(dupes)}")
        for r in self.regions:
            walk = set(r.countries) - set(r.pockets)
            if r.walk and (sorted(r.walk) != sorted(walk) or r.walk[0] != r.entry):
                errors.append(f"{r.slug}: walk must start at {r.entry} and list each walk node once")
            for role, c in (("entry", r.entry), ("exit", r.exit)):
                if c not in walk:
                    errors.append(f"{r.slug}: {role} {c} is not a walk node (a member and not a pocket)")
            for card, host in r.pockets.items() | r.placed().items():
                if card in r.pockets and card not in r.countries:
                    errors.append(f"{r.slug}: pocket {card} is not a member")
                if host not in walk:
                    errors.append(f"{r.slug}: {card}'s host {host} is not a walk node")
        by_slug = {r.slug: r for r in self.regions}
        for a in self.ambiguous:
            for label, p in (("default", a.default), ("alternative", a.alternative)):
                region = by_slug.get(p.region)
                if region is None or p.host not in set(region.countries) - set(region.pockets):
                    errors.append(f"ambiguous {a.card}: {label} host {p.host} is not a walk node of {p.region}")
            if by_slug.get(a.default.region) and by_slug[a.default.region].placed().get(a.card) != a.default.host:
                errors.append(f"ambiguous {a.card}: not placed at its default")
        for group in self.confusables:
            if len(group) < 2 or not set(group) <= states | set(cards):
                errors.append(f"confusables {group}: needs two or more known cards")
        return errors


def load_curriculum(states: Iterable[str], path: Path = CURRICULUM) -> Curriculum:
    """The curriculum, checked against the known state ids (data/countries.yaml's)."""
    curriculum = Curriculum.model_validate(YAML(typ="safe").load(path))
    if errors := curriculum.check(states):
        raise ValueError(f"{path.name}: " + "; ".join(errors))
    return curriculum
