import unittest

from geofeat import countries_ne
from geofeat.polities import load_political


class CountriesDataTest(unittest.TestCase):
    """data/countries.yaml and data/territories.yaml against data/curriculum.yaml, and as countries_ne reads them."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.countries, cls.others = load_political()

    def test_every_entry_is_placed(self) -> None:
        self.assertEqual(len(self.countries), 197)
        self.assertEqual({o.id: (o.region, o.host) for o in self.others if o.id == "somaliland"},
                         {"somaliland": (9, "somalia")})
        self.assertEqual([(c.region, c.host) for c in self.countries if c.id == "andorra"], [(1, "spain")])

    def test_countries_ne_reads_the_yaml(self) -> None:
        self.assertEqual(countries_ne.state_ids(), sorted(c.id for c in self.countries))
        for entry in (*self.countries, *self.others):
            with self.subTest(id=entry.id):
                self.assertEqual(countries_ne.parts(entry.id), tuple(entry.geometry))


if __name__ == "__main__":
    unittest.main()
