"""Draw each region's neighbour walk for review: build/walks-NN.png and build/walks-NN.txt, one per ring region, and
build/walks-ring.png, the 21 regions in ring order with the crossings between them.

usage: uv run python tools/walk_maps.py [REGION ...]   (slugs or numbers; default every region, plus the ring)

Each map outlines the region's countries and numbers the walk nodes in walk order at a point inside each (offset with
a leader line where the country is too small to hold the label). Steps between bordering countries are solid arrows,
jumps (consecutive countries with no adjacency edge) dashed orange ones. Pockets (microstates, territories and
disputes, which sit in a host's run) are markers. The side panel, and the .txt in full, lists every card of the
region in study order, block by block (countries, features, capitals and cities; ADR 0009). Approve a walk, then freeze
it with tools/freeze_walks.py.
"""

import math
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
from matplotlib.patches import FancyArrowPatch, PathPatch  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from pyproj import Transformer  # noqa: E402
from shapely.geometry import MultiPolygon, Point, Polygon, box  # noqa: E402
from shapely.geometry.base import BaseGeometry  # noqa: E402
from shapely.ops import polylabel  # noqa: E402

from geofeat import adjacency  # noqa: E402
from geofeat.card import BLOCKS, Card  # noqa: E402
from geofeat.countries_ne import outline, state_ids  # noqa: E402
from geofeat.curriculum import Region, load_curriculum  # noqa: E402
from geofeat.model import BUILD  # noqa: E402
from geofeat.order import frames  # noqa: E402
from geofeat.order.engine import Ordering, RegionReport  # noqa: E402
from geofeat.order.inputs import feature_frames, ordering  # noqa: E402
from geofeat.polities import load_political  # noqa: E402

DPI = 110
PAD_DEG = 15.0  # context drawn round a region's extent
SMALL = 0.02  # a country whose main part spans less than this share of the map gets an offset label
LAND, NODE, OCEAN, EDGE = "#ebe7df", "#f6e7c1", "#dfeaf2", "#5b5b5b"
STEP, JUMP = "#1f4e8c", "#d9730d"
ENTRY, EXIT, NUMBER = "#2e7d32", "#b23a48", "#1f4e8c"
KIND_COLOUR = {"country": "#1a1a1a", "capital": "#6b6b6b", "feature": "#2e7d32", "city": "#7b3fa0",
               "territory": "#8a5a00", "dispute": "#b23a48"}
MARKERS = {"pocket": "s", "territory": "D", "dispute": "X"}


# Geometry


def main_part(g: BaseGeometry) -> Polygon:
    parts = [p for p in getattr(g, "geoms", [g]) if isinstance(p, Polygon)]
    return max(parts, key=lambda p: p.area)


def wrap(g: BaseGeometry, west: float) -> BaseGeometry:
    """`g` with its longitudes moved into [west, west + 360), cut where it crosses the seam."""
    pieces = []
    for shift in (-360.0, 0.0, 360.0):
        lo, hi = west - shift, west + 360.0 - shift
        if lo >= 180.0 or hi <= -180.0:
            continue
        piece = shapely.clip_by_rect(g, max(lo, -180.0), -90.0, min(hi, 180.0), 90.0)
        if not piece.is_empty:
            pieces.append(shapely.transform(piece, lambda c, s=shift: c + [s, 0.0]))
    return shapely.union_all(pieces) if len(pieces) > 1 else (pieces[0] if pieces else g)


def circular_mean(lons: Iterable[float]) -> float:
    rad = np.radians(list(lons))
    return math.degrees(math.atan2(np.sin(rad).mean(), np.cos(rad).mean()))


def patch(ax: plt.Axes, g: BaseGeometry, **kw) -> None:
    """Draw a polygonal geometry as one compound path."""
    verts, codes = [], []
    for poly in (g.geoms if hasattr(g, "geoms") else [g]):
        if not isinstance(poly, Polygon) or poly.is_empty:
            continue
        for ring in (poly.exterior, *poly.interiors):
            xy = np.asarray(ring.coords)
            verts.append(xy)
            codes.append([MplPath.MOVETO] + [MplPath.LINETO] * (len(xy) - 2) + [MplPath.CLOSEPOLY])
    if verts:
        ax.add_patch(PathPatch(MplPath(np.concatenate(verts), np.concatenate(codes)), **kw))


@dataclass
class Frame:
    """A region's map: an azimuthal equal-area projection centred on it, and the lon/lat window drawn."""

    west: float
    to_xy: Transformer
    window: BaseGeometry

    def project(self, g: BaseGeometry) -> BaseGeometry:
        g = shapely.intersection(wrap(g, self.west), self.window)
        return shapely.transform(g, lambda c: np.column_stack(self.to_xy.transform(c[:, 0], c[:, 1])))

    def point(self, lon: float, lat: float) -> tuple[float, float]:
        return self.to_xy.transform(lon, lat)


def region_frame(mains: Sequence[BaseGeometry]) -> Frame:
    lon0 = circular_mean(p.centroid.x for p in mains)
    west = lon0 - 180.0
    bounds = np.array([wrap(p, west).bounds for p in mains])
    lo, hi = bounds[:, 0].min(), bounds[:, 2].max()
    s, n = bounds[:, 1].min(), bounds[:, 3].max()
    lat0 = (s + n) / 2
    to_xy = Transformer.from_crs("EPSG:4326", f"+proj=laea +lon_0={(lo + hi) / 2} +lat_0={lat0} +datum=WGS84",
                                 always_xy=True)
    window = box(max(lo - PAD_DEG, west), max(s - PAD_DEG, -89.0), min(hi + PAD_DEG, west + 360.0), min(n + PAD_DEG, 89.0))
    return Frame(west, to_xy, window)


# Inputs


@dataclass
class Atlas:
    ordering: Ordering
    adjacency: dict[str, set[str]]
    shapes: dict[str, BaseGeometry]  # every state, territory and dispute, in lon/lat
    names: dict[str, str]
    disputes: set[str]
    touches: dict[str, tuple[str, ...]]  # feature id -> the countries that frame it, as the engine places it
    segments: list[tuple[Card, str, int, bool]]  # card, block, region, moved there by parent-first


def load() -> Atlas:
    o = ordering()
    countries, others = load_political()
    names = {c.id: c.name for c in countries} | {t.id: t.name for t in others}
    shapes = {i: outline(i) for i in names}
    facts = frames.load()
    curriculum = load_curriculum(state_ids())
    segments = []
    for block in BLOCKS[1:]:  # continents and the orientation features have no region
        cards = [c for c in o.cards if c.block == block and c.study_pass != "orientation"]
        natural = [facts.features[c.id].region if c.kind == "feature" else int(c.region) for c in cards]
        # Regions run in order within a block, round the ring once (twice for features: the tier-3 ones go round
        # again); a parent feature moved before its child (into an earlier region) is the only card out of place,
        # and the cards after it say where it now sits.
        laps = [int(c.kind == "feature" and c.study_pass == 2) for c in cards]
        keys = [lap * 100 + n for lap, n in zip(laps, natural)]
        actual = list(np.minimum.accumulate(keys[::-1])[::-1]) if keys else []
        segments += [(c, block, a % 100, a != k) for c, a, k in zip(cards, actual, keys)]
    disputes = {t.id for t in others if t.kind == "dispute"}
    return Atlas(o, adjacency.neighbours(adjacency.graph()), shapes, names, disputes,
                 {k.removeprefix("feature:"): f.countries for k, f in feature_frames(facts, curriculum).items()}, segments)


# The card list


def card_line(c: Card, atlas: Atlas, region: Region, walk_no: dict[str, int], moved: bool) -> str:
    name = c.answer_lines[0]
    if c.kind == "country" and c.id in walk_no:
        text = f"#{walk_no[c.id]} {name}"
    elif c.kind == "country" and c.id in region.pockets:
        text = f"{name} (pocket in {atlas.names[region.pockets[c.id]]})"
    elif c.kind == "capital":
        text = f"{name}, capital"
    elif c.kind in ("territory", "dispute") and c.id in region.placed():
        text = f"{name} ({c.kind}, beside {atlas.names[region.placed()[c.id]]})"
    elif c.kind == "feature":
        touches = ", ".join(atlas.names.get(t, t) for t in atlas.touches.get(c.id, ())) or "no country"
        text = f"{name} [{c.prompt.lower()}; frames {touches}]"
    elif c.kind == "city":
        text = f"{name}, {c.answer_lines[1]}" + (f" (after {c.anchor.removeprefix('feature:')})" if c.anchor else "")
    else:
        text = name
    return text + (" (parent moved here)" if moved else "")


def region_cards(atlas: Atlas, number: int) -> dict[str, list[tuple[Card, bool]]]:
    out: dict[str, list[tuple[Card, bool]]] = {b: [] for b in BLOCKS[1:]}
    for c, block, region, moved in atlas.segments:
        if region == number:
            out[block].append((c, moved))
    return out


def report_of(atlas: Atlas, number: int, study: int) -> RegionReport | None:
    return next((r for r in atlas.ordering.reports if r.region.number == number and r.study_pass == study), None)


def write_text(atlas: Atlas, region: Region, report: RegionReport) -> list[tuple[str, str]]:
    """The region's listing as (kind, line) pairs; also written to build/walks-NN.txt."""
    walk = report.walk
    walk_no = {n: i for i, n in enumerate(walk.nodes, 1)}
    jumps = {b for _, b in report.jumps}
    lines: list[tuple[str, str]] = []
    cards = region_cards(atlas, region.number)
    for block, title in (("countries", "Countries"), ("features", "Physical features"), ("cities", "Capitals and cities")):
        if not cards[block]:
            continue
        lines.append(("head", title))
        for i, (c, moved) in enumerate(cards[block], 1):
            mark = "  ⇢ jump" if c.kind == "country" and c.id in jumps else ""
            lines.append((c.kind, f"{i:3d}  {card_line(c, atlas, region, walk_no, moved)}{mark}"))
    head = [
        f"Region {region.number}: {region.name}",
        f"Entry {atlas.names[region.entry]}, exit {atlas.names[region.exit]}; "
        f"{'frozen' if walk.frozen else 'generated'} walk of {len(walk.nodes)} countries",
        "Walk: " + " → ".join(atlas.names[n] for n in walk.nodes),
        f"Jumps ({len(report.jumps)}): " + (", ".join(f"{atlas.names[a]} ⇢ {atlas.names[b]}" for a, b in report.jumps)
                                           or "none"),
        f"Frontier breaks ({len(report.breaks)}): " + (", ".join(atlas.names[b] for b in report.breaks) or "none"),
    ]
    waivers = [w for s in (1, 2) if (r := report_of(atlas, region.number, s)) for w in r.waivers]
    body = [line for _, line in lines]
    text = "\n".join(head + [""] + body + ([""] + ["Waivers:"] + [f"  {w}" for w in waivers] if waivers else []))
    (BUILD / f"walks-{region.number:02d}.txt").write_text(text + "\n")
    return lines


# Region map


def label_points(points: dict[str, tuple[float, float]], small: set[str], radius: float) -> dict[str, tuple[float, float]]:
    """Where each number goes: on its point, unless the country is small or the spot is taken, then nearby."""
    placed: dict[str, tuple[float, float]] = {}
    angles = [math.radians(a) for a in (45, 135, 315, 225, 90, 270, 0, 180, 20, 160, 340, 200)]
    for key in sorted(points, key=lambda k: k in small):
        x, y = points[key]
        candidates = [] if key in small else [(x, y)]
        candidates += [(x + r * radius * math.cos(a), y + r * radius * math.sin(a)) for r in (3.0, 4.5, 6.0, 8.0)
                       for a in angles]
        free = (p for p in candidates if all(math.dist(p, q) > 2.2 * radius for q in placed.values()))
        placed[key] = next(free, candidates[0])
    return placed


def draw_region(atlas: Atlas, region: Region, report: RegionReport) -> None:
    walk = report.walk
    pockets = {p: "pocket" for p in region.pockets} | {t: "territory" for t in region.territories} | \
        {d: "dispute" for d in region.disputes}
    members = [*walk.nodes, *pockets]
    frame = region_frame([main_part(atlas.shapes[n]) for n in members])
    projected_main = {n: main_part(frame.project(main_part(atlas.shapes[n]))) for n in members}
    xs = np.array([b for n in walk.nodes for b in projected_main[n].bounds]).reshape(-1, 2)
    for n in pockets:
        xs = np.vstack([xs, np.asarray(projected_main[n].bounds).reshape(2, 2)])
    (x0, y0), (x1, y1) = xs.min(axis=0), xs.max(axis=0)
    span = max(x1 - x0, y1 - y0)
    pad = 0.08 * span
    x0, x1, y0, y1 = x0 - pad, x1 + pad, y0 - pad, y1 + pad
    tolerance = span / 1500

    lines = write_text(atlas, region, report)
    map_h = 8.6  # inches; the map's width follows the region's shape, the panel's is fixed
    map_w = min(max(map_h * (x1 - x0) / (y1 - y0), 6.0), 12.5)
    if map_w == 12.5:  # wider than the page allows: grow the view vertically instead of squashing it
        extra = ((x1 - x0) * map_h / map_w - (y1 - y0)) / 2
        y0, y1 = y0 - extra, y1 + extra
    elif map_w == 6.0:
        extra = ((y1 - y0) * map_w / map_h - (x1 - x0)) / 2
        x0, x1 = x0 - extra, x1 + extra
    panel_w, margin = 6.6, 0.2
    width, height = map_w + panel_w + 3 * margin, map_h + 1.6
    fig = plt.figure(figsize=(width, height), dpi=DPI)
    ax = fig.add_axes((margin / width, 0.3 / height, map_w / width, map_h / height))
    panel = fig.add_axes(((map_w + 2 * margin) / width, 0.3 / height, panel_w / width, map_h / height))
    panel.axis("off")
    ax.set_facecolor(OCEAN)
    view = (x0 - span * 0.1, y0 - span * 0.1, x1 + span * 0.1, y1 + span * 0.1)

    member_set = set(members)
    for i, g in atlas.shapes.items():
        if i in pockets and pockets[i] != "pocket":
            continue
        if not frame.window.intersects(wrap(g, frame.west)):
            continue
        p = frame.project(g)
        p = shapely.clip_by_rect(p, *view).simplify(tolerance)
        if p.is_empty:
            continue
        if i in walk.nodes:
            patch(ax, p, facecolor=NODE, edgecolor=EDGE, linewidth=0.9, zorder=2)
        elif i in member_set:
            patch(ax, p, facecolor=NODE, edgecolor=EDGE, linewidth=0.6, zorder=3)
        elif i not in atlas.disputes:
            patch(ax, p, facecolor=LAND, edgecolor="#c9c4ba", linewidth=0.4, zorder=1)
    for i, kind in pockets.items():
        if kind != "pocket":
            p = frame.project(atlas.shapes[i]).simplify(tolerance)
            patch(ax, p, facecolor="none", edgecolor=KIND_COLOUR[kind], linewidth=0.8, linestyle=(0, (3, 2)), zorder=4)

    points = {n: polylabel(projected_main[n], tolerance=span / 2000).coords[0] for n in members}
    small = {n for n in walk.nodes if max(np.ptp(np.asarray(projected_main[n].exterior.coords), axis=0)) < SMALL * span}
    radius = 0.017 * span
    labels = label_points({n: points[n] for n in walk.nodes}, small, radius)

    jumps = set(report.jumps)
    for a, b in zip(walk.nodes, walk.nodes[1:]):
        jump = (a, b) in jumps
        ax.add_patch(FancyArrowPatch(
            labels[a], labels[b], arrowstyle="-|>,head_length=6,head_width=3.5", mutation_scale=1.6,
            color=JUMP if jump else STEP, linewidth=2.0 if jump else 1.5, linestyle=(0, (5, 3)) if jump else "-",
            shrinkA=11, shrinkB=11, connectionstyle="arc3,rad=0.12", alpha=0.9, zorder=6))
    for i, n in enumerate(walk.nodes, 1):
        lx, ly = labels[n]
        if (lx, ly) != points[n]:
            ax.plot([points[n][0], lx], [points[n][1], ly], color=EDGE, linewidth=0.7, zorder=7)
            ax.plot(*points[n], "o", markersize=2.5, color=EDGE, zorder=7)
        colour = ENTRY if n == region.entry else EXIT if n == region.exit else NUMBER
        ax.text(lx, ly, str(i), ha="center", va="center", fontsize=9, fontweight="bold", color="white", zorder=8,
                bbox=dict(boxstyle="circle,pad=0.25", facecolor=colour, edgecolor="white", linewidth=0.8))
        ax.annotate(atlas.names[n], (lx, ly), xytext=(0, -13), textcoords="offset points", ha="center", va="top",
                    fontsize=7, color="#333333", zorder=8)
    for i, kind in pockets.items():
        x, y = points[i]
        colour = KIND_COLOUR["country" if kind == "pocket" else kind]
        ax.plot(x, y, MARKERS[kind], markersize=6, markerfacecolor=colour, markeredgecolor="white", zorder=9)
        ax.annotate(atlas.names[i], (x, y), xytext=(5, 4), textcoords="offset points", fontsize=7, color=colour,
                    fontstyle="italic", zorder=9)

    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#999999")

    key = [
        plt.Line2D([], [], color=STEP, linewidth=1.5, marker=">", markersize=5, label="step to a neighbour"),
        plt.Line2D([], [], color=JUMP, linewidth=2, linestyle=(0, (5, 3)), marker=">", markersize=5,
                   label="jump (no adjacency edge)"),
        plt.Line2D([], [], color=ENTRY, marker="o", linestyle="", markersize=8, label="entry"),
        plt.Line2D([], [], color=EXIT, marker="o", linestyle="", markersize=8, label="exit"),
        *(plt.Line2D([], [], color=KIND_COLOUR["country" if k == "pocket" else k], marker=MARKERS[k], linestyle="",
                     markersize=6, label=k) for k in ("pocket", "territory", "dispute") if k in pockets.values()),
    ]
    ax.legend(handles=key, loc="lower left", fontsize=8, framealpha=0.9)

    fig.text(margin / width, 1 - 0.4 / height, f"{region.number}. {region.name}", fontsize=18, fontweight="bold", va="center")
    jump_text = ", ".join(f"{atlas.names[a]} ⇢ {atlas.names[b]}" for a, b in report.jumps) or "none"
    fig.text(margin / width, 1 - 0.8 / height, f"Entry {atlas.names[region.entry]}  →  exit {atlas.names[region.exit]}"
             f"   ·   {'frozen' if walk.frozen else 'generated'} walk, {len(walk.nodes)} countries",
             fontsize=10.5, va="center", color="#333333")
    fig.text(margin / width, 1 - 1.1 / height, f"{len(report.jumps)} jump(s): {jump_text}", fontsize=10.5,
             va="center", color=JUMP if report.jumps else "#333333")

    size = min(9.0, 640 / max(len(lines), 1))
    step = 1.0 / max(len(lines) + 1, 34)
    for i, (kind, text) in enumerate(lines):
        y = 1.0 - i * step
        if kind == "head":
            panel.text(0, y, text, fontsize=size + 1, fontweight="bold", va="top")
        else:
            text = text if len(text) <= 78 else text[:77] + "…"
            panel.text(0, y, text, fontsize=size, va="top", color=KIND_COLOUR[kind], family="DejaVu Sans Mono",
                       fontweight="bold" if kind == "country" else "normal")
    fig.savefig(BUILD / f"walks-{region.number:02d}.png", facecolor="white")
    plt.close(fig)


# The ring


def draw_ring(atlas: Atlas, regions: Sequence[Region]) -> None:
    west = -30.0
    fig, ax = plt.subplots(figsize=(18, 9.5), dpi=DPI)
    ax.set_facecolor(OCEAN)
    palette = [plt.get_cmap("tab20")(i) for i in (*range(0, 20, 2), *range(1, 20, 2))] + [plt.get_cmap("Set3")(10)]
    colour = {c: palette[(r.number - 1) % len(palette)] for r in regions for c in r.countries}
    shapes = {i: wrap(g.simplify(0.03), west) for i, g in atlas.shapes.items() if i not in atlas.disputes}
    for i, g in shapes.items():
        patch(ax, g, facecolor=colour.get(i, LAND), edgecolor="white", linewidth=0.3, zorder=2)

    def point(country: str) -> tuple[float, float]:
        return polylabel(main_part(shapes[country]), tolerance=0.1).coords[0]

    for r in regions:
        xs = [point(c) for c in r.countries if c not in r.pockets]
        x, y = np.mean([p[0] for p in xs]), np.mean([p[1] for p in xs])
        ax.text(x, y, str(r.number), ha="center", va="center", fontsize=11, fontweight="bold", zorder=6,
                bbox=dict(boxstyle="circle,pad=0.3", facecolor="white", edgecolor="#333333", linewidth=0.8))
    for r, nxt in zip(regions, [*regions[1:], regions[0]]):
        (ax_, ay), (bx, by) = point(r.exit), point(nxt.entry)
        land = nxt.entry in atlas.adjacency.get(r.exit, ())
        style = dict(color=STEP if land else JUMP, linewidth=1.8, linestyle="-" if land else (0, (5, 3)), zorder=5,
                     arrowstyle="-|>,head_length=7,head_width=4", shrinkA=3, shrinkB=3)
        if abs(bx - ax_) <= 180:
            ax.add_patch(FancyArrowPatch((ax_, ay), (bx, by), **style))
        else:  # across the map's seam: leave by one edge and come back by the other
            shift = 360.0 if bx < ax_ else -360.0
            ax.add_patch(FancyArrowPatch((ax_, ay), (bx + shift, by), **style))
            ax.add_patch(FancyArrowPatch((ax_ - shift, ay), (bx, by), **style))
        ax.plot([ax_, bx], [ay, by], "o", markersize=3, color="#222222", zorder=6)
    ax.set_xlim(west, west + 360)
    ax.set_ylim(-58, 84)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    names = "   ".join(f"{r.number} {r.name}" for r in regions)
    ax.set_title("The ring: 21 regions in study order, exit → next entry", fontsize=16, fontweight="bold", loc="left")
    key = [plt.Line2D([], [], color=STEP, linewidth=1.8, label="crossing over an adjacency edge"),
           plt.Line2D([], [], color=JUMP, linewidth=1.8, linestyle=(0, (5, 3)), label="open-water crossing (no edge)")]
    ax.legend(handles=key, loc="lower left", fontsize=9, framealpha=0.9)
    ax.text(0, -0.015, names, transform=ax.transAxes, fontsize=8.5, va="top", wrap=True, color="#333333")
    fig.savefig(BUILD / "walks-ring.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)


def main(argv: Sequence[str] = ()) -> None:
    regions = load_curriculum(state_ids()).regions
    by_name = {r.slug: r for r in regions} | {str(r.number): r for r in regions}
    if unknown := [a for a in argv if a not in by_name]:
        sys.exit(f"unknown regions: {', '.join(unknown)}")
    chosen = [by_name[a] for a in argv] or regions
    atlas = load()
    BUILD.mkdir(exist_ok=True)
    for r in chosen:
        report = report_of(atlas, r.number, 1)
        if report is None:
            sys.exit(f"region {r.number} has no pass 1 cards")
        draw_region(atlas, r, report)
        print(f"walks-{r.number:02d}: {r.name}: {len(report.walk.nodes)} countries, {len(report.jumps)} jump(s)"
              + "".join(f"\n  {a} ⇢ {b}" for a, b in report.jumps))
    if not argv:
        draw_ring(atlas, regions)
        print("walks-ring")


if __name__ == "__main__":
    main(sys.argv[1:])
