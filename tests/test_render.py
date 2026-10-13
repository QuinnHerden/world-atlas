import unittest

from geofeat.model import Expect, Feature, Part
from geofeat.render import input_hash


def area_feature(feature_type: str) -> Feature:
    return Feature(id="x", name="X", type=feature_type, category="Regions & Rifts", tier=3, style="area",
                   geometry=[Part(layer="10m_land", select={"x": 1})], expect=Expect(bbox=(0, 0, 1, 1)))


class InputHashTest(unittest.TestCase):
    def test_retyping_into_or_out_of_a_land_family_re_renders(self) -> None:
        self.assertNotEqual(input_hash(area_feature("Plain")), input_hash(area_feature("Island")))

    def test_retyping_within_land_families_does_not(self) -> None:
        self.assertEqual(input_hash(area_feature("Plain")), input_hash(area_feature("Desert")))


if __name__ == "__main__":
    unittest.main()
