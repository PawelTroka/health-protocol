"""Pure Oura trends CSV and comprehensive API v2 health-metric parsers.

Official schema, checked 2026-09-06:
https://cloud.ouraring.com/v2/static/json/openapi-1.37.json
https://cloud.ouraring.com/v2/docs
VO2 unit: https://support.ouraring.com/hc/en-us/articles/28336620578835
The live API additionally requires heart_health for cardiovascular age/VO2 and
stress for resilience, despite these scopes being absent from the schema list.
OAuth authorization follows /docs/authentication's spo2 spelling (the schema
calls it spo2Daily). Authentication and paginated fetching belong to api.py.

CSV rows are Oura's exported daily observations. API observations use the longest
completed ``long_sleep`` period assigned to each Oura ``day``; naps and rests are
excluded. The daily sleep score can include other contributing sleep periods and
comes independently from ``daily_sleep.score``. This primary-night policy need not
reproduce every CSV aggregate. In addition, the API documents that its mean and
lowest HR use 30-second samples, whereas the app uses aggregated 5-minute samples.
Keep source_kind when storing/aggregating records; do not silently mix CSV and API
versions of the same day's metric. Date-window and current-day exclusion belong
to the caller, so these parsers remain deterministic and independent of the clock.

Values are converted to report units without rounding. Null/blank measurements
are omitted, never replaced with zero. Structural validation is not a clinical
reference-range assessment. Neither parser performs network requests or writes.

Daily summaries use Oura's assigned day (activity days start at 04:00), not a
timestamp converted to another date. Discrete HR samples use Europe/Warsaw days.
Workout/session quantities are per recorded event, so a downstream mean of daily
means is not mislabeled as a daily total. Stress/resilience categories are exposed
separately by ``categorical_inventory`` for counts. Clock times, profile values
without historical dates, ring diagnostics, and classification sequences are not
numerical health observations; they remain available in source archives.
The CSV parser intentionally retains the eleven verified sleep export columns;
the broader schema below describes API fields, not guessed CSV column names.
"""

from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


OURA_ENDPOINTS = [
    "sleep", "daily_sleep", "daily_readiness", "daily_activity", "daily_spo2",
    "daily_cardiovascular_age", "vO2_max", "daily_stress", "daily_resilience",
    "heartrate", "workout", "session",
]

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


@dataclass(frozen=True)
class _Field:
    path: str
    marker: str
    unit: str
    divisor: float = 1
    decimals: int = 1
    minimum: float | None = 0
    maximum: float | None = None


def _field(path, name, unit, divisor=1, decimals=1, minimum=0, maximum=None):
    return _Field(path, f"{name} (Oura)", unit, divisor, decimals, minimum, maximum)


def _contributors(prefix, fields):
    return tuple(_field(f"contributors.{key}", f"{prefix} {name} Contributor Score",
                        "score", maximum=100) for key, name in fields)


_SLEEP_FIELDS = (
    _field("light_sleep_duration", "Light Sleep", "h", 3600, 2),
    _field("awake_time", "Awake Time During Sleep", "h", 3600, 2),
    _field("restless_periods", "Restless Periods During Sleep", "count"),
    _field("readiness_score_delta", "Primary Sleep Readiness Score Change", "points",
           minimum=None),
    _field("sleep_score_delta", "Primary Sleep Score Change", "points", minimum=None),
)

_DAILY_FIELDS = {
    "daily_sleep": (
        _Field("score", "Sleep Score", "score", maximum=100),
    ) + _contributors("Sleep", (
        ("deep_sleep", "Deep Sleep"), ("efficiency", "Efficiency"),
        ("latency", "Latency"), ("rem_sleep", "REM Sleep"),
        ("restfulness", "Restfulness"), ("timing", "Timing"),
        ("total_sleep", "Total Sleep"),
    )),
    "daily_readiness": (
        _field("score", "Readiness Score", "score", maximum=100),
        _field("temperature_deviation", "Temperature Deviation", "°C", decimals=2,
               minimum=None),
        _field("temperature_trend_deviation", "Temperature Trend Deviation", "°C",
               decimals=2, minimum=None),
    ) + _contributors("Readiness", (
        ("activity_balance", "Activity Balance"), ("body_temperature", "Body Temperature"),
        ("hrv_balance", "HRV Balance"), ("previous_day_activity", "Previous Day Activity"),
        ("previous_night", "Previous Night"), ("recovery_index", "Recovery Index"),
        ("resting_heart_rate", "Resting HR"), ("sleep_balance", "Sleep Balance"),
        ("sleep_regularity", "Sleep Regularity"),
    )),
    "daily_activity": (
        _field("score", "Activity Score", "score", maximum=100),
        _field("steps", "Steps", "steps", decimals=0),
        _field("active_calories", "Active Energy", "kcal"),
        _field("total_calories", "Total Energy Expenditure", "kcal"),
        _field("average_met_minutes", "Average MET Minutes", "MET-min", decimals=2),
        _field("equivalent_walking_distance", "Equivalent Walking Distance", "km", 1000, 2),
        _field("high_activity_met_minutes", "High Activity MET Minutes", "MET-min"),
        _field("low_activity_met_minutes", "Low Activity MET Minutes", "MET-min"),
        _field("medium_activity_met_minutes", "Medium Activity MET Minutes", "MET-min"),
        _field("sedentary_met_minutes", "Sedentary MET Minutes", "MET-min"),
        _field("high_activity_time", "High Activity Time", "h", 3600, 2),
        _field("medium_activity_time", "Medium Activity Time", "h", 3600, 2),
        _field("low_activity_time", "Low Activity Time", "h", 3600, 2),
        _field("sedentary_time", "Sedentary Time", "h", 3600, 2),
        _field("resting_time", "Resting Time", "h", 3600, 2),
        _field("non_wear_time", "Non-wear Time", "h", 3600, 2),
        _field("inactivity_alerts", "Inactivity Alerts", "count"),
        _field("target_calories", "Activity Energy Target", "kcal"),
        _field("target_meters", "Activity Distance Target", "km", 1000, 2),
        _field("meters_to_target", "Distance Remaining to Activity Target", "km", 1000, 2,
               minimum=None),
    ) + _contributors("Activity", (
        ("meet_daily_targets", "Meet Daily Targets"), ("move_every_hour", "Move Every Hour"),
        ("recovery_time", "Recovery Time"), ("stay_active", "Stay Active"),
        ("training_frequency", "Training Frequency"), ("training_volume", "Training Volume"),
    )),
    "daily_spo2": (
        _field("spo2_percentage.average", "Average Sleeping SpO2", "%", maximum=100),
        _field("breathing_disturbance_index", "Breathing Disturbance Index", "index",
               maximum=100),
    ),
    "daily_cardiovascular_age": (
        _field("vascular_age", "Cardiovascular Age", "years", minimum=18, maximum=100),
        _field("pulse_wave_velocity", "Estimated PWV", "m/s", decimals=2),
    ),
    "vO2_max": (
        _field("vo2_max", "VO2 Max", "ml/kg/min"),
    ),
    "daily_stress": (
        _field("stress_high", "High Stress Time", "h", 3600, 2),
        _field("recovery_high", "High Recovery Time", "h", 3600, 2),
    ),
    "daily_resilience": _contributors("Resilience", (
        ("sleep_recovery", "Sleep Recovery"), ("daytime_recovery", "Daytime Recovery"),
        ("stress", "Stress"),
    )),
}

_WORKOUT_FIELDS = (
    _field("calories", "Energy per Recorded Workout", "kcal"),
    _field("distance", "Distance per Recorded Workout", "km", 1000, 2),
)
_HEARTRATE_MARKERS = {
    source: f"Sampled {label} HR (Oura)" for source, label in (
        ("awake", "Awake"), ("workout", "Workout"), ("rest", "Rest"),
        ("sleep", "Sleeping"), ("live", "Live"), ("session", "Session"),
    )
}
_SESSION_SAMPLES = (
    ("heart_rate", "Sampled HR During Sessions (Oura)", "bpm"),
    ("heart_rate_variability", "Sampled HRV During Sessions (Oura)", "ms"),
    ("motion_count", "Sampled Motion Count During Sessions (Oura)", "count"),
)
_PRIMARY_SLEEP_SAMPLES = (
    ("heart_rate", "Sampled HR During Primary Sleep (Oura)", "bpm"),
    ("hrv", "Sampled HRV During Primary Sleep (Oura)", "ms"),
)

# Public registry consumed by monthly aggregation and report generation.
OURA_METRICS = {
    marker: (unit, 2 if unit in {"h", "/min"} else 1)
    for marker, _, _, unit, _ in _METRICS
}
OURA_METRICS.update({field.marker: (field.unit, field.decimals)
                     for fields in (_SLEEP_FIELDS, _WORKOUT_FIELDS, *_DAILY_FIELDS.values())
                     for field in fields})
OURA_METRICS.update({marker: ("bpm", 1) for marker in _HEARTRATE_MARKERS.values()})
OURA_METRICS.update({marker: (unit, 1)
                     for _, marker, unit in (*_SESSION_SAMPLES, *_PRIMARY_SLEEP_SAMPLES)})
OURA_METRICS.update({
    "Duration per Recorded Workout (Oura)": ("h", 2),
    "Duration per Recorded Session (Oura)": ("min", 1),
    "Sampled Activity MET (Oura)": ("MET", 2),
})

_CATEGORICAL_FIELDS = {
    "daily_stress": ("day_summary", "Stress Day Summary (Oura)", {
        "restored": "Restored", "normal": "Normal", "stressful": "Stressful",
    }),
    "daily_resilience": ("level", "Resilience Level (Oura)", {
        "limited": "Limited", "adequate": "Adequate", "solid": "Solid",
        "strong": "Strong", "exceptional": "Exceptional",
    }),
}
OURA_CATEGORICAL_METRICS = {marker for _, marker, _ in _CATEGORICAL_FIELDS.values()}


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


def _number(value: Any, field: str, context: str, *, csv_text: bool = False,
            minimum: float | None = 0, maximum: float | None = None) -> float | None:
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
    if not math.isfinite(result):
        raise OuraParseError(f"{context}: {field} must be finite")
    if minimum is not None and result < minimum:
        raise OuraParseError(f"{context}: {field} must be at least {minimum}")
    if maximum is not None and result > maximum:
        raise OuraParseError(f"{context}: {field} must be at most {maximum}")
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


def _nested(document: dict, path: str, context: str):
    value = document
    for part in path.split("."):
        if value is None:
            return None
        if not isinstance(value, dict):
            raise OuraParseError(f"{context}: {path} requires object containers")
        value = value.get(part)
    return value


def _api_record(day, endpoint, source_id, marker, value, unit, stamp, field, **metadata):
    record = _record(day, "api", f"{endpoint}:{source_id}", marker, value, unit, stamp)
    record.update(source_endpoint=endpoint, source_field=field, **metadata)
    return record


def _field_records(document, endpoint, fields, stamp):
    records = []
    context = f"Oura {endpoint} document"
    for field in fields:
        value = _number(_nested(document, field.path, context), field.path, context,
                        minimum=field.minimum, maximum=field.maximum)
        if endpoint == "daily_spo2" and field.path == "spo2_percentage.average" and value == 0:
            # Archived responses contain exact-zero aggregates on some days.
            # Zero is unusable as an overnight oxygen-saturation measurement;
            # keep it in the raw archive, not in the numeric monthly mean.
            # Oura documents missing SpO2 but does not define a zero sentinel:
            # https://support.ouraring.com/hc/en-us/articles/7328398760851
            # Every positive value is retained, including low readings. Negative
            # or >100 values still raise the structural validation error above.
            continue
        if value is not None:
            records.append(_api_record(
                document["day"], endpoint, document["id"], field.marker,
                value / field.divisor, field.unit, stamp, field.path,
            ))
    return records


def _sample_records(document, endpoint, path, marker, unit):
    """Preserve finite samples; the caller's daily mean gives each sample weight.

    Null samples are gaps, not zeros. Source interval and index remain traceable.
    The document's assigned Oura day also applies to samples crossing midnight.
    """
    samples = document.get(path)
    if samples is None:
        return []
    context = f"Oura {endpoint} {path} samples"
    if not isinstance(samples, dict) or not isinstance(samples.get("items"), list):
        raise OuraParseError(f"{context}: expected an object containing an items list")
    interval = _number(samples.get("interval"), "interval", context)
    stamp = _timestamp(samples.get("timestamp"), context)
    if interval is None or interval <= 0 or stamp is None:
        raise OuraParseError(f"{context}: requires a positive interval and timestamp")
    start = datetime.fromisoformat(stamp)
    records = []
    for index, raw in enumerate(samples["items"]):
        value = _number(raw, path, context)
        if value is None:
            continue
        if unit == "bpm" and value == 0:
            raise OuraParseError(f"{context}: heart rate must be positive")
        try:
            recorded_at = (start + timedelta(seconds=index * interval)).isoformat()
        except (OverflowError, ValueError) as exc:
            raise OuraParseError(f"{context}: sample timestamp is out of range") from exc
        records.append(_api_record(
            document["day"], endpoint, f"{document['id']}:{path}:{index}", marker,
            value, unit, recorded_at, f"{path}.items",
            sample_index=index, sample_interval_seconds=interval,
        ))
    return records


def _daily_records(payloads):
    records = []
    for endpoint, fields in _DAILY_FIELDS.items():
        selected = {}
        for document in _documents(payloads, endpoint):
            stamp = _timestamp(document.get("timestamp"), f"Oura {endpoint} document")
            values = _field_records(document, endpoint, fields, stamp)
            if endpoint == "daily_activity":
                values.extend(_sample_records(document, endpoint, "met",
                                               "Sampled Activity MET (Oura)", "MET"))
            rank = (datetime.fromisoformat(stamp).astimezone(timezone.utc) if stamp else
                    datetime.min.replace(tzinfo=timezone.utc), document["id"])
            if document["day"] not in selected or rank > selected[document["day"]][0]:
                selected[document["day"]] = (rank, values)
        records.extend(record for _, values in selected.values() for record in values)
    return records


def _event_records(payloads):
    records = []
    for endpoint in ("workout", "session"):
        for document in _documents(payloads, endpoint):
            context = f"Oura {endpoint} document"
            start = _timestamp(document.get("start_datetime"), context)
            end = _timestamp(document.get("end_datetime"), context)
            if not start or not end:
                # An ongoing/incomplete event must not become a completed duration.
                continue
            duration = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
            if duration <= 0:
                raise OuraParseError(f"{context}: end must follow start")
            divisor, unit = (3600, "h") if endpoint == "workout" else (60, "min")
            records.append(_api_record(
                document["day"], endpoint, document["id"],
                f"Duration per Recorded {endpoint.title()} (Oura)", duration / divisor,
                unit, end, "end_datetime-start_datetime",
                derived_from=["start_datetime", "end_datetime"],
            ))
            if endpoint == "workout":
                records.extend(_field_records(document, endpoint, _WORKOUT_FIELDS, end))
            else:
                for path, marker, unit in _SESSION_SAMPLES:
                    records.extend(_sample_records(document, endpoint, path, marker, unit))
    return records


def _heartrate_records(payloads):
    documents = payloads.get("heartrate", [])
    if not isinstance(documents, list):
        raise OuraParseError("Oura heartrate: expected a list of documents")
    unique = {}
    for document in documents:
        context = "Oura heartrate document"
        if not isinstance(document, dict):
            raise OuraParseError(f"{context}: expected an object")
        stamp = _timestamp(document.get("timestamp"), context)
        if stamp is None:
            raise OuraParseError(f"{context}: timestamp is required")
        instant = datetime.fromisoformat(stamp).astimezone(timezone.utc)
        source = document.get("source")
        if not isinstance(source, str) or source not in _HEARTRATE_MARKERS:
            raise OuraParseError(f"{context}: unknown heart-rate source")
        value = _number(document.get("bpm"), "average_heart_rate", context)
        if "timestamp_unix" in document:
            unix_ms = _number(document["timestamp_unix"], "timestamp_unix", context)
            if unix_ms is None or abs(unix_ms - instant.timestamp() * 1000) > 1:
                raise OuraParseError(f"{context}: timestamp fields disagree")
        key = (instant.isoformat(), source)
        if key in unique and unique[key] != value:
            raise OuraParseError(f"{context}: conflicting duplicate sample")
        unique[key] = value
    records = []
    for (stamp, source), value in unique.items():
        if value is None:
            continue
        day = datetime.fromisoformat(stamp).astimezone(ZoneInfo("Europe/Warsaw")).date().isoformat()
        records.append(_api_record(day, "heartrate", f"{stamp}:{source}",
                                   _HEARTRATE_MARKERS[source], value, "bpm", stamp,
                                   "bpm", sample_source=source))
    return records


def categorical_inventory(payloads: dict[str, list[dict]]) -> list[dict]:
    """Return daily qualitative health observations, separate from numeric data.

    Values are labels for monthly counts, never ordinal scores. Unknown future
    text labels remain explicitly unmapped instead of acquiring an invented rank.
    Daily summaries without a timestamp keep only their authoritative Oura day.
    """
    if not isinstance(payloads, dict):
        raise OuraParseError("Oura API payloads must be a dictionary of endpoint lists")
    records = []
    for endpoint, (field, marker, labels) in _CATEGORICAL_FIELDS.items():
        selected = {}
        for document in _documents(payloads, endpoint):
            context = f"Oura {endpoint} document"
            stamp = _timestamp(document.get("timestamp"), context)
            value = document.get(field)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise OuraParseError(f"{context}: {field} must be nonempty text or null")
            rank = (datetime.fromisoformat(stamp).astimezone(timezone.utc) if stamp else
                    datetime.min.replace(tzinfo=timezone.utc), document["id"])
            if document["day"] not in selected or rank > selected[document["day"]][0]:
                selected[document["day"]] = (rank, document, stamp, value)
        for _, document, stamp, value in selected.values():
            if value is None:
                continue
            record = {
                "provider": "oura",
                "id": f"oura:event:{endpoint}:{document['id']}:{marker}",
                "day": document["day"], "metric": marker,
                "value": labels.get(value, f"Unmapped category: {value}"),
                "source_value": value, "source_kind": "api",
                "source_endpoint": endpoint, "source_field": field,
            }
            if stamp is not None:
                record["recorded_at"] = stamp
            records.append(record)
    return _sort(records)


def parse_api(payloads: dict[str, list[dict]]) -> list[dict]:
    """Normalize already-fetched and fully paginated health endpoint documents.

    Pick the completed long_sleep with greatest total_sleep_duration for each
    Oura day, breaking ties by latest bedtime_end and then lexicographic id.
    Missing total sleep, time in bed, or either bedtime endpoint means incomplete.
    Optional null measures remain absent. Missing daily score is never obtained
    from the contributors or readiness score. Daily summaries are independent of
    whether a completed primary night is available. Same-day daily documents use
    latest timestamp, then id; a latest missing field never revives an older value.
    Conflicting versions of one id raise; fetch current versions
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
                records.append(_api_record(
                    day, "sleep", document["id"], marker,
                    values[field] / divisor, unit, end, field,
                ))
        records.extend(_field_records(document, "sleep", _SLEEP_FIELDS, end))
        for path, marker, unit in _PRIMARY_SLEEP_SAMPLES:
            records.extend(_sample_records(document, "sleep", path, marker, unit))

    records.extend(_daily_records(payloads))
    records.extend(_event_records(payloads))
    records.extend(_heartrate_records(payloads))
    return _sort(records)
