"""Write build/guide.pdf: every active card with its map and its note on why it matters."""

import io
import re
from datetime import date
from pathlib import Path
from typing import get_args
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
    BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from geofeat.card import load_media
from geofeat.model import BUILD, DECK, ROOT, Category, Feature, active, load_features
from geofeat.sources import features as features_source

OUT = BUILD / "guide.pdf"
TITLE = "Geographic Features — Card Guide"
RESEARCH_AS_OF = "2026-10-12"  # docs/research/research-independent.md, where the notes in features.yaml come from
IMAGE_PX = 900
JPEG_QUALITY = 85


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
    "h1": ParagraphStyle("h1", fontName="Sans-Bold", fontSize=20, leading=26, spaceAfter=10, textColor=INK),
    "name": ParagraphStyle("name", fontName="Sans-Bold", fontSize=13, leading=16, textColor=INK),
    "alt": ParagraphStyle("alt", fontName="Sans", fontSize=10, leading=13, textColor=MUTED),
    "meta": ParagraphStyle("meta", fontName="Sans-Oblique", fontSize=9.5, leading=13, textColor=MUTED,
                           spaceBefore=3, spaceAfter=6),
    "note": ParagraphStyle("note", fontName="Sans", fontSize=10, leading=14, textColor=INK),
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


def map_image(path, width: float) -> Image:
    with PILImage.open(path) as source:
        img = source.convert("RGB").resize((IMAGE_PX, round(source.height * IMAGE_PX / source.width)), PILImage.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True)
    buf.seek(0)
    return Image(buf, width=width, height=width * img.height / img.width)


class Bookmark(Spacer):
    """A zero-size marker: the doc template turns it into a named destination, outline entry and TOC entry."""

    def __init__(self, key: str, title: str, level: int):
        super().__init__(0, 0)
        self.key, self.title, self.level = key, title, level


class Guide(BaseDocTemplate):
    def __init__(self, path, **kw):
        super().__init__(str(path), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                         bottomMargin=1.8 * cm, title=TITLE, subject="Card guide for the Geographic Features deck",
                         **kw)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates([
            PageTemplate("cover", [frame]),
            PageTemplate("body", [frame], onPage=self._footer),
        ])

    def _footer(self, canv, doc) -> None:
        canv.saveState()
        canv.setFont("Sans", 8.5)
        canv.setFillColor(MUTED)
        canv.drawString(self.leftMargin, 1 * cm, TITLE)
        canv.drawRightString(self.leftMargin + self.width, 1 * cm, str(doc.page))
        canv.restoreState()

    def afterFlowable(self, flowable) -> None:
        if isinstance(flowable, Bookmark):
            self.canv.bookmarkPage(flowable.key)
            self.canv.addOutlineEntry(flowable.title, flowable.key, level=flowable.level, closed=True)
            self.notify("TOCEntry", (flowable.level, escape(flowable.title), self.page, flowable.key))


def card_block(feature: Feature, media: dict[str, str], width: float) -> KeepTogether:
    image_w = width * 0.62
    text = [Paragraph(escape(feature.name), S["name"])]
    if feature.alt_names:
        text.append(Paragraph(escape(f"[{', '.join(feature.alt_names)}]"), S["alt"]))
    text.append(Paragraph(escape(f"{feature.type_text} · Tier {feature.tier}"), S["meta"]))
    text.append(_markdown(feature.note or "", S["note"]))
    table = Table([[map_image(DECK / media[features_source.key(feature)], image_w), text]], colWidths=[image_w, width - image_w])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE),
    ]))
    return KeepTogether([Bookmark(f"card-{feature.id}", feature.name, 1), table])


def main() -> None:
    features = active(load_features())
    media = load_media()
    keys = {f.id: features_source.key(f) for f in features}
    unrendered = sorted(f.id for f in features if keys[f.id] not in media or not (DECK / media[keys[f.id]]).exists())
    if unrendered:
        raise SystemExit(f"no rendered map for {unrendered}; run `make render` first")
    if missing := sorted(f.id for f in features if not f.note):
        raise SystemExit(f"no note for {missing}; add one in data/features.yaml")
    register_fonts()
    order = {c: i for i, c in enumerate(get_args(Category))}
    features.sort(key=lambda f: (order[f.category], f.tier, f.name.lower()))

    BUILD.mkdir(exist_ok=True)
    doc = Guide(OUT)
    toc = TableOfContents(levelStyles=[S["toc0"], S["toc1"]], dotsMinLevel=0)
    story = [
        Spacer(0, 7 * cm),
        Paragraph(escape(TITLE), S["title"]),
        Spacer(0, 1.2 * cm),
        Paragraph(f"{len(features)} cards in {len({f.category for f in features})} categories", S["cover"]),
        Paragraph(f"Research as of {RESEARCH_AS_OF}", S["cover"]),
        Paragraph(f"Built {date.today().isoformat()}", S["cover"]),
        NextPageTemplate("body"),
        PageBreak(),
        Paragraph("Contents", S["h1"]),
        toc,
    ]
    current = None
    for feature in features:
        if feature.category != current:
            current = feature.category
            count = sum(f.category == current for f in features)
            story += [
                PageBreak(),
                Bookmark(f"cat-{re.sub(r'[^a-z0-9]+', '-', current.lower())}", current, 0),
                Paragraph(f"{escape(current)} <font size=11 color='#5f6b7a'>· {count} cards</font>", S["h1"]),
            ]
        story.append(card_block(feature, media, doc.width))
    doc.multiBuild(story)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(features)} cards, {doc.page} pages, "
          f"{OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
