"""Write the PDF guide: every active card in the new-card study order (data/positions.lock), so entry N is card N in
Anki. Orientation first, then pass 1 and pass 2, each by region in ring order, with a linked contents page and PDF
bookmarks. `python -m geofeat.guide --region NN` writes one region's pass 1 and pass 2 entries only."""

import argparse
import io
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, Image, KeepTogether, NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer,
    Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

import geofeat.positions as positions
from geofeat.card import Card, Pass, load_media
from geofeat.model import BUILD, DECK, ROOT, ROOT_DECK

TITLE = f"{ROOT_DECK} — Study Guide"
RESEARCH_AS_OF = "2026-10-12"  # the research the notes were drawn from (docs/research/)
IMAGE_PX = 800  # 62% of the A4 text width is ~10.5 cm: ~195 dpi
JPEG_QUALITY = 82
SIZE_BUDGET = 80_000_000  # bytes; docs/world-atlas-plan.md


def out_path(region: int | None = None) -> Path:
    """The one place the guide's file name is decided: named after the deck, e.g. build/world-atlas-guide.pdf, or
    build/world-atlas-guide-04.pdf for one region."""
    name = re.sub(r"[^a-z0-9]+", "-", ROOT_DECK.lower()).strip("-") + "-guide"
    return BUILD / (f"{name}.pdf" if region is None else f"{name}-{region:02d}.pdf")


@dataclass(frozen=True)
class Entry:
    number: int  # the card's place in the new-card order, from 1: Anki shows it Nth
    card: Card


@dataclass
class Section:
    study_pass: Pass
    region: int | None  # None for orientation
    entries: list[Entry]


def entries(cards: list[Card], lock: dict[str, int]) -> list[Entry]:
    """The active cards in lock order, numbered as Anki introduces them. Retired uids in the lock take no number."""
    if missing := sorted(c.key for c in cards if c.uid not in lock):
        raise SystemExit(f"cards not in {positions.LOCK_FILE.name} (run `make positions`): {missing}")
    return [Entry(n, c) for n, c in enumerate(sorted(cards, key=lambda c: lock[c.uid]), 1)]


def sections(ordered: list[Entry], region_of: Callable[[Card], int]) -> list[Section]:
    """Runs of one pass and region, in ring order. A card can sit outside its own region: the order engine moves a
    parent to just before its earliest child (a waiver), and once the lock is frozen a card whose region or pass
    changes keeps its old slot. So the sections are the heaviest chain of runs (by card count) whose pass and region
    never go back in ring order, and every other run joins the next section after it, where Anki shows it."""
    runs: list[Section] = []
    for entry in ordered:
        c = entry.card
        study, region = c.study_pass, None if c.study_pass == "orientation" else region_of(c)
        if runs and (runs[-1].study_pass, runs[-1].region) == (study, region):
            runs[-1].entries.append(entry)
        else:
            runs.append(Section(study, region, [entry]))
    # best[i]: the most cards a non-decreasing chain ending at run i holds; ties go to the later predecessor
    best, previous = [0] * len(runs), [-1] * len(runs)
    for i, run in enumerate(runs):
        for j in range(i):
            if _rank(runs[j]) <= _rank(run) and (previous[i] < 0 or best[j] >= best[previous[i]]):
                previous[i] = j
        best[i] = len(run.entries) + (best[previous[i]] if previous[i] >= 0 else 0)
    chain, i = set(), max(range(len(runs)), key=lambda k: (best[k], k), default=-1)
    while i >= 0:
        chain.add(i)
        i = previous[i]
    out: list[Section] = []
    stray: list[Entry] = []
    for i, run in enumerate(runs):
        if i not in chain:
            stray += run.entries
        elif out and _rank(out[-1]) == _rank(run):  # a section a stray run cut in two
            out[-1].entries += stray + run.entries
            stray = []
        else:
            out.append(Section(run.study_pass, run.region, stray + run.entries))
            stray = []
    if stray:  # strays after the last section join it
        out[-1].entries += stray
    return out


def _rank(section: Section) -> tuple[int, int]:
    return (0, 0) if section.study_pass == "orientation" else (int(section.study_pass), section.region or 0)


def pass_title(study: Pass) -> str:
    return "Orientation" if study == "orientation" else f"Pass {study}"


def register_fonts() -> None:
    """DejaVu ships with matplotlib and, unlike the built-in Helvetica, covers names like Øresund and Ṭāriq."""
    font_dir = Path(matplotlib.get_data_path()) / "fonts/ttf"
    for name, file in [("Sans", "DejaVuSans"), ("Sans-Bold", "DejaVuSans-Bold"), ("Sans-Oblique", "DejaVuSans-Oblique")]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir / f"{file}.ttf")))
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans-Oblique")


INK = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#5f6b7a")
RULE = colors.HexColor("#d5dae0")
S = {
    "title": ParagraphStyle("title", fontName="Sans-Bold", fontSize=30, leading=38, alignment=TA_CENTER,
                            textColor=INK),
    "cover": ParagraphStyle("cover", fontName="Sans", fontSize=14, leading=22, alignment=TA_CENTER,
                            textColor=MUTED),
    "h1": ParagraphStyle("h1", fontName="Sans-Bold", fontSize=22, leading=28, spaceAfter=4, textColor=INK),
    "h2": ParagraphStyle("h2", fontName="Sans-Bold", fontSize=16, leading=21, spaceBefore=10, spaceAfter=2, textColor=INK),
    "range": ParagraphStyle("range", fontName="Sans", fontSize=10, leading=13, spaceAfter=6, textColor=MUTED),
    "meta": ParagraphStyle("meta", fontName="Sans", fontSize=9.5, leading=12, spaceAfter=3, textColor=MUTED),
    "answer": ParagraphStyle("answer", fontName="Sans-Bold", fontSize=13, leading=16, textColor=INK),
    "answer2": ParagraphStyle("answer2", fontName="Sans", fontSize=10.5, leading=13.5, textColor=MUTED),
    "note": ParagraphStyle("note", fontName="Sans", fontSize=10, leading=14, spaceBefore=6, textColor=INK),
    "toc0": ParagraphStyle("toc0", fontName="Sans-Bold", fontSize=11, leading=15, spaceBefore=8, textColor=INK),
    "toc1": ParagraphStyle("toc1", fontName="Sans", fontSize=9.5, leading=12.5, leftIndent=14, textColor=INK),
}


def _markdown(text: str, style: ParagraphStyle) -> Paragraph:
    """A paragraph with **bold** and *italic* rendered; plain escaped text if reportlab rejects the markup."""
    markup = re.sub(r"\*(.+?)\*", r"<i>\1</i>", re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape(text)))
    try:
        return Paragraph(markup, style)
    except ValueError:
        return Paragraph(escape(text), style)


def map_image(path: Path, width: float) -> Image:
    with PILImage.open(path) as source:
        px = min(IMAGE_PX, source.width)
        img = source.convert("RGB").resize((px, round(source.height * px / source.width)), PILImage.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True)
    buf.seek(0)
    return Image(buf, width=width, height=width * img.height / img.width)


class Bookmark(Spacer):
    """A zero-size marker: the doc template turns it into a named destination and an outline entry, and a TOC entry
    when `toc`."""

    def __init__(self, key: str, title: str, level: int, toc: bool = True):
        super().__init__(0, 0)
        self.key, self.title, self.level, self.toc = key, title, level, toc


class Guide(BaseDocTemplate):
    def __init__(self, path: Path, **kw):
        super().__init__(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                         bottomMargin=1.8 * cm, title=TITLE, subject=f"The {ROOT_DECK} cards in study order", **kw)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates([
            PageTemplate("cover", [frame]),
            PageTemplate("body", [frame], onPage=self._footer),
        ])
        self.bookmarks: list[str] = []  # keys in the order they were placed, for the tests

    def _footer(self, canv, doc) -> None:
        canv.saveState()
        canv.setFont("Sans", 8.5)
        canv.setFillColor(MUTED)
        canv.drawString(self.leftMargin, 1 * cm, TITLE)
        canv.drawRightString(self.leftMargin + self.width, 1 * cm, str(doc.page))
        canv.restoreState()

    def handle_documentBegin(self) -> None:
        self.bookmarks = []  # multiBuild lays the story out more than once
        super().handle_documentBegin()

    def afterFlowable(self, flowable) -> None:
        if isinstance(flowable, Bookmark):
            self.bookmarks.append(flowable.key)
            self.canv.bookmarkPage(flowable.key)
            self.canv.addOutlineEntry(flowable.title, flowable.key, level=flowable.level, closed=flowable.level > 0)
            if flowable.toc:
                self.notify("TOCEntry", (flowable.level, escape(flowable.title), self.page, flowable.key))


def entry_block(entry: Entry, image: Path, width: float, level: int) -> KeepTogether:
    c = entry.card
    image_w = width * 0.62
    text: list[Flowable] = [Paragraph(f"<b>{entry.number}</b> · {escape(c.prompt)}", S["meta"])]
    first, *rest = c.answer_lines
    text.append(Paragraph(escape(first), S["answer"]))
    text += [Paragraph(escape(line), S["answer2"]) for line in rest]
    if c.note:
        text.append(_markdown(c.note, S["note"]))
    table = Table([[map_image(image, image_w), text]], colWidths=[image_w, width - image_w])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE),
    ]))
    label = f"{entry.number}. {c.prompt}: {' / '.join(c.answer_lines)}"
    return KeepTogether([Bookmark(f"card-{c.uid}", label, level, toc=False), table])


def section_key(section: Section) -> str:
    return "orientation" if section.region is None else f"pass-{section.study_pass}-region-{section.region:02d}"


def story(parts: list[Section], names: dict[int, str], images: dict[str, Path], width: float,
          subtitle: str | None = None) -> list[Flowable]:
    total = sum(len(s.entries) for s in parts)
    cover = [Spacer(0, 7 * cm), Paragraph(escape(TITLE), S["title"]), Spacer(0, 1.2 * cm)]
    if subtitle:
        cover.append(Paragraph(escape(subtitle), S["cover"]))
    cover += [
        Paragraph(f"{total} cards in study order", S["cover"]),
        Paragraph(f"Research as of {RESEARCH_AS_OF}", S["cover"]),
        Paragraph(f"Built {date.today().isoformat()}", S["cover"]),
    ]
    out: list[Flowable] = [*cover, NextPageTemplate("body"), PageBreak(), Paragraph("Contents", S["h1"]),
                           TableOfContents(levelStyles=[S["toc0"], S["toc1"]], dotsMinLevel=0)]
    current_pass = None
    for section in parts:
        first, last = section.entries[0].number, section.entries[-1].number
        span = f"Card {first}" if first == last else f"Cards {first}–{last} · {len(section.entries)} cards"
        if section.study_pass != current_pass or section.study_pass != 2:  # pass 2's few cards run on
            out.append(PageBreak())
        if section.study_pass != current_pass:
            current_pass = section.study_pass
            title = pass_title(current_pass)
            out += [Bookmark(f"pass-{current_pass}", title, 0), Paragraph(escape(title), S["h1"])]
        if section.region is not None:
            title = f"{section.region:02d} · {names[section.region]}"
            out += [Bookmark(section_key(section), title, 1), Paragraph(escape(f"Region {title}"), S["h2"])]
        out.append(Paragraph(span, S["range"]))
        level = 1 if section.region is None else 2
        out += [entry_block(e, images[e.card.key], width, level) for e in section.entries]
    return out


def build(parts: list[Section], names: dict[int, str], images: dict[str, Path], out: Path,
          subtitle: str | None = None) -> Guide:
    register_fonts()
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = Guide(out)
    doc.multiBuild(story(parts, names, images, doc.width, subtitle))
    return doc


def load() -> tuple[list[Section], dict[int, str], dict[str, Path]]:
    """The real cards, in lock order and sectioned, with region names and rendered maps. Fails on a card that is
    unrendered, has no note, or whose note carries a research marker."""
    from geofeat.check import NOTE_MARKER
    from geofeat.countries_ne import state_ids
    from geofeat.curriculum import load_curriculum
    from geofeat.order import frames
    from geofeat.order.engine import _region, lookup
    from geofeat.order.inputs import feature_frames
    from geofeat.sources import all_cards

    cards = all_cards()
    media = load_media()
    if missing := sorted(c.key for c in cards if c.key not in media or not (DECK / media[c.key]).exists()):
        raise SystemExit(f"no rendered map for {missing}; run `make render` first")
    if missing := sorted(c.key for c in cards if not c.note):
        raise SystemExit(f"no note for {missing}")
    if marked := sorted(c.key for c in cards if NOTE_MARKER.search(c.note or "")):
        raise SystemExit(f"notes with research markers: {marked}; run `make check-data`")
    curriculum = load_curriculum(state_ids())
    frame_of = lookup(feature_frames(frames.load(), curriculum))

    def region_of(c: Card) -> int:
        return _region(c, frame_of)  # the engine's own rule, so sections match how the cards were ordered

    parts = sections(entries(cards, positions.read().positions), region_of)
    for section in parts:
        for e in section.entries:
            if e.card.study_pass != section.study_pass or (section.region and region_of(e.card) != section.region):
                print(f"card {e.number} ({e.card.key}) sits in {pass_title(section.study_pass)}, region "
                      f"{section.region}, outside its own; the guide shows it where Anki does")
    return parts, {r.number: r.name for r in curriculum.regions}, {k: DECK / v for k, v in media.items()}


def main() -> None:
    parser = argparse.ArgumentParser(prog="geofeat.guide", description=__doc__)
    parser.add_argument("--region", type=int, help="only the entries this ring region's sections hold, pass 1 and "
                        "pass 2; a card the study order placed in another region is in that region's guide")
    args = parser.parse_args()
    parts, names, images = load()
    subtitle = None
    if args.region is not None:
        if args.region not in names:
            raise SystemExit(f"no region {args.region}; the ring has {min(names)}-{max(names)}")
        parts = [s for s in parts if s.region == args.region]
        if not parts:
            raise SystemExit(f"region {args.region} has no cards")
        subtitle = f"Region {args.region:02d} · {names[args.region]}"
    out = out_path(args.region)
    doc = build(parts, names, images, out, subtitle)
    print(f"wrote {out.relative_to(ROOT)}: {sum(len(s.entries) for s in parts)} cards, {doc.page} pages, "
          f"{out.stat().st_size / 1e6:.1f} MB")
    if out.stat().st_size > SIZE_BUDGET:
        print(f"warning: over the {SIZE_BUDGET / 1e6:.0f} MB budget; lower IMAGE_PX or JPEG_QUALITY")


if __name__ == "__main__":
    main()
