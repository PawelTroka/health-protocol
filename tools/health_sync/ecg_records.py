"""Private ECG metadata reconciliation and a waveform-free public index."""

from copy import deepcopy
from datetime import date, datetime
from html import escape
import math


_PRIVATE_FIELDS = {
    "provider", "id", "signalid", "day", "recorded_at", "kind", "source_kind",
    "amplitude_unit", "sampling_frequency_hz", "sample_count", "duration_seconds",
    "model", "wearposition", "source_file",
}
_PUBLIC_FIELDS = ("recorded_at", "provider", "sample_count", "duration_seconds", "sampling_frequency_hz")
_CAPTION = "Waveforms are retained in the private sync archive."


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
    return [{key: record[key] for key in _PUBLIC_FIELDS}
            for record in reversed(_private_entries(privateentries))]


def _text(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


def _cells(row):
    # Restrict rendering to the public fields even if a caller passes a private
    # record by mistake. Never interpolate an entire record or link its source.
    return (str(row.get("recorded_at", "")).replace("T", " ", 1),
            _text(row.get("duration_seconds", "")),
            _text(row.get("sampling_frequency_hz", "")),
            str(row.get("provider", "")).title())


def render_ecg_html(rows):
    if not rows:
        return ""
    heading = f"Recorded ECG traces · {len(rows)} recordings"
    body = "\n".join("<tr>" + "".join(f"<td>{escape(cell, quote=True)}</td>" for cell in _cells(row)) + "</tr>"
                     for row in rows)
    return (f"<details><summary>{heading}</summary>\n<p>{_CAPTION}</p>\n"
            "<div class='table-scroll'><table><thead><tr><th>Date/time</th><th>Duration (s)</th>"
            "<th>Sampling frequency (Hz)</th><th>Source</th></tr></thead>"
            f"<tbody>\n{body}\n</tbody></table></div>\n</details>")


def render_ecg_md(rows):
    if not rows:
        return ""
    def cell_text(cell):
        return escape(cell, quote=True).replace("|", "&#124;").replace("\r", " ").replace("\n", " ")
    body = "\n".join("| " + " | ".join(cell_text(cell) for cell in _cells(row)) + " |" for row in rows)
    return (f"<details>\n<summary>Recorded ECG traces · {len(rows)} recordings</summary>\n\n"
            f"{_CAPTION}\n\n"
            "| Date/time | Duration (s) | Sampling frequency (Hz) | Source |\n"
            "| :--- | ---: | ---: | :--- |\n"
            f"{body}\n\n</details>")
