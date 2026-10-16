"""The curriculum order's inputs from the real data, wired into the engine: the one place deckgen, positions, the
checks and later the walk maps and the guide get the study order from. Policy is applied here, over the geometry facts
geofeat.order.frames measures and caches."""

from collections.abc import Callable

from geofeat import adjacency
from geofeat.pairs import COVER_MAX
from geofeat.card import Card, card_key
from geofeat.countries_ne import state_ids
from geofeat.curriculum import Curriculum, load_curriculum
from geofeat.model import active, load_features
from geofeat.order import frames
from geofeat.order.engine import Frame, Ordering, OrderError, curriculum_order, lookup, region_of
from geofeat.order.legacy import Siblings, dependencies, load_siblings
from geofeat.sources import all_cards

OPENS_SHARE = 0.5  # an opener opens the cluster of the first country it holds this much of, else the one it holds most of
NEAR_PAIR_KM = 50.0  # same-family features this close, or touching, are look-alikes (Bosporus and Dardanelles)
FOOTPRINT_IOU = 0.6  # a feature and a country this alike in outline are look-alikes (Italy, the Italian Peninsula)


def opener_errors(curriculum: Curriculum, facts: frames.GeometryFacts) -> list[str]:
    """Each `opener` must be an active ring feature (not orientation), in its own region, and open one region only."""
    errors, seen = [], {}
    for r in curriculum.regions:
        if r.opener is None:
            continue
        if r.opener in seen:
            errors.append(f"{r.slug}: opener {r.opener} already opens {seen[r.opener]}")
        seen[r.opener] = r.slug
        facts_of = facts.features.get(r.opener)
        if facts_of is None:
            errors.append(f"{r.slug}: opener {r.opener!r} is not an active feature outside orientation")
        elif facts_of.region != r.number:
            errors.append(f"{r.slug}: opener {r.opener} is in region {facts_of.region}, not {r.number}")
    return errors


def feature_frames(facts: frames.GeometryFacts, curriculum: Curriculum) -> dict[str, Frame]:
    """Each feature card's Frame: an opener (its region's `opener`) frames the countries it mostly covers; any other
    feature the countries it touches."""
    if errors := opener_errors(curriculum, facts):
        raise OrderError("; ".join(errors))
    openers = {r.opener for r in curriculum.regions if r.opener}
    out = {}
    for id, f in facts.features.items():
        if id in openers:
            mostly = tuple(c for c in f.touches if f.held[c] >= OPENS_SHARE)
            most = max(f.touches, key=lambda c: (f.held[c], c), default=None)
            out[card_key("feature", id)] = Frame(f.region, mostly or ((most,) if most else ()), True)
        else:
            out[card_key("feature", id)] = Frame(f.region, f.touches)
    return out


def lookalikes(cards: list[Card], curriculum: Curriculum, facts: frames.GeometryFacts) -> list[tuple[str, str]]:
    """Pairs kept 3-10 cards apart within a region (PM, 2026-10-14): each curated confusable set (a country, or else
    the dispute or territory card of that id); same-family features that touch or lie within 50 km, unless one
    contains the other (cover >= 0.9: parent and child, not look-alikes); and a feature and a country with
    near-identical outlines. The engine ignores pairs whose cards aren't in one region."""
    keys = {c.key for c in cards}

    def key(id: str) -> str:
        found = next((k for kind in ("country", "dispute", "territory", "subnational") if (k := card_key(kind, id)) in keys), None)
        if found is None:
            raise OrderError(f"confusable {id}: no country, dispute, territory or subnational card")
        return found

    pairs = [(key(a), key(b)) for group in curriculum.confusables for i, a in enumerate(group) for b in group[i + 1:]]
    pairs += [(card_key("feature", a), card_key("feature", b)) for a, b, km, cover in facts.same_family
              if km <= NEAR_PAIR_KM and cover < COVER_MAX]
    pairs += [(card_key("country", c), card_key("feature", id)) for id, f in sorted(facts.features.items())
              for c in f.touches if f.iou[c] >= FOOTPRINT_IOU]
    return pairs


def ordering(siblings: Siblings | None = None) -> Ordering:
    """Every active card in the curriculum order (ADR 0009), with its report."""
    cards = all_cards()
    siblings = siblings or load_siblings()
    features = active(load_features())
    curriculum = load_curriculum(state_ids())
    facts = frames.load()
    edges = [(card_key("feature", p), card_key("feature", c)) for p, c in sorted(dependencies(features, siblings))]
    return curriculum_order(cards, curriculum, adjacency.neighbours(adjacency.graph()), feature_frames(facts, curriculum),
                            edges, lookalikes(cards, curriculum, facts))


def card_region(curriculum: Curriculum) -> Callable[[Card], int]:
    """Each card's ring region by the engine's rule, over the same feature frames `ordering` uses."""
    frame_of = lookup(feature_frames(frames.load(), curriculum))
    return lambda c: region_of(c, frame_of)


def ideal_order(siblings: Siblings | None = None) -> list[Card]:
    return ordering(siblings).cards
