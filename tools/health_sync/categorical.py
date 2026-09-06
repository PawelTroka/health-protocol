"""Dated device classifications: observed counts, never numeric averages."""

from collections import Counter, defaultdict
from .monthly import MANAGED_START, iso_date


def validate(events):
    unique = {}
    for event in events:
        if not isinstance(event, dict) or event.get("provider") not in {"oura", "withings"}:
            raise ValueError("Invalid device classification provider.")
        if any(not isinstance(event.get(key), str) or not event[key] for key in ("id", "day", "metric", "value")):
            raise ValueError("Device classifications require an ID, date, marker and text result.")
        iso_date(event["day"])
        key = event["provider"], event["id"], event["metric"]
        if key in unique and unique[key] != event:
            raise ValueError("Conflicting device classifications share an identifier.")
        unique[key] = event
    return sorted(unique.values(), key=lambda event: (event["day"], event["provider"], event["metric"], event["id"]))


def merge(existing, incoming, providers, start, end, *, complete):
    if start < MANAGED_START or end < start:
        raise ValueError("Device classification imports begin July 2026.")
    incoming = [event for event in validate(incoming) if start <= iso_date(event["day"]) <= end]
    if any(event["provider"] not in providers for event in incoming):
        raise ValueError("Unexpected classification provider.")
    def identity(event):
        key = event["day"] if event["provider"] == "oura" else event["id"]
        return event["provider"], key, event["metric"]

    affected = {identity(event) for event in incoming}
    retained = [event for event in validate(existing)
                if not ((complete and event["provider"] in providers and start <= iso_date(event["day"]) <= end)
                        or identity(event) in affected)]
    return validate(retained + incoming)


def aggregate(events, as_of):
    buckets = defaultdict(list)
    for event in validate(events):
        day = iso_date(event["day"])
        if MANAGED_START <= day <= as_of and not (event["provider"] == "oura" and day == as_of):
            buckets[(event["day"][:7], event["provider"], event["metric"])].append(event)
    months = {}
    for (month, provider, metric), observations in sorted(buckets.items()):
        # API collections can reference the same test in both measure and ECG.
        deduped = {(event.get("recorded_at", event["day"]), event["value"]): event for event in observations}
        observations = list(deduped.values())
        counts = dict(sorted(Counter(event["value"] for event in observations).items()))
        days = {event["day"] for event in observations}
        months.setdefault(month, {})[metric] = {
            "provider": provider, "unit": "Status", "aggregation": "observed_classification_counts",
            "counts": counts, "n_records": len(observations), "n_days": len(days),
            "first_day": min(days), "last_day": max(days),
            "value": "; ".join(f"{label}: {count}" for label, count in counts.items()),
        }
    return months
