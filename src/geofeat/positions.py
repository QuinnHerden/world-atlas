"""data/positions.lock: each card's new-card position, keyed by uid. See docs/adr/0006-positions-lock-and-pos-footnote.md.

`make positions` (this module's main) is the only writer. While the lock says `draft: true` it is regenerated from
the ideal order at STRIDE. Once it isn't a draft, existing entries never change: a new uid goes into the gap after
the nearest earlier card in the ideal order that is already locked, and a retired uid keeps its slot.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from geofeat.model import ROOT

LOCK_FILE = ROOT / "data/positions.lock"
STRIDE = 500
LIMIT = 1_000_000  # a margin under 2,000,000, where Anki's Check Database rewrites new-card dues (ADR 0006)
_HEADER = re.compile(r"draft: (true|false)")
_ENTRY = re.compile(r"([A-Za-z0-9]{10}): (\d+)")


class GapExhausted(ValueError):
    pass


@dataclass(frozen=True)
class Lock:
    draft: bool
    positions: dict[str, int]


def parse(text: str) -> Lock:
    lines = text.splitlines()
    if not lines or not (header := _HEADER.fullmatch(lines[0])):
        raise ValueError("positions.lock: the first line must be `draft: true` or `draft: false`")
    positions: dict[str, int] = {}
    for number, line in enumerate(lines[1:], 2):
        if not (entry := _ENTRY.fullmatch(line)):
            raise ValueError(f"positions.lock:{number}: expected `<uid>: <position>`, got {line!r}")
        uid, value = entry.group(1), int(entry.group(2))
        if uid in positions:
            raise ValueError(f"positions.lock:{number}: {uid} appears twice")
        positions[uid] = value
    _validate(positions)
    return Lock(header.group(1) == "true", positions)


def dump(lock: Lock) -> str:
    _validate(lock.positions)
    entries = "".join(f"{uid}: {lock.positions[uid]}\n" for uid in sorted(lock.positions))
    return f"draft: {str(lock.draft).lower()}\n{entries}"


def read(path: Path = LOCK_FILE) -> Lock:
    if not path.exists():
        raise SystemExit(f"{path.name} is missing (run `make positions`)")
    return parse(path.read_text())


def _validate(positions: dict[str, int]) -> None:
    if out := sorted(uid for uid, p in positions.items() if not 0 <= p < LIMIT):
        raise ValueError(f"positions out of range [0, {LIMIT:,}): {out}")
    if len(set(positions.values())) != len(positions):
        raise ValueError("two uids share a position")


def require(lock: Lock, uids: list[str]) -> None:
    """Fail on any active uid the lock doesn't hold."""
    if missing := sorted(set(uids) - set(lock.positions)):
        raise SystemExit(f"uids not in {LOCK_FILE.name} (run `make positions` and commit it): {missing}")


def regenerate(ideal: list[str]) -> dict[str, int]:
    return {uid: STRIDE * (i + 1) for i, uid in enumerate(ideal)}


def place(locked: dict[str, int], ideal: list[str]) -> dict[str, int]:
    """Add the uids in `ideal` that `locked` lacks, never moving a locked one.

    Each new uid goes after `pred`, the nearest earlier uid in `ideal` that is locked: between locked[pred] and the
    next locked value above it, or below the lowest value when it has no pred, or at max + STRIDE when
    nothing is locked above pred. New uids that share a gap are spread evenly through it, in ideal order.
    """
    groups: dict[str | None, list[str]] = {}
    pred = None
    for uid in ideal:
        if uid in locked:
            pred = uid
        else:
            groups.setdefault(pred, []).append(uid)
    values = sorted(locked.values())
    result = dict(locked)
    for pred, new in groups.items():
        low = locked[pred] if pred is not None else -1  # below every position, 0 included
        above = [v for v in values if v > low]
        if not above:  # the end of the order (or an empty lock): extend at the stride
            low = max(low, 0)
            if low + STRIDE * len(new) >= LIMIT:
                raise GapExhausted(f"no room for {len(new)} new position(s) after {low} below {LIMIT:,}: {new}")
            result |= {uid: low + STRIDE * k for k, uid in enumerate(new, 1)}
            continue
        gap = above[0] - low
        if gap <= len(new):
            raise GapExhausted(f"no room for {len(new)} new position(s) between {low} and {above[0]} (after "
                               f"{pred or 'the start'}): {new}")
        n = len(new) + 1
        result |= {uid: low + (2 * gap * k + n) // (2 * n) for k, uid in enumerate(new, 1)}
    _validate(result)
    return result


def update(lock: Lock, ideal: list[str]) -> Lock:
    return Lock(lock.draft, regenerate(ideal) if lock.draft else place(lock.positions, ideal))


def main() -> None:
    from geofeat.order import OrderError
    from geofeat.order.inputs import ordering  # imports the card sources; keep this module light for check.py

    try:
        result = ordering()
    except OrderError as exc:
        raise SystemExit(f"study order: {exc}")
    ideal = [c.uid for c in result.cards]
    old = read() if LOCK_FILE.exists() else Lock(True, {})
    if not old.draft and (generated := sorted({r.region.slug for r in result.reports if not r.walk.frozen})):
        raise SystemExit(f"{LOCK_FILE.name} is frozen (draft: false), but these regions' walks are generated, not "
                         f"frozen in curriculum.yaml (ADR 0009): {generated}")
    new = update(old, ideal)
    tmp = LOCK_FILE.with_suffix(".tmp")
    tmp.write_text(dump(new))
    tmp.replace(LOCK_FILE)
    added = len(set(new.positions) - set(old.positions))
    dropped = len(set(old.positions) - set(new.positions))
    print(f"wrote {LOCK_FILE.name}: {len(new.positions)} uids, {added} added, {dropped} dropped"
          + (" (draft: regenerated from the ideal order)" if new.draft else ""))


if __name__ == "__main__":
    main()
