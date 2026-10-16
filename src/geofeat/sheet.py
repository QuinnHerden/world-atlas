"""Contact sheets for visual QA, written to build/.

Cards are named by key patterns: a key (`country:france`), a glob (`city:*`, `*:georgia`), or a bare id, which means a
feature (`nile`). No pattern means every rendered card.

`sheet [--out NAME.png] [patterns…]`: a grid of maps (build/sheet.png by default).
`sheet --phone [--out NAME.png] [patterns…]`: the same at phone size, PHONE_W px wide per map, PHONE_PER_PAGE to a page
(build/phone-NN.png), or all on one page with --out.
`sheet --review`: one phone-size sheet per ring region, cards in study order (build/review-NN.png), and one for the
orientation block (build/review-orientation.png), each map labelled with its study position, key and answer.
`sheet --pairs`: flagged, nested, allowed and near-threshold sibling pairs side by side, labelled with their overlap
scores, PAIRS_PER_PAGE to a page (build/pairs-NN.png); every pair goes to build/pairs.log.
"""

import math
import re
import sys
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw

from geofeat.card import card_key, load_media, match_keys
from geofeat.model import BUILD, DECK, active, load_features
from geofeat.pairs import find_pairs
from geofeat.resolve import resolve

THUMB_W, THUMB_H, LABEL_H = 480, 270, 22
OUT_NAME = re.compile(r"^[a-z0-9-]+\.png$")
PAIRS_PER_PAGE = 50
PHONE_W, PHONE_PER_PAGE = 390, 48  # a phone screen's width in CSS px
REVIEW_COLUMNS = 4


@cache
def _media() -> dict[str, str]:
    return load_media()


def card_image(key: str) -> Image.Image:
    """The map of the card with this key (`kind:id`)."""
    return Image.open(DECK / _media()[key]).convert("RGB")


def thumbnail(key: str, width: int = THUMB_W) -> Image.Image:
    """A card shrunk to sheet size on load, so a sheet of hundreds of maps doesn't hold them all at full size."""
    image = card_image(key)
    return image.resize((width, round(width * image.height / image.width)), Image.Resampling.LANCZOS)


def contact_sheet(cells: list[tuple[str, Image.Image]], columns: int, out: Path) -> None:
    rows = math.ceil(len(cells) / columns)
    w, h = cells[0][1].size if cells else (THUMB_W, THUMB_H)
    sheet = Image.new("RGB", (columns * w, max(rows, 1) * (h + LABEL_H)), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (label, image) in enumerate(cells):
        x, y = (i % columns) * w, (i // columns) * (h + LABEL_H)
        sheet.paste(image, (x, y + LABEL_H))
        draw.text((x + 6, y + 4), label, fill="black")
    sheet.save(out)
    print(out)


def pairs_sheet() -> None:
    geometries = {f.id: (f, resolve(f)) for f in active(load_features())}
    pairs = sorted(find_pairs(geometries), key=lambda p: (not p.flagged, not p.nested, -p.cover, -p.iou))
    (BUILD / "pairs.log").write_text("".join(f"{pair}\n" for pair in pairs))
    print(f"{len(pairs)} pairs -> {BUILD / 'pairs.log'}")
    shown = [p for p in pairs if p.flagged or p.nested or p.allowed or p.near]
    for old in BUILD.glob("pairs-*.png"):
        old.unlink()
    for page, start in enumerate(range(0, len(shown), PAIRS_PER_PAGE), 1):
        cells = []
        for pair in shown[start:start + PAIRS_PER_PAGE]:
            cells += [(str(pair), thumbnail(card_key("feature", pair.a))), ("", thumbnail(card_key("feature", pair.b)))]
        contact_sheet(cells, 2, BUILD / f"pairs-{page:02d}.png")


def review_sheets() -> None:
    """Every card at phone size, by region in study order: what the user signs off."""
    from geofeat.curriculum import load_curriculum
    from geofeat.countries_ne import state_ids
    from geofeat.order import frames
    from geofeat.order.inputs import feature_frames, ordering

    result = ordering()
    regions = {k: f.region for k, f in feature_frames(frames.load(), load_curriculum(state_ids())).items()}
    sheets: dict[str, list[tuple[str, str]]] = {}
    for position, card in enumerate(result.cards, 1):
        name = "orientation" if card.study_pass == "orientation" else f"{int(card.region or regions[card.key]):02d}"
        sheets.setdefault(name, []).append((f"{position} {card.key}: {' / '.join(card.answer_lines)}", card.key))
    for old in BUILD.glob("review-[0-9o]*.png"):
        old.unlink()
    for name, cells in sheets.items():  # one sheet's thumbnails in memory at a time
        contact_sheet([(label, thumbnail(key, PHONE_W)) for label, key in cells], REVIEW_COLUMNS, BUILD / f"review-{name}.png")


def out_name(args: list[str], default: str | None) -> tuple[str | None, list[str]]:
    if args[:1] != ["--out"]:
        return default, args
    if len(args) < 2 or not OUT_NAME.fullmatch(args[1]):
        sys.exit(f"--out must be a bare name like cluster.png, got {args[1:2]}")
    return args[1], args[2:]


def main() -> None:
    args = sys.argv[1:]
    if args == ["--pairs"]:
        pairs_sheet()
        return
    if args == ["--review"]:
        review_sheets()
        return
    phone = args[:1] == ["--phone"]
    out, patterns = out_name(args[1:] if phone else args, None if phone else "sheet.png")
    rendered = sorted(_media())
    try:
        keys = match_keys(patterns, rendered) if patterns else rendered
    except ValueError as exc:
        sys.exit(f"{exc} among the rendered cards")
    if not phone:
        contact_sheet([(k, thumbnail(k)) for k in keys], 4, BUILD / out)
    elif out:
        contact_sheet([(k, thumbnail(k, PHONE_W)) for k in keys], 4, BUILD / out)
    else:
        for old in BUILD.glob("phone-*.png"):
            old.unlink()
        for page, start in enumerate(range(0, len(keys), PHONE_PER_PAGE), 1):
            contact_sheet([(k, thumbnail(k, PHONE_W)) for k in keys[start:start + PHONE_PER_PAGE]], 4,
                          BUILD / f"phone-{page:02d}.png")


if __name__ == "__main__":
    main()
