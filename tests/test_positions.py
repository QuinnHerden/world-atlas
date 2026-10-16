import random
import string
import unittest

from unittest import mock

import geofeat.positions as positions
from geofeat.decks import BY_SLUG
from geofeat.positions import (
    LIMIT, STRIDE, Entry, GapExhausted, Lock, dump, frozen_errors, locked_tags, moved, parse, place, regenerate,
    stale_draft, update,
)


def uid(n: int) -> str:
    return f"U{n:09d}"


def at(*uids: str) -> list[tuple[str, object, int, str]]:
    """Placements in World Atlas's countries block, region 1, in this order."""
    return [(u, "countries", 1, "world-atlas") for u in uids]


A, B = "aaaaaaaaaa", "bbbbbbbbbb"


class FormatTest(unittest.TestCase):
    def test_round_trip_sorted_by_uid(self) -> None:
        lock = Lock(True, {B: Entry(1000, "features", 21), A: Entry(500, "continents", None)}, 3)
        text = dump(lock)
        self.assertEqual(text, f"draft: true\nseries: 3\n{A}: 500 block=continents region=- deck=world-atlas\n"
                               f"{B}: 1000 block=features region=21 deck=world-atlas\n")
        self.assertEqual(parse(text), lock)
        self.assertEqual(lock.positions, {A: 500, B: 1000})

    def test_rejects_bad_input(self) -> None:
        head = "draft: true\nseries: 3\n"
        for text in (f"{A}: 500 block=countries region=01\n", f"draft: true\n{A}: 500 block=countries region=01\n",
                     f"{head}{A}: 500\n", f"{head}{A}: x block=countries region=01\n",
                     f"{head}{A}: 1 block=countries region=01\n{A}: 2 block=countries region=01\n",
                     f"{head}{A}: 1 block=countries region=01\n{B}: 1 block=countries region=01\n",
                     f"draft: false\nseries: 3\n{A}: {LIMIT} block=countries region=01\n",
                     f"{head}{A}: 1 block=continents region=01\n", f"{head}{A}: 1 block=countries region=-\n",
                     f"{head}{A}: 1 block=cities region=-\n", f"{head}{A}: 1 block=countries region=00\n",
                     f"{head}{A}: 1 block=capitals region=01\n", f"{head}{A}: 1 pass=1 region=01\n",
                     f"{head}{A}: 1 block=countries region=1\n", f"draft: true\nseries: 0\n"):
            with self.subTest(text), self.assertRaises(ValueError):
                parse(text)

    def test_a_feature_may_have_a_region_or_none(self) -> None:
        self.assertEqual(Entry(1, "features", None).region, None)
        self.assertEqual(Entry(1, "features", 4).region, 4)


class PlaceTest(unittest.TestCase):
    def test_draft_regenerates_at_the_stride(self) -> None:
        lock = update(Lock(True, {"a": Entry(7, "countries", 3), "gone": Entry(9, "countries", 1)}), [("b", "continents", None, "world-atlas"), ("a", "features", 4, "world-atlas")])
        self.assertEqual(lock, Lock(True, {"b": Entry(500, "continents", None), "a": Entry(1000, "features", 4)}))
        self.assertEqual(regenerate([]), {})

    def test_frozen_update_adds_only_and_keeps_every_entry(self) -> None:
        old = Lock(False, {"a": Entry(500, "countries", 1), "gone": Entry(700, "countries", 1), "b": Entry(1000, "countries", 2)})
        new = update(old, [("a", "countries", 3, "world-atlas"), ("x", "countries", 2, "world-atlas"), ("b", "countries", 2, "world-atlas")])  # a's region changed: its entry still doesn't
        self.assertEqual(new, Lock(False, old.entries | {"x": Entry(600, "countries", 2)}))  # between a and the retired uid

    def test_stale_draft_is_one_the_current_order_would_rewrite(self) -> None:
        lock = Lock(True, {"a": Entry(500, "countries", 1), "b": Entry(1000, "countries", 1)})
        self.assertFalse(stale_draft(lock, at("a", "b")))
        self.assertTrue(stale_draft(lock, at("b", "a")))
        self.assertTrue(stale_draft(Lock(True, {"a": Entry(500, "countries", 1)}), at("a", "b")))
        self.assertTrue(stale_draft(lock, [("a", "countries", 1, "world-atlas"), ("b", "countries", 2, "world-atlas")]))  # same order, b's region changed
        self.assertFalse(stale_draft(Lock(False, lock.entries), at("b", "a")))  # frozen: old slots by design

    def test_moved_names_frozen_cards_whose_block_or_region_changed(self) -> None:
        lock = Lock(False, {"a": Entry(500, "countries", 1), "b": Entry(1000, "countries", 1), "c": Entry(1500, "continents", None)})
        self.assertEqual(moved(lock, [("a", "countries", 1, "world-atlas"), ("c", "continents", None, "world-atlas"), ("new", "features", 5, "world-atlas")]), [])
        self.assertEqual(len(moved(lock, [("a", "cities", 1, "world-atlas"), ("b", "countries", 7, "world-atlas")])), 2)


    def test_after_pred_spread_evenly(self) -> None:
        self.assertEqual(place({"a": 500, "b": 1000}, ["a", "x", "y", "b"]), {"a": 500, "b": 1000, "x": 667, "y": 833})

    def test_pred_is_nearest_earlier_locked_card(self) -> None:
        # x follows b in the ideal order, so it goes after b's value even though a comes later in the order
        self.assertEqual(place({"a": 500, "b": 1000, "c": 1500}, ["c", "b", "x", "a"])["x"], 1250)

    def test_no_pred_goes_below_the_lowest(self) -> None:
        self.assertEqual(place({"a": 500}, ["x", "a"])["x"], 250)

    def test_end_extends_at_the_stride(self) -> None:
        self.assertEqual(place({"a": 500, "b": 1000}, ["a", "b", "x", "y"]), {"a": 500, "b": 1000, "x": 1500, "y": 2000})

    def test_empty_lock(self) -> None:
        self.assertEqual(place({}, ["x", "y"]), {"x": STRIDE, "y": 2 * STRIDE})

    def test_retired_uid_keeps_its_slot_and_bounds_the_gap(self) -> None:
        self.assertEqual(place({"a": 500, "gone": 600, "b": 1000}, ["a", "x", "b"]), {"a": 500, "gone": 600, "b": 1000, "x": 550})

    def test_exhausted_gap_fails(self) -> None:
        with self.assertRaises(GapExhausted):
            place({"a": 500, "b": 502}, ["a", "x", "y", "b"])
        self.assertEqual(place({"a": 500, "b": 502}, ["a", "x", "b"])["x"], 501)

    def test_eight_midpoint_inserts_fit_one_stride(self) -> None:
        lock = {"a": 500, "b": 1000}
        for n in range(8):
            lock = place(lock, ["a", f"x{n}", *[f"x{m}" for m in reversed(range(n))], "b"])
        self.assertEqual(len(set(lock.values())), 10)

    def test_limit(self) -> None:
        with self.assertRaises(GapExhausted):
            place({"a": LIMIT - 100}, ["a", "x"])

    def test_no_pred_below_a_card_at_zero(self) -> None:
        with self.assertRaises(GapExhausted):  # nothing fits below 0
            place({"a": 0, "b": 10}, ["x", "a", "b"])
        self.assertEqual(place({"a": 1, "b": 10}, ["x", "a", "y", "b"]), {"a": 1, "b": 10, "x": 0, "y": 6})

    def test_property_existing_values_never_change(self) -> None:
        rng = random.Random(6)
        for _ in range(500):
            locked_uids = [uid(n) for n in range(rng.randint(0, 60))]
            lock = dict(zip(locked_uids, rng.sample(range(0, 600_000), len(locked_uids))))
            new = ["".join(rng.choices(string.ascii_letters, k=10)) for _ in range(rng.randint(0, 40))]
            ideal = rng.sample(locked_uids, rng.randint(0, len(locked_uids))) + new
            rng.shuffle(ideal)
            try:
                result = place(lock, ideal)
            except GapExhausted:
                continue
            self.assertEqual({u: result[u] for u in lock}, lock)
            self.assertEqual(set(result), set(lock) | set(new))
            self.assertEqual(len(set(result.values())), len(result))
            self.assertTrue(all(0 <= v < LIMIT for v in result.values()))


class FreezeGuardTest(unittest.TestCase):
    BASE = Lock(False, {A: Entry(500, "countries", 1), B: Entry(1000, "countries", 2)}, 3)
    V2 = "draft: false\naaaaaaaaaa: 500 pass=1 region=01\n"  # v2.0.0's lock: no series line, the old entry format

    def test_draft_or_missing_base_passes(self) -> None:
        self.assertEqual(frozen_errors(Lock(True, {}, 3), None), [])
        self.assertEqual(frozen_errors(Lock(False, {}, 3), f"draft: true\n{A}: 500\n"), [])  # the old format, unparsed

    def test_adding_uids_passes(self) -> None:
        extended = Lock(False, self.BASE.entries | {"x" * 10: Entry(750, "countries", 1)}, 3)
        self.assertEqual(frozen_errors(extended, dump(self.BASE)), [])

    def test_any_change_to_a_frozen_entry_in_the_series_fails(self) -> None:
        for entries in ({A: Entry(500, "countries", 1)},
                        {A: Entry(501, "countries", 1), B: Entry(1000, "countries", 2)},
                        {A: Entry(500, "countries", 1), B: Entry(1000, "countries", 3)},
                        {A: Entry(500, "cities", 1), B: Entry(1000, "countries", 2)}):
            with self.subTest(entries):
                self.assertTrue(frozen_errors(Lock(False, entries, 3), dump(self.BASE)))

    def test_unfreezing_fails(self) -> None:
        self.assertTrue(frozen_errors(Lock(True, self.BASE.entries, 3), dump(self.BASE)))

    def test_a_new_series_is_a_fresh_freeze(self) -> None:
        reordered = Lock(False, {A: Entry(9000, "countries", 4)}, 3)
        self.assertEqual(frozen_errors(reordered, self.V2), [])  # series 2 (no series line) isn't compared with 3
        self.assertEqual(frozen_errors(Lock(True, {}, 3), self.V2), [])  # a draft of the new series, too

    def test_a_series_never_goes_back(self) -> None:
        self.assertTrue(frozen_errors(Lock(False, self.BASE.entries, 2), dump(self.BASE)))

    def test_series_against_the_release_tags(self) -> None:
        from geofeat.positions import series_errors

        lock = Lock(False, {}, 3)
        self.assertEqual(series_errors(lock, "v2.0.0", None), [])  # the next major starts series 3
        self.assertEqual(series_errors(lock, "v2.0.0", "v3.0.0"), [])  # and v3.0.0 releases it
        self.assertEqual(series_errors(lock, "v3.1.0", "v3.2.0"), [])
        self.assertTrue(series_errors(Lock(False, {}, 2), "v3.0.0", None))  # backwards
        self.assertTrue(series_errors(Lock(False, {}, 4), "v2.0.0", None))  # skips a major
        self.assertTrue(series_errors(lock, "v2.0.0", "v2.1.0"))  # a new series without a major release
        self.assertTrue(series_errors(Lock(False, {}, 4), "v3.0.0", "v3.1.0"))  # a series bump in a minor release
        self.assertEqual(series_errors(lock, None, None), [])

    def test_newest_is_by_version_and_ignores_other_tags(self) -> None:
        from geofeat.positions import newest

        tags = ["v2.0.0", "v10.0.0", "v3.1.0", "v3.0.0-rc1", "vtest", "v3.x"]
        self.assertEqual(newest(tags), "v10.0.0")
        self.assertEqual(newest(tags, 3), "v3.1.0")
        self.assertIsNone(newest(tags, 4))

    def test_a_bad_base_is_an_error_not_a_pass(self) -> None:
        for text in ("draft: false\r\n", "<<<<<<< HEAD\n", f"draft: false\nseries: 3\n{A}: 500\n"):
            with self.subTest(text):
                self.assertTrue(frozen_errors(self.BASE, text))

    def guard(self, lock: Lock, texts: dict[str, str | None], tags: list[str] | None, strict: bool, head=(),
              release=None, require=False, shallow=False, archived=()):
        with mock.patch.object(positions, "base_text", lambda ref: texts.get(ref)), \
                mock.patch.object(positions, "release_tags", lambda: tags), \
                mock.patch.object(positions, "archive_tags", lambda: list(archived)), \
                mock.patch.object(positions, "head_tags", lambda: list(head)), \
                mock.patch.object(positions, "shallow", lambda: shallow), \
                mock.patch.dict("os.environ", {"POSITIONS_BASE": ""}):
            return positions.guard(lock, strict, release, require)

    def test_guard_checks_the_base_ref_and_the_newest_tag_of_the_series(self) -> None:
        moved_a = Lock(False, {A: Entry(501, "countries", 1), B: Entry(1000, "countries", 2)}, 3)
        self.assertEqual(self.guard(self.BASE, {"origin/main": dump(self.BASE)}, ["v3.0.0"], True), ([], []))
        tags = ["v2.0.0", "v3.1.0", "v3.0.0"]
        self.assertTrue(self.guard(moved_a, {"origin/main": dump(moved_a), "v3.1.0": dump(self.BASE)}, tags, True)[0])

    def test_guard_accepts_a_new_series_at_a_major_release_only(self) -> None:
        reordered = Lock(False, {A: Entry(9000, "countries", 4)}, 3)
        texts = {"origin/main": self.V2, "v2.0.0": self.V2}
        errors, warnings = self.guard(reordered, texts, ["v2.0.0"], True)
        self.assertEqual(errors, [])
        self.assertRegex(" ".join(warnings), "next release must be v3.0.0")
        self.assertEqual(self.guard(reordered, texts, ["v2.0.0"], True, release="v3.0.0", require=True), ([], []))
        self.assertEqual(self.guard(reordered, texts, ["v2.0.0"], True, head=["v3.0.0"], require=True), ([], []))
        self.assertTrue(self.guard(reordered, texts, ["v2.0.0"], True, release="v2.1.0", require=True)[0])
        self.assertTrue(self.guard(reordered, texts, ["v2.0.0"], True, head=["v2.1.0"])[0])
        self.assertTrue(self.guard(reordered, texts, ["v2.0.0"], True, require=True)[0])  # a release needs RELEASE_VERSION
        self.assertTrue(self.guard(Lock(False, {}, 4), texts, ["v2.0.0"], True)[0])

    def test_a_release_ships_a_frozen_lock(self) -> None:
        texts = {"origin/main": self.V2, "v2.0.0": self.V2}
        self.assertTrue(self.guard(Lock(True, {}, 3), texts, ["v2.0.0"], True, release="v3.0.0", require=True)[0])

    def test_a_series_bump_after_a_major_release_needs_the_next_major(self) -> None:
        v3 = dump(self.BASE)
        bumped = Lock(False, {A: Entry(1, "countries", 1), B: Entry(2, "countries", 2)}, 4)
        texts = {"origin/main": v3, "v3.0.0": v3}
        self.assertTrue(self.guard(bumped, texts, ["v2.0.0", "v3.0.0"], True, release="v3.1.0", require=True)[0])
        self.assertEqual(self.guard(bumped, texts, ["v2.0.0", "v3.0.0"], True, release="v4.0.0", require=True)[0], [])

    def test_a_fresh_freeze_keeps_every_released_uid(self) -> None:
        dropping = Lock(False, {B: Entry(1, "countries", 1)}, 3)
        texts = {"origin/main": self.V2 + f"{B}: 1000 pass=1 region=01\n", "v2.0.0": self.V2}
        self.assertTrue(self.guard(dropping, texts, ["v2.0.0"], True)[0])  # drops A, released in v2.0.0
        keeping = Lock(False, {A: Entry(1, "countries", 1)}, 3)  # drops B, which was only ever on main
        self.assertEqual(self.guard(keeping, texts, ["v2.0.0"], True)[0], [])

    def test_unseen_tags_fail_strict(self) -> None:
        texts = {"origin/main": dump(self.BASE)}
        self.assertTrue(self.guard(self.BASE, texts, None, True)[0])
        self.assertTrue(self.guard(self.BASE, texts, ["v2.0.0"], True, shallow=True)[0])
        self.assertEqual(len(self.guard(self.BASE, texts, None, False)[1]), 1)

    def test_an_unreadable_base_fails_strict_and_warns_otherwise(self) -> None:
        self.assertTrue(self.guard(self.BASE, {}, ["v3.0.0"], True)[0])
        errors, warnings = self.guard(self.BASE, {}, ["v3.0.0"], False)
        self.assertEqual((errors, len(warnings)), ([], 1))
        self.assertEqual(self.guard(Lock(True, {}, 3), {}, [], True), ([], []))  # a draft has nothing to guard

    # Versioning restarted at v1.0.0: v1-v3 are archive/vX.Y.Z tags, and series 1 continues archived series 3's order.
    ARCHIVED = ["archive/v1.0.0", "archive/v2.0.0", "archive/v3.0.0"]

    def restarted(self, lock_v3: Lock | None = None) -> dict[str, str]:
        v3 = dump(lock_v3 or self.BASE)
        return {"origin/main": v3, "archive/v2.0.0": self.V2, "archive/v3.0.0": v3}

    def test_a_v1_release_of_series_1_is_accepted_with_no_release_tags(self) -> None:
        series_1 = Lock(False, self.BASE.entries, 1)
        texts = self.restarted()
        self.assertEqual(self.guard(series_1, texts, [], True, archived=self.ARCHIVED), ([], []))
        self.assertEqual(self.guard(series_1, texts, [], True, release="v1.0.0", require=True, archived=self.ARCHIVED),
                         ([], []))
        added = Lock(False, self.BASE.entries | {"x" * 10: Entry(750, "countries", 1)}, 1)
        self.assertEqual(self.guard(added, texts, [], True, release="v1.1.0", require=True, archived=self.ARCHIVED),
                         ([], []))

    def test_the_first_release_is_v1(self) -> None:
        texts = self.restarted()
        for lock, release in ((self.BASE, "v3.0.0"), (Lock(False, self.BASE.entries, 4), "v4.0.0")):
            with self.subTest(release):
                self.assertTrue(self.guard(lock, texts, [], True, release=release, require=True,
                                           archived=self.ARCHIVED)[0])
        self.assertTrue(self.guard(Lock(False, self.BASE.entries, 1), texts, [], True, release="v3.0.0", require=True,
                                   archived=self.ARCHIVED)[0])

    def test_archive_tags_are_honoured_for_dropped_uids(self) -> None:
        texts = self.restarted(Lock(False, {B: Entry(1000, "countries", 2)}, 3))  # A was only ever in v2
        dropping = Lock(False, {B: Entry(1000, "countries", 2)}, 1)
        errors = self.guard(dropping, texts, [], True, archived=self.ARCHIVED)[0]
        self.assertRegex(" ".join(errors), "drops uids released in archive/v2.0.0")
        self.assertTrue(self.guard(Lock(False, {A: Entry(1, "countries", 1)}, 2), texts, ["v1.0.0"], True,
                                   archived=self.ARCHIVED)[0])  # a later fresh freeze keeps them too

    def test_series_1_extends_the_archived_series_3_lock(self) -> None:
        moved_a = Lock(False, {A: Entry(501, "countries", 1), B: Entry(1000, "countries", 2)}, 1)
        texts = self.restarted() | {"origin/main": dump(moved_a)}
        self.assertRegex(" ".join(self.guard(moved_a, texts, [], True, archived=self.ARCHIVED)[0]),
                         "changes entries frozen on archive/v3.0.0")
        self.assertTrue(self.guard(moved_a, self.restarted(), [], True, archived=self.ARCHIVED)[0])  # and on main

    def test_the_restart_moves_only_the_listed_cards_to_their_listed_positions(self) -> None:
        moved_a = Lock(False, {A: Entry(501, "countries", 1), B: Entry(1000, "countries", 2)}, 1)
        with mock.patch.object(positions, "RESTART_MOVES", {A: 501}):
            self.assertEqual(self.guard(moved_a, self.restarted(), [], True, archived=self.ARCHIVED), ([], []))
            elsewhere = Lock(False, {A: Entry(502, "countries", 1), B: Entry(1000, "countries", 2)}, 1)
            self.assertTrue(self.guard(elsewhere, self.restarted(), [], True, archived=self.ARCHIVED)[0])
            texts = self.restarted() | {"origin/main": dump(moved_a), "v1.0.0": dump(moved_a)}
            self.assertEqual(self.guard(moved_a, texts, ["v1.0.0"], True, archived=self.ARCHIVED), ([], []))  # still
            back = Lock(False, self.BASE.entries, 1)  # once v1.0.0 is out, its lock is held as released
            self.assertRegex(" ".join(self.guard(back, texts, ["v1.0.0"], True, archived=self.ARCHIVED)[0]),
                             "changes entries frozen on origin/main")

    def test_the_real_restart_moves_put_the_oceans_after_the_continents(self) -> None:
        self.assertEqual(sorted(positions.RESTART_MOVES.values()), [3600, 3700, 3800, 3900])

    def test_the_restart_is_no_way_back_once_v1_is_released(self) -> None:
        series_1 = Lock(False, self.BASE.entries, 1)
        texts = self.restarted() | {"v1.0.0": dump(series_1)}
        self.assertRegex(" ".join(self.guard(series_1, texts, ["v1.0.0"], True, archived=self.ARCHIVED)[0]),
                         "never goes back")  # origin/main holding series 3 after v1.0.0
        self.assertTrue(frozen_errors(Lock(False, self.BASE.entries, 2), dump(self.BASE), pre_release=True))

    def test_before_v1_any_other_series_fails(self) -> None:
        for lock in (self.BASE, Lock(False, self.BASE.entries, 2), Lock(True, {}, 3)):
            with self.subTest(lock.series):
                self.assertTrue(self.guard(lock, self.restarted(), [], False, archived=self.ARCHIVED)[0])

    def test_a_tag_on_head_does_not_skip_the_first_release_rule(self) -> None:
        reshuffled = Lock(False, {A: Entry(1000, "countries", 1), B: Entry(500, "countries", 2)}, 2)
        texts = self.restarted() | {"origin/main": dump(Lock(False, self.BASE.entries, 1))}
        self.assertTrue(self.guard(reshuffled, texts, ["v2.0.0"], True, head=["v2.0.0"], require=True,
                                   archived=self.ARCHIVED)[0])

    def test_a_draft_series_1_lock_is_held_to_the_archived_frozen_lock(self) -> None:
        self.assertRegex(" ".join(self.guard(Lock(True, {}, 1), self.restarted(), [], False,
                                             archived=self.ARCHIVED)[0]), "draft again")

    def test_series_1_needs_the_archive_tags(self) -> None:
        series_1 = Lock(False, self.BASE.entries, 1)
        self.assertTrue(self.guard(series_1, self.restarted(), [], True)[0])
        self.assertEqual(len(self.guard(series_1, self.restarted(), [], False)[1]), 1)
        self.assertTrue(self.guard(Lock(False, {}, 2), self.restarted(), [], True, release="v2.0.0", require=True)[0])

    def test_an_option_like_ref_is_never_passed_to_git(self) -> None:
        self.assertIsNone(positions.base_text("--output=/tmp/x"))


class LockedTagsTest(unittest.TestCase):
    TAGS = ["kind::country", "block::countries", "region::04", "category::countries"]

    def test_block_and_region_come_from_the_entry(self) -> None:
        self.assertEqual(locked_tags(self.TAGS, Entry(5, "countries", 7)),
                         ["kind::country", "block::countries", "region::07", "category::countries"])
        self.assertEqual(locked_tags(self.TAGS, None), self.TAGS)

    def test_a_feature_gains_no_region_tag(self) -> None:
        self.assertEqual(locked_tags(["kind::feature", "block::features"], Entry(5, "features", 7)),
                         ["kind::feature", "block::features"])


class RetiredLockTest(unittest.TestCase):
    """A frozen lock keeps retired uids (ADR 0006): each must stay accounted for by a retired entry."""

    LOCK = Lock(False, {A: Entry(500, "features", 1), B: Entry(250, "features", 2)}, 3)

    def errors(self, entries: list[dict]) -> list[str]:
        from geofeat.check import retired_lock_errors

        return retired_lock_errors(self.LOCK, {B}, entries)

    def test_a_retired_uid_needs_its_retired_entry(self) -> None:
        self.assertEqual(self.errors([{"id": "x", "uid": A, "retired": True}, {"id": "y", "uid": B}]), [])
        self.assertRegex(" ".join(self.errors([{"id": "y", "uid": B}])), "no source entry has")
        self.assertRegex(" ".join(self.errors([{"id": "x", "uid": A}, {"id": "y", "uid": B}])), "aren't `retired: true`")

    def test_the_committed_lock_and_data(self) -> None:
        """Every uid in the committed lock belongs to an active card or a retired entry (`make check` runs this only
        on a rendered deck)."""
        from geofeat.check import retired_lock_errors
        from geofeat.sources import PATHS, all_cards
        from ruamel.yaml import YAML

        entries = [e for path in PATHS for e in (YAML(typ="safe").load(path) or [])]
        self.assertEqual(retired_lock_errors(positions.read(), {c.uid for c in all_cards()}, entries), [])

    def test_a_retired_capital_keeps_its_uid(self) -> None:
        country = {"id": "y", "uids": {"country": B, "capital": A}, "capital": {"name": "Y", "retired": True}}
        self.assertEqual(self.errors([country]), [])
        country["capital"]["retired"] = False
        self.assertRegex(" ".join(self.errors([country])), "aren't `retired: true`")


class LockTest(unittest.TestCase):
    """The committed lock: series 1 (archived series 3's order, renumbered at the v1.0.0 restart), frozen, in the four
    blocks (ADR 0009) but for the oceans after the continents, Greenland right after Iceland."""

    def test_the_lock(self) -> None:
        lock = positions.read()
        self.assertEqual((lock.draft, lock.series), (False, 1))
        order = sorted(lock.entries, key=lambda u: lock.entries[u].position)
        self.assertEqual(order[7:11], list(positions.RESTART_MOVES))  # the oceans, after the seven continents
        blocks = [lock.entries[u].block for u in order if u not in positions.RESTART_MOVES]
        self.assertEqual(blocks, sorted(blocks, key=["continents", "countries", "features", "cities", "subdivisions"].index))
        self.assertEqual(order.index("24rdGoHY6W"), order.index("PJEhGX8mTx") + 1)  # Greenland after Iceland
        self.assertEqual(lock.entries["24rdGoHY6W"], Entry(11500, "countries", 2))

    def test_every_deck_keeps_to_its_range(self) -> None:
        lock = positions.read()
        for uid, e in lock.entries.items():
            deck = BY_SLUG[e.deck]
            self.assertTrue(deck.base <= e.position < deck.limit, uid)
        firsts = {slug: min(e.position for e in lock.entries.values() if e.deck == slug) for slug in BY_SLUG}
        self.assertEqual(firsts, {"world-atlas": 500, "italian-regions": 600_500, "us-states": 650_500,
                                  "brazilian-states": 700_500, "canadian-provinces": 750_500})


class DeckTest(unittest.TestCase):
    """Companion decks (ADR 0012): each deck's positions in its own range, and a card's deck frozen with them."""

    US = "us-states"

    def test_a_line_without_a_deck_is_world_atlas(self) -> None:
        lock = parse(f"draft: false\nseries: 3\n{A}: 500 block=continents region=-\n"
                     f"{B}: 650500 block=subdivisions region=- deck=us-states\n")
        self.assertEqual(lock.entries[A].deck, "world-atlas")
        self.assertEqual(lock.entries[B], Entry(650_500, "subdivisions", None, self.US))

    def test_entries_must_fit_their_deck(self) -> None:
        for args in ((650_500, "subdivisions", None, "world-atlas"), (500, "subdivisions", None, self.US),
                     (650_500, "countries", 1, self.US), (650_500, "subdivisions", 1, self.US), (1, "countries", 1, "nope")):
            with self.subTest(args), self.assertRaises(ValueError):
                Entry(*args)

    def test_new_uids_go_in_their_decks_range(self) -> None:
        old = Lock(False, {A: Entry(500, "continents", None)}, 3)
        placed = [(A, "continents", None, "world-atlas"), ("c" * 10, "subdivisions", None, self.US),
                  ("d" * 10, "subdivisions", None, self.US), ("e" * 10, "countries", 1, "world-atlas")]
        self.assertEqual(update(old, placed).positions, {A: 500, "c" * 10: 650_500, "d" * 10: 651_000, "e" * 10: 1000})
        draft = update(Lock(True, {}, 3), placed)
        self.assertEqual(draft.positions, {A: 500, "e" * 10: 1000, "c" * 10: 650_500, "d" * 10: 651_000})

    def test_a_new_first_card_goes_below_the_decks_lowest(self) -> None:
        deck = BY_SLUG[self.US]
        placed = place({"x": 651_000}, ["new", "x"], deck)
        self.assertTrue(deck.base <= placed["new"] < 651_000, placed)

    def test_a_draft_past_its_range_fails(self) -> None:
        deck = BY_SLUG[self.US]
        with self.assertRaises(GapExhausted):
            regenerate([f"u{i}" for i in range(100)], deck)

    def test_a_deck_that_fills_its_range_stops(self) -> None:
        deck = BY_SLUG[self.US]
        with self.assertRaises(positions.GapExhausted):
            place({"a": deck.limit - 600}, ["a", "b", "c"], deck)

    def test_a_changed_deck_is_an_error(self) -> None:
        lock = Lock(False, {A: Entry(650_500, "subdivisions", None, self.US)}, 3)
        self.assertEqual(positions.deck_errors(lock, [(A, "subdivisions", None, self.US)]), [])
        self.assertEqual(len(positions.deck_errors(lock, [(A, "subdivisions", None, "italian-regions")])), 1)
        changed = Lock(False, {A: Entry(600_500, "subdivisions", None, "italian-regions")}, 3)
        self.assertEqual(len(positions.frozen_errors(changed, dump(lock))), 1)  # the freeze guard holds the deck too

if __name__ == "__main__":
    unittest.main()
