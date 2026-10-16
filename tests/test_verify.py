import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from pydantic import ValidationError

import geofeat.check as check
import geofeat.sources as sources
from geofeat.check import Noted, noted, note_markers, verify_errors, verify_report
from geofeat.model import Verify
from geofeat.polities import Country, Dispute, Territory
from geofeat.sources.cities import City
from test_data import feature
from test_sources import cities_data, countries, data, territories

ITEM = {"claim": "Alpha is a republic.", "as_of": "2026-10"}


def rows() -> list[Noted]:
    return [
        Noted("country:alpha", "Big square.", [Verify(**ITEM), Verify(claim="Its capital is Alphaville.", as_of="2026-10-14",
                                                                       source="https://example.org/alpha")]),
        Noted("capital:alpha", "Middle.", []),
        Noted("city:alpha-port", "A port.", [Verify(**ITEM)]),
    ]


class VerifyModelTest(unittest.TestCase):
    def test_as_of_is_a_year_and_month_or_a_date(self) -> None:
        for as_of in ("2026-10", "2026-10-14"):
            Verify(claim="x", as_of=as_of)
        for as_of in ("2026", "2026-13", "Oct 2026", "2026-10-32"):
            with self.subTest(as_of=as_of), self.assertRaises(ValidationError):
                Verify(claim="x", as_of=as_of)

    def test_claim_is_required_and_fields_are_closed(self) -> None:
        for item in ({"as_of": "2026-10"}, {"claim": "", "as_of": "2026-10"}, ITEM | {"by": "me"},
                     ITEM | {"claim": "two\nlines"}, ITEM | {"source": "\x1b]8;;http://x\x1b\\"}):
            with self.subTest(item=item), self.assertRaises(ValidationError):
                Verify(**item)

    def test_every_noted_source_takes_verify(self) -> None:
        country = countries()[0]
        country["capital"] |= {"verify": [ITEM]}
        self.assertEqual(Country.model_validate(country | {"verify": [ITEM]}).capital.verify[0].claim, ITEM["claim"])
        territory, dispute = territories()
        self.assertTrue(Territory.model_validate(territory | {"verify": [ITEM]}).verify)
        self.assertTrue(Dispute.model_validate(dispute | {"verify": [ITEM]}).verify)
        self.assertTrue(City.model_validate(cities_data()[0] | {"verify": [ITEM]}).verify)
        self.assertTrue(feature("a", "Plain", verify=[Verify(**ITEM)]).verify)
        self.assertEqual(feature("a", "Plain").verify, [])


class NoteMarkerTest(unittest.TestCase):
    def test_markers_fail_whatever_their_case(self) -> None:
        for note in ("Still true (verify).", "Status as of 2026-10.", "AS OF 2025, it was.", "As of 2099 it is.",
                     "Claim (As of October).", "Claim [V].", "Claim [s].", "Population tbd.", "Re-Verify this."):
            with self.subTest(note=note):
                self.assertEqual(len(note_markers([Noted("city:x", note, [])])), 1)

    def test_clean_notes_pass(self) -> None:
        for note in ("Founded in 1652, as of old a stopover.", "A verified fact, *emphasised*.", "As of 2014 it hosted the games.",
                     "As of 2019 it was the largest port.", "Capital as of 1960, after independence.", None):
            with self.subTest(note=note):
                self.assertEqual(note_markers([Noted("city:x", note, [])]), [])

    def test_the_error_names_the_card(self) -> None:
        [error] = note_markers([Noted("capital:alpha", "Middle (as of 2026-10; verify).", [])])
        self.assertTrue(error.startswith("capital:alpha: note has research marker '(as of'"))

    def test_the_project_notes_are_clean(self) -> None:
        self.assertEqual(note_markers(noted()), [])

    def test_noted_covers_every_card(self) -> None:
        """noted() lists the sources itself; a new source must be added there, or its verify items slip the gate."""
        self.assertEqual([r.key for r in noted()], [c.key for c in sources.all_cards()])


class NotedTest(unittest.TestCase):
    def test_keys_cover_every_noted_source(self) -> None:
        country = countries()[0]
        country["capital"] |= {"verify": [ITEM]}
        territory, dispute = territories()
        with data([country | {"verify": [ITEM]}, countries()[1]], [territory, dispute | {"verify": [ITEM]}],
                  [cities_data()[0] | {"verify": [ITEM]}]), \
                mock.patch.object(check, "load_features", lambda: [feature("f", "Plain", note="Why.", verify=[Verify(**ITEM)])]):
            found = {r.key: len(r.verify) for r in noted()}
        self.assertEqual(found, {"feature:f": 1, "country:alpha": 1, "capital:alpha": 1, "country:beta": 0,
                                 "territory:gamma": 0, "dispute:delta": 1, "city:alpha-port": 1})


class ReportTest(unittest.TestCase):
    def test_lists_open_items_by_card(self) -> None:
        self.assertEqual(verify_report(rows()).splitlines(), [
            "country:alpha",
            "  [2026-10] Alpha is a republic.",
            "  [2026-10-14] Its capital is Alphaville. (source: https://example.org/alpha)",
            "city:alpha-port",
            "  [2026-10] Alpha is a republic.",
            "3 open verify item(s) on 2 card(s): country 2, city 1",
        ])

    def test_nothing_open(self) -> None:
        self.assertEqual(verify_report([Noted("capital:alpha", "Middle.", [])]), "0 open verify item(s) on 0 card(s)")

    def test_make_target_prints_the_report(self) -> None:
        out = io.StringIO()
        with mock.patch.object(check, "noted", rows), mock.patch("sys.argv", ["check", "verify-report"]), redirect_stdout(out):
            check.main()
        self.assertIn("3 open verify item(s) on 2 card(s)", out.getvalue())


class ReleaseGateTest(unittest.TestCase):
    def test_open_items_fail_only_a_release(self) -> None:
        with mock.patch.object(check, "noted", rows):
            self.assertEqual(verify_errors(release=False), [])
            self.assertEqual(verify_errors(release=True), [
                "country:alpha: 2 open verify item(s); see `make verify-report`",
                "city:alpha-port: 1 open verify item(s); see `make verify-report`",
            ])

    def test_markers_fail_with_or_without_release(self) -> None:
        dirty = [Noted("city:x", "True (verify).", [])]
        with mock.patch.object(check, "noted", lambda: dirty):
            self.assertEqual(len(verify_errors(release=False)), 1)
            self.assertEqual(verify_errors(release=True), verify_errors(release=False))

    def test_a_political_card_without_a_note_fails(self) -> None:
        bare = [Noted("capital:alpha", None, []), Noted("continent:asia", None, [])]  # features: missing_notes
        with mock.patch.object(check, "noted", lambda: bare):
            self.assertEqual(verify_errors(release=False), ["capital:alpha: no note (1-3 sentences on why it matters)"])

    def test_a_release_with_nothing_open_passes(self) -> None:
        with mock.patch.object(check, "noted", lambda: [Noted("capital:alpha", "Middle.", [])]):
            self.assertEqual(verify_errors(release=True), [])

    def test_release_flag_reaches_check_data(self) -> None:
        for argv, release in ((["check", "data"], False), (["check", "data", "--release"], True)):
            with self.subTest(argv=argv), mock.patch("sys.argv", argv), redirect_stdout(io.StringIO()), \
                    mock.patch.object(check, "check_data", return_value=([], [])) as check_data:
                check.main()
            check_data.assert_called_once_with(release=release)

    def test_check_data_runs_the_verify_rules(self) -> None:
        with mock.patch.object(check, "verify_errors", return_value=["stop"]) as rules, \
                mock.patch.object(check, "load_features", return_value=[]), \
                mock.patch.object(check, "duplicate_uids", return_value=[]), \
                mock.patch.object(check, "GEOMETRY", mock.Mock(glob=lambda _: [])), \
                mock.patch.object(check.political, "check", return_value=([], {})), \
                mock.patch.object(check.cities, "check", return_value=[]), \
                mock.patch.object(check, "lock_freeze_errors", return_value=[]), \
                mock.patch.object(check, "save_siblings") as save:
            errors, _ = check.check_data(release=True)
        save.assert_called_once()  # a verify error holds back none of the checks before it
        rules.assert_called_once_with(True)
        self.assertEqual(errors, ["stop"])

    def test_unknown_flags_are_refused(self) -> None:
        for argv in (["check"], ["check", "dta"], ["check", "data", "--relase"], ["check", "deck", "--release"]):
            with self.subTest(argv=argv), mock.patch("sys.argv", argv), self.assertRaises(SystemExit) as exit_:
                check.main()
            self.assertNotEqual(exit_.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
