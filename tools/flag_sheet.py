"""World Flags' contact sheets, for review: every flag in deck order, one JPEG per continent (build/flags-NN.jpg), each
flag numbered with its place in the deck and named as its card's back is.

usage: make flag-sheets    (or: uv run --with resvg-py==0.5.0 python tools/flag_sheet.py)

resvg rasterises the SVGs; it isn't a project dependency, since only this review tool needs it and a change to uv.lock
re-renders every map."""

import io

import resvg_py
from PIL import Image, ImageDraw, ImageFont

from geofeat.model import BUILD
from geofeat.sources import flags

COLUMNS, CELL_W, FLAG_H, LABEL_H, PAD = 6, 320, 150, 48, 16
HEADER_H = 64
MAX_H = 8000


def rasterise(card) -> Image.Image:
    png = bytes(resvg_py.svg_to_bytes(svg_path=str(card.image), height=FLAG_H * 2))
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    image.thumbnail((CELL_W - 2 * PAD, FLAG_H), Image.Resampling.LANCZOS)
    return image


def page(continent: str, cells: list[tuple[int, str, Image.Image]]) -> Image.Image:
    rows = -(-len(cells) // COLUMNS)
    height = HEADER_H + rows * (FLAG_H + LABEL_H + PAD)
    if height > MAX_H:
        raise SystemExit(f"{continent}: the sheet would be {height} px tall")
    sheet = Image.new("RGB", (COLUMNS * CELL_W, height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((PAD, 14), f"{continent.replace('-', ' ').title()} ({len(cells)})", fill="black",
              font=ImageFont.load_default(size=32))
    font = ImageFont.load_default(size=17)
    for i, (number, name, image) in enumerate(cells):
        x = (i % COLUMNS) * CELL_W + PAD
        y = HEADER_H + (i // COLUMNS) * (FLAG_H + LABEL_H + PAD)
        top = y + FLAG_H - image.height  # flags sit on a common baseline
        sheet.paste(image, (x, top), image)
        draw.rectangle((x - 1, top - 1, x + image.width, top + image.height), outline=(160, 160, 160))
        draw.text((x, y + FLAG_H + 6), f"{number}. {name}", fill="black", font=font)
    return sheet


def main() -> None:
    cards = flags.cards()
    for old in BUILD.glob("flags-*.jpg"):
        old.unlink()
    BUILD.mkdir(exist_ok=True)
    numbered = list(enumerate(cards, 1))
    for n, continent in enumerate(flags.CONTINENTS, 1):
        cells = [(i, c.answer_lines[0], rasterise(c)) for i, c in numbered if f"continent::{continent}" in c.tags]
        out = BUILD / f"flags-{n:02d}.jpg"
        page(continent, cells).save(out, quality=90)
        print(out)


if __name__ == "__main__":
    main()
