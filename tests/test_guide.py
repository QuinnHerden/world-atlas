"""The PDF guide follows positions.lock: entry N is card N in Anki, sectioned by pass and then region."""

import importlib.util
import re
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from test_order_engine import make

HAS_REPORTLAB = importlib.util.find_spec("reportlab") is not None
if HAS_REPORTLAB:
    from geofeat import guide


def cards():
    return [
        make("continent", "europe", note="A continent."),
        make("country", "a", region=1, prompt="Country", note="Country *a*."),
        make("capital", "a", region=1, prompt="City", note="Capital of a."),
        make("feature", "river", tier=2, prompt="River", note="A river."),
        make("country", "b", region=2, prompt="Country", note="Country b."),
        make("feature", "lake", tier=3, prompt="Lake", note="A lake."),
    ]


FEATURE_REGIONS = {"feature:river": 1, "feature:lake": 2}


def place_of(card):
    """As the lock would record it: the pass, and the region (None for orientation)."""
    if card.study_pass == "orientation":
        return "orientation", None
    return card.study_pass, int(card.region) if card.region else FEATURE_REGIONS[card.key]


@unittest.skipUnless(HAS_REPORTLAB, "needs the guide dependency group (uv sync --group guide)")
class GuideTest(unittest.TestCase):
    def lock(self, keys: list[str]) -> dict[str, int]:
        uid = {c.key: c.uid for c in cards()}
        return {uid[k]: 100 * (i + 1) for i, k in enumerate(keys)} | {"Retired000": 150}

    ORDER = ["continent:europe", "country:a", "feature:river", "capital:a", "country:b", "feature:lake"]

    def test_entries_follow_the_lock(self) -> None:
        got = guide.entries(list(reversed(cards())), self.lock(self.ORDER))
        self.assertEqual([e.card.key for e in got], self.ORDER)
        self.assertEqual([e.number for e in got], [1, 2, 3, 4, 5, 6])  # the retired uid takes no number

    def test_a_card_missing_from_the_lock_fails(self) -> None:
        with self.assertRaises(SystemExit):
            guide.entries(cards(), self.lock(self.ORDER[:-1]))

    def test_sections_by_pass_then_region(self) -> None:
        parts = guide.sections(guide.entries(cards(), self.lock(self.ORDER)), place_of)
        self.assertEqual([(s.study_pass, s.region, len(s.entries)) for s in parts],
                         [("orientation", None, 1), (1, 1, 3), (1, 2, 1), (2, 2, 1)])

    def runs(self, layout: list[tuple[str, int]]) -> list[tuple[object, int | None, list[str]]]:
        """Section made-up pass-1 countries, given as (id, data region) in lock order."""
        picked = [make("country", id, region=region, note="n") for id, region in layout]
        parts = guide.sections(guide.entries(picked, {c.uid: i for i, c in enumerate(picked)}), place_of)
        return [(s.study_pass, s.region, [e.card.id for e in s.entries]) for s in parts]

    def test_a_moved_card_joins_the_section_after_it(self) -> None:
        self.assertEqual(self.runs([("a", 1), ("b", 1), ("p", 2), ("c", 1), ("d", 2)]),
                         [(1, 1, ["a", "b", "p", "c"]), (1, 2, ["d"])])

    def test_a_region_whose_only_card_moved(self) -> None:
        self.assertEqual(self.runs([("a", 1), ("b", 1), ("p", 2), ("c", 1), ("d", 1), ("e", 3)]),
                         [(1, 1, ["a", "b", "p", "c", "d"]), (1, 3, ["e"])])

    def test_a_tie_keeps_the_card_in_its_own_region(self) -> None:
        self.assertEqual(self.runs([("a", 1), ("p", 2), ("b", 1), ("q", 2), ("e", 3)]),
                         [(1, 1, ["a", "p", "b"]), (1, 2, ["q"]), (1, 3, ["e"])])

    def test_a_card_left_behind_in_a_later_region(self) -> None:
        """Post-freeze drift: x's region changed to 1, but its lock slot is still in region 2."""
        self.assertEqual(self.runs([("a", 1), ("b", 2), ("c", 2), ("x", 1), ("d", 2), ("e", 3)]),
                         [(1, 1, ["a"]), (1, 2, ["b", "c", "x", "d"]), (1, 3, ["e"])])

    def test_strays_at_the_end_join_the_last_section(self) -> None:
        self.assertEqual(self.runs([("a", 1), ("b", 2), ("c", 2), ("x", 1)]),
                         [(1, 1, ["a"]), (1, 2, ["b", "c", "x"])])

    def test_pdf_entries_and_bookmarks_follow_the_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            images = {}
            for c in cards():
                images[c.key] = Path(tmp, f"{c.id}-{c.kind}.png")
                Image.new("RGB", (1600, 1000), "white").save(images[c.key])
            parts = guide.sections(guide.entries(cards(), self.lock(self.ORDER)), place_of)
            out = Path(tmp, "guide.pdf")
            doc = guide.build(parts, {1: "One", 2: "Two"}, images, out)
            data = out.read_bytes()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertIn(b"/Outlines", data)
        uid = {c.key: c.uid for c in cards()}
        self.assertEqual([k for k in doc.bookmarks if k.startswith("card-")], [f"card-{uid[k]}" for k in self.ORDER])
        self.assertEqual([k for k in doc.bookmarks if not k.startswith("card-")],
                         ["pass-orientation", "pass-1", "pass-1-region-01", "pass-1-region-02", "pass-2",
                          "pass-2-region-02"])

    def test_output_paths(self) -> None:
        slug = re.sub(r"[^a-z0-9]+", "-", guide.ROOT_DECK.lower()).strip("-")
        self.assertEqual(guide.out_path().name, f"{slug}-guide.pdf")
        self.assertEqual(guide.out_path(4).name, f"{slug}-guide-04.pdf")


if __name__ == "__main__":
    unittest.main()
