"""Pure Oura CSV and API v2 parsers for the report's eleven sleep metrics.

Official schema, checked 2026-09-06:
https://cloud.ouraring.com/v2/static/json/openapi-1.37.json
https://cloud.ouraring.com/v2/docs

CSV rows are Oura's exported daily observations. API observations use the longest
completed ``long_sleep`` period assigned to each Oura ``day``; naps and rests are
excluded. The daily sleep score can include other contributing sleep periods and
comes from ``daily_sleep.score``. This deliberate primary-night policy need not
reproduce every CSV aggregate. In addition, the API documents that its mean and
lowest HR use 30-second samples, whereas the app uses aggregated 5-minute samples.
Keep source_kind when storing/aggregating records; do not silently mix CSV and API
versions of the same day's metric. Date-window and current-day exclusion belong
to the caller, so these parsers remain deterministic and independent of the clock.

Values are converted to report units without rounding. Null/blank measurements
are omitted, never replaced with zero. Structural validation is not a clinical
reference-range assessment. Neither parser performs network requests or writes.
"""

from __future__ import annotations

import csv
import math
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


OURA_ENDPOINTS = ["sleep", "daily_sleep"]

# (report marker, CSV header after trimming, API field, report unit, divisor)
_METRICS = (
    ("Sleep Duration", "Total Sleep Duration", "total_sleep_duration", "h", 3600),
    ("REM Sleep", "REM Sleep Duration", "rem_sleep_duration", "h", 3600),
    ("Deep Sleep", "Deep Sleep Duration", "deep_sleep_duration", "h", 3600),
    ("Average Sleeping HR (Oura)", "Average Resting Heart Rate", "average_heart_rate", "bpm", 1),
    ("Mean Nightly Lowest HR (Oura)", "Lowest Resting Heart Rate", "lowest_heart_rate", "bpm", 1),
    ("Average HRV (Sleep)", "Average HRV", "average_hrv", "ms", 1),
    ("Respiratory Rate (Sleep)", "Respiratory Rate", "average_breath", "/min", 1),
    ("Sleep Efficiency", "Sleep Efficiency", "efficiency", "%", 1),
    ("Sleep Latency", "Sleep Latency", "latency", "min", 60),
    ("Sleep Score", "Sleep Score", "score", "score", 1),
    ("Time in Bed", "Total Bedtime", "time_in_bed", "h", 3600),
)
_DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_POSITIVE_FIELDS = {"average_heart_rate", "lowest_heart_rate", "average_breath"}
_OTHER_SLEEP_TYPES = {"deleted", "sleep", "late_nap", "rest", None}


class OuraParseError(ValueError):
    """The supplied Oura data cannot be safely interpreted."""


def _day(value: Any, context: str) -> str:
    if not isinstance(value, str) or not _DAY_RE.fullmatch(value):
        raise OuraParseError(f"{context}: expected a YYYY-MM-DD day")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise OuraParseError(f"{context}: invalid calendar day") from exc
    return value


def _number(value: Any, field: str, context: str, *, csv_text: bool = False) -> float | None:
    if value is None or (csv_text and isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise OuraParseError(f"{context}: {field} must be numeric or missing")
    if isinstance(value, str) and not csv_text:
        raise OuraParseError(f"{context}: {field} must be a JSON number or null")
    try:
        result = float(value)
    except (ValueError, OverflowError) as exc:
        raise OuraParseError(f"{context}: {field} is not a finite number") from exc
    if not math.isfinite(result) or result < 0:
        raise OuraParseError(f"{context}: {field} must be finite and nonnegative")
    if field in _POSITIVE_FIELDS and result == 0:
        raise OuraParseError(f"{context}: {field} must be positive when supplied")
    if field in {"efficiency", "score"} and result > 100:
        raise OuraParseError(f"{context}: {field} must be within 0-100")
    return result


def _timestamp(value: Any, context: str) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or "T" not in value:
        raise OuraParseError(f"{context}: expected an ISO timestamp with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OuraParseError(f"{context}: invalid ISO timestamp") from exc
    if parsed.utcoffset() is None:
        raise OuraParseError(f"{context}: timestamp requires a timezone")
    return parsed.isoformat()


def _sleep_consistency(values: dict, context: str) -> None:
    total = values.get("total_sleep_duration")
    bedtime = values.get("time_in_bed")
    if total is None:
        return
    if bedtime is not None and total > bedtime + 1:
        raise OuraParseError(f"{context}: sleep duration exceeds time in bed")
    stages = [values.get(key) for key in (
        "light_sleep_duration", "deep_sleep_duration", "rem_sleep_duration"
    )]
    if any(value is not None and value > total + 1 for value in stages):
        raise OuraParseError(f"{context}: a sleep stage exceeds total sleep")
    if all(value is not None for value in stages) and not math.isclose(
        sum(stages), total, rel_tol=0, abs_tol=1
    ):
        raise OuraParseError(f"{context}: sleep stages do not sum to total sleep")


def _record(day: str, source_kind: str, source_id: str, marker: str,
            value: float, unit: str, recorded_at: str | None) -> dict:
    record = {
        "provider": "oura",
        "id": f"oura:{source_kind}:{source_id}:{marker}",
        "day": day,
        "metric": marker,
        "value": value,
        "unit": unit,
        "source_kind": source_kind,
    }
    if recorded_at is not None:
        record["recorded_at"] = recorded_at
    return record


def _sort(records: list[dict]) -> list[dict]:
    return sorted(records, key=lambda record: (record["day"], record["metric"], record["id"]))


def parse_csv(path: str | Path) -> list[dict]:
    """Read an Oura trends CSV, preserving each exported daily measurement.

    ``date`` and ``Total Sleep Duration`` headers are required. Other supported
    metric columns may be absent in a partial export. Identical daily observations
    are deduplicated; conflicting duplicate dates raise instead of weighting a
    day twice. Rows without positive total sleep are incomplete and excluded.
    """
    observations: dict[str, list[dict]] = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            headers = [value.strip() for value in next(reader)]
        except StopIteration as exc:
            raise OuraParseError("Oura CSV is empty") from exc
        except csv.Error as exc:
            raise OuraParseError("Oura CSV header is malformed") from exc
        if len(headers) != len(set(headers)) or any(not header for header in headers):
            raise OuraParseError("Oura CSV has duplicate or blank headers")
        if not {"date", "Total Sleep Duration"}.issubset(headers):
            raise OuraParseError("Oura CSV requires date and Total Sleep Duration headers")
        try:
            for cells in reader:
                if not any(cell.strip() for cell in cells):
                    continue
                context = f"Oura CSV row {reader.line_num}"
                if len(cells) != len(headers):
                    raise OuraParseError(f"{context}: column count does not match header")
                row = dict(zip(headers, (cell.strip() for cell in cells)))
                day = _day(row["date"], context)
                values = {
                    api_field: _number(row.get(csv_field), api_field, context, csv_text=True)
                    for _, csv_field, api_field, _, _ in _METRICS
                }
                values["light_sleep_duration"] = _number(
                    row.get("Light Sleep Duration"), "light_sleep_duration", context, csv_text=True
                )
                _sleep_consistency(values, context)
                if not values["total_sleep_duration"]:
                    continue
                recorded_at = _timestamp(row.get("Bedtime End"), context)
                records = [
                    _record(day, "csv", day, marker, values[field] / divisor, unit, recorded_at)
                    for marker, _, field, unit, divisor in _METRICS
                    if values[field] is not None
                ]
                if day in observations and observations[day] != records:
                    raise OuraParseError(f"{context}: conflicting duplicate daily observation")
                observations[day] = records
        except csv.Error as exc:
            raise OuraParseError(f"Oura CSV row {reader.line_num} is malformed") from exc
    return _sort([record for records in observations.values() for record in records])


def _documents(payloads: dict, endpoint: str) -> list[dict]:
    documents = payloads.get(endpoint, [])
    if not isinstance(documents, list):
        raise OuraParseError(f"Oura {endpoint}: expected a list of documents")
    unique: dict[str, dict] = {}
    for document in documents:
        if not isinstance(document, dict):
            raise OuraParseError(f"Oura {endpoint}: expected document objects")
        identifier = document.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise OuraParseError(f"Oura {endpoint}: document requires a nonempty id")
        _day(document.get("day"), f"Oura {endpoint} document")
        if identifier in unique and unique[identifier] != document:
            raise OuraParseError(f"Oura {endpoint}: conflicting duplicate document id")
        unique[identifier] = document
    return list(unique.values())


def parse_api(payloads: dict[str, list[dict]]) -> list[dict]:
    """Normalize already-fetched API ``sleep`` and ``daily_sleep`` documents.

    Pick the completed long_sleep with greatest total_sleep_duration for each
    Oura day, breaking ties by latest bedtime_end and then lexicographic id.
    Missing total sleep, time in bed, or either bedtime endpoint means incomplete.
    Optional null measures remain absent. Missing daily score is never obtained
    from the contributors or readiness score. A daily score is emitted only for a
    day with a selected completed night; same-day daily-score documents use latest
    timestamp, then id. Conflicting versions of one id raise; fetch current versions
    before calling rather than combining stale and current payloads.
    """
    if not isinstance(payloads, dict):
        raise OuraParseError("Oura API payloads must be a dictionary of endpoint lists")
    primary: dict[str, tuple[tuple, dict, dict, str]] = {}
    for document in _documents(payloads, "sleep"):
        kind = document.get("type")
        if kind is not None and not isinstance(kind, str):
            raise OuraParseError("Oura sleep: sleep-period type must be text or null")
        if kind in _OTHER_SLEEP_TYPES:
            continue
        if kind != "long_sleep":
            raise OuraParseError("Oura sleep: unknown sleep-period type")
        context = "Oura long_sleep document"
        day = document["day"]
        values = {
            field: _number(document.get(field), field, context)
            for _, _, field, _, _ in _METRICS if field != "score"
        }
        values["light_sleep_duration"] = _number(
            document.get("light_sleep_duration"), "light_sleep_duration", context
        )
        start = _timestamp(document.get("bedtime_start"), context)
        end = _timestamp(document.get("bedtime_end"), context)
        _sleep_consistency(values, context)
        if not values["total_sleep_duration"] or not values["time_in_bed"] or not start or not end:
            continue
        start_time = datetime.fromisoformat(start)
        end_time = datetime.fromisoformat(end)
        if end_time <= start_time:
            raise OuraParseError("Oura long_sleep: bedtime end must follow bedtime start")
        rank = (values["total_sleep_duration"], end_time.astimezone(timezone.utc), document["id"])
        if day not in primary or rank > primary[day][0]:
            primary[day] = (rank, document, values, end)

    records: list[dict] = []
    for day, (_, document, values, end) in primary.items():
        for marker, _, field, unit, divisor in _METRICS:
            if field != "score" and values[field] is not None:
                records.append(_record(
                    day, "api", f"sleep:{document['id']}", marker,
                    values[field] / divisor, unit, end
                ))

    daily_scores: dict[str, tuple[tuple, dict]] = {}
    for document in _documents(payloads, "daily_sleep"):
        day = document["day"]
        score = _number(document.get("score"), "score", "Oura daily_sleep document")
        stamp = _timestamp(document.get("timestamp"), "Oura daily_sleep document")
        if day not in primary or score is None:
            continue
        rank = (
            datetime.fromisoformat(stamp).astimezone(timezone.utc) if stamp else
            datetime.min.replace(tzinfo=timezone.utc), document["id"]
        )
        record = _record(day, "api", f"daily_sleep:{document['id']}",
                         "Sleep Score", score, "score", stamp)
        if day not in daily_scores or rank > daily_scores[day][0]:
            daily_scores[day] = (rank, record)
    records.extend(record for _, record in daily_scores.values())
    return _sort(records)
