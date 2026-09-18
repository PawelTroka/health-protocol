"""Pure Garmin performance parsing; unknown fields/codes stay in raw archives.

Transport shapes follow the pinned Garmin client and its typed Activity model.
Keep running/cycling VO2 estimates, model ages, daily load and activity effects
distinct. A most-recent result from another date is not a new daily observation.
"""

from collections import defaultdict


PERFORMANCE_METRICS = {
    "VO2 Max Running (Garmin)": ("ml/kg/min", 1),
    "VO2 Max Cycling (Garmin)": ("ml/kg/min", 1),
    "Fitness Age (Garmin)": ("years", 1),
    "Achievable Fitness Age (Garmin)": ("years", 1),
    "Acute Training Load (Garmin)": ("load", 1),
    "Chronic Training Load (Garmin)": ("load", 1),
    "Acute/Chronic Training Load Ratio (Garmin)": ("ratio", 2),
    "Aerobic Training Effect per Workout (Garmin)": ("score", 2),
    "Anaerobic Training Effect per Workout (Garmin)": ("score", 2),
    "Training Load per Workout (Garmin)": ("load", 1),
    **{f"Workout HR Zone {zone} Duration (Garmin)": ("min", 1) for zone in range(1, 6)},
}


def _objects(raw, context):
    from . import garmin as g
    if raw is None:
        return []
    rows = raw if isinstance(raw, list) else [raw]
    if any(not isinstance(row, dict) for row in rows):
        raise g.GarminParseError(f"{context}: expected objects")
    if any(row.get("privacyProtected") is True for row in rows):
        raise g.GarminParseError(f"{context}: privacy-protected data is not a measurement")
    return rows


def _emit(records, endpoint, day, doc, path, marker, *, divisor=1, positive=False, maximum=None):
    from . import garmin as g
    unit = PERFORMANCE_METRICS[marker][0]
    field = g._Field(path, marker, unit, divisor, positive=positive, maximum=maximum)
    value = g._number(g._path(doc, path, f"Garmin {endpoint}"), field, f"Garmin {endpoint}")
    if value is not None:
        record = g._record(endpoint, day, marker, value / divisor, path, unit)
        records.append(record)
        return record
    return None


def _status_document(raw, day):
    from . import garmin as g
    doc = g._object(raw, "Garmin training status")
    if doc.get("privacyProtected") is True:
        raise g.GarminParseError("Garmin training status: privacy-protected data is not a measurement")
    devices = g._path(doc, "mostRecentTrainingStatus.latestTrainingStatusData", "Garmin training status")
    if devices is None:
        return None
    if not isinstance(devices, dict) or any(not isinstance(v, dict) for v in devices.values()):
        raise g.GarminParseError("Garmin training status: invalid device map")
    candidates = [v for v in devices.values() if v.get("primaryTrainingDevice") is True]
    if not candidates and len(devices) == 1:
        candidates = list(devices.values())
    if len(candidates) != 1:
        return None  # No arbitrary choice or mixing of multiple devices.
    selected = candidates[0]
    if selected.get("privacyProtected") is True:
        raise g.GarminParseError("Garmin training status: privacy-protected data is not a measurement")
    if selected.get("calendarDate") != day:
        return None  # The endpoint may carry an older 'most recent' status.
    return selected


def activity_identity(activity, day):
    from . import garmin as g
    ident = activity.get("activityId")
    if isinstance(ident, bool) or not isinstance(ident, (int, str)) or not str(ident).isdigit() or int(ident) <= 0:
        raise g.GarminParseError("Garmin activity requires a positive activity ID")
    stamp = activity.get("startTimeLocal")
    if not isinstance(stamp, str) or len(stamp) < 19 or stamp[10] not in ("T", " "):
        raise g.GarminParseError("Garmin activity requires its local start date")
    if g._day(stamp[:10], "Garmin activity") != day:
        raise g.GarminParseError("Garmin activity date does not match daily envelope")
    g._timestamp(stamp.replace(" ", "T", 1), "Garmin activity")
    return str(ident)


def _activities(raw, day):
    from . import garmin as g
    unique = {}
    for activity in _objects(raw, "Garmin activities"):
        ident = activity_identity(activity, day)
        if ident in unique and unique[ident] != activity:
            raise g.GarminParseError("Conflicting Garmin activity records")
        unique[ident] = activity
    # If the provider returns both a multisport parent and its component,
    # retain the parent once rather than double-counting the same exercise.
    return [(ident, activity) for ident, activity in unique.items()
            if str(activity.get("parentId")) not in unique]


def parse_performance(payload):
    from . import garmin as g
    records = []
    for day, raw in g._documents(payload, "max_metrics"):
        for doc in _objects(raw, "Garmin max metrics"):
            for key, sport in (("generic", "Running"), ("cycling", "Cycling")):
                item = g._object(doc.get(key), "Garmin VO2 max")
                # Require the actual measurement's date. No carry-forward from
                # status summaries or undated endpoint snapshots.
                if item.get("calendarDate") != day:
                    continue
                field = "vo2MaxPreciseValue" if item.get("vo2MaxPreciseValue") is not None else "vo2MaxValue"
                record = _emit(records, "max_metrics", day, item, field,
                               f"VO2 Max {sport} (Garmin)", positive=True)
                if record:
                    record["source_field"] = key + "." + field
    for day, raw in g._documents(payload, "fitness_age"):
        doc = g._object(raw, "Garmin fitness age")
        if doc.get("privacyProtected") is True:
            raise g.GarminParseError("Garmin fitness age: privacy-protected data is not a measurement")
        if not doc:
            continue
        source_day = doc.get("calendarDate")
        if source_day is None:
            # Verified live fitness-age responses date their snapshot using
            # lastUpdated, unlike the other daily metrics' calendarDate.
            stamp = doc.get("lastUpdated")
            if isinstance(stamp, str) and "T" in stamp:
                source_day = g._timestamp(stamp, "Garmin fitness age").date().isoformat()
        if source_day != day:
            continue  # An undated/latest model snapshot is not daily history.
        for field, marker in (("fitnessAge", "Fitness Age"), ("achievableFitnessAge", "Achievable Fitness Age")):
            _emit(records, "fitness_age", day, doc, field, marker + " (Garmin)", positive=True)
    for day, raw in g._documents(payload, "training_status"):
        doc = _status_document(raw, day)
        if doc:
            for field, marker in (("dailyTrainingLoadAcute", "Acute Training Load"),
                                  ("dailyTrainingLoadChronic", "Chronic Training Load"),
                                  ("dailyAcuteChronicWorkloadRatio", "Acute/Chronic Training Load Ratio")):
                _emit(records, "training_status", day, doc, "acuteTrainingLoadDTO." + field,
                      marker + " (Garmin)")
    for day, raw in g._documents(payload, "activities"):
        for ident, activity in _activities(raw, day):
            for field, marker, maximum in (
                ("aerobicTrainingEffect", "Aerobic Training Effect per Workout", 5),
                ("anaerobicTrainingEffect", "Anaerobic Training Effect per Workout", 5),
                ("activityTrainingLoad", "Training Load per Workout", None),
            ):
                record = _emit(records, "activities", day, activity, field, marker + " (Garmin)", maximum=maximum)
                if record:
                    record["id"] = f"garmin:api:activities:{ident}:{record['metric']}"
                    record["source_record_ids"] = [ident]
    for day, raw in g._documents(payload, "activity_hr_zones"):
        totals, ids = defaultdict(float), defaultdict(set)
        seen = {}
        for activity in _objects(raw, "Garmin activity HR zones"):
            ident = activity_identity(activity, day)
            if ident in seen:
                if seen[ident] != activity:
                    raise g.GarminParseError("Conflicting Garmin HR-zone records")
                continue
            seen[ident] = activity
            zone_seen = set()
            for zone in _objects(activity.get("zones"), "Garmin HR zones"):
                number = zone.get("zoneNumber")
                if type(number) is not int or not 1 <= number <= 5:
                    continue  # Unknown zone identities are not guessed.
                if number in zone_seen:
                    raise g.GarminParseError("Duplicate Garmin HR zone for one activity")
                zone_seen.add(number)
                field = g._Field("secsInZone", f"Workout HR Zone {number} Duration (Garmin)", "min")
                value = g._number(zone.get("secsInZone"), field, "Garmin HR zones")
                if value is not None:
                    totals[number] += value / 60
                    ids[number].add(ident)
        for number, value in totals.items():
            marker = f"Workout HR Zone {number} Duration (Garmin)"
            record = g._record("activity_hr_zones", day, marker, value, "zones.secsInZone", "min")
            record.update(source_record_ids=sorted(ids[number]), source_count=len(ids[number]),
                          daily_aggregation="sum_of_recorded_activity_zone_seconds")
            records.append(record)
    return records


def performance_classifications(payload):
    from . import garmin as g
    records = []
    def emit(endpoint, day, doc, path, marker, ident=None):
        value = g._path(doc, path, "Garmin classification")
        if value is None or value in ("", "NONE", "UNKNOWN", "NO_DATA"):
            return
        if not isinstance(value, str):
            raise g.GarminParseError("Garmin classification requires text, not a numeric code")
        if marker == "Training Status Feedback (Garmin)" and value in {"NO_STATUS_1", "NO_STATUS_2"}:
            return  # Verified onboarding/no-status feedback, not a health observation.
        record = g._record(endpoint, day, marker, value, path)
        if ident:
            record["id"] = f"garmin:api:{endpoint}:{ident}:{marker}"
        record["source_value"] = value
        records.append(record)
    for day, raw in g._documents(payload, "training_status"):
        doc = _status_document(raw, day)
        if doc:
            emit("training_status", day, doc, "trainingStatusFeedbackPhrase", "Training Status Feedback (Garmin)")
            emit("training_status", day, doc, "acuteTrainingLoadDTO.acwrStatus", "Training Load Status (Garmin)")
    for day, raw in g._documents(payload, "activities"):
        for ident, doc in _activities(raw, day):
            emit("activities", day, doc, "trainingEffectLabel", "Workout Training Effect (Garmin)", ident)
    return records
