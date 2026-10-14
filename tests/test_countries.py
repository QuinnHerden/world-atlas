import unittest

from ruamel.yaml import YAML

from geofeat.countries_ne import LAYERS, SOURCES
from geofeat.curriculum import load_curriculum
from geofeat.sources.political import COUNTRIES

TAGS = {name: tag for tag, name in LAYERS.items()}


def recipe(geometry: list[dict]) -> str:
    """A countries.yaml geometry list written as a countries_ne recipe: `A0 <id> + DA <id> - DA <id>`."""
    terms = [f"{'-' if p.get('subtract') else '+'} {TAGS[p['layer']]} {p['select']['ne_id']}" for p in geometry]
    return " ".join(terms)[2:]


class CountriesDataTest(unittest.TestCase):
    """data/countries.yaml mirrors countries_ne.SOURCES, which adjacency and regions still read."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = YAML(typ="safe").load(COUNTRIES)

    def test_same_states(self) -> None:
        self.assertEqual(sorted(e["id"] for e in self.entries), sorted(SOURCES))

    def test_geometry_matches_recipes(self) -> None:
        for e in self.entries:
            with self.subTest(country=e["id"]):
                self.assertTrue(all(set(p) <= {"layer", "select", "subtract"} and set(p["select"]) == {"ne_id"}
                                    for p in e["geometry"]))
                self.assertFalse(e["geometry"][0].get("subtract"))
                self.assertEqual(recipe(e["geometry"]), SOURCES[e["id"]])

    def test_every_state_in_the_curriculum(self) -> None:
        load_curriculum([e["id"] for e in self.entries])


if __name__ == "__main__":
    unittest.main()
