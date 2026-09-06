"""Personal OAuth setup with Windows user-bound DPAPI storage, never tracked secrets.

Register the exact localhost callback shown by ``redirect_uri(provider)`` in the
provider dashboard, configure using a local hidden prompt, then call authorize.
Oura: https://cloud.ouraring.com/docs/authentication
Withings: https://developer.withings.com/developer-guide/v3/integration-guide/
public-health-data-api/get-access/access-and-refresh-tokens-no-recover/
"""

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
from email.utils import parsedate_to_datetime
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import math
import os
from pathlib import Path
import secrets
import socket
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import webbrowser


PROVIDERS = {
    "oura": {"authorize": "https://cloud.ouraring.com/oauth/authorize",
             "token": "https://api.ouraring.com/oauth/token", "scope": "daily heartrate workout session spo2 heart_health stress"},
    "withings": {"authorize": "https://account.withings.com/oauth2_user/authorize2",
                 "token": "https://wbsapi.withings.net/v2/oauth2", "scope": "user.metrics,user.activity"},
}
REQUEST_TIMEOUT = 20
MAX_RESPONSE_BYTES = 32 * 1024 * 1024


class AuthError(RuntimeError):
    """Safe, credential-free error suitable for display by the CLI."""


class HTTPStatusError(AuthError):
    def __init__(self, status):
        self.status = status
        super().__init__(f"Provider request failed (HTTP {status}).")


def _provider(provider):
    if provider not in PROVIDERS:
        raise AuthError("Unknown provider; choose oura or withings.")
    return PROVIDERS[provider]


def redirect_uri(provider):
    _provider(provider)
    return f"http://localhost:8765/callback/{provider}"


def _vault_path():
    if os.name != "nt":
        raise AuthError("Credential storage requires Windows user-bound DPAPI; no plaintext fallback is enabled.")
    return Path(__file__).resolve().parents[1] / ".secrets" / "credentials.dat"


def _dpapi(data, *, decrypt=False):
    if os.name != "nt":
        raise AuthError("Windows user-bound DPAPI is required for credentials.")

    class Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    destination = Blob()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    function = crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    # CRYPTPROTECT_UI_FORBIDDEN; intentionally do not set LOCAL_MACHINE.
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(destination)):
        raise AuthError("Windows could not protect/unlock credentials for this user.")
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(destination.pbData)


def _load():
    path = _vault_path()
    if not path.exists():
        return {}
    try:
        value = json.loads(_dpapi(path.read_bytes(), decrypt=True))
        if not isinstance(value, dict) or any(not isinstance(v, dict) for v in value.values()):
            raise ValueError
        return value
    except (OSError, ValueError, UnicodeError):
        raise AuthError("The encrypted credential store could not be read; no credentials were changed.") from None


def _save(value):
    path = _vault_path()
    encrypted = _dpapi(json.dumps(value, allow_nan=False).encode("utf-8"))
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix="credentials-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encrypted)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError:
        raise AuthError("Could not atomically save encrypted credentials; authorization may need to be repeated.") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def _locked():
    """Serialize rotations across CLI processes; never rotate one token twice."""
    path = _vault_path().with_suffix(".lock")
    import msvcrt
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        deadline = time.monotonic() + 5
        while True:
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise AuthError("Another sync is using credentials; try again when it finishes.") from None
                time.sleep(0.1)
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def status():
    """Return only configuration/authorization flags, never identifiers or tokens."""
    vault = _load()
    return {provider: {
        "configured": bool(vault.get(provider, {}).get("client_id") and vault.get(provider, {}).get("client_secret")),
        "authorized": bool(vault.get(provider, {}).get("refresh_token") and not vault.get(provider, {}).get("refresh_uncertain")),
    } for provider in PROVIDERS}


def configure(provider, client_id, client_secret, redirect_uri=None):
    """Store locally entered app credentials; changing them clears previous tokens."""
    _provider(provider)
    expected_uri = globals()["redirect_uri"](provider)
    if redirect_uri is not None and redirect_uri != expected_uri:
        raise AuthError(f"Register this exact callback URL: {expected_uri}")
    if any(not isinstance(v, str) or not v.strip() or any(c in v for c in "\r\n") for v in (client_id, client_secret)):
        raise AuthError("Client ID and secret must be nonempty single-line values entered locally.")
    with _locked():
        vault = _load()
        vault[provider] = {"client_id": client_id.strip(), "client_secret": client_secret.strip(),
                           "redirect_uri": expected_uri}
        _save(vault)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _retry_delay(header, attempt):
    if header:
        try:
            delay = float(header)
        except (ValueError, TypeError):
            try:
                delay = parsedate_to_datetime(header).timestamp() - time.time()
            except (ValueError, TypeError, OverflowError):
                delay = 2 ** attempt
        if not math.isfinite(delay) or delay > 60:
            raise AuthError("Provider requested a longer retry delay; run sync again later.")
        return max(0, delay)
    return 2 ** attempt


def _request_json(url, *, form=None, headers=None, retries=0):
    """HTTPS only, no redirects or response bodies in errors; retries only for reads."""
    if urlsplit(url).scheme != "https":
        raise AuthError("Provider requests must use HTTPS.")
    body = urlencode(form).encode("utf-8") if form is not None else None
    request_headers = {"Accept": "application/json", **(headers or {})}
    if body is not None:
        request_headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = Request(url, data=body, headers=request_headers)
    for attempt in range(retries + 1):
        try:
            with build_opener(_NoRedirect()).open(request, timeout=REQUEST_TIMEOUT) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise AuthError("Provider response exceeded the safe response size.")
                value = json.loads(raw)
                if not isinstance(value, dict):
                    raise AuthError("Provider returned an unexpected JSON structure.")
                return value
        except HTTPError as error:
            if attempt < retries and (error.code == 429 or 500 <= error.code <= 599):
                delay = _retry_delay(error.headers.get("Retry-After") if error.headers else None, attempt)
                error.close()
                time.sleep(delay)
                continue
            code = error.code
            error.close()
            raise HTTPStatusError(code) from None
        except (URLError, TimeoutError, OSError):
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            raise AuthError("Provider request did not complete; check the connection and try again.") from None
        except (ValueError, UnicodeError):
            raise AuthError("Provider returned invalid JSON; no data was imported.") from None


def _withings_body(payload):
    if type(payload.get("status")) is not int or payload["status"] != 0 or not isinstance(payload.get("body"), dict):
        raise AuthError("Withings reported an unsuccessful or malformed response.")
    return payload["body"]


def _withings_sign(params, client_secret):
    fields = ("action", "client_id", "nonce" if "nonce" in params else "timestamp")
    message = ",".join(str(params[k]) for k in fields)
    return hmac.new(client_secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def _token_request(provider, config, *, code=None):
    params = {"client_id": config["client_id"],
              "grant_type": "authorization_code" if code is not None else "refresh_token"}
    if code is not None:
        params.update(code=code, redirect_uri=config["redirect_uri"])
    else:
        params["refresh_token"] = config["refresh_token"]
    if provider == "withings":
        nonce_params = {"action": "getnonce", "client_id": config["client_id"], "timestamp": int(time.time())}
        nonce_params["signature"] = _withings_sign(nonce_params, config["client_secret"])
        nonce = _withings_body(_request_json("https://wbsapi.withings.net/v2/signature", form=nonce_params)).get("nonce")
        if not isinstance(nonce, str) or not nonce:
            raise AuthError("Withings did not return an authorization nonce.")
        params.update(action="requesttoken", nonce=nonce)
        params["signature"] = _withings_sign(params, config["client_secret"])
    else:
        params["client_secret"] = config["client_secret"]
    # Tokens rotate: no automatic retry, including timeout/429/5xx ambiguity.
    value = _request_json(_provider(provider)["token"], form=params)
    if provider == "withings":
        value = _withings_body(value)
    if str(value.get("token_type", "bearer")).lower() != "bearer":
        raise AuthError("Provider returned an unsupported token type.")
    if any(not isinstance(value.get(k), str) or not value[k] for k in ("access_token", "refresh_token")):
        raise AuthError("Provider did not return both required OAuth tokens; authorize again.")
    try:
        lifetime = float(value["expires_in"])
        if not math.isfinite(lifetime) or lifetime <= 0:
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise AuthError("Provider returned invalid token expiry; authorize again.") from None
    result = {k: value[k] for k in ("access_token", "refresh_token")}
    result["expires_at"] = time.time() + lifetime
    return result


def access_token(provider, force_refresh=False):
    """Persist a rotated token before returning it to any data request."""
    _provider(provider)
    with _locked():
        vault = _load()
        config = vault.get(provider, {})
        if not config.get("client_id") or not config.get("client_secret"):
            raise AuthError(f"Run .\\tools\\Sync-Vitals.ps1 connect {provider} from the repository root to configure API access first.")
        if not config.get("refresh_token") or config.get("refresh_uncertain"):
            raise AuthError(f"Authorize {provider} locally before fetching data.")
        if not force_refresh and config.get("access_token") and config.get("expires_at", 0) > time.time() + 60:
            return config["access_token"]
        # If the process dies after a request was sent, never blindly reuse an old
        # refresh token on the next run. A new browser authorization recovers it.
        config["refresh_uncertain"] = True
        _save(vault)
        try:
            tokens = _token_request(provider, config)
        except AuthError:
            raise AuthError(f"{provider} token refresh did not complete safely; authorize locally again before retrying.") from None
        config.update(tokens)
        config.pop("refresh_uncertain", None)
        _save(vault)
        return config["access_token"]


def authorization_url(provider, state):
    """Build a consent URL; the caller must generate and verify an ephemeral state."""
    spec = _provider(provider)
    config = _load().get(provider, {})
    if not config.get("client_id") or not config.get("client_secret"):
        raise AuthError(f"Configure {provider} locally before authorizing.")
    return spec["authorize"] + "?" + urlencode({"response_type": "code", "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"], "scope": spec["scope"], "state": state})


def authorize(provider, *, timeout=180):
    """Open provider consent and accept one verified callback on loopback only."""
    _provider(provider)
    if not 1 <= timeout <= 600:
        raise AuthError("Authorization timeout must be between 1 and 600 seconds.")
    config = _load().get(provider, {})
    if config.get("redirect_uri") != redirect_uri(provider):
        raise AuthError(f"Configure {provider} locally with the exact registered callback first.")
    state = secrets.token_urlsafe(32)
    url = authorization_url(provider, state)
    result = {}
    callback_path = urlsplit(redirect_uri(provider)).path

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log callback URLs, codes, tokens, or query strings.

        def do_GET(self):
            parsed = urlsplit(self.path)
            query = parse_qs(parsed.query, keep_blank_values=True)
            valid = (parsed.path == callback_path and self.headers.get("Host") == "localhost:8765"
                     and len(query.get("state", [])) == 1
                     and secrets.compare_digest(query["state"][0], state))
            if not valid:
                status_code, message = 400, "Invalid authorization callback. Return to the terminal."
            elif query.get("error"):
                result["error"] = True
                status_code, message = 400, "Authorization was declined. Return to the terminal."
            elif len(query.get("code", [])) != 1 or not query["code"][0]:
                status_code, message = 400, "Authorization code is missing. Return to the terminal."
            else:
                result["code"] = query["code"][0]
                status_code, message = 200, "Callback received. Return to the terminal to confirm authorization completed."
            self.send_response(status_code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            self.wfile.write(message.encode())

    class LoopbackServer(HTTPServer):
        # Windows rejects SO_REUSEADDR together with SO_EXCLUSIVEADDRUSE.
        allow_reuse_address = False

        def server_bind(self):
            if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            super().server_bind()

        def get_request(self):
            connection, address = super().get_request()
            connection.settimeout(2)
            return connection, address

        def handle_error(self, request, client_address):
            pass  # Do not print a callback-containing traceback.

    try:
        server = LoopbackServer(("127.0.0.1", 8765), Callback)
    except OSError:
        raise AuthError("Cannot bind the localhost callback on port 8765; close the conflicting process and retry.") from None
    with server:
        server.timeout = 1
        if not webbrowser.open(url, new=1, autoraise=True):
            raise AuthError("Could not open the local browser; set a default browser and run authorize again.")
        deadline = time.monotonic() + timeout
        while not result and time.monotonic() < deadline:
            server.handle_request()
    if result.get("error"):
        raise AuthError("Authorization was declined; no tokens were changed.")
    if not result.get("code"):
        raise AuthError("Authorization timed out; run authorize again locally.")
    with _locked():
        vault = _load()
        current = vault.get(provider, {})
        if any(current.get(k) != config.get(k) for k in ("client_id", "client_secret", "redirect_uri")):
            raise AuthError("App configuration changed during consent; run authorize again.")
        current.update(_token_request(provider, current, code=result["code"]))
        current.pop("refresh_uncertain", None)
        _save(vault)
