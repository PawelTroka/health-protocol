"""Bounded, read-only fetches; dates are inclusive Europe/Warsaw calendar days.

Oura endpoint/pagination reference: https://cloud.ouraring.com/v2/docs
Withings schemas: https://developer.withings.com/openapi.yaml
Health collections are read on demand. Endpoint access gaps remain explicit in
the returned source metadata; transport/server failures never publish partial data.
"""

from datetime import date, datetime, time, timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import auth


MAX_PAGES = 1000


class APIError(RuntimeError):
    """Safe fetch error; incomplete responses must not be applied."""

    def __init__(self, message, *, status=None):
        self.status = status
        super().__init__(message)


def _request(provider, url, *, form=None):
    token = auth.access_token(provider)
    try:
        return auth._request_json(url, form=form, headers={"Authorization": f"Bearer {token}"}, retries=2)
    except auth.HTTPStatusError as error:
        if error.status != 401:
            raise APIError(str(error), status=error.status) from None
    # One explicit refresh on expired/revoked access; refresh itself never retries.
    token = auth.access_token(provider, force_refresh=True)
    try:
        return auth._request_json(url, form=form, headers={"Authorization": f"Bearer {token}"}, retries=2)
    except auth.HTTPStatusError as error:
        raise APIError(str(error), status=error.status) from None


def _rows(value, key):
    rows = value.get(key)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise APIError("Provider returned malformed records; no incomplete data was imported.")
    return rows


OURA_ENDPOINTS = ("sleep", "daily_sleep", "daily_readiness", "daily_activity",
                  "daily_spo2", "daily_cardiovascular_age", "vO2_max",
                  "daily_stress", "daily_resilience", "heartrate", "workout", "session")


def _chunks(start, end):
    while start <= end:
        stop = min(end, start + timedelta(days=27))
        yield start, stop
        start = stop + timedelta(days=1)


def _oura_collection(endpoint, start, end):
    rows = []
    for first, last in _chunks(start, end):
        seen = set()
        params = {"start_date": first.isoformat(), "end_date": (last + timedelta(days=1)).isoformat()}
        if endpoint == "heartrate":
            zone = ZoneInfo("Europe/Warsaw")
            params = {"start_datetime": datetime.combine(first, time.min, zone).isoformat(),
                      "end_datetime": datetime.combine(last + timedelta(days=1), time.min, zone).isoformat()}
        for _ in range(MAX_PAGES):
            page = _request("oura", f"https://api.ouraring.com/v2/usercollection/{endpoint}?" + urlencode(params))
            rows.extend(_rows(page, "data"))
            next_token = page.get("next_token")
            if next_token is None or next_token == "":
                break
            if not isinstance(next_token, str) or next_token in seen:
                raise APIError("Oura pagination did not advance; no incomplete data was imported.")
            seen.add(next_token)
            params["next_token"] = next_token
        else:
            raise APIError("Oura exceeded the page limit; fetch a smaller date range.")
    return rows


def _oura(start, end):
    result, statuses = {}, {}
    for endpoint in OURA_ENDPOINTS:
        try:
            result[endpoint] = _oura_collection(endpoint, start, end)
        except APIError as error:
            if error.status not in (403, 404):
                raise
            statuses[endpoint] = {"status": "unavailable", "http_status": error.status}
        else:
            statuses[endpoint] = {"status": "complete", "rows": len(result[endpoint])}
    result["_sync"] = {"endpoint_status": statuses, "start": start.isoformat(), "end": end.isoformat()}
    return result


def _withings_measure(start, end):
    try:
        zone = ZoneInfo("Europe/Warsaw")
    except ZoneInfoNotFoundError:
        raise APIError("Europe/Warsaw timezone data is unavailable; install tzdata before API sync.") from None
    params = {"action": "getmeas", "category": 1,
              "startdate": int(datetime.combine(start, time.min, zone).timestamp()),
              "enddate": int(datetime.combine(end + timedelta(days=1), time.min, zone).timestamp()) - 1}
    rows, seen = [], {0}
    for _ in range(MAX_PAGES):
        payload = _request("withings", "https://wbsapi.withings.net/measure", form=params)
        if type(payload.get("status")) is not int or payload["status"] != 0 or not isinstance(payload.get("body"), dict):
            raise APIError("Withings reported an unsuccessful or malformed response; no data was imported.")
        page = payload["body"]
        rows.extend(_rows(page, "measuregrps"))
        more = page.get("more", 0)
        if more not in (0, 1, False, True):
            raise APIError("Withings returned an invalid pagination flag.")
        if not more:
            break
        offset = page.get("offset")
        if type(offset) is not int or offset <= params.get("offset", 0) or offset in seen:
            raise APIError("Withings pagination did not advance; no incomplete data was imported.")
        seen.add(offset)
        params["offset"] = offset
    else:
        raise APIError("Withings exceeded the page limit; fetch a smaller date range.")
    return {"measuregrps": rows}


def _withings_daily(endpoint, action, key, fields, start, end):
    rows = []
    for first, last in _chunks(start, end):
        params = {"action": action, "startdateymd": first.isoformat(), "enddateymd": last.isoformat(),
                  "data_fields": ",".join(fields)}
        seen = {0}
        for _ in range(MAX_PAGES):
            payload = _request("withings", "https://wbsapi.withings.net/v2/" + endpoint, form=params)
            if type(payload.get("status")) is not int or payload["status"] != 0 or not isinstance(payload.get("body"), dict):
                raise APIError(f"Withings {action} returned an unsuccessful response (code {payload.get('status') if type(payload.get('status')) is int else 'invalid'}).")
            page = payload["body"]
            rows.extend(_rows(page, key))
            more = page.get("more", 0)
            if more not in (0, 1, False, True):
                raise APIError("Withings returned an invalid pagination flag.")
            if not more:
                break
            offset = page.get("offset")
            if type(offset) is not int or offset <= params.get("offset", 0) or offset in seen:
                raise APIError("Withings pagination did not advance; no incomplete data was imported.")
            seen.add(offset)
            params["offset"] = offset
        else:
            raise APIError("Withings exceeded the page limit; fetch a smaller date range.")
    return rows


def _withings_signals(endpoint, start, end):
    zone = ZoneInfo("Europe/Warsaw")
    params = {"action": "list",
              "startdate": int(datetime.combine(start, time.min, zone).timestamp()),
              "enddate": int(datetime.combine(end + timedelta(days=1), time.min, zone).timestamp()) - 1}
    rows, seen = [], {0}
    for _ in range(MAX_PAGES):
        payload = _request("withings", "https://wbsapi.withings.net/v2/" + endpoint, form=params)
        if type(payload.get("status")) is not int or payload["status"] != 0 or not isinstance(payload.get("body"), dict):
            raise APIError(f"Withings {endpoint} returned an unsuccessful response.")
        page = payload["body"]
        rows.extend(_rows(page, "series"))
        more = page.get("more", 0)
        if more not in (0, 1, False, True):
            raise APIError("Withings returned an invalid pagination flag.")
        if not more:
            return rows
        offset = page.get("offset")
        if type(offset) is not int or offset <= params.get("offset", 0) or offset in seen:
            raise APIError("Withings pagination did not advance; no incomplete data was imported.")
        seen.add(offset)
        params["offset"] = offset
    raise APIError("Withings exceeded the page limit; fetch a smaller date range.")


def _withings(start, end):
    from .withings import WITHINGS_SLEEP_FIELDS, WITHINGS_ACTIVITY_FIELDS
    result = _withings_measure(start, end)
    statuses = {"measure": {"status": "complete", "rows": len(result["measuregrps"])}}
    for endpoint, action, key, fields in (("sleep", "getsummary", "series", WITHINGS_SLEEP_FIELDS),
                                        ("measure", "getactivity", "activities", WITHINGS_ACTIVITY_FIELDS)):
        try:
            result[key] = _withings_daily(endpoint, action, key, fields, start, end)
        except APIError as error:
            if error.status not in (403, 404):
                raise
            statuses[action] = {"status": "unavailable", "http_status": error.status}
        else:
            statuses[action] = {"status": "complete", "rows": len(result[key])}
    for endpoint in ("heart", "stetho"):
        try:
            result[endpoint + "_series"] = _withings_signals(endpoint, start, end)
        except APIError as error:
            if error.status not in (403, 404):
                raise
            statuses[endpoint] = {"status": "unavailable", "http_status": error.status}
        else:
            statuses[endpoint] = {"status": "complete", "rows": len(result[endpoint + "_series"])}
    result["_sync"] = {"endpoint_status": statuses, "start": start.isoformat(), "end": end.isoformat()}
    return result


def fetch(provider, start: date, end: date):
    """Return aggregated raw endpoint rows; caller handles provenance and filtering."""
    if type(start) is not date or type(end) is not date or start > end or end == date.max:
        raise APIError("Fetch requires a valid inclusive start/end date range.")
    if provider == "oura":
        return _oura(start, end)
    if provider == "withings":
        return _withings(start, end)
    raise APIError("Unknown provider; choose oura or withings.")
