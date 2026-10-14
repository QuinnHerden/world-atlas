"""tools/freeze_walks.py: writing approved walks into data/curriculum.yaml."""

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ruamel.yaml import YAML

from geofeat.adjacency import Edge
from geofeat.countries_ne import state_ids
from geofeat.curriculum import CURRICULUM, Curriculum
from geofeat.order.engine import walks

_spec = importlib.util.spec_from_file_location("freeze_walks", Path(__file__).parents[1] / "tools/freeze_walks.py")
freeze_walks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(freeze_walks)

WEST = ["portugal", "spain", "france", "belgium", "luxembourg", "netherlands", "united-kingdom", "ireland"]
CARIBBEAN = ["trinidad-and-tobago", "grenada", "saint-vincent-and-the-grenadines", "barbados", "saint-lucia",
             "dominica", "antigua-and-barbuda", "saint-kitts-and-nevis", "dominican-republic", "haiti", "jamaica",
             "cuba", "bahamas"]


def parse(text: str) -> Curriculum:
    return Curriculum.model_validate(YAML(typ="safe").load(text))


def without_walks(text: str) -> str:
    lines, out, skipping = text.splitlines(keepends=True), [], False
    for line in lines:
        if line.startswith("    walk: ["):
            skipping = True
        elif not (skipping and line.startswith("           ")):
            skipping = False
        if not skipping:
            out.append(line)
    return "".join(out)


TEXT = without_walks(CURRICULUM.read_text())  # the real file, as before any walk was frozen


class Freeze(unittest.TestCase):
    def test_writes_only_the_chosen_region(self):
        text = freeze_walks.freeze(TEXT, {"western-europe": WEST})
        regions = {r.slug: r for r in parse(text).regions}
        self.assertEqual(regions["western-europe"].walk, WEST)
        self.assertTrue(all(not r.walk for s, r in regions.items() if s != "western-europe"))
        self.assertEqual(without_walks(text), TEXT)
        self.assertEqual(parse(text).check(state_ids()), [])

    def test_wraps_long_walks_and_keeps_the_layout(self):
        text = freeze_walks.freeze(TEXT, {"caribbean": CARIBBEAN, "western-europe": WEST})
        self.assertTrue(all(len(line) <= freeze_walks.WIDTH for line in text.splitlines() if "walk" in line))
        self.assertEqual({r.slug: r.walk for r in parse(text).regions if r.walk},
                         {"caribbean": CARIBBEAN, "western-europe": WEST})
        self.assertEqual(without_walks(text), TEXT)

    def test_refreezing_replaces_the_walk(self):
        once = freeze_walks.freeze(TEXT, {"caribbean": CARIBBEAN})
        changed = CARIBBEAN[:1] + list(reversed(CARIBBEAN[1:]))
        twice = freeze_walks.freeze(once, {"caribbean": changed})
        self.assertEqual(twice.count("    walk: ["), 1)
        self.assertEqual(next(r.walk for r in parse(twice).regions if r.slug == "caribbean"), changed)
        self.assertEqual(freeze_walks.freeze(once, {"caribbean": CARIBBEAN}), once)

    def test_the_engine_reads_a_frozen_walk(self):
        curriculum = parse(freeze_walks.freeze(TEXT, {"western-europe": WEST}))
        walk = walks(curriculum, {})[1]
        self.assertTrue(walk.frozen)
        self.assertEqual(walk.nodes, tuple(WEST))
        self.assertFalse(walks(curriculum, {})[2].frozen)

    def test_unknown_region(self):
        with self.assertRaises(ValueError):
            freeze_walks.freeze(TEXT, {"atlantis": ["x"]})
        with self.assertRaises(ValueError):
            freeze_walks.select(parse(TEXT), ["atlantis"])
        self.assertEqual(freeze_walks.select(parse(TEXT), ["1", "western-europe", "21"]), ["western-europe", "caribbean"])


class Main(unittest.TestCase):
    def run_main(self, argv: list[str], text: str = TEXT) -> str:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "curriculum.yaml"
            path.write_text(text)
            edges = [Edge("portugal", "spain", "land"), Edge("france", "spain", "land")]
            with mock.patch.object(freeze_walks.adjacency, "graph", return_value=edges), \
                    contextlib.redirect_stdout(io.StringIO()):
                freeze_walks.main(argv, path)
            return path.read_text()

    def test_one_region(self):
        text = self.run_main(["western-europe"])
        curriculum = parse(text)
        walked = [r for r in curriculum.regions if r.walk]
        self.assertEqual([r.slug for r in walked], ["western-europe"])
        self.assertEqual(walked[0].walk[:3], ["portugal", "spain", "france"])

    def test_all_regions_and_idempotent(self):
        text = self.run_main(["--all"])
        self.assertTrue(all(r.walk for r in parse(text).regions))
        self.assertEqual(self.run_main(["--all"], text), text)

    def test_needs_a_choice(self):
        for argv in ([], ["--all", "1"]):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                self.run_main(argv)


if __name__ == "__main__":
    unittest.main()
