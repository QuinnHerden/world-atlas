import unittest

from pyproj import Geod
from shapely.geometry import box

import geofeat.render as render
from geofeat.frame import CLOSE_DOT_FRAME_M, Equirectangular, frame
from geofeat.jobs import CLOSE_DOT_KM, close_dots
from geofeat.card import match_keys
from geofeat.spec import RenderSpec

GEOD = Geod(ellps="WGS84")


def east_of(lon: float, lat: float, km: float) -> tuple[float, float]:
    x, y, _ = GEOD.fwd(lon, lat, 90, km * 1000)
    return x, y


class CloseDotsTest(unittest.TestCase):
    def test_dots_within_the_limit_are_close_both_ways(self) -> None:
        kyoto = (135.77, 35.01)
        dots = {"city:kyoto": kyoto, "city:osaka": east_of(*kyoto, -43), "capital:japan": east_of(*kyoto, 370)}
        close = close_dots(dots)
        self.assertEqual(set(close), {"city:kyoto", "city:osaka"})
        (other, km), = close["city:kyoto"]
        self.assertEqual(other, "city:osaka")
        self.assertAlmostEqual(km, 43, delta=0.5)

    def test_the_limit_is_inclusive_and_measured_on_the_ellipsoid(self) -> None:
        a = (55.27, 25.2)
        self.assertTrue(close_dots({"a": a, "b": east_of(*a, CLOSE_DOT_KM - 0.5)}))
        self.assertFalse(close_dots({"a": a, "b": east_of(*a, CLOSE_DOT_KM + 0.5)}))

    def test_across_180(self) -> None:
        self.assertEqual(set(close_dots({"a": (179.9, -17.0), "b": (-179.9, -17.0)})), {"a", "b"})

    def test_no_dots(self) -> None:
        self.assertEqual(close_dots({}), {})


class PoliticalFrameTest(unittest.TestCase):
    def test_close_dot_frame_is_centred_on_the_dot_and_has_the_inset(self) -> None:
        spec = RenderSpec(style="area", country="context", dot=(135.77, 35.01), close_dot=True)
        f = frame(spec, box(129, 30, 146, 46))
        x0, x1, y0, y1 = f.extent
        self.assertAlmostEqual(x1 - x0, CLOSE_DOT_FRAME_M)
        self.assertAlmostEqual(x0 + x1, 0)
        self.assertEqual(f.projection.proj4_params["lon_0"], 135.77)
        self.assertTrue(f.inset)

    def test_close_dot_frame_stops_at_the_pole(self) -> None:
        f = frame(RenderSpec(style="area", dot=(15.6, 89.5), close_dot=True), box(10, 77, 30, 81))
        self.assertLessEqual(f.extent[3], f.projection.y_limits[1] + 1e-6)

    def test_world_spec_goes_on_the_world_map_however_small(self) -> None:
        f = frame(RenderSpec(style="area", world=True), box(10, 40, 30, 55))
        self.assertIsNone(f.extent)
        self.assertIsInstance(f.projection, Equirectangular)


class RecognisedBordersTest(unittest.TestCase):
    """The basemap's borders round Crimea, Western Sahara and Nagorno-Karabakh (ADR 0008)."""

    def test_composition_lines_are_dashed_not_solid(self) -> None:
        for res in ("10m", "50m"):
            solid, dashed = render._borders(res, (33.0, 35.5, 45.5, 46.5))  # Perekop, Crimea's isthmus
            with self.subTest(res):
                perekop = box(33.5, 45.7, 35.1, 46.3)
                self.assertGreater(dashed.intersection(perekop).length, 1)
                self.assertLess(solid.intersection(perekop).length, 0.01)

    def test_disputed_lines_are_dashed_but_not_the_stale_ones(self) -> None:
        _, dashed = render._borders("10m", (-17.5, -8.0, 27.0, 28.5))  # Western Sahara's northern edge
        self.assertGreater(dashed.length, 3)
        _, karabakh = render._borders("10m", (45.5, 48.0, 39.0, 40.5))
        self.assertEqual(karabakh.intersection(box(46.0, 39.2, 47.2, 40.4)).length, 0)
        _, donbas = render._borders("10m", (37.0, 40.5, 47.0, 49.0))
        self.assertEqual(donbas.length, 0)

    def test_every_listed_id_is_in_its_pinned_layer(self) -> None:
        """Natural Earth renumbers lines between releases; a missing id would silently draw solid."""
        for res, ids in render.DASHED_LAND.items():
            with self.subTest(res):
                self.assertLessEqual(ids, set(render.layer(f"{res}_admin_0_boundary_lines_land")["ne_id"]))
        self.assertLessEqual(render.STALE_DISPUTED_IDS, set(render.layer("10m_admin_0_boundary_lines_disputed_areas")["ne_id"]))

    def test_leases_and_overlays_are_dropped(self) -> None:
        solid, dashed = render._borders("10m", (62.0, 65.5, 45.0, 47.0))  # Baikonur
        self.assertEqual(solid.union(dashed).intersection(box(63.0, 45.4, 64.3, 46.4)).length, 0)


class MatchKeysTest(unittest.TestCase):
    keys = ["capital:france", "city:kyoto", "city:osaka", "country:france", "feature:nile"]

    def test_patterns(self) -> None:
        self.assertEqual(match_keys(["city:*"], self.keys), ["city:kyoto", "city:osaka"])
        self.assertEqual(match_keys(["*:france"], self.keys), ["capital:france", "country:france"])
        self.assertEqual(match_keys(["nile", "country:france", "*:france"], self.keys),
                         ["feature:nile", "country:france", "capital:france"])
        with self.assertRaises(ValueError):
            match_keys(["city:kyoto", "country:nowhere"], self.keys)


if __name__ == "__main__":
    unittest.main()


class FilteredRenderTest(unittest.TestCase):
    """`jobs [patterns]` renders only the matched cards and keeps every other map and media.json entry."""

    def test_only_adds(self) -> None:
        import json
        import tempfile
        from pathlib import Path
        from unittest import mock

        import geofeat.card as card
        import geofeat.jobs as jobs
        from geofeat.jobs import RenderJob

        with tempfile.TemporaryDirectory() as tmp:
            deck, build = Path(tmp, "deck"), Path(tmp, "build")
            deck.mkdir()
            build.mkdir()
            (deck / "old.png").write_bytes(b"x")
            media = build / "media.json"
            media.write_text(json.dumps({"country:alpha": "old.png"}))
            fake = {"country:alpha": RenderJob(RenderSpec(style="area"), box(0, 0, 1, 1)),
                    "country:beta": RenderJob(RenderSpec(style="area"), box(2, 2, 3, 3))}
            with mock.patch.object(jobs, "DECK", deck), mock.patch.object(jobs, "BUILD", build), \
                    mock.patch.object(jobs, "CACHE", build / "render-cache.json"), \
                    mock.patch.object(jobs, "MEDIA_INDEX", media), mock.patch.object(card, "MEDIA_INDEX", media), \
                    mock.patch.object(jobs, "card_jobs", return_value=fake), \
                    mock.patch.object(jobs, "_render_to_file", side_effect=lambda job: (deck / "new.png").write_bytes(b"y") and "new.png"):
                jobs.render_cards([], only=["country:beta"])
            self.assertEqual(json.loads(media.read_text()), {"country:alpha": "old.png", "country:beta": "new.png"})
            self.assertTrue((deck / "old.png").exists())
