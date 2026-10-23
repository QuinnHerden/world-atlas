"""World Flags (ADR 0012): the flag source, its cards and deck, the study order and look-alike spacing, and the SVGs."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pydantic import ValidationError

import geofeat.positions as positions
from geofeat import flagfiles
from geofeat.card import Card
from geofeat import deckgen
from geofeat.card import image_name
from geofeat.deckgen import FLAG_BORDER, front
from geofeat.decks import BY_SLUG, DECKS, FLAGS, WORLD
from geofeat.order import flags as order
from geofeat.order.engine import LOOKALIKE_GAP
from geofeat.polities import read_countries, read_territory_file
from geofeat.sources import flags

SVG = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 3 2">{}</svg>'


class DeckTest(unittest.TestCase):
    def test_registry(self) -> None:
        self.assertIs(DECKS[-1], FLAGS)
        self.assertEqual((FLAGS.name, FLAGS.slug, FLAGS.base, FLAGS.limit, FLAGS.block),
                         ("World Flags", "world-flags", 800_000, 950_000, "flags"))
        self.assertIs(BY_SLUG["world-flags"], FLAGS)

    def test_a_flag_is_only_ever_in_world_flags(self) -> None:
        base = dict(uid="AAAAAAAAAA", kind="flag", id="x", prompt="Flag", answer_lines=("X",), tier=1,
                    tags=("block::flags",), image=flagfiles.flag_file("france"))
        Card(deck="World Flags", **base)
        for deck in (WORLD.name, "US States"):
            with self.subTest(deck), self.assertRaises(ValidationError):
                Card(deck=deck, **base)
        with self.assertRaises(ValidationError):  # a card has a map or an image, not neither
            Card(deck="World Flags", **{**base, "image": None})

    def test_lock_entries(self) -> None:
        positions.Entry(800_500, "flags", None, "world-flags")
        for bad in ((800_500, "flags", None, "world-atlas"), (800_500, "subdivisions", None, "world-flags"),
                    (800_500, "flags", 3, "world-flags"), (500, "flags", None, "world-flags"),
                    (800_500, "countries", 3, "world-flags")):
            with self.subTest(bad), self.assertRaises(ValueError):
                positions.Entry(*bad)


class DataTest(unittest.TestCase):
    """The committed data."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cards = flags.cards()
        cls.territories = {e.id for e in read_territory_file() if e.kind == "territory" and not e.retired}

    def test_the_data_checks(self) -> None:
        self.assertEqual(flags.check(), [])
        self.assertEqual(order.errors(), [])
        self.assertEqual(flags.continent_notes(), [])

    def test_count(self) -> None:
        countries = {c.id for c in read_countries()}
        self.assertEqual(len(countries), 197)
        kinds = [f.kind for f in flags.active()]
        self.assertEqual(kinds.count("country"), 197)
        self.assertEqual(len(self.cards), 197 + len(self.territories) - len(flags.excluded()))
        self.assertEqual(len(self.cards), 217)

    def test_every_card_has_a_clean_flag_file(self) -> None:
        for card in self.cards:
            with self.subTest(card.id):
                self.assertTrue(card.image.is_file())
                self.assertEqual(flagfiles.errors(card.image.read_text()), [])

    def test_every_territory_flag_has_a_reason_to_exist(self) -> None:
        for f in flags.active():
            if f.kind == "territory":
                self.assertTrue(f.reason, f.id)
        self.assertEqual(set(flags.excluded()) | {f.id for f in flags.active() if f.kind == "territory"},
                         self.territories)
        self.assertTrue(all(flags.excluded().values()))
        self.assertIn("akrotiri-and-dhekelia", flags.excluded())  # it flies the Union Flag

    def test_no_subnationals_or_disputes(self) -> None:
        others = {e.id for e in read_territory_file() if e.kind in ("subnational", "dispute")}
        self.assertFalse(others & {f.id for f in flags.active()})

    def test_cards(self) -> None:
        card = next(c for c in self.cards if c.id == "gibraltar")
        self.assertEqual((card.kind, card.key, card.deck, card.block, card.answer_lines), (
            "flag", "flag:gibraltar", "World Flags", "flags", ("Gibraltar",)))
        self.assertEqual(card.tags, ("id_flag_gibraltar", "continent::europe", "kind::flag", "block::flags",
                                     "territory::gibraltar"))
        self.assertIn("country::turkey", next(c for c in self.cards if c.id == "turkey").tags)

    def test_continent_order(self) -> None:
        tags = [next(t for t in c.tags if t.startswith("continent::")).removeprefix("continent::") for c in self.cards]
        runs = [t for i, t in enumerate(tags) if i == 0 or tags[i - 1] != t]
        self.assertEqual(runs, ["europe", "asia", "africa", "north-america", "south-america", "oceania"])

    def test_edge_cases(self) -> None:
        continent = order.continents()
        self.assertEqual(continent, {i: c for i, c in flags.world_continents().items() if i in continent})
        self.assertEqual({i: continent[i] for i in ("russia", "turkey", "kazakhstan", "egypt", "panama", "greenland",
                                                    "aruba", "puerto-rico", "cyprus", "british-indian-ocean-territory")},
                         {"russia": "europe", "turkey": "asia", "kazakhstan": "asia", "egypt": "africa",
                          "panama": "north-america", "greenland": "north-america", "aruba": "north-america",
                          "puerto-rico": "north-america", "cyprus": "asia", "british-indian-ocean-territory": "africa"})

    def test_look_alikes_on_one_continent_are_spaced(self) -> None:
        same = [(a, b, d) for a, b, d, same in order.gaps([f.id for f in flags.active()]) if same]
        self.assertGreater(len(same), 20)
        for a, b, d in same:
            self.assertTrue(LOOKALIKE_GAP[0] <= d <= LOOKALIKE_GAP[1], f"{a} ~ {b}: {d} apart")

    def test_within_a_continent_world_atlas_order_with_few_moves(self) -> None:
        listed = [f.id for f in flags.active()]
        natural = order.world_order(listed)
        continent = order.continents()
        moved = [i for c in flags.CONTINENTS for i in order.moved([x for x in listed if continent[x] == c],
                                                                  [x for x in natural if continent[x] == c])]
        self.assertLess(len(moved), 30, moved)


    def test_locked_flags_are_listed_in_lock_order(self) -> None:
        placed = order.locked()
        self.assertEqual(len(placed), 217)
        listed = [f.id for f in flags.active()]
        self.assertEqual(sorted(listed, key=placed.get), listed)
        self.assertEqual(min(placed.values()), 800_500)

    def test_a_retired_place_is_an_error_not_a_crash(self) -> None:
        with self.assertRaises(ValueError):
            flags.card(flags.Flag(id="atlantis", uid="AAAAAAAAAA", kind="country", continent="europe"))


class LockOrderTest(unittest.TestCase):
    def test_reordered(self) -> None:
        self.assertEqual(order.reordered(["a", "x", "b", "c"], {"a": 1, "b": 3, "c": 2}), ["c"])
        self.assertEqual(order.reordered(["a", "x", "b"], {"a": 1, "b": 3}), [])

    def test_a_frozen_gap_is_a_note_and_a_new_one_an_error(self) -> None:
        flag = lambda id: flags.Flag(id=id, uid=None, kind="country", continent="europe")
        listed = [flag(i) for i in ("norway", "iceland", "a", "b", "c")]
        with mock.patch.object(flags, "active", lambda: listed), mock.patch.object(order, "locked", lambda: {}):
            self.assertTrue([e for e in order.errors() if "norway and iceland" in e])
        with mock.patch.object(flags, "active", lambda: listed), \
                mock.patch.object(order, "locked", lambda: {"norway": 1, "iceland": 2}):
            self.assertFalse([e for e in order.errors() if "norway and iceland" in e])
            self.assertTrue(order.notes())

    def test_rewrite_keeps_the_header_and_puts_retired_last(self) -> None:
        text = "# a\n# b\n- id: b\n  kind: country\n- id: r\n  retired: true\n- id: a\n  kind: country\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "flags.yaml"
            path.write_text(text)
            retired = flags.Flag(id="r", kind="country", continent="europe", retired=True)
            with mock.patch.object(flags, "PATH", path), mock.patch.object(flags, "load_flags", lambda: (retired,)), \
                    mock.patch.object(order, "locked", lambda: {}):
                order.rewrite(["a", "b"])
            self.assertEqual(path.read_text(), "# a\n# b\n- id: a\n  kind: country\n- id: b\n  kind: country\n"
                                               "- id: r\n  retired: true\n")

    def test_rewrite_never_reorders_locked_flags(self) -> None:
        with mock.patch.object(order, "locked", lambda: {"a": 1, "b": 2}), self.assertRaises(SystemExit):
            order.rewrite(["b", "a"])


class SpacingTest(unittest.TestCase):
    def test_space_moves_the_fewest(self) -> None:
        ids = list("abcdefghij")
        spaced = order.space(ids, [("a", "b")])
        self.assertEqual(order._cost(spaced, [("a", "b")], {x: i for i, x in enumerate(ids)})[0], 0)
        self.assertEqual(len(order.moved(spaced, ids)), 1)

    def test_too_far_is_pulled_in(self) -> None:
        ids = [str(i) for i in range(20)]
        spaced = order.space(ids, [("0", "19")])
        self.assertTrue(LOOKALIKE_GAP[0] <= abs(spaced.index("0") - spaced.index("19")) <= LOOKALIKE_GAP[1])

    def test_moved(self) -> None:
        self.assertEqual(order.moved(list("acdbe"), list("abcde")), ["b"])
        self.assertEqual(order.moved(list("abc"), list("abc")), [])


class SanitiseTest(unittest.TestCase):
    def test_refused(self) -> None:
        for bad in ("<script>alert(1)</script>", '<rect onload="x()"/>', "<foreignObject/>", '<image href="x.png"/>',
                    '<use xlink:href="http://example.com/a.svg#x"/>', '<use href="other.svg#x"/>',
                    '<rect style="fill:url(http://example.com/x)"/>', '<rect fill="url( \'http://e.com/x\')"/>',
                    "<style>@import 'x.css';</style>", "<a/>", "<animate/>", "<set/>", '<rect frobnicate="1"/>',
                    '<rect style="fill:\\75 rl(x)"/>', "<style>a{}<g/>@import url(http://e/x.css);</style>",
                    "<rect style=\"mask-image:image-set('https://e/x.png' 1x)\"/>", '<rect style="mask:src(x)"/>',
                    "<style>.a{mask:cross-fade(x)}</style>"):
            with self.subTest(bad), self.assertRaises(flagfiles.UnsafeSvg):
                flagfiles.sanitise(SVG.format(bad).encode())
        with self.assertRaises(flagfiles.UnsafeSvg):
            flagfiles.sanitise(b'<!DOCTYPE svg [<!ENTITY a "b">]>' + SVG.format("").encode())
        with self.assertRaises(flagfiles.UnsafeSvg):
            flagfiles.sanitise(b'<svg xmlns="http://www.w3.org/2000/svg"/>')  # no viewBox and no size

    def test_kept_dropped_and_sized(self) -> None:
        text = SVG.format('<title>t</title><metadata><x/></metadata><defs><path id="p" d="M0 0h1"/></defs>'
                          '<use xlink:href="#p" fill="url(#g)"/>').replace("<svg ", '<svg width="9" ')
        out = flagfiles.sanitise(text.encode())
        self.assertNotIn("title", out)
        self.assertNotIn("metadata", out)
        self.assertIn('xlink:href="#p"', out)
        self.assertIn('width="600" height="400"', out)
        self.assertEqual(flagfiles.errors(out), [])
        self.assertEqual(flagfiles.sanitise(out.encode()), out)

    def test_the_svg_doctype_is_dropped_and_any_other_refused(self) -> None:
        doctype = b'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'
        self.assertNotIn("DOCTYPE", flagfiles.sanitise(doctype + SVG.format("").encode()))
        with self.assertRaises(flagfiles.UnsafeSvg):
            flagfiles.sanitise(doctype.replace(b">", b' [<!ENTITY a "b">]>', 1) + SVG.format("").encode())

    def test_a_size_without_a_viewbox(self) -> None:
        out = flagfiles.sanitise(b'<svg xmlns="http://www.w3.org/2000/svg" width="1e3px" height="500"/>')
        self.assertIn('viewBox="0 0 1000 500" width="800" height="400"', out)

    def test_errors_on_a_wrong_size(self) -> None:
        self.assertTrue(flagfiles.errors(SVG.format("").replace("<svg ", '<svg width="1" height="1" ')))


class LockFileTest(unittest.TestCase):
    def test_the_committed_file_must_be_exactly_the_sanitised_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svg = flagfiles.sanitise(SVG.format('<rect width="3" height="2"/>').encode())
            hidden = '<?xml-stylesheet type="text/css" href="https://e/x.css"?>' + svg
            self.assertEqual(flagfiles.errors(hidden), [])  # the parser hides it ...
            for text, bad in ((svg, False), (hidden, True)):
                (Path(tmp) / "x.svg").write_text(text)
                entry = {"id": "x", "repo": "o/r", "commit": "c" * 40, "path": "svg/x.svg",
                         "svg_sha256": hashlib.sha256(text.encode()).hexdigest()}
                (Path(tmp) / "sources.lock").write_text(json.dumps([entry]))
                with mock.patch.object(flagfiles, "FLAG_DIR", Path(tmp)), \
                        mock.patch.object(flagfiles, "LOCK", Path(tmp) / "sources.lock"):
                    self.assertEqual(bool(flagfiles.lock_errors(["x"])), bad)  # ... the round trip doesn't

    def test_lock_entries_name_safe_paths(self) -> None:
        for bad in ({"id": "../x"}, {"repo": "o/r?x=1"}, {"path": "svg/../../x.svg"}):
            with tempfile.TemporaryDirectory() as tmp, self.subTest(bad):
                entry = {"id": "x", "repo": "o/r", "commit": "c" * 40, "path": "svg/x.svg"} | bad
                (Path(tmp) / "sources.lock").write_text(json.dumps([entry]))
                with mock.patch.object(flagfiles, "LOCK", Path(tmp) / "sources.lock"), self.assertRaises(ValueError):
                    flagfiles.read_lock()


class DeckgenTest(unittest.TestCase):
    def test_copy_images(self) -> None:
        cards = [c for c in flags.cards() if c.id in ("japan", "nepal")]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(deckgen, "DECK", Path(tmp)):
            (Path(tmp) / "stale.svg").write_text("x")
            (Path(tmp) / "map.png").write_text("x")
            japan = image_name(cards[1].image if cards[1].id == "japan" else cards[0].image)
            (Path(tmp) / japan).write_text("tampered")
            deckgen.copy_images(cards)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()),
                             sorted([image_name(c.image) for c in cards] + ["map.png"]))
            self.assertEqual(image_name(Path(tmp) / japan), japan)

    def test_the_front_is_the_flag_alone(self) -> None:
        cards = {c.id: c for c in flags.cards()}
        html = front(cards["japan"], "abc.svg")
        self.assertTrue(html.startswith('<img src="abc.svg" style="') and html.endswith('">'))
        self.assertIn(FLAG_BORDER, html)
        self.assertNotIn("Flag", html)
        self.assertNotIn(FLAG_BORDER, front(cards["nepal"], "abc.svg"))


if __name__ == "__main__":
    unittest.main()
