"""Garmin pipeline regression tests using only synthetic data and a temp cache."""

from datetime import date
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import sync_vitals as cli
from tools.health_sync import categorical, garmin, monthly, reconcile, report_layout
from tools.tests import test_sync_cli as existing


def snapshot(day="2026-08-03", steps=1000):
    return {"daily_summary": [{"day": day, "data": {
        "calendarDate": day, "totalSteps": steps, "restingHeartRate": 60,
    }}]}


def record(day, steps):
    return next(r for r in garmin.parse_api(snapshot(day, steps)) if r["metric"] == "Steps (Garmin)")


class GarminIntegrationTests(unittest.TestCase):
    setUp = existing.SyncCliTests.setUp
    prepared_reports = existing.SyncCliTests.prepared_reports
    snapshot = existing.SyncCliTests.snapshot
    args = existing.SyncCliTests.args
    run_quietly = existing.SyncCliTests.run_quietly

    def test_default_selects_connected_accounts_including_expired_configuration(self):
        states = {"oura": {"configured": True, "authorized": True},
                  "withings": {"configured": False, "authorized": False},
                  "garmin": {"configured": True, "authorized": False}}
        with patch.object(cli, "connection_status", return_value=states):
            self.assertEqual(self.args("sync").provider, "all")
            self.assertEqual(cli.selected_providers("all"), ["oura", "garmin"])
        with patch.object(cli, "connection_status", side_effect=AssertionError("unexpected auth")):
            self.assertEqual(cli.selected_providers("both"), ["oura", "withings"])
            self.assertEqual(cli.selected_providers("garmin"), ["garmin"])
        with patch.object(cli, "connection_status", return_value={}):
            with self.assertRaisesRegex(RuntimeError, "No accounts connected"):
                cli.selected_providers("all")

    def test_garmin_sync_retains_other_sources_and_coverage_and_excludes_today(self):
        old_coverage = {"oura": {"start": "2026-07-01", "end": "2026-09-05"}}
        (self.root / "results/vitals_monthly.json").write_bytes(cli.json_bytes({"sync_coverage": old_coverage}))
        payload = snapshot()
        payload["daily_summary"] += snapshot("2026-08-04", 3000)["daily_summary"]
        payload["daily_summary"] += snapshot("2026-09-06", 9999)["daily_summary"]
        payload["_sync"] = {"start": "2026-08-01", "end": "2026-09-06",
                            "endpoint_status": {"daily_summary": {"status": "complete"}}}
        self.fetch.return_value, self.fetch.side_effect = payload, None
        self.run_quietly(self.args("sync", "--provider", "garmin", "--start", "2026-08-01", "--end", "2026-09-06"))
        generated = json.loads((self.root / "results/vitals_monthly.json").read_bytes())
        self.assertEqual(generated["months"]["2026-08"]["Steps (Garmin)"]["value"], "2000")
        self.assertEqual(generated["sync_coverage"]["oura"], old_coverage["oura"])
        saved = json.loads((self.cache / "records.json").read_bytes())["records"]
        for original in self.previous_records:
            self.assertIn(original, saved)
        self.assertFalse(any(r["provider"] == "garmin" and r["day"] == "2026-09-06" for r in saved))
        self.assertEqual(len(list((self.cache / "raw/garmin").glob("*.json"))), 1)

    def test_invalid_response_preserves_reports_cache_and_archives(self):
        self.fetch.return_value, self.fetch.side_effect = snapshot(steps=True), None
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.run_quietly(self.args("sync", "--provider", "garmin"))
        self.assertEqual(self.snapshot(), before)
        self.prepare.assert_not_called()

    def test_partial_file_reimport_is_idempotent_and_rejects_session_tokens(self):
        source = self.root / "garmin.json"
        source.write_bytes(cli.json_bytes(snapshot()))
        args = self.args("import", "--garmin-json", str(source))
        self.run_quietly(args)
        first = self.snapshot()
        self.run_quietly(args)
        self.assertEqual(self.snapshot(), first)
        for credential in ("di_token", "di_refresh_token", "session_json", "oauth_token_secret"):
            payload = snapshot()
            payload["private"] = {credential: "synthetic-sensitive-value"}
            source.write_bytes(cli.json_bytes(payload))
            before = self.snapshot()
            with self.assertRaisesRegex(ValueError, "credential fields"):
                self.run_quietly(args)
            self.assertEqual(self.snapshot(), before)


class GarminReconciliationTests(unittest.TestCase):
    def test_endpoint_gap_preserves_history_but_complete_empty_removes_it(self):
        previous, incoming = [record("2026-08-03", 1000)], [record("2026-08-04", 3000)]
        bounds = (date(2026, 8, 1), date(2026, 8, 31))
        status = {"garmin": {"endpoint_status": {"daily_summary": {"status": "unavailable"}}}}
        self.assertEqual(len(reconcile.merge_synced(previous, incoming, ["garmin"], *bounds, status)), 2)
        status["garmin"]["endpoint_status"]["daily_summary"]["status"] = "complete"
        self.assertEqual(reconcile.merge_synced(previous, [], ["garmin"], *bounds, status), [])

    def test_current_day_is_excluded_from_numeric_and_categorical_averages(self):
        records = [record("2026-09-05", 1000), record("2026-09-06", 9000)]
        self.assertEqual(monthly.aggregate(records, date(2026, 9, 6))["months"]["2026-09"]["Steps (Garmin)"]["value"], "1000")
        event = {"id": "garmin:today", "provider": "garmin", "day": "2026-09-06",
                 "metric": "HRV Status (Garmin)", "value": "BALANCED"}
        self.assertEqual(categorical.aggregate([event], date(2026, 9, 6)), {})

    def test_every_registered_garmin_marker_has_a_specific_report_group(self):
        markers = set(garmin.GARMIN_METRICS) | garmin.GARMIN_CATEGORICAL_METRICS
        groups = report_layout.layout([(name, "1", "-") for name in markers])
        self.assertEqual(sum(len(group["rows"]) for group in groups), len(markers))
        self.assertNotIn("Additional measurements", {group["title"] for group in groups})
        self.assertTrue(all(name.endswith(" (Garmin)") for name in markers))


if __name__ == "__main__":
    unittest.main()
