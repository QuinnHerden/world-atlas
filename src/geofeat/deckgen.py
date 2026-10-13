"""Write the deck markdown for ankc: one file, every card in the one deck, in study order (see order.py)."""

import html
import json
import re

from geofeat.model import DECK, MEDIA_INDEX, ROOT_DECK, Feature, active, load_features
from geofeat.order import Siblings, dependencies, inverted, load_siblings, study_order

DECK_FILE = DECK / "geographic-features.md"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def id_tag(feature: Feature) -> str:
    """Lets Anki find a card again once it is retired; see "Retired cards" in the README. Kept as id_<id> because
    ankc before 0.5 cut a footnote tag at its first colon, and cards already imported carry this form."""
    return f"id_{feature.id}"


def tags(feature: Feature) -> list[str]:
    return [f"tier::{feature.tier}", f"category::{_slug(feature.category)}", id_tag(feature)]


def card(feature: Feature, image: str) -> str:
    answer = feature.name
    if feature.alt_names:
        answer += f" ({', '.join(feature.alt_names)})"
    front = f"**{html.escape(feature.type_text)}**<br>![]({image})"
    footnotes = "".join(f"[^tag]: {tag}\n" for tag in tags(feature))
    return f"---\n\n{front} ::: {html.escape(answer)}\n\n---\n[^uid]: {feature.uid}\n{footnotes}"


def ordered(features: list[Feature], siblings: Siblings) -> list[Feature]:
    return study_order(features, dependencies(features, siblings), {frozenset(pair) for pair in siblings.close})


def main() -> None:
    features = active(load_features())
    missing = [f.id for f in features if f.uid is None]
    if missing:
        raise SystemExit(f"features without a uid (run `make ids`): {missing}")
    media = json.loads(MEDIA_INDEX.read_text())
    siblings = load_siblings()
    for parent, child in inverted(features, dependencies(features, siblings)):
        print(f"order: {child} comes before its parent {parent}, which is in a later tier")

    DECK.mkdir(exist_ok=True)
    for old in DECK.glob("*.md"):
        old.unlink()
    header = f"---\ndeck: \"{ROOT_DECK}\"\n---\n"
    DECK_FILE.write_text(header + "\n".join(card(f, media[f.id]) for f in ordered(features, siblings)))
    print(f"wrote {len(features)} cards to {DECK_FILE.name}")


if __name__ == "__main__":
    main()
