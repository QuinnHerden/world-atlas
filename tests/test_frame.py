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


if __name__ == "__main__":
    unittest.main()
