"""The curriculum order's inputs from the real data, wired into the engine: the one place deckgen, positions, the
checks and later the walk maps and the guide get the study order from."""

from geofeat import adjacency
from geofeat.card import Card, card_key
from geofeat.countries_ne import state_ids
from geofeat.curriculum import Curriculum, load_curriculum
from geofeat.model import active, load_features
from geofeat.order import frames
from geofeat.order.engine import Ordering, OrderError, curriculum_order
from geofeat.order.legacy import Siblings, dependencies, load_siblings
from geofeat.sources import all_cards


def lookalikes(cards: list[Card], curriculum: Curriculum, siblings: Siblings) -> list[tuple[str, str]]:
    """The pair check's close feature pairs, and every pair within a curated confusable set (a country, or else the
    dispute or territory card of that id)."""
    keys = {c.key for c in cards}

    def key(id: str) -> str:
        found = next((k for kind in ("country", "dispute", "territory") if (k := card_key(kind, id)) in keys), None)
        if found is None:
            raise OrderError(f"confusable {id}: no country, dispute or territory card")
        return found

    pairs = [(card_key("feature", a), card_key("feature", b)) for a, b in siblings.close]
    pairs += [(key(a), key(b)) for group in curriculum.confusables for i, a in enumerate(group) for b in group[i + 1:]]
    return pairs


def ordering(siblings: Siblings | None = None) -> Ordering:
    """Every active card in the curriculum order (ADR 0009), with its report."""
    cards = all_cards()
    siblings = siblings or load_siblings()
    features = active(load_features())
    curriculum = load_curriculum(state_ids())
    edges = [(card_key("feature", p), card_key("feature", c)) for p, c in sorted(dependencies(features, siblings))]
    return curriculum_order(cards, curriculum, adjacency.neighbours(adjacency.graph()), frames.load(), edges,
                            lookalikes(cards, curriculum, siblings))


def ideal_order(siblings: Siblings | None = None) -> list[Card]:
    return ordering(siblings).cards
