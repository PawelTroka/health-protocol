"""Reviewed measurement history and presentation; no live imports or file outputs."""

from collections import Counter
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import patch


VITALS = "Vitals & Functional Health"
WAIST = "Waist Circumference (Narrowest Point)"


def table_parts(rendered, output_format):
    if output_format == "html":
        table = re.search(r"<table\b[^>]*>(.*?)</table>", rendered, re.S).group(1)
        return re.match(r"(<tr>.*?</tr>)(.*)", table, re.S).groups()
    lines = [line for line in rendered.splitlines() if line.startswith("|")]
    return lines[0], "\n".join(lines[2:])


class BodyMeasurementReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "monthly.json"
            source.write_text(json.dumps({
                "schema_version": 1, "as_of": "2026-11-07", "months": {},
            }), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(source)}):
                cls.report = runpy.run_path(
                    str(Path(__file__).parents[1] / "generate_colored_report.py"),
                    run_name="body_measurement_review_test",
                )
        cls.body_rows = next(group["rows"] for group in cls.report["layout"](
            cls.report["data"][VITALS]
        ) if group["title"] == "Body measurements")

    def observations(self, name):
        row = next(row for row in self.body_rows if row[0] == name)
        return dict(zip(self.report["date_columns"], row[1:-2]))

    def test_confirmed_waist_and_flexed_arms_share_canonical_history(self):
        names = Counter(row[0] for row in self.body_rows)
        self.assertEqual(len(self.body_rows), 22)
        expected = {
            WAIST: ("80.5", "85"),
            "Right Upper Arm Circumference (Flexed)": ("37", "38"),
            "Left Upper Arm Circumference (Flexed)": ("37", "-"),
        }
        for name, values in expected.items():
            with self.subTest(measurement=name):
                self.assertEqual(names[name], 1)
                observed = self.observations(name)
                self.assertEqual((observed["2026-11"], observed["2026-09"]), values)
        self.assertTrue({"Waist Circumference", "Right Upper Arm Circumference",
                         "Left Upper Arm Circumference"}.isdisjoint(names))

    def test_only_previous_sizes_fill_the_current_snapshot(self):
        retained = {
            "Height": "180", "Right Wrist Circumference": "15.5",
            "Right Ankle Circumference": "24", "Right Above-Ankle Circumference": "21",
            "Right Foot Length": "25.5",
        }
        for name, value in retained.items():
            with self.subTest(measurement=name):
                observed = self.observations(name)
                self.assertEqual((observed["2026-11"], observed["2026-09"]), (value, value))
        self.assertTrue(all(self.observations(row[0])["2026-11"] != "-"
                            for row in self.body_rows))
        for name in ("Left Upper Arm Circumference (Flexed)", "Left Forearm Circumference",
                     "Left Thigh Circumference", "Left Calf Circumference",
                     "Upper Facial Third Length", "Middle Facial Third Length",
                     "Lower Facial Third Length"):
            with self.subTest(no_historical_reading=name):
                self.assertEqual(self.observations(name)["2026-09"], "-")

    def test_body_sources_appear_once_per_date_header_in_both_formats(self):
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = self.report[f"render_vitals_{output_format}"](self.body_rows)
                header, cells = table_parts(rendered, output_format)
                for month in ("2026-11", "2026-09"):
                    self.assertRegex(header, month + r"<sup>\d+(?:,\d+)*</sup>")
                self.assertEqual(header.count("<sup>"), 2)
                self.assertNotIn("<sup>", cells)

    def test_clinical_table_keeps_its_cell_specific_source_note(self):
        row = ("PWV", *("6.1" if month == "2026-09" else "-"
                        for month in self.report["date_columns"]), "m/s", "<10")
        notes = {VITALS: [{"text": "Clinical source", "markers": [
            {"row": "PWV", "target": "value", "dates": ["2026-09"]},
        ]}]}
        for output_format in ("html", "md"):
            renderer = self.report[f"render_vitals_{output_format}"]
            with self.subTest(output_format=output_format), patch.dict(
                renderer.__globals__, {"result_notes": notes}
            ):
                header, cells = table_parts(renderer([row]), output_format)
                self.assertNotIn("<sup>", header)
                self.assertIn("<sup>1</sup>", cells)

    def test_positive_waist_goal_is_limited_to_the_confirmed_comparison(self):
        cases = (
            (["2026-11", "2026-09"], ["80.5", "85"], True),
            (["2026-11", "2026-09"], ["85", "80.5"], False),
            (["2026-09", "2026-11"], ["80.5", "85"], False),
            (["2026-12", "2026-11", "2026-09"], ["79", "80.5", "85"], False),
            (["2026-12", "2026-11", "2026-09"], ["pending", "80.5", "85"], False),
            (["2026-11", "2026-09"], ["pending", "85"], False),
        )
        for output_format in ("html", "md"):
            formatter = self.report[f"format_trend_{output_format}"]
            for dates, values, positive in cases:
                with self.subTest(output_format=output_format, dates=dates, values=values), \
                        patch.dict(formatter.__globals__, {"date_columns": dates}):
                    self.assertEqual("🟢" in formatter(values, "-", VITALS, WAIST), positive)
            with patch.dict(formatter.__globals__, {"date_columns": ["2026-11", "2026-09"]}):
                self.assertNotIn("🟢", formatter(["96", "99"], "-", VITALS, "Hip Circumference"))
