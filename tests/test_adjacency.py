import tempfile
import unittest
from pathlib import Path

from shapely.geometry import box

from shapely.geometry import LineString

from geofeat.adjacency import (Edge, Override, Overrides, apply_overrides, build_graph, compute_edges, country_ids,
                               distance_km, report)
from geofeat.curriculum import Curriculum, Region, load_curriculum

# On the equator one degree is about 111 km.
WORLD = {
    "a": box(0, 0, 3, 1),
    "b": box(3, 0, 6, 1),  # shares a border with a
    "c": box(6.005, 0, 9, 1),  # 0.6 km from b: a 10m sliver, still land
    "d": box(9.5, 0, 12.5, 1),  # 56 km of water from c; every other pair is over 200 km apart
    "e": box(20, 0, 21, 1),
    "f": box(179, 0, 179.9, 1),  # 22 km from g across the antimeridian
    "g": box(-179.9, 0, -179, 1),
}


def kinds(edges: list[Edge]) -> dict[tuple[str, str], str]:
    return {e.pair: e.kind for e in edges}


class EdgesTest(unittest.TestCase):
    def test_land_and_sea_edges(self) -> None:
        edges = compute_edges(WORLD)
        self.assertEqual(kinds(edges), {("a", "b"): "land", ("b", "c"): "land", ("c", "d"): "sea", ("f", "g"): "sea"})
        km = {e.pair: e.km for e in edges}
        self.assertEqual(km[("a", "b")], 0.0)
        self.assertAlmostEqual(km[("c", "d")], 55.7, delta=0.5)
        self.assertAlmostEqual(km[("f", "g")], 22.3, delta=0.5)

    def test_sea_edges_stop_at_200_km(self) -> None:
        self.assertEqual(kinds(compute_edges({"x": box(0, 0, 1, 1), "y": box(2.75, 0, 3, 1)})), {("x", "y"): "sea"})  # 195 km
        self.assertEqual(compute_edges({"x": box(0, 0, 1, 1), "y": box(2.9, 0, 3, 1)}), [])  # 212 km

    def test_antimeridian_pairs_at_high_latitude(self) -> None:
        edges = compute_edges({"x": box(177.5, 60, 178.5, 61), "y": box(-178.5, 60, -177.5, 61)})
        self.assertEqual(kinds(edges), {("x", "y"): "sea"})  # 162 km across ±180° at 60° N

    def test_distance_is_measured_on_the_ground_not_in_degrees(self) -> None:
        # Two meridian lines 1° apart: nearest in degrees at 10° N (110 km), nearest on the ground at 80° N (19 km).
        self.assertAlmostEqual(distance_km(LineString([(0, 0), (0, 80)]), LineString([(1, 10), (1, 80)])), 19.4, delta=0.5)


class OverridesTest(unittest.TestCase):
    edges = [Edge("a", "b", "land", 0.0), Edge("c", "d", "sea", 55.7)]

    def test_add_and_remove(self) -> None:
        overrides = Overrides(add=[Override(a="e", b="d", reason="island")],
                              remove=[Override(a="d", b="c", reason="not a real crossing")])
        out = apply_overrides(self.edges, overrides, "abcde")
        self.assertEqual(out, [Edge("a", "b", "land", 0.0), Edge("d", "e", "override", reason="island")])
        out = apply_overrides(self.edges, overrides, "abcde", km={("d", "e"): 612.0})
        self.assertEqual(out[-1].km, 612.0)

    def test_stale_or_bad_edits_fail(self) -> None:
        cases = {
            "unknown id": Overrides(add=[Override(a="a", b="zz", reason="r")]),
            "already a land edge": Overrides(add=[Override(a="b", b="a", reason="r")]),
            "no such edge": Overrides(remove=[Override(a="a", b="e", reason="r")]),
            "two countries": Overrides(add=[Override(a="e", b="e", reason="r")]),
            "listed twice": Overrides(add=[Override(a="a", b="e", reason="r")], remove=[Override(a="e", b="a", reason="r")]),
        }
        for message, overrides in cases.items():
            with self.subTest(message), self.assertRaisesRegex(ValueError, message):
                apply_overrides(self.edges, overrides, "abcde")

    def test_reason_required(self) -> None:
        with self.assertRaises(ValueError):
            Overrides.model_validate({"add": [{"a": "a", "b": "e"}]})
        with self.assertRaises(ValueError):
            Overrides.model_validate({"add": [{"a": "a", "b": "e", "reason": ""}]})


class CacheTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.overrides = self.dir / "adjacency.yaml"
        self.cache = self.dir / "build" / "adjacency.json"
        self.overrides.write_text("add: []\n")
        self.calls = 0

    def world(self) -> dict:
        self.calls += 1
        return WORLD

    def build(self, key: str) -> list[Edge]:
        return build_graph(self.world, WORLD, key, self.overrides, self.cache)[1]

    def test_cache_is_reused_until_an_input_changes(self) -> None:
        first = self.build("k1")
        self.assertEqual(self.build("k1"), first)
        self.assertEqual(self.calls, 1)

        self.overrides.write_text("add: [{a: e, b: d, reason: island}]\n")
        edited = self.build("k1")
        self.assertEqual(self.calls, 2)  # loads the outlines to measure the new edge, keeps the cached edges
        self.assertAlmostEqual({e.pair: e.km for e in edited}[("d", "e")], 835, delta=2)

        self.overrides.write_text("add: [{a: e, b: d, reason: island}]\nremove: [{a: a, b: b, reason: test}]\n")
        self.assertNotIn(("a", "b"), kinds(self.build("k1")))
        self.assertEqual(self.calls, 2)  # nothing new to measure

        self.build("k2")
        self.assertEqual(self.calls, 3)  # new geometry inputs recompute

    def test_a_bad_edit_fails_and_a_corrupt_cache_is_a_miss(self) -> None:
        self.build("k1")
        self.overrides.write_text("add: [{a: a, b: b, reason: dup}]\n")
        with self.assertRaises(ValueError):
            self.build("k1")
        self.overrides.write_text("add: []\n")
        self.assertEqual(len(self.build("k1")), 4)
        self.assertEqual(self.calls, 1)
        self.cache.write_text("{not json")
        self.assertEqual(len(self.build("k1")), 4)
        self.assertEqual(self.calls, 2)


class ReportTest(unittest.TestCase):
    def test_connectivity_isolation_and_seams(self) -> None:
        edges = compute_edges(WORLD)
        regions = [Region(number=1, slug="west", name="West", entry="a", exit="c", countries=["a", "b", "c"]),
                   Region(number=2, slug="east", name="East", entry="d", exit="e", countries=["d", "e"]),
                   Region(number=3, slug="date-line", name="Date line", entry="f", exit="g", countries=["f", "g"])]
        lines, ok = report(sorted(WORLD), edges, edges, regions)
        text = "\n".join(lines)
        self.assertFalse(ok)
        self.assertIn("isolated after hand edits (1): e", text)
        self.assertIn("1 West (3): connected", text)
        self.assertIn("2 East (2): 2 components: d | e", text)
        self.assertIn("1→2  c → d: c–d (sea, 55.7 km); 1 cross edge(s)", text)
        self.assertIn("2→3  e → f: no direct edge; 0 cross edge(s)", text)

        fixed = apply_overrides(edges, Overrides(add=[Override(a="d", b="e", reason="island")]), WORLD)
        lines, ok = report(sorted(WORLD), edges, fixed, regions)
        self.assertTrue(ok)
        self.assertIn("isolated before hand edits (1): e", "\n".join(lines))


class CurriculumTest(unittest.TestCase):
    """data/curriculum.yaml against the state table, and the checks on a small one; no geometry."""

    def test_the_real_curriculum_is_valid(self) -> None:
        curriculum = load_curriculum(country_ids())
        self.assertEqual(len(curriculum.regions), 21)
        self.assertEqual(sum(len(r.countries) for r in curriculum.regions), len(country_ids()))
        self.assertEqual(len(country_ids()), 197)
        territories = [t for r in curriculum.regions for t in r.territories]
        disputes = [d for r in curriculum.regions for d in r.disputes]
        subdivisions = [c for r in curriculum.regions for c in r.subdivisions]
        self.assertEqual((len(subdivisions), len(territories), len(disputes)), (5, 25, 9))

    def small(self, **region) -> list[str]:
        base = {"number": 1, "slug": "r", "name": "R", "entry": "a", "exit": "b", "countries": ["a", "b", "c"]}
        data = {"passes": [], "start": "r", "regions": [base | region], "confusables": [["a", "b"]]}
        return Curriculum.model_validate(data).check("abc")

    def test_checks(self) -> None:
        self.assertEqual(self.small(), [])
        cases = {
            "states in no region: c": {"countries": ["a", "b"]},
            "unknown states: z": {"countries": ["a", "b", "c", "z"]},
            "exit b is not a walk node": {"pockets": {"b": "a"}},
            "host z is not a walk node": {"territories": {"t": "z"}},
            "in more than one region: c": {"countries": ["a", "b", "c", "c"]},
        }
        for message, region in cases.items():
            with self.subTest(message):
                self.assertTrue(any(message in e for e in self.small(**region)), self.small(**region))


if __name__ == "__main__":
    unittest.main()
