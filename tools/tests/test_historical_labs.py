"""Historical source reconciliation, byte integrity and report rendering."""

from collections import Counter
from copy import deepcopy
from html import escape
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch

from tools import historical_labs
from tools.tests.test_report_layout import rendered_table_rows


class HistoricalLabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            monthly = Path(folder) / "monthly.json"
            monthly.write_text(json.dumps({
                "schema_version": 1, "as_of": "2026-11-21", "months": {},
            }), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(monthly)}):
                cls.report = runpy.run_path(
                    str(Path(__file__).parents[1] / "generate_colored_report.py"),
                    run_name="historical_lab_test",
                )

    def records(self):
        return [(panel["date"], record) for panel in historical_labs.HISTORICAL_LABS
                for record in panel["records"]]

    def render(self, output_format):
        return getattr(historical_labs, f"render_historical_{output_format}")(
            self.report[f"format_cell_{output_format}"]
        )

    def test_primary_report_values_and_dates_reconcile_to_13_unique_observations(self):
        # Expected transcription from the seven original PDF reports, after
        # matching their CSV/CDA and certificate duplicates to each specimen.
        expected = {
            ("2015-01-14", "Sodium"): ("141", "mmol/l"),
            ("2015-01-14", "Potassium"): ("4.2", "mmol/l"),
            ("2015-01-14", "Calcium, total"): ("9.9", "mg/dl"),
            ("2015-01-14", "Insulin"): ("16.4", "µIU/ml"),
            ("2015-01-14", "Ferritin"): ("118.3", "ng/ml"),
            ("2015-01-14", "Homocysteine"): ("10.74", "µmol/l"),
            ("2015-01-14", "Vitamin D, 25-OH"): ("18.40", "ng/ml"),
            ("2022-03-17", "SARS-CoV-2 RT-PCR"): ("Negative", "-"),
            ("2023-10-02", "Total cholesterol"): ("125", "mg/dl"),
            ("2023-10-02", "HDL cholesterol"): ("41", "mg/dl"),
            ("2023-10-02", "Non-HDL cholesterol"): ("84", "mg/dl"),
            ("2023-10-02", "LDL cholesterol"): ("73", "mg/dl"),
            ("2023-10-02", "Triglycerides"): ("54", "mg/dl"),
        }
        records = self.records()
        self.assertEqual(len(records), len(expected))
        self.assertEqual({(date, row["test"]): (row["value"], row["unit"])
                          for date, row in records}, expected)
        self.assertEqual(Counter(date for date, _ in records), {
            "2023-10-02": 5, "2022-03-17": 1, "2015-01-14": 7,
        })
        self.assertEqual([panel["date"] for panel in historical_labs.HISTORICAL_LABS],
                         ["2023-10-02", "2022-03-17", "2015-01-14"])

    def test_duplicate_ldl_precision_and_calculated_status_are_preserved(self):
        calculated = [row for _, row in self.records() if row.get("calculated")]
        self.assertEqual({row["test"] for row in calculated},
                         {"LDL cholesterol", "Non-HDL cholesterol"})
        ldl = next(row for row in calculated if row["test"] == "LDL cholesterol")
        self.assertEqual((ldl["value"], ldl["alternate_csv_value"]), ("73", "73.20"))
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = self.render(output_format)
                self.assertIn("73mg/dl in the PDF/CDA and 73.20mg/dl in the CSV", rendered)
                self.assertIn("one result", rendered)
                self.assertEqual(rendered.count("SARS-CoV-2 RT-PCR"), 1)
                self.assertIn("Non-HDL cholesterol", rendered)
                self.assertIn("LDL cholesterol", rendered)
                self.assertEqual(rendered.count("calculated)" if output_format == "html"
                                                else "calculated\\)"), 2)

    def test_only_unambiguous_source_references_reach_the_shared_formatter(self):
        expected_unscored = {"Non-HDL cholesterol", "LDL cholesterol",
                             "Triglycerides", "Vitamin D, 25-OH"}
        for output_format in ("html", "md"):
            callback = Mock(return_value="formatted-result")
            getattr(historical_labs, f"render_historical_{output_format}")(callback)
            self.assertEqual(callback.call_count, 13)
            for (_, row), call in zip(self.records(), callback.call_args_list):
                with self.subTest(output_format=output_format, marker=row["test"]):
                    self.assertEqual(len(call.args), 2)
                    self.assertEqual(call.kwargs, {})
                    self.assertEqual(call.args[0], row["value"])
                    self.assertEqual(call.args[1] == "-", row["test"] in expected_unscored)
                    if row["test"] == "SARS-CoV-2 RT-PCR":
                        self.assertEqual(call.args[1], "negative")

    def test_both_formats_render_every_observation_once_with_source_references(self):
        html = self.render("html")
        md = self.render("md")
        table_rows = rendered_table_rows(html, "html")
        values = [cells for cells in table_rows if cells[0] != "Metric"]
        self.assertEqual(len(values), 13)
        self.assertEqual(sum(line.startswith("| **") for line in md.splitlines()), 13)
        for date, record in self.records():
            marker = record["test"] + (" (calculated)" if record.get("calculated") else "")
            cells = next(cells for cells in values if cells[0] == marker)
            self.assertIn(record["value"], cells[1])
            self.assertEqual(cells[2], record["unit"])
            if record["test"] in {"Non-HDL cholesterol", "LDL cholesterol",
                                  "Triglycerides", "Vitamin D, 25-OH"}:
                self.assertEqual(cells[1], record["value"])
            for rendered in (html, md):
                self.assertIn(date, rendered)
        pcr = next(cells for cells in values if cells[0] == "SARS-CoV-2 RT-PCR")
        self.assertEqual(pcr[1:], ["🔵 Negative", "-", "-"])
        self.assertNotIn("<th>Trend</th>", html)
        self.assertNotIn("| Trend |", md)
        self.assertIn("&lt;150", html)
        self.assertIn("&lt;150", md)
        self.assertIn("&gt;100 toxic", html)
        self.assertIn("&gt;100 toxic", md)

    def test_rendering_preserves_current_comparison_data_and_date_columns(self):
        before = deepcopy((self.report["date_columns"], self.report["data"],
                           historical_labs.HISTORICAL_LABS))
        self.render("html")
        self.render("md")
        self.assertEqual((self.report["date_columns"], self.report["data"],
                          historical_labs.HISTORICAL_LABS), before)
        self.assertTrue(set(before[0]).isdisjoint({"2015-01-14", "2022-03-17", "2023-10-02"}))

    def test_source_link_and_heading_anchor_resolve(self):
        root = Path(__file__).parents[2]
        source = root / historical_labs.HISTORICAL_LABS_SOURCE
        self.assertTrue(source.is_file())
        provenance = source.read_text(encoding="utf-8")
        self.assertEqual(len(set(re.findall(r"`([0-9a-f]{64})`", provenance))), 11)
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
        for panel in historical_labs.HISTORICAL_LABS:
            self.assertIn(panel["date"], provenance)
        for output_format in ("html", "md"):
            self.assertEqual(self.render(output_format).count(historical_labs.HISTORICAL_LABS_SOURCE), 1)
        self.assertIn(f"id='{historical_labs.HISTORICAL_LABS_ANCHOR}'", self.render("html"))
        self.assertIn(f"## {historical_labs.HISTORICAL_LABS_TITLE}\n", self.render("md"))

    def test_complete_reports_include_archive_once_and_link_to_its_anchor(self):
        with tempfile.TemporaryDirectory() as folder:
            for output_format in ("html", "md"):
                with self.subTest(output_format=output_format):
                    path = Path(folder) / f"results.{output_format}"
                    self.report[f"generate_{output_format}_report"](path)
                    complete = path.read_text(encoding="utf-8")
                    self.assertEqual(complete.count(self.render(output_format)), 1)
                    markdown = output_format == "md"
                    anchor = (self.report["markdown_heading_anchor"](historical_labs.HISTORICAL_LABS_TITLE)
                              if markdown else historical_labs.HISTORICAL_LABS_ANCHOR)
                    contents = self.report["report_contents"](markdown=markdown)
                    history_links = [links for title, links in contents if title == "History"]
                    self.assertEqual(history_links, [[(historical_labs.HISTORICAL_LABS_TITLE, f"#{anchor}")]])
                    expected_link = (f"](#{anchor})" if markdown else f"href='#{anchor}'")
                    self.assertIn(expected_link, complete)

    def test_metadata_and_reference_annotations_are_escaped(self):
        panel = {
            "date": "2000-01-01", "specimen": "Serum <tag> & more",
            "note": "A <script> tag, [label](url) and table | separator.",
            "records": ({"test": "Marker | [name] <tag>", "value": "4",
                         "unit": "x|y", "reference": "<5 | [note]"},),
        }
        with patch.object(historical_labs, "HISTORICAL_LABS", (panel,)):
            html = historical_labs.render_historical_html(lambda value, _: escape(value))
            md = historical_labs.render_historical_md(lambda value, _: value)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<tag>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;5 | [note]", html)
        self.assertIn("Marker \\| \\[name\\] &lt;tag&gt;", md)
        self.assertIn("x\\|y", md)
        self.assertIn("&lt;5 \\| \\[note\\]", md)
        self.assertIn("\\[label\\]\\(url\\)", md)


if __name__ == "__main__":
    unittest.main()
