"""Contrast checks on rendered report text; no private files or report writes."""

from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import patch

from tools.health_sync.report_colors import (
    TEXT_BACKGROUNDS, contrast_ratio, readable_text_color,
)


class TextColors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.colors = []

    def handle_starttag(self, tag, attrs):
        style = dict(attrs).get("style", "")
        match = re.search(r"(?:^|;)\s*color\s*:\s*(#[0-9a-fA-F]{6})", style)
        if match:
            self.colors.append(match[1])


class ReportColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "monthly.json"
            source.write_text(json.dumps({"schema_version": 1, "as_of": "2026-11-21", "months": {}}),
                              encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(source)}):
                cls.report = runpy.run_path(str(Path(__file__).parents[1] / "generate_colored_report.py"),
                                           run_name="report_color_test")

    def assert_readable(self, colors):
        self.assertTrue(colors)
        for color in set(colors):
            for background in TEXT_BACKGROUNDS:
                with self.subTest(color=color, background=background):
                    self.assertGreaterEqual(contrast_ratio(color, background), 4.5)

    def colors(self, rendered):
        parser = TextColors()
        parser.feed(rendered)
        return parser.colors

    def test_contrast_formula_matches_known_extremes_and_unrounded_threshold(self):
        self.assertEqual(contrast_ratio("#ffffff", "#000000"), 21)
        self.assertEqual(contrast_ratio("#000000", "#ffffff"), 21)
        self.assertEqual(contrast_ratio("#abcdef", "#abcdef"), 1)
        self.assertLess(contrast_ratio("#777777", "#ffffff"), 4.5)
        self.assertGreater(contrast_ratio("#767676", "#ffffff"), 4.5)

    def test_readable_foregrounds_are_unchanged_and_light_ones_keep_channel_order(self):
        for color in ("#00008b", "#006400", "#a84a00", "#8b0000"):
            with self.subTest(color=color):
                self.assertEqual(readable_text_color(color), color)
        for color in ("#00bfff", "#32cd32", "#ffd700", "#ffa500", "#ff4500", "#ffffff"):
            adjusted = readable_text_color(color)
            with self.subTest(color=color):
                self.assertNotEqual(adjusted, color)
                self.assert_readable([adjusted])
                source = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
                result = [int(adjusted[i:i + 2], 16) for i in (1, 3, 5)]
                self.assertTrue(all(new <= old for new, old in zip(result, source)))
                for left in range(3):
                    for right in range(3):
                        if source[left] <= source[right]:
                            self.assertLessEqual(result[left], result[right])
                self.assertEqual(readable_text_color(adjusted), adjusted)

    def test_every_numeric_gradient_segment_is_readable_when_rendered(self):
        for index in range(501):
            # A 0–2 reference maps the input directly onto the existing score.
            value = str(1 + index / 100)
            with self.subTest(value=value):
                rendered = self.report["format_cell_html"](value, "0 - 2")
                self.assert_readable(self.colors(rendered))

    def test_urinalysis_attention_color_and_qualitative_statuses_are_readable(self):
        for value, reference in (("4", "5 - 8"), ("present", "absent"), ("6", "5 - 8")):
            self.assert_readable(self.colors(self.report["format_cell_html_urine"](value, reference)))
        for value in ("negative", "positive", "equivocal", "pending"):
            rendered = self.report["format_status"](value, self.report["qualitative_status"](value),
                                                    show_neutral=True)
            self.assert_readable(self.colors(rendered))

    def test_all_current_report_table_foregrounds_and_legend_are_readable(self):
        colors = []
        for category, rows in self.report["data"].items():
            colors.extend(self.colors(self.report["render_result_table_html"](category, rows)))
        self.assertGreater(len(colors), 500)
        self.assertGreater(len(set(colors)), 30)
        self.assert_readable(colors)
        legend_colors = self.colors(self.report["render_color_legend_html"]())
        self.assertEqual(len(legend_colors), 9)
        self.assert_readable(legend_colors)


if __name__ == "__main__":
    unittest.main()
