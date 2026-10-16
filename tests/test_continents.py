import unittest
from unittest import mock

from shapely.geometry import box
from shapely.ops import unary_union

import geofeat.continents as continents
from geofeat.continents import (COMPOSED, MEMBERSHIP, REGION_CONTINENT, TRANSCONTINENTAL, continent_geometry, disjoint,
                                members)
from geofeat.countries_ne import state_ids
from geofeat.model import Expect, Feature, Part, active, load_features, orientation
from geofeat.order.engine import CONTINENTS
from geofeat.regions import ring
from geofeat.resolve import resolve
from geofeat.sources import features as features_source


def continent(slug: str, part: Part) -> Feature:
    return Feature(id=slug, name=slug, type="Continent", category="Continents", tier=1, style="area",
                   geometry=[part], expect=Expect(bbox=(-180, -90, 180, 90)))


class CompositionTest(unittest.TestCase):
    # NE's landmasses overlap at 6–6.5°E; Russia straddles the line and has an island off every landmass.
    landmasses = {"europe": box(0, 0, 6.5, 10), "asia": box(6, 0, 20, 10)}
    island = box(13, 11, 14, 12)
    countries = {"germany": box(0, 0, 4, 10), "russia": unary_union([box(4, 0, 12, 10), island]),
                 "china": box(12, 0, 20, 10), "greenland": box(5, 10.5, 6, 11)}
    members = {"germany": "europe", "russia": ("europe", "asia"), "china": "asia", "greenland": "europe"}

    def compose(self, name: str):
        return continent_geometry(name, self.members, self.countries, disjoint(self.landmasses))

    def test_overlap_goes_to_the_smaller_continent(self) -> None:
        lands = disjoint(self.landmasses)
        self.assertTrue(lands["europe"].equals(box(0, 0, 6.5, 10)))
        self.assertTrue(lands["asia"].equals(box(6.5, 0, 20, 10)))

    def test_continent_is_the_union_of_its_countries_split_along_the_line(self) -> None:
        europe, asia = self.compose("europe"), self.compose("asia")
        self.assertTrue(europe.equals(unary_union([box(0, 0, 6.5, 10), self.countries["greenland"]])))
        self.assertTrue(asia.equals(unary_union([box(6.5, 0, 20, 10), self.island])))
        self.assertAlmostEqual(europe.intersection(asia).area, 0)
        self.assertTrue(unary_union([europe, asia]).equals(unary_union(list(self.countries.values()))))

    def test_a_country_off_the_landmasses_stays_whole(self) -> None:
        self.assertTrue(self.compose("europe").contains(self.countries["greenland"]))


class MembershipTest(unittest.TestCase):
    def test_every_ring_region_has_a_continent(self) -> None:
        self.assertEqual(set(REGION_CONTINENT), {r.slug for r in ring().values()})
        self.assertLessEqual(set(REGION_CONTINENT.values()), set(COMPOSED))

    def test_every_placed_entry_is_on_a_continent(self) -> None:
        placed = {i for r in ring().values() for i in (*r.countries, *r.territories, *r.disputes)}
        self.assertEqual(set(members()), placed)
        for spans in members().values():
            self.assertLessEqual(set((spans,) if isinstance(spans, str) else spans), set(COMPOSED))

    def test_exceptions_name_placed_entries(self) -> None:
        placed = {i for r in ring().values() for i in (*r.countries, *r.territories, *r.disputes)}
        self.assertLessEqual(set(MEMBERSHIP), placed)
        self.assertLessEqual(set(TRANSCONTINENTAL), set(state_ids()))

    def test_exceptions_differ_from_the_ring(self) -> None:
        region = {i: REGION_CONTINENT[r.slug] for r in ring().values() for i in (*r.countries, *r.territories, *r.disputes)}
        for entry, continent in MEMBERSHIP.items():
            self.assertNotEqual(region[entry], continent, entry)
        for entry, spans in TRANSCONTINENTAL.items():
            self.assertIn(region[entry], spans, entry)

    def test_un_geoscheme_edges(self) -> None:
        m = members()
        expected = {"indonesia": "asia", "timor-leste": "asia", "united-states": "north-america",
                    "chile": "south-america", "cyprus": "asia", "armenia": "asia", "greenland": "north-america",
                    "panama": "north-america", "trinidad-and-tobago": "north-america", "aruba": "north-america",
                    "french-guiana": "south-america", "western-sahara": "africa", "papua-new-guinea": "oceania"}
        self.assertEqual({i: m[i] for i in expected}, expected)
        caribbean = next(r for r in ring().values() if r.slug == "caribbean")
        self.assertEqual({m[c] for c in caribbean.countries}, {"north-america"})


class PartTest(unittest.TestCase):
    def test_a_continent_part_resolves_to_its_composition(self) -> None:
        with mock.patch.object(continents, "geometry", {"europe": box(0, 0, 1, 1)}.__getitem__):
            shape = resolve(continent("europe", Part(layer="continent", select={"id": "europe"})))
        self.assertTrue(shape.equals(box(0, 0, 1, 1)))

    def test_a_continent_part_takes_exactly_an_id(self) -> None:
        for part in (Part(layer="continent", select={"name": "europe"}),
                     Part(layer="continent", select={"id": "europe"}, rows=2),
                     Part(layer="continent", select={"id": "europe"}, subtract=True)):
            with self.subTest(part=part), self.assertRaisesRegex(ValueError, "exactly"):
                continents.part_geometry("x", part)

    def test_a_continent_with_sea_in_it_fails(self) -> None:
        with mock.patch.object(continents, "_checked", return_value=(box(0, 0, 1, 1), ["continent asia: 4.1% sea"])), \
                self.assertRaisesRegex(ValueError, "4.1% sea"):
            continents.geometry("asia")

    def test_only_composed_continents(self) -> None:
        with self.assertRaisesRegex(ValueError, "no composed continent"):
            continents.geometry("antarctica")


class CardsTest(unittest.TestCase):
    def test_seven_orientation_continents(self) -> None:
        found = [f for f in active(load_features()) if f.type == "Continent"]
        self.assertEqual(sorted(f.id for f in found), sorted([*COMPOSED, "antarctica"]))
        self.assertTrue(all(orientation(f) and f.tier == 1 for f in found))
        self.assertIn("Oceania", {f.name for f in found})
        self.assertEqual(set(CONTINENTS), {f.id for f in found})

    def test_continent_cards_are_their_own_kind(self) -> None:
        cards = [c for c in features_source.cards() if c.kind == "continent"]
        self.assertEqual({c.id for c in cards}, set(CONTINENTS))
        for c in cards:
            self.assertEqual((c.key, c.study_pass, c.block), (f"continent:{c.id}", "orientation", "continents"))
            self.assertLessEqual({f"id_continent_{c.id}", "kind::continent", "category::continents"}, set(c.tags))


if __name__ == "__main__":
    unittest.main()
