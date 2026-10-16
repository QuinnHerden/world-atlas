"""The curriculum order engine (ADR 0009) on the fixture world in tests/fixtures/world/world.yaml."""

import hashlib
import random
import unittest
from pathlib import Path

from ruamel.yaml import YAML
from shapely.geometry import box

from geofeat.card import Card, RenderRef, Kind, block_of, block_tag, card_key
from geofeat.curriculum import Curriculum
from geofeat.order import Frame, curriculum_order, report
from geofeat.order.walk import Walk, generate, region_walk
from geofeat.spec import RenderSpec

WORLD = Path(__file__).parent / "fixtures/world"
GOLDEN = WORLD / "golden.txt"
DATA = YAML(typ="safe").load(WORLD / "world.yaml")
REF = RenderRef(spec=RenderSpec(style="area"), geometry=lambda: (box(0, 0, 1, 1), (), None))


def make(kind: Kind, id: str, tier: int = 1, region: int | None = None, orientation: bool = False, **extra) -> Card:
    return Card(uid=hashlib.sha256(card_key(kind, id).encode()).hexdigest()[:10], kind=kind, id=id, prompt=extra.pop("prompt", "X"),
                answer_lines=(id,), tags=(block_tag(block_of(kind)),), tier=tier,
                region=None if region is None else f"{region:02d}", orientation=orientation, render=REF, **extra)


def world_cards() -> list[Card]:
    cards = []
    regions = {c["id"]: c["region"] for c in DATA["countries"]}
    for c in DATA["countries"]:
        host = f"country:{c['host']}" if "host" in c else None
        cards.append(make("country", c["id"], c.get("tier", 1), c["region"], host=host))
        if c.get("capital", True):
            cards.append(make("capital", c["id"], c.get("tier", 1), c["region"], parents=(f"country:{c['id']}",)))
    for t in DATA["territories"]:
        cards.append(make(t["kind"], t["id"], 2, t["region"], host=f"country:{t['host']}"))
    for f in DATA["features"]:
        cards.append(make("feature", f["id"], f.get("tier", 1), orientation="region" not in f, prompt=f["prompt"]))
    for c in DATA["cities"]:
        parents = (f"country:{c['country']}", f"capital:{c['country']}")
        anchor = f"feature:{c['anchor']}" if "anchor" in c else None
        cards.append(make("city", c["id"], c["tier"], regions[c["country"]], parents=parents, anchor=anchor))
    return cards


def adjacency() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for a, bs in DATA["adjacency"].items():
        for b in bs:
            out.setdefault(a, set()).add(b)
            out.setdefault(b, set()).add(a)
    return out


CURRICULUM = Curriculum.model_validate(DATA["curriculum"])
FRAMES = {f"feature:{f['id']}": Frame(f["region"], tuple(f["countries"]), f.get("opens", False))
          for f in DATA["features"] if "region" in f}
EDGES = [(f"feature:{p}", f"feature:{f['id']}") for f in DATA["features"] for p in f.get("parents", [])]
LOOKALIKES = [(f"feature:{a}", f"feature:{b}") for a, b in DATA["close"]] + [
    (f"country:{a}", f"country:{b}") for group in DATA["curriculum"]["confusables"] for a in group for b in group if a < b]


def order(cards: list[Card] | None = None, **extra):
    args = dict(adjacency=adjacency(), frames=FRAMES, edges=EDGES, lookalikes=LOOKALIKES) | extra
    return curriculum_order(world_cards() if cards is None else cards, CURRICULUM, **args)


def keys(cards: list[Card]) -> list[str]:
    return [c.key for c in cards]


class GoldenTest(unittest.TestCase):
    def test_matches_the_golden_order(self) -> None:
        # To accept a deliberate change: write keys(order().cards), one per line, to tests/fixtures/world/golden.txt.
        self.assertEqual(keys(order().cards), GOLDEN.read_text().split())

    def test_every_card_once(self) -> None:
        self.assertEqual(sorted(keys(order().cards)), sorted(keys(world_cards())))


class PassTest(unittest.TestCase):
    def test_orientation_then_pass_1_then_pass_2(self) -> None:
        passes = [{"orientation": 0, 1: 1, 2: 2}[c.study_pass] for c in order().ring]
        self.assertEqual(passes, sorted(passes))

    def test_orientation_is_continents_oceans_winds(self) -> None:
        head = keys(order().ring)[:5]
        self.assertEqual(head, ["feature:europe", "feature:atlantic-ocean", "feature:pacific-ocean",
                                "feature:trade-winds", "feature:westerlies"])

    def test_regions_in_ring_order_within_each_pass(self) -> None:
        o = order()
        self.assertEqual([(r.study_pass, r.region.number) for r in o.reports], [(1, 1), (1, 2), (1, 3), (2, 2)])


class WalkTest(unittest.TestCase):
    def test_generated_walk_grows_a_frontier_from_entry_to_exit(self) -> None:
        walk = order().reports[0].walk
        self.assertFalse(walk.frozen)
        self.assertEqual(walk.nodes, ("alba", "bravo", "cerul", "delta", "echo"))
        self.assertEqual(walk.breaks(adjacency()), [])

    def test_countries_follow_the_walk(self) -> None:
        countries = [c.id for c in order().ring if c.kind == "country" and c.host is None]
        self.assertEqual(countries, ["alba", "bravo", "cerul", "delta", "echo", "fox", "golf", "hotel", "india",
                                     "juliet", "kilo"])

    def test_prefers_the_most_recent_neighbour(self) -> None:
        adj = {"a": {"b", "c"}, "b": {"a", "d"}, "c": {"a"}, "d": {"b"}}
        self.assertEqual(generate(["a", "b", "c", "d"], "a", "c", adj), ("a", "b", "d", "c"))

    def test_warnsdorff_then_id_break_ties(self) -> None:
        # From a, b and c both border the most recent; c has fewer unvisited neighbours.
        adj = {"a": {"b", "c"}, "b": {"a", "c", "d"}, "c": {"a", "b"}, "d": {"b"}}
        self.assertEqual(generate(["a", "b", "c", "d"], "a", "d", adj), ("a", "c", "b", "d"))
        self.assertEqual(generate(["a", "x", "y"], "a", "y", {"a": {"x", "y"}, "x": {"a"}, "y": {"a"}}), ("a", "x", "y"))

    def test_exit_is_held_back(self) -> None:
        adj = {"a": {"z", "b"}, "b": {"a"}, "z": {"a"}}
        self.assertEqual(generate(["a", "b", "z"], "a", "z", adj), ("a", "b", "z"))

    def test_stuck_walk_jumps_in_listed_order_and_reports_it(self) -> None:
        north = order().reports[1]
        self.assertEqual(north.walk.nodes, ("fox", "golf", "hotel", "india"))
        self.assertEqual(north.jumps, [("hotel", "india")])
        self.assertEqual(north.breaks, ["india"])

    def test_frozen_walk_wins_and_is_checked(self) -> None:
        o = order(frozen={"west": ["alba", "cerul", "bravo", "delta", "echo"]})
        self.assertTrue(o.reports[0].walk.frozen)
        self.assertEqual([c.id for c in o.ring if c.kind == "country" and c.region == "01" and c.host is None],
                         ["alba", "cerul", "bravo", "delta", "echo"])
        with self.assertRaises(ValueError):
            region_walk(["a", "b"], "a", "b", {}, frozen=["b", "a"])
        with self.assertRaises(ValueError):
            region_walk(["a", "b"], "a", "b", {}, frozen=["a"])

    def test_frozen_walk_from_the_curriculum(self) -> None:
        data = DATA["curriculum"] | {"regions": [r | ({"walk": ["alba", "cerul", "bravo", "delta", "echo"]}
                                                      if r["slug"] == "west" else {}) for r in DATA["curriculum"]["regions"]]}
        o = curriculum_order(world_cards(), Curriculum.model_validate(data), adjacency(), FRAMES, EDGES, LOOKALIKES)
        self.assertTrue(o.reports[0].walk.frozen)
        self.assertEqual(o.reports[0].walk.nodes, ("alba", "cerul", "bravo", "delta", "echo"))

    def test_frozen_walk_for_an_unknown_region(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown regions"):
            order(frozen={"nowhere": ["alba"]})

    def test_jumps_are_consecutive_non_neighbours(self) -> None:
        adj = {"a": {"b", "c"}, "b": {"a"}, "c": {"a"}}
        walk = Walk(("a", "b", "c"), False)
        self.assertEqual(walk.jumps(adj), [("b", "c")])
        self.assertEqual(walk.breaks(adj), [])


class AnchorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.order = keys(order().ring)
        self.at = {k: i for i, k in enumerate(self.order)}

    def test_capital_two_or_three_after_its_country(self) -> None:
        for k in self.order:
            if k.startswith("capital:"):
                with self.subTest(k):
                    self.assertIn(self.at[k] - self.at["country:" + k.removeprefix("capital:")], (2, 3))

    def test_pockets_right_after_the_host_capital(self) -> None:
        self.assertEqual(self.at["country:andor"], self.at["capital:bravo"] + 1)
        # A capital whose 3-card deadline falls due goes first.
        self.assertIn(self.at["territory:isle"] - self.at["capital:delta"], (1, 2, 3))
        self.assertEqual(self.at["dispute:fjord"], self.at["capital:golf"] + 1)

    def test_feature_after_the_last_country_that_frames_it(self) -> None:
        # west-range frames bravo, its pocket andor and cerul; cerul comes last.
        self.assertEqual(self.at["feature:west-range"], self.at["country:cerul"] + 1)
        self.assertEqual(self.at["feature:north-sea"], self.at["country:golf"] + 1)

    def test_opening_feature_comes_before_its_first_country(self) -> None:
        self.assertEqual(self.at["feature:west-peninsula"], self.at["country:alba"] - 1)

    def test_unframed_feature_closes_its_region(self) -> None:
        region_1 = [k for k in self.order if self.at["feature:west-peninsula"] <= self.at[k] < self.at["country:fox"]]
        self.assertGreater(self.at["feature:inner-gulf"], self.at["country:echo"])
        self.assertEqual(region_1[-1], "feature:inner-gulf")

    def test_city_after_its_anchor_feature_or_its_capital(self) -> None:
        self.assertEqual(self.at["city:rivermouth"], self.at["feature:long-river-delta"] + 1)
        self.assertGreater(self.at["city:bravoburg"], self.at["capital:bravo"])
        self.assertEqual(self.at["city:hotelport"], self.at["feature:golf-strait"] + 1)

    def test_pass_2_follows_the_walk_without_its_countries(self) -> None:
        self.assertEqual(self.order[-3:], ["city:foxton", "feature:golf-strait", "city:hotelport"])


class BlockTest(unittest.TestCase):
    """The study order (ADR 0009): continents, countries (with territories and disputes), features, capitals and
    cities, each cut from the ring order."""

    def setUp(self) -> None:
        self.o = order()
        self.order = keys(self.o.cards)

    def test_four_blocks_in_order(self) -> None:
        rank = {"continent": 0, "country": 1, "territory": 1, "dispute": 1, "feature": 2, "capital": 3, "city": 3}
        kinds = [rank[k.split(":")[0]] for k in self.order]
        self.assertEqual(kinds, sorted(kinds))

    def test_countries_walk_with_pockets_after_their_host(self) -> None:
        political = [k for k in self.order if k.split(":")[0] in ("country", "territory", "dispute")]
        self.assertEqual(political, ["country:alba", "country:bravo", "country:andor", "country:cerul", "country:delta",
                                     "territory:isle", "country:echo", "country:fox", "country:golf", "dispute:fjord",
                                     "country:hotel", "country:india", "country:juliet", "country:kilo"])

    def test_features_keep_their_ring_order_but_for_look_alikes(self) -> None:
        features = [k for k in self.order if k.startswith("feature:")]
        self.assertEqual(sorted(features), sorted(k for k in keys(self.o.ring) if k.startswith("feature:")))
        at = {k: i for i, k in enumerate(self.order)}
        for a, b in LOOKALIKES:
            same_region = a in FRAMES and b in FRAMES and FRAMES[a].region == FRAMES[b].region
            if same_region and not any(a in w and b in w for w in self.o.waivers):
                with self.subTest((a, b)):
                    self.assertTrue(3 <= abs(at[a] - at[b]) <= 10)

    def test_each_capital_then_its_cities(self) -> None:
        towns = [k for k in self.order if k.split(":")[0] in ("capital", "city")]
        self.assertEqual(towns[:4], ["capital:alba", "capital:bravo", "city:bravoburg", "capital:cerul"])


class RepairTest(unittest.TestCase):
    def setUp(self) -> None:
        self.ordering = order()
        self.order = keys(self.ordering.ring)
        self.at = {k: i for i, k in enumerate(self.order)}

    def test_parent_moves_to_just_before_its_earliest_child(self) -> None:
        self.assertEqual(self.at["feature:ocean-sea"], self.at["feature:inner-gulf"] - 1)
        self.assertIn("feature:ocean-sea moved to region 1, before its child feature:inner-gulf", self.ordering.waivers)

    def test_parent_before_child(self) -> None:
        self.assertLess(self.at["feature:long-river"], self.at["feature:long-river-delta"])

    def test_same_id_never_side_by_side(self) -> None:
        cards = self.ordering.ring
        self.assertFalse([(a.key, b.key) for a, b in zip(cards, cards[1:]) if a.id == b.id])

    def test_lookalikes_three_to_ten_apart_within_a_region(self) -> None:
        for a, b in (("country:bravo", "country:delta"), ("feature:west-range", "feature:long-river")):
            with self.subTest(a=a, b=b):
                self.assertIn(abs(self.at[a] - self.at[b]), range(3, 11))

    def test_lookalike_window_waived_across_regions(self) -> None:
        text = report(self.ordering)
        self.assertNotIn("alba and country:juliet", text)
        self.assertNotIn("north-sea and feature:kilo-lake", text)

    def test_parent_in_a_later_pass_is_reported(self) -> None:
        cards = world_cards()
        o = order(cards, edges=EDGES + [("feature:golf-strait", "feature:north-sea")])
        self.assertIn("feature:north-sea comes before its parent feature:golf-strait, which is in a later pass", o.waivers)

    def test_parent_never_moves_into_an_earlier_pass(self) -> None:
        # pp (pass 2) is the parent of a pass-2 card in region 1 and of a pass-1 card in region 2.
        pp = make("feature", "pp", 3, prompt="Range")
        child_2 = make("feature", "aa", 3, prompt="Range")
        frames = FRAMES | {pp.key: Frame(2, ("hotel",)), child_2.key: Frame(1, ("alba",))}
        edges = EDGES + [(pp.key, child_2.key), (pp.key, "feature:north-sea")]
        o = order(world_cards() + [pp, child_2], frames=frames, edges=edges)
        at = {k: i for i, k in enumerate(keys(o.ring))}
        passes = [{"orientation": 0, 1: 1, 2: 2}[c.study_pass] for c in o.ring]
        self.assertEqual(passes, sorted(passes))
        self.assertEqual(at[pp.key], at[child_2.key] - 1)
        self.assertIn("feature:north-sea comes before its parent feature:pp, which is in a later pass", o.waivers)

    def test_unrepairable_capital_gap_is_waived(self) -> None:
        cards = [c for c in world_cards() if c.region != "03" or c.id == "kilo"]
        o = order([c for c in cards if c.key not in ("feature:ocean-sea", "feature:kilo-lake", "feature:inner-gulf")],
                  frozen={"east": ["juliet", "kilo"]})
        east = next(r for r in o.reports if r.region.number == 3)
        self.assertEqual(east.waivers, ["capital:kilo is 1 cards after country:kilo (wants 2-3)",
                                        "country:kilo and capital:kilo share an id and sit side by side"])

    def test_report_lists_jumps_and_waivers(self) -> None:
        text = report(self.ordering)
        self.assertIn("pass 1 region  2 North: generated walk, 1 jump(s): hotel→india; 1 frontier break(s): india", text)
        self.assertIn("waiver: feature:ocean-sea moved to region 1", text)


class ErrorTest(unittest.TestCase):
    def test_feature_without_a_frame(self) -> None:
        frames = {k: v for k, v in FRAMES.items() if k != "feature:north-sea"}
        with self.assertRaisesRegex(ValueError, "feature:north-sea: no frame"):
            order(frames=frames)

    def test_territory_host_must_match_the_curriculum(self) -> None:
        cards = [c for c in world_cards() if c.key != "territory:isle"] + [make("territory", "isle", 2, 1, host="country:echo")]
        with self.assertRaisesRegex(ValueError, "territory:isle: host country:echo isn't its curriculum host"):
            order(cards)

    def test_cycle(self) -> None:
        with self.assertRaisesRegex(ValueError, "cycle"):
            order(edges=EDGES + [("feature:long-river-delta", "feature:long-river")])

    def test_frames_as_a_function(self) -> None:
        self.assertEqual(keys(order(frames=lambda c: FRAMES.get(c.key)).cards), keys(order().cards))


NEARBY = 6  # about one cluster: a country, its capital and what hangs off them


class StabilityTest(unittest.TestCase):
    def test_deterministic_whatever_the_input_order(self) -> None:
        expected = keys(order().cards)
        for seed in range(5):
            cards = world_cards()
            random.Random(seed).shuffle(cards)
            adj = {k: set(sorted(v, reverse=bool(seed % 2))) for k, v in reversed(list(adjacency().items()))}
            with self.subTest(seed=seed):
                self.assertEqual(keys(order(cards, adjacency=adj).cards), expected)

    def test_adding_one_card_moves_only_nearby_cards(self) -> None:
        base = keys(order().ring)
        extra = [
            (make("feature", "east-hills", prompt="Hills"), Frame(1, ("delta",))),
            (make("city", "kilotown", 2, 3, parents=("country:kilo", "capital:kilo")), None),
            (make("feature", "fox-fell", 3, prompt="Hills"), Frame(2, ("fox",))),
        ]
        for card, frame in extra:
            with self.subTest(card.key):
                frames = FRAMES | ({card.key: frame} if frame else {})
                grown = keys(order(world_cards() + [card], frames=frames).ring)
                at = grown.index(card.key)
                rest = [k for k in grown if k != card.key]
                moved = [i for i, (a, b) in enumerate(zip(base, rest)) if a != b]
                self.assertTrue(all(abs(i - at) <= NEARBY for i in moved), f"{card.key} at {at} moved {moved}")


class CompatibilityTest(unittest.TestCase):
    def test_old_api_still_imports_from_geofeat_order(self) -> None:
        import geofeat.order as order_pkg
        from geofeat.order import legacy

        for name in ("NEAR_GAP", "SIBLINGS", "Edge", "Siblings", "dependencies", "inputs_hash", "inverted",
                     "load_siblings", "save_siblings", "study_order"):
            with self.subTest(name):
                self.assertIs(getattr(order_pkg, name), getattr(legacy, name))
