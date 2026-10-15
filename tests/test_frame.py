import unittest

from pyproj import Transformer
from shapely.geometry import box

from geofeat.frame import ASPECT, MIN_FRAME_M, Equirectangular, frame
from geofeat.model import Expect, Feature, FrameOptions, Part


def feature(**frame_options) -> Feature:
    return Feature(id="x", name="X", type="Plain", category="Regions & Rifts", tier=3, style="area",
                   geometry=[Part(layer="10m_land", select={"x": 1})], expect=Expect(bbox=(-180, -90, 180, 90)),
                   frame=FrameOptions(**frame_options))


def to_map(projection, lon: float, lat: float) -> tuple[float, float]:
    return Transformer.from_crs("EPSG:4326", projection.proj4_init, always_xy=True).transform(lon, lat)


class FrameTest(unittest.TestCase):
    def test_meridians_are_vertical_and_parallels_horizontal(self) -> None:
        f = frame(feature(), box(30, 55, 40, 65))
        for lon in (25, 35, 45):
            self.assertAlmostEqual(to_map(f.projection, lon, 50)[0], to_map(f.projection, lon, 70)[0], places=6)
        for lat in (50, 60):
            self.assertAlmostEqual(to_map(f.projection, 25, lat)[1], to_map(f.projection, 45, lat)[1], places=6)

    def test_small_feature_gets_the_minimum_frame(self) -> None:
        f = frame(feature(), box(10, 45, 10.1, 45.1))
        self.assertIsInstance(f.projection, Equirectangular)
        self.assertAlmostEqual(f.extent[1] - f.extent[0], MIN_FRAME_M, delta=1)

    def test_frame_is_true_to_scale_at_its_centre_parallel(self) -> None:
        f = frame(feature(), box(10, 60, 10.1, 60.1))
        self.assertAlmostEqual(f.projection.proj4_params["lat_ts"], 60.05, delta=0.1)

    def test_band_round_a_pole_spans_the_globe_and_stops_at_the_pole(self) -> None:
        f = frame(feature(), box(-180, 65, 180, 90).segmentize(1))
        x0, x1, _, y1 = f.extent
        self.assertAlmostEqual(x1 - x0, 2 * f.projection.x_limits[1], delta=1)
        self.assertLessEqual(y1, f.projection.y_limits[1] + 1)

    def test_highlight_wider_than_the_limit_goes_on_the_world_map(self) -> None:
        self.assertIsNone(frame(feature(), box(-100, -10, 40, 10)).extent)

    def test_fixed_centre_is_the_frame_centre(self) -> None:
        f = frame(feature(centre=(10, 50)), box(12, 51, 12.5, 51.5))
        x0, x1, y0, y1 = f.extent
        lon, lat = Transformer.from_crs(f.projection.proj4_init, "EPSG:4326", always_xy=True).transform((x0 + x1) / 2, (y0 + y1) / 2)
        self.assertAlmostEqual(lon, 10, delta=0.01)
        self.assertAlmostEqual(lat, 50, delta=0.01)
        self.assertAlmostEqual((x1 - x0) / (y1 - y0), ASPECT)

    def test_frame_across_180_is_continuous(self) -> None:
        f = frame(feature(), box(178, 60, 182, 62).intersection(box(-180, -90, 180, 90)).union(box(-180, 60, -178, 62)))
        x0, x1, _, _ = f.extent
        self.assertLess(x1 - x0, 5_000_000)




class PoliticalFrameTest(unittest.TestCase):
    """Country, territory and dispute subjects (spec.framing): ADR 0003's v2.1 amendment."""

    def frame(self, subject, neighbours=(), framing="neighbours"):
        from geofeat.spec import RenderSpec

        return frame(RenderSpec(style="area", country="subject", framing=framing), subject, neighbours)

    def width(self, f) -> float:
        return f.extent[1] - f.extent[0]

    def fill(self, f, subject) -> float:
        from geofeat.frame import project

        x0, y0, x1, y1 = project(subject, f.projection).bounds
        return max(x1 - x0, (y1 - y0) * ASPECT) / self.width(f)

    def test_mid_size_subject_fills_at_most_the_band_ceiling(self) -> None:
        from geofeat.frame import FILL_MAX

        germany = box(6, 47.3, 15, 55)
        f = self.frame(germany, (box(15, 49, 24, 55), box(-5, 42, 8, 51)))
        self.assertLessEqual(self.fill(f, germany), FILL_MAX + 0.01)
        self.assertIsNone(f.detail)

    def test_a_giant_neighbour_is_clamped_by_the_band_floor(self) -> None:
        from geofeat.frame import FILL_MIN

        nepal = box(80, 26.4, 88.2, 30.4)
        f = self.frame(nepal, (box(73, 18, 135, 53), box(68, 8, 97, 35)))
        self.assertGreaterEqual(self.fill(f, nepal), FILL_MIN - 0.01)

    def test_cap_holds_a_big_subject_with_big_neighbours(self) -> None:
        from geofeat.frame import MAX_FRAME_M

        mongolia = box(87.7, 41.6, 119.9, 52.1)
        f = self.frame(mongolia, (box(73, 18, 135, 53), box(27, 41, 180, 78)))
        self.assertAlmostEqual(self.width(f), MAX_FRAME_M, delta=1)
        self.assertEqual(f.capped, "cap")

    def test_small_subject_gets_a_regional_frame_and_a_detail_inset_without_the_locator(self) -> None:
        from geofeat.frame import POLITICAL_MIN_M

        andorra = box(1.4, 42.4, 1.8, 42.65)
        f = self.frame(andorra, (box(-9, 36, 3.3, 43.8), box(-5, 42.3, 8.2, 51.1)))
        self.assertAlmostEqual(self.width(f), POLITICAL_MIN_M, delta=1)
        self.assertIsNotNone(f.detail)
        self.assertFalse(f.inset)
        dx0, dx1, dy0, dy1 = f.detail
        self.assertLess(dx1 - dx0, self.width(f) / 4)

    def test_a_thin_subject_gets_a_detail_inset(self) -> None:
        gambia = box(-16.8, 13.2, -13.8, 13.55)  # 330 km long, under 40 km across
        self.assertIsNotNone(self.frame(gambia, (box(-17.5, 12.3, -11.4, 16.7),)).detail)

    def test_remote_subject_reaches_its_landmass_without_the_locator(self) -> None:
        nauru = box(166.9, -0.56, 166.96, -0.5)
        landmass = box(150, -6, 153, -3)
        f = self.frame(nauru, (landmass,), framing="remote")
        x0, x1, y0, y1 = f.extent
        from geofeat.frame import project

        self.assertTrue(box(x0, y0, x1, y1).intersects(project(landmass, f.projection)))
        self.assertFalse(f.inset)
        self.assertIsNotNone(f.detail)

    def test_remote_subject_too_far_from_land_keeps_the_locator(self) -> None:
        f = self.frame(box(-140.1, -25.1, -140.0, -25.0), (box(-75, -20, -70, -15),), framing="remote")
        self.assertEqual(f.capped, "remote")
        self.assertTrue(f.inset)


if __name__ == "__main__":
    unittest.main()
