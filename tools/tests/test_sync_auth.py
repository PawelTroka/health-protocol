"""No real provider HTTP requests or real user credentials are used here."""

from contextlib import nullcontext
from copy import deepcopy
from datetime import date, datetime, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit

from tools.health_sync import api, auth


class MemoryVault(unittest.TestCase):
    def setUp(self):
        self.vault = {"oura": {"client_id": "test-client", "client_secret": "test-secret",
                              "redirect_uri": auth.redirect_uri("oura"), "access_token": "old-access",
                              "refresh_token": "old-refresh", "expires_at": 0}}
        self.saves = []
        self.addCleanup(patch.stopall)
        patch.object(auth, "_locked", side_effect=lambda: nullcontext()).start()
        patch.object(auth, "_load", side_effect=lambda: deepcopy(self.vault)).start()
        patch.object(auth, "_save", side_effect=self.save).start()
        # A stray HTTP call always fails rather than accessing any real account.
        patch.object(auth, "build_opener", side_effect=AssertionError("Unmocked HTTP call")).start()

    def save(self, value):
        self.vault = deepcopy(value)
        self.saves.append(deepcopy(value))

    def test_status_discloses_only_flags(self):
        self.assertEqual(auth.status(), {"oura": {"configured": True, "authorized": True},
                                        "withings": {"configured": False, "authorized": False}})
        serialized = json.dumps(auth.status())
        self.assertNotIn("test-secret", serialized)
        self.assertNotIn("old-refresh", serialized)

    def test_configure_rejects_external_callback_and_clears_previous_tokens(self):
        with self.assertRaises(auth.AuthError):
            auth.configure("oura", "new-id", "new-secret", "https://example.com/callback")
        self.assertFalse(self.saves)
        auth.configure("oura", "new-id", "new-secret")
        self.assertNotIn("refresh_token", self.vault["oura"])

    def test_refresh_rotates_and_saves_before_token_return(self):
        def exchange(provider, config):
            self.assertTrue(self.vault[provider]["refresh_uncertain"])
            self.assertEqual(config["refresh_token"], "old-refresh")
            return {"access_token": "new-access", "refresh_token": "new-refresh", "expires_at": time.time() + 3600}
        with patch.object(auth, "_token_request", side_effect=exchange) as request:
            self.assertEqual(auth.access_token("oura"), "new-access")
            self.assertEqual(self.vault["oura"]["refresh_token"], "new-refresh")
            self.assertNotIn("refresh_uncertain", self.vault["oura"])
            self.assertEqual(auth.access_token("oura"), "new-access")
            request.assert_called_once()
        self.assertEqual(len(self.saves), 2)

    def test_ambiguous_refresh_is_not_retried_on_next_run(self):
        with patch.object(auth, "_token_request", side_effect=auth.AuthError("Timeout")) as request:
            for _ in range(2):
                with self.assertRaises(auth.AuthError):
                    auth.access_token("oura")
            request.assert_called_once()
        self.assertTrue(self.vault["oura"]["refresh_uncertain"])
        self.assertFalse(auth.status()["oura"]["authorized"])

    def test_failed_persistence_prevents_returning_new_token(self):
        with patch.object(auth, "_token_request", return_value={"access_token": "new", "refresh_token": "rotated"}), \
             patch.object(auth, "_save", side_effect=[None, auth.AuthError("Cannot save")]):
            with self.assertRaises(auth.AuthError):
                auth.access_token("oura")

    def test_withings_token_exchange_signs_nonce_and_never_sends_secret(self):
        config = {**self.vault["oura"], "redirect_uri": auth.redirect_uri("withings")}
        responses = [{"status": 0, "body": {"nonce": "test-nonce"}},
                     {"status": 0, "body": {"access_token": "a", "refresh_token": "r", "expires_in": 10800}}]
        with patch.object(auth, "_request_json", side_effect=responses) as request:
            result = auth._token_request("withings", config)
        self.assertEqual(result["refresh_token"], "r")
        nonce_call, token_call = request.call_args_list
        self.assertEqual(nonce_call.args[0], "https://wbsapi.withings.net/v2/signature")
        token_form = token_call.kwargs["form"]
        self.assertEqual(token_form["action"], "requesttoken")
        self.assertEqual(token_form["grant_type"], "refresh_token")
        self.assertEqual(token_form["signature"], auth._withings_sign(token_form, "test-secret"))
        self.assertNotIn("client_secret", token_form)
        self.assertNotIn("retries", token_call.kwargs)

    def test_oauth_callback_rejects_wrong_state_then_accepts_real_state(self):
        opened = {}
        responses = []
        class FakeServer:
            def __init__(self, address, handler):
                self.handler = handler
                self.calls = 0
                self.address = address
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def handle_request(self):
                query = parse_qs(urlsplit(opened["url"]).query)
                callback = object.__new__(self.handler)
                self.calls += 1
                state = "wrong-state" if self.calls == 1 else query["state"][0]
                callback.path = "/callback/oura?" + urlencode({"code": "local-code", "state": state})
                callback.headers = {"Host": "localhost:8765"}
                callback.send_response = responses.append
                callback.send_header = lambda *args: None
                callback.end_headers = lambda: None
                callback.wfile = io.BytesIO()
                callback.do_GET()
                self.test_address = self.address
        def open_browser(url, **kwargs):
            opened["url"] = url
            return True
        with patch.object(auth, "HTTPServer", FakeServer), \
             patch.object(auth.webbrowser, "open", side_effect=open_browser), \
             patch.object(auth, "_token_request", return_value={"access_token": "new", "refresh_token": "new-r"}) as request:
            auth.authorize("oura", timeout=2)
        self.assertEqual(responses, [400, 200])
        self.assertGreaterEqual(len(parse_qs(urlsplit(opened["url"]).query)["state"][0]), 32)
        self.assertEqual(request.call_args.kwargs["code"], "local-code")
        self.assertEqual(self.vault["oura"]["refresh_token"], "new-r")


class StorageAndTransportTests(unittest.TestCase):
    def test_unsupported_os_fails_closed(self):
        with patch.object(auth.os, "name", "posix"):
            with self.assertRaises(auth.AuthError):
                auth._vault_path()

    @unittest.skipUnless(os.name == "nt", "DPAPI is Windows-only")
    def test_dpapi_roundtrip_stores_no_plaintext(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "credentials.dat"
            with patch.object(auth, "_vault_path", return_value=path):
                auth._save({"oura": {"client_secret": "synthetic-secret-do-not-use"}})
                self.assertNotIn(b"synthetic-secret-do-not-use", path.read_bytes())
                self.assertEqual(auth._load()["oura"]["client_secret"], "synthetic-secret-do-not-use")
                self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_read_retry_respects_retry_after_and_hides_http_body(self):
        failure = HTTPError("https://api.ouraring.com/test", 429, "private-response", {"Retry-After": "3"}, io.BytesIO(b"secret"))
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"data": []}'
        opener = MagicMock()
        opener.open.side_effect = [failure, response]
        with patch.object(auth, "build_opener", return_value=opener), patch.object(auth.time, "sleep") as sleep:
            self.assertEqual(auth._request_json("https://api.ouraring.com/test", retries=2), {"data": []})
        sleep.assert_called_once_with(3)
        self.assertEqual(opener.open.call_count, 2)

    def test_token_request_transport_never_retries_ambiguous_failure(self):
        opener = MagicMock()
        opener.open.side_effect = URLError("could contain credentials")
        with patch.object(auth, "build_opener", return_value=opener):
            with self.assertRaises(auth.AuthError) as raised:
                auth._request_json("https://api.ouraring.com/oauth/token", form={"refresh_token": "secret"})
        self.assertEqual(opener.open.call_count, 1)
        self.assertNotIn("credentials", str(raised.exception))

    def test_redirects_and_long_retry_delays_are_rejected(self):
        self.assertIsNone(auth._NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com"))
        with self.assertRaises(auth.AuthError):
            auth._retry_delay("3600", 0)


class APITests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(auth, "build_opener", side_effect=AssertionError("Unmocked HTTP call")).start()

    def test_oura_follows_pages_and_preserves_endpoint_rows(self):
        pages = [{"data": [{"id": "sleep1"}], "next_token": "next"},
                 {"data": [{"id": "sleep2"}], "next_token": None},
                 {"data": [{"id": "daily1"}], "next_token": None}]
        with patch.object(api, "_request", side_effect=pages) as request:
            result = api.fetch("oura", date(2026, 8, 1), date(2026, 9, 6))
        self.assertEqual(len(result["sleep"]), 2)
        self.assertEqual(len(result["daily_sleep"]), 1)
        self.assertIn("next_token=next", request.call_args_list[1].args[1])
        self.assertIn("end_date=2026-09-07", request.call_args_list[0].args[1])

    def test_repeated_oura_cursor_fails_without_returning_partial_data(self):
        with patch.object(api, "_request", return_value={"data": [], "next_token": "same"}) as request:
            with self.assertRaises(api.APIError):
                api.fetch("oura", date(2026, 8, 1), date(2026, 9, 6))
        self.assertEqual(request.call_count, 2)

    def test_withings_offset_pagination_and_inclusive_warsaw_bounds(self):
        pages = [{"status": 0, "body": {"measuregrps": [{"grpid": 1}], "more": 1, "offset": 200}},
                 {"status": 0, "body": {"measuregrps": [{"grpid": 2}], "more": 0}}]
        captured = []
        def request(provider, url, form):
            captured.append(dict(form))
            return pages.pop(0)
        with patch.object(api, "_request", side_effect=request):
            result = api.fetch("withings", date(2026, 8, 1), date(2026, 9, 6))
        self.assertEqual(len(result["measuregrps"]), 2)
        self.assertEqual(captured[0]["category"], 1)
        self.assertNotIn("meastypes", captured[0])
        self.assertEqual(captured[1]["offset"], 200)
        self.assertEqual(captured[0]["startdate"], int(datetime(2026, 7, 31, 22, tzinfo=timezone.utc).timestamp()))
        self.assertEqual(captured[0]["enddate"], int(datetime(2026, 9, 6, 21, 59, 59, tzinfo=timezone.utc).timestamp()))

    def test_withings_status_error_or_stuck_offset_fails_closed(self):
        for payload in [{"status": 401}, {"status": False, "body": {}},
                        {"status": 0, "body": {"measuregrps": [], "more": 1, "offset": 0}}]:
            with self.subTest(payload=payload), patch.object(api, "_request", return_value=payload):
                with self.assertRaises(api.APIError):
                    api.fetch("withings", date(2026, 8, 1), date(2026, 9, 6))

    def test_http_401_refreshes_only_once(self):
        with patch.object(auth, "access_token", side_effect=["old", "new"]) as token, \
             patch.object(auth, "_request_json", side_effect=[auth.HTTPStatusError(401), {"data": []}]) as request:
            self.assertEqual(api._request("oura", "https://api.ouraring.com/test"), {"data": []})
        self.assertEqual(token.call_args_list[1].kwargs, {"force_refresh": True})
        self.assertEqual(request.call_args_list[1].kwargs["headers"]["Authorization"], "Bearer new")


if __name__ == "__main__":
    unittest.main()
