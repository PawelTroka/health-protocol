"""Preserve Garmin HRV codes while applying the existing status display policy."""

from copy import deepcopy
from datetime import date
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import patch

from tools.health_sync import categorical, garmin, vitals_targets as targets


MARKER = "HRV Status (Garmin)"


def inventory(statuses):
    return garmin.categorical_inventory({"hrv": [
        {"day": day, "data": {"hrvSummary": {"calendarDate": day, "status": status}}}
        for day, status in statuses
    ]})


class GarminHrvStatusTests(unittest.TestCase):
    def test_imported_codes_keep_literal_text_and_receive_existing_colors(self):
        for code, emoji in (("BALANCED", "🟢"), ("UNBALANCED", "🟡"),
                            ("LOW", "🟠"), ("POOR", "🔴")):
            with self.subTest(code=code):
                events = inventory([("2026-08-01", code), ("2026-08-02", code)])
                before = deepcopy(events)
                summary = categorical.aggregate(events, date(2026, 9, 1))["2026-08"][MARKER]
                self.assertEqual(summary["counts"], {code: 2})
                self.assertEqual(summary["value"], f"{code}: 2")
                parts = targets.classification_parts(MARKER, summary["value"])
                self.assertEqual(parts[0][0], f"{code}: 2")
                self.assertIsNotNone(parts[0][1])
                self.assertEqual(parts[0][1][1], emoji)
                self.assertEqual(events, before)
                self.assertTrue(all(event["source_value"] == code for event in events))

    def test_established_title_case_labels_remain_compatible(self):
        for code in ("BALANCED", "UNBALANCED", "LOW", "POOR"):
            with self.subTest(code=code):
                old = targets.classification_parts(MARKER, f"{code.title()}: 3")[0]
                new = targets.classification_parts(MARKER, f"{code}: 3")[0]
                self.assertIsNotNone(new[1])
                self.assertEqual(new[1][:2], old[1][:2])
                self.assertEqual(old[0], f"{code.title()}: 3")
        self.assertEqual(targets.classification_trend(
            ["BALANCED: 1; Balanced: 1", "Balanced: 30"], MARKER), "⚪")

    def test_uppercase_trends_compare_proportions_with_existing_ranks(self):
        better, worse = "BALANCED: 2; LOW: 1", "BALANCED: 1; LOW: 2"
        self.assertEqual(targets.classification_trend([better, worse], MARKER), "🟢")
        self.assertEqual(targets.classification_trend([worse, better], MARKER), "🟡")
        self.assertEqual(targets.classification_trend(["BALANCED: 1", "BALANCED: 30"], MARKER), "⚪")
        self.assertEqual(targets.classification_trend(["BALANCED: 1", "Poor: 3"], MARKER), "🟢")

    def test_unknown_codes_and_no_status_sentinels_remain_ungraded(self):
        for code in ("NONE", "UNKNOWN", "NO_DATA", "NEW_VENDOR_STATUS", "balanced",
                     "UNBALANCED_HIGH", "NOT_BALANCED"):
            with self.subTest(code=code):
                events = inventory([("2026-08-01", code)])
                summary = categorical.aggregate(events, date(2026, 9, 1))["2026-08"][MARKER]
                self.assertEqual(targets.classification_parts(MARKER, summary["value"]),
                                 [(f"{code}: 1", None)])
                self.assertEqual(targets.classification_trend(
                    [summary["value"], "BALANCED: 2", "LOW: 2"], MARKER), "-")

    def test_real_import_codes_reach_both_report_renderers_without_source_changes(self):
        events = inventory([("2026-07-01", "LOW"), ("2026-07-02", "LOW"),
                            ("2026-08-01", "BALANCED"), ("2026-08-02", "BALANCED")])
        payload = {"schema_version": 1, "as_of": "2026-09-01", "months": {},
                   "categorical_months": categorical.aggregate(events, date(2026, 9, 1))}
        before = deepcopy(payload)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "monthly.json"
            source.write_text(json.dumps(payload), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(source)}):
                report = runpy.run_path(str(Path(__file__).parents[1] / "generate_colored_report.py"),
                                        run_name="garmin_hrv_status_test")
            self.assertEqual({path.name for path in Path(folder).iterdir()}, {"monthly.json"})
            self.assertEqual(json.loads(source.read_text(encoding="utf-8")), before)
        rows = [row for row in report["data"]["Vitals & Functional Health"] if row[0] == MARKER]
        self.assertEqual(len(rows), 1)
        _, values, _, reference = report["split_result_row"](rows[0])
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = report[f"render_result_table_{output_format}"]("Vitals & Functional Health", rows)
                rendered = re.sub(r"<sup>[^<]*</sup>", "", rendered)
                self.assertIn("🟢 BALANCED: 2", rendered)
                self.assertIn("🟠 LOW: 2", rendered)
                self.assertEqual(report[f"format_trend_{output_format}"](
                    values, reference, "Vitals & Functional Health", MARKER), "🟢")


if __name__ == "__main__":
    unittest.main()
