"""Whole-number display compaction keeps measurement semantics and labels intact."""

import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from tools.health_sync.number_display import compact_measurement, compact_reference
from tools.tests.test_report_layout import rendered_table_rows


class NumberDisplayTests(unittest.TestCase):
    def test_whole_measurements_bounds_pairs_and_ranges_are_compact(self):
        cases = {
            "114.0": "114", "0.00": "0", "-3.00": "-3", "+4.000": "+4",
            ".00": "0", "6.0e3": "6e3", "~ 20.00": "~ 20",
            "< 10.00": "< 10", "≥5.0": "≥5", "100.0%": "100%",
            "114.0/76.3": "114/76.3", "114.0 / 75.00": "114 / 75",
            "-10.0 - 0.0": "-10 - 0", "1.00–2.0": "1–2",
            "29.0 (9/31)": "29 (9/31)", " 22.0 ": " 22 ",
            "3.0 (annotation 2.0)": "3 (annotation 2.0)",
        }
        for original, expected in cases.items():
            with self.subTest(original=original):
                self.assertEqual(compact_measurement(original), expected)

    def test_nonzero_fractional_precision_and_non_numeric_text_stay_literal(self):
        for value in (
            "76.3", "0.05", "1.20", "1.0001", "3.010", "0.001", "-0.05",
            "pending", "unknown", "Negative: 5.0", "Device code 2.0: 1",
            "00:00", "2026-01-01", "2026.01.01", "1.0.2", "M.0.2",
            "HSN EvoBomb 2.0", "LOOP EXPERIENCE 2.0 Black",
            "https://example.test/2.0", "[2.0](source)", "2.0 mg of compound",
            "", "-", None,
        ):
            with self.subTest(value=value):
                self.assertEqual(compact_measurement(value), value)

    def test_reference_limits_and_targets_compact_without_editing_labels(self):
        cases = {
            "13.0 - 18.0; target 14.0 - 16.2": "13 - 18; target 14 - 16.2",
            "0.00 - 0.10; target <= 0.08": "0 - 0.10; target <= 0.08",
            "< 20.0: negative; >= 20.0: positive": "< 20: negative; >= 20: positive",
            "36.1–37.2 (goal 36.5–37.0)": "36.1–37.2 (goal 36.5–37)",
            "<120.0/<80.0 (goal 100.0–115.0/60.0–75.0)": "<120/<80 (goal 100–115/60–75)",
            "< 2.0 (assay version 2.0)": "< 2 (assay version 2.0)",
        }
        for original, expected in cases.items():
            with self.subTest(original=original):
                self.assertEqual(compact_reference(original), expected)
        for value in ("HSN EvoBomb 2.0", "Reference version 2.0", "https://example.test/2.0", "-"):
            self.assertEqual(compact_reference(value), value)


class NumberDisplayRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "monthly.json"
            source.write_text(json.dumps({"schema_version": 1, "as_of": "2026-09-07", "months": {}}), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(source)}):
                cls.report = runpy.run_path(
                    str(Path(__file__).parents[1] / "generate_colored_report.py"), run_name="number_display_test")

    def test_both_tables_compact_values_and_references_across_categories(self):
        for category, marker, value, reference, expected in (
            ("Example laboratory", "Example", "2.00", "1.00 - 3.00", "2"),
            ("Vitals & Functional Health", "Future Device Metric", "80.0", "-", "80"),
            ("Urinalysis (General)", "pH", "5.0", "5.0 - 8.0", "5"),
            ("Gut Microbiota (GA-map)", "Dysbiosis Index", "3.0 (annotation 2.0)", "-", "3 (annotation 2.0)"),
        ):
            row = (marker, *(value if month == "2026-09" else "-"
                             for month in self.report["date_columns"]), "unit", reference)
            for output_format in ("html", "md"):
                with self.subTest(category=category, format=output_format):
                    rendered = self.report[f"render_result_table_{output_format}"](category, [row])
                    header, cells = rendered_table_rows(rendered, output_format)
                    shown = expected if output_format == "html" else expected.replace("(", r"\(").replace(")", r"\)")
                    self.assertTrue(cells[header.index("2026-09")].endswith(shown))
                    self.assertEqual(cells[header.index("Unit")], "unit")
                    if category == "Example laboratory":
                        self.assertEqual(cells[header.index("Reference")], "1 - 3")

    def test_compact_status_values_keep_annotations_escaped(self):
        value = '2.0 (<script>3.0</script>)'
        for output_format in ("html", "md"):
            with self.subTest(format=output_format):
                rendered = self.report["format_status"](
                    value, self.report["NEUTRAL"], markdown=output_format == "md")
                self.assertTrue(rendered.startswith("2 "))
                self.assertNotIn("<script>", rendered)
                self.assertIn("&lt;script&gt;3.0&lt;/script&gt;", rendered)


if __name__ == "__main__":
    unittest.main()
