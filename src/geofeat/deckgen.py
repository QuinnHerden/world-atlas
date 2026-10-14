"""Write the deck markdown for ankc: one file, every card in the one deck, in study order (see order.py)."""

import html

import geofeat.positions as positions
from geofeat.ankc import writes_pos
from geofeat.card import Card, load_media
from geofeat.model import DECK, ROOT_DECK, Feature, active, load_features
from geofeat.order import Siblings, dependencies, inverted, load_siblings, study_order
from geofeat.sources import all_cards

DECK_FILE = DECK / "geographic-features.md"


def card(c: Card, image: str, pos: int | None = None) -> str:
    front = f"**{html.escape(c.prompt)}**<br>![]({image})"
    back = "<br>".join(html.escape(line) for line in c.answer_lines)
    footnotes = "".join(f"[^tag]: {tag}\n" for tag in c.tags)
    if pos is not None:
        footnotes += f"[^pos]: {pos}\n"
    return f"---\n\n{front} ::: {back}\n\n---\n[^uid]: {c.uid}\n{footnotes}"


def ordered(features: list[Feature], siblings: Siblings) -> list[Feature]:
    return study_order(features, dependencies(features, siblings), {frozenset(pair) for pair in siblings.close})


def ideal_order(siblings: Siblings | None = None) -> list[Card]:
    """Every active card in the ideal study order. Only feature cards can be ordered until the P3 order engine."""
    cards = all_cards()
    if others := sorted(c.key for c in cards if c.kind != "feature"):
        raise SystemExit(f"no study order for cards other than features yet (P3): {others}")
    by_id = {c.id: c for c in cards}
    features = active(load_features())
    return [by_id[f.id] for f in ordered(features, siblings or load_siblings())]


def main() -> None:
    features = active(load_features())
    if missing := [f.id for f in features if f.uid is None]:
        raise SystemExit(f"features without a uid (run `make ids`): {missing}")
    media = load_media()
    siblings = load_siblings()
    for parent, child in inverted(features, dependencies(features, siblings)):
        print(f"order: {child} comes before its parent {parent}, which is in a later tier")
    cards = ideal_order(siblings)
    lock = positions.read()
    positions.require(lock, [c.uid for c in cards])
    if not lock.draft and not writes_pos():
        raise SystemExit(f"{positions.LOCK_FILE.name} is frozen (draft: false), so ankc 0.6+ must write it")
    pos = lock.positions if writes_pos() else {}

    DECK.mkdir(exist_ok=True)
    for old in DECK.glob("*.md"):
        old.unlink()
    header = f"---\ndeck: \"{ROOT_DECK}\"\n---\n"
    DECK_FILE.write_text(header + "\n".join(card(c, media[c.key], pos.get(c.uid)) for c in cards))
    print(f"wrote {len(cards)} cards to {DECK_FILE.name}" + (" with [^pos]" if pos else ""))


if __name__ == "__main__":
    main()
