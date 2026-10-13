"""Study order: the sequence in which new cards come up. See docs/adr/0004-flat-deck-and-study-order.md.

Tier 1 first, then 2, then 3. Within a tier a parent comes before its children, categories are interleaved, and
siblings near each other on the map are kept at least NEAR_GAP cards apart where the other rules allow.
"""

import hashlib
import json
from collections import Counter
from dataclasses import dataclass

from geofeat.model import BUILD, FEATURES, GEOMETRY, LOCK, ROOT, Feature

NEAR_GAP = 3
SIBLINGS = BUILD / "siblings.json"  # written by `make check-data`, read by deckgen

Edge = tuple[str, str]  # (parent, child)


@dataclass(frozen=True)
class Siblings:
    """What the pair check measured: each feature's area, and every pair near enough to compare."""

    area_km2: dict[str, float]
    close: list[tuple[str, str]]  # every pair within pairs.NEAR_M or overlapping
    nested: list[Edge]  # (outer, inner)


def dependencies(features: list[Feature], siblings: Siblings) -> set[Edge]:
    """Parent-child edges among the features.

    A feature cut out of another (`subtract`) or drawn as its context is the parent: the Himalayas before the
    Tibetan Plateau, the Nile before its delta. A feature added into another's geometry, or named in `allow_nested`,
    shares area with it, so the larger is the parent: the Mediterranean before the Aegean, the Arabian Peninsula
    before the Arabian Desert. Pairs the pair check finds nested come outer first, unless that contradicts the edges
    above or only one is a climate system: a strait inside a cyclone belt isn't part of it.
    """
    ids = {f.id for f in features}
    climate = {f.id for f in features if f.family == "climate"}
    edges: set[Edge] = set()

    def by_area(a: str, b: str) -> Edge:
        return (a, b) if (siblings.area_km2.get(a, 0), a) >= (siblings.area_km2.get(b, 0), b) else (b, a)

    for f in features:
        for part in f.geometry:
            if part.feature in ids:
                edges.add((part.feature, f.id) if part.subtract else by_area(part.feature, f.id))
        edges |= {(other, f.id) for other in f.frame.context if other in ids}
        edges |= {by_area(o.id, f.id) for o in f.allow_nested if o.id in ids}
    for outer, inner in siblings.nested:
        if outer in ids and inner in ids and (outer in climate) == (inner in climate) and not _reaches(edges, inner, outer):
            edges.add((outer, inner))
    return edges


def _reaches(edges: set[Edge], start: str, goal: str) -> bool:
    seen, todo = set(), [start]
    while todo:
        node = todo.pop()
        if node == goal:
            return True
        if node not in seen:
            seen.add(node)
            todo += [c for p, c in edges if p == node]
    return False


def inverted(features: list[Feature], edges: set[Edge]) -> list[Edge]:
    """Edges whose child sits in an earlier tier than its parent; tier order wins, so the child comes first."""
    tier = {f.id: f.tier for f in features}
    return sorted((p, c) for p, c in edges if p in tier and c in tier and tier[c] < tier[p])


def study_order(features: list[Feature], edges: set[Edge], near: set[frozenset[str]]) -> list[Feature]:
    """The features in study order. Ties fall back to the order of `features`."""
    order: list[Feature] = []
    for tier in (1, 2, 3):
        order += _tier_order([f for f in features if f.tier == tier], edges, near, order)
    return order


def _tier_order(members: list[Feature], edges: set[Edge], near: set[frozenset[str]], before: list[Feature]) -> list[Feature]:
    ids = {f.id for f in members}
    parents = {f.id: {p for p, c in edges if c == f.id and p in ids} for f in members}
    total = Counter(f.category for f in members)
    placed: list[Feature] = []
    remaining = list(members)
    while remaining:
        done = {f.id for f in placed}
        ready = [f for f in remaining if parents[f.id] <= done]
        if not ready:
            raise ValueError(f"dependency cycle among {sorted(f.id for f in remaining)}")
        recent = (before + placed)[-NEAR_GAP:]

        def key(f: Feature) -> tuple[bool, bool, float, int]:
            # Spread each category evenly: its k-th card ideally sits (k + 0.5) / n of the way through the tier.
            slot = (sum(p.category == f.category for p in placed) + 0.5) / total[f.category]
            return (
                bool(recent) and recent[-1].category == f.category,
                any(frozenset((f.id, r.id)) in near for r in recent),
                slot,
                remaining.index(f),
            )

        pick = min(ready, key=key)
        placed.append(pick)
        remaining.remove(pick)
    return placed


def inputs_hash() -> str:
    """Hash of everything the pair check reads or runs, so deckgen can tell a stale siblings file."""
    code = [ROOT / "src/geofeat" / name for name in ("pairs.py", "frame.py", "resolve.py", "style.py", "model.py")]
    h = hashlib.sha256()
    for path in (FEATURES, LOCK, *code, *sorted(GEOMETRY.glob("*.geojson"))):
        data = path.read_bytes()
        h.update(f"{path.name}\0{len(data)}\0".encode() + data)
    return h.hexdigest()


def save_siblings(siblings: Siblings) -> None:
    BUILD.mkdir(exist_ok=True)
    data = {"inputs": inputs_hash(), "area_km2": siblings.area_km2, "close": siblings.close, "nested": siblings.nested}
    SIBLINGS.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")


def load_siblings() -> Siblings:
    data = json.loads(SIBLINGS.read_text()) if SIBLINGS.exists() else {}
    if data.get("inputs") != inputs_hash():
        raise SystemExit(f"{SIBLINGS.name} is missing or stale (run `make check-data`)")
    return Siblings(data["area_km2"], [tuple(p) for p in data["close"]], [tuple(p) for p in data["nested"]])
