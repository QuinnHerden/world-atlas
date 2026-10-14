"""data/positions.lock: each card's new-card position, and the pass and region it was placed in, keyed by uid. See
docs/adr/0006-positions-lock-and-pos-footnote.md.

`make positions` (this module's main) is the only writer. While the lock says `draft: true` it is regenerated from
the ideal order at STRIDE. Once it isn't a draft, existing entries never change: a new uid goes into the gap after
the nearest earlier card in the ideal order that is already locked, and a retired uid keeps its slot. The freeze
guard (`frozen_errors`) holds the lock to that against the last frozen lock on BASE_REF.
"""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from geofeat.card import Card, Pass
from geofeat.model import ROOT

LOCK_FILE = ROOT / "data/positions.lock"
STRIDE = 500
LIMIT = 1_000_000  # a margin under 2,000,000, where Anki's Check Database rewrites new-card dues (ADR 0006)
# The ref whose committed lock a frozen lock must extend; the env var overrides it (e.g. upstream/main in a fork).
BASE_REF = os.environ.get("POSITIONS_BASE", "origin/main")
_HEADER = re.compile(r"draft: (true|false)")
_ENTRY = re.compile(r"([A-Za-z0-9]{10}): (\d+) pass=(orientation|1|2) region=(-|\d{2})")


class GapExhausted(ValueError):
    pass


@dataclass(frozen=True)
class Entry:
    """A card's slot: its position (the new-card due) and the pass and ring region it was placed in, so the guide's
    sections and the `pass::`/`region::` tags that filtered decks search are held to the order the lock records."""

    position: int
    study_pass: Pass
    region: int | None  # None for orientation, which has no region

    def __post_init__(self) -> None:
        if (self.study_pass == "orientation") != (self.region is None):
            raise ValueError(f"pass {self.study_pass} with region {self.region}: only orientation has no region")
        if self.region is not None and not 1 <= self.region <= 99:
            raise ValueError(f"region {self.region} is not 01-99")


Placement = tuple[str, Pass, int | None]  # a card in the ideal order: uid, pass, region (None for orientation)


@dataclass(frozen=True)
class Lock:
    draft: bool
    entries: dict[str, Entry]

    @property
    def positions(self) -> dict[str, int]:
        return {uid: e.position for uid, e in self.entries.items()}


def _pass(text: str) -> Pass:
    return "orientation" if text == "orientation" else 1 if text == "1" else 2


def parse(text: str) -> Lock:
    lines = text.splitlines()
    if not lines or not (header := _HEADER.fullmatch(lines[0])):
        raise ValueError("positions.lock: the first line must be `draft: true` or `draft: false`")
    entries: dict[str, Entry] = {}
    for number, line in enumerate(lines[1:], 2):
        if not (m := _ENTRY.fullmatch(line)):
            raise ValueError(f"positions.lock:{number}: expected `<uid>: <position> pass=<pass> region=<NN or ->`, "
                             f"got {line!r}")
        uid = m.group(1)
        if uid in entries:
            raise ValueError(f"positions.lock:{number}: {uid} appears twice")
        try:
            entries[uid] = Entry(int(m.group(2)), _pass(m.group(3)), None if m.group(4) == "-" else int(m.group(4)))
        except ValueError as exc:
            raise ValueError(f"positions.lock:{number}: {exc}") from None
    lock = Lock(header.group(1) == "true", entries)
    _validate(lock.positions)
    return lock


def dump(lock: Lock) -> str:
    _validate(lock.positions)
    lines = "".join(f"{uid}: {e.position} pass={e.study_pass} region={'-' if e.region is None else f'{e.region:02d}'}\n"
                    for uid, e in sorted(lock.entries.items()))
    return f"draft: {str(lock.draft).lower()}\n{lines}"


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


def _entries(positions: dict[str, int], placed: list[Placement], keep: dict[str, Entry]) -> dict[str, Entry]:
    """Entries for `positions`: a kept entry as it is, any other uid with its pass and region from `placed`."""
    where = {uid: (study, region) for uid, study, region in placed}
    return {uid: keep[uid] if uid in keep else Entry(p, *where[uid]) for uid, p in positions.items()}


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


def stale_draft(lock: Lock, placed: list[Placement]) -> bool:
    """A draft lock that `make positions` would rewrite: the study order, or a card's pass or region, changed since
    it was written. A frozen lock keeps every card's old slot by design; `moved` and `require` apply to it."""
    return lock.draft and lock != update(lock, placed)


def moved(lock: Lock, placed: list[Placement]) -> list[str]:
    """Locked cards whose pass or region is no longer the one the lock records."""
    return [f"{uid} ({e.study_pass}, region {e.region} -> {study}, region {region})" for uid, study, region in placed
            if (e := lock.entries.get(uid)) is not None and (e.study_pass, e.region) != (study, region)]


def placements(ideal: list[Card] | None = None) -> list[Placement]:
    """The ideal order's cards (by default, every active card's), with the pass and region the order engine placed
    each in."""
    from geofeat.countries_ne import state_ids
    from geofeat.curriculum import load_curriculum
    from geofeat.order.inputs import card_region, ordering  # imports the card sources; keep this module light

    region = card_region(load_curriculum(state_ids()))
    cards = ordering().cards if ideal is None else ideal
    return [(c.uid, c.study_pass, None if c.study_pass == "orientation" else region(c)) for c in cards]


def lock_error(lock: Lock) -> str | None:
    """Why the lock doesn't fit the current study order: a stale draft, a frozen card whose pass or region changed,
    or an order that can't be built."""
    from geofeat.order import OrderError

    try:
        placed = placements()
    except OrderError as exc:
        return f"study order: {exc}"
    if stale_draft(lock, placed):
        return f"{LOCK_FILE.name} is a draft written for an older study order; run `make positions` and commit it"
    if not lock.draft and (changed := moved(lock, placed)):
        return (f"{LOCK_FILE.name} is frozen, but these cards' pass or region changed since they were locked, so the "
                f"guide and the pass::/region:: tags would no longer match their slots (retire the uid and add a new "
                f"one instead; ADR 0006): {changed}")
    return None


def update(lock: Lock, placed: list[Placement]) -> Lock:
    ideal = [uid for uid, *_ in placed]
    if lock.draft:
        return Lock(True, _entries(regenerate(ideal), placed, {}))
    return Lock(False, _entries(place(lock.positions, ideal), placed, lock.entries))


def frozen_errors(lock: Lock, base_text: str | None) -> list[str]:
    """The freeze guard: once the lock on the base ref is frozen, this lock must keep it frozen and hold every one
    of its entries unchanged (position, pass and region). It may only add uids. A draft or missing base passes."""
    if base_text is None or not (header := _HEADER.fullmatch(base_text.split("\n", 1)[0])) or header.group(1) == "true":
        return []  # a draft base may be in the old `<uid>: <position>` format, so it isn't parsed
    base = parse(base_text)
    errors = [f"{LOCK_FILE.name} is a draft again, but {BASE_REF}'s is frozen"] if lock.draft else []
    if dropped := sorted(set(base.entries) - set(lock.entries)):
        errors.append(f"{LOCK_FILE.name} drops uids frozen on {BASE_REF}: {dropped}")
    if changed := sorted(u for u, e in base.entries.items() if u in lock.entries and lock.entries[u] != e):
        errors.append(f"{LOCK_FILE.name} changes entries frozen on {BASE_REF}: {changed}")
    return errors


def base_text(ref: str = BASE_REF) -> str | None:
    """The lock committed on `ref`, or None when git, the ref or the file isn't there (e.g. a source archive)."""
    path = LOCK_FILE.relative_to(ROOT).as_posix()
    try:
        result = subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:{path}"], capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def main() -> None:
    from geofeat.order import OrderError
    from geofeat.order.inputs import ordering  # imports the card sources; keep this module light for check.py

    try:
        result = ordering()
        placed = placements(result.cards)
    except OrderError as exc:
        raise SystemExit(f"study order: {exc}")
    old = read() if LOCK_FILE.exists() else Lock(True, {})
    if not old.draft and (generated := sorted({r.region.slug for r in result.reports if not r.walk.frozen})):
        raise SystemExit(f"{LOCK_FILE.name} is frozen (draft: false), but these regions' walks are generated, not "
                         f"frozen in curriculum.yaml (ADR 0009): {generated}")
    if errors := frozen_errors(old, base_text()):
        raise SystemExit("; ".join(errors))
    if not old.draft and (changed := moved(old, placed)):
        raise SystemExit(f"{LOCK_FILE.name} is frozen, but these cards' pass or region changed since they were "
                         f"locked; retire the uid and add a new one instead (ADR 0006): {changed}")
    new = update(old, placed)
    tmp = LOCK_FILE.with_suffix(".tmp")
    tmp.write_text(dump(new))
    tmp.replace(LOCK_FILE)
    added = len(set(new.positions) - set(old.positions))
    dropped = len(set(old.positions) - set(new.positions))
    print(f"wrote {LOCK_FILE.name}: {len(new.positions)} uids, {added} added, {dropped} dropped"
          + (" (draft: regenerated from the ideal order)" if new.draft else ""))


if __name__ == "__main__":
    main()
