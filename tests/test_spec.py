import unittest

from pydantic import ValidationError

from geofeat.model import Expect, Feature, FrameOptions, Part
from geofeat.resolve import features_by_id
from geofeat.spec import ADMIN1_LAYER, BASEMAP_LAYERS, RenderSpec
from geofeat.style import AREA_ALPHA, WATER_AREA_ALPHA


def feature(**kw) -> Feature:
    base = {"id": "x", "name": "X", "type": "Plain", "category": "Deserts, Plateaus & Plains", "tier": 3, "style": "area",
            "geometry": [Part(layer="10m_geography_regions_polys", select={"ne_id": 1})], "expect": Expect(bbox=(0, 0, 1, 1))}
    return Feature(**base | kw)


class FromFeatureTest(unittest.TestCase):
    def test_a_feature_card_has_no_overlays(self) -> None:
        spec = RenderSpec.from_feature(feature())
        self.assertEqual((spec.country, spec.dot, spec.outline), (None, None, None))

    def test_fill_alpha_is_lighter_at_sea_and_for_bands(self) -> None:
        self.assertEqual(RenderSpec.from_feature(feature()).fill_alpha, AREA_ALPHA)
        self.assertEqual(RenderSpec.from_feature(feature(type="Sea", category="Water Bodies")).fill_alpha, WATER_AREA_ALPHA)
        self.assertEqual(RenderSpec.from_feature(feature(style="band")).fill_alpha, WATER_AREA_ALPHA)

    def test_land_clip_and_close_up_borders(self) -> None:
        self.assertTrue(RenderSpec.from_feature(feature()).land_clip)
        self.assertFalse(RenderSpec.from_feature(feature(style="band")).land_clip)
        self.assertFalse(RenderSpec.from_feature(feature(type="Island", category="Islands")).land_clip)
        self.assertTrue(RenderSpec.from_feature(feature(type="Lake", category="Water Bodies")).close_up_borders)
        self.assertFalse(RenderSpec.from_feature(feature()).close_up_borders)

    def test_frozen_and_strict(self) -> None:
        spec = RenderSpec.from_feature(feature())
        with self.assertRaises(ValidationError):
            spec.style = "line"
        with self.assertRaises(ValidationError):
            RenderSpec(style="area", geometry=(), colour="blue")
        with self.assertRaises(ValidationError):
            RenderSpec(style="area", geometry=(), country="capital")

    def test_the_dump_includes_defaults(self) -> None:
        self.assertIn("outline", RenderSpec.from_feature(feature()).model_dump())


class LayersTest(unittest.TestCase):
    def test_selectors_plus_basemap(self) -> None:
        self.assertEqual(RenderSpec.from_feature(feature()).layers(), BASEMAP_LAYERS | {"10m_geography_regions_polys"})

    def test_admin1_borders_are_declared_only_when_drawn(self) -> None:
        self.assertNotIn(ADMIN1_LAYER, RenderSpec.from_feature(feature()).layers())
        self.assertIn(ADMIN1_LAYER, RenderSpec.from_feature(feature(frame=FrameOptions(admin1=True))).layers())

    def test_referenced_features_layers_are_included(self) -> None:
        for f in features_by_id().values():
            refs = [p.feature for p in f.geometry if p.feature] + f.frame.context
            for other in refs:
                with self.subTest(f.id, other=other):
                    self.assertLessEqual(RenderSpec.from_feature(features_by_id()[other]).layers(),
                                         RenderSpec.from_feature(f).layers())


if __name__ == "__main__":
    unittest.main()
