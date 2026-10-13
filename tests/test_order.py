import unittest

from geofeat.model import AllowNested, Expect, Feature, FrameOptions, Part
from geofeat.order import Siblings, dependencies, inverted, study_order


def feature(id: str, category: str = "Water Bodies", tier: int = 1, **extra) -> Feature:
    return Feature(id=id, name=id, type="Sea", category=category, tier=tier, style="area",
                   geometry=extra.pop("geometry", [Part(file="x.geojson")]), expect=Expect(bbox=(-180, -90, 180, 90)),
                   **extra)


def ids(features: list[Feature]) -> list[str]:
    return [f.id for f in features]


NO_SIBLINGS = Siblings(area_km2={}, close=[], nested=[])


class StudyOrderTest(unittest.TestCase):
    def test_tiers_in_order(self) -> None:
        features = [feature("c", tier=3), feature("a", tier=1), feature("b", tier=2)]
        self.assertEqual(ids(study_order(features, set(), set())), ["a", "b", "c"])

    def test_parent_before_child(self) -> None:
        features = [feature("child"), feature("other", "Rivers & Deltas"), feature("parent")]
        self.assertEqual(ids(study_order(features, {("parent", "child")}, set())), ["parent", "other", "child"])

    def test_parent_in_a_later_tier_is_not_promoted(self) -> None:
        features = [feature("parent", tier=2), feature("child", tier=1)]
        edges = {("parent", "child")}
        self.assertEqual(ids(study_order(features, edges, set())), ["child", "parent"])
        self.assertEqual(inverted(features, edges), [("parent", "child")])

    def test_categories_interleave(self) -> None:
        features = [feature(f"w{i}") for i in range(3)] + [feature(f"r{i}", "Rivers & Deltas") for i in range(3)]
        cats = [f.category for f in study_order(features, set(), set())]
        self.assertFalse(any(a == b for a, b in zip(cats, cats[1:])))

    def test_uneven_categories_spread_out(self) -> None:
        features = [feature(f"w{i}") for i in range(4)] + [feature(f"r{i}", "Rivers & Deltas") for i in range(2)]
        cats = [f.category[0] for f in study_order(features, set(), set())]
        self.assertFalse(any(a == b == "R" for a, b in zip(cats, cats[1:])))
        self.assertLessEqual(sum(a == b for a, b in zip(cats, cats[1:])), 1)

    def test_near_siblings_kept_apart(self) -> None:
        features = [feature("a"), feature("b"), feature("c"), feature("d"), feature("e")]
        order = ids(study_order(features, set(), {frozenset(("a", "b"))}))
        self.assertGreaterEqual(abs(order.index("a") - order.index("b")), 4)

    def test_cycle_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            study_order([feature("a"), feature("b")], {("a", "b"), ("b", "a")}, set())


class DependenciesTest(unittest.TestCase):
    def test_subtracted_feature_is_the_parent(self) -> None:
        plateau = feature("plateau", geometry=[Part(file="x.geojson"), Part(feature="range", subtract=True)])
        self.assertEqual(dependencies([plateau, feature("range")], NO_SIBLINGS), {("range", "plateau")})

    def test_context_feature_is_the_parent(self) -> None:
        delta = feature("delta", frame=FrameOptions(context=["river"]))
        self.assertEqual(dependencies([delta, feature("river")], NO_SIBLINGS), {("river", "delta")})

    def test_added_or_allowed_feature_larger_one_is_the_parent(self) -> None:
        areas = Siblings(area_km2={"sea": 100.0, "gulf": 10.0, "desert": 5.0, "peninsula": 50.0}, close=[], nested=[])
        sea = feature("sea", geometry=[Part(file="x.geojson"), Part(feature="gulf")])
        desert = feature("desert", geometry=[Part(feature="peninsula")],
                         allow_nested=[AllowNested(id="peninsula", reason="a named part of it")])
        features = [sea, feature("gulf"), desert, feature("peninsula")]
        self.assertEqual(dependencies(features, areas), {("sea", "gulf"), ("peninsula", "desert")})

    def test_nested_pair_outer_first_unless_it_makes_a_cycle(self) -> None:
        delta = feature("delta", frame=FrameOptions(context=["river"]))
        siblings = Siblings(area_km2={}, close=[], nested=[("delta", "river"), ("range", "pass")])
        features = [delta, feature("river"), feature("range"), feature("pass")]
        self.assertEqual(dependencies(features, siblings), {("river", "delta"), ("range", "pass")})

    def test_place_nested_in_a_climate_system_is_independent(self) -> None:
        belt = Feature(id="belt", name="belt", type="Climate belt", category="Climate Systems", tier=1, style="band",
                       geometry=[Part(file="x.geojson")], expect=Expect(bbox=(-180, -90, 180, 90)))
        siblings = Siblings(area_km2={}, close=[], nested=[("belt", "strait")])
        self.assertEqual(dependencies([belt, feature("strait")], siblings), set())

    def test_retired_references_are_ignored(self) -> None:
        cut = feature("cut", geometry=[Part(file="x.geojson"), Part(feature="gone", subtract=True)])
        self.assertEqual(dependencies([cut], NO_SIBLINGS), set())
