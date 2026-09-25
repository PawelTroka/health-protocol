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
    cell = re.sub(r"\\([()])", r"\1", cell)
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

    def test_pending_registry_excludes_all_completed_assays(self):
        pending = [name for names in self.report["lab_pending_tests"].values() for name in names]
        self.assertEqual(Counter(pending), Counter([
            "Histamine", "Butyric acid", "Zonulin", "Iodine in 24-hour urine",
            "Urine culture",
        ]))
        self.assertNotIn("Serum protein electrophoresis (whole panel)", pending)
        self.assertNotIn("ANA/ENA immunoblot", pending)
        for completed in ("ANA (IIFT + titre)", "DGP IgG", "tTG IgA", "Secretory sIgA", "Selenium"):
            self.assertNotIn(completed, pending)
        self.assertNotIn("TSH", pending)
        self.assertNotIn("Calprotectin", pending)
        self.assertNotIn("Pancreatic elastase-1", pending)

    def test_invalid_or_missing_urine_assays_do_not_become_results(self):
        excluded = {"ANA (IIFT + titre)", "Cystine", "Urine Cystine",
                    "Iodine in 24-hour urine"}
        for category, rows in self.report["data"].items():
            with self.subTest(category=category):
                self.assertTrue(excluded.isdisjoint(row[0] for row in rows))
        for category, observations in self.report["lab_followups"]["2026-09"].items():
            with self.subTest(category=category):
                self.assertTrue(excluded.isdisjoint(observations))
        # The new urine PDFs supply no usable chemistry measurements.
        # Repeat-required wording must not replace the historical concentrations.
        july = {
            "Urine Creatinine": "59.1", "Urine Albumin (Microalbuminuria)": "<3",
            "Urine Protein": "0.06", "Urine Amylase": "98", "Urine Potassium": "7.12",
            "Urine Sodium": "15.5", "Urine Urea": "2249", "Urine Calcium": "11.3",
            "Urine Magnesium": "7.1", "Urine Phosphate": "26.40", "Urine Chloride": "11",
        }
        rows = self.report["data"]["Urine Chemistry"]
        self.assertEqual({row[0] for row in rows}, set(july))
        for marker, previous in july.items():
            with self.subTest(marker=marker):
                values = self.observations("Urine Chemistry", marker)
                self.assertEqual(values["2026-09"], "-")
                self.assertEqual(values["2026-07"], previous)
        for output_format in ("html", "md"):
            rendered = self.report[f"render_result_table_{output_format}"]("Urine Chemistry", rows)
            table = rendered_table_rows(rendered, output_format)
            self.assertNotIn("2026-09", table[0])
            self.assertNotIn("Trend", table[0])

    def test_completed_celiac_and_stool_m2pk_assays_appear_in_main_tables(self):
        expected = {
            ("Immunology & Inflammation", "tTG IgA"):
                ("< 2.00", "RU/ml", "< 20.0: negative; >= 20.0: positive"),
            ("Immunology & Inflammation", "DGP IgG"):
                ("< 2.0", "RU/ml", "< 25: negative; >= 25: positive"),
            ("Stool Analysis", "M2-PK (Stool)"):
                ("< 1.00", "U/ml", "0.0 - 4.0"),
        }
        for (category, marker), (value, unit, reference) in expected.items():
            with self.subTest(marker=marker):
                observations = self.observations(category, marker)
                self.assertEqual(observations["2026-09"], value)
                self.assertTrue(all(result == "-" for month, result in observations.items()
                                    if month != "2026-09"))
                self.assertEqual(self.row(category, marker)[-2:], (unit, reference))
                group = next(group for group in self.report["lab_groups"](
                    category, self.report["data"][category])
                    if marker in [row[0] for row in group["rows"]])
                if category == "Immunology & Inflammation":
                    self.assertEqual(group["title"], "Immune Markers & Antibodies")
                for output_format, output in self.outputs.items():
                    with self.subTest(output_format=output_format):
                        rendered = self.report[f"render_result_table_{output_format}"](
                            category, group["rows"])
                        self.assertIn(rendered, output)
                        table = rendered_table_rows(rendered, output_format)
                        cells = next(row for row in table[1:] if row[0] == marker)
                        displayed = dict(zip(table[0], cells))
                        self.assertEqual(displayed["2026-09"], "🔵 " + value)
                        self.assertEqual(displayed["Unit"], unit)
                        self.assertEqual(displayed["Trend"], "-")
                        for month in self.report["historical_date_columns"]:
                            if month in displayed:
                                self.assertEqual(displayed[month], "-")
                        if output_format == "html":
                            self.assertEqual(displayed["Reference"], reference)
                        else:
                            # The generic Markdown text extractor treats paired
                            # '< ... >=' bounds as tags; inspect this cell literally.
                            line = next(line for line in rendered.splitlines()
                                        if line.startswith(f"| **{marker}** |"))
                            self.assertEqual(line.rstrip(" |").split("|")[-1].strip(), reference)

    def test_ana_iift_is_a_separate_qualitative_result_without_changing_immunoblot(self):
        category, marker, value = "Immunology & Inflammation", "ANA IIFT", "negative at 1:80"
        observations = self.observations(category, marker)
        self.assertEqual(observations["2026-09"], value)
        self.assertTrue(all(result == "-" for month, result in observations.items()
                            if month != "2026-09"))
        self.assertEqual(self.row(category, marker)[-2:], ("Status", "negative"))
        self.assertEqual(self.report["qualitative_status"](value)[1], "🔵")
        self.assertIsNone(self.report["calculate_score"](value, "negative", category, marker))
        self.assertIsNone(self.report["classify_trend"](
            [value, "-", "-", "-", "-"], "negative", category, marker))
        group = next(group for group in self.report["lab_groups"](category, self.report["data"][category])
                     if group["title"] == "Immune Markers & Antibodies")
        self.assertIn(marker, [row[0] for row in group["rows"]])
        for output_format, output in self.outputs.items():
            with self.subTest(output_format=output_format):
                rendered = self.report[f"render_result_table_{output_format}"](category, group["rows"])
                self.assertIn(rendered, output)
                table = rendered_table_rows(rendered, output_format)
                result_index = table[0].index("2026-09")
                row = next(row for row in table[1:] if row[0] == marker)
                self.assertEqual(row[result_index], "🔵 " + value)
                self.assertEqual(row[table[0].index("Trend")], "-")
                notes = self.report[f"render_result_notes_{output_format}"](category)
                self.assertNotIn("ANA IIFT", notes)
                self.assertNotIn("ANA IIFT is negative at 1:80.", output)
                self.assertNotIn("ANA IIFT/titre is pending", output)
                self.assertIn("Centromere B is equivocal (+)", output)
        self.assertEqual(self.observations("Immunology & Inflammation", "Centromere B")["2026-09"],
                         "equivocal (+)")

    def test_immunoblot_preserves_all_components_and_equivocal_centromere(self):
        category = "Immunology & Inflammation"
        expected_names = [
            "DFS70", "AMA-M2", "Ribosomal Protein P", "Histones", "Nucleosomes",
            "dsDNA", "PCNA", "Centromere B", "Jo-1", "PM-Scl100", "Scl-70",
            "SS-B", "Ro-52 Recombinant", "SS-A Native (60kDa)", "Sm", "Sm, RNP/Sm",
        ]
        group = next(group for group in self.report["lab_groups"](category, self.report["data"][category])
                     if group["title"] == "ANA/ENA Immunoblot")
        self.assertEqual([row[0] for row in group["rows"]], expected_names)
        for marker in expected_names:
            with self.subTest(marker=marker):
                observations = self.observations(category, marker)
                expected = "equivocal (+)" if marker == "Centromere B" else "negative"
                self.assertEqual(observations["2026-09"], expected)
                self.assertTrue(all(value == "-" for month, value in observations.items()
                                    if month != "2026-09"))
                self.assertEqual(self.row(category, marker)[-2:], ("Status", "negative"))
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = self.report[f"render_result_table_{output_format}"](category, group["rows"])
                table = rendered_table_rows(rendered, output_format)
                self.assertIn(rendered, self.outputs[output_format])
                self.assertEqual([cell for cell in table[0] if re.fullmatch(r"\d{4}-\d{2}", cell)],
                                 ["2026-09"])
                self.assertNotIn("Trend", table[0])
                result_index = table[0].index("2026-09")
                self.assertEqual(Counter((cells[result_index][0], literal_result(cells[result_index]))
                                         for cells in table[1:]),
                                 {("🔵", "negative"): 15, ("🟡", "equivocal (+)"): 1})

    def test_equivocal_immunoblot_is_unscored_and_blocks_stale_trends(self):
        category, marker, reference = "Immunology & Inflammation", "Centromere B", "negative"
        value = "equivocal (+)"
        self.assertTrue(self.report["is_inconclusive"](value))
        self.assertEqual(self.report["qualitative_status"](value)[1], "🟡")
        self.assertIsNone(self.report["calculate_score"](value, reference, category, marker))
        self.assertIsNone(self.report["trend_score"](value, reference, category, marker))
        for values in ([value, "negative", "positive"], ["negative", value, "positive"],
                       ["-", value, "negative", "positive"]):
            with self.subTest(values=values):
                self.assertIsNone(self.report["classify_trend"](values, reference, category, marker))
                for output_format in ("html", "md"):
                    self.assertEqual(self.report[f"format_trend_{output_format}"](
                        values, reference, category, marker), "-")

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

    def test_completed_stool_siga_preserves_history_units_and_low_status(self):
        category, marker = "Stool Analysis", "Secretory sIgA (Stool)"
        values = self.observations(category, marker)
        self.assertEqual(values["2026-09"], "339.8")
        self.assertEqual(values["2026-07"], "5023.4")
        self.assertEqual(self.row(category, marker)[-2:], ("ug/ml", "510.0 - 2040.0"))
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = self.report[f"render_result_table_{output_format}"](
                    category, [self.row(category, marker)])
                header, cells = rendered_table_rows(rendered, output_format)
                displayed = dict(zip(header, cells))
                self.assertEqual(displayed["2026-09"], "🟡 339.8 ↓")
                self.assertEqual(literal_result(displayed["2026-07"]), "5023.4")
                self.assertNotIn("its repeat is pending", self.outputs[output_format])

    def test_completed_selenium_preserves_history_and_appears_in_its_followup_table(self):
        category, marker = "Micronutrients", "Selenium"
        values = self.observations(category, marker)
        self.assertEqual(values["2026-09"], "90.60")
        self.assertEqual(values["2026-07"], "108.75")
        self.assertEqual(self.row(category, marker)[-2:], ("ug/l", "50 - 120"))
        group = next(group for group in self.report["lab_groups"](
            category, self.report["data"][category]) if group["title"] == marker)
        self.assertEqual([row[0] for row in group["rows"]], [marker])
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = self.report[f"render_result_table_{output_format}"](category, group["rows"])
                self.assertIn(rendered, self.outputs[output_format])
                header, cells = rendered_table_rows(rendered, output_format)
                displayed = dict(zip(header, cells))
                self.assertEqual(displayed["2026-09"], "🔵 90.60")
                self.assertEqual(displayed["2026-07"], "🔵 108.75")
                self.assertEqual(displayed["Unit"], "ug/l")
                self.assertEqual(displayed["Reference"], "50 - 120; target 90 - 120")
                self.assertEqual(displayed["Trend"], "⚪")

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

    def test_proteinogram_has_no_preferred_normal_midpoint(self):
        score = self.report["calculate_score"]
        classify = self.report["classify_trend"]
        for row in self.report["data"]["Proteinogram"]:
            marker, _, _, reference = self.report["split_result_row"](row)
            low, high = map(float, reference.split(" - "))
            readings = [str(low), str((low + high) / 2), str(high)]
            with self.subTest(marker=marker):
                scores = [score(value, reference, "Proteinogram", marker) for value in readings]
                self.assertEqual(len(set(scores)), 1)
                self.assertEqual(self.report["get_color_hex"](scores[0])[1], "🟢")
                for pair in (readings[:2], readings[1:], readings[::2], readings[::-2]):
                    self.assertEqual(classify(pair, reference, "Proteinogram", marker), "Stable")
                just_low = str(low - (high - low) * 0.01)
                far_low = str(low - (high - low))
                just_high = str(high + (high - low) * 0.01)
                far_high = str(high + (high - low))
                for near, far in ((just_low, far_low), (just_high, far_high)):
                    self.assertGreater(score(near, reference, "Proteinogram", marker), 1)
                    self.assertGreater(score(far, reference, "Proteinogram", marker),
                                       score(near, reference, "Proteinogram", marker))
                    self.assertIn(classify([readings[1], near], reference, "Proteinogram", marker),
                                  {"Improvement", "Major Improvement", "Breakthrough"})
                    self.assertIn(classify([near, readings[1]], reference, "Proteinogram", marker),
                                  {"Mild Worsening", "Major Decline", "Critical Decline"})
        # The category-specific policy must not flatten other laboratory ranges.
        self.assertNotEqual(score("4.7", "4.7 - 7.2"), score("5.95", "4.7 - 7.2"))

    def test_current_proteinogram_preserves_normalization_without_midpoint_trends(self):
        for row in self.report["data"]["Proteinogram"]:
            marker, values, _, reference = self.report["split_result_row"](row)
            if sum(value not in {"-", "", None} for value in values) < 2:
                continue
            with self.subTest(marker=marker):
                expected = "Improvement" if marker == "Alpha-2 Globulin" else "Stable"
                self.assertEqual(self.report["classify_trend"](values, reference, "Proteinogram", marker), expected)

    def test_explicit_directional_lab_targets_work_in_both_directions_inside_target(self):
        classify = self.report["classify_trend"]
        cases = [
            ("Cardiac Health & Coagulation", "ApoB", "0.50", "0.60"),
            ("Cardiac Health & Coagulation", "Cholesterol LDL", "55", "65"),
            ("Cardiac Health & Coagulation", "Cholesterol Non-HDL", "80", "95"),
            ("Cardiac Health & Coagulation", "Triglycerides", "50", "70"),
            ("Cardiac Health & Coagulation", "Homocysteine", "6", "7.5"),
            ("Cardiac Health & Coagulation", "ApoA1", "1.5", "1.3"),
            ("Cardiac Health & Coagulation", "Cholesterol HDL", "70", "60"),
            ("Metabolic Health", "ALT", "12", "18"),
            ("Metabolic Health", "GGTP", "14", "18"),
            ("Metabolic Health", "Insulin", "4", "6"),
            ("Immunology & Inflammation", "CRP (hs)", "0.4", "0.7"),
            ("Immunology & Inflammation", "CRP (hs)", "0.0", "0.4"),
        ]
        for category, marker, better, worse in cases:
            reference = self.row(category, marker)[-1]
            with self.subTest(marker=marker):
                self.assertEqual(classify([better, worse], reference, category, marker), "Improvement")
                self.assertEqual(classify([worse, better], reference, category, marker), "Mild Worsening")
                self.assertAlmostEqual(
                    self.report["directional_percent_delta"](better, worse, reference, category, marker),
                    -self.report["directional_percent_delta"](worse, better, reference, category, marker),
                )

    def test_lab_directional_display_filters_suppress_small_changes_symmetrically(self):
        classify = self.report["classify_trend"]
        cases = [
            ("Cardiac Health & Coagulation", "ApoB", "0.59", "0.60"),
            # Passes the relative threshold but not the absolute display floor.
            ("Cardiac Health & Coagulation", "ApoB", "0.10", "0.11"),
            ("Immunology & Inflammation", "CRP (hs)", "0.448", "0.611"),
            ("Metabolic Health", "ALT", "10", "11"),
            ("Cardiac Health & Coagulation", "ApoA1", "1.30", "1.35"),
        ]
        for category, marker, first, second in cases:
            reference = self.row(category, marker)[-1]
            with self.subTest(marker=marker):
                for pair in ([first, second], [second, first]):
                    self.assertEqual(classify(pair, reference, category, marker), "Stable")

    def test_lab_direction_cannot_reward_low_or_high_target_overshoots(self):
        classify = self.report["classify_trend"]
        for category, marker, overshoot, acceptable in (
            ("Metabolic Health", "Insulin", "1.0", "4.0"),
            ("Metabolic Health", "Albumin", "55", "48"),
            ("Cardiac Health & Coagulation", "Cholesterol HDL", "90", "70"),
        ):
            reference = self.row(category, marker)[-1]
            with self.subTest(marker=marker):
                for pair in ([overshoot, acceptable], [acceptable, overshoot]):
                    self.assertIsNone(self.report["directional_percent_delta"](*pair, reference, category, marker))
                self.assertIn(classify([overshoot, acceptable], reference, category, marker),
                              {"Mild Worsening", "Major Decline", "Critical Decline"})
                self.assertIn(classify([acceptable, overshoot], reference, category, marker),
                              {"Improvement", "Major Improvement", "Breakthrough"})

    def test_lab_symmetry_does_not_change_excluded_or_reference_only_fallbacks(self):
        classify = self.report["classify_trend"]
        for category, marker, lower, higher in (
            ("Tumor Markers", "AFP (ng/ml)", "1.99", "2.84"),
            ("Infectious Diseases", "Chlamydia IgM", "2.0", "2.7"),
        ):
            reference = self.row(category, marker)[-1]
            self.assertEqual(classify([lower, higher], reference, category, marker), "Improvement")
            self.assertEqual(classify([higher, lower], reference, category, marker), "Stable")
        self.assertEqual(classify(["0.5", "1.0"], "< 10", "Unspecified", "Marker"), "Improvement")
        self.assertEqual(classify(["1.0", "0.5"], "< 10", "Unspecified", "Marker"), "Stable")

    def test_all_followups_appear_in_september_in_both_generated_reports(self):
        values = [value for observations in self.report["lab_followups"]["2026-09"].values()
                  for value in observations.values()]
        self.assertEqual(sum(value != "pending" for value in values), 121)
        self.assertEqual(values.count("pending"), 1)
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
                      "Immunology & Inflammation")
        for category in categories:
            groups = self.report["lab_groups"](category, self.report["data"][category])
            self.assertEqual(len(groups), 3 if category == "Immunology & Inflammation" else 2)
            for output_format in ("html", "md"):
                for index, group in enumerate(groups):
                    with self.subTest(category=category, group=group["title"], output_format=output_format):
                        rendered = self.report[f"render_result_table_{output_format}"](category, group["rows"])
                        header = rendered_table_rows(rendered, output_format)[0]
                        self.assertEqual("2026-09" in header, index > 0)
                        self.assertIn("Unit", header)
                        self.assertIn("Reference", header)

    def test_hormonal_tables_preserve_all_markers_and_only_thyroid_has_september(self):
        category = "Hormonal Panel"
        rows = self.report["data"][category]
        groups = self.report["lab_groups"](category, rows)
        expected = {
            "Reproductive Hormones & Markers": [
                "Testosterone (Total)", "Testosterone (Free)", "DHT", "Estradiol (E2)",
                "Prolactin", "LH", "FSH", "SHBG", "Progesterone",
            ],
            "Adrenal Hormones & Precursors": [
                "Cortisol", "DHEA-SO4", "17-OH Progesterone", "17-Hydroxypregnenolone",
            ],
            "Growth Axis": ["IGF-1"],
            "Thyroid Function": ["TSH", "Free T3 (FT3)", "Free T4 (FT4)"],
        }
        self.assertEqual([(group["title"], [row[0] for row in group["rows"]])
                          for group in groups], list(expected.items()))
        self.assertEqual(Counter(id(row) for group in groups for row in group["rows"]),
                         Counter(map(id, rows)))
        for output_format in ("html", "md"):
            for group in groups:
                with self.subTest(group=group["title"], output_format=output_format):
                    rendered = self.report[f"render_result_table_{output_format}"](category, group["rows"])
                    table = rendered_table_rows(rendered, output_format)
                    self.assertIn(rendered, self.outputs[output_format])
                    self.assertEqual("2026-09" in table[0], group["title"] == "Thyroid Function")
                    self.assertEqual([cells[0] for cells in table[1:]], expected[group["title"]])
                    self.assertIn("Unit", table[0])
                    self.assertIn("Reference", table[0])

    def test_hcg_moves_to_tumor_markers_without_changing_results_or_scoring(self):
        category, marker = "Tumor Markers", "HCG-Beta"
        self.assertEqual([panel for panel, rows in self.report["data"].items()
                          for row in rows if row[0] == marker], [category])
        observations = self.observations(category, marker)
        self.assertEqual({month: value for month, value in observations.items() if value != "-"},
                         {"2026-07": "< 0.200", "2026-01": "< 0.200"})
        self.assertEqual(self.row(category, marker)[-2:], ("mIU/mL", "< 2.60"))
        overrides = self.report["target_overrides"]
        self.assertNotIn(("Hormonal Panel", marker), overrides)
        self.assertEqual(overrides[(category, marker)], {
            "reference": "< 2.60; target < 1", "type": "low_good",
            "optimal_max": 1.0, "high_limit": 2.6,
        })
        self.assertEqual(self.report["calculate_score"]("< 0.200", "< 2.60", category, marker), 0.35)
        for output_format in ("html", "md"):
            rendered = self.report[f"render_result_table_{output_format}"](category, self.report["data"][category])
            table = rendered_table_rows(rendered, output_format)
            cells = next(cells for cells in table[1:] if cells[0] == marker)
            values = dict(zip(table[0], cells))
            self.assertEqual(values["2026-07"], "🔵 < 0.200")
            self.assertEqual(values["2026-01"], "🔵 < 0.200")
            self.assertIn(rendered, self.outputs[output_format])

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

    def test_free_psa_and_ratio_show_context_without_an_invented_normal_range(self):
        category = "Tumor Markers"
        expected = {
            "PSA Free": ("⚪ 0.033", "Interpret with total PSA"),
            "PSA Free/Total Ratio": ("⚪ 22.05", ">25; interpret with total PSA"),
        }
        # Preserve the original laboratory fields, including the blank free-PSA interval.
        self.assertEqual(self.row(category, "PSA Free")[-2:], ("ng/mL", "-"))
        self.assertEqual(self.row(category, "PSA Free/Total Ratio")[-2:], ("%", "> 25"))
        for output_format in ("html", "md"):
            rendered = self.report[f"render_result_table_{output_format}"](category, self.report["data"][category])
            table = rendered_table_rows(rendered, output_format)
            rows = {cells[0]: dict(zip(table[0], cells)) for cells in table[1:]}
            for marker, (value, reference) in expected.items():
                with self.subTest(marker=marker, output_format=output_format):
                    self.assertEqual(rows[marker]["2026-07"], value)
                    self.assertEqual(rows[marker]["Reference"], reference)
                    self.assertEqual(rows[marker]["2026-01"], "-")
                    self.assertIsNone(self.report["calculate_score"]("22.05", reference, category, marker))
                    self.assertIsNone(self.report["classify_trend"](["22.05", "30"], reference, category, marker))
                    format_cell = self.report[f"format_cell_{output_format}"]
                    self.assertEqual(format_cell("pending", reference, category, marker), "pending")
            self.assertEqual(rows["PSA Total"]["2026-07"], "🔵 0.15")
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
