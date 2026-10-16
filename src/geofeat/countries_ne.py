"""Each state's, territory's and dispute's full recognised-border outline, for the adjacency graph and the region
derivation. The Natural Earth rows come from the `geometry` of data/countries.yaml and data/territories.yaml, the one
place they are recorded; ids are their slugs.

The outline is the full one: a country's `mainland` box is a display crop for its card only. The graph and the regions
are about where a state's land is, not what its card shows, so the outlying islands the boxes crop (the Prince Edward,
Macquarie, Kermadec and Trindade islands, Minamitorishima) still count for sea edges and feature shares. None of them
changes an edge or a feature's region today."""

from functools import cache

from shapely.geometry.base import BaseGeometry

from geofeat.model import Part
from geofeat.polities import compose, read_countries, active_territory_file


@cache
def _sources() -> tuple[tuple[str, ...], dict[str, tuple[Part, ...]]]:
    """The entries unplaced: geometry needs no curriculum, so the graph builds while curriculum.yaml is mid-edit."""
    countries, others = read_countries(), active_territory_file()
    return tuple(sorted(c.id for c in countries)), {e.id: tuple(e.geometry) for e in (*countries, *others)}


def state_ids() -> list[str]:
    """The states in data/countries.yaml."""
    return list(_sources()[0])


def parts(id: str) -> tuple[Part, ...]:
    """A state's, territory's or dispute's geometry parts as written in its yaml entry."""
    return _sources()[1][id]


def outline(id: str) -> BaseGeometry:
    """A state's, territory's or dispute's full outline, composed as its card's is but never cropped."""
    return compose(id, list(parts(id)))


def outlines() -> dict[str, BaseGeometry]:
    return {i: outline(i) for i in state_ids()}
