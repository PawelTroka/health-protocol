"""Bounded, read-only fetches; dates are inclusive Europe/Warsaw calendar days.

Oura endpoint/pagination reference: https://cloud.ouraring.com/v2/docs
Withings schemas: https://developer.withings.com/openapi.yaml
Only sleep/daily_sleep and real Withings measurements are requested; no writes,
notifications, account metadata, or automatic background runs are performed.
"""

from datetime import date, datetime, time, timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import auth


MAX_PAGES = 1000


class APIError(RuntimeError):
    """Safe fetch error; incomplete responses must not be applied."""


def _request(provider, url, *, form=None):
    token = auth.access_token(provider)
    try:
        return auth._request_json(url, form=form, headers={"Authorization": f"Bearer {token}"}, retries=2)
    except auth.HTTPStatusError as error:
        if error.status != 401:
            raise APIError(str(error)) from None
    # One explicit refresh on expired/revoked access; refresh itself never retries.
    token = auth.access_token(provider, force_refresh=True)
    try:
        return auth._request_json(url, form=form, headers={"Authorization": f"Bearer {token}"}, retries=2)
    except auth.HTTPStatusError as error:
        raise APIError(str(error)) from None


def _rows(value, key):
    rows = value.get(key)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise APIError("Provider returned malformed records; no incomplete data was imported.")
    return rows


def _oura(start, end):
    result = {}
    for endpoint in ("sleep", "daily_sleep"):
        rows, seen = [], set()
        # Include the boundary day regardless of upstream end_date inclusivity;
        # the parser filters exact record dates to the requested calendar range.
        params = {"start_date": start.isoformat(), "end_date": (end + timedelta(days=1)).isoformat()}
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
        result[endpoint] = rows
    return result


def _withings(start, end):
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


def fetch(provider, start: date, end: date):
    """Return aggregated raw endpoint rows; caller handles provenance and filtering."""
    if type(start) is not date or type(end) is not date or start > end or end == date.max:
        raise APIError("Fetch requires a valid inclusive start/end date range.")
    if provider == "oura":
        return _oura(start, end)
    if provider == "withings":
        return _withings(start, end)
    raise APIError("Unknown provider; choose oura or withings.")
