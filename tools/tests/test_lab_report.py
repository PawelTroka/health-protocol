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
            self.assertIsNone(self.report["calculate_score"](values["2026-09"], row[-1], "Stool Pathogen PCR", row[0]))
        for output_format in ("html", "md"):
            rendered = self.report[f"render_result_table_{output_format}"]("Stool Pathogen PCR", rows)
            table = rendered_table_rows(rendered, output_format)
            self.assertEqual([cell for cell in table[0] if re.fullmatch(r"\d{4}-\d{2}", cell)], ["2026-09"])
            self.assertNotIn("Trend", table[0])
            self.assertEqual(Counter(cells[0] for cells in table[1:]), Counter(outcomes.keys()))
            result_index = table[0].index("2026-09")
            for cells in table[1:]:
                expected_dot = "🟠" if outcomes[cells[0]] == "detected" else "🔵"
                self.assertTrue(cells[result_index].startswith(expected_dot + " "), cells)

    def test_pending_registry_excludes_completed_stool_and_proteinogram_results(self):
        pending = [name for names in self.report["lab_pending_tests"].values() for name in names]
        self.assertEqual(len(pending), 11)
        self.assertEqual(len(set(pending)), 11)
        self.assertNotIn("Serum protein electrophoresis (whole panel)", pending)
        self.assertIn("Iodine in 24-hour urine", pending)
        self.assertIn("tTG IgA", pending)
        self.assertNotIn("TSH", pending)
        self.assertNotIn("Calprotectin", pending)
        self.assertNotIn("Pancreatic elastase-1", pending)

    def test_stool_pdf_confirms_portal_values_and_supplies_elastase_reference(self):
        calprotectin = self.observations("Stool Analysis", "Calprotectin (Stool)")
        self.assertEqual(calprotectin["2026-09"], "< 5.0")
        self.assertEqual(calprotectin["2026-07"], "291.70")
        self.assertEqual(self.observations("Stool Analysis", "Pancreatic Elastase-1 (Stool)")["2026-09"], "600.0")
        self.assertEqual(self.row("Stool Analysis", "Pancreatic Elastase-1 (Stool)")[-2:], ("ug/g", ">= 200"))
        score = self.report["calculate_score"]
        args = (">= 200", "Stool Analysis", "Pancreatic Elastase-1 (Stool)")
        self.assertEqual(score("600.0", *args), score("200", *args))
        self.assertGreater(score("199", *args), 1.0)
        self.assertEqual(self.observations("Stool Analysis", "Secretory sIgA (Stool)")["2026-09"], "pending")

    def test_completed_proteinogram_preserves_fractions_concentrations_and_history(self):
        expected = {
            "Total Protein": ("74.90", "g/L", "64.0 - 83.0"),
            "Albumin": ("60.1", "%", "55.8 - 66.1"),
            "Alpha-1 Globulin": ("3.5", "%", "2.9 - 4.9"),
            "Alpha-2 Globulin": ("7.6", "%", "7.1 - 11.8"),
            "Beta-1 Globulin": ("6.4", "%", "4.7 - 7.2"),
            "Beta-2 Globulin": ("4.6", "%", "3.2 - 6.5"),
            "Gamma Globulin": ("17.8", "%", "11.1 - 18.8"),
            "Albumin (Concentration)": ("45.0", "g/L", "40.2 - 47.6"),
            "Alpha-1 Globulin (Concentration)": ("2.6", "g/L", "2.1 - 3.5"),
            "Alpha-2 Globulin (Concentration)": ("5.7", "g/L", "5.1 - 8.5"),
            "Beta-1 Globulin (Concentration)": ("4.8", "g/L", "3.4 - 5.2"),
            "Beta-2 Globulin (Concentration)": ("3.4", "g/L", "2.3 - 4.7"),
            "Gamma Globulin (Concentration)": ("13.3", "g/L", "8.0 - 13.5"),
        }
        january = {"Albumin": "62.3", "Alpha-1 Globulin": "2.9", "Alpha-2 Globulin": "7.0",
                   "Beta-1 Globulin": "5.9", "Beta-2 Globulin": "4.9", "Gamma Globulin": "17.0"}
        self.assertEqual(len(self.report["data"]["Proteinogram"]), len(expected))
        for marker, (value, unit, reference) in expected.items():
            with self.subTest(marker=marker):
                actual = self.observations("Proteinogram", marker)
                self.assertEqual(actual["2026-09"], value)
                self.assertEqual(self.row("Proteinogram", marker)[-2:], (unit, reference))
                for month in self.report["historical_date_columns"]:
                    self.assertEqual(actual[month], january.get(marker, "-") if month == "2026-01" else "-")
        # Electrophoretic albumin does not replace the standalone serum assay.
        self.assertEqual(self.observations("Metabolic Health", "Albumin")["2026-07"], "48.90")
        self.assertEqual(self.observations("Metabolic Health", "Albumin")["2026-09"], "-")

    def test_all_followups_appear_in_september_in_both_generated_reports(self):
        values = [value for observations in self.report["lab_followups"]["2026-09"].values()
                  for value in observations.values()]
        self.assertEqual(sum(value != "pending" for value in values), 99)
        self.assertEqual(values.count("pending"), 3)
        for category, observations in self.report["lab_followups"]["2026-09"].items():
            rows = self.report["data"][category]
            for output_format in ("html", "md"):
                rendered_rows = {}
                for group in self.report["lab_groups"](category, rows):
                    rendered = self.report[f"render_result_table_{output_format}"](category, group["rows"])
                    table = rendered_table_rows(rendered, output_format)
                    header = table[0]
                    with self.subTest(category=category, group=group["title"], output_format=output_format):
                        self.assertIn(rendered, self.outputs[output_format])
                        self.assertNotIn("2026-08", header)
                        self.assertEqual(len(table) - 1, len(group["rows"]))
                    for cells in table[1:]:
                        self.assertNotIn(cells[0], rendered_rows)
                        rendered_rows[cells[0]] = dict(zip(header, cells))
                with self.subTest(category=category, output_format=output_format):
                    self.assertEqual(len(rendered_rows), len(rows))
                for marker, value in observations.items():
                    with self.subTest(category=category, marker=marker, output_format=output_format):
                        self.assertEqual(self.observations(category, marker)["2026-09"], value)
                        self.assertEqual(literal_result(rendered_rows[marker]["2026-09"]), value)

    def test_sparse_followups_do_not_add_empty_september_columns_to_main_tables(self):
        categories = ("Metabolic Health", "Cardiac Health & Coagulation", "Micronutrients",
                      "Immunology & Inflammation", "Hormonal Panel")
        for category in categories:
            groups = self.report["lab_groups"](category, self.report["data"][category])
            self.assertEqual(len(groups), 2)
            for output_format in ("html", "md"):
                for index, group in enumerate(groups):
                    with self.subTest(category=category, group=group["title"], output_format=output_format):
                        rendered = self.report[f"render_result_table_{output_format}"](category, group["rows"])
                        header = rendered_table_rows(rendered, output_format)[0]
                        self.assertEqual("2026-09" in header, index == 1)
                        self.assertIn("Unit", header)
                        self.assertIn("Reference", header)

    def test_stool_abundance_changes_have_ordered_colors_and_trends(self):
        expected = {
            "Starch Grains": ("🟠", "🟡"),
            "Fat Droplets": ("🔵", "🟢"),
            "Fatty Acid Crystals": ("🟢", "🟢"),
            "Muscle Fibers": ("🟢", "⚪"),
            "Mucus": ("🟢", "🟢"),
        }
        category = "Stool Analysis"
        for output_format in ("html", "md"):
            rendered = self.report[f"render_result_table_{output_format}"](category, self.report["data"][category])
            table = rendered_table_rows(rendered, output_format)
            rows = {cells[0]: dict(zip(table[0], cells)) for cells in table[1:]}
            for marker, (color, trend) in expected.items():
                with self.subTest(marker=marker, output_format=output_format):
                    self.assertTrue(rows[marker]["2026-09"].startswith(color + " "))
                    self.assertEqual(rows[marker]["Trend"], trend)
        classify = self.report["classify_trend"]
        for value in ("pending", "inconclusive", "unknown wording"):
            self.assertIsNone(classify([value, "absent", "single in preparation"], "absent", category, "Mucus"))

    def test_urine_bounds_are_colored_without_losing_inequalities(self):
        category = "Urinalysis (Sediment)"
        for output_format in ("html", "md"):
            rendered = self.report[f"render_result_table_{output_format}"](category, self.report["data"][category])
            table = rendered_table_rows(rendered, output_format)
            rows = {cells[0]: dict(zip(table[0], cells)) for cells in table[1:]}
            count = 0
            for row in self.report["data"][category]:
                value = self.observations(category, row[0])["2026-01"]
                if value.startswith("<"):
                    count += 1
                    self.assertEqual(rows[row[0]]["2026-01"], "🟢 " + value)
            self.assertEqual(count, 10)
            format_cell = self.report[f"format_cell_{output_format}_urine"]
            self.assertNotIn("🟢", format_cell("<40", "<30"))
            self.assertIn("🟢", format_cell("<20", "<30"))

    def test_ck_color_respects_the_reported_reference_limits(self):
        category, marker, reference = "Cardiac Health & Coagulation", "Creatine Kinase (CK)", "20 - 200"
        for value in ("19", "201", "222"):
            score = self.report["calculate_score"](value, reference, category, marker)
            self.assertEqual(self.report["get_color_hex"](score)[1], "🟡")
        for value in ("20", "118", "153", "200"):
            score = self.report["calculate_score"](value, reference, category, marker)
            self.assertEqual(self.report["get_color_hex"](score)[1], "🔵")
        for output_format in ("html", "md"):
            rendered = self.report[f"render_result_table_{output_format}"](category, [self.row(category, marker)])
            header, cells = rendered_table_rows(rendered, output_format)
            values = dict(zip(header, cells))
            self.assertEqual(values["2026-07"], "🟡 222 ↑")
            self.assertEqual(values["2026-09"], "🔵 118")
            self.assertEqual(values["2026-01"], "🔵 153")
            self.assertIn(rendered, self.outputs[output_format])

    def test_overlapping_numeric_bounds_cannot_establish_a_trend(self):
        classify = self.report["classify_trend"]
        self.assertIsNone(classify(["101.5", ">60"], ">60", "Metabolic Health", "eGFR"))
        self.assertIsNone(self.report["directional_percent_delta"]("101.5", ">60", ">60"))
        self.assertEqual(classify(["<5.0", "291.70"], "<50", "Stool Analysis", "Calprotectin (Stool)"), "Breakthrough")
        self.assertEqual(classify(["<9", "< 9.0"], "<34", "Immunology & Inflammation", "Anti-TPO"), "Stable")

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
