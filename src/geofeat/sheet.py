"""Contact sheet: every rendered map in one image, labelled with its feature id, for visual QA."""

import json
import math
import sys

from PIL import Image, ImageDraw

from geofeat.model import BUILD, DECK, MEDIA_INDEX

THUMB_W, THUMB_H, LABEL_H, COLUMNS = 480, 270, 22, 4


def main() -> None:
    media = json.loads(MEDIA_INDEX.read_text())
    ids = sys.argv[1:] or sorted(media)
    rows = math.ceil(len(ids) / COLUMNS)
    sheet = Image.new("RGB", (COLUMNS * THUMB_W, rows * (THUMB_H + LABEL_H)), "white")
    draw = ImageDraw.Draw(sheet)
    for i, feature_id in enumerate(ids):
        x, y = (i % COLUMNS) * THUMB_W, (i // COLUMNS) * (THUMB_H + LABEL_H)
        thumb = Image.open(DECK / media[feature_id]).convert("RGB").resize((THUMB_W, THUMB_H))
        sheet.paste(thumb, (x, y + LABEL_H))
        draw.text((x + 6, y + 4), feature_id, fill="black")
    out = BUILD / "sheet.png"
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
