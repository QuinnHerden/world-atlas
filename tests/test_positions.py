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
    """Placements in the countries block, region 1, in this order."""
    return [(u, "countries", 1) for u in uids]


A, B = "aaaaaaaaaa", "bbbbbbbbbb"


class FormatTest(unittest.TestCase):
    def test_round_trip_sorted_by_uid(self) -> None:
        lock = Lock(True, {B: Entry(1000, "features", 21), A: Entry(500, "continents", None)}, 3)
        text = dump(lock)
        self.assertEqual(text, f"draft: true\nseries: 3\n{A}: 500 block=continents region=-\n"
                               f"{B}: 1000 block=features region=21\n")
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
        lock = update(Lock(True, {"a": Entry(7, "countries", 3), "gone": Entry(9, "countries", 1)}), [("b", "continents", None), ("a", "features", 4)])
        self.assertEqual(lock, Lock(True, {"b": Entry(500, "continents", None), "a": Entry(1000, "features", 4)}))
        self.assertEqual(regenerate([]), {})

    def test_frozen_update_adds_only_and_keeps_every_entry(self) -> None:
        old = Lock(False, {"a": Entry(500, "countries", 1), "gone": Entry(700, "countries", 1), "b": Entry(1000, "countries", 2)})
        new = update(old, [("a", "countries", 3), ("x", "countries", 2), ("b", "countries", 2)])  # a's region changed: its entry still doesn't
        self.assertEqual(new, Lock(False, old.entries | {"x": Entry(600, "countries", 2)}))  # between a and the retired uid

    def test_stale_draft_is_one_the_current_order_would_rewrite(self) -> None:
        lock = Lock(True, {"a": Entry(500, "countries", 1), "b": Entry(1000, "countries", 1)})
        self.assertFalse(stale_draft(lock, at("a", "b")))
        self.assertTrue(stale_draft(lock, at("b", "a")))
        self.assertTrue(stale_draft(Lock(True, {"a": Entry(500, "countries", 1)}), at("a", "b")))
        self.assertTrue(stale_draft(lock, [("a", 1, 1), ("b", 1, 2)]))  # same order, b's region changed
        self.assertFalse(stale_draft(Lock(False, lock.entries), at("b", "a")))  # frozen: old slots by design

    def test_moved_names_frozen_cards_whose_block_or_region_changed(self) -> None:
        lock = Lock(False, {"a": Entry(500, "countries", 1), "b": Entry(1000, "countries", 1), "c": Entry(1500, "continents", None)})
        self.assertEqual(moved(lock, [("a", "countries", 1), ("c", "continents", None), ("new", "features", 5)]), [])
        self.assertEqual(len(moved(lock, [("a", "cities", 1), ("b", "countries", 7)])), 2)


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
              release=None, require=False, shallow=False):
        with mock.patch.object(positions, "base_text", lambda ref: texts.get(ref)), \
                mock.patch.object(positions, "release_tags", lambda: tags), \
                mock.patch.object(positions, "head_tags", lambda: list(head)), \
                mock.patch.object(positions, "shallow", lambda: shallow), \
                mock.patch.dict("os.environ", {"POSITIONS_BASE": ""}):
            return positions.guard(lock, strict, release, require)

    def test_guard_checks_the_base_ref_and_the_newest_tag_of_the_series(self) -> None:
        moved_a = Lock(False, {A: Entry(501, "countries", 1), B: Entry(1000, "countries", 2)}, 3)
        self.assertEqual(self.guard(self.BASE, {"origin/main": dump(self.BASE)}, [], True), ([], []))
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
        self.assertTrue(self.guard(self.BASE, {}, [], True)[0])
        errors, warnings = self.guard(self.BASE, {}, [], False)
        self.assertEqual((errors, len(warnings)), ([], 1))
        self.assertEqual(self.guard(Lock(True, {}, 3), {}, [], True), ([], []))  # a draft has nothing to guard

    def test_an_option_like_ref_is_never_passed_to_git(self) -> None:
        self.assertIsNone(positions.base_text("--output=/tmp/x"))


class LockedTagsTest(unittest.TestCase):
    TAGS = ["kind::country", "block::countries", "region::04", "tier::1"]

    def test_block_and_region_come_from_the_entry(self) -> None:
        self.assertEqual(locked_tags(self.TAGS, Entry(5, "countries", 7)),
                         ["kind::country", "block::countries", "region::07", "tier::1"])
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
    """The committed lock: series 3, frozen, in the four blocks (ADR 0009), Greenland right after Iceland."""

    def test_the_lock(self) -> None:
        lock = positions.read()
        self.assertEqual((lock.draft, lock.series), (False, 3))
        order = sorted(lock.entries, key=lambda u: lock.entries[u].position)
        blocks = [lock.entries[u].block for u in order]
        self.assertEqual(blocks, sorted(blocks, key=["continents", "countries", "features", "cities"].index))
        self.assertEqual(order.index("24rdGoHY6W"), order.index("PJEhGX8mTx") + 1)  # Greenland after Iceland
        self.assertEqual(lock.entries["24rdGoHY6W"], Entry(11500, "countries", 2))

if __name__ == "__main__":
    unittest.main()
