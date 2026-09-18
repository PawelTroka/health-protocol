"""ECG export checks with synthetic signals; never read the account archive."""

import copy
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from tools.health_sync.ecg_plots import graph_path, prepare_ecg_graphs, render_ecg_svg
from tools.health_sync.ecg_records import summarize_inventory
from tools.health_sync.withings import ecg_signal_inventory


SVG = "{http://www.w3.org/2000/svg}"
POINTS_PER_MM = 72 / 25.4
HAS_MATPLOTLIB = importlib.util.find_spec("matplotlib") is not None


def trace(samples=None, frequency=4, **changes):
    samples = [0, 1000, 0, -1000, 250, -250, 500, 0] if samples is None else samples
    return {"provider": "withings", "id": "withings:ecg_signal:private-id",
            "signalid": "private-id", "day": "2026-09-01",
            "recorded_at": "2026-09-01T12:34:56+02:00", "kind": "ecg_waveform",
            "source_kind": "api", "amplitude_unit": "uV", "signal_uv": samples,
            "sampling_frequency_hz": frequency, "sample_count": len(samples),
            "duration_seconds": len(samples) / frequency if frequency else 0,
            "model": 44, "wearposition": 3, "heart_rate_bpm": 63,
            "af_classification": "Negative", **changes}


def payload(records):
    return {"heart_signals": [{"signalid": row["signalid"],
            "timestamp": int(datetime.fromisoformat(row["recorded_at"]).timestamp()),
            "data": {"signal": row["signal_uv"], "sampling_frequency": row["sampling_frequency_hz"],
                     "model": row["model"], "wearposition": row["wearposition"]}}
            for row in records],
            "heart_series": [{"heart_rate": row["heart_rate_bpm"],
                              "ecg": {"signalid": row["signalid"], "afib": 0}}
                             for row in records]}


def write_archive(root, records):
    relative = ".health-sync/raw/withings/synthetic.json"
    source = root / relative
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(json.dumps(payload(records)), encoding="utf-8")
    inventory = ecg_signal_inventory(payload(records))
    return source, inventory, summarize_inventory(inventory, relative)


def sample_paths(svg):
    root = ET.fromstring(svg)
    paths = []
    for group in root.iter(SVG + "g"):
        if group.get("id", "").startswith("ecg-samples-"):
            path = group.find(SVG + "path")
            commands = re.findall(r"[A-Za-z]", path.attrib["d"])
            if commands != ["M"] + ["L"] * (len(commands) - 1):
                raise AssertionError("The ECG trace must retain explicit unsmoothed sample vertices")
            numbers = [float(value) for value in re.findall(
                r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", path.attrib["d"])]
            paths.append((group.attrib["id"], list(zip(numbers[::2], numbers[1::2]))))
    return root, paths


@unittest.skipUnless(HAS_MATPLOTLIB, "Install tools/requirements-ecg.txt for SVG geometry checks")
class ECGSVGTests(unittest.TestCase):
    def test_recognizable_samples_preserve_time_voltage_polarity_and_native_scale(self):
        record = trace()
        snapshot = copy.deepcopy(record)
        svg, paths = sample_paths(render_ecg_svg(record))
        self.assertEqual(len(paths), 1)
        name, coordinates = paths[0]
        self.assertEqual(name, "ecg-samples-0-8")
        self.assertEqual(len(coordinates), len(record["signal_uv"]))
        x0, y0 = coordinates[0]
        for index, ((x, y), microvolts) in enumerate(zip(coordinates, record["signal_uv"])):
            self.assertAlmostEqual(x - x0, index / 4 * 25 * POINTS_PER_MM, places=4)
            # SVG y grows down the page: a positive 1,000µV must rise 10mm.
            self.assertAlmostEqual(y0 - y, microvolts / 1000 * 10 * POINTS_PER_MM, places=4)
        self.assertAlmostEqual(float(svg.attrib["width"].removesuffix("pt")),
                               (2 * 25 + 24) * POINTS_PER_MM, places=4)
        text = " ".join(svg.itertext())
        self.assertIn("Time (s)", text)
        self.assertIn("mV", text)
        self.assertIn("63bpm", text)
        self.assertIn("No AF detected (device)", text)
        self.assertNotIn("sinus", text.lower())
        self.assertEqual(record, snapshot)

    def test_all_15000_native_samples_survive_three_strips_without_smoothing(self):
        samples = [0] * 15000
        for position, voltage in ((1, 1000), (4999, -500), (5000, 750),
                                  (9999, -125), (10000, 375), (14999, -1000)):
            samples[position] = voltage
        _, paths = sample_paths(render_ecg_svg(trace(samples, 500)))
        self.assertEqual([name for name, _ in paths], [
            "ecg-samples-0-5000", "ecg-samples-5000-10000", "ecg-samples-10000-15000"])
        self.assertEqual(sum(len(points) for _, points in paths), 15000)
        for strip, (_, points) in enumerate(paths):
            self.assertEqual(len(points), 5000)
            self.assertAlmostEqual(points[-1][0] - points[0][0],
                                   4999 / 500 * 25 * POINTS_PER_MM, places=4)
            baseline_y = points[2][1]
            for index in (0, 1, 4999):
                expected = samples[strip * 5000 + index] / 1000 * 10 * POINTS_PER_MM
                self.assertAlmostEqual(baseline_y - points[index][1], expected, places=4)

    def test_bytes_are_deterministic_and_exclude_private_identifiers(self):
        first = render_ecg_svg(trace())
        second = render_ecg_svg(trace(id="different-private-id", signalid="different-signal"))
        self.assertEqual(first, second)
        for private in (b"private-id", b"different-private-id", b"different-signal", b".health-sync"):
            self.assertNotIn(private, first)
        self.assertNotIn(b"<dc:date>", first)

    def test_invalid_physical_signal_inputs_fail_instead_of_drawing(self):
        invalid = [trace([]), trace(frequency=0), trace(frequency=-1),
                   trace(frequency=float("inf")), trace([0, float("nan")]),
                   trace([0, float("inf")]), trace([0, True]),
                   trace([0, "unknown"]),
                   {**trace(), "sampling_frequency_hz": True},
                   {**trace(), "sampling_frequency_hz": "500"},
                   trace(amplitude_unit="mV"), trace(amplitude_unit=None),
                   trace([0] * 601, frequency=1)]
        for record in invalid:
            with self.subTest(record=record), self.assertRaises(ValueError):
                render_ecg_svg(record)


class ECGGraphPreparationTests(unittest.TestCase):
    def test_paths_are_content_derived_stable_and_do_not_expose_source_ids(self):
        row = trace()
        path = graph_path(row)
        self.assertRegex(path, r"^results/ECG/2026-09-01_12-34-56_[0-9a-f]{12}\.svg$")
        self.assertEqual(path, graph_path({**row, "id": "another-private-id", "signalid": "another-id",
                                          "source_file": "secret-source.json"}))
        for updates in ({"signal_uv": [1] + row["signal_uv"][1:]},
                        {"sampling_frequency_hz": 8}, {"heart_rate_bpm": 70},
                        {"af_classification": "Positive"},
                        {"recorded_at": "2026-09-01T12:34:57+02:00"}):
            with self.subTest(updates=updates):
                self.assertNotEqual(path, graph_path({**row, **updates}))

    def test_private_archive_is_read_once_and_outputs_are_only_staged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, inventory, summaries = write_archive(root, [trace(), trace(
                id="withings:ecg_signal:second-private-id", signalid="second-private-id",
                recorded_at="2026-09-01T13:34:56+02:00", heart_rate_bpm=72)])
            before = source.read_bytes()
            metadata_before = copy.deepcopy(summaries)
            with patch("tools.health_sync.ecg_plots.json.loads", wraps=json.loads) as decode, \
                    patch("tools.health_sync.ecg_plots.render_ecg_svg", return_value=b"<svg/>") as render:
                enriched, staged = prepare_ecg_graphs(root, summaries)
            self.assertEqual(decode.call_count, 1)
            self.assertEqual(render.call_count, 2)
            self.assertEqual(len(staged), 2)
            for original, updated, record in zip(summaries, enriched, inventory):
                self.assertEqual(updated, {**original, "graph_path": graph_path(record)})
                self.assertEqual(staged[root.resolve() / updated["graph_path"]], b"<svg/>")
            self.assertFalse((root / "results").exists())
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(summaries, metadata_before)

    def test_incoming_waveform_can_be_staged_before_private_archive_is_published(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inventory = [trace()]
            summaries = summarize_inventory(inventory, ".health-sync/raw/withings/not-written-yet.json")
            before = copy.deepcopy(inventory)
            with patch("pathlib.Path.read_text", side_effect=AssertionError("Must use incoming signal")), \
                    patch("tools.health_sync.ecg_plots.render_ecg_svg", return_value=b"<svg/>"):
                enriched, staged = prepare_ecg_graphs(root, summaries, inventory)
            self.assertEqual(enriched[0]["graph_path"], graph_path(inventory[0]))
            self.assertEqual(len(staged), 1)
            self.assertEqual(inventory, before)

    def test_existing_content_addressed_graph_is_not_rewritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, inventory, summaries = write_archive(root, [trace()])
            path = root / graph_path(inventory[0])
            path.parent.mkdir(parents=True)
            path.write_bytes(b"existing verified graph")
            with patch("tools.health_sync.ecg_plots.render_ecg_svg") as render:
                enriched, staged = prepare_ecg_graphs(root, summaries)
            self.assertEqual(staged, {})
            render.assert_not_called()
            self.assertEqual(path.read_bytes(), b"existing verified graph")
            self.assertEqual(enriched[0]["graph_path"], path.relative_to(root).as_posix())

    def test_source_path_must_resolve_inside_private_withings_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, summaries = write_archive(root, [trace()])
            outside_paths = ["outside.json", ".health-sync/raw/withings/../../../outside.json",
                             ".health-sync/raw/withings-lookalike/synthetic.json",
                             str(root.parent / "outside.json")]
            for source in outside_paths:
                with self.subTest(source=source), patch("pathlib.Path.read_text") as read, \
                        self.assertRaisesRegex(ValueError, "private Withings raw archive"):
                    prepare_ecg_graphs(root, [{**summaries[0], "source_file": source}])
                read.assert_not_called()

    def test_symlink_cannot_escape_archive_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, _, summaries = write_archive(root, [trace()])
            outside = root / "outside.json"
            outside.write_bytes(source.read_bytes())
            link = source.parent / "link.json"
            try:
                link.symlink_to(outside)
            except OSError as error:
                self.skipTest(f"Creating symlinks is unavailable on this host: {error}")
            with self.assertRaisesRegex(ValueError, "private Withings raw archive"):
                prepare_ecg_graphs(root, [{**summaries[0], "source_file": link.relative_to(root).as_posix()}])

    def test_missing_waveform_and_mismatched_dated_metadata_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, summaries = write_archive(root, [trace()])
            with patch("tools.health_sync.ecg_plots.render_ecg_svg") as render:
                with self.assertRaisesRegex(ValueError, "missing from its source archive"):
                    prepare_ecg_graphs(root, [{**summaries[0], "id": "withings:ecg_signal:missing"}])
                for updates in ({"sample_count": 9}, {"sampling_frequency_hz": 8},
                                {"recorded_at": "2026-09-02T12:34:56+02:00"}):
                    with self.subTest(updates=updates), self.assertRaisesRegex(ValueError, "dated metadata"):
                        prepare_ecg_graphs(root, [{**summaries[0], **updates}])
            render.assert_not_called()

    def test_claimed_sample_count_cannot_hide_short_signal_wrong_units_or_duration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, inventory, summaries = write_archive(root, [trace()])
            for changes in ({"signal_uv": inventory[0]["signal_uv"][:-1]}, {"amplitude_unit": "mV"}):
                with self.subTest(changes=changes), \
                        patch("tools.health_sync.ecg_plots.render_ecg_svg") as render, \
                        self.assertRaisesRegex(ValueError, "samples, duration or units"):
                    prepare_ecg_graphs(root, summaries, [{**inventory[0], **changes}])
                render.assert_not_called()
            with self.assertRaisesRegex(ValueError, "samples, duration or units"):
                prepare_ecg_graphs(root, [{**summaries[0], "duration_seconds": 999}])

    def test_results_are_refreshed_from_the_same_source_trace_without_stale_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, inventory, summaries = write_archive(root, [trace()])
            stale = [{**summaries[0], "heart_rate_bpm": 999, "af_classification": "Positive"}]
            with patch("tools.health_sync.ecg_plots.render_ecg_svg", return_value=b"<svg/>"):
                enriched, _ = prepare_ecg_graphs(root, stale)
            self.assertEqual(enriched[0]["heart_rate_bpm"], 63)
            self.assertEqual(enriched[0]["af_classification"], "Negative")
            self.assertEqual(enriched[0]["graph_path"], graph_path(inventory[0]))
            signal_only = payload(inventory)
            signal_only["heart_series"] = []
            source.write_text(json.dumps(signal_only), encoding="utf-8")
            with patch("tools.health_sync.ecg_plots.render_ecg_svg", return_value=b"<svg/>"):
                without_results, _ = prepare_ecg_graphs(root, stale)
            self.assertNotIn("heart_rate_bpm", without_results[0])
            self.assertNotIn("af_classification", without_results[0])


if __name__ == "__main__":
    unittest.main()
