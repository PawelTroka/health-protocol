"""A partial workout export must not shrink an already known daily zone sum."""

from copy import deepcopy
from datetime import date
import json
import unittest
from unittest.mock import patch

from tools import sync_vitals as cli
from tools.health_sync import garmin, monthly, reconcile
from tools.tests import test_sync_cli as cli_fixtures


DAY = "2026-08-03"
START, END = date(2026, 8, 1), date(2026, 8, 31)
METRIC = "Workout HR Zone 2 Duration (Garmin)"


def snapshot(activities=((1, 600), (2, 600)), *, day=DAY, zone=2):
    return {"activity_hr_zones": [{"day": day, "data": [
        {"activityId": ident, "startTimeLocal": day + "T09:00:00",
         "zones": [{"zoneNumber": zone, "secsInZone": seconds}]}
        for ident, seconds in activities
    ]}]}


def records(*args, **kwargs):
    return garmin.parse_api(snapshot(*args, **kwargs))


def merge(existing, incoming, **kwargs):
    return monthly.merge_file_records(existing, incoming, ["garmin"], START, END, **kwargs)


class GarminZoneFileMergeTests(unittest.TestCase):
    def test_partial_or_disjoint_export_cannot_replace_full_day(self):
        old = records()
        self.assertEqual(old[0]["value"], 20)
        for activities in (((1, 600),), ((3, 600),)):
            for partial_api in (False, True):
                incoming = records(activities)
                before = deepcopy((old, incoming))
                with self.subTest(activities=activities, partial_api=partial_api):
                    with self.assertRaisesRegex(ValueError, "all known activities"):
                        merge(old, incoming, partial_api=partial_api)
                    self.assertEqual((old, incoming), before)

    def test_complete_and_expanded_exports_allow_corrections_and_repeat_imports(self):
        # A lower duration is legitimate when every contributing activity is
        # present; retaining the maximum would conceal corrected measurements.
        for activities, minutes in ((((1, 300), (2, 300)), 10),
                                    (((1, 300), (2, 300), (3, 300)), 15),
                                    (((1, 0), (2, 0)), 0)):
            with self.subTest(activities=activities):
                incoming = records(activities)
                result = merge(records(), incoming)
                self.assertEqual(result, incoming)
                self.assertEqual(result[0]["value"], minutes)
                self.assertEqual(merge(result, incoming), result)

    def test_provenance_must_identify_every_contributor(self):
        for changes in ({"source_record_ids": None}, {"source_record_ids": []},
                        {"source_record_ids": ["1", "1"]},
                        {"source_record_ids": ["1", None]},
                        {"source_record_ids": "1,2"}, {"source_count": 1}):
            for damaged_side in ("existing", "incoming"):
                old, incoming = records(), records()
                (old if damaged_side == "existing" else incoming)[0].update(changes)
                with self.subTest(changes=changes, damaged_side=damaged_side):
                    with self.assertRaisesRegex(ValueError, "all known activities"):
                        merge(old, incoming)
        missing = records()
        del missing[0]["source_record_ids"]
        with self.assertRaisesRegex(ValueError, "all known activities"):
            merge(missing, records())

    def test_daily_identity_replaces_alternative_cache_ids_without_double_counting(self):
        old = records()
        old[0]["id"] = "garmin:legacy-zone-summary"
        incoming = records(((1, 300), (2, 300)))
        self.assertEqual(merge(old, incoming), incoming)
        conflicting = {**incoming[0], "id": "garmin:another-zone-summary", "value": 99}
        with self.assertRaisesRegex(ValueError, "all known activities"):
            merge(old, incoming + [conflicting])

    def test_omitted_dates_metrics_and_other_providers_are_preserved(self):
        old = records()
        retained = records(day="2026-08-04") + records(zone=3)
        retained += [{"provider": "withings", "id": "withings:weight",
                      "day": DAY, "metric": "Body Mass", "value": 80,
                      "unit": "kg", "source_kind": "api"}]
        incoming = records(((1, 300), (2, 300)))
        result = merge(old + retained, incoming)
        self.assertEqual(len(result), len(retained) + 1)
        for record in retained + incoming:
            self.assertIn(record, result)
        # A partial record outside the requested range must not block an
        # otherwise complete import inside it.
        outside = records(((1, 600),), day="2026-09-01")
        self.assertEqual(merge(old, incoming + outside), incoming)

    def test_individual_workout_effects_keep_their_existing_amendment_behavior(self):
        payload = {"activities": [{"day": DAY, "data": [
            {"activityId": ident, "startTimeLocal": DAY + "T09:00:00",
             "aerobicTrainingEffect": effect}
            for ident, effect in ((1, 2), (2, 3))
        ]}]}
        old = garmin.parse_api(payload)
        payload["activities"][0]["data"] = [payload["activities"][0]["data"][0]]
        payload["activities"][0]["data"][0]["aerobicTrainingEffect"] = 1
        result = merge(old, garmin.parse_api(payload))
        self.assertEqual(sorted(record["value"] for record in result), [1, 3])

    def test_complete_api_refresh_can_remove_a_deleted_activity(self):
        incoming = records(((1, 600),))
        coverage = {"garmin": {"endpoint_status": {
            "activity_hr_zones": {"status": "complete"}}}}
        self.assertEqual(reconcile.merge_synced(
            records(), incoming, ["garmin"], START, END, coverage), incoming)


class GarminZoneFileCliTests(unittest.TestCase):
    setUp = cli_fixtures.SyncCliTests.setUp
    prepared_reports = cli_fixtures.SyncCliTests.prepared_reports
    snapshot = cli_fixtures.SyncCliTests.snapshot
    args = cli_fixtures.SyncCliTests.args
    run_quietly = cli_fixtures.SyncCliTests.run_quietly

    def test_partial_import_preserves_cache_reports_and_archives(self):
        cache_path = self.cache / "records.json"
        original = json.loads(cache_path.read_bytes())
        original["records"] += records()
        cache_path.write_bytes(cli.json_bytes(original))
        source = self.root / "partial-garmin.json"
        source.write_bytes(cli.json_bytes(snapshot(((1, 600),))))
        before = self.snapshot()
        with patch.object(cli, "archive") as archive, \
                patch.object(cli, "atomic_commit") as commit:
            with self.assertRaisesRegex(ValueError, "all known activities"):
                self.run_quietly(self.args("import", "--garmin-json", str(source)))
        self.prepare.assert_not_called()
        archive.assert_not_called()
        commit.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_complete_file_publishes_corrected_daily_sum_and_is_idempotent(self):
        cache_path = self.cache / "records.json"
        original = json.loads(cache_path.read_bytes())
        original["records"] += records()
        cache_path.write_bytes(cli.json_bytes(original))
        source = self.root / "complete-garmin.json"
        source.write_bytes(cli.json_bytes(snapshot(((1, 300), (2, 300)))))
        args = self.args("import", "--garmin-json", str(source))
        self.run_quietly(args)
        generated = json.loads((self.root / "results/vitals_monthly.json").read_bytes())
        entry = generated["months"]["2026-08"][METRIC]
        self.assertEqual((entry["value"], entry["n_records"]), ("10.0", 2))
        before = self.snapshot()
        self.run_quietly(args)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
