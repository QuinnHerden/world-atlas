"""Sibling pairs: features near enough to be confused, compared by how their highlights overlap.

Both highlights are drawn as they would appear on one map framing the pair: polygons as filled, lines and points
widened by their stroke. A pair fails when the highlights are near-identical (IoU), or when one covers the other and
both types share a family (`model.FAMILY`: "Pass" and "Corridor" are both land passages), unless one feature declares
the pair in `allow_nested`. Nesting across families ("Delta" in a "River" frame, a "Pass" in a "Mountain range") is
reported as info. World-map features (oceans, global belts) are only compared with each other: a regional card never
shares their frame.
"""

import math
from dataclasses import dataclass

from shapely import unary_union
from shapely.geometry.base import BaseGeometry

from geofeat.frame import Frame, frame, project
from geofeat.model import Feature
from geofeat.style import CARD_PX, RING_PX, STROKE_PX

NEAR_M = 300_000
NEAR_DEG = 3.0  # cheap lon/lat prefilter, a little wider than NEAR_M
IOU_MAX = 0.8
COVER_MAX = 0.9
IOU_NEAR, COVER_NEAR = 0.5, 0.7  # close enough to a limit to be worth a look on the pairs sheet
WORLD_SPAN_M = 40_000_000  # width of a world map (plate carrée, the equator's length)


@dataclass(frozen=True)
class Pair:
    a: str
    b: str
    same_family: bool
    distance_km: float
    iou: float
    cover: float
    allowed: str | None = None  # the `allow_nested` reason, if one feature declares this pair
    inner: str = ""  # the id whose highlight is smaller: the one nested, when the pair nests

    @property
    def flagged(self) -> bool:
        return self.iou >= IOU_MAX or (self.same_family and self.cover >= COVER_MAX and not self.allowed)

    @property
    def nested(self) -> bool:
        return self.cover >= COVER_MAX and not self.flagged

    @property
    def near(self) -> bool:
        return self.iou >= IOU_NEAR or self.cover >= COVER_NEAR

    def __str__(self) -> str:
        mark = "FLAG " if self.flagged else "allowed " if self.allowed and self.nested else "nested " if self.nested else ""
        return f"{mark}{self.a} ~ {self.b}: {self.distance_km:.0f} km, IoU {self.iou:.2f}, cover {self.cover:.2f}"


def _maybe_near(a: BaseGeometry, b: BaseGeometry) -> bool:
    """Cheap lon/lat box test, also trying b shifted a full turn so features either side of 180° meet."""
    ax0, ay0, ax1, ay1 = a.bounds
    bx0, by0, bx1, by1 = b.bounds
    if ay0 - NEAR_DEG > by1 or by0 - NEAR_DEG > ay1:
        return False
    lon_margin = NEAR_DEG / max(math.cos(math.radians(max(abs(ay0), abs(ay1), abs(by0), abs(by1)))), 0.05)
    return any(ax0 - lon_margin <= bx1 + shift and bx0 + shift - lon_margin <= ax1 for shift in (-360, 0, 360))


def _span(f: Frame) -> float:
    return WORLD_SPAN_M if f.extent is None else f.extent[1] - f.extent[0]


def _footprint(feature: Feature, shape: BaseGeometry, span_m: float) -> BaseGeometry:
    if feature.style in ("area", "band"):
        return shape
    px = RING_PX if feature.style == "point" else STROKE_PX[feature.style]
    return shape.buffer(px / 2 / CARD_PX * span_m)


def compare(fa: Feature, ga: BaseGeometry, fb: Feature, gb: BaseGeometry) -> Pair | None:
    union = unary_union([ga, gb])
    shared, other = frame(fa, union), frame(fb, union)
    pa, pb = project(ga, shared.projection), project(gb, shared.projection)
    distance = pa.distance(pb)
    if distance > NEAR_M:
        return None
    span = max(_span(shared), _span(other))
    a, b = _footprint(fa, pa, span), _footprint(fb, pb, span)
    if min(a.area, b.area) == 0:
        return None
    overlap = a.intersection(b).area
    return Pair(
        fa.id, fb.id, fa.family == fb.family, distance / 1000,
        iou=overlap / a.union(b).area, cover=overlap / min(a.area, b.area), allowed=_allowed(fa, fb),
        inner=fa.id if a.area <= b.area else fb.id,
    )


def _allowed(fa: Feature, fb: Feature) -> str | None:
    reasons = [o.reason for o in fa.allow_nested if o.id == fb.id] + [o.reason for o in fb.allow_nested if o.id == fa.id]
    return "; ".join(reasons) or None


def find_pairs(geometries: dict[str, tuple[Feature, BaseGeometry]]) -> list[Pair]:
    items = sorted(geometries.items())
    world = {i for i, (f, g) in items if frame(f, g).extent is None}
    pairs = []
    for i, (ia, (fa, ga)) in enumerate(items):
        for ib, (fb, gb) in items[i + 1:]:
            if (ia in world) == (ib in world) and _maybe_near(ga, gb) and (pair := compare(fa, ga, fb, gb)):
                pairs.append(pair)
    return pairs
