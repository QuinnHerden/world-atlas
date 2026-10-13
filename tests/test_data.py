import unittest
from typing import get_args
from unittest import mock

import geopandas as gpd
from shapely.geometry import Point, box

import geofeat.resolve as resolve
from geofeat.check import provenance_errors
from geofeat.model import FAMILY, AllowNested, Expect, Feature, FeatureType, Part
from geofeat.pairs import Pair, compare
from geofeat.resolve import area_km2, _drop_slivers, clip_to_land


def feature(id: str, type: str, style: str = "area", **extra) -> Feature:
    return Feature(id=id, name=id, type=type, category="Deserts, Plateaus & Plains", tier=1, style=style,
                   geometry=[Part(file="x.geojson")], expect=Expect(bbox=(-180, -90, 180, 90)), **extra)


class VocabularyTest(unittest.TestCase):
    def test_every_type_has_a_family(self) -> None:
        self.assertEqual(set(FAMILY), set(get_args(FeatureType)))


class PairTest(unittest.TestCase):
    outer, inner = box(10, 10, 14, 13), box(11, 11, 12, 12)

    def test_same_family_covering_is_flagged(self) -> None:
        pair = compare(feature("a", "Plain"), self.outer, feature("b", "Desert"), self.inner)
        self.assertTrue(pair.same_family)
        self.assertTrue(pair.flagged)
        self.assertFalse(pair.nested)

    def test_other_family_covering_is_nested(self) -> None:
        pair = compare(feature("a", "Mountain range"), self.outer, feature("b", "Plain"), self.inner)
        self.assertFalse(pair.flagged)
        self.assertTrue(pair.nested)

    def test_allow_nested_turns_a_flag_into_allowed(self) -> None:
        a = feature("a", "Plain", allow_nested=[AllowNested(id="b", reason="b is a named part of a")])
        pair = compare(a, self.outer, feature("b", "Desert"), self.inner)
        self.assertFalse(pair.flagged)
        self.assertTrue(pair.nested)
        self.assertEqual(pair.allowed, "b is a named part of a")
        self.assertTrue(str(pair).startswith("allowed "))

    def test_near_identical_is_flagged_even_when_allowed(self) -> None:
        self.assertTrue(Pair("a", "b", same_family=False, distance_km=0, iou=0.85, cover=0.9, allowed="reason").flagged)

    def test_far_apart_is_no_pair(self) -> None:
        self.assertIsNone(compare(feature("a", "Plain"), box(0, 0, 1, 1), feature("b", "Plain"), box(20, 0, 21, 1)))


class DropSliversTest(unittest.TestCase):
    keep = box(0, 0, 10, 10)

    def test_small_cut_scrap_is_dropped(self) -> None:
        cut = self.keep.difference(box(9.9, -1, 9.99, 11))  # leaves a 0.01 deg strip (~1,200 km²) on the east edge
        result, trimmed = _drop_slivers(feature("a", "Plain"), self.keep, cut)
        self.assertEqual(result.geom_type, "Polygon")
        self.assertEqual(trimmed, 0)

    def test_large_cut_piece_is_kept(self) -> None:
        cut = self.keep.difference(box(4, -1, 5, 11))
        result, _ = _drop_slivers(feature("a", "Plain"), self.keep, cut)
        self.assertEqual(result.geom_type, "MultiPolygon")

    def test_too_many_slivers_fail(self) -> None:
        many = box(0, 0, 1, 1).difference(box(0.96, -1, 0.97, 2))  # scrap is a large share of a small feature
        with self.assertRaisesRegex(ValueError, "slivers"):
            _drop_slivers(feature("a", "Plain"), box(0, 0, 1, 1), many)

    def test_trim_to_largest_keeps_one_polygon(self) -> None:
        keep = box(0, 0, 10, 10).union(box(20, 0, 21, 1))  # an untouched islet as well as the cut piece
        cut = keep.difference(box(4, -1, 5, 11))
        result, trimmed = _drop_slivers(feature("a", "Plain", trim_to_largest=True), keep, cut)
        self.assertEqual(result.geom_type, "Polygon")
        self.assertAlmostEqual(trimmed, area_km2(box(0, 0, 4, 10)) + area_km2(box(20, 0, 21, 1)), delta=1)


class LandClipTest(unittest.TestCase):
    land = gpd.GeoDataFrame(geometry=[box(0, 0, 5, 5)], crs="EPSG:4326")
    shape = box(3, 3, 8, 8)

    def clip(self, f: Feature):
        with mock.patch.object(resolve, "layer", lambda name: self.land):
            return clip_to_land(f, self.shape)

    def test_land_family_area_is_clipped(self) -> None:
        self.assertTrue(self.clip(feature("a", "Plain")).equals(box(3, 3, 5, 5)))
        self.assertTrue(self.clip(feature("a", "Peninsula")).equals(box(3, 3, 5, 5)))

    def test_water_islands_and_lines_are_not(self) -> None:
        for f in (feature("a", "Sea"), feature("a", "Island"), feature("a", "Corridor", style="line")):
            self.assertTrue(self.clip(f).equals(self.shape), f.type)

    def test_shape_wholly_at_sea_clips_to_empty(self) -> None:
        with mock.patch.object(resolve, "layer", lambda name: self.land):
            self.assertTrue(clip_to_land(feature("a", "Plain"), box(10, 10, 11, 11)).is_empty)


class ProvenanceTest(unittest.TestCase):
    def collection(self, **props) -> dict:
        base = {"source": "Wikipedia 'X' coordinates", "method": "reference-coords", "refs": ["Wikipedia 'X'"]}
        return {"features": [{"type": "Feature", "properties": {**base, **props}, "geometry": Point(0, 0).__geo_interface__}]}

    def test_complete_provenance_passes(self) -> None:
        self.assertEqual(provenance_errors("x.geojson", self.collection()), [])

    def test_missing_or_unknown_method_fails(self) -> None:
        missing = self.collection()
        del missing["features"][0]["properties"]["method"]
        self.assertTrue(provenance_errors("x.geojson", missing))
        self.assertTrue(provenance_errors("x.geojson", self.collection(method="guess")))

    def test_unverified_or_placeholder_source_fails(self) -> None:
        for source in ("Approximate. UNVERIFIED: check later", "Placeholder shape"):
            errors = provenance_errors("x.geojson", self.collection(source=source))
            self.assertTrue(any("unverified or a placeholder" in e for e in errors), source)

    def test_refs_must_be_a_non_empty_list(self) -> None:
        for refs in ("Wikipedia", [], [""]):
            self.assertTrue(provenance_errors("x.geojson", self.collection(refs=refs)), refs)


if __name__ == "__main__":
    unittest.main()
