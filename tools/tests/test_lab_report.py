"""September lab transcription and rendering regressions; no private PDF reads."""

from collections import Counter
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import patch

from tools.tests.test_report_layout import rendered_table_rows


def literal_result(cell):
    """Strip display status while retaining the literal measurement/inequality."""
    return re.sub(r"\s+[↑↓]$", "", re.sub(r"^[⚪🔵🟢🟡🟠🔴]\s+", "", cell))


class SeptemberLabReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Definitions are loaded without main and with synthetic monthly input.
        # Generators write only into this temporary directory, never the repo.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "monthly.json"
            source.write_text(json.dumps({
                "schema_version": 1, "as_of": "2026-09-17", "months": {},
            }), encoding="utf-8")
            with patch.dict(os.environ, {
                "HEALTH_PROTOCOL_VITALS_MONTHLY": str(source),
                "HEALTH_PROTOCOL_REPORT_DIR": str(root),
            }):
                cls.report = runpy.run_path(
                    str(Path(__file__).parents[1] / "generate_colored_report.py"),
                    run_name="lab_report_test",
                )
            cls.loaded_files = {path.name for path in root.iterdir()}
            cls.outputs = {}
            for output_format in ("html", "md"):
                path = root / f"results.{output_format}"
                cls.report[f"generate_{output_format}_report"](path)
                cls.outputs[output_format] = path.read_text(encoding="utf-8")

    def row(self, category, marker):
        return next(row for row in self.report["data"][category] if row[0] == marker)

    def observations(self, category, marker):
        _, values, _, _ = self.report["split_result_row"](self.row(category, marker))
        return dict(zip(self.report["date_columns"], values))

    def test_loading_definitions_does_not_generate_reports(self):
        self.assertEqual(self.loaded_files, {"monthly.json"})

    def test_historical_thyroid_eosinophils_and_hs_crp_remain_unchanged(self):
        expected = {
            ("Hormonal Panel", "TSH"): ("4.57", "3.17", "1.68", "3.54"),
            ("Hormonal Panel", "Free T3 (FT3)"): ("5.47", "4.54", "4.29", "5.57"),
            ("Hormonal Panel", "Free T4 (FT4)"): ("19.80", "16.30", "20.67", "17.70"),
            ("Morphology", "Eosinophils"): ("0.5", "0.5", "0.42", "0.55"),
            ("Morphology", "Eosinophils %"): ("7.7", "6.5", "7.6", "6.0"),
            ("Immunology & Inflammation", "CRP (hs)"): ("0.611", "0.448", "< 0.15", "not detected"),
        }
        for (category, marker), values in expected.items():
            with self.subTest(category=category, marker=marker):
                actual = self.observations(category, marker)
                self.assertEqual(tuple(actual[month] for month in self.report["historical_date_columns"]), values)

    def test_stool_pcr_does_not_replace_cultures_antigen_tests_or_inflammation(self):
        for marker in ("Salmonella species", "Shigella species", "Yersinia species",
                       "Aeromonas species", "Plesiomonas species"):
            with self.subTest(marker=marker):
                actual = self.observations("Stool Culture", marker)
                self.assertEqual(actual["2026-07"], "negative")
                self.assertEqual(actual["2026-09"], "-")
        for marker, july in {
            "Giardia lamblia Antigen": "negative",
            "Helicobacter pylori Antigen": "0.12 (not detected)",
            "Calprotectin (Stool)": "291.70",
            "Secretory sIgA (Stool)": "5023.4",
        }.items():
            with self.subTest(marker=marker):
                self.assertEqual(self.observations("Stool Analysis", marker)["2026-07"], july)

    def test_completed_new_assays_preserve_exact_values_units_and_reference_ranges(self):
        expected = {
            ("Immunology & Inflammation", "CRP (Conventional)"): ("0.7", "mg/L", "< 5.0"),
            ("Immunology & Inflammation", "IgA (Serum)"): ("3.0", "g/L", "0.7 - 4.0"),
            ("Immunology & Inflammation", "Rheumatoid Factor (RF)"): ("< 10", "IU/mL", "< 14"),
            ("Immunology & Inflammation", "Anti-CCP"): ("<8", "U/mL", "< 17.00"),
            ("Immunology & Inflammation", "TSH Receptor Antibodies (TRAb)"):
                ("< 0.14", "IU/L", "< 0.550: negative; >= 0.550: positive"),
            ("Immunology & Inflammation", "Complement C3"): ("89", "mg/dL", "90 - 180"),
            ("Immunology & Inflammation", "Complement C4"): ("14.2", "mg/dL", "10.0 - 40.0"),
        }
        for (category, marker), (value, unit, reference) in expected.items():
            with self.subTest(marker=marker):
                self.assertEqual(self.observations(category, marker)["2026-09"], value)
                self.assertEqual(self.row(category, marker)[-2:], (unit, reference))
                self.assertTrue(all(self.observations(category, marker)[month] == "-"
                                    for month in self.report["historical_date_columns"]))
        self.assertEqual(self.observations("Immunology & Inflammation", "CRP (hs)")["2026-09"], "-")
        self.assertEqual(self.observations("Morphology", "Eosinophils")["2026-09"], "1.1")
        self.assertEqual(self.observations("Morphology", "Eosinophils %")["2026-09"], "15.5")
        self.assertEqual(self.observations("Immunology & Inflammation", "ASO")["2026-09"], "390")
        for marker, value in {"TSH": "4.25", "Free T3 (FT3)": "5.66", "Free T4 (FT4)": "19.70"}.items():
            self.assertEqual(self.observations("Hormonal Panel", marker)["2026-09"], value)
        for marker, value in {"Yeast Cells": "present", "Occult Blood (Human Hemoglobin)": "negative"}.items():
            self.assertEqual(self.observations("Stool Analysis", marker)["2026-09"], value)

    def test_pcr_preserves_all_21_reported_lines_and_only_epec_is_detected(self):
        rows = self.report["data"]["Stool Pathogen PCR"]
        self.assertEqual(len(rows), 21)
        self.assertEqual(len({row[0] for row in rows}), 21)
        outcomes = {row[0]: self.observations("Stool Pathogen PCR", row[0])["2026-09"] for row in rows}
        self.assertEqual(Counter(outcomes.values()), {"detected": 1, "not detected": 20})
        self.assertEqual(outcomes["Enteropathogenic E. coli (EPEC)"], "detected")
        self.assertEqual(outcomes["Shiga-like Toxin-producing E. coli (STEC) stx1/stx2"], "not detected")
        self.assertIn("Vibrio (parahaemolyticus, vulnificus, cholerae)", outcomes)
        self.assertIn("Vibrio cholerae", outcomes)
        for row in rows:
            values = self.observations("Stool Pathogen PCR", row[0])
            self.assertTrue(all(value == "-" for month, value in values.items() if month != "2026-09"))
        for output_format in ("html", "md"):
            rendered = self.report[f"render_result_table_{output_format}"]("Stool Pathogen PCR", rows)
            table = rendered_table_rows(rendered, output_format)
            self.assertEqual([cell for cell in table[0] if re.fullmatch(r"\d{4}-\d{2}", cell)], ["2026-09"])
            self.assertNotIn("Trend", table[0])
            self.assertEqual(Counter(cells[0] for cells in table[1:]), Counter(outcomes.keys()))

    def test_pending_registry_excludes_two_completed_portal_results(self):
        pending = [name for names in self.report["lab_pending_tests"].values() for name in names]
        self.assertEqual(len(pending), 12)
        self.assertEqual(len(set(pending)), 12)
        self.assertIn("Serum protein electrophoresis (whole panel)", pending)
        self.assertIn("Iodine in 24-hour urine", pending)
        self.assertIn("tTG IgA", pending)
        self.assertNotIn("TSH", pending)
        self.assertNotIn("Calprotectin", pending)
        self.assertNotIn("Pancreatic elastase-1", pending)

    def test_portal_completion_preserves_inequality_history_and_missing_reference(self):
        calprotectin = self.observations("Stool Analysis", "Calprotectin (Stool)")
        self.assertEqual(calprotectin["2026-09"], "< 5.0")
        self.assertEqual(calprotectin["2026-07"], "291.70")
        self.assertEqual(self.observations("Stool Analysis", "Pancreatic Elastase-1 (Stool)")["2026-09"], "600.0")
        self.assertEqual(self.row("Stool Analysis", "Pancreatic Elastase-1 (Stool)")[-2:], ("ug/g", "-"))
        self.assertIsNone(self.report["calculate_score"]("600.0", "-", "Stool Analysis", "Pancreatic Elastase-1 (Stool)"))
        self.assertEqual(self.observations("Stool Analysis", "Secretory sIgA (Stool)")["2026-09"], "pending")
        for marker in ("Calprotectin (Stool)", "Pancreatic Elastase-1 (Stool)"):
            numbers = self.report["note_numbers"]("Stool Analysis", marker, "value", "2026-09")
            notes = [self.report["result_notes"]["Stool Analysis"][number - 1]["text"] for number in numbers]
            self.assertTrue(any("portal screenshots" in note for note in notes))
            self.assertFalse(any("single specimens collected September 16" in note for note in notes))

    def test_all_followups_appear_in_september_in_both_generated_reports(self):
        values = [value for observations in self.report["lab_followups"]["2026-09"].values()
                  for value in observations.values()]
        self.assertEqual(sum(value != "pending" for value in values), 86)
        self.assertEqual(values.count("pending"), 9)
        for category, observations in self.report["lab_followups"]["2026-09"].items():
            rows = self.report["data"][category]
            for output_format in ("html", "md"):
                rendered = self.report[f"render_result_table_{output_format}"](category, rows)
                table = rendered_table_rows(rendered, output_format)
                header = table[0]
                rendered_rows = {cells[0]: cells for cells in table[1:]}
                with self.subTest(category=category, output_format=output_format):
                    self.assertIn(rendered, self.outputs[output_format])
                    self.assertIn("2026-09", header)
                    self.assertNotIn("2026-08", header)
                    self.assertEqual(len(rendered_rows), len(rows))
                for marker, value in observations.items():
                    with self.subTest(category=category, marker=marker, output_format=output_format):
                        self.assertEqual(self.observations(category, marker)["2026-09"], value)
                        self.assertEqual(literal_result(rendered_rows[marker][header.index("2026-09")]), value)

    def test_pending_results_are_unscored_and_block_stale_trends(self):
        pending = [(category, marker)
                   for category, observations in self.report["lab_followups"]["2026-09"].items()
                   for marker, value in observations.items() if value == "pending"]
        self.assertTrue(pending)
        for category, marker in pending:
            row = self.row(category, marker)
            _, values, _, ref = self.report["split_result_row"](row)
            with self.subTest(category=category, marker=marker):
                self.assertIsNone(self.report["calculate_score"]("pending", ref, category, marker))
                self.assertIsNone(self.report["trend_score"]("pending", ref, category, marker))
                self.assertIsNone(self.report["classify_trend"](values, ref, category, marker))
                for output_format in ("html", "md"):
                    self.assertEqual(self.report[f"format_trend_{output_format}"](values, ref, category, marker), "-")
                    rendered = self.report[f"render_result_table_{output_format}"](category, [row])
                    header, cells = rendered_table_rows(rendered, output_format)
                    self.assertNotIn("Trend", header)
                    self.assertEqual(cells[header.index("2026-09")], "pending")
        # TSH previously had a trend; pending cannot merely fall through to July.
        values = ["pending", "-", "4.57", "3.17", "1.68", "3.54"]
        self.assertIsNone(self.report["classify_trend"](values, "0.27 - 4.20", "Hormonal Panel", "TSH"))


if __name__ == "__main__":
    unittest.main()
