"""Card sources. Each module adapts one data file to Cards; everything downstream reads only Cards."""

from collections import Counter
from pathlib import Path

from geofeat.card import Card
from geofeat.sources import features

MODULES = (features,)
PATHS: tuple[Path, ...] = tuple(m.PATH for m in MODULES)  # the YAML files `make ids` mints uids in


def all_cards() -> list[Card]:
    """Every active card from every source. Keys and uids must be unique across sources."""
    cards = [card for module in MODULES for card in module.cards()]
    for field in ("key", "uid"):
        counts = Counter(getattr(c, field) for c in cards)
        if duplicates := sorted(v for v, n in counts.items() if n > 1):
            raise ValueError(f"duplicate card {field}: {duplicates}")
    return cards
