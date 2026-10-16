"""Headless import test: import dist/world-atlas.apkg with the official Anki library, as the desktop app would with its
default options, and check what a learner gets.

usage: make import-test    (or: uv run --with anki==26.09.3 python tools/import_test.py [--v1 PATH])

Fresh import: every note lands in the World Atlas deck, new cards come up in data/positions.lock order, a region
filtered deck (`tag:region::05 is:new`, "Order due") gives that region's cards in lock order, and Check Database
changes no due.

Companion decks: each companion package imported after World Atlas lands in its own deck at its lock positions, shares
World Atlas's note type without adding or renaming one, and leaves the World Atlas cards untouched.

Upgrade from v1: the Geographic Features package of commit V1_COMMIT is imported first and a few cards are studied.
Importing World Atlas then updates the feature notes in place (same note ids), keeps their scheduling and leaves them
in their old decks, and Change Deck moves them into World Atlas with their scheduling intact. The v1 package is built
from `git archive V1_COMMIT` with placeholder maps (the maps don't matter to the import) and cached in
build/import-test/. It uses today's ankc, so the test checks that its guids and note type match the shipped v1's
(tests/fixtures); `--v1` uses a real v1 package instead. The first build needs the network for v1's environment. The
cache is keyed by ankc's version only: delete build/import-test/ after changing a local ankc at the same version.
"""

import argparse
import html
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from collections.abc import Iterable
from pathlib import Path

from anki.buildinfo import version as anki_version
from anki.collection import Collection, ImportAnkiPackageOptions, ImportAnkiPackageRequest
from anki.decks_pb2 import Deck
from anki.import_export_pb2 import ImportAnkiPackageUpdateCondition
from anki.scheduler_pb2 import QueuedCards

import geofeat.positions as positions
from geofeat.ankc import ankc_command, ankc_version_text
from geofeat.deckgen import NOTE_STYLE
from geofeat.decks import COMPANIONS, WORLD, DeckInfo
from geofeat.model import BUILD, ROOT, ROOT_DECK
from geofeat.sources import all_cards

V1_COMMIT = "b63bf0e0a4c304e3105fe83c8616f7e725ad76d7"  # v1: the 166-card Geographic Features deck
V1_DECK = "Geographic Features"
WORK = BUILD / "import-test"
FIXTURES = ROOT / "tests/fixtures"
REGION = "05"
FIRST = 40  # new cards compared with the lock through the scheduler's own queue
STUDIED = (3, 3, 4)  # the answers given to v1 cards before the upgrade: Good, Good, Easy
SCHEDULING = "c.did, c.type, c.queue, c.due, c.ivl, c.factor, c.reps, c.lapses, c.left, c.odue, c.odid"

failures: list[str] = []


def check(ok: bool, what: str, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'} {what}" + (f": {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(what)


def package(deck: DeckInfo = WORLD) -> Path:
    path = ROOT / "dist" / f"{deck.slug}.apkg"
    if not path.exists():
        sys.exit(f"no {path.relative_to(ROOT)}; run `make all`")
    return path


def build_v1() -> Path:
    """The v1 package from `git archive V1_COMMIT`, its deck generator and ankc, with a 1x1 placeholder per map."""
    out = WORK / f"geographic-features-{V1_COMMIT[:7]}-ankc-{ankc_version_text()}.apkg"
    if out.exists():
        return out
    WORK.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=WORK) as tmp:
        src = Path(tmp)
        archive = subprocess.run(["git", "-C", str(ROOT), "archive", f"{V1_COMMIT}^{{commit}}"], check=True,
                                 capture_output=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(src, filter="data")
        env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}  # v1's own environment, not this one's
        (src / "dist").mkdir()
        placeholders = (
            "import json\n"
            "from PIL import Image\n"
            "from geofeat.model import DECK, MEDIA_INDEX, active, load_features\n"
            "DECK.mkdir(); MEDIA_INDEX.parent.mkdir()\n"
            "media = {f.id: f'{f.id}.png' for f in active(load_features())}\n"
            "for name in media.values(): Image.new('RGB', (1, 1)).save(DECK / name)\n"
            "MEDIA_INDEX.write_text(json.dumps(media))\n"
        )
        for command in (["uv", "run", "--quiet", "--locked", "python", "-c", placeholders],
                        ["uv", "run", "--quiet", "--locked", "python", "-m", "geofeat.deckgen"]):
            subprocess.run(command, cwd=src, env=env, check=True, stdout=subprocess.DEVNULL)
        # from the repo root, like the Makefile, so a relative $ANKC (`uv run --with ../ankcompiler ankc`) resolves
        subprocess.run([*ankc_command(), "build", "--deck", V1_DECK, "--path", str(src / "deck"), "--output",
                        str(src / "dist")], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        built = list((src / "dist").glob("*.apkg"))
        if len(built) != 1:
            sys.exit(f"v1 build made {len(built)} packages")
        committed = subprocess.run(["git", "-C", str(ROOT), "show", "-s", "--format=%ct", f"{V1_COMMIT}^{{commit}}"],
                                   check=True, capture_output=True, text=True).stdout
        backdate(built[0], out, int(committed))
    return out


def backdate(package: Path, out: Path, when: int) -> None:
    """Write `package` to `out` with every note, card and note type modified at `when`: built today, v1 would look newer than
    World Atlas, and the default "Update notes: If newer" would skip the update a real v1 user gets."""
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(package) as source:
            source.extractall(tmp)
            names = source.namelist()
        db = sqlite3.connect(Path(tmp) / "collection.anki2")
        db.execute("update notes set mod = ?", (when,))
        db.execute("update cards set mod = ?", (when,))
        models = json.loads(db.execute("select models from col").fetchone()[0])
        db.execute("update col set models = ?", (json.dumps({k: m | {"mod": when} for k, m in models.items()}),))
        db.commit()
        db.close()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
            for name in names:
                target.write(Path(tmp) / name, name)


def default_options() -> ImportAnkiPackageOptions:
    """The desktop import dialog's defaults: update notes and note types if newer, no scheduling, no deck options."""
    if_newer = ImportAnkiPackageUpdateCondition.IMPORT_ANKI_PACKAGE_UPDATE_CONDITION_IF_NEWER
    return ImportAnkiPackageOptions(merge_notetypes=False, update_notes=if_newer, update_notetypes=if_newer,
                                    with_scheduling=False, with_deck_configs=False)


def import_package(col: Collection, path: Path) -> None:
    log = col.import_anki_package(ImportAnkiPackageRequest(package_path=str(path), options=default_options())).log
    print(f"  imported {path.name}: {len(log.new)} new, {len(log.updated)} updated, {len(log.duplicate)} unchanged, "
          f"{len(log.conflicting)} conflicting, {len(log.missing_notetype)} missing note type")


def unlimited(col: Collection, deck: str) -> int:
    """The deck's id, with its new-card and review limits lifted so the queue shows every card."""
    did = col.decks.id_for_name(deck)
    conf = col.decks.config_dict_for_deck_id(did)
    conf["new"]["perDay"] = conf["rev"]["perDay"] = 9999
    col.decks.update_config(conf)
    return did


def new_queue(col: Collection, did: int, limit: int) -> list[str]:
    """Guids of the new cards the scheduler would show next in this deck, in order."""
    col.decks.select(did)
    queued = col.sched.get_queued_cards(fetch_limit=limit).cards
    return [col.db.scalar("select guid from notes where id = ?", q.card.note_id) for q in queued
            if q.queue == QueuedCards.NEW]


def scheduling(col: Collection, guids: Iterable[str] | None = None) -> dict[str, tuple]:
    """guid -> (note id, card id, scheduling columns) for every card, or those of `guids`."""
    rows = col.db.all(f"select n.guid, n.id, c.id, {SCHEDULING} from cards c join notes n on n.id = c.nid")
    wanted = None if guids is None else set(guids)
    return {g: tuple(rest) for g, *rest in rows if wanted is None or g in wanted}


def deck_names(col: Collection, guids: Iterable[str]) -> set[str]:
    wanted = set(guids)
    return {col.decks.name(did) for g, did in col.db.all("select n.guid, c.did from cards c join notes n on n.id = c.nid")
            if g in wanted}


def answer(col: Collection, guid: str) -> str:
    """The first line of a card's answer, before any <br> or the note's <hr>: its name."""
    note = col.get_note(col.db.scalar("select id from notes where guid = ?", guid))
    return html.unescape(re.sub(r"<[^>]+>", "", re.split(r"<br>|<hr>", note["Answer"])[0]))


def fresh_import(apkg: Path, lock: dict[str, int], tmp: Path) -> None:
    print(f"fresh import of {apkg.name}")
    col = Collection(str(tmp / "fresh.anki2"))
    try:
        import_package(col, apkg)
        cards = scheduling(col)
        check(len(cards) == len(lock) and set(cards) == set(lock), f"{len(lock)} notes, one per lock entry",
              f"{len(cards)} notes; {len(set(lock) - set(cards))} lock uids missing, {len(set(cards) - set(lock))} extra")
        check(deck_names(col, cards) == {ROOT_DECK}, f'every card in "{ROOT_DECK}"', str(deck_names(col, cards)))
        backs = [col.get_note(row[0])["Answer"] for row in cards.values()]
        check(all(NOTE_STYLE in back for back in backs), "every back carries its note under the answer",
              f"{sum(NOTE_STYLE in b for b in backs)} of {len(backs)}")
        check(any("<em>" in b for b in backs) and not any("*" in b for b in backs),
              "a note's *emphasis* reaches the back as <em>, with no stray asterisks")
        wrong = sorted(g for g, row in cards.items() if row[5] != lock.get(g))  # row[5]: due
        check(not wrong, "every new card's due equals its lock position", f"{len(wrong)} differ, e.g. {wrong[:5]}")
        order = sorted(lock, key=lock.__getitem__)
        did = unlimited(col, ROOT_DECK)
        queue = new_queue(col, did, FIRST)
        check(queue == order[:FIRST], f"the first {FIRST} new cards come up in lock order",
              f"first mismatch at {next((i for i, (a, b) in enumerate(zip(queue, order)) if a != b), len(queue))}")

        before = scheduling(col)
        problems, ok = col.fix_integrity()
        after = scheduling(col)
        changed = sorted(g for g in before if before[g] != after.get(g))
        check(ok and not changed, "Check Database changes no card", f"ok={ok}, {len(changed)} changed: {changed[:5]}; "
              f"{problems}")

        tag = f"region::{REGION}"
        region = [g for g in order if tag in col.get_note(col.db.scalar("select id from notes where guid = ?", g)).tags]
        print(f"  first 16 new cards: {', '.join(answer(col, g) for g in order[:16])}")
        print(f"  region {REGION} filtered deck: {', '.join(answer(col, g) for g in region)}")
        print(f"  positions {lock[order[0]]} to {lock[order[-1]]}")
        filtered = col.sched.get_or_create_filtered_deck(deck_id=0)
        filtered.name = f"Region {REGION}"
        del filtered.config.search_terms[:]
        filtered.config.search_terms.append(Deck.Filtered.SearchTerm(
            search=f'deck:"{ROOT_DECK}" tag:{tag} is:new', limit=9999, order=Deck.Filtered.SearchTerm.Order.DUE))
        fid = col.sched.add_or_update_filtered_deck(filtered).id
        got = new_queue(col, fid, len(region) + 10)
        check(bool(region) and got == region, f"a `tag:{tag} is:new` filtered deck, Order due, gives region {REGION}'s "
              f"{len(region)} cards in lock order", f"got {len(got)}; first mismatch at "
              f"{next((i for i, (a, b) in enumerate(zip(got, region)) if a != b), min(len(got), len(region)))}")
        col.sched.empty_filtered_deck(fid)
        back = scheduling(col)
        check(all(back[g] == before[g] for g in region), "emptying the filtered deck restores every due")
    finally:
        col.close()


def companion_imports(world: Path, lock: dict[str, int], tmp: Path) -> None:
    """World Atlas, then each companion deck into the same collection: each package's notes land in its own deck at
    their lock positions, they share World Atlas's note type (one note type, nothing re-mapped or duplicated), and the
    World Atlas cards are untouched."""
    print("companion decks imported after World Atlas")
    col = Collection(str(tmp / "companions.anki2"))
    try:
        import_package(col, world)
        before, notetypes = scheduling(col), col.models.all_names_and_ids()
        for deck in COMPANIONS:
            apkg = package(deck)
            import_package(col, apkg)
            mine = {c.uid for c in all_cards() if c.deck == deck.name}
            cards = scheduling(col, mine)
            check(set(cards) == mine, f"{apkg.name}: one note per {deck.name} card", f"{len(cards)} of {len(mine)}")
            check(deck_names(col, mine) == {deck.name}, f'{apkg.name}: every card in "{deck.name}"', str(deck_names(col, mine)))
            wrong = sorted(g for g, row in cards.items() if row[5] != lock.get(g))
            check(not wrong, f"{apkg.name}: every due equals its lock position", f"{len(wrong)} differ")
        check([(n.id, n.name) for n in col.models.all_names_and_ids()] == [(n.id, n.name) for n in notetypes],
              "the companion decks share World Atlas's note type; no note type is added or renamed")
        check(scheduling(col, before) == before, "World Atlas's notes and cards are untouched")
    finally:
        col.close()


def upgrade(v1: Path, apkg: Path, lock: dict[str, int], tmp: Path) -> None:
    print(f"upgrade: {v1.name}, study {len(STUDIED)} cards, then {apkg.name}")
    col = Collection(str(tmp / "upgrade.anki2"))
    try:
        import_package(col, v1)
        old = scheduling(col)
        old_decks = deck_names(col, old)
        check(bool(old) and all(d == V1_DECK or d.startswith(f"{V1_DECK}::") for d in old_decks),
              f"v1: {len(old)} notes under {V1_DECK!r}", str(old_decks))
        shipped = {line.split()[1] for line in (FIXTURES / "feature-uids-v1.txt").read_text().splitlines()
                   if line and not line.startswith("#")}
        model = json.loads((FIXTURES / "ankc-qa-model-v1.json").read_text())
        notetype = col.models.by_name(model["name"])
        check(set(old) == shipped and notetype is not None and notetype["id"] == model["id"],
              "v1 matches the shipped deck: its guids and note type are the fixtures'")
        root = unlimited(col, V1_DECK)
        col.decks.select(root)
        for ease in STUDIED:
            col.sched.answerCard(col.sched.getCard(), ease)
        studied = scheduling(col)
        reviewed = sorted(g for g in studied if studied[g][3] != 0)  # [3]: type; 0 is new
        check(len(reviewed) == len(STUDIED), f"{len(STUDIED)} v1 cards studied", str(reviewed))

        import_package(col, apkg)
        after = scheduling(col)
        shared = sorted(set(studied) & set(lock))
        check(all(after[g][0] == studied[g][0] for g in shared),
              f"{len(shared)} feature notes kept their note ids (updated in place)")
        check(all(after[g][2:] == studied[g][2:] for g in studied),
              f"all {len(studied)} v1 cards kept their deck and scheduling, the {len(reviewed)} studied ones included",
              str([g for g in studied if after[g][2:] != studied[g][2:]][:5]))
        tagged = [g for g in shared if "kind::feature" in col.get_note(after[g][0]).tags]
        check(len(tagged) == len(shared), "the shared notes carry World Atlas tags (the update was applied)",
              f"{len(tagged)} of {len(shared)}")
        noted = [g for g in shared if NOTE_STYLE in col.get_note(after[g][0])["Answer"]]
        check(len(noted) == len(shared), "their backs now carry the card note, scheduling kept (above)",
              f"{len(noted)} of {len(shared)}")
        added = set(lock) - set(studied)
        check(deck_names(col, added) == {ROOT_DECK}, f'the {len(added)} new notes land in "{ROOT_DECK}"')

        target = col.decks.id_for_name(ROOT_DECK)
        col.set_deck([after[g][1] for g in studied], target)
        moved = scheduling(col)
        check(deck_names(col, studied) == {ROOT_DECK}, f'Change Deck moves all {len(studied)} v1 cards to "{ROOT_DECK}"')
        check(all(moved[g][3:] == studied[g][3:] for g in studied), "and they keep their scheduling")
        retired = len(set(studied) - set(lock))
        print(f"  {ROOT_DECK} now holds {len(moved)} cards: {len(lock)} current and {retired} retired v1 notes")
    finally:
        col.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--v1", type=Path, help="a Geographic Features v1 package to upgrade from (default: built)")
    args = parser.parse_args()
    print(f"anki {anki_version}")
    apkg = package()
    v1 = args.v1 or build_v1()
    every = positions.read().positions
    world = {c.uid for c in all_cards() if c.deck == WORLD.name}
    lock = {uid: p for uid, p in every.items() if uid in world}  # a frozen lock keeps retired uids
    with tempfile.TemporaryDirectory() as tmp:
        fresh_import(apkg, lock, Path(tmp))
        upgrade(v1, apkg, lock, Path(tmp))
        companion_imports(apkg, every, Path(tmp))
    if failures:
        sys.exit(f"{len(failures)} check(s) failed")
    print("import test: ok")


if __name__ == "__main__":
    main()
