import html
import unittest

from shapely.geometry import box

from geofeat.card import Card, RenderRef
from geofeat.deckgen import card
from geofeat.model import Expect, Feature, Part
from geofeat.sources.features import card as feature_card
from geofeat.spec import RenderSpec


def feature(**extra) -> Feature:
    fields = dict(id="bosporus", uid="MAPQnshVtc", name="Bosporus", type="Strait", category="Straits & Chokepoints",
                  tier=1, style="strait", geometry=[Part(file="x.geojson")], expect=Expect(bbox=(28, 40, 30, 42)))
    return Feature(**(fields | extra))


def legacy_card(f: Feature, image: str) -> str:
    """deckgen.card as it was before the Card DTO (a88f402), less its tags, which gained kind::feature."""
    answer = f.name + (f" ({', '.join(f.alt_names)})" if f.alt_names else "")
    return f"---\n\n**{html.escape(f.type_text)}**<br>![]({image}) ::: {html.escape(answer)}\n\n---\n[^uid]: {f.uid}\n"


class FeatureCardTest(unittest.TestCase):
    def test_text_is_unchanged(self) -> None:
        for f in (feature(), feature(name="Bab-el-Mandeb & Co", alt_names=["Gate of Tears", "Bab al-Mandab"]),
                  feature(type="Wind system", qualifier="July", style="flow-wind", category="Climate Systems")):
            with self.subTest(f.name):
                self.assertTrue(card(feature_card(f), "abc.png").startswith(legacy_card(f, "abc.png")))

    def test_single_line_answer_has_no_break(self) -> None:
        text = card(feature_card(feature(alt_names=["İstanbul Boğazı"])), "abc.png")
        self.assertIn("::: Bosporus (İstanbul Boğazı)\n", text)
        self.assertNotIn("<br>", text.split(":::")[1])

    def test_card_carries_its_tags(self) -> None:
        text = card(feature_card(feature()), "abc.png")
        self.assertIn("[^uid]: MAPQnshVtc\n[^tag]: tier::1\n[^tag]: category::straits-chokepoints\n"
                      "[^tag]: id_bosporus\n[^tag]: kind::feature\n", text)

    def test_pos_only_when_given(self) -> None:
        c = feature_card(feature())
        self.assertNotIn("[^pos]", card(c, "abc.png"))
        self.assertTrue(card(c, "abc.png", 1500).endswith("[^tag]: kind::feature\n[^pos]: 1500\n"))


class AnswerLinesTest(unittest.TestCase):
    def test_lines_are_escaped_then_joined(self) -> None:
        c = Card(uid="AAAAAAAAAA", kind="capital", id="paris", prompt="Capital", answer_lines=("Paris", "Capital of France & 'co'"),
                 tags=(), tier=1, render=RenderRef(spec=RenderSpec(style="point"), geometry=lambda: (box(0, 0, 1, 1), (), None)))
        self.assertIn("::: Paris<br>Capital of France &amp; &#x27;co&#x27;\n", card(c, "abc.png"))

    def test_markdown_is_rejected(self) -> None:
        for text in ("Alps![](/etc/passwd)", "[x](javascript:alert(1))", "a ::: b", "*bold*", "line\nbreak"):
            with self.subTest(text), self.assertRaises(ValueError):
                Card(uid="AAAAAAAAAA", kind="city", id="x", prompt="City", answer_lines=(text,), tags=(), tier=1,
                     render=RenderRef(spec=RenderSpec(style="point"), geometry=lambda: (box(0, 0, 1, 1), (), None)))


if __name__ == "__main__":
    unittest.main()
