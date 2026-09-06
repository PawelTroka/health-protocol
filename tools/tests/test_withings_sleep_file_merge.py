"""Partial sleep exports must not erase a session already included in a day."""

from contextlib import redirect_stdout
from datetime import date, datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import sync_vitals as cli
from tools.health_sync.monthly import merge_file_records
from tools.health_sync.withings import parse_api


START, END = date(2026, 8, 1), date(2026, 8, 31)
METRIC = "Sleep Duration (Withings)"


def daily(source_ids=("first", "second"), day="2026-08-03", **changes):
    return {"provider": "withings", "id": f"withings:sleep:daily-{day}:{METRIC}",
            "day": day, "metric": METRIC, "value": 7, "unit": "h", "source_kind": "api",
            "source_record_ids": list(source_ids), "source_count": len(source_ids), **changes}


def legacy(identifier, day="2026-08-03"):
    return {"provider": "withings", "id": f"withings:sleep:{identifier}:{METRIC}",
            "day": day, "metric": METRIC, "value": 3.5, "unit": "h", "source_kind": "api"}


def merge(existing, incoming, **options):
    return merge_file_records(existing, incoming, ["withings"], START, END, **options)


class WithingsSleepFileMergeTests(unittest.TestCase):
    def test_partial_daily_replacement_fails_and_does_not_mutate_inputs(self):
        existing, incoming = [daily()], [daily(("first",), value=3.5)]
        before = json.dumps([existing, incoming], sort_keys=True)
        with self.assertRaisesRegex(ValueError, "full API sync"):
            merge(existing, incoming)
        self.assertEqual(json.dumps([existing, incoming], sort_keys=True), before)

    def test_complete_or_expanded_daily_source_set_replaces_once_and_is_idempotent(self):
        for ids in (("first", "second"), ("first", "second", "third")):
            with self.subTest(ids=ids):
                replacement = daily(ids, value=8)
                result = merge([daily()], [replacement])
                self.assertEqual(result, [replacement])
                self.assertEqual(merge(result, [replacement]), result)

    def test_legacy_sessions_are_covered_then_removed_without_daily_double_counting(self):
        old = [legacy("first"), legacy("second")]
        with self.assertRaisesRegex(ValueError, "full API sync"):
            merge(old, [daily(("first",))])
        replacement = daily()
        self.assertEqual(merge(old, [replacement]), [replacement])

    def test_unknown_legacy_source_and_missing_daily_provenance_fail_closed(self):
        unknown = {**legacy("first"), "id": "unknown-legacy-sleep-reading"}
        missing = daily()
        del missing["source_record_ids"]
        for old in (unknown, missing):
            with self.subTest(old=old), self.assertRaisesRegex(ValueError, "full API sync"):
                merge([old], [daily()])
        with self.assertRaisesRegex(ValueError, "full API sync"):
            merge([daily()], [missing])

    def test_invalid_source_identity_lists_and_competing_daily_values_are_rejected(self):
        for values in ([], ["first", "first"], ["first", None], "first"):
            with self.subTest(values=values), self.assertRaisesRegex(ValueError, "full API sync"):
                merge([daily()], [daily(source_record_ids=values)])
        with self.assertRaisesRegex(ValueError, "full API sync"):
            merge([daily()], [daily(source_count=3)])
        with self.assertRaisesRegex(ValueError, "full API sync"):
            merge([], [legacy("first"), legacy("second")], partial_api=True)

    def test_other_days_metrics_and_ordinary_measurements_remain_untouched(self):
        other_day = daily(day="2026-08-04")
        other_metric = {**daily(), "id": "withings:sleep:daily-2026-08-03:Deep Sleep (Withings)",
                        "metric": "Deep Sleep (Withings)", "value": 1}
        weight = {"provider": "withings", "id": "withings:measure:weight:Body Mass",
                  "day": "2026-08-03", "metric": "Body Mass", "value": 80,
                  "unit": "kg", "source_kind": "api"}
        replacement = daily(value=8)
        result = merge([daily(), other_day, other_metric, weight], [replacement])
        for retained in (replacement, other_day, other_metric, weight):
            self.assertIn(retained, result)
        self.assertEqual(len(result), 4)

    def test_real_parser_partial_file_stops_before_any_report_or_archive_write(self):
        start = int(datetime(2026, 8, 3, tzinfo=timezone.utc).timestamp())
        first = {"id": "first", "completed": True, "startdate": start,
                 "enddate": start + 3 * 3600, "data": {"total_sleep_time": 3 * 3600}}
        second = {"id": "second", "completed": True, "startdate": start + 4 * 3600,
                  "enddate": start + 8 * 3600, "data": {"total_sleep_time": 4 * 3600}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / ".health-sync"
            cache.mkdir()
            records = parse_api({"series": [first, second]})
            (cache / "records.json").write_bytes(cli.json_bytes({"schema_version": 1, "records": records}))
            (root / "results").mkdir()
            for name in ("results.md", "results.html", "results/vitals_monthly.json"):
                (root / name).write_bytes(b"Existing output\n")
            source = root / "partial.json"
            source.write_bytes(cli.json_bytes({"series": [first]}))
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            args = cli.parser().parse_args(["import", "--withings-json", str(source),
                                           "--start", "2026-08-01", "--end", "2026-08-31"])
            with patch.object(cli, "ROOT", root), patch.object(cli, "CACHE", cache), \
                    patch.object(cli, "datetime") as clock, \
                    patch.object(cli, "prepare_reports") as reports, \
                    patch.object(cli, "archive") as archive, \
                    patch.object(cli, "atomic_commit") as commit, redirect_stdout(io.StringIO()):
                clock.now.return_value = datetime(2026, 9, 6, 12, tzinfo=timezone.utc)
                with self.assertRaisesRegex(ValueError, "full API sync"):
                    cli.run_import(args)
            reports.assert_not_called()
            archive.assert_not_called()
            commit.assert_not_called()
            self.assertEqual({p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}, before)


if __name__ == "__main__":
    unittest.main()
