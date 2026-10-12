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
INSET_BELOW_M = 5_000_000  # frames narrower than this get a locator globe
MIN_SPAN_M = {"point": 600_000, "strait": 600_000}
SHORT_STRAIT_M = 50_000
SHORT_STRAIT_SPAN_M = 400_000
MIN_SPAN_SMALL_AREA_M = 800_000
SMALL_AREA_M = 50_000


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


def frame(feature: Feature, geometry: BaseGeometry) -> Frame:
    """Fit the highlight, or with `frame.centre`, the smallest frame on that centre that still holds it."""
    fixed = feature.frame.centre
    projection = laea(geometry) if fixed is None else ccrs.LambertAzimuthalEqualArea(*fixed)
    x0, y0, x1, y1 = project(geometry, projection).bounds
    width, height = x1 - x0, y1 - y0

    if not math.isfinite(width + height) or max(width, height) > GLOBAL_SPAN_M:
        return Frame(ccrs.EqualEarth(central_longitude=centre(geometry)[0]), None, inset=False)

    if fixed is None:
        frame_w = max(width, height * ASPECT) / FILL
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    else:
        frame_w = 2 * max(abs(x0), abs(x1), abs(y0) * ASPECT, abs(y1) * ASPECT) * 1.15
        cx, cy = 0.0, 0.0
    if feature.frame.min_span_km:
        frame_w = max(frame_w, feature.frame.min_span_km * 1000)
    elif feature.style == "strait" and max(width, height) < SHORT_STRAIT_M:
        frame_w = max(frame_w, SHORT_STRAIT_SPAN_M)
    elif feature.style in MIN_SPAN_M:
        frame_w = max(frame_w, MIN_SPAN_M[feature.style])
    elif max(width, height) < SMALL_AREA_M:
        frame_w = max(frame_w, MIN_SPAN_SMALL_AREA_M)
    frame_h = frame_w / ASPECT

    extent = (cx - frame_w / 2, cx + frame_w / 2, cy - frame_h / 2, cy + frame_h / 2)
    return Frame(projection, extent, inset=frame_w < INSET_BELOW_M)
