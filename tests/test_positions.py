import random
import string
import unittest

from unittest import mock

import geofeat.positions as positions
from geofeat.positions import (
    LIMIT, STRIDE, Entry, GapExhausted, Lock, dump, frozen_errors, locked_tags, moved, parse, place, regenerate,
    stale_draft, update,
)


def uid(n: int) -> str:
    return f"U{n:09d}"


def at(*uids: str) -> list[tuple[str, object, int]]:
    """Placements in pass 1, region 1, in this order."""
    return [(u, 1, 1) for u in uids]


A, B = "aaaaaaaaaa", "bbbbbbbbbb"


class FormatTest(unittest.TestCase):
    def test_round_trip_sorted_by_uid(self) -> None:
        lock = Lock(True, {B: Entry(1000, 2, 21), A: Entry(500, "orientation", None)})
        text = dump(lock)
        self.assertEqual(text, f"draft: true\n{A}: 500 pass=orientation region=-\n{B}: 1000 pass=2 region=21\n")
        self.assertEqual(parse(text), lock)
        self.assertEqual(lock.positions, {A: 500, B: 1000})

    def test_rejects_bad_input(self) -> None:
        for text in (f"{A}: 500 pass=1 region=01\n", f"draft: true\n{A}: 500\n", f"draft: true\n{A}: x pass=1 region=01\n",
                     f"draft: true\n{A}: 1 pass=1 region=01\n{A}: 2 pass=1 region=01\n",
                     f"draft: true\n{A}: 1 pass=1 region=01\n{B}: 1 pass=1 region=01\n",
                     f"draft: false\n{A}: {LIMIT} pass=1 region=01\n",
                     f"draft: true\n{A}: 1 pass=orientation region=01\n", f"draft: true\n{A}: 1 pass=1 region=-\n",
                     f"draft: true\n{A}: 1 pass=1 region=00\n", f"draft: true\n{A}: 1 pass=3 region=01\n",
                     f"draft: true\n{A}: 1 pass=1 region=1\n"):
            with self.subTest(text), self.assertRaises(ValueError):
                parse(text)


class PlaceTest(unittest.TestCase):
    def test_draft_regenerates_at_the_stride(self) -> None:
        lock = update(Lock(True, {"a": Entry(7, 1, 3), "gone": Entry(9, 1, 1)}), [("b", "orientation", None), ("a", 2, 4)])
        self.assertEqual(lock, Lock(True, {"b": Entry(500, "orientation", None), "a": Entry(1000, 2, 4)}))
        self.assertEqual(regenerate([]), {})

    def test_frozen_update_adds_only_and_keeps_every_entry(self) -> None:
        old = Lock(False, {"a": Entry(500, 1, 1), "gone": Entry(700, 1, 1), "b": Entry(1000, 1, 2)})
        new = update(old, [("a", 1, 3), ("x", 1, 2), ("b", 1, 2)])  # a's region changed: its entry still doesn't
        self.assertEqual(new, Lock(False, old.entries | {"x": Entry(600, 1, 2)}))  # between a and the retired uid

    def test_stale_draft_is_one_the_current_order_would_rewrite(self) -> None:
        lock = Lock(True, {"a": Entry(500, 1, 1), "b": Entry(1000, 1, 1)})
        self.assertFalse(stale_draft(lock, at("a", "b")))
        self.assertTrue(stale_draft(lock, at("b", "a")))
        self.assertTrue(stale_draft(Lock(True, {"a": Entry(500, 1, 1)}), at("a", "b")))
        self.assertTrue(stale_draft(lock, [("a", 1, 1), ("b", 1, 2)]))  # same order, b's region changed
        self.assertFalse(stale_draft(Lock(False, lock.entries), at("b", "a")))  # frozen: old slots by design

    def test_moved_names_frozen_cards_whose_pass_or_region_changed(self) -> None:
        lock = Lock(False, {"a": Entry(500, 1, 1), "b": Entry(1000, 1, 1), "c": Entry(1500, "orientation", None)})
        self.assertEqual(moved(lock, [("a", 1, 1), ("c", "orientation", None), ("new", 2, 5)]), [])
        self.assertEqual(len(moved(lock, [("a", 2, 1), ("b", 1, 7)])), 2)


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
    BASE = Lock(False, {A: Entry(500, 1, 1), B: Entry(1000, 1, 2)})

    def test_draft_or_missing_base_passes(self) -> None:
        self.assertEqual(frozen_errors(Lock(True, {}), None), [])
        self.assertEqual(frozen_errors(Lock(False, {}), f"draft: true\n{A}: 500\n"), [])  # the old format, unparsed

    def test_adding_uids_passes(self) -> None:
        self.assertEqual(frozen_errors(Lock(False, self.BASE.entries | {"x" * 10: Entry(750, 1, 1)}), dump(self.BASE)), [])

    def test_any_change_to_a_frozen_entry_fails(self) -> None:
        for entries in ({A: Entry(500, 1, 1)}, {A: Entry(501, 1, 1), B: Entry(1000, 1, 2)},
                        {A: Entry(500, 1, 1), B: Entry(1000, 1, 3)}, {A: Entry(500, 2, 1), B: Entry(1000, 1, 2)}):
            with self.subTest(entries):
                self.assertTrue(frozen_errors(Lock(False, entries), dump(self.BASE)))

    def test_unfreezing_fails(self) -> None:
        self.assertTrue(frozen_errors(Lock(True, self.BASE.entries), dump(self.BASE)))

    def test_a_bad_base_is_an_error_not_a_pass(self) -> None:
        for text in ("draft: false\r\n", "<<<<<<< HEAD\n", f"draft: false\n{A}: 500\n"):
            with self.subTest(text):
                self.assertTrue(frozen_errors(self.BASE, text))

    def guard(self, lock: Lock, texts: dict[str, str | None], tag: str | None, strict: bool):
        with mock.patch.object(positions, "base_text", lambda ref: texts.get(ref)), \
                mock.patch.object(positions, "release_tag", lambda: tag), \
                mock.patch.dict("os.environ", {"POSITIONS_BASE": ""}):
            return positions.guard(lock, strict)

    def test_guard_checks_the_base_ref_and_the_release_tag(self) -> None:
        moved_a = Lock(False, {A: Entry(501, 1, 1), B: Entry(1000, 1, 2)})
        self.assertEqual(self.guard(self.BASE, {"origin/main": dump(self.BASE)}, None, True), ([], []))
        self.assertTrue(self.guard(moved_a, {"origin/main": dump(moved_a), "v9.0.0": dump(self.BASE)}, "v9.0.0", True)[0])

    def test_an_unreadable_base_fails_strict_and_warns_otherwise(self) -> None:
        self.assertTrue(self.guard(self.BASE, {}, None, True)[0])
        errors, warnings = self.guard(self.BASE, {}, None, False)
        self.assertEqual((errors, len(warnings)), ([], 1))
        self.assertEqual(self.guard(Lock(True, {}), {}, None, True), ([], []))  # a draft has nothing to guard

    def test_an_option_like_ref_is_never_passed_to_git(self) -> None:
        self.assertIsNone(positions.base_text("--output=/tmp/x"))


class LockedTagsTest(unittest.TestCase):
    TAGS = ["kind::country", "pass::1", "region::04", "tier::1"]

    def test_pass_and_region_come_from_the_entry(self) -> None:
        self.assertEqual(locked_tags(self.TAGS, Entry(5, 1, 7)), ["kind::country", "pass::1", "region::07", "tier::1"])
        self.assertEqual(locked_tags(self.TAGS, None), self.TAGS)

    def test_a_feature_gains_no_region_tag(self) -> None:
        self.assertEqual(locked_tags(["kind::feature", "pass::2"], Entry(5, 1, 7)), ["kind::feature", "pass::1"])


if __name__ == "__main__":
    unittest.main()
