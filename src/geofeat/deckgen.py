"""Write the deck markdown for ankc: one file per deck (geofeat.decks), World Atlas's and each companion deck's, every
card in the study order (geofeat.order). A card's media is its rendered map, already in deck/, or its ready-made image
(a flag's SVG), copied into deck/ here under its content-hash name."""

import html
import shutil
from pathlib import Path

import geofeat.positions as positions
from geofeat.ankc import writes_pos
from geofeat.card import Card, card_media, image_name, load_media
from geofeat.decks import BY_NAME, DECKS, WORLD, DeckInfo
from geofeat.model import DECK, Feature, active, load_features
from geofeat.order import OrderError, Siblings, dependencies, report, study_order
from geofeat.order.inputs import deck_order, ideal_order, ordering  # noqa: F401  ideal_order re-exported for check.py

DECK_FILE = DECK / f"{WORLD.slug}.md"


def deck_file(deck: DeckInfo) -> Path:
    return DECK / f"{deck.slug}.md"
# The note under the answer: smaller, and muted by opacity rather than a grey, so it reads in light and night mode.
NOTE_STYLE = "font-size:0.8em;opacity:0.65;margin-top:0.4em"
# A flag at its own aspect ratio (its SVG's intrinsic size), shrunk to fit the card's width and to leave the answer room
# below it. The half-transparent grey border shows a white flag's edge (Japan, Cyprus) on a white card and any flag's
# on a dark one, in day and night mode alike.
FLAG_SIZE = "max-width:100%;max-height:45vh"
FLAG_BORDER = ";box-sizing:border-box;border:1px solid rgba(128,128,128,0.6)"
UNBORDERED = frozenset({"nepal"})  # not a rectangle: a border would draw a box round the pennants


def front(c: Card, image: str) -> str:
    """A card with a ready-made image (a flag) shows it alone; every other card shows its type in bold above its map."""
    if c.image is not None:
        style = FLAG_SIZE + ("" if c.id in UNBORDERED else FLAG_BORDER)
        return f'<img src="{html.escape(image)}" style="{style}">'
    return f"**{html.escape(c.prompt)}**<br>![]({image})"


def card(c: Card, image: str, pos: int | None = None, tags: list[str] | None = None) -> str:
    back = "<br>".join(html.escape(line) for line in c.answer_lines)
    if c.note:  # ankc renders the note's *italics* as <em>; the HTML passes through intact
        back += f'<hr><div style="{NOTE_STYLE}">{html.escape(c.note)}</div>'
    footnotes = "".join(f"[^tag]: {tag}\n" for tag in (c.tags if tags is None else tags))
    if pos is not None:
        footnotes += f"[^pos]: {pos}\n"
    return f"---\n\n{front(c, image)} ::: {back}\n\n---\n[^uid]: {c.uid}\n{footnotes}"


def ordered(features: list[Feature], siblings: Siblings) -> list[Feature]:
    """ADR 0004's feature order; check-data still runs it as the feature dependency-cycle gate."""
    return study_order(features, dependencies(features, siblings), {frozenset(pair) for pair in siblings.close})


def require_rendered(cards: list[Card], media: dict[str, str]) -> None:
    if missing := [c.key for c in cards
                   if c.render is not None and (c.key not in media or not (DECK / media[c.key]).exists())]:
        raise SystemExit(f"cards not rendered (run `make render`): {missing}")
    if missing := [c.key for c in cards if c.image is not None and not c.image.exists()]:
        raise SystemExit(f"cards' images are missing: {missing}")


def copy_images(cards: list[Card]) -> None:
    """Copy each ready-made image into deck/ under its content-hash name, and drop the copies no card uses. A copy
    already there is kept only if its bytes still hash to its name."""
    names = {image_name(c.image): c.image for c in cards if c.image is not None}
    for name, path in names.items():
        if not (DECK / name).exists() or image_name(DECK / name) != name:
            shutil.copyfile(path, DECK / name)
    for stale in {p.name for p in DECK.glob("*.svg")} - set(names):
        (DECK / stale).unlink()


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
    cards = deck_order(result)
    positions.require(lock, [c.uid for c in cards])
    if not lock.draft and not writes_pos():
        raise SystemExit(f"{positions.LOCK_FILE.name} is frozen (draft: false), so ankc 0.6+ must write it")
    pos = lock.positions if writes_pos() else {}
    if moved := [f"{c.key} is locked in {lock.entries[c.uid].deck}, not {BY_NAME[c.deck].slug}" for c in cards
                 if lock.entries[c.uid].deck != BY_NAME[c.deck].slug]:
        raise SystemExit(f"a card's deck is frozen with its position: {'; '.join(moved)}")
    require_rendered(cards, media)

    DECK.mkdir(exist_ok=True)
    copy_images(cards)
    for old in DECK.glob("*.md"):
        old.unlink()
    for deck in DECKS:
        mine = [c for c in cards if c.deck == deck.name]
        header = f"---\ndeck: \"{deck.name}\"\n---\n"
        body = [card(c, card_media(c, media), pos.get(c.uid), positions.locked_tags(c.tags, lock.entries.get(c.uid)))
                for c in mine]
        deck_file(deck).write_text(header + "\n".join(body))
        print(f"wrote {len(mine)} cards to {deck_file(deck).name}" + (" with [^pos]" if pos else ""))


if __name__ == "__main__":
    main()
