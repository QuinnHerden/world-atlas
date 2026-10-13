"""Contact sheets for visual QA, written to build/.

`sheet [--out NAME.png] [ids…]`: a grid of maps, every map by default.
`sheet --phone [ids…]`: the same at phone size, PHONE_W px wide per map, PHONE_PER_PAGE to a page (build/phone-NN.png).
`sheet --pairs`: flagged, nested, allowed and near-threshold sibling pairs side by side, labelled with their overlap
scores, PAIRS_PER_PAGE to a page (build/pairs-NN.png); every pair goes to build/pairs.log.
"""

import json
import math
import re
import sys
from functools import cache
from pathlib import Path

from PIL import Image, ImageDraw

from geofeat.model import BUILD, DECK, MEDIA_INDEX, active, load_features
from geofeat.pairs import find_pairs
from geofeat.resolve import resolve

THUMB_W, THUMB_H, LABEL_H = 480, 270, 22
OUT_NAME = re.compile(r"^[a-z0-9-]+\.png$")
PAIRS_PER_PAGE = 50
PHONE_W, PHONE_PER_PAGE = 390, 48  # a phone screen's width in CSS px


@cache
def _media() -> dict[str, str]:
    return json.loads(MEDIA_INDEX.read_text())


def card_image(feature_id: str) -> Image.Image:
    return Image.open(DECK / _media()[feature_id]).convert("RGB")


def thumbnail(feature_id: str, width: int = THUMB_W) -> Image.Image:
    """A card shrunk to sheet size on load, so a sheet of hundreds of maps doesn't hold them all at full size."""
    image = card_image(feature_id)
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
            cells += [(str(pair), thumbnail(pair.a)), ("", thumbnail(pair.b))]
        contact_sheet(cells, 2, BUILD / f"pairs-{page:02d}.png")


def main() -> None:
    args = sys.argv[1:]
    if args == ["--pairs"]:
        pairs_sheet()
        return
    if args[:1] == ["--phone"]:
        ids = args[1:] or sorted(_media())
        for old in BUILD.glob("phone-*.png"):
            old.unlink()
        for page, start in enumerate(range(0, len(ids), PHONE_PER_PAGE), 1):
            cells = [(i, thumbnail(i, PHONE_W)) for i in ids[start:start + PHONE_PER_PAGE]]
            contact_sheet(cells, 4, BUILD / f"phone-{page:02d}.png")
        return
    out = "sheet.png"
    if args[:1] == ["--out"]:
        out, args = args[1], args[2:]
        if not OUT_NAME.fullmatch(out):
            sys.exit(f"--out must be a bare name like cluster.png, got {out!r}")
    ids = args or sorted(_media())
    contact_sheet([(i, thumbnail(i)) for i in ids], 4, BUILD / out)


if __name__ == "__main__":
    main()
