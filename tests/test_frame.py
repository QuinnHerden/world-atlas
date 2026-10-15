import unittest

from pyproj import Transformer
from shapely.geometry import MultiPoint, Point, box

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
    """Country, territory and dispute subjects (spec.framing) on their curriculum region's frame."""

    REGION = MultiPoint([(14, 42), (30, 42), (14, 52), (30, 52)])  # member hull points, a Central Europe-sized box

    def frame(self, subject, region=REGION, **spec):
        from geofeat.spec import RenderSpec

        return frame(RenderSpec(style="area", **({"country": "subject", "framing": "region"} | spec)), subject, region)

    def test_cards_in_a_region_share_its_frame(self) -> None:
        a, b = self.frame(box(19, 46, 22, 48)), self.frame(box(24, 44, 27, 47))
        self.assertEqual(a.extent, b.extent)
        self.assertEqual(a.projection.proj4_params, b.projection.proj4_params)

    def test_a_subject_outside_the_region_frame_moves_its_own_frame(self) -> None:
        shared, outlier = self.frame(box(19, 46, 22, 48)), self.frame(box(44, 36, 46, 38))
        self.assertNotEqual(shared.extent, outlier.extent)
        from geofeat.frame import project

        x0, y0, x1, y1 = project(box(44, 36, 46, 38), outlier.projection).bounds
        fx0, fx1, fy0, fy1 = outlier.extent
        self.assertTrue(fx0 < x0 and x1 < fx1 and fy0 < y0 and y1 < fy1)

    def test_a_giant_keeps_its_v2_frame(self) -> None:
        from geofeat.spec import RenderSpec

        giant = box(-74, -34, -35, 5)  # Brazil-sized
        v2 = frame(RenderSpec(style="area", country="subject"), giant)
        self.assertEqual(self.frame(giant).extent, v2.extent)

    def test_small_subject_gets_a_detail_inset_without_the_locator(self) -> None:
        f = self.frame(box(20.0, 42.2, 21.8, 43.2))  # Kosovo-sized
        self.assertIsNotNone(f.detail)
        self.assertFalse(f.inset)

    def test_a_mid_size_subject_keeps_the_locator_and_no_inset(self) -> None:
        f = self.frame(box(16, 45.7, 22.9, 48.6))  # Hungary-sized
        self.assertIsNone(f.detail)
        self.assertTrue(f.inset)

    def test_close_dot_city_gets_a_detail_inset_round_its_dot(self) -> None:
        from geofeat.frame import CLOSE_DOT_DETAIL_M, DETAIL_SHARE, DETAIL_ZOOM, project

        f = self.frame(box(19, 46, 22, 48), country="context", dot=(20.0, 47.0), close_dot=True)
        dx0, dx1, dy0, dy1 = f.detail
        width = f.extent[1] - f.extent[0]
        self.assertAlmostEqual(dx1 - dx0, min(CLOSE_DOT_DETAIL_M, width * DETAIL_SHARE / DETAIL_ZOOM))
        x, y = project(Point(20.0, 47.0), f.projection).coords[0]
        self.assertTrue(dx0 < x < dx1 and dy0 < y < dy1)

    def test_pacific_sub_frames_keep_the_locator(self) -> None:
        f = self.frame(box(20.0, 42.2, 21.8, 43.2), framing="pacific")
        self.assertTrue(f.inset)


class FitAxisTest(unittest.TestCase):
    def test_moves_to_hold_the_subject_or_widens(self) -> None:
        from geofeat.frame import _fit_axis

        self.assertEqual(_fit_axis(0, 10, 2, 8, 1), (0, 10))  # already holds it
        self.assertEqual(_fit_axis(0, 10, 8, 12, 1), (3, 10))  # moved right
        self.assertEqual(_fit_axis(0, 10, -4, 1, 1), (-5, 10))  # moved left
        self.assertEqual(_fit_axis(0, 10, 0, 12, 1), (-1, 14))  # widened


class PacificFramesTest(unittest.TestCase):
    def test_every_oceania_entry_is_on_exactly_one_sub_frame(self) -> None:
        from ruamel.yaml import YAML

        from geofeat.framing import OCEANIA, PACIFIC_FRAMES
        from geofeat.model import ROOT

        regions = YAML(typ="safe").load(ROOT / "data/curriculum.yaml")["regions"]
        oceania = next(r for r in regions if r["number"] == OCEANIA)
        ids = [*oceania["countries"], *oceania.get("territories", {}), *oceania.get("disputes", {})]
        for id in ids:
            with self.subTest(id):
                self.assertEqual(sum(id in cards for _, cards in PACIFIC_FRAMES.values()), 1)


if __name__ == "__main__":
    unittest.main()
