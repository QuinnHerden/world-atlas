"""Render one unlabelled map per feature: shaded basemap, red highlight, optional locator globe."""

import io
import math
from functools import cache

import cartopy.crs as ccrs
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely
from PIL import Image
from pyproj import Transformer
from shapely import unary_union
from shapely.geometry import LineString, Polygon, box
from shapely.geometry.base import BaseGeometry

from geofeat.frame import Frame, frame, project
from geofeat.model import VENDOR
from geofeat.ne import GEOD, flow_lines, layer
from geofeat.spec import RELIEF, RenderSpec
from geofeat.style import (
    BORDER, BORDER_PX, CASING, CASING_PX, CLOSE_UP_BORDER_PX, COAST, COAST_PX, CONTEXT_EDGE,
    CONTEXT_EDGE_PX, CONTEXT_RIVER, CONTEXT_RIVER_PX, CONTEXT_TINT_ALPHA, CURRENT_HEAD_EVERY_PX, CURRENT_HEAD_PX,
    DOT_PX, FORMER_SHORE, FORMER_SHORE_PX, HIGHLIGHT, INSET_DOT_PX, INSET_FRAME, INSET_FRAME_MIN_PX,
    INSET_FRAME_PX, INSET_LAND, INSET_OCEAN, LAND, OCEAN, OUTLINE_ALPHA, OUTLINE_PX, PARENT_RIVER_PX, RING_PX,
    STRAIT_OUTLINE_PX, STROKE_PX, WATER_AREA_ALPHA, WIND_CASING_PX, WIND_CHEVRON_ARM_PX, WIND_CHEVRON_PX, WIND_DASH_PX,
    WIND_GLYPH_PX,
)

WIDTH_PX, HEIGHT_PX, DPI = 1600, 900, 100
SCALE = 2  # stroke sizes below are specified for an 800 px wide card

# px at 1600 wide: an area smaller than a disc ~16 px across on a phone, or under ~25 px long there, also gets a ring
SMALL_HIGHLIGHT_PX, SHORT_HIGHLIGHT_PX = 66, 100
SMALL_RING_CLEAR_PX = 24
# A polygon strait narrower than this on average (px at 1600 wide) is drawn as a channel line, a wider one as a sea
CHANNEL_MAX_PX = 24
CLOSE_UP_M = 3_000_000  # a spec with close_up_borders gets heavier borders in frames narrower than this
LARGE_FRAME_M = 4_000_000  # narrower frames use 10m land, so narrow straits stay open
PLATE = ccrs.PlateCarree()
POLYGONAL = ("Polygon", "MultiPolygon")
WORLD = (-180, 180, -90, 90)  # lon0, lon1, lat0, lat1
INSET_PROJECTION = ccrs.PlateCarree()  # centred on 0° on every card
INSET_W_PX = 160
# Lease and buffer-zone outlines (Baikonur, Guantánamo, the DMZ, UN zones) that would draw as stray rings and double lines
NOT_BORDERS = ("Lease limit", "Overlay limit")
WIND_CHEVRON_ANGLE = math.radians(35)
# A strait or line whose highlight is shorter than this (px at 1600 wide) also gets a locating ring.
SMALL_STRAIT_PX, STRAIT_RING_MIN_PX, STRAIT_RING_CLEAR_PX = 123, 120, 24
STRAIT_RING_STROKE_PX, STRAIT_RING_CASING_PX = 6, 2


def pt(px: float) -> float:
    """Convert a stroke size given for an 800 px card into matplotlib points."""
    return px * SCALE * 72 / DPI


def pt_full(px: float) -> float:
    """Convert a size given in pixels of the 1600 px image into matplotlib points."""
    return px * 72 / DPI


@cache
def _relief() -> np.ndarray:
    return np.asarray(Image.open(VENDOR / RELIEF))


def _relief_layers(lon0: float, lon1: float, lat0: float, lat1: float):
    """Crop the relief raster and split it into a shadow layer and a highlight layer (RGBA)."""
    raster = _relief()
    per_deg = raster.shape[1] / 360
    c0, c1 = max(int((lon0 + 180) * per_deg), 0), int(np.ceil((lon1 + 180) * per_deg))
    r0, r1 = max(int((90 - lat1) * per_deg), 0), int(np.ceil((90 - lat0) * per_deg))
    crop = raster[r0:r1, c0:c1]
    extent = (c0 / per_deg - 180, (c0 + crop.shape[1]) / per_deg - 180, 90 - (r0 + crop.shape[0]) / per_deg, 90 - r0 / per_deg)
    step = max(1, crop.shape[1] // 3000)
    crop = crop[::step, ::step].astype(np.float32)
    if crop.shape[1] < WIDTH_PX:  # upsample smoothly so close-up frames don't show raster blocks
        size = (WIDTH_PX, max(1, round(crop.shape[0] * WIDTH_PX / crop.shape[1])))
        crop = np.asarray(Image.fromarray(crop, mode="F").resize(size, Image.Resampling.BICUBIC))
    flat = 175.0
    shadow = np.zeros(crop.shape + (4,), dtype=np.float32)
    shadow[..., 3] = np.clip((flat - crop) / flat, 0, 1) * 0.55
    light = np.ones(crop.shape + (4,), dtype=np.float32)
    light[..., 3] = np.clip((crop - flat) / (255 - flat), 0, 1) * 0.35
    return shadow, light, extent


def _clip(gdf, bounds):
    lon0, lon1, lat0, lat1 = bounds
    return gdf.cx[lon0:lon1, lat0:lat1].geometry


def _fill(ax, shapes, bounds, colour: str, zorder: float, world: bool) -> None:
    """Draw polygons near the frame. In a regional frame they are cut to it and projected here: cartopy's own
    projection of whole-world land and ocean polygons fails in some frames (Titicaca) and fills others inside out
    (Pyrenees, Arctic Ocean). World maps project fine and keep cartopy's handling of the map edge."""
    style = {"facecolor": colour, "edgecolor": "none", "zorder": zorder}
    if world:
        ax.add_geometries(shapes, PLATE, **style)
        return
    lon0, lon1, lat0, lat1 = bounds
    window = box(lon0, lat0, lon1, lat1).segmentize(0.5)
    projected = [project(g.intersection(window), ax.projection) for g in shapes]
    ax.add_geometries([g for g in projected if not g.is_empty], ax.projection, **style)


def _basemap(ax, spec: RenderSpec, frame_: Frame, lonlat_bounds) -> None:
    world = frame_.extent is None
    span = None if world else frame_.extent[1] - frame_.extent[0]
    res = "50m" if world or span > LARGE_FRAME_M else "10m"
    land_rows = _clip(layer(f"{res}_land"), lonlat_bounds)
    _fill(ax, land_rows, lonlat_bounds, LAND, 1, world)
    shadow, light, extent = _relief_layers(*lonlat_bounds)
    for img in (shadow, light):
        ax.imshow(img, extent=extent, transform=PLATE, origin="upper", regrid_shape=WIDTH_PX, zorder=1.1)
    lakes = _clip(layer("50m_lakes"), lonlat_bounds)
    _fill(ax, _clip(layer(f"{res}_ocean"), lonlat_bounds), lonlat_bounds, OCEAN, 1.2, world)
    _fill(ax, lakes, lonlat_bounds, OCEAN, 1.2, world)
    rivers = layer("50m_rivers_lake_centerlines")
    ax.add_geometries(  # above borders, which often follow a river (the Ohio)
        _clip(rivers[rivers["scalerank"] <= 4], lonlat_bounds),
        PLATE, facecolor="none", edgecolor=CONTEXT_RIVER, linewidth=pt(CONTEXT_RIVER_PX), zorder=1.42,
    )
    lon0, lon1, lat0, lat1 = lonlat_bounds
    land = unary_union([shapely.clip_by_rect(g, lon0, lat0, lon1, lat1) for g in land_rows])
    dry = land.difference(shapely.make_valid(unary_union(list(lakes))))
    borders = layer(f"{res}_admin_0_boundary_lines_land")
    borders = unary_union(list(_clip(borders[~borders["featurecla"].isin(NOT_BORDERS)], lonlat_bounds)))
    border_px = CLOSE_UP_BORDER_PX if spec.close_up_borders and span is not None and span < CLOSE_UP_M else BORDER_PX
    ax.add_geometries(  # Natural Earth runs some land borders across straits (Kerch) and lakes (Erie); keep them on land
        [borders.intersection(dry)], PLATE, facecolor="none", edgecolor=BORDER, linewidth=pt(border_px), zorder=1.4,
    )
    if spec.frame.admin1:
        states = unary_union(list(_clip(layer("50m_admin_1_states_provinces_lines"), lonlat_bounds)))
        ax.add_geometries([states.intersection(dry)], PLATE, facecolor="none", edgecolor=BORDER, linewidth=pt(BORDER_PX), zorder=1.4)
    # Natural Earth splits land at ±180 and the clip above cuts it at the window: neither edge is a coast
    seams = unary_union([LineString([(x, -90), (x, 90)]) for x in (-180, 180)] + [box(lon0, lat0, lon1, lat1).boundary])
    coast = land.boundary.difference(seams.buffer(1e-9))
    ax.add_geometries([coast], PLATE, facecolor="none", edgecolor=COAST, linewidth=pt(COAST_PX), zorder=1.5)


def _ring(ax, x: float, y: float, crs, size: float = pt(RING_PX), core: float = pt(4), casing: float = pt(1.5)) -> None:
    ax.plot(x, y, transform=crs, marker="o", ms=size, mfc="none", mec=CASING, mew=core + 2 * casing, zorder=5)
    ax.plot(x, y, transform=crs, marker="o", ms=size, mfc="none", mec=HIGHLIGHT, mew=core, zorder=5.1)


def _metres_per_px(ax) -> float:
    x0, x1 = ax.get_xlim()
    return (x1 - x0) / WIDTH_PX


def _arrows(ax, geometry: BaseGeometry, frame_: Frame, wind: bool) -> None:
    """Heads along each head-to-tail line, placed in lon/lat so crossings and ±180° splits never get one.

    Winds: an open chevron every WIND_GLYPH_PX and at the end. Currents: a filled head at the end and evenly
    before it, at least every CURRENT_HEAD_EVERY_PX and always one near halfway.
    """
    mpp = _metres_per_px(ax) * SCALE  # metres per px of an 800 px card
    to_map = Transformer.from_crs("EPSG:4326", frame_.projection.proj4_init, always_xy=True)
    for line in flow_lines(geometry):
        length_px = GEOD.geometry_length(line) / mpp
        heads = max(1, math.ceil(length_px / WIND_GLYPH_PX)) if wind else max(2, math.ceil(length_px / CURRENT_HEAD_EVERY_PX))
        for k in range(1, heads + 1):
            at = k / heads
            tip = to_map.transform(*line.interpolate(at, normalized=True).coords[0])
            back = to_map.transform(*line.interpolate(at - 0.001, normalized=True).coords[0])
            norm = math.hypot(tip[0] - back[0], tip[1] - back[1]) or 1.0
            ux, uy = (tip[0] - back[0]) / norm, (tip[1] - back[1]) / norm
            if wind:
                _chevron(ax, tip, ux, uy, WIND_CHEVRON_ARM_PX * mpp, frame_.projection)
            else:
                _head(ax, tip, ux, uy, CURRENT_HEAD_PX[0] * mpp, CURRENT_HEAD_PX[1] * mpp, frame_.projection)


def _chevron(ax, tip: tuple[float, float], ux: float, uy: float, arm: float, crs) -> None:
    xs, ys = [], []
    for sign in (1, -1):
        c, s_ = math.cos(WIND_CHEVRON_ANGLE), sign * math.sin(WIND_CHEVRON_ANGLE)
        xs.append(tip[0] - arm * (ux * c - uy * s_))
        ys.append(tip[1] - arm * (uy * c + ux * s_))
    xs.insert(1, tip[0])
    ys.insert(1, tip[1])
    casing = pt(WIND_CHEVRON_PX + 2 * WIND_CASING_PX)
    ax.plot(xs, ys, transform=crs, color=CASING, lw=casing, solid_capstyle="butt", solid_joinstyle="miter", zorder=5.2)
    ax.plot(xs, ys, transform=crs, color=HIGHLIGHT, lw=pt(WIND_CHEVRON_PX), solid_capstyle="butt", solid_joinstyle="miter", zorder=5.3)


def _head(ax, tip: tuple[float, float], ux: float, uy: float, length: float, width: float, crs) -> None:
    bx, by = tip[0] - ux * length, tip[1] - uy * length
    half = width / 2
    xs = [bx - uy * half, tip[0], bx + uy * half]
    ys = [by + ux * half, tip[1], by - ux * half]
    ax.fill(xs, ys, transform=crs, facecolor=HIGHLIGHT, edgecolor=CASING, lw=pt(CASING_PX), zorder=5.2)


def _dash(style: str, width_px: float) -> str | tuple:
    """Wind dashes, given in px and so the same length whatever the line width (matplotlib scales them by width)."""
    if style != "flow-wind":
        return "solid"
    return 0, tuple(px / width_px for px in WIND_DASH_PX)


def _short_ring(ax, geometry: BaseGeometry, frame_: Frame) -> None:
    """Short straits and canals vanish on a phone; ring them, leaving the line visible inside."""
    x0, y0, x1, y1 = project(geometry, frame_.projection).bounds
    long_px = max(x1 - x0, y1 - y0) / _metres_per_px(ax)
    if long_px < SMALL_STRAIT_PX:
        diameter = max(long_px + 2 * STRAIT_RING_CLEAR_PX, STRAIT_RING_MIN_PX)
        _ring(ax, (x0 + x1) / 2, (y0 + y1) / 2, frame_.projection, size=pt_full(diameter),
              core=pt_full(STRAIT_RING_STROKE_PX), casing=pt_full(STRAIT_RING_CASING_PX))


def _context(ax, context: tuple[BaseGeometry, ...]) -> None:
    for shape in context:
        ax.add_geometries([shape], PLATE, facecolor="none", edgecolor=CONTEXT_RIVER,
                          linewidth=pt(PARENT_RIVER_PX), zorder=1.35)


def _small_ring(ax, shape: BaseGeometry, frame_: Frame) -> None:
    """Ring a projected area too small or short to find on a phone."""
    px0, py0, px1, py1 = shape.bounds
    across = max(px1 - px0, py1 - py0) / _metres_per_px(ax)
    if 2 * math.sqrt(shape.area / math.pi) / _metres_per_px(ax) < SMALL_HIGHLIGHT_PX or across < SHORT_HIGHLIGHT_PX:
        size = max(pt(RING_PX), pt_full(across + 2 * SMALL_RING_CLEAR_PX))
        _ring(ax, (px0 + px1) / 2, (py0 + py1) / 2, frame_.projection, size=size)


def _country(ax, geometry: BaseGeometry, frame_: Frame, subject: bool) -> None:
    """A country, for the countries PoC. As the subject: a crisp red outline with a white casing over a faint fill,
    ringed when small. As context for a city dot: washed lighter and edged in a dark neutral, with nothing red."""
    fuse = 2 * _metres_per_px(ax)
    shape = project(geometry, frame_.projection).buffer(fuse).buffer(-fuse)
    crs = frame_.projection
    if not subject:
        ax.add_geometries([shape], crs, facecolor=CASING, alpha=CONTEXT_TINT_ALPHA, edgecolor="none", zorder=4)
        ax.add_geometries([shape], crs, facecolor="none", edgecolor=CONTEXT_EDGE, linewidth=pt(CONTEXT_EDGE_PX), zorder=4.1)
        return
    ax.add_geometries([shape], crs, facecolor=HIGHLIGHT, alpha=OUTLINE_ALPHA, edgecolor="none", zorder=4)
    ax.add_geometries([shape], crs, facecolor="none", edgecolor=CASING, linewidth=pt(OUTLINE_PX + 2 * CASING_PX), zorder=4.05)
    ax.add_geometries([shape], crs, facecolor="none", edgecolor=HIGHLIGHT, linewidth=pt(OUTLINE_PX), zorder=4.1)
    _small_ring(ax, shape, frame_)


def _dot(ax, lon: float, lat: float) -> None:
    """A city: a red disc in a white casing edged in a dark hairline, so it reads on any fill. No ring."""
    for size, colour in ((DOT_PX + 2 * CASING_PX + 1, CONTEXT_EDGE), (DOT_PX + 2 * CASING_PX, CASING), (DOT_PX, HIGHLIGHT)):
        ax.plot(lon, lat, transform=PLATE, marker="o", ms=pt(size), mfc=colour, mec="none", zorder=6)


def _highlight(ax, spec: RenderSpec, geometry: BaseGeometry, frame_: Frame) -> None:
    style = spec.style
    if style == "point":
        _ring(ax, geometry.centroid.x, geometry.centroid.y, PLATE)
        return
    if style in ("area", "band"):
        # Natural Earth cuts polygons at 180°; fusing in map space hides the cut instead of outlining it
        fuse = 2 * _metres_per_px(ax)
        shape = project(geometry, frame_.projection).buffer(fuse).buffer(-fuse)
        alpha = spec.fill_alpha
        edge = {"linewidth": pt(2.75)} if style == "area" else {"linewidth": pt(2), "linestyle": (0, (5, 3))}
        ax.add_geometries([shape], frame_.projection, facecolor=HIGHLIGHT, alpha=alpha, edgecolor="none", zorder=4)
        ax.add_geometries([shape], frame_.projection, facecolor="none", edgecolor=HIGHLIGHT, zorder=4.1, **edge)
        if style == "area":
            _small_ring(ax, shape, frame_)
    else:
        core = STROKE_PX[style]
        polygons = [g for g in getattr(geometry, "geoms", [geometry]) if g.geom_type in POLYGONAL]
        if style == "strait" and polygons:
            shape = project(unary_union(polygons), frame_.projection)
            if 2 * shape.area / shape.length / _metres_per_px(ax) > CHANNEL_MAX_PX:  # mean width, for a long shape
                ax.add_geometries([shape], frame_.projection, facecolor=HIGHLIGHT, alpha=WATER_AREA_ALPHA, edgecolor="none", zorder=4)
                ax.add_geometries([shape], frame_.projection, facecolor="none", edgecolor=HIGHLIGHT,
                                  linewidth=pt(STRAIT_OUTLINE_PX), zorder=4.1)
                _short_ring(ax, geometry, frame_)
                return
            ax.add_geometries(polygons, PLATE, facecolor=HIGHLIGHT, edgecolor="none", zorder=4.05)
        casing = core + 2 * (WIND_CASING_PX if style == "flow-wind" else CASING_PX)
        ax.add_geometries([geometry], PLATE, facecolor="none", edgecolor=CASING, linewidth=pt(casing), linestyle=_dash(style, casing), zorder=4)
        ax.add_geometries([geometry], PLATE, facecolor="none", edgecolor=HIGHLIGHT, linewidth=pt(core), linestyle=_dash(style, core), zorder=4.1)
        if style.startswith("flow"):
            _arrows(ax, geometry, frame_, wind=style == "flow-wind")
        if style in ("strait", "line"):
            _short_ring(ax, geometry, frame_)


def _inset(fig, frame_: Frame, highlight_px: tuple[float, float, float, float]) -> None:
    """The same flat world map on every card, marking the frame as a box, or a dot where the box would be tiny."""
    w, margin = INSET_W_PX * SCALE, 12 * SCALE
    h = w / 2
    corners = [(margin, margin), (WIDTH_PX - w - margin, margin), (margin, HEIGHT_PX - h - margin),
               (WIDTH_PX - w - margin, HEIGHT_PX - h - margin)]
    hx0, hy0, hx1, hy1 = highlight_px
    clear = box(hx0 - 20 * SCALE, hy0 - 20 * SCALE, hx1 + 20 * SCALE, hy1 + 20 * SCALE)
    x, y = next((c for c in corners if not box(c[0], c[1], c[0] + w, c[1] + h).intersects(clear)), corners[0])

    ax = fig.add_axes([x / WIDTH_PX, y / HEIGHT_PX, w / WIDTH_PX, h / HEIGHT_PX], projection=INSET_PROJECTION)
    ax.set_global()
    ax.set_facecolor(INSET_OCEAN)
    ax.spines["geo"].set_edgecolor(COAST)
    ax.spines["geo"].set_linewidth(pt(1))
    ax.add_geometries(layer("50m_land").geometry, PLATE, facecolor=INSET_LAND, edgecolor="none")
    fx0, fx1, fy0, fy1 = frame_.extent
    outline = Polygon([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)]).segmentize((fx1 - fx0) / 50)
    lons, lats = Transformer.from_crs(frame_.projection.proj4_init, "EPSG:4326", always_xy=True).transform(
        *np.array(outline.exterior.coords).T)
    across = np.ptp(lons) > 180  # a box across 180° would split at the inset's edges: mark it with the dot
    small = max(np.ptp(lons) / 360 * w, np.ptp(lats) / 180 * h) < INSET_FRAME_MIN_PX * SCALE
    if small or across:
        ax.plot((fx0 + fx1) / 2, (fy0 + fy1) / 2, transform=frame_.projection, marker="o", ms=pt(INSET_DOT_PX),
                mfc=INSET_FRAME, mec=CASING, mew=pt(CASING_PX), zorder=2)
        return
    casing = INSET_FRAME_PX + 2 * CASING_PX
    ax.add_geometries([outline], frame_.projection, facecolor="none", edgecolor=CASING, linewidth=pt(casing), zorder=2)
    ax.add_geometries([outline], frame_.projection, facecolor="none", edgecolor=INSET_FRAME, linewidth=pt(INSET_FRAME_PX), zorder=2.1)


def render(spec: RenderSpec, geometry: BaseGeometry, context: tuple[BaseGeometry, ...] = (),
           former: BaseGeometry | None = None) -> bytes:
    """The card's map: `geometry` drawn as `spec` says over the basemap, with `context` lines drawn faintly underneath
    and a `former` shoreline dashed in grey. Reads nothing but the basemap layers and relief."""
    if spec.outline:
        raise NotImplementedError("RenderSpec.outline is reserved and not drawn yet")
    frame_ = frame(spec, geometry)
    fig = plt.figure(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI, facecolor=OCEAN)
    ax = fig.add_axes([0, 0, 1, 1], projection=frame_.projection)
    ax.set_facecolor(OCEAN)
    ax.spines["geo"].set_visible(False)
    if frame_.extent is None:
        ax.set_global()
        bounds = WORLD
    else:
        ax.set_extent(frame_.extent, crs=frame_.projection)
        lon0, lon1, lat0, lat1 = ax.get_extent(crs=PLATE)
        bounds = (max(lon0 - 2, -180), min(lon1 + 2, 180), max(lat0 - 2, -90), min(lat1 + 2, 90))
    _basemap(ax, spec, frame_, bounds)
    _context(ax, context)
    if former is not None:
        ax.add_geometries([former], PLATE, facecolor="none", edgecolor=FORMER_SHORE,
                          linewidth=pt(FORMER_SHORE_PX), linestyle=(0, (4, 3)), zorder=1.45)
    if spec.country:
        _country(ax, geometry, frame_, subject=spec.country == "subject")
    else:
        _highlight(ax, spec, geometry, frame_)
    if spec.dot:
        _dot(ax, *spec.dot)

    if frame_.inset:
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        px0, py0, px1, py1 = project(geometry, frame_.projection).bounds
        to_px = lambda vx, vy: ((vx - x0) / (x1 - x0) * WIDTH_PX, (vy - y0) / (y1 - y0) * HEIGHT_PX)
        _inset(fig, frame_, (*to_px(px0, py0), *to_px(px1, py1)))

    raw = io.BytesIO()
    fig.savefig(raw, format="png", dpi=DPI, facecolor=OCEAN, metadata={"Software": None})
    plt.close(fig)
    out = io.BytesIO()
    Image.open(raw).convert("RGB").quantize(256, method=Image.Quantize.FASTOCTREE).save(out, format="PNG", optimize=True)
    return out.getvalue()


if __name__ == "__main__":
    from geofeat.jobs import main

    main()
