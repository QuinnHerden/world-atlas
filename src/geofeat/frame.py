"""Choose a projection and a 16:9 extent for each feature."""

import math
from dataclasses import dataclass, replace
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
# members' main bodies, REGION_MARGIN larger and at least REGION_MIN_M wide ("region"), or a sub-frame's fixed box
# ("fixed"), shared by every card on it whose subject fits SUBJECT_MARGIN in from the edges (others shift or widen
# theirs). A subject that would still fill more than REGION_FILL_MAX of it widens its frame to that fill, unless it is
# a giant, whose v2.0 frame was over GIANT_FRAME_M wide: those keep their v2.0 frames (Russia, Canada, the United
# States, Greenland, China, India, Japan, Myanmar, Indonesia, Australia, DR Congo, Brazil, Argentina, Chile, Peru;
# Myanmar and Peru sit near the line). A scattered state (Kiribati, French Polynesia) is never a giant, nor is a subject
# inside its sub-frame's box. No political card has the world locator.
REGION_MARGIN = 1.1
REGION_FILL_MAX = 0.35
GIANT_FRAME_M = 8_000_000
REGION_MIN_M = 3_500_000
SUBJECT_MARGIN = 0.04  # of the frame's width
# Parts within GROUP_GAP_M of each other form a group; the largest is the main body, which a detail inset shows. A
# state whose main body holds less than MAIN_GROUP_DETAIL of its land is scattered (Kiribati, French Polynesia): no
# inset, and never a giant.
GROUP_GAP_M = 300_000
MAIN_GROUP_DETAIL = 0.65
# A subject gets a detail inset when its land, where it is shown, is no bigger than a disc DETAIL_DISC_PX across (px at
# 1600 wide; 14 px on a 390 px phone). Area alone decides, so a long, thin but sizeable state (Tajikistan, Malawi,
# Chile) doesn't qualify, and states of a size are treated alike. The inset must draw it at least DETAIL_ZOOM times as
# large.
DETAIL_DISC_PX = 56
DETAIL_ZOOM = 2.0
DETAIL_FILL = 0.8  # the subject's share of the detail inset, on the 16:9 measure
DETAIL_MIN_M = 200_000  # a microstate's inset still shows the coast or valley round it
DETAIL_SHARE = 0.35  # the inset's share of the card's width (render.py draws it)
CLOSE_DOT_DETAIL_M = CLOSE_DOT_FRAME_M  # a close-dot city's detail inset: at most the v2.0 close-dot frame
CITY_DETAIL_MAX_M = 1_200_000  # any other city's inset: its host whole if that fits, else this much round the dot


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
    # what the inset shows on the main map, in the same projection: its subject's convex hull, or a close dot. The
    # leader lines run from it; nothing is drawn round it, so it never covers a small neighbour (Rwanda, Burundi)
    mark: BaseGeometry | None = None


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
    if getattr(feature, "framing", None) and region is not None:
        political = _political(feature, geometry, region)
        if political is not None:
            return political
        v2 = feature.model_copy(update={"framing": None})  # only a RenderSpec carries `framing`
        giant = replace(frame(v2, geometry), inset=False)  # a giant: its v2.0 frame
        if feature.dot is None or feature.close_dot or giant.extent is None:  # a close dot's frame is already local
            return giant
        host, _ = main_group(project(geometry, giant.projection))
        return replace(giant, **_city_detail(feature, giant.projection, host, giant.extent[1] - giant.extent[0]))
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
    """The region's shared frame (from its member or box points), moved or widened for a subject that doesn't fit it.
    None for a giant, which the caller frames as v2.0 did. A detail inset for a subject small at this scale, or
    CLOSE_DOT_DETAIL_M round a close dot (a city or capital card, whose subject is its host), with its box."""
    projection = Equirectangular(*centre(points))
    rx0, ry0, rx1, ry1 = project(points, projection).bounds
    width = _long(rx0, ry0, rx1, ry1)
    if feature.framing == "region":
        width = max(width * REGION_MARGIN, REGION_MIN_M)
    x0, y0 = (rx0 + rx1 - width) / 2, (ry0 + ry1 - width / ASPECT) / 2

    projected = project(geometry, projection)
    if projected.is_empty or not math.isfinite(sum(projected.bounds)):
        return None
    main, share = main_group(projected)
    sx0, sy0, sx1, sy1 = projected.bounds
    margin = SUBJECT_MARGIN * width
    x0, w = _fit_axis(x0, width, sx0, sx1, margin)
    y0, h = _fit_axis(y0, width / ASPECT, sy0, sy1, margin)
    if w > width or h * ASPECT > width:  # widened: keep 16:9 round the widened box
        cx, cy = x0 + w / 2, y0 + h / 2
        width = max(w, h * ASPECT)
        x0, y0 = cx - width / 2, cy - width / ASPECT / 2
    size = _long(sx0, sy0, sx1, sy1)
    # A subject inside its sub-frame's box keeps the box, however large (French Polynesia measures as a giant by a
    # hair); one that overflows it, Australia on Melanesia's, is still a giant.
    boxed = feature.framing != "region" and rx0 <= sx0 and sx1 <= rx1 and ry0 <= sy0 and sy1 <= ry1
    giant = not boxed and size / FILL > GIANT_FRAME_M and share >= MAIN_GROUP_DETAIL
    if giant or width > 2 * projection.x_limits[1]:
        return None
    if size / width > REGION_FILL_MAX:  # widen round the subject's side of the frame
        grown = size / REGION_FILL_MAX
        x0 = min(max(x0 - (grown - width) / 2, sx1 + margin - grown), sx0 - margin)
        y0 = min(max(y0 - (grown - width) / ASPECT / 2, sy1 + margin - grown / ASPECT), sy0 - margin)
        width = grown
    pole_y = projection.y_limits[1]
    y0 = min(max(y0, -pole_y), pole_y - width / ASPECT)
    extent = (x0, x0 + width, y0, y0 + width / ASPECT)

    if getattr(feature, "dot", None) is not None:  # a capital or city: always an inset round its dot
        return Frame(projection, extent, inset=False, **_city_detail(feature, projection, main, width))
    if share < MAIN_GROUP_DETAIL and getattr(feature, "inset", None) is not True:
        return Frame(projection, extent, inset=False)  # scattered: no main body to show
    tx0, ty0, tx1, ty1 = main.bounds  # outlying specks (Rodrigues, Rotuma) neither size nor fill the inset
    inset_km = getattr(feature, "inset_km", None)
    dw = inset_km * 1000 if inset_km else max(_long(tx0, ty0, tx1, ty1) / DETAIL_FILL, DETAIL_MIN_M)
    wanted = getattr(feature, "inset", None)
    if wanted is None:
        disc = 2 * math.sqrt(main.area / math.pi)
        wanted = disc < DETAIL_DISC_PX * width / 1600 and width / dw * DETAIL_SHARE >= DETAIL_ZOOM
    if not wanted:
        return Frame(projection, extent, inset=False)
    detail = _window(projection, (tx0 + tx1) / 2, (ty0 + ty1) / 2, dw)
    return Frame(projection, extent, inset=False, detail=detail, mark=main.convex_hull)


def _window(projection: ccrs.Projection, cx: float, cy: float, width: float) -> tuple[float, float, float, float]:
    """A 16:9 extent `width` wide round (cx, cy), moved back from a pole."""
    pole_y = projection.y_limits[1]
    cy = min(max(cy, -pole_y + width / ASPECT / 2), pole_y - width / ASPECT / 2)
    return cx - width / 2, cx + width / 2, cy - width / ASPECT / 2, cy + width / ASPECT / 2


def _city_detail(feature: Framed, projection: ccrs.Projection, host: BaseGeometry, width: float) -> dict:
    """A capital's or city's inset (no 2x rule): CLOSE_DOT_DETAIL_M round a close dot, as tight as a small region
    needs; otherwise its host's main body at DETAIL_FILL, at least DETAIL_MIN_M and at most CITY_DETAIL_MAX_M wide,
    centred on the host when that keeps the dot well inside, else on the dot."""
    x, y = _to_map(projection, *feature.dot)
    if getattr(feature, "close_dot", False):
        dw, cx, cy = min(CLOSE_DOT_DETAIL_M, width * DETAIL_SHARE / DETAIL_ZOOM), x, y
    else:
        tx0, ty0, tx1, ty1 = host.bounds
        dw = min(max(_long(tx0, ty0, tx1, ty1) / DETAIL_FILL, DETAIL_MIN_M), CITY_DETAIL_MAX_M)
        cx, cy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
        if abs(x - cx) > 0.4 * dw or abs(y - cy) > 0.4 * dw / ASPECT:
            cx, cy = x, y
    return {"detail": _window(projection, cx, cy, dw), "mark": shapely.Point(x, y)}


def _close_dot(lon: float, lat: float) -> Frame:
    """CLOSE_DOT_FRAME_M wide, centred on the dot (moved back from a pole), with the inset."""
    projection = Equirectangular(lon, lat)
    half_w, half_h = CLOSE_DOT_FRAME_M / 2, CLOSE_DOT_FRAME_M / ASPECT / 2
    pole_y = projection.y_limits[1]
    cy = min(max(_to_map(projection, lon, lat)[1], -pole_y + half_h), pole_y - half_h)
    return Frame(projection, (-half_w, half_w, cy - half_h, cy + half_h), inset=True)


def _to_map(projection: ccrs.Projection, lon: float, lat: float) -> tuple[float, float]:
    return Transformer.from_crs("EPSG:4326", projection.proj4_init, always_xy=True).transform(lon, lat)
