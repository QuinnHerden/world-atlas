"""The curriculum order's real-data wiring: frames and look-alike pairs from the geometry facts, openers, and the P4
skip for unrendered kinds."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from shapely.geometry import box

from geofeat.card import Card, Kind, RenderRef, pass_tag, study_pass
from geofeat.curriculum import Curriculum, Region
from geofeat.deckgen import skip_unrendered
from geofeat.order import Frame, OrderError
from geofeat.order import frames
from geofeat.order.frames import Facts, GeometryFacts
from geofeat.order.inputs import feature_frames, lookalikes, opener_errors
from geofeat.spec import RenderSpec

REF = RenderRef(spec=RenderSpec(style="area"), geometry=lambda: (box(0, 0, 1, 1), (), None))


def make(kind: Kind, id: str) -> Card:
    return Card(uid=(id + "0" * 10)[:10], kind=kind, id=id, prompt="X", answer_lines=(id,),
                tags=(pass_tag(study_pass(kind, 1)),), tier=1, render=REF)


def region(number: int, opener: str | None = None) -> Region:
    return Region(number=number, slug=f"r{number}", name="R", entry="a", exit="b", countries=["a", "b"], opener=opener)


FACTS = GeometryFacts(
    features={
        "peninsula": Facts(1, ("a", "b"), {"a": 0.2, "b": 0.9}, {"a": 0.1, "b": 0.7}),
        "strait": Facts(1, ("a", "b"), {"a": 0.0, "b": 0.0}, {"a": 0.0, "b": 0.0}),
        "split": Facts(2, ("a", "b"), {"a": 0.3, "b": 0.4}, {"a": 0.2, "b": 0.3}),
        "islet": Facts(2, (), {}, {}),
    },
    # (a, b, km, cover): near; too far; near but nested
    same_family=[("peninsula", "strait", 0.0, 0.2), ("split", "strait", 60.0, 0.0), ("islet", "split", 0.0, 0.95)],
)


class LookalikesTest(unittest.TestCase):
    def test_confusables_near_same_family_features_and_footprints(self) -> None:
        cards = [make("country", "niger"), make("country", "nigeria"), make("country", "b"),
                 make("country", "somalia"), make("dispute", "somaliland")]
        curriculum = Curriculum.model_construct(confusables=[["niger", "nigeria"], ["somalia", "somaliland"]])
        self.assertEqual(lookalikes(cards, curriculum, FACTS), [
            ("country:niger", "country:nigeria"), ("country:somalia", "dispute:somaliland"),
            ("feature:peninsula", "feature:strait"), ("country:b", "feature:peninsula")])

    def test_contained_pair_is_not_a_lookalike(self) -> None:
        pairs = lookalikes([], Curriculum.model_construct(confusables=[]), FACTS)
        self.assertNotIn(("feature:islet", "feature:split"), pairs)
        self.assertNotIn(("feature:split", "feature:strait"), pairs)

    def test_confusable_without_a_card(self) -> None:
        curriculum = Curriculum.model_construct(confusables=[["niger", "nigeria"]])
        with self.assertRaisesRegex(OrderError, "confusable nigeria"):
            lookalikes([make("country", "niger")], curriculum, FACTS)


class FeatureFramesTest(unittest.TestCase):
    def test_opener_frames_what_it_mostly_covers_others_what_they_touch(self) -> None:
        curriculum = Curriculum.model_construct(regions=[region(1, "peninsula"), region(2, "split")])
        frames = feature_frames(FACTS, curriculum)
        self.assertEqual(frames["feature:peninsula"], Frame(1, ("b",), True))
        self.assertEqual(frames["feature:strait"], Frame(1, ("a", "b"), False))
        self.assertEqual(frames["feature:split"], Frame(2, ("b",), True))  # none mostly: the one it holds most of

    def test_opener_touching_nothing_opens_the_region(self) -> None:
        curriculum = Curriculum.model_construct(regions=[region(2, "islet")])
        self.assertEqual(feature_frames(FACTS, curriculum)["feature:islet"], Frame(2, (), True))

    def test_opener_errors(self) -> None:
        curriculum = Curriculum.model_construct(regions=[
            region(2, "peninsula"), region(1, "gone"), Region(**region(3).model_dump() | {"slug": "r3b", "opener": "peninsula"})])
        self.assertEqual(opener_errors(curriculum, FACTS), [
            "r2: opener peninsula is in region 1, not 2",
            "r1: opener 'gone' is not an active feature outside orientation",
            "r3b: opener peninsula already opens r2",
            "r3b: opener peninsula is in region 1, not 3"])
        with self.assertRaisesRegex(OrderError, "opener peninsula is in region 1"):
            feature_frames(FACTS, curriculum)


class FactsCacheTest(unittest.TestCase):
    def test_round_trip_and_recompute_when_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(frames, "CACHE", Path(tmp) / "frames.json"), \
                mock.patch.object(frames, "BUILD", Path(tmp)), \
                mock.patch.object(frames, "compute", return_value=FACTS) as compute, \
                mock.patch.object(frames, "inputs_hash", return_value="k1") as key:
            self.assertEqual(frames.load(), FACTS)
            self.assertEqual(frames.load(), FACTS)
            self.assertEqual(compute.call_count, 1)
            key.return_value = "k2"
            frames.load()
            self.assertEqual(compute.call_count, 2)
            (Path(tmp) / "frames.json").write_text("{not json")
            frames.load()
            self.assertEqual(compute.call_count, 3)


class SkipUnrenderedTest(unittest.TestCase):
    cards = [make("feature", "alps"), make("country", "chile")]

    def test_every_card_needs_a_map_by_default(self) -> None:
        with mock.patch.dict(os.environ, {"ALLOW_UNRENDERED": ""}), self.assertRaises(SystemExit):
            skip_unrendered(self.cards, {"feature:alps": "a.png"})

    def test_flag_skips_only_new_kinds(self) -> None:
        with mock.patch.dict(os.environ, {"ALLOW_UNRENDERED": "1"}):
            self.assertEqual(skip_unrendered(self.cards, {"feature:alps": "a.png"}), self.cards[:1])
            with self.assertRaises(SystemExit):
                skip_unrendered(self.cards, {"country:chile": "c.png"})
