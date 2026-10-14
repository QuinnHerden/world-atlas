import unittest
from unittest import mock

from pydantic import ValidationError
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

from geofeat.model import Expect, Feature, Part, load_features
from geofeat.regions import ORIENTATION, REGIONS, continent_geometry, derive, disjoint, override_errors

# A synthetic ring on the equator: regions 1 and 3 face each other across a 1° strait, region 2 lies north of both.
WORLD = {1: box(0, 0, 10, 10), 2: box(0, 12, 25, 20), 3: box(11, 0, 25, 10)}


def feature(type: str, id: str = "x", style: str = "area", **extra) -> Feature:
    return Feature(id=id, name=id, type=type, category="Regions & Rifts", tier=1, style=style,
                   geometry=[Part(file="x.geojson")], expect=Expect(bbox=(-180, -90, 180, 90)), **extra)


class DeriveTest(unittest.TestCase):
    def test_oceans_and_planetary_winds_go_to_orientation(self) -> None:
        self.assertEqual(derive(feature("Ocean"), box(-10, -10, 0, 0), WORLD).region, ORIENTATION)
        winds = feature("Wind system", id="westerlies", style="flow-wind")
        self.assertEqual(derive(winds, LineString([(0, 11), (25, 11)]), WORLD).region, ORIENTATION)
        self.assertEqual(derive(feature("Continent"), box(0, 0, 25, 20), WORLD).region, ORIENTATION)

    def test_strait_goes_to_the_later_shore(self) -> None:
        assignment = derive(feature("Strait", style="strait"), box(10, 0, 11, 10), WORLD)
        self.assertEqual((assignment.region, assignment.rule), (3, "shore"))
        self.assertAlmostEqual(assignment.share, 0.5, places=2)

    def test_a_region_barely_touching_a_strait_is_not_a_shore(self) -> None:
        world = WORLD | {4: box(10, 10.4, 11, 11)}  # a speck just off the strait's mouth
        self.assertEqual(derive(feature("Strait", style="strait"), box(10, 0, 11, 10), world).region, 3)

    def test_sea_route_goes_to_the_region_with_most_shore(self) -> None:
        route = LineString([(0, -0.3), (12, -0.3)])
        self.assertEqual(derive(feature("Sea route", style="line"), route, WORLD).region, 1)

    def test_climate_goes_to_the_land_it_covers(self) -> None:
        band = box(8, 5, 25, 15)
        assignment = derive(feature("Climate belt", style="band"), band, WORLD)
        self.assertEqual((assignment.region, assignment.rule), (3, "climate"))

    def test_area_goes_to_the_largest_share(self) -> None:
        assignment = derive(feature("Plain"), box(8, 2, 14, 8), WORLD)
        self.assertEqual((assignment.region, assignment.measure), (3, "area"))
        self.assertAlmostEqual(assignment.share, 0.5, places=2)
        self.assertAlmostEqual(assignment.shares[1], 2 / 6, places=2)

    def test_uncovered_water_goes_by_shoreline(self) -> None:
        assignment = derive(feature("Sea"), box(0, -5, 25, 0), WORLD)
        self.assertEqual((assignment.region, assignment.measure), (3, "shoreline"))
        self.assertGreater(assignment.share, 0.5)

    def test_line_goes_by_length(self) -> None:
        river = LineString([(9, 5), (20, 5)])
        assignment = derive(feature("River", style="line"), river, WORLD)
        self.assertEqual((assignment.region, assignment.measure), (3, "length"))

    def test_point_goes_to_the_nearest_region(self) -> None:
        assignment = derive(feature("Plain", style="point"), Point(10.4, 5), WORLD)
        self.assertEqual((assignment.region, assignment.measure), (1, "point"))

    def test_override_keeps_the_derived_region(self) -> None:
        plain = feature("Plain", region=1, region_reason="the plan puts it in region 1")
        assignment = derive(plain, box(8, 2, 14, 8), WORLD)
        self.assertEqual((assignment.region, assignment.derived, assignment.rule), (1, 3, "override"))


class OverrideFieldTest(unittest.TestCase):
    def test_every_override_is_in_the_ring(self) -> None:
        self.assertEqual(override_errors(load_features()), [])
        with mock.patch.dict(REGIONS, clear=True):
            plain = feature("Plain", region=3, region_reason="a region the ring lacks")
            self.assertEqual(override_errors([plain]), ["x: region 3 is not in the ring"])
            with self.assertRaisesRegex(ValueError, "not in the ring"):
                derive(plain, box(0, 0, 1, 1), WORLD)

    def test_region_needs_a_reason(self) -> None:
        with self.assertRaises(ValidationError):
            feature("Plain", region=3)
        with self.assertRaises(ValidationError):
            feature("Plain", region_reason="a reason with no region")

    def test_region_is_in_the_ring(self) -> None:
        for region in (0, 22):
            with self.assertRaises(ValidationError):
                feature("Plain", region=region, region_reason="out of the ring")

    def test_anchor_is_a_card_key_with_a_reason(self) -> None:
        feature("Sea", anchor="country:egypt", anchor_reason="placed after Egypt's card")
        with self.assertRaises(ValidationError):
            feature("Sea", anchor="egypt", anchor_reason="placed after Egypt's card")
        with self.assertRaises(ValidationError):
            feature("Sea", anchor="country:egypt")

    def test_continent_is_its_own_family(self) -> None:
        self.assertEqual(feature("Continent").family, "continent")


class ContinentTest(unittest.TestCase):
    # NE's landmasses overlap at 6–6.5°E; Russia straddles the line and has an island off every landmass.
    landmasses = {"Europe": box(0, 0, 6.5, 10), "Asia": box(6, 0, 20, 10)}
    island = box(13, 11, 14, 12)
    countries = {"germany": box(0, 0, 4, 10), "russia": unary_union([box(4, 0, 12, 10), island]),
                 "china": box(12, 0, 20, 10), "greenland": box(5, 10.5, 6, 11)}
    members = {"germany": "Europe", "russia": ("Europe", "Asia"), "china": "Asia", "greenland": "Europe"}

    def test_overlap_goes_to_the_smaller_continent(self) -> None:
        lands = disjoint(self.landmasses)
        self.assertTrue(lands["Europe"].equals(box(0, 0, 6.5, 10)))
        self.assertTrue(lands["Asia"].equals(box(6.5, 0, 20, 10)))

    def test_continent_is_the_union_of_its_countries_split_along_the_line(self) -> None:
        europe = continent_geometry("Europe", self.members, self.countries, self.landmasses)
        asia = continent_geometry("Asia", self.members, self.countries, self.landmasses)
        self.assertTrue(europe.equals(unary_union([box(0, 0, 6.5, 10), self.countries["greenland"]])))
        self.assertTrue(asia.equals(unary_union([box(6.5, 0, 20, 10), self.island])))
        self.assertAlmostEqual(europe.intersection(asia).area, 0)
        self.assertTrue(unary_union([europe, asia]).equals(unary_union(list(self.countries.values()))))

    def test_a_country_off_the_landmasses_stays_whole(self) -> None:
        europe = continent_geometry("Europe", self.members, self.countries, self.landmasses)
        self.assertTrue(europe.contains(self.countries["greenland"]))


if __name__ == "__main__":
    unittest.main()
