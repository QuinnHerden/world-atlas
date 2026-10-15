"""Write the deck markdown for ankc: one file, every card in the one deck, in the curriculum order (geofeat.order)."""

import html

import geofeat.positions as positions
from geofeat.ankc import writes_pos
from geofeat.card import Card, load_media
from geofeat.model import DECK, ROOT_DECK, Feature, active, load_features
from geofeat.order import OrderError, Siblings, dependencies, report, study_order
from geofeat.order.inputs import ideal_order, ordering  # noqa: F401  ideal_order re-exported for check.py

DECK_FILE = DECK / "world-atlas.md"
# The note under the answer: smaller, and muted by opacity rather than a grey, so it reads in light and night mode.
NOTE_STYLE = "font-size:0.8em;opacity:0.65;margin-top:0.4em"


def card(c: Card, image: str, pos: int | None = None, tags: list[str] | None = None) -> str:
    front = f"**{html.escape(c.prompt)}**<br>![]({image})"
    back = "<br>".join(html.escape(line) for line in c.answer_lines)
    if c.note:  # ankc renders the note's *italics* as <em>; the HTML passes through intact
        back += f'<hr><div style="{NOTE_STYLE}">{html.escape(c.note)}</div>'
    footnotes = "".join(f"[^tag]: {tag}\n" for tag in (c.tags if tags is None else tags))
    if pos is not None:
        footnotes += f"[^pos]: {pos}\n"
    return f"---\n\n{front} ::: {back}\n\n---\n[^uid]: {c.uid}\n{footnotes}"


def ordered(features: list[Feature], siblings: Siblings) -> list[Feature]:
    """ADR 0004's feature order; check-data still runs it as the feature dependency-cycle gate."""
    return study_order(features, dependencies(features, siblings), {frozenset(pair) for pair in siblings.close})


def require_rendered(cards: list[Card], media: dict[str, str]) -> None:
    if missing := [c.key for c in cards if c.key not in media or not (DECK / media[c.key]).exists()]:
        raise SystemExit(f"cards not rendered (run `make render`): {missing}")


def main() -> None:
    features = active(load_features())
    if missing := [f.id for f in features if f.uid is None]:
        raise SystemExit(f"features without a uid (run `make ids`): {missing}")
    media = load_media()
    try:
        result = ordering()
    except OrderError as exc:
        raise SystemExit(f"study order: {exc}")
    print(report(result))
    lock = positions.read()
    positions.require(lock, [c.uid for c in result.cards])
    if not lock.draft and not writes_pos():
        raise SystemExit(f"{positions.LOCK_FILE.name} is frozen (draft: false), so ankc 0.6+ must write it")
    pos = lock.positions if writes_pos() else {}
    cards = result.cards
    require_rendered(cards, media)

    DECK.mkdir(exist_ok=True)
    for old in DECK.glob("*.md"):
        old.unlink()
    header = f"---\ndeck: \"{ROOT_DECK}\"\n---\n"
    body = [card(c, media[c.key], pos.get(c.uid), positions.locked_tags(c.tags, lock.entries.get(c.uid))) for c in cards]
    DECK_FILE.write_text(header + "\n".join(body))
    print(f"wrote {len(cards)} cards to {DECK_FILE.name}" + (" with [^pos]" if pos else ""))


if __name__ == "__main__":
    main()
