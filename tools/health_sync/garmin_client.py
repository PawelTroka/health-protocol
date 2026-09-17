"""Optional personal Garmin Connect access with only DPAPI session persistence.

Uses the native in-memory session API in garminconnect 0.3.15. This is an
unofficial personal-account client, separate from Garmin's partner Health API.
The wrapper never uses token-file load/dump methods or retains a password.
"""

from contextlib import contextmanager
from datetime import date, timedelta
import getpass
from importlib import metadata
import json
import logging
import sys
import warnings

from . import auth
from .api import APIError


REQUIRED_VERSION = "0.3.15"
MAX_DAYS = 366
ENDPOINTS = {
    "daily_summary": "get_user_summary",
    "sleep": "get_sleep_data",
    "hrv": "get_hrv_data",
    "training_readiness": "get_training_readiness",
}
SESSION_KEYS = {"di_token", "di_refresh_token", "di_client_id"}


@contextmanager
def _quiet_client():
    """Upstream exceptions/logs can contain account or response information."""
    previous = logging.root.manager.disable
    logging.disable(max(previous, logging.CRITICAL))
    try:
        yield
    finally:
        logging.disable(previous)


def _library():
    try:
        installed = metadata.version("garminconnect")
        if installed != REQUIRED_VERSION:
            raise auth.AuthError("Install the pinned Garmin dependency with .\\tools\\Install-Garmin.ps1 first.")
        import garminconnect
        return garminconnect
    except (ImportError, metadata.PackageNotFoundError):
        raise auth.AuthError("Install the Garmin dependency with .\\tools\\Install-Garmin.ps1 first.") from None


def _session_data(value):
    if not isinstance(value, str) or len(value) > 64 * 1024:
        return None
    try:
        data = json.loads(value)
    except (TypeError, ValueError):
        return None
    if (not isinstance(data, dict) or set(data) != SESSION_KEYS
            or any(v is not None and not isinstance(v, str) for v in data.values())):
        return None
    return data


def status():
    """Return flags only; do not import the optional client or expose tokens."""
    vault = auth._load()
    data = _session_data(vault.get("garmin", {}).get("session_json"))
    valid = bool(data and data.get("di_token") and data.get("di_refresh_token") and data.get("di_client_id"))
    return {"configured": "garmin" in vault, "authorized": valid}


def _save_session(client, vault):
    """Persist rotations even when the following data/profile request failed."""
    try:
        serialized = client.client.dumps()
        data = _session_data(serialized)
    except Exception:
        raise auth.AuthError("Could not preserve the Garmin session securely; reconnect locally before retrying.") from None
    if not data or not all(data.get(key) for key in SESSION_KEYS):
        return False
    if vault.get("garmin", {}).get("session_json") != serialized:
        vault["garmin"] = {"session_json": serialized}
        auth._save(vault)
    return True


def _clear_credentials(client):
    if client is not None:
        client.username = None
        client.password = None
        client.prompt_mfa = None
        # MFA failures may leave response/session objects on the pinned client.
        # Its dedicated cleanup preserves tokens but drops that transient state.
        client.client._clear_mfa_pending_state()


def _secret(prompt):
    # GetPassWarning means getpass would fall back to visible stdin input.
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            value = getpass.getpass(prompt)
    except (getpass.GetPassWarning, EOFError, KeyboardInterrupt):
        raise auth.AuthError("Garmin connection cancelled; enter credentials in a local interactive terminal.") from None
    if not value or any(character in value for character in "\r\n"):
        raise auth.AuthError("Garmin credentials must be nonempty values entered locally.")
    return value


def _failure(error, library, *, connecting=False):
    """Translate only exception types/status numbers, never response content."""
    status_code = getattr(getattr(error, "response", None), "status_code", None)
    if isinstance(error, library.GarminConnectTooManyRequestsError) or status_code == 429:
        return "Garmin rate limit reached; wait before running the sync again."
    if isinstance(error, library.GarminConnectAuthenticationError) or status_code in (401, 403):
        return "Garmin authorization failed; reconnect locally with .\\tools\\Sync-Vitals.ps1 connect garmin."
    if connecting:
        return "Garmin connection did not complete; check the account and connection, then try again locally."
    return "Garmin data request did not complete; no partial results were imported."


def connect():
    """Authorize with hidden local prompts; persist only the encrypted session."""
    if not sys.stdin.isatty():
        raise auth.AuthError("Run .\\tools\\Sync-Vitals.ps1 connect garmin in a local interactive terminal.")
    with _quiet_client():
        library = _library()
    email = _secret("Garmin Connect email (hidden): ")
    password = _secret("Garmin Connect password (hidden): ")
    client = None
    try:
        with auth._locked(), _quiet_client():
            vault = auth._load()
            try:
                client = library.Garmin(email=email, password=password,
                                       prompt_mfa=lambda: _secret("Garmin verification code (hidden): "),
                                       retry_attempts=0)
                # Explicit inline JSON overrides GARMINTOKENS. Passing None can
                # activate upstream's environment-selected plaintext token file.
                client.login("{}")
                if not _save_session(client, vault):
                    raise auth.AuthError("Garmin did not return a reusable session; reconnect locally.")
            except auth.AuthError:
                raise
            except (Exception, KeyboardInterrupt) as error:
                raise auth.AuthError(_failure(error, library, connecting=True)) from None
            finally:
                if client is not None:
                    _save_session(client, vault)
    finally:
        email = password = None
        _clear_credentials(client)


def _validate_payload(endpoint, value):
    allowed = (dict, list) if endpoint == "training_readiness" else (dict,)
    if value is None and endpoint != "daily_summary":
        return
    if not isinstance(value, allowed) or isinstance(value, list) and any(not isinstance(row, dict) for row in value):
        raise APIError("Garmin returned malformed records; no incomplete data was imported.")
    try:
        size = len(json.dumps(value, allow_nan=False).encode("utf-8"))
    except (TypeError, ValueError, OverflowError):
        raise APIError("Garmin returned malformed records; no incomplete data was imported.") from None
    if size > auth.MAX_RESPONSE_BYTES:
        raise APIError("Garmin response exceeded the safe response size.")


def fetch(start: date, end: date):
    """Read bounded daily snapshots; caller defers current-day observations.

    Only optional-endpoint HTTP 404 means unavailable. A gap makes the entire
    endpoint incomplete so reconciliation retains existing cached observations;
    successful days around each gap remain usable amendments. All other request
    failures abort publication. Upstream uses bounded 15-second data requests
    and one refresh/retry on HTTP 401; additional data retries are disabled.
    """
    if (type(start) is not date or type(end) is not date or start > end
            or end == date.max or (end - start).days >= MAX_DAYS):
        raise APIError(f"Garmin fetch requires an inclusive date range of at most {MAX_DAYS} days.")
    with auth._locked(), _quiet_client():
        vault = auth._load()
        serialized = vault.get("garmin", {}).get("session_json")
        data = _session_data(serialized)
        if not data or not all(data.get(key) for key in SESSION_KEYS):
            raise auth.AuthError("Connect Garmin locally with .\\tools\\Sync-Vitals.ps1 connect garmin first.")
        library = _library()
        client = None
        try:
            client = library.Garmin(retry_attempts=0)
            client.login(serialized)
            _save_session(client, vault)
            result, statuses = {}, {}
            for endpoint, method_name in ENDPOINTS.items():
                rows = result[endpoint] = []
                unavailable_days = []
                day = start
                while day <= end:
                    try:
                        value = getattr(client, method_name)(day.isoformat())
                    except library.GarminConnectNotFoundError:
                        if endpoint == "daily_summary":
                            raise
                        unavailable_days.append(day.isoformat())
                        day += timedelta(days=1)
                        continue
                    finally:
                        _save_session(client, vault)
                    _validate_payload(endpoint, value)
                    rows.append({"day": day.isoformat(), "data": value})
                    day += timedelta(days=1)
                if unavailable_days:
                    statuses[endpoint] = {"status": "unavailable", "http_status": 404, "rows": len(rows),
                                          "unavailable_days": unavailable_days}
                else:
                    statuses[endpoint] = {"status": "complete", "rows": len(rows)}
            result["_sync"] = {"endpoint_status": statuses, "start": start.isoformat(), "end": end.isoformat()}
            return result
        except (auth.AuthError, APIError):
            raise
        except (Exception, KeyboardInterrupt) as error:
            raise APIError(_failure(error, library)) from None
        finally:
            if client is not None:
                try:
                    _save_session(client, vault)
                finally:
                    _clear_credentials(client)
