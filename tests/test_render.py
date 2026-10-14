import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import geofeat.render as render
import geofeat.resolve as resolver
from geofeat.model import ROOT, Expect, Feature, Part
from geofeat.render import RENDERER, UndeclaredLayer, input_hash, only_layers
from geofeat.spec import RenderSpec


def area_feature(feature_type: str, layer: str = "10m_land") -> Feature:
    return Feature(id="x", name="X", type=feature_type, category="Regions & Rifts", tier=3, style="area",
                   geometry=[Part(layer=layer, select={"x": 1})], expect=Expect(bbox=(0, 0, 1, 1)))


class InputHashTest(unittest.TestCase):
    def test_retyping_into_or_out_of_a_land_family_re_renders(self) -> None:
        self.assertNotEqual(input_hash(area_feature("Plain")), input_hash(area_feature("Island")))

    def test_retyping_within_land_families_does_not(self) -> None:
        self.assertEqual(input_hash(area_feature("Plain")), input_hash(area_feature("Desert")))


class CacheKeyScopeTest(unittest.TestCase):
    """input_hash against a copy of the repo's renderer files and locks, edited one way at a time."""

    feature = area_feature("Plain", layer="10m_geography_regions_polys")

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.copies = 0

    def _hash(self, edit=lambda root: None) -> str:
        """The feature's hash with ROOT and LOCK pointing at a fresh copy, after `edit(copy_root)`."""
        self.copies += 1
        root = self.tmp / str(self.copies)
        for name in (*RENDERER, "model.py"):
            (root / "src/geofeat").mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / "src/geofeat" / name, root / "src/geofeat" / name)
        (root / "data").mkdir()
        shutil.copy(ROOT / "uv.lock", root / "uv.lock")
        shutil.copy(ROOT / "data/sources.lock", root / "data/sources.lock")
        edit(root)
        with mock.patch.object(render, "ROOT", root), mock.patch.object(render, "LOCK", root / "data/sources.lock"):
            return input_hash(self.feature)

    @staticmethod
    def _edit_lock(root: Path, change) -> None:
        path = root / "data/sources.lock"
        path.write_text(json.dumps(change(json.loads(path.read_text()))))

    @staticmethod
    def _append(root: Path, name: str, text: str) -> None:
        path = root / name
        path.write_text(path.read_text() + text)

    def test_copy_matches_the_repo(self) -> None:
        self.assertEqual(self._hash(), input_hash(self.feature))

    def test_editing_model_py_keeps_the_key(self) -> None:
        self.assertEqual(self._hash(), self._hash(lambda r: self._append(r, "src/geofeat/model.py", "\n# edit\n")))

    def test_editing_renderer_code_or_uv_lock_changes_it(self) -> None:
        base = self._hash()
        for name in (*(f"src/geofeat/{n}" for n in RENDERER), "uv.lock"):
            with self.subTest(name):
                self.assertNotEqual(base, self._hash(lambda r: self._append(r, name, "\n# edit\n")))

    def test_an_unrelated_lock_entry_keeps_the_key(self) -> None:
        new = {"repo": "nvkelso/natural-earth-vector", "commit": "0" * 40, "path": "geojson/ne_10m_populated_places.geojson",
               "sha256": "0" * 64, "blob": "0" * 40}
        self.assertEqual(self._hash(), self._hash(lambda r: self._edit_lock(r, lambda lock: [*lock, new])))

    def test_changing_an_unused_layers_entry_keeps_the_key(self) -> None:
        self.assertEqual(self._hash(), self._hash(lambda r: self._edit_lock(r, lambda lock: [
            {**e, "sha256": "0" * 64} if e["path"].endswith("ne_10m_admin_0_countries.geojson") else e for e in lock])))

    def test_a_relock_with_unchanged_bytes_keeps_the_key(self) -> None:
        self.assertEqual(self._hash(), self._hash(lambda r: self._edit_lock(r, lambda lock: [
            {**e, "commit": "1" * 40} for e in lock])))

    def test_changing_a_used_layers_entry_changes_it(self) -> None:
        for used in ("ne_10m_geography_regions_polys.geojson", "ne_50m_ocean.geojson", "GRAY_50M_SR.tif"):
            with self.subTest(used):
                self.assertNotEqual(self._hash(), self._hash(lambda r: self._edit_lock(r, lambda lock: [
                    {**e, "sha256": "0" * 64} if e["path"].endswith("/" + used) else e for e in lock])))


class LayerGuardTest(unittest.TestCase):
    def test_an_undeclared_layer_raises_during_a_render(self) -> None:
        spec = RenderSpec.from_feature(area_feature("Plain"))
        with only_layers(spec.layers()), self.assertRaises(UndeclaredLayer):
            resolver.layer("50m_admin_1_states_provinces_lines")

    def test_resolving_a_feature_inside_the_guard_is_checked(self) -> None:
        with only_layers(frozenset()), self.assertRaises(UndeclaredLayer):
            resolver.resolve(area_feature("Plain"))

    def test_a_module_that_imported_the_loader_by_name_is_guarded_too(self) -> None:
        import geofeat.check as check
        with only_layers(frozenset()), self.assertRaises(UndeclaredLayer):
            check.layer("10m_land")
        self.assertIs(check.layer, resolver.layer)

    def test_the_loader_is_restored_afterwards(self) -> None:
        load = resolver.layer
        with self.assertRaises(UndeclaredLayer), only_layers(frozenset()):
            resolver.layer("10m_land")
        self.assertIs(resolver.layer, load)


if __name__ == "__main__":
    unittest.main()
