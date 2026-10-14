import ast
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from shapely.geometry import LineString, MultiPolygon, Polygon, box

import geofeat.jobs as jobs
from geofeat.model import ROOT, FrameOptions
from geofeat.jobs import RENDERER, RenderJob, geometry_hash
from geofeat.spec import BASEMAP_LAYERS, RenderSpec

SPEC = RenderSpec(style="area")
SHAPE = box(10, 40, 12, 42)
JOB = RenderJob(SPEC, SHAPE)


class GeometryHashTest(unittest.TestCase):
    def test_float_noise_vertex_order_and_part_order_dont_count(self) -> None:
        shifted = Polygon([(12, 42), (10, 42), (10, 40), (12 + 1e-11, 40), (12, 42)])  # other start, other winding
        self.assertEqual(geometry_hash(SHAPE), geometry_hash(shifted))
        a, b = box(0, 0, 1, 1), box(5, 5, 6, 6)
        self.assertEqual(geometry_hash(MultiPolygon([a, b])), geometry_hash(MultiPolygon([b, a])))

    def test_negative_zero_is_zero(self) -> None:
        self.assertEqual(geometry_hash(LineString([(-1e-12, 0), (1, 1)])), geometry_hash(LineString([(0, 0), (1, 1)])))

    def test_a_directed_line_keeps_its_direction(self) -> None:
        east, west = LineString([(0, 0), (10, 0)]), LineString([(10, 0), (0, 0)])
        self.assertEqual(geometry_hash(east), geometry_hash(west))
        self.assertNotEqual(geometry_hash(east, directed=True), geometry_hash(west, directed=True))

    def test_a_real_change_does(self) -> None:
        self.assertNotEqual(geometry_hash(SHAPE), geometry_hash(box(10, 40, 12, 42.001)))


class KeyTest(unittest.TestCase):
    def test_re_resolving_to_identical_geometry_keeps_the_key(self) -> None:
        self.assertEqual(JOB.key(), RenderJob(RenderSpec(style="area"), box(10, 40, 12, 42)).key())

    def test_geometry_changes_it(self) -> None:
        self.assertNotEqual(JOB.key(), RenderJob(SPEC, box(10, 40, 12, 43)).key())

    def test_every_visual_field_changes_it(self) -> None:
        changes = {
            "style": "band", "fill_alpha": 0.3, "close_up_borders": True, "country": "subject", "dot": (11.0, 41.0),
            "outline": "dashed", "frame": FrameOptions(min_span_km=4000),
        }
        self.assertEqual(set(changes), set(RenderSpec.model_fields), "a new RenderSpec field needs a case here")
        for field, value in changes.items():
            with self.subTest(field):
                self.assertNotEqual(JOB.key(), RenderJob(SPEC.model_copy(update={field: value}), SHAPE).key())
        for options in (FrameOptions(centre=(11, 41)), FrameOptions(admin1=True)):
            with self.subTest(options):
                self.assertNotEqual(JOB.key(), RenderJob(RenderSpec(style="area", frame=options), SHAPE).key())

    def test_reversing_a_flow_line_changes_it(self) -> None:
        current = RenderSpec(style="flow-current")
        east, west = LineString([(0, 0), (10, 0)]), LineString([(10, 0), (0, 0)])
        self.assertNotEqual(RenderJob(current, east).key(), RenderJob(current, west).key())

    def test_context_and_former_count_by_shape(self) -> None:
        river = LineString([(10, 39), (11, 43)])
        with_river = RenderJob(SPEC, SHAPE, context=(river,))
        self.assertNotEqual(JOB.key(), with_river.key())
        self.assertNotEqual(with_river.key(), RenderJob(SPEC, SHAPE, context=(LineString([(10, 39), (11, 44)]),)).key())
        self.assertNotEqual(JOB.key(), RenderJob(SPEC, SHAPE, former=SHAPE.boundary).key())
        self.assertNotEqual(RenderJob(SPEC, SHAPE, context=(SHAPE.boundary,)).key(), RenderJob(SPEC, SHAPE, former=SHAPE.boundary).key())


class KeyScopeTest(unittest.TestCase):
    """The key against a copy of the repo's renderer files and locks, edited one way at a time."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.copies = 0

    def _key(self, edit=lambda root: None) -> str:
        """JOB's key with ROOT and LOCK pointing at a fresh copy, after `edit(copy_root)`."""
        self.copies += 1
        root = self.tmp / str(self.copies)
        (root / "src/geofeat").mkdir(parents=True)
        for name in (*RENDERER, "model.py", "resolve.py", "jobs.py"):
            shutil.copy(ROOT / "src/geofeat" / name, root / "src/geofeat" / name)
        (root / "data").mkdir()
        shutil.copy(ROOT / "uv.lock", root / "uv.lock")
        shutil.copy(ROOT / "data/sources.lock", root / "data/sources.lock")
        edit(root)
        with mock.patch.object(jobs, "ROOT", root), mock.patch.object(jobs, "LOCK", root / "data/sources.lock"):
            return JOB.key()

    @staticmethod
    def _edit_lock(root: Path, change) -> None:
        path = root / "data/sources.lock"
        path.write_text(json.dumps(change(json.loads(path.read_text()))))

    @staticmethod
    def _append(root: Path, name: str) -> None:
        path = root / name
        path.write_text(path.read_text() + "\n# edit\n")

    def _resha(self, file: str):
        return lambda r: self._edit_lock(r, lambda lock: [
            {**e, "sha256": "0" * 64} if Path(e["path"]).name == file else e for e in lock])

    def test_copy_matches_the_repo(self) -> None:
        self.assertEqual(self._key(), JOB.key())

    def test_editing_model_resolve_or_jobs_keeps_the_key(self) -> None:
        base = self._key()
        for name in ("model.py", "resolve.py", "jobs.py"):
            with self.subTest(name):
                self.assertEqual(base, self._key(lambda r: self._append(r, f"src/geofeat/{name}")))

    def test_editing_renderer_code_or_uv_lock_changes_it(self) -> None:
        base = self._key()
        for name in (*(f"src/geofeat/{n}" for n in RENDERER), "uv.lock"):
            with self.subTest(name):
                self.assertNotEqual(base, self._key(lambda r: self._append(r, name)))

    def test_an_unrelated_lock_entry_keeps_the_key(self) -> None:
        new = {"repo": "nvkelso/natural-earth-vector", "commit": "0" * 40, "path": "geojson/ne_10m_populated_places.geojson",
               "sha256": "0" * 64, "blob": "0" * 40}
        self.assertEqual(self._key(), self._key(lambda r: self._edit_lock(r, lambda lock: [*lock, new])))

    def test_a_selector_only_layers_entry_keeps_the_key(self) -> None:
        self.assertEqual(self._key(), self._key(self._resha("ne_10m_geography_regions_polys.geojson")))

    def test_a_relock_with_unchanged_bytes_keeps_the_key(self) -> None:
        self.assertEqual(self._key(), self._key(lambda r: self._edit_lock(r, lambda lock: [
            {**e, "commit": "1" * 40} for e in lock])))

    def test_a_basemap_layers_sha_changes_it(self) -> None:
        for file in (*(f"ne_{name}.geojson" for name in sorted(BASEMAP_LAYERS)), "GRAY_50M_SR.tif"):
            with self.subTest(file):
                self.assertNotEqual(self._key(), self._key(self._resha(file)))


class BasemapDeclaredTest(unittest.TestCase):
    def test_render_reads_only_basemap_layers(self) -> None:
        """Every layer() call in the hashed modules names a BASEMAP_LAYERS layer, at either scale, so its pin is in
        the key; and they don't reach the resolver, whose output is hashed as geometry, not its code."""
        names = []
        for node in (n for name in RENDERER for n in ast.walk(ast.parse((ROOT / "src/geofeat" / name).read_text()))):
            if isinstance(node, ast.ImportFrom):
                self.assertNotEqual(node.module, "geofeat.resolve")
            func = getattr(node, "func", None)
            if isinstance(node, ast.Call) and (getattr(func, "id", None) or getattr(func, "attr", None)) == "layer":
                arg = node.args[0]
                if isinstance(arg, ast.Constant):
                    names.append(arg.value)
                else:
                    self.assertIsInstance(arg, ast.JoinedStr, ast.unparse(arg))
                    template = "".join(v.value if isinstance(v, ast.Constant) else "{}" for v in arg.values)
                    names += [template.format(res) for res in ("10m", "50m")]
        self.assertTrue(names)
        self.assertLessEqual(set(names), BASEMAP_LAYERS)


if __name__ == "__main__":
    unittest.main()
