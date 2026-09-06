"""Validation and deterministic calendar averages; no network or file writes."""

import calendar
import json
import math
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


MANAGED_START = date(2026, 8, 1)  # July is the explicitly preserved baseline.
METRICS = {
    "oura": {
        "Average Sleeping HR (Oura)": ("bpm", 1),
        "Mean Nightly Lowest HR (Oura)": ("bpm", 1),
        "Average HRV (Sleep)": ("ms", 1),
        "Respiratory Rate (Sleep)": ("/min", 1),
        "Sleep Duration": ("h", 2),
        "Time in Bed": ("h", 2),
        "Sleep Efficiency": ("%", 1),
        "Sleep Latency": ("min", 1),
        "Sleep Score": ("score", 1),
        "REM Sleep": ("h", 2),
        "Deep Sleep": ("h", 2),
    },
    "withings": {
        "Body Mass": ("kg", 1), "BMI": ("kg/m^2", 1),
        "Body Fat": ("%", 1), "Muscle": ("%", 1),
        "Bone": ("%", 1), "Visceral Fat Index": ("index", 1),
        "Blood Pressure": ("mmHg", 1), "PWV": ("m/s", 1),
        "Temperature": ("C", 1),
    },
}


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
        key = (provider, record["id"], metric)
        if key in unique and unique[key] != record:
            raise ValueError(f"Conflicting duplicate measurement ID for {metric}.")
        unique[key] = record
    return sorted(unique.values(), key=lambda r: (r["day"], r["provider"], r["metric"], r["id"]))


def merge_records(existing, incoming, providers, start, end):
    """Replace each fetched provider's requested range, retaining other history."""
    if start < MANAGED_START or end < start:
        raise ValueError("The managed range begins 2026-08-01; July's baseline is protected.")
    existing, incoming = validate_records(existing), validate_records(incoming)
    incoming = [r for r in incoming if start <= iso_date(r["day"]) <= end]
    if any(r["provider"] not in providers for r in incoming):
        raise ValueError("Incoming records contain a provider outside this import.")
    for provider in providers:
        if not any(r["provider"] == provider for r in incoming):
            raise ValueError(f"No usable {provider} readings in the requested range; existing results were preserved.")
    retained = [r for r in existing if not (r["provider"] in providers and start <= iso_date(r["day"]) <= end)]
    return validate_records(retained + incoming)


def merge_file_records(existing, incoming, providers, start, end):
    """Files amend represented observations; a partial export cannot erase history."""
    # Reuse range/provider/input checks without treating a file as a full fetch.
    incoming = merge_records([], incoming, providers, start, end)
    existing = validate_records(existing)

    def key(record):
        identity = record["day"] if record["provider"] == "oura" else record["id"]
        return record["provider"], identity, record["metric"]

    replacements = {key(record) for record in incoming}
    if len(replacements) != len(incoming):
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
            "n_days": len(days), "n_records": sum(map(len, days.values())),
            "first_day": min(days), "last_day": max(days),
            "calendar_days": calendar_days, "elapsed_days": elapsed_days,
            "partial_month": (first.year, first.month) == (as_of.year, as_of.month),
            "aggregation": "mean_of_daily_means",
            "source_kinds": sorted({r["source_kind"] for readings in days.values() for r in readings}),
        }
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
        "text": "Imported monthly means: each observed day has equal weight; repeated Withings readings are averaged within the day first. Missing days are excluded; current-day Oura data are deferred until tomorrow. "
        + "; ".join(coverage)
        + ". API and CSV Oura HR values can differ because the provider uses different sampling methods. Per-metric counts and dates: <a href='results/vitals_monthly.json'>monthly source data</a>. Sync: <a href='tools/README.md'>on-demand instructions</a>.",
        "markers": markers,
    }


def apply_report_overlay(followups, notes, payload):
    """Replace only imported cells and their old snapshot-specific footnotes."""
    automated = {(month, metric) for month, metrics in payload["months"].items() for metric in metrics}
    for month, metrics in payload["months"].items():
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
    notes[:] = filtered_notes + [report_note(payload)]
