"""Choose a projection and a 16:9 extent for each feature."""

import math
from dataclasses import dataclass

import cartopy.crs as ccrs
import numpy as np
import shapely
from pyproj import Transformer
from shapely import unary_union
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

from geofeat.model import Feature

ASPECT = 16 / 9
FILL = 0.45  # share of the frame's long axis the highlight should cover
GLOBAL_SPAN_M = 10_000_000  # wider than this goes on a world map
# Every regional frame is at least this wide, so recognisable coastlines are always in view; small features get a ring
MIN_FRAME_M = 2_600_000
EARTH_R_M = 6_371_008
INSET_BELOW_M = 8_000_000  # wider frames show whole continents, and their box on the world inset wraps


@dataclass(frozen=True)
class Frame:
    projection: ccrs.Projection
    extent: tuple[float, float, float, float] | None  # x0, x1, y0, y1 in projection metres; None = global
    inset: bool


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


def frame(feature: Feature, geometry: BaseGeometry) -> Frame:
    """Fit the highlight in an equirectangular map round its centre (or `frame.centre`), then redraw that frame with
    the projection centred on it, true to scale along its centre parallel, and refit. A highlight wider than
    GLOBAL_SPAN_M, or one the frame can't hold, goes on a world map."""
    fixed = feature.frame.centre
    lon, lat = fixed or centre(geometry)
    min_w = max(MIN_FRAME_M, (feature.frame.min_span_km or 0) * 1000)
    world = Frame(Equirectangular(centre(geometry)[0], 0), None, inset=False)
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


def _to_map(projection: ccrs.Projection, lon: float, lat: float) -> tuple[float, float]:
    return Transformer.from_crs("EPSG:4326", projection.proj4_init, always_xy=True).transform(lon, lat)
