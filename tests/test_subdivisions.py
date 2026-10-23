"""Companion decks (ADR 0012): the subdivision source, its cards and decks, the tiling check and the walk."""

import unittest

from pydantic import ValidationError
from shapely.geometry import box

import geofeat.sources.subdivisions as subdivisions
from geofeat.card import Card, RenderRef
from geofeat.decks import BY_COUNTRY, BY_NAME, SUBDIVISION_DECKS, DECKS, WORLD, DeckInfo, deck_of_position
from geofeat.order import companions
from geofeat.spec import RenderSpec

A1 = "10m_admin_1_states_provinces"


def entry(**kw) -> dict:
    return {"id": "us-maine", "uid": "MaineMaine", "name": "Maine", "country": "united-states", "type": "State",
            "geometry": [{"layer": A1, "select": {"iso_3166_2": "US-ME"}}], "expect": [-71.1, 43.0, -66.9, 47.5],
            "note": "Rocky coast.", **kw}


class ModelTest(unittest.TestCase):
    def test_an_entry_belongs_to_its_countrys_deck(self) -> None:
        s = subdivisions.Subdivision.model_validate(entry())
        self.assertEqual(s.deck.name, "US States")

    def test_ids_carry_the_decks_prefix_and_countries_need_a_deck(self) -> None:
        for bad in ({"id": "it-maine"}, {"id": "maine"}, {"country": "france", "id": "fr-maine"}, {"type": "County"}):
            with self.subTest(bad), self.assertRaises(ValidationError):
                subdivisions.Subdivision.model_validate(entry(**bad))

    def test_the_card(self) -> None:
        card = subdivisions.card(subdivisions.Subdivision.model_validate(entry(alt_names=["Pine Tree State"])))
        self.assertEqual((card.kind, card.key, card.prompt, card.deck, card.block), (
            "subdivision", "subdivision:us-maine", "State", "US States", "subdivisions"))
        self.assertEqual(card.answer_lines, ("Maine (Pine Tree State)",))
        self.assertEqual(card.tags, ("id_subdivision_us-maine", "kind::subdivision", "block::subdivisions",
                                     "country::united-states"))
        self.assertFalse([t for t in card.tags if t.startswith(("region::", "tier::"))])

    def test_only_subdivisions_go_in_a_companion_deck(self) -> None:
        ref = RenderRef(spec=RenderSpec(style="area"), geometry=lambda: (box(0, 0, 1, 1), (), None))
        base = dict(uid="AAAAAAAAAA", id="x", prompt="State", answer_lines=("X",), tier=1, render=ref)
        Card(kind="subdivision", tags=("block::subdivisions",), deck="US States", **base)
        Card(kind="country", tags=("block::countries",), **base)
        for kind, block, deck in (("subdivision", "subdivisions", WORLD.name), ("country", "countries", "US States"),
                                  ("subdivision", "subdivisions", "Nowhere")):
            with self.subTest(kind=kind, deck=deck), self.assertRaises(ValidationError):
                Card(kind=kind, tags=(f"block::{block}",), deck=deck, **base)


class DeckRegistryTest(unittest.TestCase):
    def test_ranges_are_disjoint_and_ordered(self) -> None:
        for a, b in zip(DECKS, DECKS[1:]):
            self.assertLessEqual(a.limit, b.base)
        self.assertEqual(deck_of_position(650_500).slug, "us-states")
        self.assertEqual(deck_of_position(900_000).slug, "world-flags")
        self.assertIsNone(deck_of_position(960_000))

    def test_names_and_slugs(self) -> None:
        self.assertEqual([d.slug for d in DECKS], ["world-atlas", "italian-regions", "us-states", "brazilian-states",
                                                   "canadian-provinces", "world-flags"])
        self.assertEqual(BY_NAME["World Atlas"], WORLD)
        self.assertEqual(sorted(BY_COUNTRY), ["brazil", "canada", "italy", "united-states"])


class TilingTest(unittest.TestCase):
    def test_overlap_gap_and_spill(self) -> None:
        whole = box(0, 0, 2, 1)
        self.assertEqual(subdivisions.tiling_errors("c", {"a": box(0, 0, 1, 1), "b": box(1, 0, 2, 1)}, whole), [])
        errors = subdivisions.tiling_errors("c", {"a": box(0, 0, 1.2, 1), "b": box(1, 0, 1.5, 1)}, whole)
        self.assertEqual(len(errors), 2)  # a and b overlap; a strip is left uncovered
        self.assertRegex(" ".join(subdivisions.tiling_errors("c", {"a": box(0, 0, 2.5, 1)}, whole)), "spill")


class WalkTest(unittest.TestCase):
    ADJ = {"a": {"b"}, "b": {"a", "c", "d"}, "c": {"b", "d"}, "d": {"b", "c"}, "island": set()}

    def test_generate_takes_the_frontier_then_jumps(self) -> None:
        deck = DeckInfo("T", "t", 0, 1, "t", "t", 5, "a")
        walk = companions.generate(deck, self.ADJ, ["a", "b", "c", "d", "island"])
        self.assertEqual(walk[:2], ["a", "b"])
        self.assertEqual(walk[-1], "island")
        self.assertEqual(companions.breaks(walk, self.ADJ), [])

    def test_lookalikes_wait_while_another_step_is_open(self) -> None:
        deck = DeckInfo("T", "t", 0, 1, "t", "t", 5, "b", (("b", "c"),))
        self.assertEqual(companions.generate(deck, self.ADJ, ["a", "b", "c", "d", "island"])[:3], ["b", "a", "d"])

    def test_an_avoidable_jump_is_a_break(self) -> None:
        self.assertEqual(companions.breaks(["a", "c", "b", "d", "island"], self.ADJ), ["c"])
        self.assertEqual(companions.breaks(["a", "b", "island", "c", "d"], self.ADJ), ["island"])

    def test_lookalike_gaps(self) -> None:
        deck = DeckInfo("T", "t", 0, 1, "t", "t", 5, "a", (("a", "b"), ("a", "d")))
        self.assertEqual(len(companions.lookalike_gaps(deck, ["a", "b", "c", "d"])), 1)  # a-d is 3 apart


class DataTest(unittest.TestCase):
    """The committed data: each companion deck's count, first card and walk."""

    def test_counts_and_entries(self) -> None:
        for deck in SUBDIVISION_DECKS:
            members = subdivisions.of_country(deck.country)
            self.assertEqual(len(members), deck.cards, deck.name)
            self.assertEqual(members[0].id, deck.entry)

    def test_every_card_is_in_its_deck(self) -> None:
        countries = {s.id: s.country for s in subdivisions.active()}
        for card in subdivisions.cards():
            self.assertEqual(card.deck, BY_COUNTRY[countries[card.id]].name)
            self.assertIn(f"country::{countries[card.id]}", card.tags)


class CountryMapTest(unittest.TestCase):
    """The companion decks' frames (ADR 0013), checked on the real outlines without rendering."""

    @classmethod
    def setUpClass(cls) -> None:
        from geofeat import country_map
        from geofeat.jobs import card_job

        cls.cm = country_map
        cls.plans = {c.id: country_map.layout(*(lambda j: (j.spec, j.geometry, j.context))(card_job(c)))
                     for c in subdivisions.cards()}

    def test_one_main_frame_per_deck(self) -> None:
        frames: dict[str, set] = {}
        for id, plan in self.plans.items():
            frames.setdefault(id.split("-")[0], set()).add(tuple(round(v) for v in plan["main"].extent))
        self.assertEqual({k: len(v) for k, v in frames.items()}, {"it": 1, "us": 1, "br": 1, "ca": 1})

    def test_the_inset_and_boxes_cover_none_of_the_country(self) -> None:
        from shapely import unary_union
        from shapely.geometry import box as rect

        from geofeat.frame import project

        for country in BY_COUNTRY:
            plan = next(p for i, p in self.plans.items() if i.startswith(BY_COUNTRY[country].prefix + "-"))
            main = plan["main"]
            boxed = {id(q) for _, members in plan["boxes"] for q in members}
            shown = main.to_card(project(unary_union([q for q in plan["parts"] if id(q) not in boxed]), main.projection))
            x, y, w, h = plan["inset_px"]
            with self.subTest(country=country):
                self.assertTrue(rect(0, 0, 1600, 900).contains(shown))
                self.assertFalse(shown.intersects(rect(x, y, x + w, y + h)))
                for panel, _ in plan["boxes"]:
                    bx, by, bw, bh = panel.px
                    self.assertFalse(shown.intersects(rect(bx, by, bx + bw, by + bh)))

    def test_alaska_and_hawaii_are_boxed(self) -> None:
        for id in ("us-alaska", "us-hawaii"):
            plan = self.plans[id]
            self.assertIsNot(plan["home"], plan["main"], id)
        self.assertIs(self.plans["us-texas"]["home"], self.plans["us-texas"]["main"])

    def test_the_inset_zooms_at_least_one_and_a_half_times(self) -> None:
        for id, plan in self.plans.items():
            inset, home = plan["inset"], plan["home"]
            lon, lat = self.cm.centre(plan["subject"])
            main_ground = home.metres_per_px / self.cm._ground_scale(home.projection, lon, lat)
            inset_ground = (inset.extent[1] - inset.extent[0]) / plan["inset_px"][2]
            self.assertGreaterEqual(main_ground / inset_ground, self.cm.INSET_ZOOM - 1e-9, id)

    def test_small_subjects_fill_enough_of_the_inset(self) -> None:
        from geofeat.frame import project

        for id in ("us-district-of-columbia", "br-distrito-federal", "us-rhode-island", "it-molise"):
            inset = self.plans[id]["inset"]
            x0, _, x1, _ = project(self.plans[id]["subject"], inset.projection).bounds
            self.assertGreaterEqual((x1 - x0) / (inset.extent[1] - inset.extent[0]), 0.15, id)  # "about 15-20%"

    def test_the_largest_have_no_inset(self) -> None:
        cropped = sorted(i for i, p in self.plans.items() if p["inset"].fit == "cropped")
        self.assertEqual(cropped, sorted([
            "us-idaho", "us-california", "us-texas", "br-amazonas", "br-para", "br-mato-grosso", "br-bahia",
            "ca-saskatchewan", "ca-manitoba", "ca-ontario", "ca-quebec", "ca-newfoundland-and-labrador",
            "ca-northwest-territories", "ca-nunavut"]))

    def test_a_reorder_keeps_the_render_key(self) -> None:
        from dataclasses import replace

        from geofeat.jobs import card_job

        job = card_job(next(c for c in subdivisions.cards() if c.id == "it-molise"))
        self.assertEqual(job.key(), replace(job, context=tuple(reversed(job.context))).key())


class KeyScopeTest(unittest.TestCase):
    """Only a companion card's key holds the companion renderer and its layer, so tuning it leaves World Atlas's maps
    cached."""

    def test_the_country_renderer_is_in_country_keys_only(self) -> None:
        from unittest import mock

        from shapely.geometry import box as rect

        import geofeat.jobs as jobs

        world = jobs.RenderJob(RenderSpec(style="area"), rect(0, 0, 1, 1))
        country = jobs.RenderJob(RenderSpec(style="area", country="subject", framing="country", country_frame="italy"),
                                 rect(0, 0, 1, 1))
        with mock.patch.object(jobs, "_code_hash", wraps=jobs._code_hash) as code:
            world.key()
            country.key()
        self.assertEqual([c.args[1] for c in code.call_args_list], [jobs.RENDERER, jobs.RENDERER + jobs.COUNTRY_MAP])

    def test_country_framing_needs_its_frame(self) -> None:
        for kw in ({"framing": "country"}, {"country_frame": "italy"}):
            with self.subTest(kw), self.assertRaises(ValidationError):
                RenderSpec(style="area", **kw)


if __name__ == "__main__":
    unittest.main()
