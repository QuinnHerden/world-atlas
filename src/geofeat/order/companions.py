"""A companion deck's study order (ADR 0012): its subdivisions in the order data/subdivisions.yaml lists them, which is
a neighbour walk over their adjacency graph. The graph comes from the Natural Earth admin-1 outlines as the country
graph does (ADR 0008): land edges, and for an island with none, sea edges up to SEA_KM (Sicilia and Calabria, Prince
Edward Island). Two subdivisions that both have land neighbours get no sea edge: within 100 km "across water" is often
across a third state's land (Illinois and Arkansas). It is cached
in build/subdivision-adjacency.json, keyed by a hash of its inputs.

`python -m geofeat.order.companions` prints each deck's walk, its jumps and its look-alike gaps; `--write` rewrites
data/subdivisions.yaml in the generated order. `make check-data` fails on a listed order whose step borders nothing
before it, unless nothing in the walk so far could have been reached (an island state, Alaska, Hawaii)."""

import json
import sys
from pathlib import Path

import shapely

from shapely.geometry.base import BaseGeometry

from geofeat import adjacency, ne, polities, resolve
from geofeat.card import Card, card_key
from geofeat.decks import SUBDIVISION_DECKS, DeckInfo
from geofeat.model import BUILD, LOCK
from geofeat.order.engine import LOOKALIKE_GAP
from geofeat.order.walk import Adjacency
from geofeat.sources import subdivisions

CACHE = BUILD / "subdivision-adjacency.json"
SEA_KM = 100.0  # tighter than the country graph's 200 km: these are neighbours inside one country


def geometry_key(country: str) -> str:
    specs = json.dumps({s.id: [p.model_dump() for p in s.geometry] for s in subdivisions.of_country(country)}, sort_keys=True)
    files = [Path(__file__), *(Path(m.__file__) for m in (adjacency, resolve, polities, ne)), LOCK]
    return adjacency._hash(files, f"{shapely.__version__} {shapely.geos_version_string}\0{specs}")


def graph(country: str) -> dict[str, set[str]]:
    """Each subdivision's neighbours: within LAND_KM, or for an island, SEA_KM across water."""
    ids = [s.id for s in subdivisions.of_country(country)]
    data = adjacency._read(CACHE)
    key = geometry_key(country)
    entry = data.get(country, {})
    if entry.get("key") != key:
        outlines: dict[str, BaseGeometry] = subdivisions.outlines(country)
        edges = adjacency.compute_edges(outlines)
        landed = {i for e in edges if e.kind == "land" for i in e.pair}
        edges = [e for e in edges if e.kind == "land" or e.km <= SEA_KM and not set(e.pair) <= landed]
        entry = {"key": key, "edges": [[e.a, e.b, e.km] for e in edges]}
        adjacency._write(CACHE, data | {country: entry})
    out: dict[str, set[str]] = {i: set() for i in ids}
    for a, b, _ in entry["edges"]:
        if a in out and b in out:
            out[a].add(b)
            out[b].add(a)
    return out


def generate(deck: DeckInfo, adj: Adjacency, nodes: list[str]) -> list[str]:
    """The walk from `deck.entry`, grown as order.walk.generate grows a region's (a connected frontier, the step whose
    latest bordering card is the most recent first, then Warnsdorff's rule, then id), except that a step with a
    look-alike among the last LOOKALIKE_GAP[0] - 1 cards waits while another frontier step is open. With no frontier
    left it jumps to the first unvisited in `nodes` (Alaska, then Hawaii)."""
    like: dict[str, set[str]] = {}
    for a, b in deck.lookalikes:
        like.setdefault(a, set()).add(b)
        like.setdefault(b, set()).add(a)
    walk, rank = [deck.entry], {deck.entry: 0}
    members = set(nodes)
    while len(walk) < len(nodes):
        unvisited = members - set(walk)
        frontier = sorted(n for n in unvisited if adj[n] & rank.keys())
        recent = set(walk[-(LOOKALIKE_GAP[0] - 1):])
        if frontier:
            def key(n: str) -> tuple[bool, int, int, str]:
                return (bool(like.get(n, set()) & recent), -max(rank[m] for m in adj[n] if m in rank),
                        len(adj[n] & unvisited), n)
            step = min(frontier, key=key)
        else:
            step = next(n for n in nodes if n in unvisited)
        rank[step] = len(walk)
        walk.append(step)
    return walk


def breaks(walk: list[str], adj: Adjacency) -> list[str]:
    """Steps that border nothing before them although something unvisited did: the walk jumped while it could step."""
    out = []
    for i, n in enumerate(walk[1:], 1):
        seen, rest = set(walk[:i]), set(walk[i:])
        if not adj[n] & seen and any(adj[m] & seen for m in rest):
            out.append(n)
    return out


def lookalike_gaps(deck: DeckInfo, walk: list[str]) -> list[str]:
    at = {n: i for i, n in enumerate(walk)}
    return [f"{a} and {b} are {abs(at[a] - at[b])} cards apart (wants {LOOKALIKE_GAP[0]}-{LOOKALIKE_GAP[1]})"
            for a, b in deck.lookalikes if a in at and b in at
            and not LOOKALIKE_GAP[0] <= abs(at[a] - at[b]) <= LOOKALIKE_GAP[1]]


def study_order(cards: list[Card]) -> list[Card]:
    """The companion decks' cards, deck by deck in registry order, each in data/subdivisions.yaml's (walk) order."""
    by_key = {c.key: c for c in cards}
    return [by_key[k] for deck in SUBDIVISION_DECKS for s in subdivisions.of_country(deck.country)
            if (k := card_key("subdivision", s.id)) in by_key]


def errors() -> list[str]:
    """The listed order of each deck must be a walk from its entry, without avoidable jumps; look-alikes name members."""
    out = []
    for deck in SUBDIVISION_DECKS:
        walk = [s.id for s in subdivisions.of_country(deck.country)]
        if not walk:
            continue
        if walk[0] != deck.entry:
            out.append(f"{deck.name}: data/subdivisions.yaml must list {deck.entry} first (the walk's entry)")
        if unknown := sorted({i for pair in deck.lookalikes for i in pair} - set(walk)):
            out.append(f"{deck.name}: look-alikes name unknown subdivisions {unknown}")
        out += [f"{deck.name}: {n} borders nothing before it in data/subdivisions.yaml; run "
                f"`python -m geofeat.order.companions --write`" for n in breaks(walk, graph(deck.country))]
    return out


def main() -> None:
    write = sys.argv[1:] == ["--write"]
    orders = {}
    for deck in SUBDIVISION_DECKS:
        nodes = [s.id for s in subdivisions.of_country(deck.country)]
        adj = graph(deck.country)
        walk = generate(deck, adj, nodes)
        orders[deck.country] = walk
        jumps = [f"{a}→{b}" for a, b in zip(walk, walk[1:]) if b not in adj[a]]
        print(f"{deck.name} ({len(walk)}): {', '.join(walk)}")
        print(f"  jumps: {', '.join(jumps) or 'none'}")
        for gap in lookalike_gaps(deck, walk):
            print(f"  look-alikes {gap}")
    if write:
        rewrite(orders)


def rewrite(orders: dict[str, list[str]]) -> None:
    """Reorder data/subdivisions.yaml's entries as text blocks, so each keeps its layout: each deck's entries in its
    walk order, decks in registry order, retired entries after their deck's. The file must hold entries only (no
    comments between them, which would move with the entry before them)."""
    text = subdivisions.PATH.read_text()
    if not text.startswith("- id: ") or "\n#" in text:
        raise SystemExit("data/subdivisions.yaml: comments or a header; not rewritten")
    blocks = ["- id: " + b for b in text.split("\n- id: ")]
    blocks[0] = blocks[0].removeprefix("- id: ")
    by_id = {b.split("\n", 1)[0].removeprefix("- id: ").strip(): b.strip("\n") for b in blocks}
    entries = {s.id: s for s in subdivisions.load_subdivisions()}
    order = [i for deck in SUBDIVISION_DECKS for i in orders.get(deck.country, [])
             + [s.id for s in entries.values() if s.country == deck.country and s.retired]]
    if sorted(order) != sorted(by_id):
        raise SystemExit("data/subdivisions.yaml: entries outside the companion decks; not rewritten")
    subdivisions.PATH.write_text("\n\n".join(by_id[i] for i in order) + "\n")
    print(f"rewrote {subdivisions.PATH.name}")


if __name__ == "__main__":
    main()
