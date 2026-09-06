"""Pure Withings API parsing; no requests, file access, or report mutation.

The current official schema is https://developer.withings.com/openapi.yaml
(measure-getmeas and sleepv2-getsummary, checked 2026-09-06). CSV export units
depend on account preferences and the official export guide does not specify
exact headers, so this module intentionally does not guess a CSV schema.
"""

from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
import math
import re
from zoneinfo import ZoneInfo


# Only schema-supported numeric measurements enter monthly averages. The live
# OpenAPI calls 130/139 AF classifications, not physical measurements. ECG
# interval (135-138) and ESC (229) fields have no explicit units in
# this schema and are retained by the caller in raw responses, not guessed here.
# Feet-specific NHS IDs are also documented on the official Body Scan data page:
# https://developer.withings.com/developer-guide/v3/integration-guide/onsite-mode/data-api/all-available-health-data-body-scan/
WITHINGS_MEASURE_TYPES = {
    1: ("Body Mass", "kg"),
    4: ("Height", "m"),
    5: ("Fat-Free Mass (Withings)", "kg"),
    6: ("Body Fat", "%"),
    8: ("Fat Mass (Withings)", "kg"),
    9: ("Diastolic Blood Pressure", "mmHg"),
    10: ("Systolic Blood Pressure", "mmHg"),
    11: ("Pulse Rate (Withings)", "bpm"),
    12: ("Temperature", "C"),
    54: ("SpO2 (Withings)", "%"),
    71: ("Body Temperature", "C"),
    73: ("Skin Temperature (Withings)", "C"),
    76: ("Muscle Mass (Withings)", "kg"),
    77: ("Water Mass (Withings)", "kg"),
    88: ("Bone Mass (Withings)", "kg"),
    91: ("PWV", "m/s"),
    123: ("VO2max (Withings)", "ml/kg/min"),
    147: ("Urinary pH (Withings)", "pH"),
    148: ("Urine Specific Gravity (Withings)", "ratio"),
    151: ("Urinary Nitrites (Withings)", "umol/L"),
    155: ("Vascular Age (Withings)", "years"),
    158: ("Nerve Health Score Left Foot (Withings)", "score"),
    159: ("Nerve Health Score Right Foot (Withings)", "score"),
    167: ("Nerve Health Score Feet (Withings)", "score"),
    168: ("Extracellular Water (Withings)", "kg"),
    169: ("Intracellular Water (Withings)", "kg"),
    170: ("Visceral Fat Index", "index"),
    173: ("Fat-Free Mass", "kg"),
    174: ("Fat Mass", "kg"),
    175: ("Muscle Mass", "kg"),
    196: ("Nerve Response Score (Withings)", "score"),
    204: ("Urinary Ketones (Withings)", "mmol/L"),
    205: ("Urinary Vitamin C (Withings)", "mmol/L"),
    226: ("Basal Metabolic Rate (Withings)", "kcal/day"),
    227: ("Metabolic Age (Withings)", "years"),
    248: ("Urinary Calcium (Withings)", "mmol/L"),
    249: ("Urinary Creatinine (Withings)", "mmol/L"),
    251: ("Urinary Calcium/Creatinine Ratio (Withings)", "mmol/mmol"),
}

_SEGMENTS = {2: "Right Arm", 3: "Left Arm", 10: "Left Leg", 11: "Right Leg", 12: "Torso"}
_SEGMENT_TYPES = {173, 174, 175}

# field -> (distinct report marker, report unit, conversion divisor, decimals).
_SLEEP_METRICS = {
    "total_timeinbed": ("Time in Bed (Withings)", "h", 3600, 2),
    "total_sleep_time": ("Sleep Duration (Withings)", "h", 3600, 2),
    "asleepduration": ("External Sleep Duration (Withings)", "h", 3600, 2),
    "lightsleepduration": ("Light Sleep (Withings)", "h", 3600, 2),
    "remsleepduration": ("REM Sleep (Withings)", "h", 3600, 2),
    "deepsleepduration": ("Deep Sleep (Withings)", "h", 3600, 2),
    "sleep_efficiency": ("Sleep Efficiency (Withings)", "%", 0.01, 1),
    "sleep_latency": ("Sleep Latency (Withings)", "min", 60, 1),
    "wakeup_latency": ("Wakeup Latency (Withings)", "min", 60, 1),
    "wakeupduration": ("Awake Duration (Withings)", "min", 60, 1),
    "waso": ("Wake After Sleep Onset (Withings)", "min", 60, 1),
    "wakeupcount": ("Wakeup Count (Withings)", "count", 1, 1),
    "nb_rem_episodes": ("REM Episode Count (Withings)", "count", 1, 1),
    "out_of_bed_count": ("Out of Bed Count (Withings)", "count", 1, 1),
    "hr_average": ("Average Sleeping HR (Withings)", "bpm", 1, 1),
    "hr_min": ("Mean Nightly Lowest HR (Withings)", "bpm", 1, 1),
    "hr_max": ("Mean Nightly Highest HR (Withings)", "bpm", 1, 1),
    # Official Sleep HRV support specifies ms and first/last 90-minute averages:
    # https://support.withings.com/hc/en-us/articles/35762631441681-Sleep-U-S-Nighttime-Heart-Rate-Variability-HRV
    "rmssd_start_avg": ("HRV at Sleep Start (Withings)", "ms", 1, 1),
    "rmssd_end_avg": ("HRV at Sleep End (Withings)", "ms", 1, 1),
    "rr_average": ("Respiratory Rate During Sleep (Withings)", "/min", 1, 1),
    "rr_min": ("Minimum Sleeping Respiratory Rate (Withings)", "/min", 1, 1),
    "rr_max": ("Maximum Sleeping Respiratory Rate (Withings)", "/min", 1, 1),
    "snoring": ("Snoring Duration (Withings)", "min", 60, 1),
    "snoringepisodecount": ("Snoring Episode Count (Withings)", "count", 1, 1),
    "sleep_score": ("Sleep Score (Withings)", "score", 1, 1),
    "apnea_hypopnea_index": ("Sleep Apnea AHI", "events/h", 1, 1),
    "withings_index": ("Sleep Rx Breathing Events Index (Withings)", "events/h", 1, 1),
    "mvt_score_avg": ("Sleeping Movement Score (Withings)", "score", 1, 1),
    "mvt_active_duration": ("Sleeping Movement Duration (Withings)", "min", 60, 1),
    "chest_movement_rate_wellness_average": ("Wellness Respiratory Rate (Withings)", "/min", 1, 1),
    "chest_movement_rate_wellness_min": ("Minimum Wellness Respiratory Rate (Withings)", "/min", 1, 1),
    "chest_movement_rate_wellness_max": ("Maximum Wellness Respiratory Rate (Withings)", "/min", 1, 1),
    "breathing_sounds": ("Breathing Sounds Duration (Withings)", "min", 60, 1),
    "breathing_sounds_episode_count": ("Breathing Sounds Episode Count (Withings)", "count", 1, 1),
    "chest_movement_rate_average": ("Chest Movement Rate (Withings)", "events/min", 1, 1),
    "chest_movement_rate_min": ("Minimum Chest Movement Rate (Withings)", "events/min", 1, 1),
    "chest_movement_rate_max": ("Maximum Chest Movement Rate (Withings)", "events/min", 1, 1),
    "core_body_temperature_min": ("Minimum Sleeping Core Temperature (Withings)", "C", 1, 2),
    "core_body_temperature_max": ("Maximum Sleeping Core Temperature (Withings)", "C", 1, 2),
    "core_body_temperature_avg": ("Average Sleeping Core Temperature (Withings)", "C", 1, 2),
}
_ACTIVITY_METRICS = {
    "steps": ("Steps (Withings)", "steps", 1, 1),
    "distance": ("Distance (Withings)", "m", 1, 1),
    "elevation": ("Floors Climbed (Withings)", "floors", 1, 1),
    "soft": ("Light Activity Duration (Withings)", "min", 60, 1),
    "moderate": ("Moderate Activity Duration (Withings)", "min", 60, 1),
    "intense": ("Intense Activity Duration (Withings)", "min", 60, 1),
    "active": ("Active Duration (Withings)", "min", 60, 1),
    "calories": ("Active Calories (Withings)", "kcal", 1, 1),
    "totalcalories": ("Total Calories (Withings)", "kcal", 1, 1),
    "hr_average": ("Average Daily HR (Withings)", "bpm", 1, 1),
    "hr_min": ("Mean Daily Lowest HR (Withings)", "bpm", 1, 1),
    "hr_max": ("Mean Daily Highest HR (Withings)", "bpm", 1, 1),
    "hr_zone_0": ("HR Light Zone Duration (Withings)", "min", 60, 1),
    "hr_zone_1": ("HR Moderate Zone Duration (Withings)", "min", 60, 1),
    "hr_zone_2": ("HR Intense Zone Duration (Withings)", "min", 60, 1),
    "hr_zone_3": ("HR Maximal Zone Duration (Withings)", "min", 60, 1),
}
# Include nonnumeric/under-specified fields when fetching so raw archives remain
# complete even though those fields intentionally do not enter numeric averages.
WITHINGS_SLEEP_FIELDS = list(_SLEEP_METRICS) + [
    "breathing_disturbances_intensity", "breathing_quality_assessment", "night_events",
    "core_body_temperature_status",
]
WITHINGS_ACTIVITY_FIELDS = list(_ACTIVITY_METRICS)
WITHINGS_METRICS = {
    "Body Mass": ("kg", 1), "Height (Withings)": ("cm", 1), "BMI": ("kg/m^2", 1),
    "Body Fat": ("%", 1), "Muscle": ("%", 1), "Bone": ("%", 1),
    "Lean Mass (Withings)": ("%", 1), "Body Water (Withings)": ("%", 1),
    "Blood Pressure": ("mmHg", 1), "Temperature": ("C", 1), "PWV": ("m/s", 1),
    "Visceral Fat Index": ("index", 1),
}
WITHINGS_METRICS.update({
    marker: (unit, 3 if unit == "ratio" else 2 if unit in {"kg", "mmol/L", "umol/L", "mmol/mmol"} else 1)
    for kind, (marker, unit) in WITHINGS_MEASURE_TYPES.items()
    if kind not in {1, 4, 6, 9, 10, 12, 71, 91, 170, *_SEGMENT_TYPES}
})
WITHINGS_METRICS.update({
    f"{WITHINGS_MEASURE_TYPES[kind][0]} - {segment} (Withings)": ("kg", 2)
    for kind in _SEGMENT_TYPES for segment in _SEGMENTS.values()
})
WITHINGS_METRICS.update({marker: (unit, places) for marker, unit, _, places in _SLEEP_METRICS.values()})
WITHINGS_METRICS.update({marker: (unit, places) for marker, unit, _, places in _ACTIVITY_METRICS.values()})


def _integer(value):
    if type(value) is int:
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value.strip()):
        try:
            return int(value)
        except ValueError:
            pass
    return None


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        number = float(value)
    except (ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _scaled(measure):
    # Never default a missing exponent to zero or truncate a fractional unit.
    exponent = _integer(measure.get("unit"))
    value = measure.get("value")
    if exponent is None or not -308 <= exponent <= 308 or _number(value) is None:
        return None
    try:
        exact = Decimal(str(value)).scaleb(exponent)
        scaled = float(exact)
    except (InvalidOperation, ValueError, OverflowError):
        return None
    if not math.isfinite(scaled) or (scaled == 0 and exact != 0):
        return None
    return scaled


def _timestamp(value, zone):
    value = _integer(value)
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(value, timezone.utc).astimezone(zone)
    except (ValueError, OverflowError, OSError):
        return None


def _identifier(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        return None
    value = str(value).strip()
    return value or None


def _collect(payloads, direct_key, page_key, user_ids, response_key=None):
    """Accept client-flattened rows or a list of full successful API pages."""
    rows = payloads.get(direct_key, []) or []
    if not isinstance(rows, list):
        raise ValueError(f"Withings {direct_key} must be a list")
    rows = list(rows)
    pages = payloads.get(page_key, []) or []
    if not isinstance(pages, list):
        raise ValueError(f"Withings {page_key} pages must be a list")
    for page in pages:
        if not isinstance(page, dict) or _integer(page.get("status")) != 0:
            raise ValueError("Withings API response is malformed or unsuccessful")
        body = page.get("body")
        if not isinstance(body, dict):
            raise ValueError("Withings API response has no valid body")
        for container in (page, body):
            user_id = _identifier(container.get("userid"))
            if user_id is not None:
                user_ids.add(user_id)
        items = body.get(response_key or direct_key, []) or []
        if not isinstance(items, list):
            raise ValueError(f"Withings response {direct_key} must be a list")
        rows.extend(items)
    if pages and pages[-1]["body"].get("more") in (True, 1, "1"):
        raise ValueError("Withings API pagination is incomplete")
    valid = [row for row in rows if isinstance(row, dict)]
    for row in valid:
        user_id = _identifier(row.get("userid"))
        if user_id is not None:
            user_ids.add(user_id)
    return valid


def _day(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _latest_unique(rows, id_key):
    """Keep the newest revision of each API object, without depending on order."""
    latest = {}
    for row in rows:
        key = _identifier(row.get(id_key))
        if key is None:
            continue
        previous = latest.get(key)
        modified = _integer(row.get("modified")) or 0
        previous_modified = (_integer(previous.get("modified")) or 0) if previous else -1
        if previous is None or modified > previous_modified:
            latest[key] = row
        elif modified == previous_modified and previous != row:
            raise ValueError("Conflicting Withings revisions share an identifier and timestamp")
    return latest.items()


def _record(key, metric, value, unit, recorded, *, kind="measure", **metadata):
    return {
        "provider": "withings",
        "id": f"withings:{kind}:{key}:{metric}",
        "day": recorded.date().isoformat(),
        "metric": metric,
        "value": value,
        "unit": unit,
        "source_kind": "api",
        "recorded_at": recorded.isoformat(),
        **metadata,
    }


_SLEEP_WEIGHTED_FIELDS = {
    "hr_average", "rr_average", "apnea_hypopnea_index", "withings_index",
    "chest_movement_rate_wellness_average", "chest_movement_rate_average",
    "core_body_temperature_avg",
}
_SLEEP_SESSION_MEAN_FIELDS = {
    "sleep_latency", "wakeup_latency", "rmssd_start_avg", "rmssd_end_avg",
    "sleep_score", "mvt_score_avg",
}


def _sleep_daily_records(sleeps, zone):
    """Combine distinct sleep periods before applying equal-day monthly means.

    No overlap is silently summed, even across devices or end-date boundaries.
    Session scores, latencies, and HRV edge windows cannot reconstruct an entire
    night, so retain their observed-session means with explicit provenance.
    """
    sessions = []
    for key, sleep in _latest_unique(sleeps, "id"):
        if sleep.get("completed") is not True or not isinstance(sleep.get("data"), dict):
            continue
        start, end = (_timestamp(sleep.get(field), zone) for field in ("startdate", "enddate"))
        if start is None or end is None or end.timestamp() <= start.timestamp():
            continue
        sessions.append((start, end, key, sleep))
    sessions.sort(key=lambda session: (session[0].timestamp(), session[1].timestamp(), session[2]))
    for previous, current in zip(sessions, sessions[1:]):
        if current[0].timestamp() < previous[1].timestamp():
            raise ValueError("Overlapping Withings sleep sessions cannot be combined safely")
    days = {}
    for session in sessions:
        days.setdefault(session[1].date().isoformat(), []).append(session)

    def valid_value(session, field, *, allow_negative=False):
        value = _number(session[3]["data"].get(field))
        if field in _SLEEP_METRICS and _SLEEP_METRICS[field][1] in {"bpm", "/min"} and value == 0:
            return None
        return value if value is not None and (allow_negative or value >= 0) else None

    records = []
    for day, periods in sorted(days.items()):
        for field, (marker, unit, divisor, _) in _SLEEP_METRICS.items():
            values = [(period, valid_value(period, field, allow_negative=unit == "C")) for period in periods]
            values = [(period, value) for period, value in values if value is not None]
            if field == "sleep_efficiency":
                pairs = [(period, valid_value(period, "total_sleep_time"), valid_value(period, "total_timeinbed"))
                         for period in periods]
                pairs = [(period, slept, bed) for period, slept, bed in pairs
                         if slept is not None and bed is not None and 0 <= slept <= bed and bed > 0]
                if not pairs:
                    continue
                value = sum(slept for _, slept, _ in pairs) / sum(bed for _, _, bed in pairs)
                contributors = [period for period, _, _ in pairs]
                aggregation = "ratio_of_daily_totals"
            elif not values:
                continue
            elif field in _SLEEP_WEIGHTED_FIELDS:
                weighted = [(period, value, valid_value(period, "total_sleep_time")) for period, value in values]
                weighted = [(period, value, weight) for period, value, weight in weighted
                            if weight is not None and weight > 0]
                if not weighted:
                    continue
                value = sum(value * weight for _, value, weight in weighted) / sum(weight for _, _, weight in weighted)
                contributors = [period for period, _, _ in weighted]
                aggregation = "sleep_duration_weighted_mean"
            else:
                contributors = [period for period, _ in values]
                numbers = [value for _, value in values]
                if field.endswith("_min"):
                    value, aggregation = min(numbers), "minimum"
                elif field.endswith("_max"):
                    value, aggregation = max(numbers), "maximum"
                elif field in _SLEEP_SESSION_MEAN_FIELDS:
                    value, aggregation = sum(numbers) / len(numbers), "mean_of_sessions"
                else:
                    value, aggregation = sum(numbers), "sum_nonoverlapping_sessions"
            intervals = [{"id": period[2], "started_at": period[0].isoformat(),
                          "ended_at": period[1].isoformat(),
                          "source_deviceid": period[3].get("hash_deviceid", period[3].get("deviceid")),
                          "model": period[3].get("model"), "model_id": period[3].get("model_id")}
                         for period in contributors]
            records.append(_record(f"daily-{day}", marker, value / divisor, unit, periods[-1][1],
                                   kind="sleep", source_field=field, source_day=day,
                                   started_at=contributors[0][0].isoformat(),
                                   daily_aggregation=aggregation, source_count=len(contributors),
                                   source_record_ids=[period[2] for period in contributors],
                                   source_intervals=intervals))
    return records


def parse_api(payloads: dict, *, height_cm: float | None = 180.0) -> list[dict]:
    """Normalize one authenticated user's measurements in Europe/Warsaw.

    Accepted flattened keys: measuregrps, series (sleep), activities, heart_series.
    Full response page keys: measure, sleep, activity, heart. Stetho and categorical
    observations are available separately through categorical_inventory.
    The caller must finish pagination before passing results. Explicitly mixed
    user IDs and ambiguous-user attrib=1 groups are never merged into a person.
    Manual entries (attrib=2/4) remain eligible and retain their attribution.

    BP is one ``Blood Pressure`` record with ``value=[systolic, diastolic]``.
    Other values are finite numbers. Missing/invalid readings are skipped;
    unsupported classifications are retained in a separate categorical inventory.
    A configured height derives BMI only with same-group weight; None disables
    BMI. Muscle and bone percentages require weight from the same group.
    Visceral fat remains the device's 0-20 index; it is never converted to %.
    """
    if not isinstance(payloads, dict):
        raise ValueError("Withings payloads must be an object")
    height = _number(height_cm) if height_cm is not None else None
    if height_cm is not None and (height is None or height <= 0 or height / 100 == 0):
        raise ValueError("Configured height must be a positive finite number or None")
    zone = ZoneInfo("Europe/Warsaw")
    user_ids = set()
    user_id = _identifier(payloads.get("userid"))
    if user_id is not None:
        user_ids.add(user_id)
    groups = _collect(payloads, "measuregrps", "measure", user_ids)
    sleeps = _collect(payloads, "series", "sleep", user_ids)
    activities = _collect(payloads, "activities", "activity", user_ids)
    hearts = _collect(payloads, "heart_series", "heart", user_ids, "series")
    if len(user_ids) > 1:
        raise ValueError("Withings payloads contain more than one user")
    records = []
    for key, group in _latest_unique(groups, "grpid"):
        attribution = _integer(group.get("attrib"))
        if _integer(group.get("category")) != 1 or attribution == 1:
            continue
        recorded = _timestamp(group.get("date"), zone)
        measures = group.get("measures")
        if recorded is None or not isinstance(measures, list):
            continue
        values = {}
        segments = {}
        for measure in measures:
            if not isinstance(measure, dict):
                continue
            measure_type = _integer(measure.get("type"))
            value = _scaled(measure) if measure_type in WITHINGS_MEASURE_TYPES else None
            if value is not None:
                if measure_type in _SEGMENT_TYPES:
                    position = _integer(measure.get("position"))
                    if position in _SEGMENTS:
                        segment_key = (measure_type, position)
                        if segment_key in segments and segments[segment_key] != value:
                            raise ValueError("Conflicting Withings segment measurements in one group")
                        segments[segment_key] = value
                    continue
                if measure_type in values and values[measure_type] != value:
                    raise ValueError("Conflicting Withings measurements of the same type in one group")
                values[measure_type] = value
        metadata = {"group_id": key, "attribution": attribution}
        for field in ("deviceid", "hash_deviceid", "model", "model_id"):
            if group.get(field) is not None:
                metadata[field] = group[field]
        modified = _timestamp(group.get("modified"), zone)
        if modified is not None:
            metadata["source_modified_at"] = modified.isoformat()

        def emit(metric, value, unit, types, **extra):
            if isinstance(value, list):
                finite = all(math.isfinite(component) for component in value)
            else:
                finite = math.isfinite(value)
            if finite:
                records.append(_record(key, metric, value, unit, recorded,
                                       source_types=types, **metadata, **extra))

        weight = values.get(1)
        if weight is not None and weight > 0:
            emit("Body Mass", weight, "kg", [1])
            if height is not None:
                # Divide successively to avoid underflow in height squared.
                bmi = weight / (height / 100) / (height / 100)
                if bmi > 0:
                    emit("BMI", bmi, "kg/m^2", [1],
                         derived_from={"weight_kg": weight, "configured_height_cm": height})
            for measure_type, metric in ((8, "Body Fat"), (76, "Muscle"), (88, "Bone"),
                                         (5, "Lean Mass (Withings)"), (77, "Body Water (Withings)")):
                mass = values.get(measure_type)
                if mass is not None and 0 <= mass <= weight and not (measure_type == 8 and 6 in values):
                    emit(metric, mass / weight * 100, "%", [measure_type, 1],
                         derived_from={"mass_kg": mass, "weight_kg": weight,
                                       "same_group": key})
        ratio = values.get(6)
        if ratio is not None and 0 <= ratio <= 100:
            emit("Body Fat", ratio, "%", [6])
        visceral_fat_index = values.get(170)
        if visceral_fat_index is not None and 0 <= visceral_fat_index <= 20:
            emit("Visceral Fat Index", visceral_fat_index, "index", [170])
        systolic, diastolic = values.get(10), values.get(9)
        if systolic is not None and diastolic is not None and systolic >= diastolic > 0:
            emit("Blood Pressure", [systolic, diastolic], "mmHg", [10, 9])
        temperature_type = 71 if 71 in values else 12
        if temperature_type in values:
            emit("Temperature", values[temperature_type], "C", [temperature_type])
        if values.get(91, 0) > 0:
            emit("PWV", values[91], "m/s", [91])
        if values.get(4, 0) > 0:
            emit("Height (Withings)", values[4] * 100, "cm", [4])
        handled = {1, 4, 6, 9, 10, 12, 71, 91, 170}
        for kind, value in values.items():
            if kind in handled:
                continue
            marker, unit = WITHINGS_MEASURE_TYPES[kind]
            if unit != "C" and value < 0:
                continue
            if unit == "%" and value > 100:
                continue
            if unit == "kg" and weight is not None and weight > 0 and value > weight:
                continue
            emit(marker, value, unit, [kind])
        for (kind, position), value in segments.items():
            if value >= 0 and (weight is None or weight <= 0 or value <= weight):
                marker = f"{WITHINGS_MEASURE_TYPES[kind][0]} - {_SEGMENTS[position]} (Withings)"
                emit(marker, value, "kg", [kind], source_position=position)

    # Completed summaries retain their own Withings identities; they never
    # replace Oura metrics or relabel the Sleep Rx index as medical AHI.
    records.extend(_sleep_daily_records(sleeps, zone))

    # getactivity returns daily aggregates. Revisions replace a date rather than
    # adding another full day's steps/calories or averaging duplicate snapshots.
    dated = [{**activity, "_date_id": activity["date"]} for activity in activities
             if _day(activity.get("date")) is not None]
    for key, activity in _latest_unique(dated, "_date_id"):
        recorded = datetime.combine(_day(activity["date"]), time.min, zone)
        modified = _timestamp(activity.get("modified"), zone)
        for field, (marker, unit, divisor, _) in _ACTIVITY_METRICS.items():
            value = _number(activity.get(field))
            if value is not None and value >= 0 and not (unit == "bpm" and value == 0):
                records.append(_record(key, marker, value / divisor, unit, recorded,
                                       kind="activity", source_field=field,
                                       source_timezone=activity.get("timezone"),
                                       source_modified_at=modified.isoformat() if modified else None))

    for key, heart in _latest_unique(_heart_identifiers(hearts), "_heart_id"):
        recorded = _timestamp(heart.get("timestamp"), zone)
        rate = _number(heart.get("heart_rate"))
        if recorded is not None and rate is not None and rate > 0:
            records.append(_record(key, "ECG Recorded Heart Rate (Withings)", rate, "bpm", recorded,
                                   kind="heart", source_field="heart_rate"))
    return sorted(records, key=lambda record: (record["recorded_at"], record["id"]))


WITHINGS_METRICS["ECG Recorded Heart Rate (Withings)"] = ("bpm", 1)


def _heart_identifiers(hearts):
    records = []
    for heart in hearts:
        ecg = heart.get("ecg")
        identifier = _identifier(ecg.get("signalid")) if isinstance(ecg, dict) else None
        if identifier is None:
            # Timestamp+device is a fallback for records without an ECG signal ID.
            stamp = _integer(heart.get("timestamp"))
            device = _identifier(heart.get("deviceid"))
            if stamp is not None and device is not None:
                identifier = f"{stamp}:{device}"
        if identifier is not None:
            records.append({**heart, "_heart_id": identifier})
    return records


_AF_MEASURE_LABELS = {
    0: "Negative", 1: "Positive", 2: "Inconclusive", 3: "No signal", 4: "Other",
    5: "Noise", 6: "Low Heart Rate", 7: "High Heart Rate", 8: "Inconclusive US",
    9: "Negative normal HR", 10: "Negative high HR", 11: "Positive normal HR",
    12: "Positive high HR", 13: "No Diagnosis",
}

WITHINGS_CATEGORICAL_METRICS = {
    "ECG AF Classification (Withings)",
    "PPG AF Classification (Withings)",
    "Heart Sounds Classification (Withings)",
    "Breathing Disturbance Intensity (Withings)",
    "Breathing Quality Assessment (Withings)",
    "Core Body Temperature Status (Withings)",
}


def _matching_af_measure_ids(groups, hearts):
    """Match repeated ECG exports conservatively, including BPM timestamp lag.

    BPM getmeas dates can precede heart/list dates by the measurement duration.
    For unequal timestamps, require the same device and exact HR plus both BP
    values within two minutes. Each side must have a unique candidate; ambiguous
    matches remain separate observations rather than discarding a real test.
    """
    candidates = {}
    for key, group in groups:
        stamp = _integer(group.get("date"))
        measures = group.get("measures")
        if stamp is None or not isinstance(measures, list):
            continue
        values = {_integer(m.get("type")): _scaled(m) for m in measures if isinstance(m, dict)}
        if 130 not in values:
            continue
        device = _identifier(group.get("deviceid") or group.get("hash_deviceid"))
        matches = []
        for heart_key, heart in hearts:
            ecg, bp = heart.get("ecg"), heart.get("bloodpressure")
            at = _integer(heart.get("timestamp"))
            heart_device = _identifier(heart.get("deviceid"))
            if (at is None or not isinstance(ecg, dict) or ecg.get("afib") is None
                    or (device is not None and heart_device is not None and device != heart_device)):
                continue
            if stamp == at:
                matches.append(heart_key)
            elif (0 < at - stamp <= 120 and device is not None and device == heart_device
                    and isinstance(bp, dict) and all(values.get(kind) is not None for kind in (9, 10, 11))
                    and values[9] == _number(bp.get("diastole"))
                    and values[10] == _number(bp.get("systole"))
                    and values[11] == _number(heart.get("heart_rate"))):
                matches.append(heart_key)
        if len(matches) == 1:
            candidates[key] = matches[0]
    return {key for key, heart_key in candidates.items()
            if list(candidates.values()).count(heart_key) == 1}


def categorical_inventory(payloads: dict) -> list[dict]:
    """Return dated nonnumeric observations, never monthly-average inputs.

    Known AF labels describe only the provider's AF classifier, not a diagnosis
    of normal sinus rhythm. Undocumented VHD/PPG/breathing codes stay explicitly
    unmapped. Raw responses remain the authoritative full-resolution archive.
    """
    if not isinstance(payloads, dict):
        raise ValueError("Withings payloads must be an object")
    user_ids = set()
    own_user = _identifier(payloads.get("userid"))
    if own_user is not None:
        user_ids.add(own_user)
    groups = _collect(payloads, "measuregrps", "measure", user_ids)
    sleeps = _collect(payloads, "series", "sleep", user_ids)
    hearts = _collect(payloads, "heart_series", "heart", user_ids, "series")
    stethos = _collect(payloads, "stetho_series", "stetho", user_ids, "series")
    if len(user_ids) > 1:
        raise ValueError("Withings payloads contain more than one user")
    zone = ZoneInfo("Europe/Warsaw")
    events = []
    latest_groups = list(_latest_unique(groups, "grpid"))
    latest_hearts = list(_latest_unique(_heart_identifiers(hearts), "_heart_id"))
    duplicate_af_groups = _matching_af_measure_ids(latest_groups, latest_hearts)

    def emit(key, field, raw, recorded, labels=None):
        if recorded is None or raw is None or isinstance(raw, (dict, list, bool)):
            return
        if isinstance(raw, (int, float)) and _number(raw) is None:
            return
        code = _integer(raw)
        label = (labels or {}).get(code)
        if label is None:
            label = str(raw) if isinstance(raw, str) and code is None else f"Device code {raw}"
        events.append({"provider": "withings", "id": f"withings:event:{key}:{field}",
                       "day": recorded.date().isoformat(), "recorded_at": recorded.isoformat(),
                       "metric": field, "value": label, "source_value": raw, "source_kind": "api"})

    for key, group in latest_groups:
        if _integer(group.get("category")) != 1 or _integer(group.get("attrib")) == 1:
            continue
        recorded = _timestamp(group.get("date"), zone)
        for measure in group.get("measures", []) if isinstance(group.get("measures"), list) else []:
            if not isinstance(measure, dict):
                continue
            kind = _integer(measure.get("type"))
            if kind == 130 and key in duplicate_af_groups:
                continue
            if kind in {130, 139}:
                emit(f"measure:{key}", "ECG AF Classification (Withings)" if kind == 130 else
                     "PPG AF Classification (Withings)", measure.get("value"), recorded,
                     _AF_MEASURE_LABELS if kind == 130 else None)
    for key, heart in latest_hearts:
        recorded = _timestamp(heart.get("timestamp"), zone)
        if isinstance(heart.get("ecg"), dict):
            emit(f"heart:{key}", "ECG AF Classification (Withings)", heart["ecg"].get("afib"),
                 recorded, {0: "Negative", 1: "Positive", 2: "Inconclusive"})
        if isinstance(heart.get("stetho"), dict):
            emit(f"heart:{key}", "Heart Sounds Classification (Withings)", heart["stetho"].get("vhd"), recorded)
    for key, stetho in _latest_unique(stethos, "signalid"):
        emit(f"stetho:{key}", "Heart Sounds Classification (Withings)", stetho.get("vhd"),
             _timestamp(stetho.get("timestamp"), zone))
    for key, sleep in _latest_unique(sleeps, "id"):
        if sleep.get("completed") is not True or not isinstance(sleep.get("data"), dict):
            continue
        for field, marker in {
            "breathing_disturbances_intensity": "Breathing Disturbance Intensity (Withings)",
            "breathing_quality_assessment": "Breathing Quality Assessment (Withings)",
            "core_body_temperature_status": "Core Body Temperature Status (Withings)",
        }.items():
            emit(f"sleep:{key}", marker, sleep["data"].get(field), _timestamp(sleep.get("enddate"), zone))
    return sorted(events, key=lambda event: (event["recorded_at"], event["id"]))
