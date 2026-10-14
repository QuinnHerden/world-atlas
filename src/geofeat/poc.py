"""Countries PoC: a separate 9-card deck testing country and capital cards, built from data/poc-countries.yaml.

Each capital entry gives two cards: the country outlined (back: its name) and its capital as a dot with the country
as context (back: the capital). A city entry gives the dot card only. Writes the deck to build/poc/, and contact
sheets of every front to build/poc-sheet.png and, 390 px wide, build/poc-phone.png.
"""

import hashlib
import html
import sys
import unicodedata
from typing import Annotated, Literal

import shapely
from PIL import Image
from pydantic import Field, model_validator
from ruamel.yaml import YAML
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry

from geofeat.model import BUILD, ROOT, CardText, Expect, Feature, Part, Strict, load_features
from geofeat.resolve import layer
from geofeat.render import render
from geofeat.sheet import PHONE_W, THUMB_W, contact_sheet

DATA = ROOT / "data/poc-countries.yaml"
OUT = BUILD / "poc"
BBox = tuple[float, float, float, float]  # lon_min, lat_min, lon_max, lat_max; unlike features.yaml, never across 180°
Uid = Annotated[str, Field(pattern=r"^[A-Za-z0-9]{10}$")]


class Place(Strict):
    name: CardText
    ne_id: int
    expect: BBox
    mainland: BBox | None = None  # keep only the polygons inside this box


class Entry(Strict):
    id: str
    kind: Literal["capital", "city"]
    country: Place
    city: Place
    uids: dict[Literal["country", "city"], Uid]

    @model_validator(mode="after")
    def _cards(self) -> "Entry":
        needed = {"country", "city"} if self.kind == "capital" else {"city"}
        if set(self.uids) != needed:
            raise ValueError(f"{self.id}: a {self.kind} entry needs uids for exactly {sorted(needed)}")
        return self


def _select(name: str, place: Place) -> BaseGeometry:
    gdf = layer(name)
    rows = gdf[gdf["ne_id"] == place.ne_id]
    if len(rows) != 1:
        raise ValueError(f"{place.name}: {name} ne_id {place.ne_id} matched {len(rows)} rows")
    geometry = rows.geometry.iloc[0]
    if place.mainland:
        geometry = shapely.union_all([p for p in shapely.get_parts(geometry) if box(*place.mainland).contains(p)])
    if not box(*place.expect).contains(geometry):
        raise ValueError(f"{place.name}: geometry {geometry.bounds} falls outside expected bbox {place.expect}")
    return geometry


def _feature(entry: Entry) -> Feature:
    """A stand-in Feature, so the main renderer and framing draw the country. Only its id, type and frame are read."""
    return Feature(
        id=entry.id, name=entry.country.name, type="Region", category="Regions & Rifts", tier=1, style="area",
        geometry=[Part(layer="10m_admin_0_countries", select={"ne_id": entry.country.ne_id})],
        expect=Expect(bbox=entry.country.expect),
    )


def cards(entry: Entry) -> list[tuple[str, str, str, bytes]]:
    """(uid, prompt, answer, png) for each of the entry's cards."""
    shape = _select("10m_admin_0_countries", entry.country)
    city = _select("10m_populated_places", entry.city)
    out = []
    if entry.kind == "capital":
        png = render(_feature(entry), shape, country="subject")
        out.append((entry.uids["country"], "Country", entry.country.name, png))
    prompt = "Capital" if entry.kind == "capital" else "City"
    png = render(_feature(entry), shape, country="context", dot=(city.x, city.y))
    out.append((entry.uids["city"], prompt, f"{entry.city.name} ({entry.country.name})", png))
    return out


def _note(uid: str, prompt: str, answer: str, image: str, entry: Entry) -> str:
    tags = [f"kind::{prompt.lower()}", f"id_{entry.id}"]
    footnotes = "".join(f"[^tag]: {tag}\n" for tag in tags)
    return f"---\n\n**{prompt}**<br>![]({image}) ::: {html.escape(answer)}\n\n---\n[^uid]: {uid}\n{footnotes}"


def _cell(png_path, label: str, width: int) -> tuple[str, Image.Image]:
    label = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()  # the sheet's bitmap font is ASCII
    image = Image.open(png_path).convert("RGB")
    return label, image.resize((width, round(width * image.height / image.width)), Image.Resampling.LANCZOS)


def main() -> None:
    deck_name = sys.argv[1]
    entries = [Entry.model_validate(e) for e in YAML(typ="safe").load(DATA)]
    uids = [uid for e in entries for uid in e.uids.values()] + [f.uid for f in load_features() if f.uid]
    if duplicates := {u for u in uids if uids.count(u) > 1}:
        raise SystemExit(f"uids used twice, here or in features.yaml: {sorted(duplicates)}")
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.iterdir():
        old.unlink()
    notes, shown = [], []
    for entry in entries:
        for uid, prompt, answer, png in cards(entry):
            image = f"{hashlib.sha256(png).hexdigest()[:12]}.png"
            (OUT / image).write_bytes(png)
            notes.append(_note(uid, prompt, answer, image, entry))
            shown.append((OUT / image, f"{prompt} -> {answer}"))
            print(f"rendered {entry.id} {prompt.lower()} -> {image}")
    (OUT / "poc-countries.md").write_text(f"---\ndeck: \"{deck_name}\"\n---\n" + "\n".join(notes))
    contact_sheet([_cell(p, label, THUMB_W * 2) for p, label in shown], 2, BUILD / "poc-sheet.png")
    contact_sheet([_cell(p, label, PHONE_W) for p, label in shown], 2, BUILD / "poc-phone.png")


if __name__ == "__main__":
    main()
