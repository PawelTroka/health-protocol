"""A result's punctuation must not silently change its numerical meaning."""

from decimal import Decimal
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from tools.health_sync.result_bounds import bound_within_reference, bounded_comparison, is_bounded
from tools.health_sync.result_numbers import parse_reference, parse_result


class ResultNumberTests(unittest.TestCase):
    def test_signed_decimal_scientific_and_annotated_results(self):
        for raw, expected in {
            "-5": "-5", "+.125": "0.125", "1e3": "1000", "1e-3": ".001",
            "-2.5E+2": "-250", " 1,5 ": "1.5", "0,125": ".125",
            "1234,567": "1234.567", "~65": "65", "3 (mild dysbiosis)": "3",
        }.items():
            with self.subTest(raw=raw):
                self.assertEqual(parse_result(raw).value, Decimal(expected))
                self.assertEqual(parse_result(raw).operator, "")

    def test_ambiguous_or_non_scalar_text_is_not_rewritten_as_a_number(self):
        for raw in (
            "1,234", "12,345", "123,456", "1,234.5", "1.234,5", "1,",
            "3 / 5", "108/70", "1-2", "1 234", "12 mg/L", "1e", "1e+",
            "Normal: 2; Inconclusive: 1", "result 3", "3 (note) extra",
            "NaN", "Infinity", "-inf", "<unknown", "~<5", None, 1.5,
        ):
            with self.subTest(raw=raw):
                self.assertIsNone(parse_result(raw))

    def test_bounds_keep_their_comparators_with_all_supported_number_formats(self):
        for raw, number, operator in (
            ("<1e-3", ".001", "<"), ("≥ -1,5", "-1.5", ">="),
            ("≤ 0,125 (reporting limit)", ".125", "<="),
        ):
            with self.subTest(raw=raw):
                result = parse_result(raw)
                self.assertEqual((result.value, result.operator), (Decimal(number), operator))
                self.assertTrue(is_bounded(raw))

    def test_approximate_scalars_do_not_establish_exact_interval_relationships(self):
        self.assertTrue(parse_result("~65").approximate)
        self.assertIsNone(bound_within_reference("~65", "<70"))
        self.assertIsNone(bounded_comparison("<65", "~65"))
        self.assertIsNone(bounded_comparison("~65", "<65"))

    def test_reference_ranges_use_the_same_whole_number_grammar(self):
        for raw, expected in (
            ("-3 - -1; target -2", ("-3", "-1")),
            ("-1e3–2e3", ("-1000", "2000")),
            ("1,5 - 2,5", ("1.5", "2.5")),
            ("36.1–37.2 (goal 36.5–37.0)", ("36.1", "37.2")),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(parse_reference(raw), tuple(map(Decimal, expected)))
        for raw in (
            "1,234 - 2,345", "3 - 1", "1-2 trailing", "5 to 8",
            "1-2 (goal 1.5) extra", "1-2 (goal (1.5))", "1-2 (goal 1.5",
            "1-2 (goal 1.5) (extra)",
        ):
            self.assertIsNone(parse_reference(raw))



class ReportNumberIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "monthly.json"
            source.write_text(json.dumps({
                "schema_version": 1, "as_of": "2026-11-20", "months": {},
            }), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(source)}):
                cls.report = runpy.run_path(
                    str(Path(__file__).parents[1] / "generate_colored_report.py"),
                    run_name="result_number_test",
                )
            if {path.name for path in Path(folder).iterdir()} != {"monthly.json"}:
                raise AssertionError("Loading definitions must not generate reports")

    def test_scalar_directions_preserve_signs_and_reference_number_formats(self):
        for value, reference, expected in (
            ("-5", "0 - 10", "↓"), ("-4", "-3 - -1", "↓"),
            ("-0.5", "-3 - -1", "↑"), ("1e3", "0 - 1e2", "↑"),
            ("1,5", "1 - 2", ""), ("0.1", "0 - 0.1", ""),
            ("3 / 5", "0 - 10", None), ("1,234", "0 - 10", None),
            ("<10", "<5", None), (">60", "90 - 120", None),
            ("<0,5", "<1", None), ("≤ 0.125 (limit)", "<1", None),
        ):
            with self.subTest(value=value, reference=reference):
                self.assertEqual(self.report["get_direction"](value, reference), expected)

    def test_scoring_and_rendering_preserve_the_numeric_value_and_original_text(self):
        score = self.report["calculate_score"]
        self.assertEqual(score("1e3", "0 - 100"), score("1000", "0 - 100"))
        self.assertEqual(score("1e-3", "0 - 1"), score("0.001", "0 - 1"))
        self.assertEqual(score("1,5", "1 - 2"), score("1.5", "1 - 2"))
        self.assertEqual(score("1000", "0 - 1e3"), score("1000", "0 - 1000"))
        for format_name in ("html", "md"):
            formatter = self.report[f"format_cell_{format_name}"]
            for value, reference, arrow in (("-5", "0 - 10", "↓"), ("1e3", "0 - 100", "↑")):
                rendered = formatter(value, reference)
                self.assertIn(value, rendered)
                self.assertIn(arrow, rendered)
            self.assertNotIn("↑", formatter("<10", "<5"))

    def test_malformed_numbers_do_not_get_a_score_or_a_stale_trend(self):
        for raw in ("3 / 5", "1,234", "12 mg/L", "1e+", "1e400", "1e-400"):
            with self.subTest(raw=raw):
                self.assertIsNone(self.report["numeric_from_result"](raw))
                self.assertIsNone(self.report["calculate_score"](raw, "0 - 10"))
                self.assertIsNone(self.report["classify_trend"]([raw, "8", "6"], "0 - 10", "Lab"))
        self.assertIsNone(self.report["calculate_score"]("<unknown", "<unknown"))
        self.assertIsNone(self.report["calculate_score"]("1", "<1e-400"))

    def test_compact_goal_reference_keeps_direction_in_both_report_formats(self):
        category, marker = "Vitals & Functional Health", "Temperature"
        reference = self.report["target_reference"](category, marker, "-")
        for format_name in ("html", "md"):
            formatter = self.report[f"format_cell_{format_name}"]
            for value, arrow in (("35", "↓"), ("38", "↑")):
                with self.subTest(format_name=format_name, value=value):
                    self.assertIn(arrow, formatter(value, reference, category, marker))
            for value in ("36.9", "<35", ">38"):
                with self.subTest(format_name=format_name, value=value):
                    rendered = formatter(value, reference, category, marker)
                    self.assertNotIn("↑", rendered)
                    self.assertNotIn("↓", rendered)

    def test_comparison_endpoints_never_enter_numeric_percentage_changes(self):
        for raw in ("<1e-3", ">0,5", "≤ 0.125 (limit)"):
            with self.subTest(raw=raw):
                self.assertIsNone(self.report["numeric_from_result"](raw))
                self.assertIsNone(self.report["numeric_value"](raw))
                self.assertIsNone(self.report["directional_percent_delta"](raw, "0.1", "<1"))

    def test_new_bound_notations_keep_the_existing_uncertainty_policy(self):
        for raw in (">90,5", ">90.5 (reporting limit)"):
            with self.subTest(raw=raw):
                self.assertIsNone(self.report["calculate_score"](
                    raw, ">60", "Metabolic Health", "eGFR"))
                for format_name in ("html", "md"):
                    rendered = self.report[f"format_cell_{format_name}"](
                        raw, ">60", "Metabolic Health", "eGFR")
                    self.assertIn("🟢", rendered)
                    self.assertNotIn("🔵", rendered)
                    self.assertNotIn("↑", rendered)
                    self.assertNotIn("↓", rendered)

    def test_blood_pressure_accepts_exactly_two_scalar_components(self):
        pair = self.report["numeric_pair_from_result"]
        self.assertEqual(pair("108/70"), (108, 70))
        self.assertEqual(pair("120,5 / 75,5"), (120.5, 75.5))
        for raw in ("120 80", "120/80/70", "120 over 80", "<120/80", "120/80 plus 70"):
            with self.subTest(raw=raw):
                self.assertIsNone(pair(raw))

    def test_urinalysis_reuses_scalar_parsing_without_losing_minus_signs(self):
        format_value = self.report["format_urinalysis_value"]
        self.assertEqual(format_value("-6", "5 - 8")[1], "🟠")
        self.assertEqual(format_value("6,5", "5 - 8")[1], "🟢")
        self.assertEqual(format_value("6/5", "5 - 8")[1], "")


if __name__ == "__main__":
    unittest.main()
