"""Complete result labels must not be inferred from words inside other text."""

from html import escape
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch


class QualitativeResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load definitions with synthetic input; never write reports or read PDFs.
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "monthly.json"
            source.write_text(json.dumps({
                "schema_version": 1, "as_of": "2026-11-20", "months": {},
            }), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(source)}):
                cls.report = runpy.run_path(
                    str(Path(__file__).parents[1] / "generate_colored_report.py"),
                    run_name="qualitative_result_test",
                )

    def test_urine_unknown_negated_and_mixed_labels_have_no_grade(self):
        for value in (
            "abnormal", "not normal", "unclear", "not clear", "not present",
            "cannot be detected", "not negative", "not non-reactive", "not yellow",
            "normal / abnormal", "positive / negative", "normal but cloudy",
            "inconclusive (normal sample?)", "pending (normal sample?)",
            "nieobecne", "nieliczne", "niemętny",
        ):
            with self.subTest(value=value):
                self.assertEqual(self.report["format_urinalysis_value"](value, "absent"),
                                 ("#000000", ""))
                for output_format in ("html", "md"):
                    rendered = self.report[f"format_cell_{output_format}_urine"](value, "absent")
                    self.assertNotRegex(rendered, "[🔵🟢🟡🟠🔴]")

    def test_trends_do_not_grade_text_containing_known_words(self):
        for value in (
            "abnormal", "not normal", "unclear", "not clear", "not present",
            "cannot be detected", "not negative", "not non-reactive", "not yellow",
            "normal / abnormal", "positive / negative", "normal but cloudy",
            "inconclusive (normal sample?)", "pending (normal sample?)",
        ):
            with self.subTest(value=value):
                self.assertIsNone(self.report["trend_score"](value, "normal", "Urinalysis", "Clarity"))

    def test_unrecognized_label_pair_has_no_trend(self):
        for values in (
            ["abnormal", "normal"], ["normal", "abnormal"],
            ["not present", "absent"], ["absent", "not present"],
            ["normal but cloudy", "cloudy"], ["positive / negative", "positive"],
        ):
            with self.subTest(values=values):
                self.assertIsNone(self.report["classify_trend"](values, "normal", "Urinalysis", "Clarity"))
                for output_format in ("html", "md"):
                    self.assertEqual(self.report[f"format_trend_{output_format}"](
                        values, "normal", "Urinalysis", "Clarity"), "-")

    def test_generic_normal_prefix_does_not_grade_free_text(self):
        for value in ("normal / abnormal", "normal but cloudy", "normal (except for blood)",
                      "normal sinus rhythm / abnormal", "normal range unknown"):
            with self.subTest(value=value):
                self.assertIsNone(self.report["calculate_score"](value, "normal"))
                for output_format in ("html", "md"):
                    rendered = self.report[f"format_cell_{output_format}"](value, "normal")
                    self.assertNotRegex(rendered, "[🔵🟢🟡🟠🔴]")

    def test_complete_normal_annotations_keep_existing_grades(self):
        for value in ("normal", "normal sinus rhythm", "minor",
                      "normal (no signs of valvular heart disease)", "normal (apex area)"):
            with self.subTest(value=value):
                self.assertEqual(self.report["calculate_score"](value, "normal"), 0.0)
                self.assertTrue(self.report["format_cell_md"](value, "normal").startswith("🔵 "))

    def test_urine_recognized_labels_keep_existing_grades(self):
        expected = {
            "🔵": ("not detected", "absent", "normal", "clear", "negative", "non-reactive",
                  "neg", "light yellow", "yellow", "pale yellow", "słomkowy"),
            "🔴": ("present", "detected", "cloudy", "turbid", "bloody", "obecne", "liczne",
                  "mętny", "krwisty"),
        }
        for emoji, values in expected.items():
            for value in values:
                with self.subTest(value=value):
                    self.assertEqual(self.report["format_cell_md_urine"](value, "normal"),
                                     f"{emoji} {value}")
                    self.assertIn(f"{emoji} {value}</span>",
                                  self.report["format_cell_html_urine"](value, "normal"))

    def test_recognized_labels_ignore_case_and_spacing(self):
        for value, emoji, score in (("  NOT\tDETECTED  ", "🔵", 0.0),
                                    (" LIGHT   Yellow ", "🔵", 0.0),
                                    ("  PRESENT ", "🔴", 3.0)):
            with self.subTest(value=value):
                self.assertEqual(self.report["format_cell_md_urine"](value, "normal"),
                                 f"{emoji} {value}")
                self.assertEqual(self.report["trend_score"](value, "normal", "Urinalysis", "Clarity"),
                                 score)
        self.assertEqual(self.report["calculate_score"](" NORMAL   SINUS RHYTHM ", "normal"), 0.0)
        self.assertEqual(self.report["qualitative_status"](" NOT\tDETECTED ")[1], "🔵")

    def test_qualitative_assay_special_cases_keep_existing_display(self):
        for value, emoji, marker in (("negative at 1:80", "🔵", "ANA IIFT"),
                                     ("equivocal (+)", "🟡", "Centromere B")):
            with self.subTest(value=value):
                self.assertEqual(self.report["qualitative_status"](value)[1], emoji)
                self.assertIsNone(self.report["calculate_score"](
                    value, "negative", "Immunology & Inflammation", marker))
                self.assertTrue(self.report["format_cell_md"](
                    value, "negative", "Immunology & Inflammation", marker).startswith(emoji + " "))
        self.assertEqual(self.report["qualitative_status"]("negative at 1:80 / positive"),
                         self.report["NEUTRAL"])

    def test_unknown_result_text_stays_escaped(self):
        value = "normal <sample> & abnormal"
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                self.assertEqual(self.report[f"format_cell_{output_format}_urine"](value, "normal"),
                                 escape(value))
                self.assertEqual(self.report[f"format_cell_{output_format}"](value, "normal"),
                                 escape(value))

    def test_numeric_urine_values_and_recognized_trends_are_unchanged(self):
        for value, reference, emoji in (("6.5", "5 - 8", "🟢"), ("9", "5 - 8", "🟠"),
                                         ("1.020", "1.005 - 1.03", "🟢")):
            with self.subTest(value=value):
                self.assertEqual(self.report["format_cell_md_urine"](value, reference),
                                 f"{emoji} {value}")
        for values, expected in ((["normal", "normal"], "Stable"),
                                 (["clear", "cloudy"], "Breakthrough"),
                                 (["present", "absent"], "Critical Decline")):
            with self.subTest(values=values):
                self.assertEqual(self.report["classify_trend"](values, "normal", "Urinalysis", "Clarity"),
                                 expected)


if __name__ == "__main__":
    unittest.main()
