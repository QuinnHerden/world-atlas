"""Each state's, territory's and dispute's full recognised-border outline, for the adjacency graph and the region
derivation. The Natural Earth rows come from the `geometry` of data/countries.yaml and data/territories.yaml, the one
place they are recorded; ids are their slugs.

The outline is the full one: a country's `mainland` box is a display crop for its card only. The graph and the regions
are about where a state's land is, not what its card shows, so the outlying islands the boxes crop (the Prince Edward,
Macquarie, Kermadec and Trindade islands, Minamitorishima) still count for sea edges and feature shares. None of them
changes an edge or a feature's region today."""

from functools import cache

import shapely
from shapely import unary_union
from shapely.geometry.base import BaseGeometry

from geofeat.model import Part
from geofeat.polities import BBox, Subdivision, active_territory_file, compose, in_bbox, read_countries


@cache
def _sources() -> tuple[tuple[str, ...], dict[str, tuple[Part, ...]], dict[str, BBox]]:
    """The entries unplaced: geometry needs no curriculum, so the graph builds while curriculum.yaml is mid-edit. A
    subdivision's `within` defines it (Kaliningrad is the part of Russia's row inside it), so it applies here too;
    a country's `mainland` is a display crop and doesn't."""
    countries, others = read_countries(), active_territory_file()
    within = {e.id: e.within for e in others if isinstance(e, Subdivision) and e.within}
    return tuple(sorted(c.id for c in countries)), {e.id: tuple(e.geometry) for e in (*countries, *others)}, within


def state_ids() -> list[str]:
    """The states in data/countries.yaml."""
    return list(_sources()[0])


def parts(id: str) -> tuple[Part, ...]:
    """A state's, territory's or dispute's geometry parts as written in its yaml entry."""
    return _sources()[1][id]


def outline(id: str) -> BaseGeometry:
    """A state's, subdivision's, territory's or dispute's full outline, composed as its card's is but never cropped
    to `mainland`."""
    shape = compose(id, list(parts(id)))
    if box := _sources()[2].get(id):
        shape = unary_union([p for p in shapely.get_parts(shape) if in_bbox(p, box)])
    return shape


def outlines() -> dict[str, BaseGeometry]:
    return {i: outline(i) for i in state_ids()}
