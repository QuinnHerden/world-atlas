"""World Flags' images: one sanitised SVG per flag in data/flags/<id>.svg, made from an upstream file pinned in
data/flags/sources.lock. The SVGs are committed; a build only copies them into deck/ (geofeat.deckgen), and `make
check-data` holds each to its lock entry and to `errors` below.

A lock entry pins its upstream file one of two ways:

- `repo`, `commit` (a full sha on upstream history) and `path`: a file in a GitHub repo, fetched through `gh api`;
- `commons` (the file page), `url` and `timestamp`: a Wikimedia Commons upload, fetched over HTTPS and checked against
  Commons' own `sha1`.

Each records the download's `sha256` and the sanitised file's `svg_sha256`. `python -m geofeat.flagfiles` re-fetches
every pinned file and rewrites the SVGs, failing on any checksum that differs; `--relock ID...` re-pins those entries
(after editing their source fields) and records their checksums. See CONTRIBUTING.md, "Update a flag".

Sanitising keeps only an allow-list of SVG elements and presentation attributes, so nothing can run or load: no script,
foreignObject, image, link, animation or event attribute, no reference outside the file, and no CSS that imports or
points elsewhere. Anything else fails the fetch for review rather than being silently dropped; only titles,
descriptions, comments and editor metadata are dropped. The root gets a `width` and `height` from its `viewBox`, so the
card's <img> has the flag's own aspect ratio as its intrinsic size."""

import hashlib
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from geofeat.fetch import _blob_sha, _check_upstream, _download, _gh
from geofeat.model import ROOT

FLAG_DIR = ROOT / "data/flags"
LOCK = FLAG_DIR / "sources.lock"
SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
HEIGHT = 400  # the intrinsic height every flag gets; its width follows the viewBox
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_FILES = "https://upload.wikimedia.org/wikipedia/commons/"
USER_AGENT = "world-atlas-flags (https://github.com/QuinnHerden/world-atlas)"

ELEMENTS = frozenset({
    "svg", "g", "defs", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "use", "symbol", "clipPath",
    "mask", "linearGradient", "radialGradient", "stop", "pattern", "style",
})
DROPPED = frozenset({"title", "desc", "metadata"})
ATTRIBUTES = frozenset({
    "id", "class", "d", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "fx", "fy", "width", "height",
    "points", "transform", "viewBox", "preserveAspectRatio", "version", "fill", "fill-opacity", "fill-rule", "stroke",
    "stroke-width", "stroke-opacity", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray",
    "stroke-dashoffset", "opacity", "color", "clip-path", "clip-rule", "clipPathUnits", "mask", "maskUnits",
    "maskContentUnits", "gradientUnits", "gradientTransform", "spreadMethod", "offset", "stop-color", "stop-opacity",
    "patternUnits", "patternContentUnits", "patternTransform", "overflow", "display", "visibility", "paint-order",
    "image-rendering", "shape-rendering", "text-rendering", "color-rendering", "font-family", "font-weight",
    "font-size", "letter-spacing", "word-spacing", "text-anchor", "style", "type", "aria-label", f"{{{XLINK}}}href",
    "href",
})
HREFS = frozenset({f"{{{XLINK}}}href", "href"})
# In an attribute or a <style>: a url() to anything but a fragment of this file, an import, a script URL, an
# old-IE expression, or an escape that could spell any of them
UNSAFE_CSS = re.compile(r"url\(\s*['\"]?(?!#)|@import|javascript:|expression\(|\\", re.IGNORECASE)
# CSS (a `style` attribute or a <style>) is held to an allow-list besides: no quotes, at-rules, slashes or escapes,
# and no function but a colour or a url() to a fragment, since image-set(), src() and the like load files too
CSS_CHARS = re.compile(r"[\w\s#.,:;%(){}*>+!-]*")
CSS_FUNCTIONS = frozenset({"url", "rgb", "rgba", "hsl", "hsla"})
CSS_FUNCTION = re.compile(r"([\w-]*)\s*\(")
MAX_BYTES = 2_000_000  # a download larger than any flag is refused before it is read in full
NUMBER = r"-?[0-9.]+(?:[eE][-+]?[0-9]+)?"
VIEWBOX = re.compile(rf"\s*({NUMBER})[\s,]+({NUMBER})[\s,]+({NUMBER})[\s,]+({NUMBER})\s*")
LENGTH = re.compile(r"([0-9.]+(?:e[0-9]+)?)(?:px)?")  # a root width or height in user units: 900, 1e3px


class UnsafeSvg(ValueError):
    pass


def _local(tag: str) -> tuple[str | None, str]:
    """An element's namespace and local name."""
    if tag.startswith("{"):
        ns, _, name = tag[1:].partition("}")
        return ns, name
    return None, tag


def _problems(root: ET.Element) -> list[str]:
    """Why a parsed SVG isn't safe to ship: what `sanitise` refuses, and what it must already have removed."""
    out = []
    if root.tag != f"{{{SVG}}}svg":
        out.append(f"the root is {root.tag}, not an svg element")
    for element in root.iter():
        ns, name = _local(element.tag)
        if ns != SVG or name not in ELEMENTS:
            out.append(f"element {element.tag} is not allowed")
            continue
        if name == "style" and (len(element) or not _safe_css(element.text or "")):
            out.append("a <style> holds an element, or CSS outside the allow-list")
        for key, value in element.attrib.items():
            if key not in ATTRIBUTES:
                out.append(f"attribute {key} on {name} is not allowed")
            elif key in HREFS and not value.startswith("#"):
                out.append(f"{name} refers outside the file: {value[:60]!r}")
            elif UNSAFE_CSS.search(value) or key == "style" and not _safe_css(value):
                out.append(f"attribute {key} on {name} imports or points outside the file")
    return out


def _safe_css(css: str) -> bool:
    return bool(CSS_CHARS.fullmatch(css)) and not UNSAFE_CSS.search(css) and all(
        m.group(1).lower() in CSS_FUNCTIONS for m in CSS_FUNCTION.finditer(css))


# The SVG 1.0/1.1 DOCTYPE editors still write: a public identifier and no internal subset. ElementTree never fetches
# the DTD, so it is dropped; any other DOCTYPE, which could declare entities, is refused.
SVG_DOCTYPE = re.compile(r'<!DOCTYPE\s+svg\s+PUBLIC\s+"-//W3C//DTD SVG 1\.[01]//EN"\s+"[^"<>\[\]]*"\s*>')


def _parse(text: str) -> ET.Element:
    text = SVG_DOCTYPE.sub("", text, count=1)
    if re.search(r"<!DOCTYPE|<!ENTITY", text, re.IGNORECASE):
        raise UnsafeSvg("has a DOCTYPE or an entity declaration")
    try:
        return ET.fromstring(text)
    except ET.ParseError as exc:
        raise UnsafeSvg(f"is not well-formed XML: {exc}") from None


def _viewbox(root: ET.Element) -> tuple[float, float]:
    """The viewBox's width and height."""
    match = VIEWBOX.fullmatch(root.get("viewBox", ""))
    if not match or float(match.group(3)) <= 0 or float(match.group(4)) <= 0:
        raise UnsafeSvg(f"needs a viewBox, got {root.get('viewBox')!r}")
    return float(match.group(3)), float(match.group(4))


def _size(width: float, height: float) -> tuple[str, str]:
    return f"{HEIGHT * width / height:.2f}".rstrip("0").rstrip("."), str(HEIGHT)


def sanitise(data: bytes) -> str:
    """The upstream SVG as the deck ships it: editor namespaces, titles, descriptions and comments dropped, the size set
    from the viewBox. Raises UnsafeSvg on anything outside the allow-lists."""
    root = _parse(data.decode("utf-8-sig"))
    for parent in list(root.iter()):
        for child in list(parent):
            ns, name = _local(child.tag)
            if ns not in (SVG, None) or ns == SVG and name in DROPPED:  # editor data (sodipodi:, rdf:), titles
                parent.remove(child)
        for key in [k for k in parent.attrib if k.startswith("{") and not k.startswith(f"{{{XLINK}}}")]:
            del parent.attrib[key]  # sodipodi:, inkscape: and other editor attributes
    if problems := _problems(root):
        raise UnsafeSvg("; ".join(sorted(set(problems))))
    width, height = root.attrib.pop("width", None), root.attrib.pop("height", None)
    if "viewBox" not in root.attrib and (w := LENGTH.fullmatch(width or "")) and (h := LENGTH.fullmatch(height or "")):
        root.set("viewBox", f"0 0 {float(w.group(1)):g} {float(h.group(1)):g}")  # a size without a viewBox: its user units
    root.attrib["width"], root.attrib["height"] = _size(*_viewbox(root))
    ET.register_namespace("", SVG)
    ET.register_namespace("xlink", XLINK)
    return ET.tostring(root, encoding="unicode") + "\n"


def errors(text: str) -> list[str]:
    """Why a committed flag SVG isn't one `sanitise` would write: unsafe content, or a size off its viewBox."""
    try:
        root = _parse(text)
        problems = _problems(root)
        if (root.get("width"), root.get("height")) != _size(*_viewbox(root)):
            problems.append(f"width and height must be {_size(*_viewbox(root))}, the viewBox's ratio at height {HEIGHT}")
    except UnsafeSvg as exc:
        return [str(exc)]
    return sorted(set(problems))


def flag_file(id: str) -> Path:
    return FLAG_DIR / f"{id}.svg"


# What a lock entry may name, so an id stays a file name in data/flags/ and a repo and path stay one API path
LOCK_ID = re.compile(r"[a-z0-9][a-z0-9-]*")
LOCK_REPO = re.compile(r"[\w.-]+/[\w.-]+")
LOCK_PATH = re.compile(r"(?!.*\.\.)[\w./-]+\.svg")


def read_lock() -> dict[str, dict]:
    entries = json.loads(LOCK.read_text())
    by_id = {e["id"]: e for e in entries}
    if len(by_id) != len(entries):
        raise ValueError(f"{LOCK.name}: an id appears twice")
    for id, e in by_id.items():
        if not LOCK_ID.fullmatch(id) or "repo" in e and not (LOCK_REPO.fullmatch(e["repo"]) and LOCK_PATH.fullmatch(e["path"])):
            raise ValueError(f"{LOCK.name}: entry {id!r} has an id, repo or path outside the allowed forms")
    return by_id


def lock_errors(ids: list[str]) -> list[str]:
    """Each flag must have a lock entry, and its committed SVG must be the sanitised file the entry records."""
    try:
        lock = read_lock()
    except (OSError, ValueError, KeyError) as exc:
        return [f"{LOCK.name}: {exc}"]
    out = []
    if extra := sorted(set(lock) - set(ids)):
        out.append(f"{LOCK.name}: entries for no flag: {extra}")
    for id in ids:
        path = flag_file(id)
        if id not in lock:
            out.append(f"{id}: no entry in {LOCK.name}")
        elif not path.exists():
            out.append(f"{id}: {path.relative_to(ROOT)} is missing (run `python -m geofeat.flagfiles`)")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != lock[id].get("svg_sha256"):
            out.append(f"{id}: {path.name} differs from the file {LOCK.name} records; regenerate it, never edit it")
        elif problems := errors(path.read_text()):
            out += [f"{id}: {e}" for e in problems]
        elif sanitise(path.read_bytes()) != path.read_text():  # anything the parser hides (a processing instruction)
            out.append(f"{id}: {path.name} is not exactly what sanitising writes; regenerate it")
    return out


def _commons_info(entry: dict) -> dict:
    query = urllib.parse.urlencode({"action": "query", "format": "json", "prop": "imageinfo", "titles": entry["commons"],
                                    "iiprop": "url|sha1|timestamp"})
    with urllib.request.urlopen(urllib.request.Request(f"{COMMONS_API}?{query}", headers={"User-Agent": USER_AGENT}),
                                timeout=60) as response:
        pages = json.load(response)["query"]["pages"]
    return next(iter(pages.values()))["imageinfo"][0]


def _download_entry(entry: dict) -> bytes:
    if "repo" in entry:
        if len(data := _download(entry)) > MAX_BYTES:
            raise SystemExit(f"{entry['id']}: the download is over {MAX_BYTES:,} bytes")
        return data
    if not entry["url"].startswith(COMMONS_FILES):
        raise SystemExit(f"{entry['id']}: a Commons url must start {COMMONS_FILES}")
    with urllib.request.urlopen(urllib.request.Request(entry["url"], headers={"User-Agent": USER_AGENT}),
                                timeout=60) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SystemExit(f"{entry['id']}: the download is over {MAX_BYTES:,} bytes")
    return data


def _verify_upstream(entry: dict, data: bytes) -> dict[str, str]:
    """At relock: the pin is on upstream history and the download is the file upstream serves at it. Returns the
    upstream checksum to record."""
    if "repo" in entry:
        _check_upstream(entry)
        remote = json.loads(_gh(f"repos/{entry['repo']}/contents/{entry['path']}?ref={entry['commit']}"))["sha"]
        if _blob_sha(data) != remote:
            raise SystemExit(f"{entry['id']}: the download does not match the repo's blob sha")
        return {"blob": remote}
    info = _commons_info(entry)
    if info["url"].split("?")[0] != entry["url"] or info["timestamp"] != entry["timestamp"]:
        raise SystemExit(f"{entry['id']}: Commons now serves {info['url']} of {info['timestamp']}; update the entry")
    if hashlib.sha1(data).hexdigest() != info["sha1"]:
        raise SystemExit(f"{entry['id']}: the download does not match Commons' sha1")
    return {"sha1": info["sha1"]}


def fetch(lock: dict[str, dict], relock: set[str]) -> None:
    """Download each pinned file, check it (or, for `relock`, pin it), and write its sanitised SVG."""
    FLAG_DIR.mkdir(exist_ok=True)
    for id, entry in lock.items():
        data = _download_entry(entry)
        pins = _verify_upstream(entry, data) if id in relock else {}
        if id not in relock and hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise SystemExit(f"{id}: the download's checksum differs from {LOCK.name}" + (
                "; Commons serves only a file's latest upload, so a new one there means re-pinning it"
                if "commons" in entry else ""))
        try:
            svg = sanitise(data)
        except UnsafeSvg as exc:
            raise SystemExit(f"{id}: {exc}") from None
        digest = hashlib.sha256(svg.encode()).hexdigest()
        if id not in relock and digest != entry["svg_sha256"]:
            raise SystemExit(f"{id}: the sanitised file's checksum differs from {LOCK.name} (did sanitise change?)")
        flag_file(id).write_text(svg)
        if id in relock:  # only once its SVG is written, so the lock never records a file that isn't there
            for key in ("blob", "sha1"):
                entry.pop(key, None)
            entry |= pins | {"sha256": hashlib.sha256(data).hexdigest(), "svg_sha256": digest}
        print(f"{'relocked' if id in relock else 'fetched'} {id}")


def main() -> None:
    """`flagfiles [ID...]` re-fetches those flags (default: all) at their pins; `flagfiles --relock ID...` re-pins."""
    args = sys.argv[1:]
    relocking = args[:1] == ["--relock"]
    ids = args[1:] if relocking else args
    lock = read_lock()
    if relocking and not ids or not set(ids) <= set(lock):
        sys.exit("usage: python -m geofeat.flagfiles [ID...] | --relock ID...  (IDs from data/flags/sources.lock)")
    try:
        fetch({id: e for id, e in lock.items() if not ids or id in ids}, set(ids) if relocking else set())
    finally:
        if relocking:  # the entries relocked before any failure
            LOCK.write_text(json.dumps(list(lock.values()), indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
