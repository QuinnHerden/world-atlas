"""Each state's, territory's and dispute's full recognised-border outline, for the adjacency graph and the region
derivation. The Natural Earth rows come from the `geometry` of data/countries.yaml and data/territories.yaml, the one
place they are recorded; ids are their slugs.

The outline is the full one: a country's `mainland` box is a display crop for its card only. The graph and the regions
are about where a state's land is, not what its card shows, so the outlying islands the boxes crop (the Prince Edward,
Macquarie, Kermadec and Trindade islands, Minamitorishima) still count for sea edges and feature shares. None of them
changes an edge or a feature's region today."""

from functools import cache

import shapely
from shapely.geometry.base import BaseGeometry

from geofeat import ne
from geofeat.model import Part
from geofeat.sources.political import load_political


@cache
def _sources() -> tuple[tuple[str, ...], dict[str, tuple[Part, ...]]]:
    countries, others = load_political()
    return tuple(sorted(c.id for c in countries)), {e.id: tuple(e.geometry) for e in (*countries, *others)}


def state_ids() -> list[str]:
    """The states in data/countries.yaml."""
    return list(_sources()[0])


def parts(id: str) -> tuple[Part, ...]:
    """A state's, territory's or dispute's geometry parts as written in its yaml entry."""
    return _sources()[1][id]


@cache
def _row(layer: str, nid: int) -> BaseGeometry:
    rows = ne.layer(layer)
    match = rows[rows["ne_id"] == nid]
    if len(match) != 1:
        raise ValueError(f"{layer} {nid}: {len(match)} rows")
    return shapely.make_valid(match.geometry.iloc[0])


def _part_row(id: str, part: Part) -> BaseGeometry:
    if part.layer is None or part.select is None or set(part.select) != {"ne_id"} or part.rows != 1:
        raise ValueError(f"{id}: an outline part must be one Natural Earth row selected by ne_id, not {part}")
    return _row(part.layer, int(part.select["ne_id"]))


def outline(id: str) -> BaseGeometry:
    """A state's, territory's or dispute's full outline: the union of its added rows less its subtracted ones."""
    geometry = shapely.union_all([_part_row(id, p) for p in parts(id) if not p.subtract])
    if cut := [_part_row(id, p) for p in parts(id) if p.subtract]:
        geometry = geometry.difference(shapely.union_all(cut))
    return geometry


def outlines() -> dict[str, BaseGeometry]:
    return {i: outline(i) for i in state_ids()}
