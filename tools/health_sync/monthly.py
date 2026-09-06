"""Validation and deterministic calendar averages; no network or file writes."""

import calendar
import json
import math
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .oura import OURA_CATEGORICAL_METRICS, OURA_METRICS
from .withings import WITHINGS_CATEGORICAL_METRICS, WITHINGS_METRICS


# The user reopened July on 2026-09-06. Original manual values remain in the
# generator/source history; imported July cells now receive their actual means.
MANAGED_START = date(2026, 7, 1)
METRICS = {"oura": OURA_METRICS, "withings": WITHINGS_METRICS}
CATEGORICAL_METRICS = {"oura": OURA_CATEGORICAL_METRICS, "withings": WITHINGS_CATEGORICAL_METRICS}
if OURA_METRICS.keys() & WITHINGS_METRICS.keys():
    raise ValueError("Provider metric names must be distinct; preserve source identity.")


def iso_date(value):
    if not isinstance(value, str):
        raise ValueError("Dates must use YYYY-MM-DD text.")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Dates must use YYYY-MM-DD.")
    return parsed


def validate_records(records):
    """Reject malformed input and conflicting IDs; exact repeats are harmless."""
    if not isinstance(records, list):
        raise ValueError("Expected a list of measurement records.")
    unique = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each measurement record must be an object.")
        provider = record.get("provider")
        metric = record.get("metric")
        if provider not in METRICS or metric not in METRICS[provider]:
            raise ValueError(f"Unsupported provider or metric: {provider}/{metric}")
        if not isinstance(record.get("id"), str) or not record["id"]:
            raise ValueError("A measurement needs a stable ID.")
        iso_date(record["day"])
        if record.get("unit") != METRICS[provider][metric][0]:
            raise ValueError(f"Unexpected unit for {metric}.")
        value = record.get("value")
        numbers = value if metric == "Blood Pressure" else [value]
        if not isinstance(numbers, list) or len(numbers) != (2 if metric == "Blood Pressure" else 1):
            raise ValueError("Blood pressure requires a same-reading systolic/diastolic pair.")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in numbers):
            raise ValueError(f"Non-finite or nonnumeric measurement: {metric}.")
        if record.get("source_kind") not in {"api", "csv"}:
            raise ValueError("Expected an API or CSV source.")
        if type(record.get("source_count", 1)) is not int or record.get("source_count", 1) < 1:
            raise ValueError("A combined observation needs a positive source reading count.")
        key = (provider, record["id"], metric)
        if key in unique and unique[key] != record:
            raise ValueError(f"Conflicting duplicate measurement ID for {metric}.")
        unique[key] = record
    return sorted(unique.values(), key=lambda r: (r["day"], r["provider"], r["metric"], r["id"]))


def merge_records(existing, incoming, providers, start, end):
    """Replace each fetched provider's requested range, retaining other history."""
    if start < MANAGED_START or end < start:
        raise ValueError("The managed range begins 2026-07-01; earlier history is retained.")
    existing, incoming = validate_records(existing), validate_records(incoming)
    incoming = [r for r in incoming if start <= iso_date(r["day"]) <= end]
    if any(r["provider"] not in providers for r in incoming):
        raise ValueError("Incoming records contain a provider outside this import.")
    for provider in providers:
        if not any(r["provider"] == provider for r in incoming):
            raise ValueError(f"No usable {provider} readings in the requested range; existing results were preserved.")
    retained = [r for r in existing if not (r["provider"] in providers and start <= iso_date(r["day"]) <= end)]
    return validate_records(retained + incoming)


def _withings_sleep_cell(record):
    if record["provider"] == "withings" and (
        record["id"].startswith("withings:sleep:")
        or record.get("source_endpoint") in ("sleep", "getsummary")
    ):
        return record["day"], record["metric"]
    return None


def _sleep_record_ids(record):
    """Recover contributing session IDs, including the previous per-session cache."""
    if "source_record_ids" in record:
        values = record["source_record_ids"]
        if (isinstance(values, list) and values
                and all(isinstance(value, str) and value.strip() for value in values)
                and len(set(values)) == len(values)
                and record.get("source_count", len(values)) == len(values)):
            return set(values)
        return None
    parts = record["id"].split(":", 3)
    if (len(parts) == 4 and parts[:2] == ["withings", "sleep"]
            and parts[2] and not parts[2].startswith("daily-")
            and parts[3] == record["metric"] and record.get("source_count", 1) == 1):
        return {parts[2]}
    return None


def _check_sleep_file_coverage(existing, incoming):
    """A partial file cannot safely recompute a day without every prior session."""
    cells = {}
    previous_cells = defaultdict(list)
    for record in existing:
        if record["provider"] == "withings":
            previous_cells[(record["day"], record["metric"])].append(record)
    for record in incoming:
        cell = _withings_sleep_cell(record)
        if cell is not None:
            cells.setdefault(cell, []).append(record)
    for (day, metric), replacements in cells.items():
        message = (
            f"The Withings sleep file cannot replace all known sessions for {day} / {metric}. "
            "Run a full API sync for this date range; existing results were preserved."
        )
        # Coalesced daily values cannot be combined by averaging another daily
        # value, and their component durations/weights are no longer recoverable.
        if len(replacements) != 1:
            raise ValueError(message)
        source_ids = _sleep_record_ids(replacements[0])
        if source_ids is None:
            raise ValueError(message)
        for previous in previous_cells[(day, metric)]:
            previous_ids = _sleep_record_ids(previous)
            if previous_ids is None or not previous_ids <= source_ids:
                raise ValueError(message)
    return set(cells)


def merge_file_records(existing, incoming, providers, start, end, *, partial_api=False):
    """Amend represented observations without erasing unrepresented history.

    A partial API fetch may contain multiple observations for one Oura day and
    metric; they replace that cell's previous observation set together. CSV
    exports still require a single daily value and never mix with API versions.
    A Withings daily sleep value must cover every previously known contributing
    session before replacing that day; incomplete files require a full API sync.
    """
    # Reuse range/provider/input checks without treating a file as a full fetch.
    incoming = merge_records([], incoming, providers, start, end)
    existing = validate_records(existing)
    sleep_cells = _check_sleep_file_coverage(existing, incoming)

    def key(record):
        if record["provider"] == "withings" and (record["day"], record["metric"]) in sleep_cells:
            identity = ("sleep-day", record["day"])
        else:
            identity = record["day"] if record["provider"] == "oura" else record["id"]
        return record["provider"], identity, record["metric"]

    replacements = {key(record) for record in incoming}
    if partial_api and any(record["source_kind"] != "api" for record in incoming):
        raise ValueError("Partial API merging requires only API observations.")
    if len(replacements) != len(incoming) and not partial_api:
        raise ValueError("Competing daily Oura values in one import.")
    return validate_records([r for r in existing if key(r) not in replacements] + incoming)


def _mean(values):
    return sum((Decimal(str(v)) for v in values), Decimal(0)) / len(values)


def _rounded(value, places):
    return format(value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP), f".{places}f")


def aggregate(records, as_of):
    buckets = defaultdict(lambda: defaultdict(list))
    for record in validate_records(records):
        day = iso_date(record["day"])
        if MANAGED_START <= day <= as_of and not (record["provider"] == "oura" and day == as_of):
            buckets[(day.strftime("%Y-%m"), record["provider"], record["metric"])][record["day"]].append(record)
    months = {}
    for (month, provider, metric), days in sorted(buckets.items()):
        unit, places = METRICS[provider][metric]
        components = 2 if metric == "Blood Pressure" else 1
        averages = []
        for component in range(components):
            daily = [_mean([r["value"][component] if components == 2 else r["value"] for r in readings]) for readings in days.values()]
            averages.append(_rounded(_mean(daily), places))
        first = iso_date(month + "-01")
        calendar_days = calendar.monthrange(first.year, first.month)[1]
        elapsed_days = min((as_of - first).days + 1, calendar_days)
        entry = {
            "value": "/".join(averages), "unit": unit, "provider": provider,
            "n_days": len(days), "n_records": sum(r.get("source_count", 1) for readings in days.values() for r in readings),
            "first_day": min(days), "last_day": max(days),
            "calendar_days": calendar_days, "elapsed_days": elapsed_days,
            "partial_month": (first.year, first.month) == (as_of.year, as_of.month),
            "aggregation": "mean_of_daily_means",
            "source_kinds": sorted({r["source_kind"] for readings in days.values() for r in readings}),
        }
        daily_methods = sorted({r["daily_aggregation"] for readings in days.values() for r in readings
                                if r.get("daily_aggregation")})
        if daily_methods:
            entry["daily_aggregation"] = daily_methods
        months.setdefault(month, {})[metric] = entry
    return {"schema_version": 1, "as_of": as_of.isoformat(), "months": months}


def load_monthly(path):
    path = Path(path)
    if not path.exists():
        return {"schema_version": 1, "months": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(payload.get("months"), dict):
        raise ValueError("Unsupported monthly-vitals file; run tools/sync_vitals.py to rebuild it.")
    as_of = iso_date(payload["as_of"])
    for month, metrics in payload["months"].items():
        first = iso_date(month + "-01")
        if first < MANAGED_START or first > as_of or not isinstance(metrics, dict):
            raise ValueError("Invalid monthly-vitals date range.")
        for metric, entry in metrics.items():
            provider = entry["provider"]
            if provider not in METRICS or metric not in METRICS[provider]:
                raise ValueError("Unknown monthly-vitals metric.")
            if entry["unit"] != METRICS[provider][metric][0] or entry["aggregation"] != "mean_of_daily_means":
                raise ValueError("Unexpected monthly-vitals unit or aggregation.")
            values = entry["value"].split("/")
            try:
                finite = all(Decimal(v).is_finite() for v in values)
            except ArithmeticError as error:
                raise ValueError("Invalid monthly-vitals numeric text.") from error
            if len(values) != (2 if metric == "Blood Pressure" else 1) or not finite:
                raise ValueError("Invalid monthly-vitals value.")
            if not 0 < entry["n_days"] <= entry["elapsed_days"] <= entry["calendar_days"] <= 31:
                raise ValueError("Invalid monthly-vitals coverage.")
            expected_days = calendar.monthrange(first.year, first.month)[1]
            if entry["calendar_days"] != expected_days or entry["elapsed_days"] != min((as_of - first).days + 1, expected_days):
                raise ValueError("Monthly-vitals calendar coverage does not match the date.")
            if entry.get("partial_month") != ((first.year, first.month) == (as_of.year, as_of.month)):
                raise ValueError("Invalid partial-month flag.")
            if not isinstance(entry.get("n_records"), int) or entry["n_records"] < entry["n_days"]:
                raise ValueError("Invalid monthly-vitals reading count.")
            if not first <= iso_date(entry["first_day"]) <= iso_date(entry["last_day"]) <= as_of or entry["last_day"][:7] != month:
                raise ValueError("Invalid monthly-vitals observation dates.")
    categorical_months = payload.get("categorical_months", {})
    if not isinstance(categorical_months, dict):
        raise ValueError("Monthly device classifications must be an object.")
    for month, metrics in categorical_months.items():
        first = iso_date(month + "-01")
        if first < MANAGED_START or first > as_of or not isinstance(metrics, dict):
            raise ValueError("Invalid monthly-classification date range.")
        for metric, entry in metrics.items():
            if not isinstance(entry, dict):
                raise ValueError("Monthly classifications require structured entries.")
            provider = entry.get("provider")
            if provider not in CATEGORICAL_METRICS or metric not in CATEGORICAL_METRICS[provider]:
                raise ValueError("Unknown monthly device classification.")
            if any(metric in registry for registry in METRICS.values()):
                raise ValueError("A classification cannot replace a numeric metric.")
            if entry.get("unit") != "Status" or entry.get("aggregation") != "observed_classification_counts":
                raise ValueError("Device classifications must use observed counts, not averages.")
            counts = entry.get("counts")
            if not isinstance(counts, dict) or not counts or any(
                not isinstance(label, str) or not label.strip() or any(ord(char) < 32 for char in label)
                or type(count) is not int or count <= 0 for label, count in counts.items()
            ):
                raise ValueError("Invalid device classification counts.")
            expected = "; ".join(f"{label}: {count}" for label, count in sorted(counts.items()))
            if entry.get("value") != expected or type(entry.get("n_records")) is not int or entry["n_records"] != sum(counts.values()):
                raise ValueError("Device classification display and counts do not agree.")
            first_day, last_day = iso_date(entry["first_day"]), iso_date(entry["last_day"])
            if not first <= first_day <= last_day <= as_of or last_day.strftime("%Y-%m") != month:
                raise ValueError("Invalid monthly-classification observation dates.")
            if (type(entry.get("n_days")) is not int
                    or not 0 < entry["n_days"] <= min(entry["n_records"], (last_day - first_day).days + 1)):
                raise ValueError("Invalid monthly-classification coverage.")
    return payload


def report_note(payload):
    """One report footnote for imported cells, with coverage grouped by source."""
    markers, groups = [], defaultdict(list)
    for month, metrics in sorted(payload["months"].items()):
        for metric, entry in metrics.items():
            markers.append({"row": metric, "target": "value", "dates": [month]})
            groups[(month, entry["provider"], entry["elapsed_days"], entry["partial_month"])].append(entry["n_days"])
    coverage = []
    for (month, provider, elapsed, partial), counts in groups.items():
        n = str(min(counts)) if min(counts) == max(counts) else f"{min(counts)}-{max(counts)}"
        coverage.append(f"{month} {provider.title()}: {n}/{elapsed} elapsed days" + (" (month to date)" if partial else ""))
    return {
        "text": "Imported monthly means from July 2026 onward: each observed day has equal weight. Repeated ordinary measurements are averaged within the day first. Withings split-night sleep sessions are combined per day: durations and counts sum; heart rate, respiratory rate and AHI use sleep-duration weights; daily minima/maxima retain their extrema; efficiency uses combined sleep/time in bed. Scores, latencies and start/end HRV remain means of reported sessions, with HRV describing observed session-start/session-end windows. Provider-specific rows retain their distinct definitions. Missing days are excluded; current-day Oura data are deferred until tomorrow. "
        + "; ".join(coverage)
        + ". Classifications are not averaged as numeric codes. API and CSV Oura HR values can differ because the provider uses different sampling methods. Per-metric counts and dates: <a href='results/vitals_monthly.json'>monthly source data</a>. Sync: <a href='tools/README.md'>on-demand instructions</a>.",
        "markers": markers,
    }


def apply_report_overlay(followups, notes, payload):
    """Replace only imported cells and their old snapshot-specific footnotes."""
    numeric = {(month, metric) for month, metrics in payload["months"].items() for metric in metrics}
    categorical = {(month, metric) for month, metrics in payload.get("categorical_months", {}).items() for metric in metrics}
    automated = numeric | categorical
    for collection in (payload["months"], payload.get("categorical_months", {})):
        for month, metrics in collection.items():
            followups.setdefault(month, {}).update({metric: entry["value"] for metric, entry in metrics.items()})
    if not automated:
        return
    filtered_notes = []
    for note in notes:
        if not note["markers"]:
            filtered_notes.append(note)
            continue
        remaining = []
        for marker in note["markers"]:
            if marker.get("target") != "value" or not marker.get("dates"):
                remaining.append(marker)
                continue
            for metric in marker.get("rows", [marker.get("row")]):
                dates = [d for d in marker["dates"] if (d, metric) not in automated]
                if dates:
                    remaining.append({"row": metric, "target": "value", "dates": dates})
        if remaining:
            filtered_notes.append({**note, "markers": remaining})
    notes[:] = filtered_notes + ([report_note(payload)] if numeric else [])
    if categorical:
        notes.append({
            "text": "Imported device classifications show counts of observed labels within each calendar month; they are not numeric averages, clinical diagnoses or estimates for unrecorded days. Entries labeled Device code preserve API values with unverified meanings and may include unavailable-result codes; they are not interpreted as clinical findings. Different provider classifications retain separate rows. Coverage and exact counts: <a href='results/vitals_monthly.json'>monthly source data</a>.",
            "markers": [{"row": metric, "target": "value", "dates": [month]} for month, metric in sorted(categorical)],
        })
