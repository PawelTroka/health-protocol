"""Dated ECG metadata tests using synthetic signals and no private files."""

import copy
from datetime import date, datetime
import unittest

from tools.health_sync.ecg_records import (
    merge_summaries, public_summaries, render_ecg_html, render_ecg_md, summarize_inventory,
)
from tools.health_sync.withings import ecg_signal_inventory


def trace(identifier="one", day="2026-09-01", **changes):
    return {"provider": "withings", "id": f"withings:ecg_signal:{identifier}",
            "signalid": identifier, "day": day, "recorded_at": day + "T12:00:00+02:00",
            "kind": "ecg_waveform", "source_kind": "api", "amplitude_unit": "uV",
            "sampling_frequency_hz": 10, "sample_count": 4, "duration_seconds": 0.4,
            "signal_uv": [11, 22, 33, 44], "model": 21, "wearposition": 0, **changes}


def summary(identifier="one", day="2026-09-01", **changes):
    return summarize_inventory([trace(identifier, day, **changes)], ".health-sync/raw/withings/private.json")[0]


class ECGRecordsTests(unittest.TestCase):
    def test_actual_withings_inventory_projects_to_public_recording_metadata(self):
        timestamp = int(datetime.fromisoformat("2026-09-01T12:00:00+02:00").timestamp())
        payload = {"heart_signals": [{"signalid": 1234, "timestamp": timestamp,
                                     "data": {"signal": [11, 22, 33, 44], "sampling_frequency": 10,
                                              "model": 21, "wearposition": 0}}]}
        original = copy.deepcopy(payload)
        private = summarize_inventory(ecg_signal_inventory(payload), "private.json")
        self.assertEqual(public_summaries(private), [{"provider": "withings",
            "recorded_at": "2026-09-01T12:00:00+02:00", "sample_count": 4,
            "sampling_frequency_hz": 10, "duration_seconds": 0.4}])
        self.assertEqual(payload, original)

    def test_metadata_summary_drops_signal_and_unknown_fields_without_mutating_inventory(self):
        inventory = [trace(unexpected_private_payload={"secret": "value"})]
        original = copy.deepcopy(inventory)
        result = summarize_inventory(inventory + inventory, ".health-sync/raw/withings/private.json")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sample_count"], 4)
        self.assertEqual(result[0]["source_file"], ".health-sync/raw/withings/private.json")
        self.assertNotIn("signal_uv", result[0])
        self.assertNotIn("unexpected_private_payload", result[0])
        self.assertEqual(inventory, original)

    def test_public_projection_is_an_explicit_allowlist_with_latest_first(self):
        entries = [summary("early"), summary("late", "2026-09-03")]
        original = copy.deepcopy(entries)
        rows = public_summaries(entries)
        self.assertEqual(rows[0]["recorded_at"], "2026-09-03T12:00:00+02:00")
        self.assertEqual(set(rows[0]), {"recorded_at", "provider", "sample_count",
                                       "duration_seconds", "sampling_frequency_hz"})
        self.assertEqual(entries, original)

    def test_optional_provider_results_and_safe_graph_path_reach_public_rows(self):
        path = "results/ECG/2026-09-01_12-00-00_abcdef123456.svg"
        entry = summary(heart_rate_bpm=62, af_classification="Negative", graph_path=path)
        row = public_summaries([entry])[0]
        self.assertEqual(row["heart_rate_bpm"], 62)
        self.assertEqual(row["af_classification"], "Negative")
        self.assertEqual(row["graph_path"], path)
        self.assertEqual(set(row), {"recorded_at", "provider", "sample_count", "duration_seconds",
                                    "sampling_frequency_hz", "heart_rate_bpm", "af_classification", "graph_path"})
        self.assertEqual(public_summaries([summary(heart_rate_bpm=None, af_classification=None, graph_path=None)]),
                         public_summaries([summary()]))

    def test_provider_classifications_are_not_reinterpreted_as_sinus_rhythm(self):
        path = "results/ECG/2026-09-01_12-00-00_abcdef123456.svg"
        for classification, label in (("Negative", "🔵 No AF detected"), ("Positive", "🟠 AF detected"),
                                      ("Inconclusive", "⚪ Inconclusive")):
            rows = public_summaries([summary(heart_rate_bpm=62.5, af_classification=classification, graph_path=path)])
            for render in (render_ecg_html, render_ecg_md):
                with self.subTest(classification=classification, render=render.__name__):
                    text = render(rows)
                    self.assertIn(label, text)
                    self.assertIn("62.5 bpm", text)
                    self.assertIn(path, text)
                    self.assertIn("View trace", text)
                    self.assertNotIn("sinus", text.lower())
                    self.assertNotIn("private sync archive", text)
        self.assertIn(f'<a href="{path}">View trace</a>', render_ecg_html(rows))
        self.assertIn(f"[View trace]({path})", render_ecg_md(rows))

    def test_unsafe_graph_paths_and_invalid_results_are_rejected(self):
        invalid_paths = ["javascript:alert(1)", "https://example.com/trace.svg", ".health-sync/raw/signal.json",
                         "results/ECG/../private.svg", "results/ECG/%2e%2e/private.svg",
                         "results/ECG/2026-09-01_12-00-00_ABCDEF123456.svg",
                         "results/ECG/2026-09-01_12-00-00_abcdef123456.svg?private=secret",
                         "results/ECG/2026-09-01_12-00-00_abcdef123456.svg\n", "", 123]
        for path in invalid_paths:
            with self.subTest(path=path), self.assertRaises(ValueError):
                summary(graph_path=path)
            for render in (render_ecg_html, render_ecg_md):
                with self.subTest(path=path, render=render.__name__), self.assertRaises(ValueError):
                    render([{**public_summaries([summary()])[0], "graph_path": path}])
        for changes in ({"heart_rate_bpm": 0}, {"heart_rate_bpm": True}, {"heart_rate_bpm": float("inf")},
                        {"af_classification": "Normal sinus rhythm"}, {"af_classification": []}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                summary(**changes)

    def test_partial_merge_amends_ids_and_retains_unrepresented_dates(self):
        old = [summary("july", "2026-07-01"), summary("one"), summary("two", "2026-09-02")]
        replacement = summary("one", model=99)
        incoming = [replacement, summary("outside", "2026-10-01")]
        original = copy.deepcopy((old, incoming))
        result = merge_summaries(old, incoming, date(2026, 9, 1), date(2026, 9, 30))
        self.assertEqual(len(result), 3)
        self.assertEqual(next(row for row in result if row["signalid"] == "one")["model"], 99)
        self.assertEqual({row["signalid"] for row in result}, {"july", "one", "two"})
        self.assertEqual((old, incoming), original)
        self.assertEqual(result, merge_summaries(result, incoming, "2026-09-01", "2026-09-30"))

    def test_complete_window_can_remove_missing_recordings_but_not_other_months(self):
        old = [summary("july", "2026-07-01"), summary("one"), summary("two", "2026-09-02")]
        result = merge_summaries(old, [summary("new", "2026-09-04")], "2026-09-01", "2026-09-30", complete=True)
        self.assertEqual({row["signalid"] for row in result}, {"july", "new"})
        self.assertEqual(merge_summaries(old, [], "2026-09-01", "2026-09-30", complete=True), old[:1])
        self.assertEqual(merge_summaries(old, [], "2026-09-01", "2026-09-30"), old)

    def test_conflicting_duplicate_ids_invalid_dates_and_inconsistent_metadata_rejected(self):
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            summarize_inventory([trace(), trace(model=99)], "private.json")
        for changes in ({"recorded_at": "2026-09-01T12:00:00"}, {"recorded_at": "2026-09-02T12:00:00+02:00"},
                        {"sample_count": True}, {"sampling_frequency_hz": 0},
                        {"duration_seconds": float("nan")}, {"duration_seconds": 1}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                summary(**changes)
        with self.assertRaises(ValueError):
            merge_summaries([], [], "2026-09-02", "2026-09-01")
        with self.assertRaisesRegex(ValueError, "outside"):
            merge_summaries([summary("same", "2026-07-01")], [summary("same")],
                            "2026-09-01", "2026-09-30")

    def test_rendering_is_closed_compact_and_never_exposes_private_metadata(self):
        private = summary()
        for render in (render_ecg_html, render_ecg_md):
            text = render([private])  # Even accidental private input is safe.
            self.assertIn("Recorded ECG traces · 1 recordings", text)
            self.assertIn("2026-09-01 12:00:00+02:00", text)
            self.assertIn("Withings", text)
            self.assertNotIn("private sync archive", text)
            self.assertNotIn("View trace", text)
            self.assertIn("—", text)
            self.assertNotIn("<details open", text)
            for secret in ("withings:ecg_signal:one", ".health-sync", "private.json", "signal_uv", "wearposition"):
                self.assertNotIn(secret, text)
            self.assertEqual(render([]), "")

    def test_both_renderers_escape_fields_and_markdown_cannot_add_rows_or_columns(self):
        rows = [{"recorded_at": '<script>alert("x")</script>|\nextra [private](secret)',
                 "heart_rate_bpm": "<img>100 & 200", "provider": "withings"}]
        for render in (render_ecg_html, render_ecg_md):
            text = render(rows)
            self.assertNotIn("<script>", text)
            self.assertNotIn("<img>", text)
            self.assertIn("&lt;script&gt;", text)
            self.assertIn("100 &amp; 200", text)
        markdown = render_ecg_md(rows)
        self.assertIn("&#124;", markdown)
        self.assertNotIn("\nextra", markdown)
        self.assertIn(r"\[private\](secret)", markdown)
        self.assertEqual(sum(line.startswith("|") for line in markdown.splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
