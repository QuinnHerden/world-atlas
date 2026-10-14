"""The neighbour walk over a region's countries (ADR 0009, docs/world-atlas-plan.md#walking-the-countries)."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

Adjacency = Mapping[str, frozenset[str] | set[str]]


@dataclass(frozen=True)
class Walk:
    nodes: tuple[str, ...]
    frozen: bool  # read from curriculum.yaml rather than generated

    def jumps(self, adjacency: Adjacency) -> list[tuple[str, str]]:
        """Consecutive countries that don't border."""
        return [(a, b) for a, b in zip(self.nodes, self.nodes[1:]) if b not in adjacency.get(a, ())]

    def breaks(self, adjacency: Adjacency) -> list[str]:
        """Countries that border none introduced before them: the frontier rule's jumps."""
        return [n for i, n in enumerate(self.nodes[1:], 1) if not adjacency.get(n, set()) & set(self.nodes[:i])]


def generate(nodes: Sequence[str], entry: str, exit: str, adjacency: Adjacency) -> tuple[str, ...]:
    """A deterministic walk from `entry` that grows a connected frontier and ends at or near `exit`.

    Each step takes a country bordering one already introduced, preferring the one whose latest introduced neighbour
    is the most recent, then the fewest unvisited neighbours (Warnsdorff's rule), then id. `exit` is held back while
    any other country can be taken. When nothing borders the walk, it jumps to the first unvisited country in `nodes`
    (the curriculum's listed order, which is geographic), so the jump goes where a person would put it.
    """
    members = set(nodes)
    if entry not in members or exit not in members:
        raise ValueError(f"entry {entry!r} and exit {exit!r} must be among {sorted(members)}")
    adj = {n: set(adjacency.get(n, ())) & members for n in nodes}
    walk = [entry]
    rank = {entry: 0}
    while len(walk) < len(nodes):
        unvisited = members - set(walk)
        frontier = sorted(n for n in unvisited if adj[n] & rank.keys())
        held = [n for n in frontier if n != exit] or frontier
        if held:
            def key(n: str) -> tuple[int, int, str]:
                return -max(rank[m] for m in adj[n] if m in rank), len(adj[n] & unvisited), n
            step = min(held, key=key)
        else:
            rest = [n for n in nodes if n in unvisited]
            step = next((n for n in rest if n != exit), rest[0])
        rank[step] = len(walk)
        walk.append(step)
    return tuple(walk)


def region_walk(nodes: Sequence[str], entry: str, exit: str, adjacency: Adjacency,
                frozen: Sequence[str] | None = None) -> Walk:
    """The frozen walk if there is one, checked to cover exactly the walk nodes from `entry`; otherwise generated."""
    if frozen:
        if sorted(frozen) != sorted(nodes) or frozen[0] != entry:
            raise ValueError(f"frozen walk {list(frozen)} must start at {entry!r} and cover exactly {sorted(nodes)}")
        return Walk(tuple(frozen), True)
    return Walk(generate(nodes, entry, exit, adjacency), False)
