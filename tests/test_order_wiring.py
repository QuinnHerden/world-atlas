"""deckgen's wiring of the curriculum order: look-alike pairs from the data, and the P4 skip for unrendered kinds."""

import os
import unittest
from unittest import mock

from shapely.geometry import box

from geofeat.card import Card, Kind, RenderRef, pass_tag, study_pass
from geofeat.curriculum import Curriculum
from geofeat.deckgen import skip_unrendered
from geofeat.order.inputs import lookalikes
from geofeat.order import Siblings
from geofeat.spec import RenderSpec

REF = RenderRef(spec=RenderSpec(style="area"), geometry=lambda: (box(0, 0, 1, 1), (), None))


def make(kind: Kind, id: str) -> Card:
    return Card(uid=(id + "0" * 10)[:10], kind=kind, id=id, prompt="X", answer_lines=(id,),
                tags=(pass_tag(study_pass(kind, 1)),), tier=1, render=REF)


class LookalikesTest(unittest.TestCase):
    def test_close_features_and_confusable_sets(self) -> None:
        cards = [make("country", "niger"), make("country", "nigeria"), make("feature", "niger"),
                 make("country", "somalia"), make("dispute", "somaliland")]
        curriculum = Curriculum.model_construct(confusables=[["niger", "nigeria"], ["somalia", "somaliland"]])
        siblings = Siblings(area_km2={}, close=[("bosporus", "dardanelles")], nested=[])
        self.assertEqual(lookalikes(cards, curriculum, siblings), [
            ("feature:bosporus", "feature:dardanelles"), ("country:niger", "country:nigeria"),
            ("country:somalia", "dispute:somaliland")])


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
