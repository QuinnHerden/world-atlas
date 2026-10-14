import unittest

from pydantic import ValidationError

from geofeat.model import Expect, Feature, FrameOptions, Part
from geofeat.spec import RenderSpec
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

    def test_close_up_borders(self) -> None:
        self.assertTrue(RenderSpec.from_feature(feature(type="Lake", category="Water Bodies")).close_up_borders)
        self.assertFalse(RenderSpec.from_feature(feature()).close_up_borders)

    def test_renaming_retiering_or_retyping_within_a_look_keeps_the_spec(self) -> None:
        self.assertEqual(RenderSpec.from_feature(feature()),
                         RenderSpec.from_feature(feature(id="y", name="Y", tier=1, type="Desert")))

    def test_context_and_former_names_are_left_to_the_job(self) -> None:
        spec = RenderSpec.from_feature(feature(frame=FrameOptions(context=["nile"], former="aral.geojson", min_span_km=3000)))
        self.assertEqual(spec.frame, FrameOptions(min_span_km=3000))

    def test_frozen_and_strict(self) -> None:
        spec = RenderSpec.from_feature(feature())
        with self.assertRaises(ValidationError):
            spec.style = "line"
        with self.assertRaises(ValidationError):
            RenderSpec(style="area", colour="blue")
        with self.assertRaises(ValidationError):
            RenderSpec(style="area", country="capital")

    def test_the_dump_includes_defaults(self) -> None:
        self.assertIn("outline", RenderSpec.from_feature(feature()).model_dump())


if __name__ == "__main__":
    unittest.main()
