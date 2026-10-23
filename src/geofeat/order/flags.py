"""World Flags' study order (ADR 0012): the flags in data/flags.yaml's order. That order is generated here and checked by
`make check-data`.

`generate` takes each continent in CONTINENTS order and lists its flags in World Atlas's frozen order of those places,
the new-card positions data/positions.lock gives their country and territory cards, so the deck follows World Atlas's
region ring and walks. It then moves as few cards as it can, as short a way as it can, until every look-alike pair on
the continent (FLAGS.lookalikes) is LOOKALIKE_GAP cards apart: never adjacent, never more than 10 apart. Pairs on two
continents are far apart anyway and are only reported.

`python -m geofeat.order.flags` prints each continent's order, every card it moved and every look-alike pair's
distance; `--write` rewrites data/flags.yaml in the generated order, but never reorders cards already in the lock.

Once a card is locked, its position is its place in the deck, so `make check-data` holds the file to the lock: the
locked flags must be listed in the order of their positions, so that `make positions` slots a new flag after the right
card. A look-alike gap broken by a card not yet locked fails the check; one between two locked cards can't be mended
without a new lock series (ADR 0011), so it is only noted. The check doesn't require the generated order, so the lock
can outlive a later change to the generator or the look-alike list."""

import itertools
import sys

import geofeat.positions as positions
from geofeat.card import Card, card_key
from geofeat.decks import FLAGS
from geofeat.order.engine import LOOKALIKE_GAP
from geofeat.polities import read_countries, read_territory_file
from geofeat.sources import flags as source


def continents() -> dict[str, str]:
    """Each active flag's recorded continent."""
    return {f.id: f.continent for f in source.active()}


def locked() -> dict[str, int]:
    """Each active flag that is in the lock: its position."""
    lock = positions.read().positions
    return {f.id: lock[f.uid] for f in source.active() if f.uid in lock}


def place_uids() -> dict[str, str]:
    """Each country's and territory's World Atlas card uid."""
    uids = {c.id: c.uids["country"] for c in read_countries()}
    return uids | {e.id: e.uid for e in read_territory_file() if e.kind == "territory" and e.uid}


def world_order(ids: list[str]) -> list[str]:
    """`ids` in World Atlas's frozen order: their country or territory card's position in the lock."""
    lock, uids = positions.read().positions, place_uids()
    if missing := sorted(i for i in ids if uids.get(i) not in lock):
        raise ValueError(f"no World Atlas position for {missing}")
    return sorted(ids, key=lambda i: lock[uids[i]])


def pairs_within(ids: list[str]) -> list[tuple[str, str]]:
    members = set(ids)
    return [(a, b) for a, b in FLAGS.lookalikes if a in members and b in members]


def gap_ok(distance: int) -> bool:
    return LOOKALIKE_GAP[0] <= distance <= LOOKALIKE_GAP[1]


def _cost(order: list[str], pairs: list[tuple[str, str]], base: dict[str, int]) -> tuple[int, int]:
    """Broken look-alike gaps, then how far the order is from `base`: the pairs of cards it puts the other way round
    (moving one card k slots costs k)."""
    at = {id: i for i, id in enumerate(order)}
    broken = sum(not gap_ok(abs(at[a] - at[b])) for a, b in pairs)
    ranks = [base[id] for id in order]
    return broken, sum(r > later for i, r in enumerate(ranks) for later in ranks[i + 1:])


def moved(order: list[str], natural: list[str]) -> list[str]:
    """The fewest cards whose moves turn `natural` into `order`: those outside a longest run that keeps its order."""
    rank = {id: i for i, id in enumerate(natural)}
    best: list[list[str]] = []  # best[k]: a kept run of length k + 1 ending in the lowest rank found so far
    for id in order:
        k = next((k for k, run in enumerate(best) if rank[run[-1]] > rank[id]), len(best))
        run = (best[k - 1] if k else []) + [id]
        best[k:k + 1] = [run]
    kept = set(best[-1]) if best else set()
    return [id for id in order if id not in kept]


def space(order: list[str], pairs: list[tuple[str, str]]) -> list[str]:
    """`order` with look-alikes spaced: a greedy descent that moves one card to another slot at a time, taking the move
    that most lowers `_cost`, until no move does. Deterministic: ties go to the earliest card and slot."""
    base = {id: i for i, id in enumerate(order)}
    best, cost = list(order), _cost(order, pairs, base)
    while cost[0]:
        candidate = None
        for id in list(best):
            rest = [x for x in best if x != id]
            for slot in range(len(best)):
                trial = rest[:slot] + [id] + rest[slot:]
                if (c := _cost(trial, pairs, base)) < cost:
                    candidate, cost = trial, c
        if candidate is None:
            raise ValueError(f"look-alikes can't all be spaced among {order}")
        best = candidate
    return best


def generate(ids: list[str]) -> list[str]:
    """Every flag id in study order: continent by continent, World Atlas's order within each, look-alikes spaced."""
    continent = continents()
    out = []
    for c in source.CONTINENTS:
        members = world_order([i for i in ids if continent[i] == c])
        out += space(members, pairs_within(members))
    return out


def gaps(order: list[str]) -> list[tuple[str, str, int, bool]]:
    """Every look-alike pair in the deck: its ids, how many cards apart, and whether they share a continent."""
    at = {id: i for i, id in enumerate(order)}
    continent = continents()
    return [(a, b, abs(at[a] - at[b]), continent[a] == continent[b]) for a, b in FLAGS.lookalikes if a in at and b in at]


def reordered(order: list[str], placed: dict[str, int]) -> list[str]:
    """Locked flags that `order` lists before a flag locked ahead of them."""
    seen = [i for i in order if i in placed]
    return [b for a, b in zip(seen, seen[1:]) if placed[b] < placed[a]]


def errors() -> list[str]:
    """Every look-alike must have a flag; the locked flags must be listed in lock order; and a look-alike pair on one
    continent with a card not yet locked must be LOOKALIKE_GAP cards apart."""
    order = [f.id for f in source.active()]
    placed = locked()
    out = [f"{FLAGS.name}: look-alike {i} has no flag" for i in sorted({i for p in FLAGS.lookalikes for i in p} - set(order))]
    out += [f"{source.PATH.name}: {i} is listed after a flag the lock places after it; list the locked flags in lock "
            f"order" for i in reordered(order, placed)]
    out += [f"{FLAGS.name}: look-alikes {a} and {b} are {d} cards apart (want {LOOKALIKE_GAP[0]}-{LOOKALIKE_GAP[1]}); "
            f"run `python -m geofeat.order.flags`" for a, b, d, same in gaps(order)
            if same and not gap_ok(d) and not {a, b} <= set(placed)]
    return out


def notes() -> list[str]:
    """Look-alike gaps between two locked cards that the lock froze outside LOOKALIKE_GAP."""
    placed = locked()
    return [f"{FLAGS.name}: look-alikes {a} and {b} are {d} cards apart, both locked" for a, b, d, same
            in gaps([f.id for f in source.active()]) if same and not gap_ok(d) and {a, b} <= set(placed)]


def study_order(cards: list[Card]) -> list[Card]:
    """World Flags' cards in data/flags.yaml's order."""
    by_key = {c.key: c for c in cards}
    return [by_key[k] for f in source.active() if (k := card_key("flag", f.id)) in by_key]


def rewrite(order: list[str]) -> None:
    """Reorder data/flags.yaml's entries as text blocks, so each keeps its layout; retired entries go last. The file
    must hold entries only, after an optional header of comment lines."""
    if moved_locked := reordered(order, locked()):
        raise SystemExit(f"{source.PATH.name}: the order moves locked flags ({', '.join(moved_locked)}); not rewritten")
    text = source.PATH.read_text()
    header = "".join(itertools.takewhile(lambda line: line.startswith("#"), text.splitlines(keepends=True)))
    body = text[len(header):]
    if not body.startswith("- id: ") or "\n#" in body:
        raise SystemExit(f"{source.PATH.name}: comments between entries; not rewritten")
    blocks = ["- id: " + b for b in body.split("\n- id: ")]
    blocks[0] = blocks[0].removeprefix("- id: ")
    by_id = {b.split("\n", 1)[0].removeprefix("- id: ").strip(): b.strip("\n") for b in blocks}
    retired = [f.id for f in source.load_flags() if f.retired]
    if sorted(order + retired) != sorted(by_id):
        raise SystemExit(f"{source.PATH.name}: the order doesn't hold every entry once; not rewritten")
    source.PATH.write_text(header + "\n".join(by_id[i] for i in order + retired) + "\n")
    print(f"rewrote {source.PATH.name}")


def main() -> None:
    write = sys.argv[1:] == ["--write"]
    ids = [f.id for f in source.active()]
    order = generate(ids)
    continent = continents()
    world = {i: n for n, i in enumerate(world_order(ids))}
    for c in source.CONTINENTS:
        members = [i for i in order if continent[i] == c]
        natural = sorted(members, key=world.get)
        print(f"{c} ({len(members)}): {', '.join(members)}")
        shifts = [f"{i} {natural.index(i) + 1}→{members.index(i) + 1}" for i in moved(members, natural)]
        print(f"  moved: {', '.join(shifts) or 'none'}")
    for a, b, d, same in gaps(order):
        print(f"  {a} ~ {b}: {d} apart" + ("" if same else " (across continents)")
              + ("" if not same or gap_ok(d) else " BROKEN"))
    if write:
        rewrite(order)


if __name__ == "__main__":
    main()
