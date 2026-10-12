"""Render one unlabelled map per feature: shaded basemap, red highlight, optional locator globe."""

import hashlib
import io
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import cache
from pathlib import Path

import cartopy.crs as ccrs
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch
from PIL import Image
from shapely.geometry import LineString, MultiLineString, Polygon, box
from shapely.geometry.base import BaseGeometry

from geofeat.frame import Frame, centre, frame, project
from geofeat.model import BUILD, DECK, LOCK, MEDIA_INDEX, ROOT, VENDOR, Feature, active, load_features
from geofeat.resolve import layer, resolve

CACHE = BUILD / "render-cache.json"  # input hash -> rendered PNG name
JOBS = int(os.environ.get("JOBS", "1"))  # each worker loads its own copy of the layers; ~1.5 GB per worker

WIDTH_PX, HEIGHT_PX, DPI = 1600, 900, 100
SCALE = 2  # stroke sizes below are specified for an 800 px wide card

LAND = "#E9E4D8"
OCEAN = "#C3D5E2"
BORDER = "#A39E94"
COAST = "#7F8A93"
CONTEXT_RIVER = "#9DB8CC"
HIGHLIGHT = "#B2182B"
CASING = "#FFFFFF"
INSET_LAND = "#BDB6A8"
INSET_OCEAN = "#DCE7EF"

WATER_CATEGORIES = {"Oceans & Seas", "Straits & Chokepoints", "Lakes"}
SMALL_HIGHLIGHT_PX = 12 * SCALE
LARGE_FRAME_M = 2_000_000
PLATE = ccrs.PlateCarree()
POLYGONAL = ("Polygon", "MultiPolygon")


def pt(px: float) -> float:
    """Convert a stroke size given for an 800 px card into matplotlib points."""
    return px * SCALE * 72 / DPI


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
        PLATE, facecolor="none", edgecolor=CONTEXT_RIVER, linewidth=pt(0.6), zorder=1.3,
    )
    ax.add_geometries(
        _clip(layer(f"{res}_admin_0_boundary_lines_land"), lonlat_bounds),
        PLATE, facecolor="none", edgecolor=BORDER, linewidth=pt(0.5), zorder=1.4,
    )
    ax.add_geometries(
        _clip(layer(f"{res}_land"), lonlat_bounds), PLATE, facecolor="none", edgecolor=COAST, linewidth=pt(0.6), zorder=1.5
    )


def _ring(ax, x: float, y: float, crs) -> None:
    ax.plot(x, y, transform=crs, marker="o", ms=pt(32), mfc="none", mec=CASING, mew=pt(7), zorder=5)
    ax.plot(x, y, transform=crs, marker="o", ms=pt(32), mfc="none", mec=HIGHLIGHT, mew=pt(4), zorder=5.1)


def _lines(geometry: BaseGeometry) -> list[LineString]:
    if isinstance(geometry, LineString):
        return [geometry]
    if isinstance(geometry, MultiLineString):
        return list(geometry.geoms)
    return [g for part in getattr(geometry, "geoms", []) for g in _lines(part)]


def _metres_per_px(ax) -> float:
    x0, x1 = ax.get_xlim()
    return (x1 - x0) / WIDTH_PX


def _arrows(ax, geometry: BaseGeometry, frame_: Frame, every_px: float, dashed: bool) -> None:
    """Place arrowheads along each line, every `every_px` pixels of map distance."""
    step = every_px * SCALE * _metres_per_px(ax)
    for line in _lines(project(geometry, frame_.projection)):
        d = step / 2
        while d < line.length:
            a, b = line.interpolate(max(d - step * 0.05, 0)), line.interpolate(d)
            ax.add_patch(FancyArrowPatch(
                (a.x, a.y), (b.x, b.y), arrowstyle="->" if dashed else "-|>",
                mutation_scale=pt(14), color=HIGHLIGHT, linewidth=pt(3), shrinkA=0, shrinkB=0, zorder=5.2,
            ))
            d += step


def _highlight(ax, feature: Feature, geometry: BaseGeometry, frame_: Frame) -> None:
    style = feature.style
    if style == "point":
        _ring(ax, geometry.centroid.x, geometry.centroid.y, PLATE)
        return
    if style in ("area", "band"):
        # Natural Earth cuts polygons at 180°; fusing in map space hides the cut instead of outlining it
        fuse = 2 * _metres_per_px(ax)
        shape = project(geometry, frame_.projection).buffer(fuse).buffer(-fuse)
        alpha = 0.40 if style == "area" and feature.category not in WATER_CATEGORIES else 0.30
        edge = {"linewidth": pt(2.75)} if style == "area" else {"linewidth": pt(2), "linestyle": (0, (5, 3))}
        ax.add_geometries([shape], frame_.projection, facecolor=HIGHLIGHT, alpha=alpha, edgecolor="none", zorder=4)
        ax.add_geometries([shape], frame_.projection, facecolor="none", edgecolor=HIGHLIGHT, zorder=4.1, **edge)
        px0, py0, px1, py1 = shape.bounds
        if style == "area" and max(px1 - px0, py1 - py0) / _metres_per_px(ax) < SMALL_HIGHLIGHT_PX:
            _ring(ax, (px0 + px1) / 2, (py0 + py1) / 2, frame_.projection)
    else:
        core = {"line": 5, "strait": 6, "flow-current": 4, "flow-wind": 3}[style]
        polygons = [g for g in getattr(geometry, "geoms", [geometry]) if g.geom_type in POLYGONAL]
        if style == "strait" and polygons:
            ax.add_geometries(polygons, PLATE, facecolor=HIGHLIGHT, edgecolor="none", zorder=4)
        dash = (0, (5, 3)) if style == "flow-wind" else "solid"
        ax.add_geometries([geometry], PLATE, facecolor="none", edgecolor=CASING, linewidth=pt(core + 3), zorder=4)
        ax.add_geometries([geometry], PLATE, facecolor="none", edgecolor=HIGHLIGHT, linewidth=pt(core), linestyle=dash, zorder=4.1)
        if style.startswith("flow"):
            _arrows(ax, geometry, frame_, every_px=150, dashed=style == "flow-wind")


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
    ax.add_geometries([outline], frame_.projection, facecolor="none", edgecolor=HIGHLIGHT, linewidth=pt(1.5))


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
    Image.open(raw).convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT).save(out, format="PNG", optimize=True)
    return out.getvalue()


@cache
def _code_hash() -> str:
    h = hashlib.sha256()
    for name in ("render.py", "frame.py", "resolve.py", "model.py"):
        h.update((ROOT / "src/geofeat" / name).read_bytes())
    for path in (ROOT / "uv.lock", LOCK):
        h.update(path.read_bytes())
    return h.hexdigest()


def input_hash(feature: Feature) -> str:
    """Everything that changes a feature's pixels; renaming, re-tiering or retyping it does not."""
    h = hashlib.sha256(_code_hash().encode())
    h.update(feature.model_dump_json(include={"category", "style", "geometry", "frame"}).encode())
    for part in feature.geometry:
        if part.file:
            h.update((ROOT / "geometry" / part.file).read_bytes())
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
