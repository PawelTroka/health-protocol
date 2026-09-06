"""Reconcile API snapshots by endpoint coverage without erasing access gaps."""

from . import categorical
from .monthly import MANAGED_START, iso_date, validate_records
from .oura import OURA_ENDPOINTS


_WITHINGS_ENDPOINTS = {
    "measure": "measure", "measuregrps": "measure", "getmeas": "measure",
    "sleep": "getsummary", "series": "getsummary", "getsummary": "getsummary",
    "activity": "getactivity", "activities": "getactivity", "getactivity": "getactivity",
    "heart": "heart", "heart_series": "heart", "stetho": "stetho", "stetho_series": "stetho",
}
_LEGACY_OURA_SLEEP = {
    "Sleep Duration", "REM Sleep", "Deep Sleep", "Average Sleeping HR (Oura)",
    "Mean Nightly Lowest HR (Oura)", "Average HRV (Sleep)",
    "Respiratory Rate (Sleep)", "Sleep Efficiency", "Sleep Latency", "Time in Bed",
}


def infer_endpoint(record):
    """Return a coverage-status key only for a recognized source identity.

    Earlier parser records encoded the collection in their stable IDs. The
    original eleven-column Oura CSV is also a known daily sleep source; broader
    undocumented origins deliberately remain unknown and are only amended.
    """
    provider = record.get("provider")
    explicit = record.get("source_endpoint")
    if provider == "oura" and explicit in OURA_ENDPOINTS:
        return explicit
    if provider == "withings" and isinstance(explicit, str) and explicit in _WITHINGS_ENDPOINTS:
        return _WITHINGS_ENDPOINTS[explicit]
    identifier = record.get("id", "")
    parts = identifier.split(":") if isinstance(identifier, str) else []
    if provider == "oura":
        if len(parts) > 3 and parts[:2] in (["oura", "api"], ["oura", "event"]):
            if parts[2] in OURA_ENDPOINTS:
                return parts[2]
        if record.get("source_kind") == "csv":
            if record.get("metric") == "Sleep Score":
                return "daily_sleep"
            if record.get("metric") in _LEGACY_OURA_SLEEP:
                return "sleep"
    elif provider == "withings" and len(parts) > 2 and parts[0] == "withings":
        kind = parts[2] if parts[1] == "event" and len(parts) > 3 else parts[1]
        return _WITHINGS_ENDPOINTS.get(kind)
    return None


def _complete_endpoints(fetch_status, providers, start, end):
    if not isinstance(fetch_status, dict):
        raise ValueError("API coverage must be a dictionary of provider statuses.")
    complete = set()
    for provider in providers:
        coverage = fetch_status.get(provider, {})
        if not isinstance(coverage, dict):
            raise ValueError("API provider coverage must be an object.")
        for bound, expected in (("start", start), ("end", end)):
            if bound in coverage and iso_date(coverage[bound]) != expected:
                raise ValueError("API coverage dates do not match the requested import range.")
        statuses = coverage.get("endpoint_status", {})
        if not isinstance(statuses, dict):
            raise ValueError("API endpoint coverage must be an object.")
        for endpoint, status in statuses.items():
            if not isinstance(status, dict):
                raise ValueError("Each API endpoint status must be an object.")
            if provider == "withings":
                endpoint = _WITHINGS_ENDPOINTS.get(endpoint)
            elif endpoint not in OURA_ENDPOINTS:
                endpoint = None
            if endpoint is not None and status.get("status") == "complete":
                complete.add((provider, endpoint))
    return complete


def _amendment_key(record):
    # An Oura day's observation set replaces a CSV aggregate or prior samples
    # together. Withings events on the same day remain independent observations.
    identity = record["day"] if record["provider"] == "oura" else record["id"]
    return record["provider"], identity, record["metric"]


def merge_synced(existing, incoming, providers, start, end, fetch_status, *, classifications=False):
    """Replace successful endpoint snapshots and amend observations elsewhere.

    Explicitly complete but empty collections remove their old observations in
    the fetched range. Unavailable endpoints and unknown origins preserve their
    history unless an incoming observation explicitly replaces the same identity.
    Completeness is independent for each endpoint/provider. Date filtering and
    validation happen before reconciliation; this function performs no writes.
    """
    if start < MANAGED_START or end < start:
        raise ValueError("API reconciliation begins 2026-07-01 and requires an ordered range.")
    providers = set(providers)
    if not providers or not providers <= {"oura", "withings"}:
        raise ValueError("API reconciliation requires known providers.")
    validate = categorical.validate if classifications else validate_records
    existing = validate(existing)
    incoming = [record for record in validate(incoming) if start <= iso_date(record["day"]) <= end]
    if any(record["provider"] not in providers for record in incoming):
        raise ValueError("Incoming observations contain an unexpected provider.")
    complete = _complete_endpoints(fetch_status, providers, start, end)
    replacements = {_amendment_key(record) for record in incoming}
    retained = []
    for record in existing:
        in_range = start <= iso_date(record["day"]) <= end
        endpoint_complete = (record["provider"], infer_endpoint(record)) in complete
        if in_range and (endpoint_complete or _amendment_key(record) in replacements):
            continue
        retained.append(record)
    return validate(retained + incoming)
