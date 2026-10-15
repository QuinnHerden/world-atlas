"""Choose a projection and a 16:9 extent for each feature."""

import math
from dataclasses import dataclass
from typing import Protocol

import cartopy.crs as ccrs
import numpy as np
import shapely
from pyproj import Transformer
from shapely import unary_union
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from geofeat.model import FrameOptions

ASPECT = 16 / 9
FILL = 0.45  # share of the frame's long axis the highlight should cover
GLOBAL_SPAN_M = 10_000_000  # wider than this goes on a world map
# Every regional frame is at least this wide, so recognisable coastlines are always in view; small features get a ring
MIN_FRAME_M = 2_600_000
EARTH_R_M = 6_371_008
INSET_BELOW_M = 8_000_000  # wider frames show whole continents, and their box on the world inset wraps
# A capital or city with another carded dot this close gets a frame of its own, this wide, centred on it (ADR 0003)
CLOSE_DOT_FRAME_M = 1_000_000

# Country, territory and dispute subjects (spec.framing) are framed on their curriculum region: the box round its
# members' main bodies, REGION_MARGIN larger and at least REGION_MIN_M wide, shared by every card in the region whose
# subject fits inside it SUBJECT_MARGIN in from the edges (others shift or widen theirs). A subject that would still
# fill more than REGION_FILL_MAX of it widens its frame to that fill, unless it is a giant, whose v2.0 frame was over
# GIANT_FRAME_M wide: those keep their v2.0 frames (Russia, Canada, the United States, Greenland, China, India, Japan,
# Myanmar, Indonesia, Australia, DR Congo, Brazil, Argentina, Chile, Peru; Myanmar and Peru sit near the line). A
# scattered Pacific state (Kiribati, French Polynesia) is never a giant: it widens on its sub-frame, with the locator.
REGION_MARGIN = 1.1
REGION_FILL_MAX = 0.35
GIANT_FRAME_M = 8_000_000
REGION_MIN_M = 3_500_000
SUBJECT_MARGIN = 0.04  # of the frame's width
# Parts within GROUP_GAP_M of each other form a group; the largest is the main body. A Pacific subject is fitted by
# its main body alone when that holds MAIN_GROUP_FRAME of its land (Fiji without Rotuma).
GROUP_GAP_M = 300_000
MAIN_GROUP_FRAME, MAIN_GROUP_DETAIL = 0.9, 0.65
# A subject shorter than this on its long axis, or thinner (its largest part's narrowest enclosing rectangle) on its
# short one (px at 1600 wide; 40 and 12 px on a 390 px phone), gets a detail inset of itself (of its main group, if
# that holds MAIN_GROUP_DETAIL of its land), if the inset draws it at least DETAIL_ZOOM times as large
DETAIL_LONG_PX, DETAIL_SHORT_PX = 165, 49
DETAIL_ZOOM = 2.0
DETAIL_FILL = 0.8  # the subject's share of the detail inset, on the 16:9 measure
DETAIL_MIN_M = 300_000  # a microstate's inset still shows the coast or valley round it
DETAIL_SHARE = 0.35  # the inset's share of the card's width (render.py draws it)
CLOSE_DOT_DETAIL_M = CLOSE_DOT_FRAME_M  # a close-dot city's detail inset: at most the v2.0 close-dot frame


class Framed(Protocol):
    """A Feature or a RenderSpec: anything carrying frame options. A RenderSpec may also ask for the world map
    (`world`) or a close-dot frame (`close_dot`, with its `dot`)."""

    @property
    def frame(self) -> FrameOptions: ...


@dataclass(frozen=True)
class Frame:
    projection: ccrs.Projection
    extent: tuple[float, float, float, float] | None  # x0, x1, y0, y1 in projection metres; None = global
    inset: bool  # the world locator
    detail: tuple[float, float, float, float] | None = None  # a detail inset's extent, in the same projection


def centre(geometry: BaseGeometry) -> tuple[float, float]:
    """Lon/lat centre as the mean of vertex unit vectors, so it is right across 180° and near the poles."""
    lon, lat = np.radians(shapely.get_coordinates(geometry.segmentize(1.0))).T
    x, y, z = (np.cos(lat) * np.cos(lon)).mean(), (np.cos(lat) * np.sin(lon)).mean(), np.sin(lat).mean()
    lon_c = math.degrees(math.atan2(y, x)) if math.hypot(x, y) > 0.2 else 0.0  # globe-wrapping: no meaningful centre
    return lon_c, math.degrees(math.atan2(z, math.hypot(x, y)))


def laea(geometry: BaseGeometry) -> ccrs.Projection:
    lon, lat = centre(geometry)
    return ccrs.LambertAzimuthalEqualArea(central_longitude=lon, central_latitude=lat)


def project(geometry: BaseGeometry, projection: ccrs.Projection) -> BaseGeometry:
    """Project lon/lat geometry, first splitting it at the projection's back meridian so nothing wraps."""
    to_proj = Transformer.from_crs("EPSG:4326", projection.proj4_init, always_xy=True)
    seam = (projection.proj4_params.get("lon_0", 0) + 360) % 360 - 180
    eps = 1e-6  # keep vertices off the seam itself, where they could land on either map edge
    pieces = [geometry.intersection(box(-180, -90, seam - eps, 90)), geometry.intersection(box(seam + eps, -90, 180, 90))]
    return unary_union([shapely.make_valid(transform(to_proj.transform, p)) for p in pieces if not p.is_empty])


class Equirectangular(ccrs._RectangularProjection):
    """Plate carrée in metres on a sphere, true to scale along `standard_parallel`: meridians are vertical lines and
    parallels horizontal, so north is straight up everywhere on the map."""

    def __init__(self, central_longitude: float, standard_parallel: float) -> None:
        half_w = math.pi * EARTH_R_M * math.cos(math.radians(standard_parallel))
        self.threshold = half_w / 360
        params = [("proj", "eqc"), ("lon_0", central_longitude), ("lat_ts", standard_parallel), ("units", "m")]
        super().__init__(params, half_w, math.pi / 2 * EARTH_R_M, globe=ccrs.Globe(ellipse=None, semimajor_axis=EARTH_R_M))


def _fit(geometry: BaseGeometry, projection: ccrs.Projection, at: tuple[float, float] | None, min_w: float) -> tuple[float, float, float]:
    """Width and centre (x, y) of the frame: the highlight at FILL, or centred `at` a point, the smallest frame there
    that holds it; never under min_w."""
    x0, y0, x1, y1 = project(geometry, projection).bounds
    if at is not None:
        ox, oy = at
        reach = max(abs(x0 - ox), abs(x1 - ox), abs(y0 - oy) * ASPECT, abs(y1 - oy) * ASPECT)
        return max(2 * reach * 1.15, min_w), ox, oy
    return max(max(x1 - x0, (y1 - y0) * ASPECT) / FILL, min_w), (x0 + x1) / 2, (y0 + y1) / 2


def frame(feature: Framed, geometry: BaseGeometry, region: BaseGeometry | None = None) -> Frame:
    """Fit the highlight in an equirectangular map round its centre (or `frame.centre`), then redraw that frame with
    the projection centred on it, true to scale along its centre parallel, and refit. A highlight wider than
    GLOBAL_SPAN_M, or one the frame can't hold, goes on a world map, as does a spec asking for it (continents). A
    close-dot spec gets CLOSE_DOT_FRAME_M round its dot instead, and a political subject (`framing`) its
    region's frame (unless it is a giant)."""
    world = Frame(Equirectangular(centre(geometry)[0], 0), None, inset=False)
    if getattr(feature, "world", False):
        return world
    if getattr(feature, "framing", None) and region is not None and (political := _political(feature, geometry, region)):
        return political
    if getattr(feature, "close_dot", False):
        return _close_dot(*feature.dot)
    fixed = feature.frame.centre
    lon, lat = fixed or centre(geometry)
    min_w = max(MIN_FRAME_M, (feature.frame.min_span_km or 0) * 1000)
    first = Equirectangular(lon, lat)
    x0, y0, x1, y1 = project(geometry, first).bounds
    if not math.isfinite(x1 - x0 + y1 - y0) or max(x1 - x0, y1 - y0) > GLOBAL_SPAN_M:
        return world

    frame_w, cx, cy = _fit(geometry, first, None if fixed is None else _to_map(first, lon, lat), min_w)
    flon, flat = Transformer.from_crs(first.proj4_init, "EPSG:4326", always_xy=True).transform(cx, cy)
    projection = Equirectangular(flon, flat)
    frame_w, cx, cy = _fit(geometry, projection, _to_map(projection, flon, flat), frame_w)
    frame_w = min(frame_w, 2 * projection.x_limits[1])  # a band round a pole (the Arctic) shows the globe's full width
    pole_y = projection.y_limits[1]
    cy = min(max(cy, -pole_y + frame_w / ASPECT / 2), pole_y - frame_w / ASPECT / 2)  # never show past a pole
    extent = (cx - frame_w / 2, cx + frame_w / 2, cy - frame_w / ASPECT / 2, cy + frame_w / ASPECT / 2)
    fx0, fx1, fy0, fy1 = extent
    if not box(fx0, fy0, fx1, fy1).buffer(frame_w * 1e-6).contains(project(geometry, projection).envelope):
        return world
    return Frame(projection, extent, inset=frame_w < INSET_BELOW_M)


def _long(x0: float, y0: float, x1: float, y1: float) -> float:
    """A box's size on the 16:9 frame: the frame width it would fill."""
    return max(x1 - x0, (y1 - y0) * ASPECT)


def main_group(shape: BaseGeometry) -> tuple[BaseGeometry, float]:
    """The largest group of a projected shape's parts within GROUP_GAP_M of each other, and its share of the area."""
    parts = shapely.get_parts(shape)
    groups = shapely.get_parts(unary_union(shapely.buffer(parts, GROUP_GAP_M / 2, quad_segs=4)))
    members = [unary_union([p for p in parts if g.intersects(p)]) for g in groups]
    main = max(members, key=lambda m: m.area)
    return main, main.area / shape.area if shape.area else 1.0


def _fit_axis(lo: float, size: float, s0: float, s1: float, margin: float) -> tuple[float, float]:
    """An interval [lo, lo + size] moved to hold [s0, s1] `margin` in from its ends, or widened if it can't."""
    need = s1 - s0 + 2 * margin
    if need > size:
        return s0 - margin, need
    return min(max(lo, s1 + margin - size), s0 - margin), size


def _political(feature: Framed, geometry: BaseGeometry, points: BaseGeometry) -> Frame | None:
    """The region's shared frame (from its member points), moved or widened for a subject that doesn't fit it. None
    for a giant, which the caller frames as v2.0 did. A detail inset for a subject under DETAIL_LONG_PX long or
    DETAIL_SHORT_PX thin, or CLOSE_DOT_DETAIL_M round a close dot (a city or capital card, whose subject is its host);
    the world locator only without one, on frames under INSET_BELOW_M, and always on a Pacific sub-frame."""
    framing = feature.framing
    projection = Equirectangular(*centre(points))
    rx0, ry0, rx1, ry1 = project(points, projection).bounds
    width = max(_long(rx0, ry0, rx1, ry1) * REGION_MARGIN, REGION_MIN_M)
    x0, y0 = (rx0 + rx1 - width) / 2, (ry0 + ry1 - width / ASPECT) / 2

    projected = project(geometry, projection)
    if projected.is_empty or not math.isfinite(sum(projected.bounds)):
        return None
    main, share = main_group(projected)
    fit = main if framing == "pacific" and share >= MAIN_GROUP_FRAME else projected
    sx0, sy0, sx1, sy1 = fit.bounds
    margin = SUBJECT_MARGIN * width
    x0, w = _fit_axis(x0, width, sx0, sx1, margin)
    y0, h = _fit_axis(y0, width / ASPECT, sy0, sy1, margin)
    if w > width or h * ASPECT > width:  # widened: keep 16:9 round the widened box
        cx, cy = x0 + w / 2, y0 + h / 2
        width = max(w, h * ASPECT)
        x0, y0 = cx - width / 2, cy - width / ASPECT / 2
    size = _long(sx0, sy0, sx1, sy1)
    scattered = framing == "pacific" and share < MAIN_GROUP_FRAME
    if (size / FILL > GIANT_FRAME_M and not scattered) or width > 2 * projection.x_limits[1]:
        return None
    if size / width > REGION_FILL_MAX:  # widen round the subject's side of the frame
        grown = size / REGION_FILL_MAX
        x0 = min(max(x0 - (grown - width) / 2, sx1 + margin - grown), sx0 - margin)
        y0 = min(max(y0 - (grown - width) / ASPECT / 2, sy1 + margin - grown / ASPECT), sy0 - margin)
        width = grown
    pole_y = projection.y_limits[1]
    y0 = min(max(y0, -pole_y), pole_y - width / ASPECT)
    extent = (x0, x0 + width, y0, y0 + width / ASPECT)

    px = 1600 / width  # px per metre at 1600 wide
    target = main if share >= MAIN_GROUP_DETAIL else projected
    tx0, ty0, tx1, ty1 = target.bounds
    body = max(shapely.get_parts(target), key=lambda p: p.area)
    thin = 0.0  # a degenerate sliver (a line or point after make_valid) is as thin as it gets
    if body.geom_type == "Polygon":
        cx_, cy_ = np.array(shapely.minimum_rotated_rectangle(body).exterior.coords).T
        thin = min(math.hypot(cx_[1] - cx_[0], cy_[1] - cy_[0]), math.hypot(cx_[2] - cx_[1], cy_[2] - cy_[1]))
    detail = None
    if getattr(feature, "close_dot", False):
        dcx, dcy = _to_map(projection, *feature.dot)
        dw = min(CLOSE_DOT_DETAIL_M, width * DETAIL_SHARE / DETAIL_ZOOM)  # tighter in a small region, still 2x
        dcy = min(max(dcy, -pole_y + dw / ASPECT / 2), pole_y - dw / ASPECT / 2)
        detail = (dcx - dw / 2, dcx + dw / 2, dcy - dw / ASPECT / 2, dcy + dw / ASPECT / 2)
    elif max(tx1 - tx0, ty1 - ty0) * px < DETAIL_LONG_PX or thin * px < DETAIL_SHORT_PX:
        dw = max(_long(tx0, ty0, tx1, ty1) / DETAIL_FILL, DETAIL_MIN_M)
        if width / dw * DETAIL_SHARE >= DETAIL_ZOOM:
            dcx, dcy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
            dcy = min(max(dcy, -pole_y + dw / ASPECT / 2), pole_y - dw / ASPECT / 2)  # never past a pole
            detail = (dcx - dw / 2, dcx + dw / 2, dcy - dw / ASPECT / 2, dcy + dw / ASPECT / 2)
    locator = framing == "pacific" or (detail is None and width < INSET_BELOW_M)
    return Frame(projection, extent, inset=locator, detail=detail)


def _close_dot(lon: float, lat: float) -> Frame:
    """CLOSE_DOT_FRAME_M wide, centred on the dot (moved back from a pole), with the inset."""
    projection = Equirectangular(lon, lat)
    half_w, half_h = CLOSE_DOT_FRAME_M / 2, CLOSE_DOT_FRAME_M / ASPECT / 2
    pole_y = projection.y_limits[1]
    cy = min(max(_to_map(projection, lon, lat)[1], -pole_y + half_h), pole_y - half_h)
    return Frame(projection, (-half_w, half_w, cy - half_h, cy + half_h), inset=True)


def _to_map(projection: ccrs.Projection, lon: float, lat: float) -> tuple[float, float]:
    return Transformer.from_crs("EPSG:4326", projection.proj4_init, always_xy=True).transform(lon, lat)
