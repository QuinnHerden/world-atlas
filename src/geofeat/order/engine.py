"""The curriculum order (ADR 0009). The engine first builds the ring order: orientation, then pass 1 and
pass 2 round the ring of regions. The study order is cut from it in four blocks (`blocks`): continents, countries
(with territories and disputed areas), physical features, then capitals and cities.

Within a region the countries follow the neighbour walk, and every other card hangs off one already placed:

- a capital comes 2-3 cards after its country;
- a pocket (a microstate, territory or dispute with a `host`) and a city without an anchor feature come right after
  the host's or country's capital;
- a physical feature comes right after the last country of its region that frames it, or just before the first one
  when it opens the region (the Iberian Peninsula); one that no country frames closes the region;
- a city with an `anchor` comes right after that feature.

In pass 2 the countries and capitals are already known, so they are placeholders: their cards aren't there, but the
cards that hang off them keep the walk's order. Local repair then applies, in precedence order, parent before child,
the capital's 2-3 card gap, no two cards with the same id side by side, and look-alikes 3-10 cards apart within a
region. Walk countries never move, so the frontier rule outranks all of these. What can't be repaired is reported.

Everything here is a pure function of its arguments: no set iteration order or float decides a tie, and every
tie-break ends in an id.
"""

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from geofeat.card import Card, Pass
from geofeat.curriculum import Curriculum, Region
from geofeat.order.walk import Adjacency, Walk, region_walk

CAPITAL_GAP = (2, 3)
LOOKALIKE_GAP = (3, 10)
REPAIR_REACH = 12  # how far a repair may move a card
CONTINENTS = ("europe", "africa", "asia", "oceania", "north-america", "south-america", "antarctica")  # ring order
OCEANS = ("atlantic-ocean", "indian-ocean", "pacific-ocean", "arctic-ocean")
WINDS = ("trade-winds", "westerlies")


class OrderError(ValueError):
    """The data can't be ordered: a card with no place, a cycle, a bad frozen walk."""


@dataclass(frozen=True)
class Frame:
    """Where a physical feature sits: its region, the countries of that region it touches, and whether it opens the
    region (or the cluster of its first country) as an advance organiser."""

    region: int
    countries: tuple[str, ...] = ()
    opens: bool = False


@dataclass
class RegionReport:
    study_pass: Pass
    region: Region
    walk: Walk
    jumps: list[tuple[str, str]]
    breaks: list[str]
    waivers: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Ordering:
    cards: list[Card]  # the study order: the four blocks (`blocks`)
    reports: list[RegionReport]  # of the ring order
    waivers: list[str]  # those that belong to no one region: parents in a later pass, moved parents, seams
    ring: list[Card] = field(default_factory=list)  # the interleaved ring order the blocks are cut from


Frames = Mapping[str, Frame] | Callable[[Card], Frame | None]


def lookup(frames: Frames) -> Callable[[Card], Frame | None]:
    return frames if callable(frames) else (lambda c: frames.get(c.key))  # type: ignore[union-attr]


def orientation_rank(card: Card) -> tuple[int, int, str]:
    """Continents, then oceans, then the planetary winds, each in a fixed order; anything else after, by id."""
    for group, ids in enumerate((CONTINENTS, OCEANS, WINDS)):
        if card.id in ids:
            return group, ids.index(card.id), card.id
    if card.kind == "continent" or card.prompt == "Continent":
        return 0, len(CONTINENTS), card.id
    if card.prompt == "Ocean":
        return 1, len(OCEANS), card.id
    return 3, 0, card.id


def walks(curriculum: Curriculum, adjacency: Adjacency, frozen: Mapping[str, Sequence[str]] | None = None) -> dict[int, Walk]:
    """Each region's walk: `frozen[slug]` (tests), else the region's frozen `walk` in curriculum.yaml, else generated."""
    frozen = frozen or {}
    if unknown := sorted(set(frozen) - {r.slug for r in curriculum.regions}):
        raise OrderError(f"frozen walks for unknown regions: {unknown}")
    out = {}
    for r in curriculum.regions:
        nodes = [c for c in r.countries if c not in r.pockets]
        try:
            out[r.number] = region_walk(nodes, r.entry, r.exit, adjacency, frozen.get(r.slug) or r.walk)
        except ValueError as exc:
            raise OrderError(f"{r.slug}: {exc}") from exc
    return out


def curriculum_order(cards: Iterable[Card], curriculum: Curriculum, adjacency: Adjacency, frames: Frames,
                     edges: Iterable[tuple[str, str]] = (), lookalikes: Iterable[tuple[str, str]] = (),
                     frozen: Mapping[str, Sequence[str]] | None = None) -> Ordering:
    """Every card in the ideal study order, and what the order had to waive.

    `adjacency` maps a country id to the ids it borders (by land or sea edge). `frames` gives each non-orientation
    feature card's Frame, by key or as a function. `edges` are extra (parent key, child key) pairs, on top of each
    card's own `parents`. `lookalikes` are pairs of keys to keep 3-10 cards apart within a region. `frozen` overrides
    the walks by region slug.
    """
    cards = sorted(cards, key=lambda c: c.key)
    frame_of = lookup(frames)
    parents = _parents(cards, edges)
    by_number = {r.number: r for r in curriculum.regions}
    region_walks = walks(curriculum, adjacency, frozen)

    orientation: list[Card] = []
    segments: dict[tuple[Pass, int], list[Card]] = {}
    problems = []
    for c in cards:
        if c.study_pass == "orientation":
            orientation.append(c)
            continue
        region = region_of(c, frame_of)
        if region not in by_number:
            problems.append(f"{c.key}: region {region} is not in the curriculum")
            continue
        segments.setdefault((c.study_pass, region), []).append(c)
    if problems:
        raise OrderError("; ".join(problems))

    entries: list[tuple[Card, tuple[Pass, int]]] = [(c, ("orientation", 0)) for c in sorted(orientation, key=orientation_rank)]
    anchors: dict[str, str] = {}
    for study in (1, 2):
        for number in sorted(by_number):
            seg = segments.get((study, number), [])
            if seg:
                placed, seg_anchors = _place(seg, by_number[number], region_walks[number], frame_of, parents)
                entries += [(c, (study, number)) for c in placed]
                anchors |= seg_anchors

    waivers: list[str] = []
    entries = _parents_first(entries, parents, waivers, anchors)
    lookalike_pairs = sorted({tuple(sorted(p)) for p in lookalikes if p[0] != p[1]})
    walk_nodes = {f"country:{n}" for w in region_walks.values() for n in w.nodes}
    reports: list[RegionReport] = []
    ordered: list[Card] = list(c for c, s in entries if s[0] == "orientation")
    for study in (1, 2):
        for number in sorted(by_number):
            seg = [c for c, s in entries if s == (study, number)]
            if not seg:
                continue
            members = {c.key for c in seg}
            pairs = [(a, b) for a, b in lookalike_pairs if a in members and b in members]
            ctx = _Context(parents, anchors, pairs, walk_nodes)
            seg = _repair(seg, ctx)
            ordered += seg
            walk = region_walks[number]
            reports.append(RegionReport(study, by_number[number], walk, walk.jumps(adjacency), walk.breaks(adjacency),
                                        _waivers(seg, ctx)))
    segment = {c.key: seg for c, seg in entries}
    waivers += [f"{a.key} and {b.key} share an id and sit side by side" for a, b in zip(ordered, ordered[1:])
                if a.id == b.id and (segment[a.key] != segment[b.key] or segment[a.key][0] == "orientation")]
    study = blocks(ordered, curriculum, region_walks)
    study, study_waivers = _block_lookalikes(study, segment, parents, lookalike_pairs)
    return Ordering(study, reports, waivers + study_waivers, ordered)


def _block_lookalikes(cards: list[Card], segment: Mapping[str, tuple[Pass, int]], parents: Mapping[str, tuple[str, ...]],
                      pairs: list[tuple[str, str]]) -> tuple[list[Card], list[str]]:
    """The look-alike window in the study order, where cutting the blocks out of the ring closes up the gaps. Within
    each run of features of one ring segment the cards are repaired as in the ring (parent before child first); the
    countries block keeps its walk, so a pair there is only reported, as is anything repair can't fix."""
    out: list[Card] = []
    i = 0
    while i < len(cards):
        j = i
        while j < len(cards) and cards[j].block == cards[i].block and segment[cards[j].key] == segment[cards[i].key]:
            j += 1
        run = cards[i:j]
        if run[0].block == "features" and len(run) > 1:
            members = {c.key for c in run}
            run = _repair(run, _Context(parents, {}, [(a, b) for a, b in pairs if a in members and b in members], set()))
        out += run
        i = j
    pos = {c.key: n for n, c in enumerate(out)}
    by_key = {c.key: c for c in out}
    waivers = []
    for a, b in pairs:
        if a in pos and b in pos and by_key[a].block == by_key[b].block and segment[a][1] == segment[b][1]:
            gap = abs(pos[a] - pos[b])
            if not LOOKALIKE_GAP[0] <= gap <= LOOKALIKE_GAP[1]:
                waivers.append(f"study order: look-alikes {a} and {b} are {gap} cards apart "
                               f"(wants {LOOKALIKE_GAP[0]}-{LOOKALIKE_GAP[1]})")
    return out, waivers


def blocks(ring: list[Card], curriculum: Curriculum, region_walks: Mapping[int, Walk]) -> list[Card]:
    """The study order (ADR 0009), cut from the ring order in four blocks:

    1. continents, in ring order (CONTINENTS);
    2. countries, territories and disputed areas, region by region round the ring: each walk node, then its pocket
       countries (in member order), then the territories and disputes it hosts (in curriculum order);
    3. physical features in their ring order: orientation (oceans, then planetary winds), pass 1 round the ring, then
       pass 2, which keeps parent before child;
    4. capitals and cities, region by region in the same country order: each country's capital, then its cities in
       ring order (core before secondary).
    """
    by_key = {c.key: c for c in ring}
    cities: dict[str, list[Card]] = {}
    for c in ring:
        if c.kind == "city":
            country = next((p.removeprefix("country:") for p in c.parents if p.startswith("country:")), None)
            if country is None:
                raise OrderError(f"{c.key}: no country parent")
            cities.setdefault(country, []).append(c)
    political: list[str] = []
    towns: list[Card] = []
    for r in sorted(curriculum.regions, key=lambda r: r.number):
        for node in region_walks[r.number].nodes:
            members = [node, *(p for p in r.countries if r.pockets.get(p) == node)]
            political += [f"country:{m}" for m in members]
            political += [f"{kind}:{i}" for kind, group in (("territory", r.territories), ("dispute", r.disputes))
                          for i, host in group.items() if host == node]
            for m in members:
                towns += [by_key[k] for k in (f"capital:{m}",) if k in by_key] + cities.pop(m, [])
    out = [c for c in ring if c.kind == "continent"]
    out += [by_key[k] for k in political if k in by_key]
    out += [c for c in ring if c.kind == "feature"] + towns
    if missing := sorted({c.key for c in ring} - {c.key for c in out}):
        raise OrderError(f"no block place for {missing}")
    return out


def region_of(card: Card, frame_of: Callable[[Card], Frame | None]) -> int:
    """The ring region a card is ordered in: a feature's frame region, otherwise the card's own."""
    if card.kind == "feature":
        frame = frame_of(card)
        if frame is None:
            raise OrderError(f"{card.key}: no frame (its region and the countries it touches)")
        return frame.region
    if card.region is None:
        raise OrderError(f"{card.key}: no region")
    return int(card.region)


def _parents(cards: list[Card], edges: Iterable[tuple[str, str]]) -> dict[str, tuple[str, ...]]:
    """Each key's parent keys among the cards, from the cards' own `parents` and `edges`. Raises on a cycle."""
    keys = {c.key for c in cards}
    sets: dict[str, set[str]] = {c.key: {p for p in c.parents if p in keys} for c in cards}
    for p, child in edges:
        if p in keys and child in keys and p != child:
            sets[child].add(p)
    state: dict[str, int] = {}

    def visit(k: str) -> None:
        state[k] = 1
        for p in sorted(sets[k]):
            if state.get(p) == 1:
                raise OrderError(f"dependency cycle through {p} and {k}")
            if p not in state:
                visit(p)
        state[k] = 2

    for k in sorted(sets):
        if k not in state:
            visit(k)
    return {k: tuple(sorted(v)) for k, v in sets.items()}


def _topological(keys: list[str], parents: Mapping[str, tuple[str, ...]], rank: Callable[[str], tuple]) -> list[str]:
    """`keys` with each parent among them before its child, otherwise by `rank`."""
    members = set(keys)
    waiting = {k: {p for p in parents.get(k, ()) if p in members} for k in keys}
    out: list[str] = []
    while waiting:
        ready = sorted((k for k, ps in waiting.items() if not ps), key=rank)
        pick = ready[0]
        out.append(pick)
        del waiting[pick]
        for ps in waiting.values():
            ps.discard(pick)
    return out


def _place(cards: list[Card], region: Region, walk: Walk, frame_of: Callable[[Card], Frame | None],
           parents: Mapping[str, tuple[str, ...]]) -> tuple[list[Card], dict[str, str]]:
    """One region's cards of one pass, in anchored order, and each placed card's anchor key."""
    present = {c.key: c for c in cards}
    rank = {n: (i, 0) for i, n in enumerate(walk.nodes)}
    rank |= {p: (rank[h][0], 1) for p, h in region.pockets.items() if h in rank}
    member_order = {c: i for i, c in enumerate(region.countries)}
    children: dict[str, list[str]] = {}
    before: dict[str, list[str]] = {}
    trailing: list[str] = []
    anchors: dict[str, str] = {}
    problems: list[str] = []

    def hang(key: str, under: str) -> None:
        children.setdefault(under, []).append(key)
        anchors[key] = under

    for p in sorted(region.pockets, key=member_order.__getitem__):
        hang(f"country:{p}", f"capital:{region.pockets[p]}")
    for c in cards:
        if c.kind in ("country", "capital"):
            if c.id not in rank:
                problems.append(f"{c.key}: not a country of region {region.number}")
            elif c.kind == "country" and c.host and c.host != f"country:{region.pockets.get(c.id)}":
                problems.append(f"{c.key}: host {c.host} isn't its curriculum host")
        elif c.kind in ("territory", "dispute"):
            host = (c.host or "").removeprefix("country:")
            if host != region.placed().get(c.id):
                problems.append(f"{c.key}: host {c.host} isn't its curriculum host in region {region.number}")
            elif host not in rank:
                problems.append(f"{c.key}: host {c.host} is not a country of region {region.number}")
            else:
                hang(c.key, f"capital:{host}")
        elif c.kind == "city":
            country = next((p.removeprefix("country:") for p in c.parents if p.startswith("country:")), None)
            if c.anchor and c.anchor in present:
                hang(c.key, c.anchor)
            elif country in rank:
                hang(c.key, f"capital:{country}")
            else:
                problems.append(f"{c.key}: its country {country} is not in region {region.number}")
        elif c.kind == "feature":
            frame = frame_of(c)
            assert frame is not None  # region_of checked
            framing = sorted((n for n in frame.countries if n in rank), key=lambda n: (rank[n], n))
            if frame.opens:
                before.setdefault(f"country:{framing[0] if framing else walk.nodes[0]}", []).append(c.key)
            elif framing:
                hang(c.key, f"country:{framing[-1]}")
            else:
                trailing.append(c.key)
        else:
            problems.append(f"{c.key}: a {c.kind} card has no place in a ring region")
    if problems:
        raise OrderError("; ".join(problems))

    def sibling_rank(k: str) -> tuple:
        c = present.get(k)
        kind_rank = ("feature", "country", "territory", "dispute", "city").index(k.split(":")[0])
        return (kind_rank, member_order.get(k.removeprefix("country:"), 0) if k.startswith("country:") else 0,
                c.tier if c else 0, k)

    for lists in (children, before):
        for k, v in lists.items():
            lists[k] = _topological(v, parents, sibling_rank)
    trailing = _topological(trailing, parents, sibling_rank)

    out: list[Card] = []
    stack: list[str] = []
    pending: list[tuple[int, str]] = []  # (country's position, capital key)
    done: set[str] = set()
    waiting: dict[str, list[str]] = {}  # parent key -> cards that hang off something placed before it

    def push(keys: list[str]) -> None:
        for k in reversed(keys):
            stack.append(k)
            stack.extend(reversed(before.get(k, [])))

    def emit(key: str) -> None:
        if key in present:
            if late := [p for p in parents.get(key, ()) if p in present and p not in done]:
                waiting.setdefault(late[0], []).append(key)  # placed as soon as that parent is
                return
            out.append(present[key])
            done.add(key)
        if key.startswith("country:"):
            capital = "capital:" + key.removeprefix("country:")
            if key in present and capital in present:
                pending.append((len(out) - 1, capital))
                push(children.get(key, []))
            else:  # no capital card here: what hangs off the capital follows the country's own cards
                push(children.get(capital, []))
                push(children.get(key, []))
        else:
            push(children.get(key, []))
        push(waiting.pop(key, []))

    backbone = [f"country:{n}" for n in walk.nodes]
    while True:
        pos = len(out)
        pending.sort()
        if pending and pos - pending[0][0] >= CAPITAL_GAP[1]:
            emit(pending.pop(0)[1])
        elif stack:
            emit(stack.pop())
        elif pending and pos - pending[0][0] >= CAPITAL_GAP[0]:
            emit(pending.pop(0)[1])
        elif backbone:
            push([backbone.pop(0)])
            if not backbone:
                trailing_keys, trailing[:] = list(trailing), []
                stack[:0] = list(reversed(trailing_keys))  # after the last country's own run
        elif pending:
            emit(pending.pop(0)[1])
        else:
            break
    if missing := sorted(set(present) - {c.key for c in out}):
        raise OrderError(f"region {region.number}: no place for {missing}")
    return out, {k: a for k, a in anchors.items() if a in present}


def _parents_first(entries: list[tuple[Card, tuple[Pass, int]]], parents: Mapping[str, tuple[str, ...]],
                   waivers: list[str], anchors: dict[str, str]) -> list[tuple[Card, tuple[Pass, int]]]:
    """Move a parent that comes after its child, in the same pass (so in a later region), to just before its earliest
    child, where it no longer follows its anchor. A parent in a later pass isn't promoted; it's reported."""
    entries = list(entries)
    while True:
        pos = {c.key: i for i, (c, _) in enumerate(entries)}
        late = sorted((pos[p], p) for k in pos for p in parents.get(k, ()) if pos[p] > pos[k]
                      and entries[pos[p]][1][0] == entries[pos[k]][1][0])
        if not late:
            break
        _, parent = late[0]
        study = entries[pos[parent]][1][0]
        first = min(pos[k] for k in pos if parent in parents.get(k, ()) and entries[pos[k]][1][0] == study)
        card, _ = entries.pop(pos[parent])
        segment = entries[first][1]
        entries.insert(first, (card, segment))
        anchors.pop(card.key, None)
        waivers.append(f"{card.key} moved to region {segment[1]}, before its child {entries[first + 1][0].key}")
    pos = {c.key: i for i, (c, _) in enumerate(entries)}
    for k in pos:
        for p in parents.get(k, ()):
            if pos[p] > pos[k]:
                waivers.append(f"{k} comes before its parent {p}, which is in a later pass")
    return entries


@dataclass(frozen=True)
class _Context:
    parents: Mapping[str, tuple[str, ...]]
    anchors: Mapping[str, str]
    lookalikes: list[tuple[str, str]]  # sorted pairs within the segment
    walk_nodes: set[str]


def _violations(seg: list[Card], ctx: _Context) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    """Within one segment, by precedence: parent after child, card before its anchor, capital gap, same id side by
    side, look-alike window. Each list holds descriptions."""
    pos = {c.key: i for i, c in enumerate(seg)}
    parent = [f"{k} comes before its parent {p}" for k in pos for p in ctx.parents.get(k, ()) if p in pos and pos[p] > pos[k]]
    anchor = [f"{k} comes before {a}, which it follows" for k in pos if (a := ctx.anchors.get(k)) in pos and pos[a] > pos[k]]
    capital = []
    for c in seg:
        if c.kind == "capital" and (country := f"country:{c.id}") in pos:
            gap = pos[c.key] - pos[country]
            if not CAPITAL_GAP[0] <= gap <= CAPITAL_GAP[1]:
                capital.append(f"{c.key} is {gap} cards after {country} (wants {CAPITAL_GAP[0]}-{CAPITAL_GAP[1]})")
    same = [f"{a.key} and {b.key} share an id and sit side by side" for a, b in zip(seg, seg[1:]) if a.id == b.id]
    look = []
    for a, b in ctx.lookalikes:
        if a in pos and b in pos:
            gap = abs(pos[a] - pos[b])
            if not LOOKALIKE_GAP[0] <= gap <= LOOKALIKE_GAP[1]:
                look.append(f"look-alikes {a} and {b} are {gap} cards apart (wants {LOOKALIKE_GAP[0]}-{LOOKALIKE_GAP[1]})")
    return parent, anchor, capital, same, look


def _score(seg: list[Card], ctx: _Context) -> tuple[int, ...]:
    return tuple(len(v) for v in _violations(seg, ctx))


def _offenders(seg: list[Card], ctx: _Context) -> list[str]:
    """Keys a repair may move: those in a violation below anchor order, earliest first, then every other card, nearest
    a violation first, which may help by moving between a pair. Walk countries never move."""
    pos = {c.key: i for i, c in enumerate(seg)}
    keys: list[str] = []
    for c in seg:
        if c.kind == "capital" and (country := f"country:{c.id}") in pos:
            if not CAPITAL_GAP[0] <= pos[c.key] - pos[country] <= CAPITAL_GAP[1]:
                keys.append(c.key)
    for a, b in zip(seg, seg[1:]):
        if a.id == b.id:
            keys += [b.key, a.key]
    for pair in ctx.lookalikes:
        a, b = sorted(pair, key=lambda k: (pos.get(k, -1), k))
        if a in pos and b in pos and not LOOKALIKE_GAP[0] <= pos[b] - pos[a] <= LOOKALIKE_GAP[1]:
            keys += [b, a]
    first = sorted(set(keys) - ctx.walk_nodes, key=lambda k: (pos[k], k))
    spots = sorted({pos[k] for k in keys})
    helpers = [c.key for c in seg if c.key not in ctx.walk_nodes and c.key not in keys]
    return first + sorted(helpers, key=lambda k: (min((abs(pos[k] - s) for s in spots), default=0), pos[k]))


def _repair(seg: list[Card], ctx: _Context) -> list[Card]:
    """Move one card at a time, nearest target first, while that lowers the violation counts in precedence order."""
    score = _score(seg, ctx)
    while any(score):
        for key in _offenders(seg, ctx):
            i = next(n for n, c in enumerate(seg) if c.key == key)
            targets = sorted((t for t in range(max(0, i - REPAIR_REACH), min(len(seg), i + REPAIR_REACH + 1)) if t != i),
                             key=lambda t: (abs(t - i), t))
            better = None
            for t in targets:
                moved = seg[:i] + seg[i + 1:]
                moved.insert(t, seg[i])
                if (s := _score(moved, ctx)) < score:
                    better = moved, s
                    break
            if better:
                seg, score = better
                break
        else:
            break
    return seg


def _waivers(seg: list[Card], ctx: _Context) -> list[str]:
    return [w for group in _violations(seg, ctx) for w in group]


def report(ordering: Ordering) -> str:
    """Per region and pass of the ring order: the walk's jumps and frontier breaks, then every waiver (the ring's,
    then the study order's look-alike pairs, marked `study order:`)."""
    lines = []
    for r in ordering.reports:
        head = f"pass {r.study_pass} region {r.region.number:2d} {r.region.name}"
        if r.study_pass == 1:
            jumps = ", ".join(f"{a}→{b}" for a, b in r.jumps) or "none"
            breaks = ", ".join(r.breaks) or "none"
            lines.append(f"{head}: {'frozen' if r.walk.frozen else 'generated'} walk, {len(r.jumps)} jump(s): {jumps}; "
                         f"{len(r.breaks)} frontier break(s): {breaks}")
        elif r.waivers:
            lines.append(head)
        lines += [f"  waiver: {w}" for w in r.waivers]
    lines += [f"waiver: {w}" for w in ordering.waivers]
    return "\n".join(lines)
