"""Each physical feature's Frame from the real data: the region regions.py assigns it, and the countries of that region
its shape touches. Measuring needs the Natural Earth outlines, so the result is cached in build/frames.json, keyed by
a hash of everything it reads, as the pair check's siblings.json is."""

import hashlib
import json

from shapely.geometry.base import BaseGeometry

from geofeat.card import card_key
from geofeat.model import BUILD, FEATURES, GEOMETRY, LOCK, ROOT, active, load_features, orientation
from geofeat.order.engine import Frame

CACHE = BUILD / "frames.json"
TOUCH_DEG = 0.5  # a feature this close to a country frames it: a strait or sea touches its shores
OPENS_SHARE = 0.5  # a region frame feature opens the cluster of the first country it holds this much of, else
# the one it holds most of
# Region frame features open their region, or the cluster of their first country (docs/world-atlas-plan.md, "Placing
# each card type"). Policy that belongs in data/curriculum.yaml once its schema has a place for it.
REGION_FRAMES = frozenset({
    "iberian-peninsula", "italian-peninsula", "balkan-peninsula", "arabian-peninsula", "korean-peninsula",
    "malay-peninsula", "anatolia", "levant",
})
SCHEMA = 1


def inputs_hash() -> str:
    """Every data file the frames read, and all of geofeat's code: coarse, but never stale."""
    h = hashlib.sha256(f"schema {SCHEMA}\0".encode())
    data = ROOT / "data"
    paths = (FEATURES, LOCK, data / "countries.yaml", data / "territories.yaml", data / "curriculum.yaml",
             *sorted((ROOT / "src/geofeat").rglob("*.py")), *sorted(GEOMETRY.glob("*.geojson")))
    for path in paths:
        content = path.read_bytes()
        h.update(f"{path.relative_to(ROOT)}\0{len(content)}\0".encode() + content)
    return h.hexdigest()


def compute() -> dict[str, Frame]:
    from geofeat import regions
    from geofeat.countries_ne import outline
    from geofeat.resolve import resolve

    ring = regions.ring()
    outlines = regions.region_outlines()
    shapes: dict[str, BaseGeometry] = {}
    frames = {}
    for feature in active(load_features()):
        if orientation(feature):
            continue
        geometry = resolve(feature)
        region = regions.derive(feature, geometry, outlines).region
        opens = feature.id in REGION_FRAMES
        near = geometry.buffer(TOUCH_DEG)
        countries, held = [], {}
        for country in ring[region].countries:
            if country not in shapes:
                shapes[country] = outline(country)
            shape = shapes[country]
            if opens and shape.area > 0:
                held[country] = shape.intersection(geometry).area / shape.area
                if held[country] >= OPENS_SHARE:
                    countries.append(country)
            elif near.intersects(shape):
                countries.append(country)
        if opens and not countries and held:  # a peninsula split from most of every state (Malaysia, Thailand)
            countries.append(max(held, key=lambda c: (held[c], c)))
        frames[card_key("feature", feature.id)] = Frame(region, tuple(countries), opens)
    return frames


def load() -> dict[str, Frame]:
    """The frames, from the cache while its inputs are unchanged."""
    key = inputs_hash()
    try:
        cached = json.loads(CACHE.read_text())
        if cached["inputs"] == key:
            return {k: Frame(v["region"], tuple(v["countries"]), v["opens"]) for k, v in cached["frames"].items()}
    except (OSError, ValueError, KeyError, TypeError):
        pass  # missing or unreadable: recompute
    frames = compute()
    BUILD.mkdir(exist_ok=True)
    data = {"inputs": key, "frames": {k: {"region": f.region, "countries": list(f.countries), "opens": f.opens}
                                      for k, f in sorted(frames.items())}}
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n")
    tmp.replace(CACHE)
    return frames
