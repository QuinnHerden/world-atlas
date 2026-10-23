"""data/positions.lock: each card's new-card position, and the block and region it was placed in, keyed by uid. See
docs/adr/0006-positions-lock-and-pos-footnote.md and docs/adr/0011-refreezing-at-a-major-version.md.

`make positions` (this module's main) is the only writer. While the lock says `draft: true` it is regenerated from
the ideal order at STRIDE. Once it isn't a draft, existing entries never change: a new uid goes into the gap after
the nearest earlier card in the ideal order that is already locked, and a retired uid keeps its slot. The lock
declares the major version series it belongs to (`series: N`). The freeze guard (`guard`) holds it to the frozen lock
of the same series on origin/main and on the newest release tag of that series; a lock of a new series is a fresh
freeze, allowed only as the next major version. Versioning restarted at v1.0.0: the earlier releases are archived as
`archive/vX.Y.Z` tags, pre-1.0 history whose uids every lock keeps, and series 1 continues the archived series 3 order, but for the oceans' move (RESTART_MOVES).
"""

import os
import re
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

from geofeat.card import BLOCKS, Block, Card
from geofeat.decks import BY_NAME, BY_SLUG, COMPANION_BLOCKS, DECKS, WORLD, DeckInfo
from geofeat.model import ROOT

LOCK_FILE = ROOT / "data/positions.lock"
STRIDE = 500
LIMIT = 1_000_000  # a margin under 2,000,000, where Anki's Check Database rewrites new-card dues (ADR 0006)
if any(d.limit > LIMIT for d in DECKS):
    raise ValueError(f"a deck's position range passes {LIMIT:,}")
DEFAULT_BASE = "origin/main"  # the ref whose committed lock a frozen lock must extend; POSITIONS_BASE overrides it
LEGACY_SERIES = 2  # a frozen lock with no `series:` line is v2's, the only one written before series existed
FIRST_SERIES = 1  # versioning restarted at v1.0.0: the first release under the vX.Y.Z tags is series 1's
RESTARTED_FROM = 3  # the archived series whose frozen order series 1 continues, entry for entry but RESTART_MOVES
ARCHIVE_PREFIX = "archive/"  # archive/vX.Y.Z: a pre-1.0 release, archived when versioning restarted
# The one reorder series 1 makes to the archived series-3 order, before its first release: the four oceans (Atlantic,
# Indian, Pacific, Arctic) move from the head of the features block to just after the seven continents, new-card
# positions 8-11. Re-importing never changes a card's due, so only fresh imports see it (ADR 0011's amendment).
RESTART_MOVES: dict[str, int] = {"N3NGMxsbci": 3600, "KPgnUeNLWJ": 3700, "9dKZ99t54a": 3800, "wSxtLBdr0g": 3900}
_HEADER = re.compile(r"draft: (true|false)")
_SERIES = re.compile(r"series: ([1-9][0-9]*)", re.ASCII)
_LEGACY_ENTRY = re.compile(r"[A-Za-z0-9]{10}: [0-9]+ pass=(orientation|1|2) region=(-|[0-9]{2})", re.ASCII)  # series 2's format
# `deck=` names the entry's deck by slug (geofeat.decks); a line without it (series 3 before the companion decks) is
# World Atlas's
_ENTRY = re.compile(r"([A-Za-z0-9]{10}): ([0-9]+) block=(" + "|".join(BLOCKS) + r") region=(-|[0-9]{2})"
                    r"(?: deck=(" + "|".join(BY_SLUG) + r"))?", re.ASCII)


class GapExhausted(ValueError):
    pass


@dataclass(frozen=True)
class Entry:
    """A card's slot: its position (the new-card due) and the block and ring region it was placed in, so the
    `block::`/`region::` tags that filtered decks search are held to the order the lock records."""

    position: int
    block: Block
    region: int | None  # None for a continent, an orientation feature (an ocean, a planetary wind band) or a companion card
    deck: str = WORLD.slug  # the deck's slug; frozen like the position, since re-importing never moves a card's deck

    def __post_init__(self) -> None:
        if (self.block == "continents" or self.block in COMPANION_BLOCKS) and self.region is not None or \
                self.block in ("countries", "cities") and self.region is None:
            raise ValueError(f"block {self.block} with region {self.region}: continents and companion cards have no "
                             f"region, political cards and cities one")
        if self.region is not None and not 1 <= self.region <= 99:
            raise ValueError(f"region {self.region} is not 01-99")
        if (deck := BY_SLUG.get(self.deck)) is None:
            raise ValueError(f"unknown deck {self.deck!r}")
        if self.block != deck.block and (deck.block is not None or self.block in COMPANION_BLOCKS):
            raise ValueError(f"block {self.block} in deck {self.deck}: a companion deck holds its own block, and only it")
        if not deck.base <= self.position < deck.limit:
            raise ValueError(f"position {self.position} is outside {deck.slug}'s range [{deck.base:,}, {deck.limit:,})")


Placement = tuple[str, Block, int | None, str]  # a card in the ideal order: uid, block, region (None: none), deck slug


@dataclass(frozen=True)
class Lock:
    draft: bool
    entries: dict[str, Entry]
    series: int = LEGACY_SERIES  # the major version series whose frozen order this is

    @property
    def positions(self) -> dict[str, int]:
        return {uid: e.position for uid, e in self.entries.items()}


def header(text: str) -> tuple[bool, int]:
    """A lock's (draft, series) from its first lines; a lock without a `series:` line is LEGACY_SERIES."""
    lines = text.splitlines()
    if not lines or not (head := _HEADER.fullmatch(lines[0])):
        raise ValueError("positions.lock: the first line must be `draft: true` or `draft: false`")
    series = _SERIES.fullmatch(lines[1]) if len(lines) > 1 else None
    return head.group(1) == "true", int(series.group(1)) if series else LEGACY_SERIES


def parse(text: str) -> Lock:
    draft, series = header(text)
    lines = text.splitlines()
    if len(lines) < 2 or not _SERIES.fullmatch(lines[1]):
        raise ValueError("positions.lock: the second line must be `series: <major version>`")
    entries: dict[str, Entry] = {}
    for number, line in enumerate(lines[2:], 3):
        if not (m := _ENTRY.fullmatch(line)):
            raise ValueError(f"positions.lock:{number}: expected `<uid>: <position> block=<block> region=<NN or -> "
                             f"deck=<deck>`, got {line!r}")
        uid = m.group(1)
        if uid in entries:
            raise ValueError(f"positions.lock:{number}: {uid} appears twice")
        try:
            entries[uid] = Entry(int(m.group(2)), m.group(3), None if m.group(4) == "-" else int(m.group(4)),
                                 m.group(5) or WORLD.slug)
        except ValueError as exc:
            raise ValueError(f"positions.lock:{number}: {exc}") from None
    lock = Lock(draft, entries, series)
    _validate(lock.positions)
    return lock


def dump(lock: Lock) -> str:
    _validate(lock.positions)
    lines = "".join(f"{uid}: {e.position} block={e.block} region={'-' if e.region is None else f'{e.region:02d}'} "
                    f"deck={e.deck}\n" for uid, e in sorted(lock.entries.items()))
    return f"draft: {str(lock.draft).lower()}\nseries: {lock.series}\n{lines}"


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


def regenerate(ideal: list[str], deck: DeckInfo = WORLD) -> dict[str, int]:
    if deck.base + STRIDE * len(ideal) >= deck.limit:
        raise GapExhausted(f"{len(ideal)} cards don't fit {deck.slug}'s range at stride {STRIDE}")
    return {uid: deck.base + STRIDE * (i + 1) for i, uid in enumerate(ideal)}


def _entries(positions: dict[str, int], placed: list[Placement], keep: dict[str, Entry]) -> dict[str, Entry]:
    """Entries for `positions`: a kept entry as it is, any other uid with its block, region and deck from `placed`."""
    where = {uid: (block, region, deck) for uid, block, region, deck in placed}
    return {uid: keep[uid] if uid in keep else Entry(p, *where[uid]) for uid, p in positions.items()}


def place(locked: dict[str, int], ideal: list[str], deck: DeckInfo = WORLD) -> dict[str, int]:
    """Add the uids in `ideal` that `locked` lacks, never moving a locked one; `locked` and `ideal` are one deck's,
    and every position stays in its range.

    Each new uid goes after `pred`, the nearest earlier uid in `ideal` that is locked: between locked[pred] and the
    next locked value above it, or below the lowest value (and at or above the deck's base) when it has no pred, or at
    max + STRIDE when nothing is locked above pred (from the deck's base when nothing is locked at all). New uids that
    share a gap are spread evenly through it, in ideal order.
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
        low = locked[pred] if pred is not None else deck.base - 1  # below every position, the base included
        above = [v for v in values if v > low]
        if not above:  # the end of the order (or an empty deck): extend at the stride
            low = max(low, deck.base)
            if low + STRIDE * len(new) >= deck.limit:
                raise GapExhausted(f"no room for {len(new)} new position(s) after {low} below {deck.limit:,}: {new}")
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
    """A draft lock that `make positions` would rewrite: the study order, or a card's block or region, changed since
    it was written. A frozen lock keeps every card's old slot by design; `moved` and `require` apply to it."""
    return lock.draft and lock != update(lock, placed)


def moved(lock: Lock, placed: list[Placement]) -> list[str]:
    """Locked cards whose block or region the order engine would now give differently. A frozen card keeps the lock's:
    its slot and its `block::`/`region::` tags (`locked_tags`)."""
    return [f"{uid} (locked: block {e.block}, region {e.region}; now: block {block}, region {region})"
            for uid, block, region, _ in placed
            if (e := lock.entries.get(uid)) is not None and (e.block, e.region) != (block, region)]


def deck_errors(lock: Lock, placed: list[Placement]) -> list[str]:
    """Locked cards now in another deck. Unlike a block or region, a deck can't be kept from the lock: the card is in
    its package, and re-importing never moves a card to another deck, so a changed deck fails."""
    return [f"{uid} is locked in deck {e.deck} but is now in {deck}" for uid, _, _, deck in placed
            if (e := lock.entries.get(uid)) is not None and e.deck != deck]


def locked_tags(tags: list[str], entry: Entry | None) -> list[str]:
    """A card's tags with `block::` and any `region::` tag taken from its lock entry, so a filtered deck finds the card
    where its slot is. A card without an entry, or without a region tag (a feature), is left as it is."""
    if entry is None:
        return list(tags)
    out = []
    for tag in tags:
        if tag.startswith("block::"):
            out.append(f"block::{entry.block}")
        elif tag.startswith("region::"):
            if entry.region is not None:
                out.append(f"region::{entry.region:02d}")
        else:
            out.append(tag)
    return out


def placements(ideal: list[Card] | None = None) -> list[Placement]:
    """The ideal order's cards (by default, every deck's active cards), with the block and the region the order engine
    placed each in (none for a continent, an orientation feature or a companion deck's card), and the deck."""
    from geofeat.countries_ne import state_ids
    from geofeat.curriculum import load_curriculum
    from geofeat.order.inputs import card_region, deck_order  # imports the card sources; keep this module light

    region = card_region(load_curriculum(state_ids()))
    cards = deck_order() if ideal is None else ideal
    return [(c.uid, c.block, None if c.study_pass == "orientation" or c.block in COMPANION_BLOCKS else region(c),
             BY_NAME[c.deck].slug) for c in cards]


def lock_error(lock: Lock) -> str | None:
    """Why the lock doesn't fit the current study order: a stale draft, or an order that can't be built. A frozen
    card whose block or region changed only gets a warning: it keeps the lock's."""
    from geofeat.order import OrderError

    try:
        placed = placements()
    except OrderError as exc:
        return f"study order: {exc}"
    if stale_draft(lock, placed):
        return f"{LOCK_FILE.name} is a draft written for an older study order; run `make positions` and commit it"
    if errors := deck_errors(lock, placed):
        return "; ".join(errors)
    if not lock.draft:
        warn_moved(lock, placed)
    return None


def warn_moved(lock: Lock, placed: list[Placement]) -> None:
    for line in moved(lock, placed):
        print(f"warning: frozen card keeps its locked block and region (slot, tags): {line}")


def update(lock: Lock, placed: list[Placement]) -> Lock:
    """Each deck's positions within its range: regenerated for a draft, else the new uids placed among the locked."""
    positions: dict[str, int] = {}
    for deck in DECKS:
        ideal = [uid for uid, *_, slug in placed if slug == deck.slug]
        if lock.draft:
            positions |= regenerate(ideal, deck)
        else:
            mine = {u: e.position for u, e in lock.entries.items() if e.deck == deck.slug}
            positions |= place(mine, ideal, deck)
    return Lock(lock.draft, _entries(positions, placed, {} if lock.draft else lock.entries), lock.series)


def frozen_errors(lock: Lock, base_text: str | None, ref: str = DEFAULT_BASE, pre_release: bool = False
                  ) -> list[str]:
    """The freeze guard against one base lock: once the lock on `ref` is frozen, a lock of the same series must keep
    it frozen and hold every one of its entries unchanged (position, block and region). It may only add uids. A lock
    of a later series is a fresh freeze and isn't compared (`series_errors` decides whether it may exist); an earlier
    series is an error. A draft or missing base passes. `pre_release`: `ref` holds pre-1.0 history, so a series-1 lock
    is held to its series-RESTARTED_FROM lock as if they were one series, and a RESTART_MOVES card may be at its new
    position."""
    if base_text is None:
        return []
    try:
        draft, series = header(base_text)
    except ValueError:
        return [f"{ref}'s {LOCK_FILE.name} has no `draft: true|false` header"]
    if draft:
        return []  # a draft base may be in an older format, so it isn't parsed
    continued = pre_release and (series, lock.series) == (RESTARTED_FROM, FIRST_SERIES)
    if series > lock.series and not continued:
        return [f"{LOCK_FILE.name} is series {lock.series}, but {ref}'s is series {series}: a series never goes back"]
    if series < lock.series:  # an older series: not compared, but it must be a well-formed lock of its own format
        lines = base_text.splitlines()
        body = lines[2:] if len(lines) > 1 and _SERIES.fullmatch(lines[1]) else lines[1:]
        entry = _LEGACY_ENTRY if series == LEGACY_SERIES else _ENTRY
        if not body or not all(entry.fullmatch(line) for line in body):
            return [f"{ref}'s {LOCK_FILE.name} is not a well-formed series {series} lock"]
        return []
    try:
        base = parse(base_text)
    except ValueError as exc:
        return [f"{ref}'s {LOCK_FILE.name}: {exc}"]
    errors = [f"{LOCK_FILE.name} is a draft again, but {ref}'s is frozen"] if lock.draft else []
    if dropped := sorted(set(base.entries) - set(lock.entries)):
        errors.append(f"{LOCK_FILE.name} drops uids frozen on {ref}: {dropped}")
    excused = RESTART_MOVES if pre_release else {}
    if changed := sorted(u for u, e in base.entries.items() if u in lock.entries and lock.entries[u] != e
                         and (u not in excused or lock.entries[u] != replace(e, position=excused[u]))):
        errors.append(f"{LOCK_FILE.name} changes entries frozen on {ref}: {changed}")
    return errors


_RELEASE = re.compile(r"v([0-9]+)\.([0-9]+)\.([0-9]+)", re.ASCII)


def version(tag: str) -> tuple[int, int, int] | None:
    """A release tag's (major, minor, patch); None for anything not exactly vX.Y.Z (v3.0.0-rc1, vtest)."""
    m = _RELEASE.fullmatch(tag)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def dropped_released(lock: Lock, text: str | None, tag: str) -> list[str]:
    """A fresh freeze may reorder, but must keep every uid of the release before it: users hold those notes. (A uid
    only ever on a branch or main, never released, may go.) A draft is checked once it is frozen."""
    if text is None or lock.draft:
        return []
    lines = text.splitlines()
    body = lines[2:] if len(lines) > 1 and _SERIES.fullmatch(lines[1]) else lines[1:]
    if dropped := sorted({line.split(":", 1)[0] for line in body if line} - set(lock.entries)):
        return [f"{LOCK_FILE.name} drops uids released in {tag}: {dropped}"]
    return []


def major(tag: str) -> int | None:
    return v[0] if (v := version(tag)) else None


def newest(tags: list[str], series: int | None = None) -> str | None:
    """The highest vX.Y.Z tag among `tags` (of one major `series`, if given), by version, not by commit distance."""
    found = [t for t in tags if (v := version(t)) and (series is None or v[0] == series)]
    return max(found, key=version, default=None)


def newest_first(tags: list[str]) -> str | None:
    """The lowest vX.Y.Z tag among `tags`, by version: the first release."""
    return min((t for t in tags if version(t)), key=version, default=None)


def series_errors(lock: Lock, last: str | None, release: str | None) -> list[str]:
    """A lock's series against the release tags. `last` is the newest release reachable from HEAD; `release` the
    version this build is for (a release build's RELEASE_VERSION, or a release tag on HEAD). The series may stay at the
    newest release's major or start the next one, a fresh freeze; only a major version may start it, so a release
    must be of the lock's series."""
    errors = []
    if last is not None and (prior := major(last)) is not None:
        if lock.series < prior:
            errors.append(f"{LOCK_FILE.name} is series {lock.series}, older than release {last}")
        elif lock.series > prior + 1:
            errors.append(f"{LOCK_FILE.name} is series {lock.series}, but a new series must be the next major "
                          f"version after {last} (series {prior + 1})")
    if release is not None and major(release) != lock.series:
        errors.append(f"this build is for {release}, but {LOCK_FILE.name} is series {lock.series}: a release must be "
                      f"of its lock's series, and only a major version starts a series")
    return errors


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def base_ref() -> str:
    return os.environ.get("POSITIONS_BASE") or DEFAULT_BASE


def base_text(ref: str) -> str | None:
    """The lock committed on `ref`, or None when git, the ref or the file isn't there (e.g. a source archive)."""
    if ref.startswith("-"):  # never let the ref read as a git option
        return None
    return _git("show", "--end-of-options", f"{ref}:{LOCK_FILE.relative_to(ROOT).as_posix()}")


def release_tags() -> list[str] | None:
    """Every vX.Y.Z tag merged into HEAD, or None when git can't list them."""
    out = _git("tag", "--merged", "HEAD", "--list", "v*")
    return None if out is None else [t for t in out.split() if version(t)]


def archive_tags() -> list[str] | None:
    """Every archive/vX.Y.Z tag merged into HEAD: the pre-1.0 releases. None when git can't list them."""
    out = _git("tag", "--merged", "HEAD", "--list", f"{ARCHIVE_PREFIX}v*")
    return None if out is None else [t for t in out.split() if version(t.removeprefix(ARCHIVE_PREFIX))]


def head_tags() -> list[str]:
    """The release tags on HEAD itself."""
    out = _git("tag", "--points-at", "HEAD", "--list", "v*")
    return [t for t in (out or "").split() if version(t)]


def shallow() -> bool:
    return (_git("rev-parse", "--is-shallow-repository") or "").strip() == "true"


def guard(lock: Lock, strict: bool, release: str | None = None, require_release: bool = False
          ) -> tuple[list[str], list[str]]:
    """The freeze guard: (errors, warnings). The lock is held to the base ref's and to that of the newest release of
    its own series, and its series to the release tags (`series_errors`). `strict` (a release build, or `make
    positions`) makes an unreadable base ref, a shallow clone or unreadable tags an error for a frozen lock, not a
    warning. `release`, a release build's version (RELEASE_VERSION=vX.Y.Z), and every release tag on HEAD must be of the
    lock's series; `require_release` (a release build) fails without one. Every lock keeps the uids of every archived
    pre-1.0 release, and a series-1 lock extends the newest archived series-RESTARTED_FROM lock; until the first
    release, the base ref may still hold that lock."""
    ref = base_ref()
    text = base_text(ref)
    tags = release_tags()
    archived = archive_tags()
    continued = newest([t.removeprefix(ARCHIVE_PREFIX) for t in archived or []], RESTARTED_FROM)
    restarting = continued is not None and tags == []  # the restart is visible and nothing is released since
    errors, warnings = frozen_errors(lock, text, ref, pre_release=restarting), []
    if restarting and lock.series != FIRST_SERIES:
        errors.append(f"{LOCK_FILE.name} is series {lock.series}: until v{FIRST_SERIES}.0.0 is tagged it must be series "
                      f"{FIRST_SERIES}")
    problems = []
    if text is None:
        problems.append(f"can't read {LOCK_FILE.name} on {ref} to check the frozen lock against it (fetch it, e.g. "
                        f"`git fetch origin main` or a full-depth CI checkout, or set POSITIONS_BASE)")
    if tags is None or shallow():
        problems.append("can't see every release tag (a shallow clone, or no git): fetch the full history and tags")
    if continued is None and (lock.series == FIRST_SERIES or tags == []):  # without them, no rule bounds the series
        problems.append(f"can't see the archived pre-1.0 releases ({ARCHIVE_PREFIX}v{RESTARTED_FROM}.*): fetch the tags")
    if not lock.draft:
        (errors if strict else warnings).extend(problems)
    tags = tags or []
    last = newest(tags)
    releases = ([release] if release else []) + head_tags()
    if release is not None and version(release) is None:
        errors.append(f"RELEASE_VERSION={release!r} is not vX.Y.Z")
    elif require_release and not releases:
        errors.append("a release build needs its version: set RELEASE_VERSION=vX.Y.Z (or tag HEAD)")
    elif continued is not None and (first := newest_first(tags + releases)) and major(first) != FIRST_SERIES:
        errors.append(f"the first release is v{FIRST_SERIES}.x (versioning restarted at v1.0.0), not {first}")
    if require_release and lock.draft:
        errors.append(f"a release must ship a frozen {LOCK_FILE.name} (draft: false)")
    errors += series_errors(lock, last, None)
    for tag in releases:
        errors += series_errors(lock, None, tag)
    if last is not None and major(last) is not None and lock.series > major(last) and not releases:
        warnings.append(f"{LOCK_FILE.name} is series {lock.series}, not yet released: the next release must be "
                        f"v{lock.series}.0.0")
    if last is not None and (prior := major(last)) is not None and prior < lock.series:
        errors += dropped_released(lock, base_text(last), last)
    for tag in archived or []:
        errors += dropped_released(lock, base_text(tag), tag)
    if lock.series == FIRST_SERIES and continued is not None:
        tag = ARCHIVE_PREFIX + continued
        if (archived_text := base_text(tag)) != text:  # before the first release, main may hold the same lock
            errors += frozen_errors(lock, archived_text, tag, pre_release=True)
    if (tag := newest(tags, lock.series)) is not None and tag != ref:
        errors += frozen_errors(lock, base_text(tag), tag)
    return errors, warnings


def main() -> None:
    from geofeat.order import OrderError
    from geofeat.order.inputs import deck_order, ordering  # imports the card sources; keep this module light

    try:
        result = ordering()
        placed = placements(deck_order(result))
    except OrderError as exc:
        raise SystemExit(f"study order: {exc}")
    old = read() if LOCK_FILE.exists() else Lock(True, {}, FIRST_SERIES)
    if not old.draft and (generated := sorted({r.region.slug for r in result.reports if not r.walk.frozen})):
        raise SystemExit(f"{LOCK_FILE.name} is frozen (draft: false), but these regions' walks are generated, not "
                         f"frozen in curriculum.yaml (ADR 0009): {generated}")
    if errors := guard(old, strict=True)[0] + deck_errors(old, placed):
        raise SystemExit("; ".join(errors))
    if not old.draft:
        warn_moved(old, placed)
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
