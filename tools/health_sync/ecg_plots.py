"""Render recorded ECG samples without filtering, resampling or interpretation."""

from datetime import datetime
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path

from .withings import ecg_signal_inventory


PLOT_VERSION = "ecg-raw-v1"


def graph_path(record):
    content = {key: record.get(key) for key in
               ("recorded_at", "sampling_frequency_hz", "signal_uv", "heart_rate_bpm", "af_classification")}
    content["plot_version"] = PLOT_VERSION
    digest = hashlib.sha256(json.dumps(content, sort_keys=True, allow_nan=False).encode()).hexdigest()[:12]
    stamp = datetime.fromisoformat(record["recorded_at"]).strftime("%Y-%m-%d_%H-%M-%S")
    return f"results/ECG/{stamp}_{digest}.svg"


def render_ecg_svg(record):
    """Full-resolution vector strips: 25mm/s and 10mm/mV at native print size."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        from matplotlib.figure import Figure
        from matplotlib.ticker import MultipleLocator, FuncFormatter
    except ImportError:
        raise RuntimeError("ECG graphs require: python -m pip install -r tools/requirements-ecg.txt") from None

    frequency = record["sampling_frequency_hz"]
    samples = record["signal_uv"]
    if (not samples or isinstance(frequency, bool) or not isinstance(frequency, (int, float))
            or not math.isfinite(frequency) or frequency <= 0
            or any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not math.isfinite(value) for value in samples)):
        raise ValueError("ECG plotting requires finite samples and a positive sampling frequency.")
    if record.get("amplitude_unit") != "uV":
        raise ValueError("ECG signal amplitude must be explicitly identified as microvolts.")
    duration = len(samples) / frequency
    strip_seconds = min(10, max(1, math.ceil(duration)))
    strips = math.ceil(duration / strip_seconds)
    if strips > 60:
        raise ValueError("ECG recording exceeds the supported graph length.")
    mv = [value / 1000 for value in samples]
    low = min(-0.5, math.floor((min(mv) - 0.1) * 2) / 2)
    high = max(0.5, math.ceil((max(mv) + 0.1) * 2) / 2)
    # Preserve all samples and the full amplitude range, including artifacts.
    # Native dimensions encode the standard ECG time/voltage scale; responsive
    # browser zoom changes physical size, while axis values remain accurate.
    width_mm = strip_seconds * 25 + 24
    strip_height_mm = (high - low) * 10
    gap_mm, top_mm, bottom_mm = 12, 29, 13
    height_mm = top_mm + strips * strip_height_mm + (strips - 1) * gap_mm + bottom_mm
    style = {"svg.hashsalt": PLOT_VERSION, "svg.fonttype": "none", "path.simplify": False,
             "font.family": "DejaVu Sans", "font.size": 8, "axes.linewidth": 0.4}
    with matplotlib.rc_context(style):
        fig = Figure(figsize=(width_mm / 25.4, height_mm / 25.4), facecolor="white")
        stamp = datetime.fromisoformat(record["recorded_at"])
        title = "ECG · " + stamp.strftime("%Y-%m-%d %H:%M:%S %z")
        hr = record.get("heart_rate_bpm")
        af = record.get("af_classification")
        outcome = {"Negative": "No AF detected (device)", "Positive": "AF detected (device)",
                   "Inconclusive": "Inconclusive (device)"}.get(af, "AF result not supplied")
        summary = f"Withings · {duration:g}s · {frequency:g}Hz"
        if hr is not None:
            summary += f" · {hr:g}bpm"
        summary += " · " + outcome
        fig.text(16 / width_mm, 1 - 8 / height_mm, title, fontsize=12, weight="bold", va="top", color="#123653")
        fig.text(16 / width_mm, 1 - 16 / height_mm, summary, fontsize=8.5, va="top", color="#334155")
        for index in range(strips):
            start, end = index * strip_seconds, (index + 1) * strip_seconds
            first = round(start * frequency)
            last = min(len(mv), round(end * frequency))
            top = top_mm + index * (strip_height_mm + gap_mm)
            axes = fig.add_axes((16 / width_mm, 1 - (top + strip_height_mm) / height_mm,
                                 strip_seconds * 25 / width_mm, strip_height_mm / height_mm))
            axes.set_xlim(start, end)
            axes.set_ylim(low, high)
            axes.set_facecolor("#fffdfd")
            axes.xaxis.set_major_locator(MultipleLocator(0.2))
            axes.xaxis.set_minor_locator(MultipleLocator(0.04))
            axes.yaxis.set_major_locator(MultipleLocator(0.5))
            axes.yaxis.set_minor_locator(MultipleLocator(0.1))
            axes.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}" if abs(value-round(value)) < 1e-6 else ""))
            axes.grid(which="major", color="#e8a7ae", linewidth=0.45)
            axes.grid(which="minor", color="#f5dce0", linewidth=0.25)
            axes.tick_params(which="both", length=0, labelsize=7, colors="#475569", pad=3)
            axes.set_ylabel("mV", fontsize=8, labelpad=3)
            axes.set_xlabel("Time (s)", fontsize=8, labelpad=2)
            for spine in axes.spines.values():
                spine.set_color("#d99ca4")
            line, = axes.plot([sample / frequency for sample in range(first, last)], mv[first:last],
                              color="#17212c", linewidth=0.6, solid_capstyle="round")
            line.set_gid(f"ecg-samples-{first}-{last}")
        fig.text(16 / width_mm, 3 / height_mm,
                 f"Original device signal · {len(samples):,} samples · grid 0.2s × 0.5mV · 25mm/s, 10mm/mV at 100% print size",
                 fontsize=7, color="#64748b")
        buffer = BytesIO()
        fig.savefig(buffer, format="svg", metadata={"Date": None, "Creator": "Health protocol ECG renderer"})
        return buffer.getvalue()


def prepare_ecg_graphs(root, summaries, incoming=()):
    """Return enriched metadata and staged graph bytes; never change raw sources."""
    root = Path(root).resolve()
    raw_root = (root / ".health-sync" / "raw" / "withings").resolve()
    available = {record["id"]: record for record in incoming}
    loaded = {}
    enriched, changes = [], {}
    for summary in summaries:
        record = available.get(summary["id"])
        if record is None:
            source = (root / summary["source_file"]).resolve()
            if not source.is_relative_to(raw_root):
                raise ValueError("ECG source must be in the private Withings raw archive.")
            if source not in loaded:
                payload = json.loads(source.read_text(encoding="utf-8"))
                loaded[source] = {item["id"]: item for item in ecg_signal_inventory(payload)}
            record = loaded[source].get(summary["id"])
        if record is None:
            raise ValueError("A recorded ECG waveform is missing from its source archive.")
        if any(record[key] != summary[key] for key in ("recorded_at", "sample_count", "sampling_frequency_hz")):
            raise ValueError("ECG waveform does not match its dated metadata.")
        if (len(record["signal_uv"]) != summary["sample_count"]
                or not math.isclose(len(record["signal_uv"]) / record["sampling_frequency_hz"],
                                    summary["duration_seconds"], rel_tol=1e-9)
                or record.get("amplitude_unit") != "uV"):
            raise ValueError("ECG waveform samples, duration or units do not match its metadata.")
        path = graph_path(record)
        updated = {**summary, "graph_path": path}
        for key in ("heart_rate_bpm", "af_classification"):
            updated.pop(key, None)
            if key in record:
                updated[key] = record[key]
        enriched.append(updated)
        destination = root / path
        if not destination.exists():
            changes[destination] = render_ecg_svg(record)
    return enriched, changes
