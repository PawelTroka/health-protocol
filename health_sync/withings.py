"""Pure Withings API parsing; no requests, file access, or report mutation.

The current official schema is https://developer.withings.com/openapi.yaml
(measure-getmeas and sleepv2-getsummary, checked 2026-09-06). CSV export units
depend on account preferences and the official export guide does not specify
exact headers, so this module intentionally does not guess a CSV schema.
"""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import math
import re
from zoneinfo import ZoneInfo


# API base units, including constituents used only in same-group derivations.
# Pulse (11), AF/ECG classifications, nerve conductance/NRS, and VO2max are not
# mapped to differently defined report rows or to the existing Oura VO2max row.
WITHINGS_MEASURE_TYPES = {
    1: ("Body Mass", "kg"),
    4: ("Height", "m"),
    6: ("Body Fat", "%"),
    8: ("Fat Mass", "kg"),
    9: ("Diastolic Blood Pressure", "mmHg"),
    10: ("Systolic Blood Pressure", "mmHg"),
    12: ("Temperature", "C"),
    71: ("Body Temperature", "C"),
    76: ("Muscle Mass", "kg"),
    88: ("Bone Mass", "kg"),
    91: ("PWV", "m/s"),
    170: ("Visceral Fat Index", "index"),
}


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


def _collect(payloads, direct_key, page_key, user_ids):
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
        items = body.get(direct_key, []) or []
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


def parse_api(payloads: dict, *, height_cm: float | None = 180.0) -> list[dict]:
    """Normalize one authenticated user's measurements in Europe/Warsaw.

    Accepted keys: ``measuregrps`` and ``series`` contain flattened API objects;
    ``measure`` and ``sleep`` contain full getmeas/getsummary response pages.
    The caller must finish pagination before passing results. Explicitly mixed
    user IDs and ambiguous-user attrib=1 groups are never merged into a person.
    Manual entries (attrib=2/4) remain eligible and retain their attribution.

    BP is one ``Blood Pressure`` record with ``value=[systolic, diastolic]``.
    Other values are finite numbers. Missing/invalid readings are skipped;
    unsupported classifications are left to the report's manual source layer.
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
        for measure in measures:
            if not isinstance(measure, dict):
                continue
            measure_type = _integer(measure.get("type"))
            value = _scaled(measure) if measure_type in WITHINGS_MEASURE_TYPES else None
            if value is not None:
                if measure_type in values and values[measure_type] != value:
                    raise ValueError("Conflicting Withings measurements of the same type in one group")
                values[measure_type] = value
        metadata = {"group_id": key, "attribution": attribution}
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
            for measure_type, metric in ((8, "Body Fat"), (76, "Muscle"), (88, "Bone")):
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

    # Only medical AHI is imported here: other Withings sleep statistics must
    # not replace the report's Oura sleep aggregates or use a wellness index.
    for key, sleep in _latest_unique(sleeps, "id"):
        if sleep.get("completed") is not True:
            continue
        start = _timestamp(sleep.get("startdate"), zone)
        end = _timestamp(sleep.get("enddate"), zone)
        data = sleep.get("data")
        if start is None or end is None or end.timestamp() <= start.timestamp() or not isinstance(data, dict):
            continue
        ahi = _number(data.get("apnea_hypopnea_index"))
        if ahi is not None and ahi >= 0:
            records.append(_record(key, "Sleep Apnea AHI", ahi, "events/h", end,
                                   kind="sleep", source_field="apnea_hypopnea_index",
                                   started_at=start.isoformat()))
    return sorted(records, key=lambda record: (record["recorded_at"], record["id"]))
