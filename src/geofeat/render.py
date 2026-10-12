"""Render one unlabelled map per feature: shaded basemap, red highlight, optional locator globe."""

import hashlib
import io
import json
import math
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import cache
from pathlib import Path

import cartopy.crs as ccrs
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely
from PIL import Image
from pyproj import Transformer
from shapely import unary_union
from shapely.geometry import Polygon, box
from shapely.geometry.base import BaseGeometry

from geofeat.frame import Frame, centre, frame, project
from geofeat.model import BUILD, DECK, LOCK, MEDIA_INDEX, ROOT, VENDOR, Feature, active, load_features
from geofeat.resolve import GEOD, features_by_id, flow_lines, layer, resolve
from geofeat.style import (
    AREA_ALPHA, BORDER, CASING, CASING_PX, COAST, CONTEXT_RIVER, CONTEXT_RIVER_PX, CURRENT_HEAD_EVERY_PX, CURRENT_HEAD_PX,
    HIGHLIGHT, INSET_FRAME, INSET_LAND, INSET_OCEAN, LAND, OCEAN, PARENT_RIVER_PX, RING_PX, STROKE_PX,
    WATER_AREA_ALPHA, WIND_CASING_PX, WIND_CHEVRON_ARM_PX, WIND_CHEVRON_PX, WIND_DASH_PX, WIND_GLYPH_PX,
)

CACHE = BUILD / "render-cache.json"  # input hash -> rendered PNG name
JOBS = int(os.environ.get("JOBS", "1"))  # each worker loads its own copy of the layers; ~1.5 GB per worker

WIDTH_PX, HEIGHT_PX, DPI = 1600, 900, 100
SCALE = 2  # stroke sizes below are specified for an 800 px wide card

WATER_CATEGORIES = {"Oceans & Seas", "Straits & Chokepoints", "Lakes"}
SMALL_HIGHLIGHT_PX = 12 * SCALE
LARGE_FRAME_M = 2_000_000
PLATE = ccrs.PlateCarree()
POLYGONAL = ("Polygon", "MultiPolygon")
WIND_CHEVRON_ANGLE = math.radians(35)
# A strait whose highlight is shorter than this (px at 1600 wide) also gets a locating ring.
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
    return np.asarray(Image.open(VENDOR / "GRAY_50M_SR.tif"))


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


def _basemap(ax, lonlat_bounds, large: bool) -> None:
    res = "50m" if large else "10m"
    ax.add_geometries(_clip(layer(f"{res}_land"), lonlat_bounds), PLATE, facecolor=LAND, edgecolor="none", zorder=1)
    shadow, light, extent = _relief_layers(*lonlat_bounds)
    for img in (shadow, light):
        ax.imshow(img, extent=extent, transform=PLATE, origin="upper", regrid_shape=WIDTH_PX, zorder=1.1)
    for water in (f"{res}_ocean", "50m_lakes"):
        ax.add_geometries(_clip(layer(water), lonlat_bounds), PLATE, facecolor=OCEAN, edgecolor="none", zorder=1.2)
    rivers = layer("50m_rivers_lake_centerlines")
    ax.add_geometries(
        _clip(rivers[rivers["scalerank"] <= 4], lonlat_bounds),
        PLATE, facecolor="none", edgecolor=CONTEXT_RIVER, linewidth=pt(CONTEXT_RIVER_PX), zorder=1.3,
    )
    lon0, lon1, lat0, lat1 = lonlat_bounds
    land = unary_union([shapely.clip_by_rect(g, lon0, lat0, lon1, lat1) for g in _clip(layer(f"{res}_land"), lonlat_bounds)])
    borders = unary_union(list(_clip(layer(f"{res}_admin_0_boundary_lines_land"), lonlat_bounds)))
    ax.add_geometries(  # Natural Earth runs some land borders across straits (Kerch); keep them on land
        [borders.intersection(land)], PLATE, facecolor="none", edgecolor=BORDER, linewidth=pt(0.5), zorder=1.4,
    )
    ax.add_geometries([land], PLATE, facecolor="none", edgecolor=COAST, linewidth=pt(0.6), zorder=1.5)


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


def _strait_ring(ax, geometry: BaseGeometry, frame_: Frame) -> None:
    """Short straits vanish on a phone; ring them, leaving the channel visible inside."""
    x0, y0, x1, y1 = project(geometry, frame_.projection).bounds
    long_px = max(x1 - x0, y1 - y0) / _metres_per_px(ax)
    if long_px < SMALL_STRAIT_PX:
        diameter = max(long_px + 2 * STRAIT_RING_CLEAR_PX, STRAIT_RING_MIN_PX)
        _ring(ax, (x0 + x1) / 2, (y0 + y1) / 2, frame_.projection, size=pt_full(diameter),
              core=pt_full(STRAIT_RING_STROKE_PX), casing=pt_full(STRAIT_RING_CASING_PX))


def _context(ax, feature: Feature) -> None:
    for other in feature.frame.context:
        ax.add_geometries([resolve(features_by_id()[other])], PLATE, facecolor="none", edgecolor=CONTEXT_RIVER,
                          linewidth=pt(PARENT_RIVER_PX), zorder=1.35)


def _highlight(ax, feature: Feature, geometry: BaseGeometry, frame_: Frame) -> None:
    style = feature.style
    if style == "point":
        _ring(ax, geometry.centroid.x, geometry.centroid.y, PLATE)
        return
    if style in ("area", "band"):
        # Natural Earth cuts polygons at 180°; fusing in map space hides the cut instead of outlining it
        fuse = 2 * _metres_per_px(ax)
        shape = project(geometry, frame_.projection).buffer(fuse).buffer(-fuse)
        alpha = AREA_ALPHA if style == "area" and feature.category not in WATER_CATEGORIES else WATER_AREA_ALPHA
        edge = {"linewidth": pt(2.75)} if style == "area" else {"linewidth": pt(2), "linestyle": (0, (5, 3))}
        ax.add_geometries([shape], frame_.projection, facecolor=HIGHLIGHT, alpha=alpha, edgecolor="none", zorder=4)
        ax.add_geometries([shape], frame_.projection, facecolor="none", edgecolor=HIGHLIGHT, zorder=4.1, **edge)
        px0, py0, px1, py1 = shape.bounds
        if style == "area" and max(px1 - px0, py1 - py0) / _metres_per_px(ax) < SMALL_HIGHLIGHT_PX:
            _ring(ax, (px0 + px1) / 2, (py0 + py1) / 2, frame_.projection)
    else:
        core = STROKE_PX[style]
        polygons = [g for g in getattr(geometry, "geoms", [geometry]) if g.geom_type in POLYGONAL]
        if style == "strait" and polygons:
            ax.add_geometries(polygons, PLATE, facecolor=HIGHLIGHT, edgecolor="none", zorder=4.05)
        casing = core + 2 * (WIND_CASING_PX if style == "flow-wind" else CASING_PX)
        ax.add_geometries([geometry], PLATE, facecolor="none", edgecolor=CASING, linewidth=pt(casing), linestyle=_dash(style, casing), zorder=4)
        ax.add_geometries([geometry], PLATE, facecolor="none", edgecolor=HIGHLIGHT, linewidth=pt(core), linestyle=_dash(style, core), zorder=4.1)
        if style.startswith("flow"):
            _arrows(ax, geometry, frame_, wind=style == "flow-wind")
        if style == "strait":
            _strait_ring(ax, geometry, frame_)


def _inset(fig, geometry: BaseGeometry, frame_: Frame, highlight_px: tuple[float, float, float, float]) -> None:
    size, margin = 110 * SCALE, 12 * SCALE
    corners = [(margin, margin), (WIDTH_PX - size - margin, margin), (margin, HEIGHT_PX - size - margin),
               (WIDTH_PX - size - margin, HEIGHT_PX - size - margin)]
    hx0, hy0, hx1, hy1 = highlight_px
    clear = box(hx0 - 20 * SCALE, hy0 - 20 * SCALE, hx1 + 20 * SCALE, hy1 + 20 * SCALE)
    x, y = next((c for c in corners if not box(c[0], c[1], c[0] + size, c[1] + size).intersects(clear)), corners[0])

    lon, lat = centre(geometry)
    ax = fig.add_axes(
        [x / WIDTH_PX, y / HEIGHT_PX, size / WIDTH_PX, size / HEIGHT_PX],
        projection=ccrs.Orthographic(central_longitude=lon, central_latitude=lat),
    )
    ax.set_global()
    ax.set_facecolor(INSET_OCEAN)
    ax.spines["geo"].set_edgecolor(COAST)
    ax.spines["geo"].set_linewidth(pt(1))
    ax.add_geometries(layer("50m_land").geometry, PLATE, facecolor=INSET_LAND, edgecolor="none")
    fx0, fx1, fy0, fy1 = frame_.extent
    outline = Polygon([(fx0, fy0), (fx1, fy0), (fx1, fy1), (fx0, fy1)]).segmentize((fx1 - fx0) / 50)
    ax.add_geometries([outline], frame_.projection, facecolor="none", edgecolor=CASING, linewidth=pt_full(6), zorder=2)
    ax.add_geometries([outline], frame_.projection, facecolor="none", edgecolor=INSET_FRAME, linewidth=pt_full(3), zorder=2.1)


def render(feature: Feature, geometry: BaseGeometry) -> bytes:
    frame_ = frame(feature, geometry)
    fig = plt.figure(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI, facecolor=OCEAN)
    ax = fig.add_axes([0, 0, 1, 1], projection=frame_.projection)
    ax.set_facecolor(OCEAN)
    ax.spines["geo"].set_visible(False)
    if frame_.extent is None:
        ax.set_global()
        bounds = (-180, 180, -90, 90)
    else:
        ax.set_extent(frame_.extent, crs=frame_.projection)
        lon0, lon1, lat0, lat1 = ax.get_extent(crs=PLATE)
        bounds = (max(lon0 - 2, -180), min(lon1 + 2, 180), max(lat0 - 2, -90), min(lat1 + 2, 90))
    large = frame_.extent is None or frame_.extent[1] - frame_.extent[0] > LARGE_FRAME_M
    _basemap(ax, bounds, large)
    _context(ax, feature)
    _highlight(ax, feature, geometry, frame_)

    if frame_.inset:
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        px0, py0, px1, py1 = project(geometry, frame_.projection).bounds
        to_px = lambda vx, vy: ((vx - x0) / (x1 - x0) * WIDTH_PX, (vy - y0) / (y1 - y0) * HEIGHT_PX)
        _inset(fig, geometry, frame_, (*to_px(px0, py0), *to_px(px1, py1)))

    raw = io.BytesIO()
    fig.savefig(raw, format="png", dpi=DPI, facecolor=OCEAN, metadata={"Software": None})
    plt.close(fig)
    out = io.BytesIO()
    Image.open(raw).convert("RGB").quantize(256, method=Image.Quantize.FASTOCTREE).save(out, format="PNG", optimize=True)
    return out.getvalue()


@cache
def _code_hash() -> str:
    h = hashlib.sha256()
    for name in ("render.py", "frame.py", "resolve.py", "model.py", "style.py"):
        h.update((ROOT / "src/geofeat" / name).read_bytes())
    for path in (ROOT / "uv.lock", LOCK):
        h.update(path.read_bytes())
    return h.hexdigest()


def input_hash(feature: Feature, stack: tuple[str, ...] = ()) -> str:
    """Everything that changes a feature's pixels, including the features it references; renaming, re-tiering or retyping it does not."""
    h = hashlib.sha256(_code_hash().encode())
    h.update(feature.model_dump_json(include={"category", "style", "geometry", "frame", "trim_to_largest"}).encode())
    for part in feature.geometry:
        if part.file:
            h.update((ROOT / "geometry" / part.file).read_bytes())
    for other in [p.feature for p in feature.geometry if p.feature]:
        if other in stack:
            raise ValueError(f"{feature.id}: reference cycle through {other!r}")
        h.update(input_hash(features_by_id()[other], (*stack, feature.id)).encode())
    for other in feature.frame.context:  # drawn as plain geometry, so only its shape matters
        h.update(shapely.to_wkb(resolve(features_by_id()[other])))
    return h.hexdigest()


def _render_to_file(feature: Feature) -> str:
    png = render(feature, resolve(feature))
    file = f"{hashlib.sha256(png).hexdigest()[:12]}.png"
    (DECK / file).write_bytes(png)
    return file


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def main() -> None:
    DECK.mkdir(exist_ok=True)
    BUILD.mkdir(exist_ok=True)
    cache_ = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    features = active(load_features())
    keys = {f.id: input_hash(f) for f in features}
    todo = [f for f in features if not (keys[f.id] in cache_ and (DECK / cache_[keys[f.id]]).exists())]

    with ProcessPoolExecutor(max_workers=JOBS) as pool:
        futures = {pool.submit(_render_to_file, f): f for f in todo}
        try:
            for future in as_completed(futures):
                feature = futures[future]
                cache_[keys[feature.id]] = future.result()
                _write_json(CACHE, cache_)
                print(f"rendered {feature.id} -> {cache_[keys[feature.id]]}")
        except BaseException:
            pool.shutdown(cancel_futures=True)
            raise

    media = {f.id: cache_[keys[f.id]] for f in features}
    _write_json(MEDIA_INDEX, media)
    for stale in {p.name for p in DECK.glob("*.png")} - set(media.values()):
        (DECK / stale).unlink()
    _write_json(CACHE, {k: v for k, v in cache_.items() if v in media.values()})


if __name__ == "__main__":
    main()
