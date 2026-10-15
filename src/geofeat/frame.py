"""Choose a projection and a 16:9 extent for each feature."""

import math
from dataclasses import dataclass
from typing import Literal, Protocol

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

# Country, territory and dispute subjects (spec.framing). Fill is the subject's share of the frame, measured on the
# 16:9 frame (its width against the frame's, its height against the frame's height), so tall thin states behave.
# The band the neighbourhood's frame is clamped to. The floor is 0.19, not 0.15: a subject taller than wide at 15%
# fills 135 of the 900 px height, under DETAIL_LONG_PX, and would get a detail inset it doesn't need.
FILL_MAX, FILL_MIN = 0.30, 0.19
POLITICAL_MIN_M = 2_600_000  # however small the subject, the main map is regional; a detail inset shows its shape
MAX_FRAME_M = 8_000_000  # roughly a continent: the band never widens a frame past this, nor past the old FILL fit
# A subject shorter than this on its long axis, or thinner (its largest part's narrowest enclosing rectangle) on its
# short one, gets a detail inset
# (px at 1600 wide; 40 and 12 px on a 390 px phone), if the inset draws it at least DETAIL_ZOOM times as large
DETAIL_LONG_PX, DETAIL_SHORT_PX = 165, 49
DETAIL_ZOOM = 1.5
DETAIL_FILL = 0.8  # the subject's share of the detail inset, on the same 16:9 measure
DETAIL_MIN_M = 300_000  # a microstate's inset still shows the coast or valley round it
DETAIL_SHARE = 0.35  # the inset's share of the card's width (render.py draws it)
REMOTE_MARGIN = 1.3  # a remote subject's frame holds it and its landmass with this much room, off the edges


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
    # "cap": MAX_FRAME_M held the frame narrower than the band asked; "remote": the nearest landmass lay too far
    capped: Literal["cap", "remote"] | None = None


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


def frame(feature: Framed, geometry: BaseGeometry, neighbours: tuple[BaseGeometry, ...] = ()) -> Frame:
    """Fit the highlight in an equirectangular map round its centre (or `frame.centre`), then redraw that frame with
    the projection centred on it, true to scale along its centre parallel, and refit. A highlight wider than
    GLOBAL_SPAN_M, or one the frame can't hold, goes on a world map, as does a spec asking for it (continents). A
    close-dot spec gets CLOSE_DOT_FRAME_M round its dot instead, and a political subject (`framing`) its
    neighbourhood's frame."""
    world = Frame(Equirectangular(centre(geometry)[0], 0), None, inset=False)
    if getattr(feature, "world", False):
        return world
    if getattr(feature, "close_dot", False):
        return _close_dot(*feature.dot)
    if getattr(feature, "framing", None):
        return _political(feature.framing, geometry, neighbours) or world
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


def _political(framing: str, geometry: BaseGeometry, neighbours: tuple[BaseGeometry, ...]) -> Frame | None:
    """The subject's bbox grown by a typical neighbour's width on every side (the median of the neighbours' largest
    parts, so one giant neighbour doesn't set it), clamped to the FILL_MIN-FILL_MAX band, at least POLITICAL_MIN_M,
    and capped at MAX_FRAME_M unless the old FILL fit is wider. A remote subject's frame grows to take in the nearest
    landmass, unless that would pass MAX_FRAME_M; then it keeps the band's frame and the locator. A subject under
    DETAIL_LONG_PX long or DETAIL_SHORT_PX thin gets a detail inset; the locator shows only without one, on frames
    under INSET_BELOW_M. None: the subject needs the world map."""
    first = Equirectangular(*centre(geometry))
    sx0, sy0, sx1, sy1 = project(geometry, first).bounds
    if not math.isfinite(sx1 - sx0 + sy1 - sy0) or max(sx1 - sx0, sy1 - sy0) > GLOBAL_SPAN_M:
        return None
    size = _long(sx0, sy0, sx1, sy1)
    cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    shapes = [project(n, first) for n in neighbours]
    shapes = [s for s in shapes if not s.is_empty]
    if framing == "neighbours" and shapes:
        widths = [max(b[2] - b[0], b[3] - b[1]) for s in shapes
                  for b in [max(shapely.get_parts(s), key=lambda p: p.area).bounds]]
        grow = float(np.median(widths))
        want = _long(sx0 - grow, sy0 - grow, sx1 + grow, sy1 + grow)
    else:
        want = size / FILL_MAX
    width = max(min(max(want, size / FILL_MAX), size / FILL_MIN), POLITICAL_MIN_M)
    limit = max(MAX_FRAME_M, size / FILL)
    capped = "cap" if width > limit else None
    width = min(width, limit)
    locator = width < INSET_BELOW_M and framing != "remote"  # a remote subject's landmass orients it instead
    if framing == "remote" and shapes:
        ux0, uy0, ux1, uy1 = unary_union([box(sx0, sy0, sx1, sy1), *shapes]).bounds
        reach = _long(ux0, uy0, ux1, uy1) * REMOTE_MARGIN
        if reach <= MAX_FRAME_M:
            width, cx, cy = max(width, reach), (ux0 + ux1) / 2, (uy0 + uy1) / 2
        else:
            capped, locator = "remote", True

    flon, flat = Transformer.from_crs(first.proj4_init, "EPSG:4326", always_xy=True).transform(cx, cy)
    projection = Equirectangular(flon, flat)
    ox, oy = _to_map(projection, flon, flat)
    sx0, sy0, sx1, sy1 = project(geometry, projection).bounds
    reach = max(abs(sx0 - ox), abs(sx1 - ox), abs(sy0 - oy) * ASPECT, abs(sy1 - oy) * ASPECT)
    width = min(max(width, 2.2 * reach), 2 * projection.x_limits[1])  # recentred, it still holds the subject
    pole_y = projection.y_limits[1]
    oy = min(max(oy, -pole_y + width / ASPECT / 2), pole_y - width / ASPECT / 2)
    extent = (ox - width / 2, ox + width / 2, oy - width / ASPECT / 2, oy + width / ASPECT / 2)
    if not box(extent[0], extent[2], extent[1], extent[3]).buffer(width * 1e-6).contains(box(sx0, sy0, sx1, sy1)):
        return None

    px = 1600 / width  # px per metre at 1600 wide
    long = max(sx1 - sx0, sy1 - sy0)
    main = max(shapely.get_parts(project(geometry, projection)), key=lambda p: p.area)
    thin = 0.0  # a degenerate sliver (a line or point after make_valid) is as thin as it gets
    if main.geom_type == "Polygon":
        rx, ry = np.array(shapely.minimum_rotated_rectangle(main).exterior.coords).T
        thin = min(math.hypot(rx[1] - rx[0], ry[1] - ry[0]), math.hypot(rx[2] - rx[1], ry[2] - ry[1]))
    dw = max(_long(sx0, sy0, sx1, sy1) / DETAIL_FILL, DETAIL_MIN_M)
    detail = None
    if (long * px < DETAIL_LONG_PX or thin * px < DETAIL_SHORT_PX) and width / dw * DETAIL_SHARE >= DETAIL_ZOOM:
        dcx, dcy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
        dcy = min(max(dcy, -pole_y + dw / ASPECT / 2), pole_y - dw / ASPECT / 2)  # never past a pole
        detail = (dcx - dw / 2, dcx + dw / 2, dcy - dw / ASPECT / 2, dcy + dw / ASPECT / 2)
    return Frame(projection, extent, inset=locator and (detail is None or capped == "remote"),
                 detail=detail, capped=capped)


def _close_dot(lon: float, lat: float) -> Frame:
    """CLOSE_DOT_FRAME_M wide, centred on the dot (moved back from a pole), with the inset."""
    projection = Equirectangular(lon, lat)
    half_w, half_h = CLOSE_DOT_FRAME_M / 2, CLOSE_DOT_FRAME_M / ASPECT / 2
    pole_y = projection.y_limits[1]
    cy = min(max(_to_map(projection, lon, lat)[1], -pole_y + half_h), pole_y - half_h)
    return Frame(projection, (-half_w, half_w, cy - half_h, cy + half_h), inset=True)


def _to_map(projection: ccrs.Projection, lon: float, lat: float) -> tuple[float, float]:
    return Transformer.from_crs("EPSG:4326", projection.proj4_init, always_xy=True).transform(lon, lat)
