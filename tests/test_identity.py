import contextlib
import re
import io
import json
import sqlite3
import subprocess
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from PIL import Image
from shapely.geometry import box

import geofeat.ids as ids
import geofeat.jobs as jobs
import geofeat.sources as sources
from geofeat.ankc import ankc_command, writes_pos
from geofeat.card import Card, RenderRef, id_tag, migrate_media
from geofeat.check import ankc_supported
from geofeat.deckgen import DECK_FILE, card
from geofeat.model import ROOT_DECK, load_features
from geofeat.spec import RenderSpec

FIXTURES = Path(__file__).parent / "fixtures"


def make_card(kind: str, id: str, uid: str, shape=box(0, 0, 1, 1)) -> Card:
    return Card(uid=uid, kind=kind, id=id, prompt=kind.title(), answer_lines=(id,), tags=(id_tag(kind, id), "pass::1"), tier=1,
                render=RenderRef(spec=RenderSpec(style="area"), geometry=lambda: (shape, (), None)))


class UidFreezeTest(unittest.TestCase):
    def test_feature_uids_never_change(self) -> None:
        """Every feature uid shipped before World Atlas, with its id. A uid is a note's identity in users'
        collections; renaming an id is allowed, but must be a deliberate edit to this fixture."""
        lines = [l.split() for l in (FIXTURES / "feature-uids-v1.txt").read_text().splitlines() if not l.startswith("#")]
        frozen = dict(lines)
        self.assertEqual(len(frozen), 166)
        current = {f.id: f.uid for f in load_features()}
        self.assertEqual({i: current.get(i) for i in frozen}, frozen)


class DeckIdentityTest(unittest.TestCase):
    """What an existing collection matches on when it imports World Atlas: note GUIDs (the uids, above) and the note
    type. The deck id is derived from the deck name, so it changed with the rename; that is expected (ADR 0007)."""

    DECK_ID = 168430863  # "World Atlas"; "Geographic Features" was 201983241

    def test_names(self) -> None:
        self.assertEqual(ROOT_DECK, "World Atlas")
        self.assertEqual(DECK_FILE.name, "world-atlas.md")

    @unittest.skipIf(ankc_supported(), "needs ankc 0.5 or 0.6")
    def test_package_keeps_the_note_type(self) -> None:
        expected = json.loads((FIXTURES / "ankc-qa-model-v1.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp) / "deck", Path(tmp) / "dist"
            src.mkdir()
            out.mkdir()
            Image.new("RGB", (1, 1)).save(src / "map.png")
            c = make_card("feature", "bosporus", "AAAAAAAAAA")
            (src / DECK_FILE.name).write_text(f"---\ndeck: \"{ROOT_DECK}\"\n---\n" + card(c, "map.png", 7 if writes_pos() else None))
            subprocess.run([*ankc_command(), "build", "--deck", ROOT_DECK, "--path", str(src), "--output", str(out)],
                           check=True, capture_output=True)
            self.assertEqual([p.name for p in out.iterdir()], ["world-atlas.apkg"])
            with zipfile.ZipFile(out / "world-atlas.apkg") as archive:
                archive.extract("collection.anki2", tmp)
            with contextlib.closing(sqlite3.connect(Path(tmp) / "collection.anki2")) as db:
                models = json.loads(db.execute("select models from col").fetchone()[0])
                decks = json.loads(db.execute("select decks from col").fetchone()[0])
                notes = db.execute("select guid, mid from notes").fetchall()
        self.assertEqual(notes, [("AAAAAAAAAA", expected["id"])])
        model = models[str(expected["id"])]
        self.assertEqual({"id": int(model["id"]), "name": model["name"], "type": model["type"],
                          "sortf": model["sortf"], "req": model["req"],
                          "fields": [f["name"] for f in model["flds"]],
                          "templates": [{k: t[k] for k in ("name", "ord", "qfmt", "afmt")} for t in model["tmpls"]],
                          "css": model["css"]},
                         {k: v for k, v in expected.items() if not k.startswith("_")})
        self.assertEqual({v["name"]: int(v["id"]) for v in decks.values() if v["name"] != "Default"}, {ROOT_DECK: self.DECK_ID})


    def test_retired_card_search_misses_active_cards(self) -> None:
        """The README's search for v1's retired passes, corridors and islands, which users bulk-delete, matches the type
        word on the card front; no active card may carry one of those words."""
        hits = [c.key for c in sources.all_cards() if re.search("island|pass|corridor", c.prompt, re.IGNORECASE)]
        self.assertEqual(hits, [])


class KeysByKindTest(unittest.TestCase):
    def test_id_tags(self) -> None:
        self.assertEqual(id_tag("feature", "georgia"), "id_georgia")
        self.assertEqual(id_tag("country", "georgia"), "id_country_georgia")

    def test_media_migration(self) -> None:
        self.assertEqual(migrate_media({"nile": "a.png", "country:niger": "b.png"}),
                         {"feature:nile": "a.png", "country:niger": "b.png"})

    def test_two_kinds_share_an_id(self) -> None:
        feature = make_card("feature", "georgia", "AAAAAAAAAA", box(0, 0, 1, 1))
        country = make_card("country", "georgia", "BBBBBBBBBB", box(40, 41, 46, 44))
        self.assertNotEqual(feature.key, country.key)
        with tempfile.TemporaryDirectory() as tmp:
            deck, build = Path(tmp) / "deck", Path(tmp) / "build"
            deck.mkdir()
            (deck / "stale0000000.png").write_bytes(b"old")

            def fake_render(job: jobs.RenderJob) -> str:
                file = f"{job.key()[:12]}.png"
                (deck / file).write_bytes(b"png")
                return file

            with mock.patch.multiple(jobs, DECK=deck, BUILD=build, CACHE=build / "cache.json",
                                     MEDIA_INDEX=build / "media.json", _render_to_file=fake_render), \
                    contextlib.redirect_stdout(io.StringIO()):
                media = jobs.render_cards([feature, country])
                self.assertEqual(set(media), {"feature:georgia", "country:georgia"})
                self.assertNotEqual(media["feature:georgia"], media["country:georgia"])
                self.assertEqual(json.loads((build / "media.json").read_text()), media)
                self.assertEqual({p.name for p in deck.glob("*.png")}, set(media.values()))  # one cleanup, all kinds
                with mock.patch.object(jobs, "_render_to_file", side_effect=AssertionError("re-rendered")):
                    self.assertEqual(jobs.render_cards([feature, country]), media)
                    self.assertEqual(set(jobs.render_cards([country])), {"country:georgia"})
                self.assertEqual({p.name for p in deck.glob("*.png")}, {media["country:georgia"]})

    def test_keys_and_uids_unique_across_sources(self) -> None:
        def module(*cards: Card) -> types.SimpleNamespace:
            return types.SimpleNamespace(cards=lambda: list(cards), PATH=None)

        ok = (module(make_card("feature", "georgia", "AAAAAAAAAA")), module(make_card("country", "georgia", "BBBBBBBBBB")))
        with mock.patch.object(sources, "MODULES", ok):
            self.assertEqual(len(sources.all_cards()), 2)
        for clash in ((module(make_card("feature", "a", "AAAAAAAAAA")), module(make_card("country", "b", "AAAAAAAAAA"))),
                      (module(make_card("country", "a", "AAAAAAAAAA")), module(make_card("country", "a", "BBBBBBBBBB")))):
            with mock.patch.object(sources, "MODULES", clash), self.assertRaises(ValueError):
                sources.all_cards()


class IdsTest(unittest.TestCase):
    def test_mint_missing_and_duplicates_across_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.yaml", Path(tmp) / "b.yaml"
            a.write_text("- id: x\n  name: X\n- id: y\n  uid: YYYYYYYYYY\n  name: Y\n")
            b.write_text("- id: z\n  name: Z\n  retired: true\n")
            minted = iter(["MMMMMMMMM1", "MMMMMMMMM2"])
            with mock.patch.object(ids, "mint", lambda: next(minted)):
                self.assertEqual(ids.mint_missing([a, b]), 2)
            self.assertEqual(a.read_text(), "- id: x\n  uid: MMMMMMMMM1\n  name: X\n- id: y\n  uid: YYYYYYYYYY\n  name: Y\n")
            self.assertEqual(b.read_text(), "- id: z\n  uid: MMMMMMMMM2\n  name: Z\n  retired: true\n")
            self.assertEqual(ids.duplicate_uids([a, b]), [])
            b.write_text("- id: z\n  uid: YYYYYYYYYY\n  retired: true\n")
            self.assertEqual(ids.duplicate_uids([a, b]), ["YYYYYYYYYY"])

    def test_nested_uids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.yaml", Path(tmp) / "b.yaml"
            a.write_text("- id: niger\n  uids:\n    country:\n    capital: CCCCCCCCCC\n- id: monaco\n  uids:\n    country:\n")
            b.write_text("- id: niger\n  uid: CCCCCCCCCC\n")
            minted = iter(["MMMMMMMMM1", "MMMMMMMMM2"])
            with mock.patch.object(ids, "mint", lambda: next(minted)):
                self.assertEqual(ids.mint_missing([a]), 2)
            self.assertEqual(a.read_text(), "- id: niger\n  uids:\n    country: MMMMMMMMM1\n    capital: CCCCCCCCCC\n"
                                            "- id: monaco\n  uids:\n    country: MMMMMMMMM2\n")
            self.assertEqual(ids.duplicate_uids([a, b]), ["CCCCCCCCCC"])


if __name__ == "__main__":
    unittest.main()
