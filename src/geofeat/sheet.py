"""Contact sheets for visual QA, written to build/.

`sheet [--out NAME.png] [ids…]`: a grid of maps, every map by default.
`sheet --pairs`: every sibling pair side by side, labelled with its overlap scores.
"""

import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from geofeat.model import BUILD, DECK, MEDIA_INDEX, active, load_features
from geofeat.pairs import find_pairs
from geofeat.resolve import resolve

THUMB_W, THUMB_H, LABEL_H = 480, 270, 22
OUT_NAME = re.compile(r"^[a-z0-9-]+\.png$")


def card_image(feature_id: str) -> Image.Image:
    media = json.loads(MEDIA_INDEX.read_text())
    return Image.open(DECK / media[feature_id]).convert("RGB")


def contact_sheet(cells: list[tuple[str, Image.Image]], columns: int, out: Path) -> None:
    rows = math.ceil(len(cells) / columns)
    sheet = Image.new("RGB", (columns * THUMB_W, max(rows, 1) * (THUMB_H + LABEL_H)), "white")
    draw = ImageDraw.Draw(sheet)
    for i, (label, image) in enumerate(cells):
        x, y = (i % columns) * THUMB_W, (i // columns) * (THUMB_H + LABEL_H)
        sheet.paste(image.resize((THUMB_W, THUMB_H), Image.Resampling.LANCZOS), (x, y + LABEL_H))
        draw.text((x + 6, y + 4), label, fill="black")
    sheet.save(out)
    print(out)


def pairs_sheet() -> None:
    geometries = {f.id: (f, resolve(f)) for f in active(load_features())}
    cells = []
    for pair in sorted(find_pairs(geometries), key=lambda p: (not p.flagged, not p.nested)):
        print(pair)
        cells += [(str(pair), card_image(pair.a)), ("", card_image(pair.b))]
    contact_sheet(cells, 4, BUILD / "pairs.png")


def main() -> None:
    args = sys.argv[1:]
    if args == ["--pairs"]:
        pairs_sheet()
        return
    out = "sheet.png"
    if args[:1] == ["--out"]:
        out, args = args[1], args[2:]
        if not OUT_NAME.fullmatch(out):
            sys.exit(f"--out must be a bare name like cluster.png, got {out!r}")
    ids = args or sorted(json.loads(MEDIA_INDEX.read_text()))
    contact_sheet([(i, card_image(i)) for i in ids], 4, BUILD / out)


if __name__ == "__main__":
    main()
