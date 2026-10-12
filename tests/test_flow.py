import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from shapely.geometry import LineString

import geofeat.resolve as resolve
from geofeat.model import Expect, Feature, Part
from geofeat.resolve import combine, flow_lines


class FlowLinesTest(unittest.TestCase):
    def test_crossing_lines_stay_two(self) -> None:
        lines = combine([LineString([(0, 0), (2, 2)]), LineString([(0, 2), (2, 0)])])
        self.assertEqual(len(flow_lines(lines)), 2)

    def test_crossing_lines_from_file_stay_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            collection = {"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"source": "test"},
                 "geometry": {"type": "LineString", "coordinates": coords}}
                for coords in ([[0, 0], [2, 2]], [[0, 2], [2, 0]])
            ]}
            (Path(tmp) / "x.geojson").write_text(json.dumps(collection))
            with mock.patch.object(resolve, "GEOMETRY", Path(tmp)):
                self.assertEqual(len(flow_lines(resolve._custom("x.geojson"))), 2)

    def test_crossing_file_parts_of_a_feature_stay_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for name, coords in (("a.geojson", [[0, 0], [2, 2]]), ("b.geojson", [[0, 2], [2, 0]])):
                (Path(tmp) / name).write_text(json.dumps({"type": "FeatureCollection", "features": [
                    {"type": "Feature", "properties": {"source": "test"}, "geometry": {"type": "LineString", "coordinates": coords}}
                ]}))
            feature = Feature(id="x", name="X", type="Ocean current", category="Climate Systems", tier=3, style="flow-current",
                              geometry=[Part(file="a.geojson"), Part(file="b.geojson")], expect=Expect(bbox=(0, 0, 2, 2)))
            with mock.patch.object(resolve, "GEOMETRY", Path(tmp)):
                self.assertEqual(len(flow_lines(resolve.resolve(feature))), 2)

    def test_line_split_at_antimeridian_rejoins(self) -> None:
        halves = combine([LineString([(170, 10), (180, 12)]), LineString([(-180, 12), (-170, 14)])])
        self.assertEqual(len(flow_lines(halves)), 1)


if __name__ == "__main__":
    unittest.main()
