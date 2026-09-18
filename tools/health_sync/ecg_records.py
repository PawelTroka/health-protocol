"""Private ECG metadata reconciliation and dated results with graph links."""

from copy import deepcopy
from datetime import date, datetime
from html import escape
import math
import re


_PRIVATE_FIELDS = {
    "provider", "id", "signalid", "day", "recorded_at", "kind", "source_kind",
    "amplitude_unit", "sampling_frequency_hz", "sample_count", "duration_seconds",
    "model", "wearposition", "source_file", "heart_rate_bpm", "af_classification", "graph_path",
}
_PUBLIC_FIELDS = ("recorded_at", "provider", "sample_count", "duration_seconds", "sampling_frequency_hz")
_OPTIONAL_PUBLIC_FIELDS = ("heart_rate_bpm", "af_classification", "graph_path")
_AF_LABELS = {"Negative": "🔵 No AF detected", "Positive": "🟠 AF detected", "Inconclusive": "⚪ Inconclusive"}
_GRAPH_PATH = re.compile(r"results/ECG/[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}_[0-9a-f]{12}\.svg")


def _graph_path(value):
    if value is None:
        return None
    if not isinstance(value, str) or not _GRAPH_PATH.fullmatch(value):
        raise ValueError("An ECG graph must be a dated SVG in results/ECG.")
    return value


def _date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        parsed = date.fromisoformat(value)
        if parsed.isoformat() == value:
            return parsed
    raise ValueError("ECG coverage dates must use YYYY-MM-DD.")


def _private_entries(entries):
    if not isinstance(entries, list):
        raise ValueError("ECG summaries must be a list.")
    unique = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("An ECG summary must be an object.")
        record = {key: deepcopy(value) for key, value in entry.items() if key in _PRIVATE_FIELDS}
        if record.get("provider") != "withings":
            raise ValueError("Unsupported ECG provider.")
        if any(not isinstance(record.get(key), str) or not record[key].strip()
               for key in ("id", "recorded_at", "source_file")):
            raise ValueError("ECG summaries need an identifier, timestamp and private source.")
        day = _date(record.get("day"))
        stamp = datetime.fromisoformat(record["recorded_at"])
        if stamp.utcoffset() is None or stamp.date() != day:
            raise ValueError("ECG timestamp must include its timezone and agree with its day.")
        if type(record.get("sample_count")) is not int or record["sample_count"] <= 0:
            raise ValueError("ECG sample counts must be positive integers.")
        for key in ("sampling_frequency_hz", "duration_seconds"):
            value = record.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError("ECG frequency and duration must be positive finite numbers.")
        if not math.isclose(record["duration_seconds"],
                            record["sample_count"] / record["sampling_frequency_hz"], rel_tol=1e-9):
            raise ValueError("ECG duration disagrees with its samples and frequency.")
        for key in _OPTIONAL_PUBLIC_FIELDS:
            if record.get(key) is None:
                record.pop(key, None)
        heart_rate = record.get("heart_rate_bpm")
        if heart_rate is not None and (isinstance(heart_rate, bool) or not isinstance(heart_rate, (int, float))
                                       or not math.isfinite(heart_rate) or heart_rate <= 0):
            raise ValueError("ECG heart rate must be a positive finite number.")
        classification = record.get("af_classification")
        if classification is not None and (not isinstance(classification, str) or classification not in _AF_LABELS):
            raise ValueError("Unsupported provider ECG AF classification.")
        _graph_path(record.get("graph_path"))
        identifier = record["id"]
        if identifier in unique and unique[identifier] != record:
            raise ValueError("Conflicting ECG summaries share an identifier.")
        unique[identifier] = record
    return sorted(unique.values(), key=lambda record: (datetime.fromisoformat(record["recorded_at"]).timestamp(), record["id"]))


def summarize_inventory(inventory, source_file):
    """Copy dated metadata only; the original source already holds the signals."""
    if not isinstance(inventory, list):
        raise ValueError("ECG inventory must be a list.")
    if any(not isinstance(record, dict) for record in inventory):
        raise ValueError("An ECG inventory item must be an object.")
    return _private_entries([{**record, "source_file": source_file} for record in inventory])


def merge_summaries(existing, incoming, start, end, complete=False):
    """Replace complete date windows; partial results amend only their IDs."""
    start, end = _date(start), _date(end)
    if end < start:
        raise ValueError("ECG coverage end must not precede its start.")
    existing, incoming = _private_entries(existing), _private_entries(incoming)
    incoming = [record for record in incoming if start <= _date(record["day"]) <= end]
    replacements = {record["id"] for record in incoming}
    if any(record["id"] in replacements and not start <= _date(record["day"]) <= end
           for record in existing):
        raise ValueError("An ECG amendment cannot move an existing recording from outside its coverage window.")
    retained = [record for record in existing
                if record["id"] not in replacements
                and not (complete and start <= _date(record["day"]) <= end)]
    return _private_entries(retained + incoming)


def public_summaries(privateentries):
    """Return only dated, non-identifying recording metadata, newest first."""
    return [{key: record[key] for key in (*_PUBLIC_FIELDS, *_OPTIONAL_PUBLIC_FIELDS) if key in record}
            for record in reversed(_private_entries(privateentries))]


def _text(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


def _cells(row):
    # Restrict rendering to the public fields even if a caller passes a private
    # record by mistake. Never interpolate an entire record or link its source.
    return (str(row.get("recorded_at", "")).replace("T", " ", 1),
            _text(row["heart_rate_bpm"]) + " bpm" if row.get("heart_rate_bpm") is not None else "—",
            _AF_LABELS.get(row.get("af_classification"), "—"),
            _graph_path(row.get("graph_path")),
            str(row.get("provider", "")).title())


def render_ecg_html(rows):
    if not rows:
        return ""
    heading = f"Recorded ECG traces · {len(rows)} recordings"
    def cells(row):
        recorded_at, heart_rate, result, path, provider = _cells(row)
        link = f'<a href="{escape(path, quote=True)}">View trace</a>' if path else "—"
        return [escape(cell, quote=True) for cell in (recorded_at, heart_rate, result)] + [link, escape(provider, quote=True)]
    body = "\n".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in cells(row)) + "</tr>" for row in rows)
    return (f"<details><summary>{heading}</summary>\n"
            "<div class='table-scroll'><table><thead><tr><th>Date/time</th><th>Heart rate</th>"
            "<th>Result</th><th>ECG</th><th>Source</th></tr></thead>"
            f"<tbody>\n{body}\n</tbody></table></div>\n</details>")


def render_ecg_md(rows):
    if not rows:
        return ""
    def cell_text(cell):
        text = escape(cell, quote=True).replace("|", "&#124;").replace("\r", " ").replace("\n", " ")
        return re.sub(r"([\\`*_\[\]{}])", r"\\\1", text)
    def cells(row):
        recorded_at, heart_rate, result, path, provider = _cells(row)
        link = f"[View trace]({path})" if path else "—"
        return [cell_text(cell) for cell in (recorded_at, heart_rate, result)] + [link, cell_text(provider)]
    body = "\n".join("| " + " | ".join(cells(row)) + " |" for row in rows)
    return (f"<details>\n<summary>Recorded ECG traces · {len(rows)} recordings</summary>\n\n"
            "| Date/time | Heart rate | Result | ECG | Source |\n"
            "| :--- | ---: | :--- | :--- | :--- |\n"
            f"{body}\n\n</details>")
