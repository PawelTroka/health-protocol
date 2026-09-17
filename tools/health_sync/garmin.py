"""Pure Garmin Connect daily-summary parsers; no authentication or network I/O.

Field names and source units were checked against python-garminconnect 0.3.15
``garminconnect/typed.py`` and its tests on 2026-09-17:
https://github.com/cyberjunky/python-garminconnect/blob/v0.3.15/garminconnect/typed.py

The fetcher wraps each actual response in ``{"day": requested_day, "data": raw}``.
Source calendar dates, when supplied, must match that requested day. Measurements
remain Garmin-specific; they are not interchangeable with Oura/Withings values.
Missing/null/negative sentinels are omitted. Valid zero activity/stress values
are retained on observed days, but an entirely zero summary is not evidence of a
day's wear. HR, HRV, respiration and SpO2 require positive values. No categorical
codes are averaged. The caller handles date windows and partial current days.

Only AFTER_WAKEUP_RESET training-readiness snapshots enter morning summaries.
Multiple morning snapshots use the latest timestamp; an ambiguous set fails
rather than arbitrarily taking a reading. Recovery time is supplied in minutes;
REACHED_ZERO explicitly overrides Garmin's stale remaining-time number to zero.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


GARMIN_ENDPOINTS = ["daily_summary", "sleep", "hrv", "training_readiness"]
GARMIN_CATEGORICAL_METRICS = {"HRV Status (Garmin)"}
_DAY_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


class GarminParseError(ValueError):
    """The supplied Garmin data cannot be safely interpreted."""


@dataclass(frozen=True)
class _Field:
    path: str
    marker: str
    unit: str
    divisor: float = 1
    decimals: int = 1
    positive: bool = False
    maximum: float | None = None


def _field(path, marker, unit, divisor=1, decimals=1, positive=False, maximum=None):
    return _Field(path, f"{marker} (Garmin)", unit, divisor, decimals, positive, maximum)


_FIELDS = {
    "daily_summary": (
        _field("totalSteps", "Steps", "steps", decimals=0),
        _field("totalDistanceMeters", "Distance", "km", 1000, 2),
        _field("totalKilocalories", "Total Energy Expenditure", "kcal"),
        _field("activeKilocalories", "Active Energy", "kcal"),
        _field("bmrKilocalories", "Basal Energy Expenditure", "kcal"),
        _field("restingHeartRate", "Resting HR", "bpm", positive=True),
        _field("minHeartRate", "Daily Minimum HR", "bpm", positive=True),
        _field("maxHeartRate", "Daily Maximum HR", "bpm", positive=True),
        _field("moderateIntensityMinutes", "Moderate Intensity Minutes", "min"),
        _field("vigorousIntensityMinutes", "Vigorous Intensity Minutes", "min"),
        _field("floorsAscended", "Floors Ascended", "floors", decimals=0),
        _field("floorsDescended", "Floors Descended", "floors", decimals=0),
        _field("averageStressLevel", "Average Stress", "score", maximum=100),
        _field("maxStressLevel", "Maximum Stress", "score", maximum=100),
        _field("bodyBatteryHighestValue", "Body Battery Highest", "score", maximum=100),
        _field("bodyBatteryLowestValue", "Body Battery Lowest", "score", maximum=100),
        _field("bodyBatteryChargedValue", "Body Battery Charged", "points"),
        _field("bodyBatteryDrainedValue", "Body Battery Drained", "points"),
    ),
    "sleep": (
        _field("sleepTimeSeconds", "Sleep Duration", "h", 3600, 2),
        _field("deepSleepSeconds", "Deep Sleep", "h", 3600, 2),
        _field("lightSleepSeconds", "Light Sleep", "h", 3600, 2),
        _field("remSleepSeconds", "REM Sleep", "h", 3600, 2),
        _field("awakeSleepSeconds", "Awake Time During Sleep", "h", 3600, 2),
        _field("napTimeSeconds", "Nap Duration", "h", 3600, 2),
        _field("sleepScores.overall.value", "Sleep Score", "score", maximum=100),
        _field("avgSpO2", "Average Sleeping SpO2", "%", positive=True, maximum=100),
        _field("averageRespirationValue", "Respiratory Rate (Sleep)", "/min",
               decimals=2, positive=True),
    ),
    "hrv": (
        _field("lastNightAvg", "Average Nightly HRV", "ms", positive=True),
        _field("lastNight5MinHigh", "Highest 5-minute Nightly HRV", "ms", positive=True),
        _field("weeklyAvg", "7-day Average HRV", "ms", positive=True),
    ),
    "training_readiness": (
        _field("score", "Morning Training Readiness", "score", positive=True, maximum=100),
        _field("recoveryTime", "Morning Recovery Time", "h", 60, 2),
    ),
}
GARMIN_METRICS = {
    field.marker: (field.unit, field.decimals)
    for fields in _FIELDS.values() for field in fields
}


def _day(value: Any, context: str) -> str:
    if not isinstance(value, str) or not _DAY_RE.fullmatch(value):
        raise GarminParseError(f"{context}: expected a YYYY-MM-DD day")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise GarminParseError(f"{context}: invalid calendar day") from exc
    return value


def _calendar_date(document: dict, requested: str, context: str) -> None:
    source = document.get("calendarDate")
    if source is not None and _day(source, context) != requested:
        raise GarminParseError(f"{context}: calendarDate does not match requested day")


def _object(value: Any, context: str) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise GarminParseError(f"{context}: expected an object or null")
    return value


def _documents(payload: dict, endpoint: str):
    documents = payload.get(endpoint, [])
    if not isinstance(documents, list):
        raise GarminParseError(f"Garmin {endpoint}: expected a list of daily envelopes")
    unique = {}
    for envelope in documents:
        context = f"Garmin {endpoint} envelope"
        if not isinstance(envelope, dict) or "data" not in envelope:
            raise GarminParseError(f"{context}: expected an object with day and data")
        day = _day(envelope.get("day"), context)
        if day in unique and unique[day] != envelope:
            raise GarminParseError(f"{context}: conflicting duplicate requested day")
        unique[day] = envelope
    for day in sorted(unique):
        yield day, unique[day]["data"]


def _path(document: dict, path: str, context: str) -> Any:
    value = document
    for part in path.split("."):
        if value is None:
            return None
        if not isinstance(value, dict):
            raise GarminParseError(f"{context}: {path} has a malformed parent object")
        value = value.get(part)
    return value


def _number(value: Any, field: _Field, context: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GarminParseError(f"{context}: {field.path} must be a JSON number or null")
    try:
        result = float(value)
    except OverflowError as exc:
        raise GarminParseError(f"{context}: {field.path} must be finite") from exc
    if not math.isfinite(result):
        raise GarminParseError(f"{context}: {field.path} must be finite")
    if result < 0 or (field.positive and result == 0):
        return None
    if field.maximum is not None and result > field.maximum:
        raise GarminParseError(f"{context}: {field.path} exceeds {field.maximum}")
    return result


def _timestamp(value: Any, context: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or "T" not in value:
        raise GarminParseError(f"{context}: timestamp must be an ISO datetime")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GarminParseError(f"{context}: timestamp must be an ISO datetime") from exc


def _morning(raw: Any, day: str, context: str) -> dict:
    if raw is None:
        return {}
    documents = raw if isinstance(raw, list) else [raw]
    candidates = []
    for entry in documents:
        document = _object(entry, context)
        _calendar_date(document, day, context)
        source_context = document.get("inputContext")
        if source_context is not None and not isinstance(source_context, str):
            raise GarminParseError(f"{context}: inputContext must be text or null")
        if source_context == "AFTER_WAKEUP_RESET":
            stamp = _timestamp(document.get("timestamp"), context)
            if document not in [item[1] for item in candidates]:
                candidates.append((stamp, document))
    if not candidates:
        return {}
    if len(candidates) == 1:
        return candidates[0][1]
    stamps = [stamp for stamp, _ in candidates]
    if any(stamp is None for stamp in stamps):
        raise GarminParseError(f"{context}: multiple morning readings require timestamps")
    aware = {stamp.utcoffset() is not None for stamp in stamps}
    if len(aware) != 1:
        raise GarminParseError(f"{context}: morning timestamps use inconsistent timezones")
    latest = max(stamps)
    selected = [document for stamp, document in candidates if stamp == latest]
    if len(selected) != 1:
        raise GarminParseError(f"{context}: conflicting morning readings at one timestamp")
    return selected[0]


def _summary(raw: Any, endpoint: str, day: str) -> dict:
    context = f"Garmin {endpoint} {day}"
    if endpoint == "training_readiness":
        return _morning(raw, day, context)
    document = _object(raw, context)
    _calendar_date(document, day, context)
    if endpoint in {"sleep", "hrv"}:
        key = "dailySleepDTO" if endpoint == "sleep" else "hrvSummary"
        document = _object(document.get(key), context)
        _calendar_date(document, day, context)
    if document.get("privacyProtected") is True:
        raise GarminParseError(f"{context}: privacy-protected data is not a measurement")
    return document


def _record(endpoint, day, marker, value, field, unit=None):
    record = {
        "provider": "garmin", "id": f"garmin:api:{endpoint}:{day}:{marker}",
        "day": day, "metric": marker, "value": value, "source_kind": "api",
        "source_endpoint": endpoint, "source_field": field,
    }
    if unit is not None:
        record["unit"] = unit
    return record


def parse_api(payload: dict[str, list[dict]]) -> list[dict]:
    """Normalize verified daily Garmin summary fields without mixing providers."""
    if not isinstance(payload, dict):
        raise GarminParseError("Garmin payload must be a dictionary of endpoint lists")
    summaries = {
        endpoint: [(day, _summary(raw, endpoint, day))
                   for day, raw in _documents(payload, endpoint)]
        for endpoint in GARMIN_ENDPOINTS
    }
    sleep_duration = _FIELDS["sleep"][0]
    observed_sleep_days = {
        day for day, document in summaries["sleep"]
        if (_number(document.get("sleepTimeSeconds"), sleep_duration,
                    f"Garmin sleep {day}") or 0) > 0
    }
    records = []
    for endpoint, fields in _FIELDS.items():
        for day, document in summaries[endpoint]:
            context = f"Garmin {endpoint} {day}"
            values = {field.path: _number(_path(document, field.path, context), field, context)
                      for field in fields}
            has_values = any(value is not None and value > 0 for value in values.values())
            if endpoint == "daily_summary" and not has_values and day not in observed_sleep_days:
                continue
            if endpoint == "sleep" and not has_values:
                continue
            if endpoint == "sleep" and values["sleepTimeSeconds"] == 0:
                # An explicit zero main-sleep duration denotes no completed night.
                # A separately supplied nap duration can still be a real observation.
                values = {key: value if key == "napTimeSeconds" else None
                          for key, value in values.items()}
            if endpoint == "training_readiness":
                phrase = document.get("recoveryTimeChangePhrase")
                if phrase is not None and not isinstance(phrase, str):
                    raise GarminParseError(f"{context}: recoveryTimeChangePhrase must be text")
                if phrase == "REACHED_ZERO":
                    values["recoveryTime"] = 0
            for field in fields:
                value = values[field.path]
                if value is not None:
                    records.append(_record(endpoint, day, field.marker,
                                           value / field.divisor, field.path, field.unit))
    return sorted(records, key=lambda record: (record["day"], record["metric"], record["id"]))


def categorical_inventory(payload: dict[str, list[dict]]) -> list[dict]:
    """Preserve HRV status text as counts, without guessing ranks or averaging codes."""
    if not isinstance(payload, dict):
        raise GarminParseError("Garmin payload must be a dictionary of endpoint lists")
    records = []
    for day, raw in _documents(payload, "hrv"):
        document = _summary(raw, "hrv", day)
        value = document.get("status")
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise GarminParseError(f"Garmin hrv {day}: status must be nonempty text or null")
        record = _record("hrv", day, "HRV Status (Garmin)", value, "status")
        record["source_value"] = value
        records.append(record)
    return records
