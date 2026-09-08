"""Lossless report grouping and synthetic renderer checks; no live imports."""

from collections import Counter
from html import unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from tools.health_sync import report_layout


def sample_row(name, unit="index", value="1.0"):
    return (name, value, "-", "-", unit, "-")


class TableRows(HTMLParser):
    """Extract text cell rows and native disclosure state without a browser."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = None
        self.cell = None
        self.details = []
        self.depth = 0
        self.row_depths = []
        self.in_sup = False

    def handle_starttag(self, tag, attrs):
        if tag == "details":
            self.details.append(dict(attrs))
            self.depth += 1
        elif tag == "tr":
            self.current_row = []
        elif tag in {"td", "th"}:
            self.cell = ""
        elif tag == "sup":
            self.in_sup = True

    def handle_endtag(self, tag):
        if tag == "details":
            self.depth -= 1
        elif tag == "sup":
            self.in_sup = False
        elif tag in {"td", "th"} and self.cell is not None:
            self.current_row.append(self.cell.strip())
            self.cell = None
        elif tag == "tr" and self.current_row is not None:
            self.rows.append(self.current_row)
            self.row_depths.append(self.depth)
            self.current_row = None

    def handle_data(self, data):
        if self.cell is not None and not self.in_sup:
            self.cell += data


def rendered_table_rows(rendered, output_format):
    if output_format == "html":
        parsed = TableRows()
        parsed.feed(rendered)
        return parsed.rows
    rows = []
    for line in rendered.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
            continue
        rows.append([
            unescape(re.sub(r"<[^>]*>|\*", "", re.sub(r"<sup>.*?</sup>", "", cell)))
            for cell in cells
        ])
    return rows


class LayoutPartitionTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            sample_row("Body Mass", "kg", "80.4"), sample_row("Bone", "%", "4.2"),
            sample_row("Visceral Fat Index", "index", "2.3"), sample_row("VO2max", "ml/kg/min", "44"),
            sample_row("PWV", "m/s", "6.1"), sample_row("Sleep Duration", "h", "7.51"),
            sample_row("Heart Sounds Classification (Withings)", "Status", "Negative: 1"),
            sample_row("Future Firmware Marker (Oura)", "index", "12.3"),
        ]

    def test_empty_layout_has_no_empty_sections_or_counts(self):
        groups = report_layout.layout([])
        self.assertEqual(groups, [])
        self.assertEqual(report_layout.counts(groups), {"main": 0, "details": 0, "total": 0})

    def test_partition_preserves_each_original_object_once_without_mutation(self):
        original = list(self.rows)
        groups = report_layout.layout(self.rows)
        flattened = [row for group in groups for row in group["rows"]]
        self.assertEqual(self.rows, original)
        self.assertEqual(Counter(map(id, flattened)), Counter(map(id, self.rows)))
        self.assertEqual(len({row[0] for row in flattened}), len(self.rows))
        for group in groups:
            self.assertTrue(group["rows"])
            self.assertTrue(isinstance(group["title"], str) and group["title"].strip())
            self.assertIsInstance(group["description"], str)
            self.assertIs(type(group["details"]), bool)
        numbers = report_layout.counts(groups)
        self.assertEqual(numbers["total"], len(self.rows))
        self.assertEqual(numbers["main"] + numbers["details"], numbers["total"])
        self.assertEqual(numbers["details"], sum(len(group["rows"]) for group in groups if group["details"]))

    def test_group_order_is_deterministic_and_does_not_depend_on_first_seen_row(self):
        first = report_layout.layout(self.rows)
        repeated = report_layout.layout(self.rows)
        reverse_input = report_layout.layout(list(reversed(self.rows)))
        self.assertEqual(first, repeated)
        self.assertEqual(first, reverse_input)

    def test_unknown_details_are_alphabetical_and_duplicate_inputs_are_preserved(self):
        alpha = sample_row("Alpha Future Marker", "index", "1")
        zulu = sample_row("Zulu Future Marker", "index", "2")
        same_name_distinct_row = sample_row("Alpha Future Marker", "index", "3")
        inputs = [zulu, alpha, same_name_distinct_row, alpha]
        groups = report_layout.layout(inputs)
        self.assertEqual(len(groups), 1)
        self.assertTrue(groups[0]["details"])
        rows = groups[0]["rows"]
        self.assertEqual([row[0] for row in rows],
                         ["Alpha Future Marker"] * 3 + ["Zulu Future Marker"])
        self.assertEqual(Counter(map(id, rows)), Counter(map(id, inputs)))
        self.assertEqual(report_layout.counts(groups), {"main": 0, "details": 4, "total": 4})

    def test_user_requested_body_and_fitness_metrics_remain_visible(self):
        main = {row[0] for group in report_layout.layout(self.rows) if not group["details"] for row in group["rows"]}
        self.assertTrue({"Bone", "Visceral Fat Index", "VO2max", "PWV"}.issubset(main))
        bone = next(row for row in self.rows if row[0] == "Bone")
        self.assertEqual(bone[-2], "%")

    def test_unknown_future_metric_is_retained_in_details(self):
        unknown = self.rows[-1]
        group = next(group for group in report_layout.layout(self.rows) if any(row is unknown for row in group["rows"]))
        self.assertTrue(group["details"])
        self.assertEqual(group["rows"][-1][-2:], ("index", "-"))


class GroupedRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ignore the real synced file. Loading generator definitions writes no
        # outputs; all actual render checks below use synthetic rows or tempfiles.
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "monthly.json"
            source.write_text(json.dumps({"schema_version": 1, "as_of": "2026-09-06", "months": {}}), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(source)}):
                cls.report = runpy.run_path(str(Path(__file__).parents[1] / "generate_colored_report.py"), run_name="layout_test")

    def setUp(self):
        dates = self.report["date_columns"]
        self.rows = []
        for name, unit, value in [
            ("Bone", "%", "4.2"), ("Visceral Fat Index", "index", "2.3"),
            ("VO2max", "ml/kg/min", "44"), ("PWV", "m/s", "6.1"),
            ("Body Mass", "kg", "80.4"), ("Sleep Duration", "h", "7.51"),
            ("Future Firmware Marker (Oura)", "index", "12.3"),
        ]:
            values = [value if month in {"2026-07", "2026-08", "2026-09"} else "-" for month in dates]
            self.rows.append((name, *values, unit, "-"))

    def test_html_groups_keep_every_row_once_and_details_start_closed(self):
        rendered = self.report["render_vitals_html"](self.rows)
        parsed = TableRows()
        parsed.feed(rendered)
        display = lambda name: self.report["display_metric_name"]("Vitals & Functional Health", name)
        expected = {display(row[0]) for row in self.rows}
        actual = [row[0] for row in parsed.rows if row and row[0] in expected]
        self.assertEqual(Counter(actual), Counter(expected))
        self.assertTrue(parsed.details)
        self.assertTrue(all("open" not in attributes for attributes in parsed.details))
        main = {row[0] for row, depth in zip(parsed.rows, parsed.row_depths) if depth == 0}
        self.assertTrue({"Bone", "Visceral Fat Index", "VO2max", "PWV"}.issubset(main))
        hidden = {row[0] for row, depth in zip(parsed.rows, parsed.row_depths) if depth > 0}
        self.assertIn(display("Future Firmware Marker (Oura)"), hidden)

    def test_markdown_keeps_every_row_once_and_retains_native_disclosure(self):
        rendered = self.report["render_vitals_md"](self.rows)
        expected = {self.report["display_metric_name"]("Vitals & Functional Health", row[0]) for row in self.rows}
        names = [unescape(name) for name in re.findall(r"(?m)^\| \*\*(.*?)\*\* \|", rendered)]
        self.assertEqual(Counter(name for name in names if name in expected), Counter(expected))
        self.assertIn("<details>", rendered)
        self.assertIn("<summary>", rendered)
        self.assertNotRegex(rendered, r"<details\s+open")
        self.assertEqual(rendered.count("<details>"), rendered.count("</details>"))

    def test_group_titles_never_replace_canonical_category_for_scoring_or_notes(self):
        for renderer_name in ("render_vitals_html", "render_vitals_md"):
            renderer = self.report[renderer_name]
            namespace = renderer.__globals__
            scoring = MagicMock(wraps=namespace["target_reference"])
            notes = MagicMock(wraps=namespace["note_numbers"])
            with self.subTest(renderer=renderer_name), patch.dict(namespace, {"target_reference": scoring, "note_numbers": notes}):
                renderer(self.rows)
            self.assertGreater(scoring.call_count, 0)
            self.assertGreater(notes.call_count, 0)
            self.assertEqual({call.args[0] for call in scoring.call_args_list}, {"Vitals & Functional Health"})
            self.assertEqual({call.args[0] for call in notes.call_args_list}, {"Vitals & Functional Health"})

    def test_each_subtable_omits_only_its_entirely_empty_months(self):
        observations = {
            "Bone": {"2026-07": "4.2"},
            "Body Mass": {"2026-09": "80.4"},
            "Future Firmware Marker (Oura)": {"2026-08": "12.3"},
        }
        rows = [
            (row[0], *(observations[row[0]].get(month, "-") for month in self.report["date_columns"]), *row[-2:])
            for row in self.rows if row[0] in observations
        ]
        display_observations = {
            self.report["display_metric_name"]("Vitals & Functional Health", name): values
            for name, values in observations.items()
        }
        for output_format in ("html", "md"):
            renderer = self.report[f"render_vitals_{output_format}"]
            with self.subTest(output_format=output_format), patch.dict(renderer.__globals__, {
                f"format_cell_{output_format}": lambda value, *_: str(value),
            }):
                rendered = renderer(rows)
                header = None
                found = set()
                for cells in rendered_table_rows(rendered, output_format):
                    if cells[0] == "Metric":
                        header = cells
                        continue
                    found.add(cells[0])
                    expected_months = (["2026-08"] if cells[0].startswith("Future")
                                       else ["2026-09", "2026-07"])
                    self.assertEqual([value for value in header if re.fullmatch(r"\d{4}-\d{2}", value)],
                                     expected_months)
                    self.assertEqual(len(cells), len(header))
                    for month in expected_months:
                        self.assertEqual(cells[header.index(month)], display_observations[cells[0]].get(month, "-"))
                self.assertEqual(found, set(display_observations))

    def test_trend_header_and_cell_are_second_in_both_table_modes(self):
        values = {"2026-09": "6.1", "2026-08": "6.5", "2026-07": "7.0"}
        row = ("PWV", *(values.get(month, "-") for month in self.report["date_columns"]), "m/s", "< 10")
        for output_format in ("html", "md"):
            renderer = self.report[f"render_result_table_{output_format}"]
            for compact in (False, True):
                with self.subTest(output_format=output_format, compact=compact), patch.dict(renderer.__globals__, {
                    f"format_trend_{output_format}": MagicMock(return_value="trend-sentinel"),
                    f"format_cell_{output_format}": lambda value, *_: f"value-{value}",
                }):
                    rendered = renderer("Vitals & Functional Health", [row], compact=compact)
                    header, cells = rendered_table_rows(rendered, output_format)
                    self.assertEqual(header[:2], ["Metric" if compact else "", "Trend"])
                    self.assertEqual(cells[:2], ["PWV", "trend-sentinel"])
                    self.assertEqual(header[2:5], ["2026-09", "2026-08", "2026-07"])
                    self.assertEqual(cells[2:5], ["value-6.1", "value-6.5", "value-7.0"])
                    self.assertEqual(cells[header.index("Unit")], "m/s")
                    self.assertEqual(len(cells), len(header))

    def test_compact_reference_omits_empty_column_and_preserves_real_reference(self):
        unknown = ("Future Firmware Marker (Oura)", *self.rows[0][1:])
        for renderer_name, header in (("render_result_table_html", "<i>Reference</i>"),
                                      ("render_result_table_md", "*Reference*")):
            renderer = self.report[renderer_name]
            no_reference = renderer("Vitals & Functional Health", [unknown], compact=True)
            with_reference = renderer("Vitals & Functional Health", [self.rows[3]], compact=True)
            self.assertNotIn(header, no_reference)
            self.assertNotRegex(no_reference, r"no clinical target|no separate target|[Uu]nclassified")
            self.assertIn(header, with_reference)
            self.assertIn("target &lt; 7" if renderer_name.endswith("html") else "target < 7", with_reference)

    def test_single_observations_in_different_months_do_not_create_a_trend_column(self):
        dates = self.report["date_columns"]
        rows = [
            ("Chest Circumference", *("105" if month == "2026-09" else "-" for month in dates), "cm", "-"),
            ("Hip Circumference", *("97" if month == "2026-07" else "-" for month in dates), "cm", "-"),
        ]
        for output_format in ("html", "md"):
            for compact in (False, True):
                with self.subTest(output_format=output_format, compact=compact):
                    rendered = self.report[f"render_result_table_{output_format}"](
                        "Vitals & Functional Health", rows, compact=compact)
                    header, *results = rendered_table_rows(rendered, output_format)
                    self.assertNotIn("Trend", header)
                    self.assertEqual([cell for cell in header if re.fullmatch(r"\d{4}-\d{2}", cell)],
                                     ["2026-09", "2026-07"])
                    self.assertEqual(len(results), 2)
                    self.assertTrue(all(len(row) == len(header) for row in results))

    def test_repeated_height_and_single_body_measurement_do_not_create_a_trend(self):
        dates = self.report["date_columns"]
        rows = [
            ("Height", *("180" if month in {"2026-09", "2026-07"} else "-" for month in dates), "cm", "-"),
            ("Chest Circumference", *("105" if month == "2026-09" else "-" for month in dates), "cm", "-"),
        ]
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = self.report[f"render_result_table_{output_format}"]("Vitals & Functional Health", rows, compact=True)
                header, *results = rendered_table_rows(rendered, output_format)
                self.assertNotIn("Trend", header)
                self.assertEqual(results[0][header.index("2026-09")], "180")
                self.assertEqual(results[0][header.index("2026-07")], "180")

    def test_provider_suffixes_are_removed_only_when_display_names_remain_unique(self):
        display = self.report["display_metric_name"]
        category = "Vitals & Functional Health"
        original = [tuple(row) for row in self.report["data"][category]]
        names = [row[0] for row in original]
        labels = [display(category, name) for name in names]
        self.assertEqual(len(labels), len(set(labels)))
        self.assertEqual(display(category, "Future Firmware Marker (Oura)"), "Future Firmware Marker")
        self.assertEqual(display(category, "Nerve Health Score Left Foot (Withings)"), "Nerve Health Score Left Foot")
        self.assertEqual(display(category, "Sleep Score (Withings)"), "Sleep Score (Withings)")
        self.assertEqual(display(category, "Sleep Score"), "Sleep Score")
        self.assertEqual(self.report["data"][category], original)
        self.assertIn("Average Sleeping HR (Oura)", names)


if __name__ == "__main__":
    unittest.main()
