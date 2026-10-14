"""Turn cards into render jobs, key them, and render the ones the cache doesn't hold. Nothing here changes pixels,
so this module isn't in the cache key; render.py and the modules it draws with are."""

import gc
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry.base import BaseGeometry

import geofeat.ne as ne
from geofeat.card import Card
from geofeat.model import BUILD, DECK, LOCK, MEDIA_INDEX, ROOT, VENDOR
from geofeat.render import render
from geofeat.resolve import features_by_id
from geofeat.sources import all_cards
from geofeat.spec import BASEMAP_LAYERS, RELIEF, RenderSpec

CACHE = BUILD / "render-cache.json"  # cache key -> rendered PNG name
JOBS = int(os.environ.get("JOBS", "1"))  # each worker loads its own copy of the basemap layers; ~1.5 GB per worker

RENDERER = ("render.py", "frame.py", "ne.py", "style.py", "spec.py")  # what render() runs; hashed into every key
GEOMETRY_DECIMALS = 7  # degrees: ~1 cm, far below a pixel, and above float noise between runs


@cache
def _code_hash(root: Path) -> str:
    h = hashlib.sha256()
    for name in RENDERER:
        h.update(name.encode() + b"\0" + (root / "src/geofeat" / name).read_bytes())
    h.update((root / "uv.lock").read_bytes())
    return h.hexdigest()


def _basemap_files() -> list[str]:
    return sorted({f"ne_{name}.geojson" for name in BASEMAP_LAYERS} | {RELIEF})


def _check_vendor() -> None:
    """The key trusts the lock's sha256 for the basemap files, so check the bytes in vendor/ match it (vendor/ may
    be shared with another checkout). Selector layers needn't be checked: what they resolve to is hashed."""
    _basemap_hash(LOCK)  # fails clearly on a missing or duplicate entry
    pinned = {Path(e["path"]).name: e["sha256"] for e in json.loads(LOCK.read_text())}
    for file in _basemap_files():
        with open(VENDOR / file, "rb") as f:
            actual = hashlib.file_digest(f, "sha256").hexdigest()
        if actual != pinned[file]:
            raise ValueError(f"vendor/{file} doesn't match {LOCK.name}; run make fetch")


@cache
def _basemap_hash(lock: Path) -> str:
    """The pinned sha256 of every basemap layer and the relief raster. Only the content hash counts, so a relock
    that leaves a file's bytes unchanged doesn't re-render, and entries for other layers don't count at all."""
    entries = json.loads(lock.read_text())
    by_name = {Path(entry["path"]).name: entry["sha256"] for entry in entries}
    if len(by_name) != len(entries):
        raise ValueError(f"{lock.name}: two entries share a file name")
    files = _basemap_files()
    if missing := [f for f in files if f not in by_name]:
        raise ValueError(f"not in {lock.name}: {missing}")
    return hashlib.sha256(json.dumps({f: by_name[f] for f in files}, sort_keys=True).encode()).hexdigest()


def geometry_hash(geometry: BaseGeometry, directed: bool = False) -> str:
    """A geometry's identity: coordinates rounded to GEOMETRY_DECIMALS (and -0 made 0), normalised so vertex and
    part order don't count. A `directed` geometry (a flow line, whose arrows follow its vertex order and whose
    first part anchors the unwrap across 180°) isn't normalised."""
    rounded = shapely.transform(geometry, lambda xy: np.round(xy, GEOMETRY_DECIMALS) + 0.0)
    return hashlib.sha256(shapely.to_wkb(rounded if directed else shapely.normalize(rounded))).hexdigest()


@dataclass(frozen=True)
class RenderJob:
    """Everything render() takes for one card, and its cache key."""

    spec: RenderSpec
    geometry: BaseGeometry
    context: tuple[BaseGeometry, ...] = ()
    former: BaseGeometry | None = None

    def key(self) -> str:
        """The cache key: the spec's visual fields, the geometry it draws, the renderer's code and uv.lock, and the
        basemap's pinned data. Renaming, re-tiering or retyping a card, editing model.py or a selector, or pinning
        a layer the basemap doesn't draw changes nothing unless the geometry or spec changes."""
        h = hashlib.sha256()
        for part in (
            _code_hash(ROOT),
            _basemap_hash(LOCK),
            json.dumps(self.spec.model_dump(mode="json"), sort_keys=True),  # defaults included, so a new field counts
            geometry_hash(self.geometry, directed=self.spec.style.startswith("flow")),
            *(f"context {geometry_hash(g)}" for g in self.context),
            f"former {geometry_hash(self.former)}" if self.former is not None else "former none",
        ):
            h.update(part.encode() + b"\0")
        return h.hexdigest()

    def render(self) -> bytes:
        return render(self.spec, self.geometry, self.context, self.former)


def card_job(card: Card) -> RenderJob:
    return RenderJob(*card.render.resolve())


def _render_to_file(job: RenderJob) -> str:
    png = job.render()
    file = f"{hashlib.sha256(png).hexdigest()[:12]}.png"
    tmp = DECK / f"{file}.{os.getpid()}.tmp"
    tmp.write_bytes(png)
    tmp.replace(DECK / file)
    return file


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def render_cards(cards: list[Card]) -> dict[str, str]:
    """Render what the cache lacks, write media.json (card key -> PNG) and drop the PNGs and cache entries no card
    uses. Everything is keyed by Card.key, so two kinds may share an id, and the cleanup spans every kind."""
    DECK.mkdir(exist_ok=True)
    BUILD.mkdir(exist_ok=True)
    cache_ = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    jobs = {c.key: card_job(c) for c in cards}
    keys = {key: job.key() for key, job in jobs.items()}
    todo = [key for key in jobs if not (keys[key] in cache_ and (DECK / cache_[keys[key]]).exists())]

    def done(key: str, file: str) -> None:
        cache_[keys[key]] = file
        _write_json(CACHE, cache_)
        print(f"rendered {key} -> {file}", flush=True)

    if JOBS <= 1:  # in this process, so the layers loaded to resolve the jobs aren't loaded a second time
        for key in todo:
            done(key, _render_to_file(jobs[key]))
    else:
        todo_jobs = {key: jobs[key] for key in todo}
        del jobs
        ne.layer.cache_clear()  # don't fork n copies of the layers the parent loaded to resolve
        features_by_id.cache_clear()
        gc.collect()
        with ProcessPoolExecutor(max_workers=JOBS) as pool:
            futures = {pool.submit(_render_to_file, todo_jobs[key]): key for key in todo}
            try:
                for future in as_completed(futures):
                    done(futures[future], future.result())
            except BaseException:
                pool.shutdown(cancel_futures=True)
                raise

    media = {key: cache_[keys[key]] for key in keys}
    _write_json(MEDIA_INDEX, media)
    for stale in {p.name for p in DECK.glob("*.png")} - set(media.values()):
        (DECK / stale).unlink()
    _write_json(CACHE, {k: v for k, v in cache_.items() if v in media.values()})
    print(f"rendered {len(todo)} of {len(keys)} cards")
    return media


def main() -> None:
    _check_vendor()
    render_cards(all_cards())


if __name__ == "__main__":
    main()
