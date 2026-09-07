"""GA-map transcription and presentation regressions; no PDF or live-data access."""

from collections import Counter
from html import unescape
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import patch

from tools.tests.test_report_layout import TableRows


def markdown_rows(rendered):
    rows = []
    for line in rendered.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        if all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
            continue
        cleaned = []
        for cell in cells:
            cell = re.sub(r"<sup>.*?</sup>", "", cell)
            cell = unescape(re.sub(r"<[^>]*>|\*\*", "", cell))
            cleaned.append(re.sub(r"\\([\\`*_{}\[\]()#!|])", r"\1", cell))
        rows.append(cleaned)
    return rows


class MicrobiotaReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Loading definitions does not run main or regenerate checked-in reports.
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "monthly.json"
            source.write_text(json.dumps({
                "schema_version": 1, "as_of": "2026-09-07", "months": {},
            }), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(source)}):
                cls.report = runpy.run_path(
                    str(Path(__file__).parents[1] / "generate_colored_report.py"),
                    run_name="microbiota_test",
                )
        cls.category = cls.report["MICROBIOTA_CATEGORY"]

    def setUp(self):
        self.rows = list(self.report["data"][self.category])

    def test_results_use_july_sample_date_not_august_report_date(self):
        self.assertEqual(self.category, "Gut Microbiota (GA-map)")
        self.assertEqual(len(self.rows), 62)
        for row in self.rows:
            _, values, _, _ = self.report["split_result_row"](row)
            observations = dict(zip(self.report["date_columns"], values))
            self.assertNotEqual(observations["2026-07"], "-")
            self.assertTrue(all(value == "-" for month, value in observations.items() if month != "2026-07"))
        notes = " ".join(note["text"] for note in self.report["result_notes"][self.category])
        self.assertIn("collected July 7, 2026", notes)
        self.assertIn("received July 9", notes)
        self.assertIn("reported August 4", notes)

    def test_48_unique_markers_exclude_example_page_and_preserve_signed_spot_checks(self):
        markers = self.report["microbiota_markers"]
        by_id = {marker[0]: marker for marker in markers}
        self.assertEqual(len(markers), 48)
        self.assertEqual(len(by_id), 48)
        self.assertEqual({marker[4] for marker in markers}, {2, 3, 4, 5})
        row_lookup = {row[0]: row for row in self.rows}
        july = self.report["date_columns"].index("2026-07") + 1
        for marker_id, expected in {205: 3, 322: 3, 330: -2, 305: -1, 324: 1}.items():
            with self.subTest(marker_id=marker_id):
                marker = by_id[marker_id]
                self.assertEqual(marker[3], expected)
                row = row_lookup[self.report["microbiota_marker_name"](marker)]
                self.assertEqual(row[july], f"{expected:+d}")
                self.assertEqual(row[-2:], ("Chart position", "-"))
        zero = row_lookup[self.report["microbiota_marker_name"](by_id[300])]
        self.assertEqual(zero[july], "0")

    def test_sections_preserve_original_rows_and_unknown_future_markers(self):
        sections = self.report["microbiota_report_sections"](self.rows)
        flattened = [row for section in sections for row in section["rows"]]
        self.assertEqual(Counter(map(id, flattened)), Counter(map(id, self.rows)))
        self.assertEqual([len(section["rows"]) for section in sections if not section["details"]], [2, 12])
        self.assertEqual(sum(len(section["rows"]) for section in sections if section["details"]), 48)
        future = ("999 - Future laboratory marker", *self.rows[-1][1:])
        expanded = self.report["microbiota_report_sections"](self.rows + [future])
        self.assertTrue(next(section["details"] for section in expanded if any(row is future for row in section["rows"])))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.report["microbiota_report_sections"](self.rows + [self.rows[0]])

    def test_html_shows_14_findings_and_hides_48_markers_without_changing_values(self):
        rendered = self.report["render_microbiota_html"](self.rows)
        parsed = TableRows()
        parsed.feed(rendered)
        expected = {row[0]: row[self.report["date_columns"].index("2026-07") + 1] for row in self.rows}
        results = [(row, depth) for row, depth in zip(parsed.rows, parsed.row_depths) if row[0] in expected]
        self.assertEqual(Counter(row[0] for row, _ in results), Counter(expected.keys()))
        self.assertEqual(Counter(depth for _, depth in results), {0: 14, 1: 48})
        self.assertEqual(len(parsed.details), 1)
        self.assertNotIn("open", parsed.details[0])
        for cells, _ in results:
            self.assertEqual(cells[1], expected[cells[0]])
        for header in (row for row in parsed.rows if row[0] == "Metric"):
            self.assertEqual([cell for cell in header if re.fullmatch(r"\d{4}-\d{2}", cell)], ["2026-07"])
            self.assertNotIn("Trend", header)
        self.assertNotIn("color:", rendered)

    def test_markdown_keeps_each_literal_result_once_with_closed_marker_details(self):
        rendered = self.report["render_microbiota_md"](self.rows)
        parsed = markdown_rows(rendered)
        expected = {row[0]: row[self.report["date_columns"].index("2026-07") + 1] for row in self.rows}
        results = [row for row in parsed if row[0] in expected]
        self.assertEqual(Counter(row[0] for row in results), Counter(expected.keys()))
        for cells in results:
            self.assertEqual(cells[1], expected[cells[0]])
        self.assertEqual(rendered.count("<details>"), 1)
        self.assertEqual(rendered.count("</details>"), 1)
        self.assertNotRegex(rendered, r"<details\s+open")
        self.assertIn("48 results", rendered)
        self.assertTrue(all("Trend" not in row for row in parsed if row[0] == "Metric"))

    def test_category_guard_blocks_targets_and_future_qualitative_or_numeric_trends(self):
        namespace = self.report["calculate_score"].__globals__
        target = self.report["low_good_target"]("invented target", 1.0, 2.0)
        marker = "Future laboratory marker"
        with patch.dict(namespace["target_overrides"], {(self.category, marker): target}), \
                patch.dict(namespace, {"no_score_markers": set()}):
            self.assertEqual(self.report["target_reference"](self.category, marker, "lab reference"), "lab reference")
            for latest, previous in [("normal", "positive"), ("+3", "-2")]:
                with self.subTest(latest=latest):
                    self.assertIsNone(self.report["calculate_score"](latest, "< 1", self.category, marker))
                    self.assertIsNone(self.report["trend_score"](latest, "< 1", self.category, marker))
                    self.assertIsNone(self.report["classify_trend"]([latest, previous], "< 1", self.category, marker))
                    values = [latest if month == "2026-09" else previous if month == "2026-07" else "-"
                              for month in self.report["date_columns"]]
                    row = (marker, *values, "Lab classification", "< 1")
                    self.assertFalse(self.report["category_has_trends"]([row], self.category))
                    for output_format in ("html", "md"):
                        rendered = self.report[f"render_microbiota_{output_format}"]([row])
                        table = TableRows() if output_format == "html" else None
                        if table is not None:
                            table.feed(rendered)
                        parsed = table.rows if table is not None else markdown_rows(rendered)
                        self.assertNotIn("Trend", parsed[0])
                        self.assertEqual(parsed[1][1:3], [latest, previous])

    def test_report_values_are_literal_escaped_text_in_both_formats(self):
        dangerous = 'raw <script>alert(1)</script> | [label](url) & text'
        changed = list(self.rows[0])
        changed[self.report["date_columns"].index("2026-07") + 1] = dangerous
        rows = [tuple(changed), *self.rows[1:]]
        html = self.report["render_microbiota_html"](rows)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        parsed = TableRows()
        parsed.feed(html)
        self.assertEqual(next(row[1] for row in parsed.rows if row[0] == changed[0]), dangerous)
        markdown = self.report["render_microbiota_md"](rows)
        self.assertNotIn("<script>", markdown)
        self.assertIn(r"\|", markdown)
        self.assertIn(r"\[label\]\(url\)", markdown)


if __name__ == "__main__":
    unittest.main()
