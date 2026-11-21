"""Historical source reconciliation, original-byte integrity and normal tables."""

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import patch

from tools import historical_labs
from tools.tests.test_report_layout import rendered_table_rows


class HistoricalLabTests(unittest.TestCase):
    @classmethod
    def load_report(cls):
        with tempfile.TemporaryDirectory() as folder:
            monthly = Path(folder) / "monthly.json"
            monthly.write_text(json.dumps({
                "schema_version": 1, "as_of": "2026-11-21", "months": {},
            }), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(monthly)}):
                return runpy.run_path(
                    str(Path(__file__).parents[1] / "generate_colored_report.py"),
                    run_name="historical_lab_test",
                )

    @classmethod
    def setUpClass(cls):
        cls.report = cls.load_report()

    def row(self, category, marker, report=None):
        return next(row for row in (report or self.report)["data"][category] if row[0] == marker)

    def observations(self, category, marker, report=None):
        report = report or self.report
        _, values, _, _ = report["split_result_row"](self.row(category, marker, report))
        return dict(zip(report["date_columns"], values))

    def test_primary_values_map_to_13_unique_observations_in_existing_categories(self):
        # Source reconciliation uses the original collection dates, never the
        # filenames' November 2026 export date or a CDA document timestamp.
        expected = {
            ("2015-01-14", "Micronutrients", "Sodium"): ("141", "mmol/l"),
            ("2015-01-14", "Micronutrients", "Potassium"): ("4.2", "mmol/l"),
            ("2015-01-14", "Micronutrients", "Calcium (Total)"): ("9.9", "mg/dL"),
            ("2015-01-14", "Metabolic Health", "Insulin"): ("16.4", "uU/mL"),
            ("2015-01-14", "Micronutrients", "Ferritin"): ("118.3", "ng/ml"),
            ("2015-01-14", "Cardiac Health & Coagulation", "Homocysteine"): ("10.74", "umol/l"),
            ("2015-01-14", "Micronutrients", "Vitamin D3"): ("18.40", "ng/ml"),
            ("2022-03-17", "Infectious Diseases", "SARS-CoV-2 RT-PCR"): ("Negative", "Status"),
            ("2023-10-02", "Cardiac Health & Coagulation", "Cholesterol Total"): ("125", "mg/dL"),
            ("2023-10-02", "Cardiac Health & Coagulation", "Cholesterol HDL"): ("41", "mg/dL"),
            ("2023-10-02", "Cardiac Health & Coagulation", "Cholesterol Non-HDL"): ("84", "mg/dL"),
            ("2023-10-02", "Cardiac Health & Coagulation", "Cholesterol LDL"): ("73", "mg/dl"),
            ("2023-10-02", "Cardiac Health & Coagulation", "Triglycerides"): ("54", "mg/dL"),
        }
        records = historical_labs.HISTORICAL_LABS
        self.assertEqual(len(records), len(expected))
        self.assertEqual({(row["date"], row["category"], row["marker"]): (row["value"], row["unit"])
                          for row in records}, expected)
        for (date, category, marker), (value, unit) in expected.items():
            self.assertEqual(self.observations(category, marker)[date], value)
            self.assertEqual(self.row(category, marker)[-2], unit)
        self.assertEqual(Counter(row["date"] for row in records), {
            "2023-10-02": 5, "2022-03-17": 1, "2015-01-14": 7,
        })

    def test_exact_dates_are_chronological_without_reinterpreting_legacy_tuples(self):
        dates = self.report["date_columns"]
        self.assertEqual(dates, sorted(set(dates), reverse=True))
        self.assertEqual(dates[-3:], ["2023-10-02", "2022-03-17", "2015-01-14"])
        self.assertEqual(self.report["historical_date_columns"],
                         ["2026-07", "2026-01", "2025-05", "2025-01"])
        self.assertEqual(self.observations("Metabolic Health", "Insulin")["2026-07"], "8.6")
        self.assertEqual(self.observations("Micronutrients", "Ferritin")["2025-05"], "134")
        self.assertEqual(self.observations("Cardiac Health & Coagulation", "Cholesterol LDL")["2026-01"], "76")

    def test_all_old_results_render_once_in_normal_tables_in_both_complete_reports(self):
        with tempfile.TemporaryDirectory() as folder:
            for output_format in ("html", "md"):
                path = Path(folder) / f"results.{output_format}"
                self.report[f"generate_{output_format}_report"](path)
                complete = path.read_text(encoding="utf-8")
                self.assertNotIn("Historical Laboratory Results", complete)
                self.assertNotIn("results-historical-laboratory-results", complete)
                self.assertNotIn("History", [title for title, _ in self.report["report_contents"]()])
                for result in historical_labs.HISTORICAL_LABS:
                    category, marker, date = result["category"], result["marker"], result["date"]
                    with self.subTest(format=output_format, date=date, marker=marker):
                        rows = self.report["data"][category]
                        self.assertEqual(sum(row[0] == marker for row in rows), 1)
                        section = self.report[f"render_lab_{output_format}"](category, rows)
                        self.assertEqual(complete.count(section), 1)
                        group = next(group for group in self.report["lab_groups"](category, rows)
                                     if any(row[0] == marker for row in group["rows"]))
                        rendered = self.report[f"render_result_table_{output_format}"](category, group["rows"])
                        header, *table = rendered_table_rows(rendered, output_format)
                        cells = next(row for row in table if row[0] == marker)
                        self.assertIn(result["value"], cells[header.index(date)])
                        self.assertEqual(cells[header.index("Unit")], result["unit"])

    def test_existing_observations_units_references_and_trends_are_unchanged(self):
        with patch.object(historical_labs, "HISTORICAL_LABS", ()):
            baseline = self.load_report()
        for category, rows in baseline["data"].items():
            for old_row in rows:
                marker, old_values, unit, ref = baseline["split_result_row"](old_row)
                if marker == "SARS-CoV-2 RT-PCR":
                    continue  # This is the sole new marker, with one old specimen.
                with self.subTest(category=category, marker=marker):
                    new_row = self.row(category, marker)
                    self.assertEqual(new_row[-2:], (unit, ref))
                    actual = self.observations(category, marker)
                    for date, value in zip(baseline["date_columns"], old_values):
                        self.assertEqual(actual[date], value)
                    old_ref = baseline["target_reference"](category, marker, ref)
                    new_ref = self.report["target_reference"](category, marker, ref)
                    self.assertEqual(new_ref, old_ref)
                    old_trend = baseline["format_trend_md"](old_values, old_ref, category, marker)
                    new_trend = self.report["format_trend_md"](list(actual.values()), new_ref, category, marker)
                    self.assertEqual(new_trend, old_trend)

    def test_missing_historical_assays_are_not_carried_forward_or_backfilled(self):
        expected = {(row["date"], row["category"], row["marker"]): row["value"]
                    for row in historical_labs.HISTORICAL_LABS}
        dates = {key[0] for key in expected}
        actual = {}
        for category, rows in self.report["data"].items():
            for row in rows:
                observations = self.observations(category, row[0])
                for date in dates:
                    if observations[date] != "-":
                        actual[(date, category, row[0])] = observations[date]
        self.assertEqual(actual, expected)

    def test_original_ranges_units_calculated_status_and_ldl_precision_remain_traceable(self):
        records = {row["marker"]: row for row in historical_labs.HISTORICAL_LABS}
        self.assertEqual(records["Calcium (Total)"]["source_reference"], "8.4 - 10.2")
        self.assertEqual(records["Homocysteine"]["source_reference"], "0.00 - 12.00")
        self.assertEqual(records["Insulin"]["source_unit"], "µIU/ml")
        self.assertEqual(records["Homocysteine"]["source_unit"], "µmol/l")
        self.assertEqual({row["marker"] for row in records.values() if row.get("calculated")},
                         {"Cholesterol LDL", "Cholesterol Non-HDL"})
        self.assertEqual((records["Cholesterol LDL"]["value"], records["Cholesterol LDL"]["alternate_csv_value"]),
                         ("73", "73.20"))
        self.assertEqual(records["Vitamin D3"]["value"], "18.40")
        for category in {row["category"] for row in records.values()}:
            notes = self.report["result_notes"][category]
            for date in {row["date"] for row in records.values() if row["category"] == category}:
                self.assertTrue(any(date in note["text"] and historical_labs.HISTORICAL_LABS_SOURCE in note["text"]
                                    for note in notes))
        lipid_notes = self.report["result_notes"]["Cardiac Health & Coagulation"]
        self.assertTrue(any("LDL and non-HDL are calculated" in note["text"] for note in lipid_notes))

    def test_pcr_is_one_completed_qualitative_result_without_a_trend(self):
        category, marker = "Infectious Diseases", "SARS-CoV-2 RT-PCR"
        observations = self.observations(category, marker)
        self.assertEqual({date: value for date, value in observations.items() if value != "-"},
                         {"2022-03-17": "Negative"})
        self.assertEqual(self.row(category, marker)[-2:], ("Status", "negative"))
        self.assertIsNone(self.report["classify_trend"](list(observations.values()), "negative", category, marker))
        for output_format in ("html", "md"):
            rendered = self.report[f"render_result_table_{output_format}"](category, [self.row(category, marker)])
            header, row = rendered_table_rows(rendered, output_format)
            self.assertEqual(row[header.index("2022-03-17")], "🔵 Negative")
            self.assertNotIn("Trend", header)

    def test_provenance_links_all_11_unchanged_raw_originals(self):
        root = Path(__file__).parents[2]
        source = root / historical_labs.HISTORICAL_LABS_SOURCE
        self.assertTrue(source.is_file())
        provenance = source.read_text(encoding="utf-8")
        inventory = provenance.split("## Source inventory", 1)[1].split("## Verification", 1)[0]
        originals = re.findall(
            r"\| \[([^\]]+)\]\(\.\./([^\)]+)\) \| [^|]+\| [^|]+\| `([0-9a-f]{64})` \|",
            inventory,
        )
        self.assertEqual(len(originals), 11)
        self.assertEqual(len({filename for _, filename, _ in originals}), 11)
        for label, filename, expected_hash in originals:
            with self.subTest(filename=filename):
                self.assertEqual(label, filename)
                original = (source.parent / ".." / filename).resolve()
                self.assertEqual(original.parent, (root / "results").resolve())
                self.assertTrue(original.is_file())
                self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), expected_hash)
        for date in {row["date"] for row in historical_labs.HISTORICAL_LABS}:
            self.assertIn(date, provenance)
        self.assertIn("73.20", provenance)
        self.assertNotIn("archive", provenance)


if __name__ == "__main__":
    unittest.main()
