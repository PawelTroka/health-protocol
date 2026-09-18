"""Interpretation boundaries and presentation checks without live health data."""

from decimal import Decimal
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import patch

from tools.health_sync import report_guidance as guidance
from tools.tests.test_report_layout import rendered_table_rows


VITALS = "Vitals & Functional Health"


class NumericalChangeTests(unittest.TestCase):
    def test_strict_numbers_preserve_signed_decimal_values(self):
        examples = {
            "0": "0", "-2.75": "-2.75", "+0.125": "0.125",
            "~ 80.4": "80.4", " 15.0 ": "15.0",
            "3 (mild dysbiosis)": "3",
        }
        for raw, expected in examples.items():
            with self.subTest(raw=raw):
                actual = guidance.strict_number(raw)
                self.assertIsInstance(actual, Decimal)
                self.assertEqual(actual, Decimal(expected))

    def test_censored_multivalue_and_categorical_data_are_not_numbers(self):
        for raw in ("<3", "> 5", "≤10", "108/76", "Negative: 5", "Normal: 2; Inconclusive: 1",
                    "1-2", "pending", "unknown", "inconclusive", "not available", "-", "", "NaN", "inf"):
            with self.subTest(raw=raw):
                self.assertIsNone(guidance.strict_number(raw))

    def test_changes_are_signed_exact_differences_without_percentage_division(self):
        examples = [
            (["80.4", "79.2"], "↑ +1.2"),
            (["-2.75", "-3.10"], "↑ +0.35"),
            (["0.1", "0.3"], "↓ -0.2"),
            (["0", "1.25"], "↓ -1.25"),
            (["1.25", "0"], "↑ +1.25"),
            (["0.00", "0"], "→ 0"),
            (["4.20", "-", "4.2"], "→ 0"),
        ]
        for values, expected in examples:
            with self.subTest(values=values):
                self.assertEqual(guidance.numerical_change(values), expected)

    def test_newest_unknown_result_does_not_fall_back_to_an_older_trend(self):
        for values in ([], ["3"], ["-", "3"], ["pending", "78", "70"],
                       ["-", "inconclusive", "78", "70"], ["unknown", "78", "70"],
                       ["<3", "2", "1"], ["Normal: 3", "Normal: 2"], ["3", "Negative: 2"]):
            with self.subTest(values=values):
                self.assertEqual(guidance.numerical_change(values), "-")


class ProviderGuidanceTests(unittest.TestCase):
    def assert_status(self, marker, value, emoji):
        status = guidance.guide_status(VITALS, marker, value)
        self.assertIsNotNone(status, (marker, value))
        color, actual_emoji, label = status
        self.assertRegex(color, r"^#[0-9a-fA-F]{6}$")
        self.assertEqual(actual_emoji, emoji)
        self.assertTrue(isinstance(label, str) and label.strip())

    def test_oura_scores_use_provider_bands_at_every_boundary(self):
        markers = ("Sleep Score", "Readiness Score (Oura)", "Activity Score (Oura)",
                   "Sleep Efficiency Contributor Score (Oura)")
        for marker in markers:
            for value, emoji in (("0", "🟠"), ("59.9", "🟠"), ("60", "🟡"),
                                 ("69.9", "🟡"), ("70", "🟢"), ("84.9", "🟢"),
                                 ("85", "🔵"), ("100", "🔵")):
                with self.subTest(marker=marker, value=value):
                    self.assert_status(marker, value, emoji)
            for value in ("-0.1", "100.1", "pending", "<85"):
                with self.subTest(marker=marker, invalid=value):
                    self.assertIsNone(guidance.guide_status(VITALS, marker, value))

    def test_withings_sleep_score_uses_its_own_provider_boundaries(self):
        for value, emoji in (("0", "🟠"), ("49.9", "🟠"), ("50", "🟡"),
                             ("74.9", "🟡"), ("75.1", "🟢"), ("100", "🟢")):
            with self.subTest(value=value):
                self.assert_status("Sleep Score (Withings)", value, emoji)
        for value in ("-1", "75", "101", "pending"):
            self.assertIsNone(guidance.guide_status(VITALS, "Sleep Score (Withings)", value))

    def test_withings_visceral_fat_is_an_index_with_bounded_provider_guidance(self):
        for value, emoji in (("0", "🟢"), ("5", "🟢"), ("5.1", "🟠"), ("20", "🟠")):
            with self.subTest(value=value):
                self.assert_status("Visceral Fat Index", value, emoji)
        for value in ("-1", "21", "pending", "5%"):
            with self.subTest(invalid=value):
                self.assertIsNone(guidance.guide_status(VITALS, "Visceral Fat Index", value))

    def test_nerve_health_preserves_boundary_and_separates_confirmed_from_api_means(self):
        self.assert_status("Nerve Health Score", "49", "🟠")
        self.assert_status("Nerve Health Score", "51", "🟢")
        for value in ("50", "pending", "-1", "101"):
            with self.subTest(value=value):
                self.assertIsNone(guidance.guide_status(VITALS, "Nerve Health Score", value))
        for marker in ("Nerve Health Score Feet (Withings)",
                       "Nerve Health Score Left Foot (Withings)", "Nerve Health Score Right Foot (Withings)"):
            with self.subTest(marker=marker):
                self.assert_status(marker, "69", "🟢")
                self.assert_status(marker, "49", "🟡")
                self.assertIsNone(guidance.guide_status(VITALS, marker, "50"))
                self.assertIn("comparison", guidance.guide_reference(VITALS, marker, "-"))

    def test_sleep_latency_is_not_monotonically_better_when_shorter(self):
        for value in ("15", "20"):
            self.assert_status("Sleep Latency", value, "🔵")
        for value in ("5", "14.9", "20.1", "30"):
            with self.subTest(value=value):
                self.assert_status("Sleep Latency", value, "🟢")
        for value in ("0", "4.9", "30.1", "45"):
            with self.subTest(value=value):
                self.assert_status("Sleep Latency", value, "🟡")
        self.assertIsNone(guidance.guide_status(VITALS, "Sleep Latency", "-1"))

    def test_sleep_efficiency_and_oxygen_saturation_do_not_accept_impossible_percentages(self):
        for marker, low, threshold in (("Sleep Efficiency", "84.9", "85"),
                                       ("Average Sleeping SpO2 (Oura)", "94.9", "95")):
            self.assert_status(marker, low, "🟡")
            self.assert_status(marker, threshold, "🟢")
            self.assert_status(marker, "100", "🟢")
            for value in ("-0.1", "100.1", "pending"):
                with self.subTest(marker=marker, value=value):
                    self.assertIsNone(guidance.guide_status(VITALS, marker, value))

    def test_unknown_and_anthropometric_metrics_do_not_receive_invented_healthy_targets(self):
        for marker in ("Height", "Right Foot Length", "Chest Circumference",
                       "Waist Circumference (Narrowest Point)", "Future Firmware Marker (Oura)"):
            with self.subTest(marker=marker):
                self.assertIsNone(guidance.guide_status(VITALS, marker, "85"))
        self.assertIsNone(guidance.guide_reference("Other category", "Sleep Score", "lab range"))
        # An unsupported measurement-site target stays absent; explanatory
        # measurement guidance belongs in source notes, not each result cell.
        self.assertIsNone(guidance.guide_reference(
            VITALS, "Waist Circumference (Narrowest Point)", "-"))


class VitalsTrendTests(unittest.TestCase):
    def test_supported_directions_and_target_changes_use_emoji_without_magnitude_claims(self):
        cases = (
            ("Sleep Score", ["80.4", "78.7"], "🟢"),
            ("Sleep Score", ["90", "80"], "🟢"),
            ("Sleep Score", ["90", "55"], "🟢"),
            ("Readiness Score (Oura)", ["69.9", "76.1"], "🟡"),
            ("Sleep Efficiency Contributor Score (Oura)", ["86", "81.8"], "🟢"),
            ("Sleep Efficiency", ["86.3", "84.6"], "🟢"),
            ("Sleep Efficiency", ["95", "90"], "⚪"),
            ("Average Sleeping SpO2 (Oura)", ["95", "94.7"], "🟢"),
            ("Visceral Fat Index", ["2.4", "2.5"], "⚪"),
            ("Visceral Fat Index", ["5", "6"], "🟢"),
            ("Sleep Score (Withings)", ["76", "74"], "🟢"),
            # Ambiguous category boundaries do not erase a known numerical
            # direction toward a target or a better provider quality score.
            ("Sleep Score (Withings)", ["75", "49"], "🟢"),
            ("Nerve Health Score", ["50", "49"], "🟢"),
            ("Nerve Health Score", ["51", "49"], "🟢"),
        )
        for marker, values, expected in cases:
            with self.subTest(marker=marker, values=values):
                self.assertEqual(guidance.vitals_trend(values, marker), expected)

    def test_latency_target_entry_exit_and_outside_changes(self):
        for values, expected in ((["16.8", "22.7"], "🟢"), (["5", "16"], "🟡"),
                                 (["5", "22"], "🟡"), (["18", "16"], "⚪")):
            with self.subTest(values=values):
                self.assertEqual(guidance.vitals_trend(values, "Sleep Latency"), expected)

    def test_context_dependent_and_future_metrics_never_invent_a_direction(self):
        for marker in ("Max HRV", "Highest 5-minute Nightly HRV (Garmin)",
                       "Resilience Stress Contributor Score (Oura)",
                       "Primary Sleep Score Change (Oura)", "Future Firmware Marker"):
            for values in (["90", "50"], ["50", "90"], ["50", "50"]):
                with self.subTest(marker=marker, values=values):
                    self.assertEqual(guidance.vitals_trend(values, marker), "⚪")

    def test_newest_unknown_or_incomparable_result_blocks_older_trends(self):
        for values in ([], ["80"], ["pending", "90", "80"], ["unknown", "90", "80"],
                       ["inconclusive", "90", "80"], ["<90", "80", "70"],
                       ["Negative: 5", "Negative: 6"], ["80", "unknown", "70"]):
            with self.subTest(values=values):
                self.assertEqual(guidance.vitals_trend(values, "Sleep Score"), "-")
        self.assertEqual(guidance.vitals_trend(["-", "90", "-", "80"], "Sleep Score"), "🟢")
        self.assertEqual(guidance.vitals_trend(["180", "180"], "Height"), "-")
        self.assertEqual(guidance.vitals_trend(["180", "180"], "Height (Withings)"), "-")


class StoolResidueGuidanceTests(unittest.TestCase):
    def test_reported_abundance_is_ordered_for_each_residue_marker(self):
        expected = (
            ("absent", 0, "🔵"),
            ("absent in preparation", 0, "🔵"),
            ("single in preparation", 1, "🟢"),
            ("few in preparation", 2, "🟡"),
            ("fairly numerous in preparation", 3, "🟠"),
        )
        for marker in ("Starch Grains", "Fat Droplets", "Fatty Acid Crystals", "Muscle Fibers", "Mucus"):
            for value, rank, emoji in expected:
                with self.subTest(marker=marker, value=value):
                    self.assertEqual(guidance.stool_residue_rank("Stool Analysis", marker, value), rank)
                    status = guidance.guide_status("Stool Analysis", marker, value)
                    self.assertEqual(status[1], emoji)
                    self.assertIn("absent", status[2].lower())

    def test_abundance_is_not_generalized_to_other_markers_or_unknown_wording(self):
        for category, marker, value in (
            ("Urinalysis (Microscopic)", "Mucus", "few in preparation"),
            ("Stool Analysis", "Yeast Cells", "few in preparation"),
            ("Stool Analysis", "Leukocytes on Mucus", "present"),
            ("Stool Analysis", "Starch Grains", "Pending"),
            ("Stool Analysis", "Starch Grains", "not absent in preparation"),
            ("Stool Analysis", "Starch Grains", "few to fairly numerous in preparation"),
            ("Stool Analysis", "Starch Grains", "numerous in preparation"),
            ("Stool Analysis", "Starch Grains", None),
        ):
            with self.subTest(category=category, marker=marker, value=value):
                self.assertIsNone(guidance.stool_residue_rank(category, marker, value))
                self.assertIsNone(guidance.guide_status(category, marker, value))


class GuidanceRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Only load definitions. The monthly fixture and report destination are
        # isolated, so these checks cannot sync accounts or rewrite the reports.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "monthly.json"
            source.write_text(json.dumps({"schema_version": 1, "as_of": "2026-09-07", "months": {}}), encoding="utf-8")
            with patch.dict(os.environ, {
                "HEALTH_PROTOCOL_VITALS_MONTHLY": str(source),
                "HEALTH_PROTOCOL_REPORT_DIR": str(root),
            }):
                cls.report = runpy.run_path(
                    str(Path(__file__).parents[1] / "generate_colored_report.py"),
                    run_name="guidance_test",
                )
            cls.loaded_files = {path.name for path in root.iterdir()}

    def row(self, marker, observations, unit="score"):
        return (marker, *(observations.get(month, "-") for month in self.report["date_columns"]), unit, "-")

    def test_loading_definitions_does_not_generate_reports(self):
        self.assertEqual(self.loaded_files, {"monthly.json"})

    def test_both_outputs_show_guidance_and_trend_next_to_metric_without_empty_dates(self):
        row = self.row("Sleep Score", {"2026-09": "90", "2026-07": "80"})
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = self.report[f"render_result_table_{output_format}"](VITALS, [row], compact=True)
                header, result = rendered_table_rows(rendered, output_format)
                self.assertEqual(header[:2], ["Metric", "Trend"])
                self.assertIn("Reference", header)
                self.assertEqual([cell for cell in header if re.fullmatch(r"\d{4}-\d{2}", cell)], ["2026-09", "2026-07"])
                self.assertEqual(len(header), len(result))
                self.assertIn("90", result[header.index("2026-09")])
                self.assertIn("🔵", result[header.index("2026-09")])
                self.assertIn("85", result[header.index("Reference")])
                self.assertNotEqual(result[1], "-")

    def test_bone_uses_comparison_color_and_flat_trend_within_its_range(self):
        row = self.row("Bone", {"2026-09": "4.2", "2026-07": "4.1"}, "%")
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = self.report[f"render_result_table_{output_format}"](VITALS, [row], compact=True)
                header, result = rendered_table_rows(rendered, output_format)
                self.assertEqual(header[:2], ["Metric", "Trend"])
                self.assertEqual(result[1], "⚪")
                cell = result[header.index("2026-09")]
                self.assertIn("4.2", cell)
                self.assertIn("🟢", cell)
                self.assertEqual(result[header.index("Reference")], "3–5")

    def test_both_renderers_use_emoji_for_known_and_unknown_vital_trends(self):
        cases = (("Sleep Efficiency", "86.3", "84.6", "🟢"),
                 ("Sleep Score", "80.4", "78.7", "🟢"),
                 ("Sleep Latency", "16.8", "22.7", "🟢"),
                 ("Steps (Garmin)", "5000", "4000", "🟢"),
                 ("Future Firmware Marker", "12", "11", "⚪"))
        for marker, current, previous, expected in cases:
            for output_format in ("html", "md"):
                with self.subTest(marker=marker, format=output_format):
                    row = self.row(marker, {"2026-09": current, "2026-07": previous})
                    rendered = self.report[f"render_result_table_{output_format}"](VITALS, [row], compact=True)
                    header, result = rendered_table_rows(rendered, output_format)
                    self.assertEqual(result[header.index("Trend")], expected)

    def test_scored_vitals_do_not_reuse_older_pairs_after_unknown_result(self):
        for output_format in ("html", "md"):
            formatter = self.report[f"format_trend_{output_format}"]
            self.assertEqual(formatter(["unknown", "18", "25"], "10 - 20", VITALS, "Body Fat"), "-")
            self.assertEqual(formatter(["15", "unknown", "25"], "10 - 20", VITALS, "Body Fat"), "-")
            self.assertEqual(formatter(["12", "15"], "10 - 20", VITALS, "Body Fat"), "⚪")

    def test_unclassified_results_are_literal_values_without_neutral_dots_or_boilerplate(self):
        row = self.row("Chest Circumference", {"2026-09": "105"}, "cm")
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = self.report[f"render_result_table_{output_format}"](VITALS, [row], compact=True)
                header, result = rendered_table_rows(rendered, output_format)
                self.assertEqual(result[header.index("2026-09")], "105")
                self.assertNotIn("Trend", header)
                self.assertNotIn("Reference", header)
                self.assertNotRegex(rendered, r"⚪|[Uu]nclassified|no separate target|no clinical target")

    def test_references_preserve_supplied_ranges_without_filler(self):
        rows = [self.row("Future Laboratory Marker", {"2026-09": "12.5"})]
        for ref in ("-", "2–20"):
            row = (*rows[0][:-1], ref)
            with self.subTest(ref=ref):
                self.assertEqual(self.report["target_reference"]("Other laboratory category", row[0], ref), ref)
                for output_format in ("html", "md"):
                    rendered = self.report[f"render_result_table_{output_format}"]("Other laboratory category", [row])
                    header, result = rendered_table_rows(rendered, output_format)
                    self.assertIn("Reference", header)
                    self.assertEqual(result[header.index("Reference")], ref)
                    self.assertNotIn("no separate target", rendered)


if __name__ == "__main__":
    unittest.main()
