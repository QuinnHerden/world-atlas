"""Card sources. Each module adapts one data file to Cards; everything downstream reads only Cards."""

from collections import Counter
from pathlib import Path

from geofeat.card import Card
from geofeat.sources import cities, features, political, subdivisions

MODULES = (features, political, cities, subdivisions)
# The YAML files `make ids` mints uids in and the uid check reads. The political ones join once they exist.
PATHS: tuple[Path, ...] = (features.PATH, *(p for p in (*political.PATHS, cities.PATH, subdivisions.PATH) if p.exists()))


def all_cards() -> list[Card]:
    """Every active card from every source. Keys and uids must be unique across sources."""
    cards = [card for module in MODULES for card in module.cards()]
    for field in ("key", "uid"):
        counts = Counter(getattr(c, field) for c in cards)
        if duplicates := sorted(v for v, n in counts.items() if n > 1):
            raise ValueError(f"duplicate card {field}: {duplicates}")
    return cards
