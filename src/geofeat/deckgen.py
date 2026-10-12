"""Write the deck markdown for ankc: one file per category and tier, one card per feature."""

import html
import json
import re
from collections import defaultdict

from geofeat.model import DECK, MEDIA_INDEX, Feature, active, load_features


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def card(feature: Feature, image: str) -> str:
    answer = feature.name
    if feature.alt_names:
        answer += f" ({', '.join(feature.alt_names)})"
    front = f"**{html.escape(feature.type_text)}**<br>![]({image})"
    return f"---\n\n{front} ::: {html.escape(answer)}\n\n---\n[^uid]: {feature.uid}\n"


def main() -> None:
    features = active(load_features())
    missing = [f.id for f in features if f.uid is None]
    if missing:
        raise SystemExit(f"features without a uid (run `make ids`): {missing}")
    media = json.loads(MEDIA_INDEX.read_text())

    files: dict[tuple[str, int], list[Feature]] = defaultdict(list)
    for feature in features:
        files[(feature.category, feature.tier)].append(feature)

    DECK.mkdir(exist_ok=True)
    for old in DECK.glob("*.md"):
        old.unlink()
    for (category, tier), members in sorted(files.items()):
        header = f"---\ndeck: \"{members[0].subdeck}\"\ntags:\n  - tier::{tier}\n---\n"
        body = "\n".join(card(f, media[f.id]) for f in members)
        (DECK / f"{_slug(category)}-tier-{tier}.md").write_text(header + body)
    print(f"wrote {len(features)} cards in {len(files)} files")


if __name__ == "__main__":
    main()
