import random
import string
import unittest

from geofeat.positions import LIMIT, STRIDE, GapExhausted, Lock, dump, parse, place, regenerate, update


def uid(n: int) -> str:
    return f"U{n:09d}"


class FormatTest(unittest.TestCase):
    def test_round_trip_sorted_by_uid(self) -> None:
        lock = Lock(True, {"bbbbbbbbbb": 1000, "aaaaaaaaaa": 500})
        text = dump(lock)
        self.assertEqual(text, "draft: true\naaaaaaaaaa: 500\nbbbbbbbbbb: 1000\n")
        self.assertEqual(parse(text), lock)

    def test_rejects_bad_input(self) -> None:
        for text in ("aaaaaaaaaa: 500\n", "draft: true\naaaaaaaaaa: x\n", "draft: true\naaaaaaaaaa: 1\naaaaaaaaaa: 2\n",
                     "draft: true\naaaaaaaaaa: 1\nbbbbbbbbbb: 1\n", f"draft: false\naaaaaaaaaa: {LIMIT}\n"):
            with self.subTest(text), self.assertRaises(ValueError):
                parse(text)


class PlaceTest(unittest.TestCase):
    def test_draft_regenerates_at_the_stride(self) -> None:
        lock = update(Lock(True, {"a": 7, "gone": 9}), ["b", "a"])
        self.assertEqual(lock, Lock(True, {"b": 500, "a": 1000}))
        self.assertEqual(regenerate([]), {})

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


if __name__ == "__main__":
    unittest.main()
