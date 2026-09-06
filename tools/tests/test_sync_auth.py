"""No real provider HTTP requests or real user credentials are used here."""

from contextlib import nullcontext
from copy import deepcopy
from datetime import date, datetime, timezone
import io
import json
import os
from pathlib import Path
import socket
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
        servers = []
        class FakeServer:
            def __init__(self, address, handler):
                self.handler = handler
                self.calls = 0
                self.address = address
                self.socket = MagicMock()
                servers.append(self)
                self.server_bind()
            def server_bind(self):
                pass
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
        self.assertEqual(servers[0].address, ("127.0.0.1", 8765))
        self.assertFalse(servers[0].allow_reuse_address)
        calls = servers[0].socket.setsockopt.call_args_list
        self.assertFalse(any(call.args[1] == socket.SO_REUSEADDR for call in calls))
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            servers[0].socket.setsockopt.assert_called_once_with(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)

    def test_authorization_requests_expanded_health_scopes_without_personal_data(self):
        query = parse_qs(urlsplit(auth.authorization_url("oura", "synthetic-state")).query)
        self.assertEqual(set(query["scope"][0].split()),
                         {"daily", "heartrate", "workout", "session", "spo2", "heart_health", "stress"})
        self.assertNotIn("client_secret", query)
        self.assertEqual(query["redirect_uri"], ["http://localhost:8765/callback/oura"])
        self.assertEqual(set(auth.PROVIDERS["withings"]["scope"].split(",")), {"user.metrics", "user.activity"})


class StorageAndTransportTests(unittest.TestCase):
    def test_unsupported_os_fails_closed(self):
        with patch.object(auth.os, "name", "posix"):
            with self.assertRaises(auth.AuthError):
                auth._vault_path()

    @unittest.skipUnless(os.name == "nt", "DPAPI is Windows-only")
    def test_vault_path_is_ignored_tools_secrets_without_reading_credentials(self):
        expected = Path(auth.__file__).resolve().parents[1] / ".secrets" / "credentials.dat"
        self.assertEqual(auth._vault_path(), expected)

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

    def test_repeated_server_error_stops_after_bounded_read_retries(self):
        opener = MagicMock()
        opener.open.side_effect = [HTTPError("https://api.ouraring.com/test", 503, "private", {}, None) for _ in range(3)]
        with patch.object(auth, "build_opener", return_value=opener), patch.object(auth.time, "sleep") as sleep:
            with self.assertRaises(auth.HTTPStatusError) as raised:
                auth._request_json("https://api.ouraring.com/test", retries=2)
        self.assertEqual(raised.exception.status, 503)
        self.assertEqual(opener.open.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertNotIn("private", str(raised.exception))


class APITests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.object(auth, "access_token", return_value="synthetic-access-token").start()
        patch.object(auth, "build_opener", side_effect=AssertionError("Unmocked HTTP call")).start()

    def test_oura_collection_follows_pages_and_preserves_rows(self):
        pages = [{"data": [{"id": "sleep1"}], "next_token": "next"},
                 {"data": [{"id": "sleep2"}], "next_token": None}]
        with patch.object(api, "_request", side_effect=pages) as request:
            result = api._oura_collection("sleep", date(2026, 9, 1), date(2026, 9, 6))
        self.assertEqual([row["id"] for row in result], ["sleep1", "sleep2"])
        self.assertIn("next_token=next", request.call_args_list[1].args[1])
        self.assertIn("end_date=2026-09-07", request.call_args_list[0].args[1])

    def test_oura_fetches_twelve_collections_in_bounded_28_day_chunks(self):
        captured = []
        def request(provider, url):
            endpoint = urlsplit(url).path.rsplit("/", 1)[1]
            query = parse_qs(urlsplit(url).query)
            captured.append((provider, endpoint, query))
            return {"data": [{"id": f"{endpoint}:{len(captured)}"}], "next_token": None}
        with patch.object(api, "_request", side_effect=request):
            result = api.fetch("oura", date(2026, 7, 1), date(2026, 9, 6))
        expected = {"sleep", "daily_sleep", "daily_readiness", "daily_activity", "daily_spo2",
                    "daily_cardiovascular_age", "vO2_max", "daily_stress", "daily_resilience",
                    "heartrate", "workout", "session"}
        self.assertEqual(set(result) - {"_sync"}, expected)
        self.assertEqual(len(captured), 36)
        self.assertEqual(result["_sync"]["start"], "2026-07-01")
        self.assertEqual(result["_sync"]["end"], "2026-09-06")
        for endpoint in expected:
            self.assertEqual(len(result[endpoint]), 3)
            self.assertEqual(result["_sync"]["endpoint_status"][endpoint], {"status": "complete", "rows": 3})
        normal = [query for _, endpoint, query in captured if endpoint == "sleep"]
        self.assertEqual([(q["start_date"][0], q["end_date"][0]) for q in normal],
                         [("2026-07-01", "2026-07-29"), ("2026-07-29", "2026-08-26"), ("2026-08-26", "2026-09-07")])
        heart = [query for _, endpoint, query in captured if endpoint == "heartrate"]
        self.assertEqual(heart[0]["start_datetime"], ["2026-07-01T00:00:00+02:00"])
        self.assertEqual(heart[-1]["end_datetime"], ["2026-09-07T00:00:00+02:00"])
        self.assertNotIn("start_date", heart[0])

    def test_oura_optional_access_gap_is_explicit_and_drops_partial_endpoint_rows(self):
        def collection(endpoint, start, end):
            if endpoint == "daily_spo2":
                raise api.APIError("Forbidden", status=403)
            if endpoint == "daily_resilience":
                raise api.APIError("Absent", status=404)
            return []
        with patch.object(api, "_oura_collection", side_effect=collection):
            result = api.fetch("oura", date(2026, 7, 1), date(2026, 9, 6))
        self.assertNotIn("daily_spo2", result)
        self.assertNotIn("daily_resilience", result)
        statuses = result["_sync"]["endpoint_status"]
        self.assertEqual(statuses["daily_spo2"], {"status": "unavailable", "http_status": 403})
        self.assertEqual(statuses["daily_resilience"], {"status": "unavailable", "http_status": 404})
        self.assertEqual(statuses["sleep"], {"status": "complete", "rows": 0})

    def test_transport_server_or_auth_failure_never_becomes_optional_gap(self):
        for failure in (auth.AuthError("Timeout"), api.APIError("Server", status=503),
                        api.APIError("Unauthorized", status=401)):
            with self.subTest(failure=failure), patch.object(api, "_oura_collection", side_effect=[[], failure]):
                with self.assertRaises(type(failure)):
                    api.fetch("oura", date(2026, 7, 1), date(2026, 9, 6))

    def test_repeated_oura_cursor_fails_without_returning_partial_data(self):
        with patch.object(api, "_request", return_value={"data": [], "next_token": "same"}) as request:
            with self.assertRaises(api.APIError):
                api.fetch("oura", date(2026, 8, 1), date(2026, 9, 6))
        self.assertEqual(request.call_count, 2)

    def test_oura_page_limit_fails_closed(self):
        with patch.object(api, "MAX_PAGES", 2), \
             patch.object(api, "_request", side_effect=[{"data": [], "next_token": "a"}, {"data": [], "next_token": "b"}]):
            with self.assertRaisesRegex(api.APIError, "page limit"):
                api._oura_collection("sleep", date(2026, 7, 1), date(2026, 7, 1))

    def test_withings_offset_pagination_and_inclusive_warsaw_bounds(self):
        pages = [{"status": 0, "body": {"measuregrps": [{"grpid": 1}], "more": 1, "offset": 200}},
                 {"status": 0, "body": {"measuregrps": [{"grpid": 2}], "more": 0}}]
        captured = []
        def request(provider, url, form):
            captured.append(dict(form))
            return pages.pop(0)
        with patch.object(api, "_request", side_effect=request):
            result = api._withings_measure(date(2026, 8, 1), date(2026, 9, 6))
        self.assertEqual(len(result["measuregrps"]), 2)
        self.assertEqual(captured[0]["category"], 1)
        self.assertNotIn("meastypes", captured[0])
        self.assertEqual(captured[1]["offset"], 200)
        self.assertEqual(captured[0]["startdate"], int(datetime(2026, 7, 31, 22, tzinfo=timezone.utc).timestamp()))
        self.assertEqual(captured[0]["enddate"], int(datetime(2026, 9, 6, 21, 59, 59, tzinfo=timezone.utc).timestamp()))

    def test_withings_fetches_measure_sleep_and_activity_and_keeps_coverage(self):
        with patch.object(api, "_withings_measure", return_value={"measuregrps": [{"grpid": 1}]}), \
             patch.object(api, "_withings_daily", side_effect=[[{"id": "sleep1"}], [{"date": "2026-07-01"}]]) as daily, \
             patch.object(api, "_withings_signals", return_value=[]) as signals:
            result = api.fetch("withings", date(2026, 7, 1), date(2026, 9, 6))
        self.assertEqual(set(result), {"measuregrps", "series", "activities", "heart_series", "stetho_series", "_sync"})
        self.assertEqual(daily.call_args_list[0].args[:3], ("sleep", "getsummary", "series"))
        self.assertEqual(daily.call_args_list[1].args[:3], ("measure", "getactivity", "activities"))
        self.assertIn("apnea_hypopnea_index", daily.call_args_list[0].args[3])
        self.assertIn("steps", daily.call_args_list[1].args[3])
        self.assertEqual(set(result["_sync"]["endpoint_status"]), {"measure", "getsummary", "getactivity", "heart", "stetho"})
        self.assertEqual([call.args[0] for call in signals.call_args_list], ["heart", "stetho"])

    def test_withings_daily_chunks_and_offsets_have_no_missing_days(self):
        captured = []
        def request(provider, url, *, form):
            captured.append(dict(form))
            more = 0 if "offset" in form else 1
            return {"status": 0, "body": {"series": [{"id": str(len(captured))}], "more": more, "offset": 100}}
        with patch.object(api, "_request", side_effect=request):
            rows = api._withings_daily("sleep", "getsummary", "series", ["apnea_hypopnea_index"],
                                       date(2026, 7, 1), date(2026, 9, 6))
        self.assertEqual(len(rows), 6)
        first_pages = captured[::2]
        self.assertEqual([(p["startdateymd"], p["enddateymd"]) for p in first_pages],
                         [("2026-07-01", "2026-07-28"), ("2026-07-29", "2026-08-25"), ("2026-08-26", "2026-09-06")])
        self.assertTrue(all("offset" not in page for page in first_pages))
        self.assertTrue(all(page["offset"] == 100 for page in captured[1::2]))

    def test_withings_optional_gaps_preserve_successful_measurements(self):
        with patch.object(api, "_withings_measure", return_value={"measuregrps": [{"grpid": 1}]}), \
             patch.object(api, "_withings_daily", side_effect=[api.APIError("Forbidden", status=403), []]), \
             patch.object(api, "_withings_signals", side_effect=[[], api.APIError("Absent", status=404)]):
            result = api.fetch("withings", date(2026, 7, 1), date(2026, 9, 6))
        self.assertEqual(result["measuregrps"], [{"grpid": 1}])
        self.assertNotIn("series", result)
        self.assertEqual(result["activities"], [])
        self.assertEqual(result["_sync"]["endpoint_status"]["getsummary"], {"status": "unavailable", "http_status": 403})
        self.assertEqual(result["_sync"]["endpoint_status"]["getactivity"], {"status": "complete", "rows": 0})
        self.assertEqual(result["_sync"]["endpoint_status"]["stetho"], {"status": "unavailable", "http_status": 404})
        self.assertNotIn("stetho_series", result)

    def test_withings_signals_paginate_metadata_without_raw_waveform_requests(self):
        for endpoint in ("heart", "stetho"):
            pages = [{"status": 0, "body": {"series": [{"id": 1}], "more": 1, "offset": 100}},
                     {"status": 0, "body": {"series": [{"id": 2}], "more": 0}}]
            captured = []
            def request(provider, url, *, form):
                captured.append((url, dict(form)))
                return pages.pop(0)
            with self.subTest(endpoint=endpoint), patch.object(api, "_request", side_effect=request):
                rows = api._withings_signals(endpoint, date(2026, 7, 1), date(2026, 9, 6))
            self.assertEqual(rows, [{"id": 1}, {"id": 2}])
            self.assertTrue(all(url == f"https://wbsapi.withings.net/v2/{endpoint}" for url, _ in captured))
            self.assertTrue(all(form["action"] == "list" for _, form in captured))
            self.assertNotIn("offset", captured[0][1])
            self.assertEqual(captured[1][1]["offset"], 100)
            self.assertEqual(captured[0][1]["startdate"], int(datetime(2026, 6, 30, 22, tzinfo=timezone.utc).timestamp()))

    def test_withings_signal_status_failure_and_nonadvancing_offset_are_fatal(self):
        for payload in [{"status": 503}, {"status": 0, "body": {"series": [], "more": 1, "offset": 0}},
                        {"status": 0, "body": {"series": [], "more": 1, "offset": "100"}}]:
            with self.subTest(payload=payload), patch.object(api, "_request", return_value=payload):
                with self.assertRaises(api.APIError):
                    api._withings_signals("heart", date(2026, 7, 1), date(2026, 9, 6))

    def test_withings_required_measurement_error_and_daily_transport_error_fail_closed(self):
        with patch.object(api, "_withings_measure", side_effect=api.APIError("Forbidden", status=403)):
            with self.assertRaises(api.APIError):
                api.fetch("withings", date(2026, 7, 1), date(2026, 9, 6))
        with patch.object(api, "_withings_measure", return_value={"measuregrps": []}), \
             patch.object(api, "_withings_daily", side_effect=auth.AuthError("Timeout")):
            with self.assertRaises(auth.AuthError):
                api.fetch("withings", date(2026, 7, 1), date(2026, 9, 6))

    def test_withings_daily_malformed_status_and_repeated_offset_fail_closed(self):
        bad = [{"status": 401}, {"status": False, "body": {}},
               {"status": 0, "body": {"series": [], "more": 1, "offset": 0}},
               {"status": 0, "body": {"series": [], "more": "1", "offset": 100}},
               {"status": 0, "body": {"series": ["bad record"], "more": 0}}]
        for payload in bad:
            with self.subTest(payload=payload), patch.object(api, "_request", return_value=payload):
                with self.assertRaises(api.APIError):
                    api._withings_daily("sleep", "getsummary", "series", [], date(2026, 7, 1), date(2026, 7, 2))

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

    def test_invalid_fetch_ranges_fail_before_network(self):
        with patch.object(api, "_request") as request:
            for start, end in [(date(2026, 9, 6), date(2026, 7, 1)), ("2026-07-01", date(2026, 9, 6)),
                               (datetime(2026, 7, 1), date(2026, 9, 6)), (date(2026, 7, 1), date.max)]:
                with self.subTest(start=start, end=end), self.assertRaises(api.APIError):
                    api.fetch("oura", start, end)
            request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
