"""Geometry facts the curriculum order needs, from the real data: each feature's region (regions.py), the countries of
that region it touches with the share of each it holds and their outline IoU, and the distance between same-family
features within the pair check's reach. Measuring needs the Natural Earth outlines, so the facts are cached in
build/frames.json. The key hashes every data file the facts read and all of geofeat's code: coarse, so a policy edit
in curriculum.yaml or the code re-measures too, but never stale. The policy itself (openers, which pairs count as
look-alikes) is applied in geofeat.order.inputs."""

import hashlib
import json
from dataclasses import asdict, dataclass

from shapely.geometry.base import BaseGeometry

from geofeat.model import BUILD, FEATURES, GEOMETRY, LOCK, ROOT, active, load_features, orientation

CACHE = BUILD / "frames.json"
SCHEMA = 3
TOUCH_DEG = 0.5  # a feature this close to a country frames it: a strait or sea touches its shores


@dataclass(frozen=True)
class Facts:
    region: int
    touches: tuple[str, ...]  # countries of its own region within TOUCH_DEG, in curriculum order
    held: dict[str, float]  # share of each touched country's area inside the feature
    iou: dict[str, float]  # each touched country's outline against the feature's


@dataclass(frozen=True)
class GeometryFacts:
    features: dict[str, Facts]  # by feature id
    same_family: list[tuple[str, str, float, float]]  # feature ids, km apart and cover, same family, within pairs.NEAR_M


def inputs_hash() -> str:
    """Every data file the facts read, and all of geofeat's code: coarse, but never stale."""
    h = hashlib.sha256(f"schema {SCHEMA}\0".encode())
    data = ROOT / "data"
    paths = (FEATURES, LOCK, data / "countries.yaml", data / "territories.yaml", data / "curriculum.yaml",
             *sorted((ROOT / "src/geofeat").rglob("*.py")), *sorted(GEOMETRY.glob("*.geojson")))
    for path in paths:
        content = path.read_bytes()
        h.update(f"{path.relative_to(ROOT)}\0{len(content)}\0".encode() + content)
    return h.hexdigest()


def _iou(a: BaseGeometry, b: BaseGeometry) -> float:
    union = a.union(b).area
    return a.intersection(b).area / union if union else 0.0


def compute() -> GeometryFacts:
    from geofeat import pairs, regions
    from geofeat.countries_ne import outline
    from geofeat.resolve import resolve

    ring = regions.ring()
    outlines = regions.region_outlines()
    shapes: dict[str, BaseGeometry] = {}
    features = [f for f in active(load_features()) if not orientation(f)]
    geometries = {f.id: resolve(f) for f in features}
    facts = {}
    for feature in features:
        geometry = geometries[feature.id]
        region = regions.derive(feature, geometry, outlines).region
        near = geometry.buffer(TOUCH_DEG)
        touches, held, iou = [], {}, {}
        for country in ring[region].countries:
            if country not in shapes:
                shapes[country] = outline(country)
            shape = shapes[country]
            if near.intersects(shape):
                touches.append(country)
                held[country] = shape.intersection(geometry).area / shape.area if shape.area else 0.0
                iou[country] = _iou(geometry, shape)  # in lon/lat: fine for these sizes, distorted near the poles
        facts[feature.id] = Facts(region, tuple(touches), held, iou)
    same_family = []
    for i, a in enumerate(features):
        for b in features[i + 1:]:
            ga, gb = geometries[a.id], geometries[b.id]
            if a.family == b.family and pairs._maybe_near(ga, gb) and (pair := pairs.compare(a, ga, b, gb)):
                same_family.append((*sorted((a.id, b.id)), pair.distance_km, pair.cover))
    return GeometryFacts(facts, sorted(same_family))


def load() -> GeometryFacts:
    """The facts, from the cache while its inputs are unchanged."""
    key = inputs_hash()
    try:
        cached = json.loads(CACHE.read_text())
        if cached["inputs"] == key:
            return GeometryFacts(
                {k: Facts(v["region"], tuple(v["touches"]), v["held"], v["iou"]) for k, v in cached["features"].items()},
                [(a, b, km, cover) for a, b, km, cover in cached["same_family"]])
    except (OSError, ValueError, KeyError, TypeError):
        pass  # missing, stale or unreadable: recompute
    facts = compute()
    BUILD.mkdir(exist_ok=True)
    data = {"inputs": key, "features": {k: asdict(f) for k, f in sorted(facts.features.items())},
            "same_family": facts.same_family}
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n")
    tmp.replace(CACHE)
    return facts
