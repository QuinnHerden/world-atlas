import contextlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import geopandas as gpd
from pydantic import ValidationError
from ruamel.yaml import YAML
from shapely.geometry import MultiPolygon, Point, box

import geofeat.ids as ids
import geofeat.polities as polities
import geofeat.resolve as resolve
import geofeat.sources as sources
import geofeat.sources.cities as cities
import geofeat.sources.political as political
import geofeat.sources.features as features_source
from geofeat.card import PASS_ORDER, Card, pass_tag, study_pass
from geofeat.model import Feature, load_features
from geofeat.model import Part
from geofeat.polities import Country, Dispute, RingPlace, Territory, in_bbox, outline

A0, DA = "10m_admin_0_countries", "10m_admin_0_disputed_areas"
LAYERS = {
    A0: gpd.GeoDataFrame({"ne_id": [1, 2, 3, 5]}, geometry=[
        box(0, 0, 10, 10), box(10, 0, 11, 1), box(20, 20, 21, 21), MultiPolygon([box(0, 0, 10, 10), box(30, 30, 31, 31)]),
    ]),
    DA: gpd.GeoDataFrame({"ne_id": [4, 6]}, geometry=[box(0, 0, 2, 2), box(10, 0, 12, 2)]),
    political.PLACES: gpd.GeoDataFrame({"ne_id": [101, 102, 103]}, geometry=[Point(5, 5), Point(1, 1), Point(15, 5)]),
}


def a0(ne_id: int, **kw) -> dict:
    return {"layer": A0, "select": {"ne_id": ne_id}, **kw}


FEATURE_REGIONS = {"nile": 1}  # what regions.py would derive; anything else is region 1 too
PLACEMENTS = {  # what data/curriculum.yaml would give
    "alpha": RingPlace(1, None, "country"), "beta": RingPlace(2, None, "country"),
    "gamma": RingPlace(3, None, "territory"), "delta": RingPlace(1, "alpha", "dispute"),
}


def countries() -> list[dict]:
    return [
        {"id": "alpha", "name": "Alpha", "alt_names": ["Alfa"], "uids": {"country": "CountryAAA", "capital": "CapitalAAA"},
         "tier": 1, "note": "Big square.", "geometry": [a0(1)], "expect": [0, 0, 10, 10],
         "capital": {"name": "Alphaville", "ne_id": 101, "expect": [4, 4, 6, 6], "note": "Middle."}},
        {"id": "beta", "name": "Beta", "uids": {"country": "CountryBBB"}, "tier": 3,
         "geometry": [a0(2)], "expect": [10, 0, 11, 1], "capital": None},
    ]


def territories() -> list[dict]:
    return [
        {"kind": "territory", "id": "gamma", "name": "Gamma Isle", "uid": "TerritoryG", "sovereign": "alpha",
         "status_line": "Overseas department of Alpha", "geometry": [a0(3)], "expect": [20, 20, 21, 21]},
        {"kind": "dispute", "id": "delta", "name": "Delta", "uid": "DisputeDDD", "parties": ["beta", {"label": "Éire Front"}, "alpha"],
         "geometry": [{"layer": DA, "select": {"ne_id": 4}}], "expect": [0, 0, 2, 2]},
    ]


def feature_entry() -> dict:
    return {"id": "x", "name": "X", "type": "Plain", "category": "Deserts, Plateaus & Plains", "tier": 3, "style": "area",
            "geometry": [a0(1)], "expect": {"bbox": [0, 0, 1, 1]}}


def cities_data() -> list[dict]:
    return [{"id": "alpha-port", "name": "Alpha Port", "uid": "CityAAAAAA", "country": "alpha", "tier": "core",
             "ne_id": 102, "expect": [0, 0, 2, 2]}]


@contextlib.contextmanager
def data(countries=None, territories=None, cities_=None):
    """Write the given entries to a temporary data/ and point the sources and the NE layer lookup at them."""
    with tempfile.TemporaryDirectory() as tmp:
        paths = {}
        for name, entries in (("countries", countries), ("territories", territories), ("cities", cities_)):
            paths[name] = Path(tmp) / f"{name}.yaml"
            if entries is not None:
                YAML().dump(entries, paths[name])
        placed = set(e["id"] for e in territories or [] if isinstance(e, dict) and "id" in e)

        def placements(states: list[str]) -> dict[str, RingPlace]:  # the curriculum places only what the files hold
            return {k: v for k, v in PLACEMENTS.items() if k in states or k in placed}

        with mock.patch.multiple(polities, COUNTRIES=paths["countries"], TERRITORIES=paths["territories"],
                                 layer=LAYERS.__getitem__, curriculum_placements=placements), mock.patch.object(resolve, "layer", LAYERS.__getitem__), \
                mock.patch.object(cities, "PATH", paths["cities"]), \
                mock.patch.object(cities, "feature_region", lambda f: FEATURE_REGIONS.get(f, 1)):
            yield paths


def by_key(cards) -> dict:
    return {c.key: c for c in cards}


class CardTextTest(unittest.TestCase):
    def setUp(self) -> None:
        with data(countries(), territories(), cities_data()):
            self.cards = by_key(political.cards() + cities.cards())
            self.countries = political.load_countries()

    def test_every_kind(self) -> None:
        text = {k: (c.prompt, c.answer_lines) for k, c in self.cards.items()}
        self.assertEqual(text, {
            "country:alpha": ("Country", ("Alpha (Alfa)",)),
            "capital:alpha": ("City", ("Alphaville", "Capital of Alpha")),
            "country:beta": ("Country", ("Beta",)),
            "territory:gamma": ("Territory", ("Gamma Isle", "Overseas department of Alpha")),
            "dispute:delta": ("Disputed territory", ("Delta", "Disputed: Alpha, Beta, Éire Front")),
            "city:alpha-port": ("City", ("Alpha Port", "Alpha")),
        })

    def test_tags(self) -> None:
        self.assertEqual(self.cards["country:alpha"].tags,
                         ("tier::1", "category::countries", "id_country_alpha", "kind::country", "region::01", "pass::1"))
        self.assertEqual(self.cards["capital:alpha"].tags,
                         ("tier::1", "category::cities", "id_capital_alpha", "kind::capital", "region::01", "pass::1"))
        self.assertEqual(self.cards["city:alpha-port"].tags,
                         ("tier::2", "category::cities", "id_city_alpha-port", "kind::city", "region::01", "pass::1"))
        self.assertEqual(self.cards["territory:gamma"].tags[2:], ("id_territory_gamma", "kind::territory", "region::03", "pass::1"))
        self.assertEqual(self.cards["dispute:delta"].tags[2:], ("id_dispute_delta", "kind::dispute", "region::01", "pass::1"))

    def test_passes(self) -> None:
        self.assertEqual({k: c.study_pass for k, c in self.cards.items()}, dict.fromkeys(self.cards, 1))
        self.assertEqual(self.cards["country:beta"].tier, 3)  # a tier-3 microstate stays in pass 1
        secondary = cities_data()[0] | {"tier": "secondary"}
        with data(countries(), cities_=[secondary]):
            (city,) = cities.cards()
        self.assertEqual((city.study_pass, city.tags[-1]), (2, "pass::2"))

    def test_regions_notes_and_parents(self) -> None:
        self.assertEqual(self.cards["city:alpha-port"].region, "01")  # inherited from its country
        self.assertEqual(self.cards["territory:gamma"].region, "03")
        self.assertEqual(self.cards["capital:alpha"].note, "Middle.")
        self.assertEqual(self.cards["capital:alpha"].parents, ("country:alpha",))
        self.assertEqual(self.cards["city:alpha-port"].parents, ("country:alpha", "capital:alpha"))
        self.assertEqual(self.cards["dispute:delta"].host, "country:alpha")
        self.assertEqual((self.cards["dispute:delta"].anchor, self.cards["country:alpha"].host), (None, None))

    def test_render_specs(self) -> None:
        with data(countries(), territories(), cities_data()):
            spec = {k: c.render.resolve()[0] for k, c in self.cards.items()}
        self.assertEqual((spec["country:alpha"].country, spec["country:alpha"].dot), ("subject", None))
        self.assertEqual((spec["capital:alpha"].country, spec["capital:alpha"].dot), ("context", (5.0, 5.0)))
        self.assertEqual((spec["city:alpha-port"].country, spec["city:alpha-port"].dot), ("context", (1.0, 1.0)))
        for key in ("territory:gamma", "dispute:delta"):
            self.assertEqual((spec[key].country, spec[key].outline), ("subject", "dashed"))

    def test_dot_cards_draw_their_country(self) -> None:
        with data(countries(), territories(), cities_data()):
            _, shape, context, former = self.cards["city:alpha-port"].render.resolve()
        self.assertTrue(shape.equals(box(0, 0, 10, 10)))
        self.assertEqual((context, former), ((), None))

    def test_unsafe_text_is_rejected(self) -> None:
        bad = countries()
        bad[0]["name"] = "Alpha <b>"
        with data(bad), self.assertRaises(ValidationError):
            political.load_countries()
        for name in ("Alpha\r---\rB", "Alpha\u2028B", "{{c1::Alpha}}"):
            with self.subTest(name=name), self.assertRaises(ValidationError):
                Country.model_validate(countries()[0] | {"name": name})

    def test_placement_comes_from_the_curriculum(self) -> None:
        self.assertEqual([(c.region, c.host) for c in self.countries], [(1, None), (2, None)])
        for model, entry in ((Country, countries()[0]), (Territory, territories()[0]), (Dispute, territories()[1])):
            for field in ("region", "host"):
                with self.subTest(model=model.__name__, field=field), self.assertRaises(ValidationError):
                    model.model_validate(entry | {field: 1 if field == "region" else "alpha"})
        with data(countries()), mock.patch.dict(PLACEMENTS, clear=True), \
                self.assertRaisesRegex(ValueError, "countries.yaml: not placed in any region of curriculum.yaml: alpha, beta"):
            political.load_countries()
        with self.assertRaisesRegex(ValueError, "not placed"):
            Country.model_validate(countries()[0]).region
        with data(countries(), territories()), mock.patch.dict(PLACEMENTS):
            del PLACEMENTS["gamma"]
            self.assertEqual(political.check()[0], ["territories.yaml: not placed in any region of curriculum.yaml: gamma"])
            with self.assertRaisesRegex(ValueError, "territories.yaml: not placed"):
                political.cards()
        with data(countries(), territories(), [cities_data()[0] | {"anchor": "nile"}]), mock.patch.dict(PLACEMENTS), \
                mock.patch.object(cities, "feature_region", side_effect=AssertionError("political failed: no region rule")):
            del PLACEMENTS["gamma"]
            self.assertEqual(cities.check(political.check()[1]), [])
        with data(countries(), territories()), mock.patch.dict(PLACEMENTS, {"gamma": RingPlace(3, None, "dispute")}):
            self.assertEqual(political.check()[0], ["gamma: a territory that curriculum.yaml places as a dispute"])
        with data(countries(), territories()[1:]), \
                mock.patch.object(polities, "curriculum_placements", lambda states: PLACEMENTS):
            self.assertEqual(political.check()[0],
                             ["curriculum.yaml: places what territories.yaml has no entry for: gamma"])

    def test_bbox_must_be_finite_and_in_range(self) -> None:
        for expect in ([float("-inf"), 0, 10, 10], [0, 0, 190, 10], [0, -91, 10, 10]):
            with self.subTest(expect=expect), self.assertRaises(ValidationError):
                Country.model_validate(countries()[0] | {"expect": expect})


class NullCapitalTest(unittest.TestCase):
    def test_no_capital_card(self) -> None:
        with data(countries()):
            self.assertEqual([c.key for c in political.cards()], ["country:alpha", "capital:alpha", "country:beta"])

    def test_uid_slots_follow_the_capital(self) -> None:
        null_with_slot = countries()[1] | {"uids": {"country": "CountryBBB", "capital": None}}
        with self.assertRaises(ValidationError):
            Country.model_validate(null_with_slot)
        capital_without_slot = countries()[0] | {"uids": {"country": "CountryAAA"}}
        with self.assertRaises(ValidationError):
            Country.model_validate(capital_without_slot)

    def test_capital_needs_one_source(self) -> None:
        entry = countries()[0]
        entry["capital"] = entry["capital"] | {"file": "yaren.geojson"}
        with self.assertRaises(ValidationError):
            Country.model_validate(entry)

    def test_unminted_uid(self) -> None:
        entry = countries()[0]
        entry["uids"]["capital"] = None
        with data([entry]), self.assertRaisesRegex(ValueError, "alpha capital: no uid"):
            political.cards()


class PartiesTest(unittest.TestCase):
    names = {"alpha": "argentina", "beta": "United Kingdom", "gamma": "Eagle"}

    def dispute(self, parties: list) -> Dispute:
        return Dispute.model_validate(territories()[1] | {"parties": parties})

    def test_alphabetical_ignoring_case_and_accents(self) -> None:
        self.assertEqual(self.dispute(["beta", "alpha"]).parties_line(self.names), "Disputed: argentina, United Kingdom")
        self.assertEqual(self.dispute([{"label": "Zeta"}, {"label": "Éire"}, "gamma"]).parties_line(self.names),
                         "Disputed: Eagle, Éire, Zeta")

    def test_at_least_two_distinct(self) -> None:
        for parties in (["alpha"], ["alpha", "alpha"], [{"label": "X"}, {"label": "X"}]):
            with self.subTest(parties=parties), self.assertRaises(ValidationError):
                self.dispute(parties)
        with self.assertRaisesRegex(ValueError, "party names repeat"):
            self.dispute(["beta", {"label": "united kingdom"}]).parties_line(self.names)

    def test_party_refs_must_be_countries(self) -> None:
        with self.assertRaisesRegex(ValueError, r"parties \['omega'\] are not countries"):
            self.dispute(["alpha", "omega"]).parties_line(self.names)
        with self.assertRaises(ValidationError):
            self.dispute(["alpha", "Polisario Front"])  # free text needs {label: ...}


class UniquenessTest(unittest.TestCase):
    def test_duplicate_uid_across_sources(self) -> None:
        clash = cities_data()
        clash[0]["uid"] = "CountryAAA"
        with data(countries(), territories(), clash) as paths:
            self.assertEqual(ids.duplicate_uids(list(paths.values())), ["CountryAAA"])
            with mock.patch.object(sources, "MODULES", (political, cities)), \
                    self.assertRaisesRegex(ValueError, "duplicate card uid"):
                sources.all_cards()

    def test_duplicate_ids_within_a_file(self) -> None:
        with data(countries() + [countries()[1] | {"uids": {"country": "CountryCCC"}}]), \
                self.assertRaisesRegex(ValueError, "duplicate country id"):
            political.load_countries()
        clash = territories()
        clash[1]["id"] = "gamma"
        with data(territories=clash), self.assertRaisesRegex(ValueError, "duplicate territory or dispute id"):
            polities.load_territories()

    def test_two_kinds_share_an_id(self) -> None:
        city = cities_data()[0] | {"id": "alpha"}
        with data(countries(), cities_=[city]):
            keys = [c.key for c in political.cards() + cities.cards()]
        self.assertEqual(len(keys), len(set(keys)))

    def test_mint_fills_nested_slots(self) -> None:
        entries = countries()
        entries[0]["uids"] = {"country": "CountryAAA", "capital": None}
        with data(entries, cities_=[cities_data()[0] | {"uid": None}]) as paths, \
                mock.patch.object(ids, "mint", side_effect=["MintedAAAA", "MintedBBBB"]):
            self.assertEqual(ids.mint_missing([paths["countries"], paths["cities"]]), 2)
            self.assertEqual(political.load_countries()[0].uids["capital"], "MintedAAAA")
            self.assertEqual(cities.load_cities()[0].uid, "MintedBBBB")


class CheckTest(unittest.TestCase):
    def test_clean(self) -> None:
        with data(countries(), territories(), cities_data()):
            errors, outlines = political.check()
            self.assertEqual(errors + cities.check(outlines), [])
        self.assertEqual(set(outlines), {"alpha", "beta"})

    def test_no_files_no_cards(self) -> None:
        with data():
            self.assertEqual(political.cards() + cities.cards(), [])
            self.assertEqual(political.check(), ([], {}))
            self.assertEqual(cities.check({}), [])

    def test_city_outside_its_country(self) -> None:
        city = cities_data()[0] | {"ne_id": 103, "expect": [14, 4, 16, 6]}
        with data(countries(), cities_=[city]):
            errors = cities.check(political.check()[1])
        self.assertEqual(errors, ["alpha-port: point (15.000, 5.000) is outside alpha's outline"])

    def test_capital_outside_its_country(self) -> None:
        entry = countries()[0]
        entry["capital"] |= {"ne_id": 103, "expect": [14, 4, 16, 6]}
        with data([entry]):
            self.assertEqual(political.check()[0], ["alpha capital: point (15.000, 5.000) is outside alpha's outline"])

    def test_unknown_city_country(self) -> None:
        with data(countries(), cities_=[cities_data()[0] | {"country": "omega"}]):
            self.assertEqual(cities.check(political.check()[1]), ["alpha-port: country 'omega' is not in countries.yaml"])
            with self.assertRaisesRegex(ValueError, "omega"):
                cities.cards()

    def test_unknown_references(self) -> None:
        bad = territories()
        bad[0] |= {"sovereign": "omega"}
        bad[1]["parties"] = ["alpha", "omega"]
        with data(countries(), bad):
            self.assertEqual(political.check()[0], [
                "gamma: sovereign 'omega' is not a country",
                "delta: parties ['omega'] are not countries (use `{label: ...}` for a non-state party)",
            ])

    def test_city_anchor_pass(self) -> None:
        cases = {("atlantic-ocean", "core"): "pass orientation", ("lake-baikal", "secondary"): None}
        tier3 = next(f.id for f in load_features() if f.tier == 3 and not f.retired)
        cases[(tier3, "core")] = "is in pass 2, the city in pass 1"
        cases[(tier3, "secondary")] = None
        for (anchor, tier), error in cases.items():
            with self.subTest(anchor=anchor, tier=tier), \
                    data(countries(), cities_=[cities_data()[0] | {"anchor": anchor, "tier": tier}]):
                errors = cities.check(political.check()[1])
                if error:
                    self.assertIn(error, errors[0])
                else:
                    self.assertEqual(errors, [])

    def test_city_anchor(self) -> None:
        with data(countries(), cities_=[cities_data()[0] | {"anchor": "nile"}]):
            self.assertEqual(cities.check(political.check()[1]), [])
            self.assertEqual(cities.cards()[0].anchor, "feature:nile")
        with data(countries(), cities_=[cities_data()[0] | {"anchor": "atlantis"}]):
            self.assertEqual(cities.check(political.check()[1]), ["alpha-port: anchor 'atlantis' is not an active feature"])
        with data(countries(), cities_=[cities_data()[0] | {"anchor": "nile"}]), mock.patch.dict(FEATURE_REGIONS, {"nile": 10}):
            self.assertEqual(cities.check(political.check()[1]), ["alpha-port: anchor 'nile' is in region 10, alpha in region 1"])

    def test_expect_and_point_box(self) -> None:
        entry = countries()[0]
        entry["expect"] = [0, 0, 9, 10]
        entry["capital"] |= {"expect": [0, 0, 1, 1]}
        with data([entry]):
            errors = political.check()[0]
        self.assertEqual(len(errors), 1)
        self.assertIn("outside expected bbox", errors[0])
        entry = countries()[0]
        entry["capital"] |= {"expect": [0, 0, 1, 1]}
        with data([entry]), self.assertRaisesRegex(ValueError, "alpha capital: point .* outside expected bbox"):
            by_key(political.cards())["capital:alpha"].render.resolve()

    def test_composition(self) -> None:
        entry = countries()[0]
        entry["geometry"] = [a0(1), {"layer": DA, "select": {"ne_id": 4}, "subtract": True}, {"layer": DA, "select": {"ne_id": 6}}]
        entry["expect"] = [0, 0, 12, 10]
        with data([entry]):
            errors, outlines = political.check()
        self.assertEqual(errors, [])
        self.assertAlmostEqual(outlines["alpha"].area, 100 - 4 + 4)
        entry["geometry"] = [a0(1), {"layer": DA, "select": {"ne_id": 6}, "subtract": True}, {"layer": DA, "select": {"ne_id": 4}}]
        with data([entry]):
            errors = political.check()[0]
        self.assertEqual(len(errors), 2)
        self.assertIn("subtracted part {'ne_id': 6} is only", errors[0])
        self.assertIn("added part {'ne_id': 4} overlaps the base", errors[1])


class OutlineTest(unittest.TestCase):
    def test_mainland_drops_overseas_parts(self) -> None:
        with mock.patch.object(resolve, "layer", LAYERS.__getitem__):
            shape = outline("x", [Part(**a0(5))], expect=(0, 0, 10, 10), mainland=(-1, -1, 11, 11))
            self.assertTrue(shape.equals(box(0, 0, 10, 10)))
            with self.assertRaisesRegex(ValueError, "outside expected bbox"):
                outline("x", [Part(**a0(5))], expect=(0, 0, 10, 10))

    def test_bbox_across_180(self) -> None:
        fiji = MultiPolygon([box(177, -19, 180, -16), box(-180, -19, -179, -16)])
        self.assertTrue(in_bbox(fiji, (176, -20, -178, -15)))
        self.assertFalse(in_bbox(fiji, (-178, -20, 176, -15)))
        self.assertFalse(in_bbox(fiji, (177, -20, 180, -15)))


class EdgeCaseTest(unittest.TestCase):
    def test_zero_area_part(self) -> None:
        entry = countries()[0]
        entry["geometry"] = [a0(1), {"layer": political.PLACES, "select": {"ne_id": 102}}]
        with data([entry]):
            self.assertIn("has no area", political.check()[0][0])

    def test_empty_select(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty select"):
            outline("x", [Part(layer=A0, select={})], expect=(0, 0, 10, 10))

    def test_city_that_is_its_capital(self) -> None:
        with data(countries(), cities_=[cities_data()[0] | {"ne_id": 101, "expect": [4, 4, 6, 6]}]):
            self.assertEqual(cities.check(political.check()[1]), ["alpha-port: is alpha's capital, which has a capital card"])

    def test_bad_yaml_and_kind(self) -> None:
        with data(territories=[{"kind": "colony", "id": "x"}]), self.assertRaisesRegex(ValueError, "`kind` must be"):
            polities.load_disputes()
        with data() as paths:
            paths["countries"].write_text("- id: [unclosed\n")
            self.assertIn("countries.yaml", political.check()[0][0])

    def test_hand_placed_capital(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "yaren.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"source": "test", "method": "reference-coords", "refs": ["test"]},
                 "geometry": {"type": "Point", "coordinates": [3, 3]}}]}))
            entry = countries()[0]
            entry["capital"] = {"name": "Yaren", "file": "yaren.geojson", "expect": [2, 2, 4, 4]}
            with data([entry]), mock.patch.object(resolve, "GEOMETRY", Path(tmp)):
                self.assertEqual(by_key(political.cards())["capital:alpha"].render.resolve()[0].dot, (3.0, 3.0))
                self.assertEqual(political.check()[0], [])

    def test_ne_id_must_match_one_row(self) -> None:
        entry = countries()[0]
        entry["capital"] |= {"ne_id": 999}
        with data([entry]), self.assertRaisesRegex(ValueError, "ne_id 999 matched 0 rows"):
            by_key(political.cards())["capital:alpha"].render.resolve()


class PassTest(unittest.TestCase):
    def test_rules(self) -> None:
        self.assertEqual(study_pass("feature", 1), 1)
        self.assertEqual(study_pass("feature", 3), 2)
        self.assertEqual(study_pass("feature", 1, orientation=True), "orientation")
        self.assertEqual(study_pass("country", 3), 1)
        self.assertEqual(study_pass("capital", 3), 1)
        self.assertEqual(study_pass("city", 2), 1)
        self.assertEqual(study_pass("city", 3), 2)
        self.assertEqual(study_pass("continent", 1), "orientation")
        self.assertEqual(sorted(["orientation", 2, 1], key=PASS_ORDER.__getitem__), ["orientation", 1, 2])

    def test_feature_cards(self) -> None:
        cards = by_key(features_source.cards())
        orientation = {c.id for c in cards.values() if c.study_pass == "orientation"}
        self.assertEqual(orientation, {"atlantic-ocean", "pacific-ocean", "indian-ocean", "arctic-ocean", "trade-winds", "westerlies",
                                       "africa", "antarctica", "asia", "europe", "north-america", "oceania", "south-america"})
        for c in cards.values():
            self.assertEqual(c.study_pass, "orientation" if c.id in orientation else 1 if c.tier <= 2 else 2)
            self.assertIn(pass_tag(c.study_pass), c.tags)

    def test_tag_must_match(self) -> None:
        card = by_key(features_source.cards())["feature:nile"]
        with self.assertRaisesRegex(ValidationError, "needs exactly the tag pass::1"):
            Card(**dict(card) | {"tags": card.tags[:-1]})


class TextRulesTest(unittest.TestCase):
    def test_line_breaks_and_cloze_are_rejected_everywhere(self) -> None:
        for text in ("a\rb", "a\u2028b", "a\x00b", "{{c1::a}}", "a\u202eb", "a\u200bb", "a\x90b", "a\ufeffb"):
            with self.subTest(text=text):
                with self.assertRaises(ValidationError):
                    Feature.model_validate(feature_entry() | {"name": text})
                with self.assertRaises(ValidationError):
                    Country.model_validate(countries()[0] | {"note": text})

    def test_notes(self) -> None:
        Country.model_validate(countries()[0] | {"note": "The *kamikaze* wind, 1274."})  # emphasis is fine
        for note in ("![](https://x/y.png)", "[x](https://x)", "<b>", "`code`", "# Heading"):
            with self.subTest(note=note), self.assertRaises(ValidationError):
                Country.model_validate(countries()[0] | {"note": note})


class LazyDotTest(unittest.TestCase):
    def test_building_cards_reads_no_points(self) -> None:
        layers = {k: v for k, v in LAYERS.items() if k != political.PLACES}
        with data(countries(), territories(), cities_data()), mock.patch.object(polities, "layer", layers.__getitem__):
            built = by_key(political.cards() + cities.cards())
            self.assertIsNone(built["capital:alpha"].render.spec.dot)
            with self.assertRaises(KeyError):
                built["capital:alpha"].render.resolve()

    def test_a_card_without_a_dot_keeps_its_spec(self) -> None:
        card = by_key(features_source.cards())["feature:nile"]
        self.assertIs(card.render.resolve()[0], card.render.spec)


class WiringTest(unittest.TestCase):
    def test_sources_registered(self) -> None:
        self.assertEqual(sources.MODULES[1:], (political, cities))

    def test_missing_files_are_left_out_of_paths(self) -> None:
        with mock.patch.object(Path, "exists", lambda p: p.name == "features.yaml"):
            self.assertEqual([p.name for p in importlib.reload(sources).PATHS], ["features.yaml"])
        importlib.reload(sources)


if __name__ == "__main__":
    unittest.main()
