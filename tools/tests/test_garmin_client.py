"""Mock-only Garmin transport/auth tests; no real vault, credentials, or HTTP."""

from contextlib import nullcontext
from copy import deepcopy
from datetime import date, timedelta
import getpass
import io
import json
import logging
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from tools.health_sync import auth, garmin_client
from tools.health_sync.api import APIError


class AuthenticationError(Exception):
    pass


class RateLimitError(Exception):
    pass


class NotFoundError(Exception):
    pass


def session(access="test-access", refresh="test-refresh"):
    return json.dumps({"di_token": access, "di_refresh_token": refresh, "di_client_id": "test-client"})


class GarminClientTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)
        self.vault = {"oura": {"refresh_token": "other-provider"},
                      "garmin": {"session_json": session()}}
        self.saves = []
        self.client = MagicMock()
        self.client.client.dumps.return_value = session()
        self.client.login.return_value = (None, None)
        self.client.get_user_summary.return_value = {"totalSteps": 123}
        self.client.get_sleep_data.return_value = {"dailySleepDTO": {"sleepTimeSeconds": 24000}}
        self.client.get_hrv_data.return_value = None
        self.client.get_training_readiness.return_value = [{"score": 70}]
        self.library = SimpleNamespace(Garmin=MagicMock(return_value=self.client),
                                       GarminConnectAuthenticationError=AuthenticationError,
                                       GarminConnectTooManyRequestsError=RateLimitError,
                                       GarminConnectNotFoundError=NotFoundError)
        patch.object(garmin_client, "_library", return_value=self.library).start()
        patch.object(auth, "_locked", side_effect=lambda: nullcontext()).start()
        patch.object(auth, "_load", side_effect=lambda: deepcopy(self.vault)).start()
        patch.object(auth, "_save", side_effect=self.save).start()
        patch.object(auth, "build_opener", side_effect=AssertionError("Unexpected HTTP access")).start()
        self.first = date(2026, 9, 15)

    def save(self, value):
        self.vault = deepcopy(value)
        self.saves.append(deepcopy(value))

    def fetch(self, days=1):
        return garmin_client.fetch(self.first, self.first + timedelta(days=days - 1))

    def test_status_discloses_only_flags_without_optional_import(self):
        with patch.object(garmin_client, "_library", side_effect=AssertionError("Must be optional")):
            self.assertEqual(garmin_client.status(), {"configured": True, "authorized": True})
        self.assertFalse(self.saves)

    def test_missing_or_malformed_session_is_unauthorized(self):
        for value in (None, "/plaintext/tokens", "{}", "[]", session(refresh=None),
                      json.dumps({"di_token": "x", "di_refresh_token": "r", "password": "never"})):
            self.vault["garmin"] = {"session_json": value}
            self.assertEqual(garmin_client.status(), {"configured": True, "authorized": False})
            with self.assertRaisesRegex(auth.AuthError, "Connect Garmin locally"):
                self.fetch()
        self.library.Garmin.assert_not_called()

    def test_no_garmin_vault_entry_means_unconfigured(self):
        del self.vault["garmin"]
        self.assertEqual(garmin_client.status(), {"configured": False, "authorized": False})

    def test_connect_requires_interactive_stdin_before_prompts(self):
        with patch.object(garmin_client.sys.stdin, "isatty", return_value=False), \
             patch.object(getpass, "getpass") as prompt:
            with self.assertRaisesRegex(auth.AuthError, "interactive terminal"):
                garmin_client.connect()
        prompt.assert_not_called()

    def test_connect_uses_hidden_prompts_inline_json_and_only_encrypted_tokens(self):
        self.client.client.dumps.return_value = session("new-access", "new-refresh")
        with patch.object(garmin_client.sys.stdin, "isatty", return_value=True), \
             patch.object(getpass, "getpass", side_effect=["private@example.test", "private-password"]), \
             patch.dict("os.environ", {"GARMINTOKENS": "plaintext/path"}):
            garmin_client.connect()
        self.client.login.assert_called_once_with("{}")
        options = self.library.Garmin.call_args.kwargs
        self.assertEqual(options["retry_attempts"], 0)
        self.assertEqual(options["email"], "private@example.test")
        self.assertEqual(options["password"], "private-password")
        self.assertIsNone(self.client.username)
        self.assertIsNone(self.client.password)
        self.assertIsNone(self.client.prompt_mfa)
        self.client.client._clear_mfa_pending_state.assert_called_once()
        saved = json.dumps(self.vault)
        self.assertNotIn("private@example", saved)
        self.assertNotIn("private-password", saved)
        self.assertIn("new-refresh", saved)
        self.assertEqual(self.vault["oura"], {"refresh_token": "other-provider"})
        self.client.client.dump.assert_not_called()
        self.client.client.load.assert_not_called()

    def test_mfa_callback_uses_hidden_prompt(self):
        def login(_):
            callback = self.library.Garmin.call_args.kwargs["prompt_mfa"]
            self.assertEqual(callback(), "123456")
        self.client.login.side_effect = login
        with patch.object(garmin_client.sys.stdin, "isatty", return_value=True), \
             patch.object(getpass, "getpass", side_effect=["mail", "password", "123456"]) as prompt:
            garmin_client.connect()
        self.assertIn("verification", prompt.call_args.args[0])
        self.assertNotIn("123456", json.dumps(self.vault))

    def test_visible_getpass_fallback_is_rejected(self):
        with patch.object(getpass, "getpass", side_effect=getpass.GetPassWarning("echo enabled")):
            with self.assertRaisesRegex(auth.AuthError, "interactive terminal"):
                garmin_client._secret("test: ")

    def test_login_failure_preserves_rotated_tokens_and_clears_credentials(self):
        def fail(_):
            self.client.client.dumps.return_value = session("rotated-access", "rotated-refresh")
            raise AuthenticationError("private@example.test secret response")
        self.client.login.side_effect = fail
        with patch.object(garmin_client.sys.stdin, "isatty", return_value=True), \
             patch.object(getpass, "getpass", side_effect=["private@example.test", "password"]):
            with self.assertRaisesRegex(auth.AuthError, "authorization failed") as error:
                garmin_client.connect()
        self.assertNotIn("secret", str(error.exception))
        self.assertIn("rotated-refresh", self.vault["garmin"]["session_json"])
        self.assertIsNone(self.client.password)

    def test_fetch_restores_inline_session_and_wraps_actual_daily_payloads(self):
        result = self.fetch(days=2)
        self.client.login.assert_called_once_with(session())
        self.library.Garmin.assert_called_once_with(retry_attempts=0)
        self.assertEqual(result["daily_summary"][0], {"day": "2026-09-15", "data": {"totalSteps": 123}})
        self.assertEqual(result["hrv"][1], {"day": "2026-09-16", "data": None})
        self.assertEqual(result["_sync"]["start"], "2026-09-15")
        self.assertEqual(result["_sync"]["end"], "2026-09-16")
        self.assertEqual(set(result) - {"_sync"}, set(garmin_client.ENDPOINTS))
        for endpoint in garmin_client.ENDPOINTS:
            self.assertEqual(result["_sync"]["endpoint_status"][endpoint], {"status": "complete", "rows": 2})
        self.client.client.dump.assert_not_called()
        self.client.client.load.assert_not_called()

    def test_current_day_is_included_for_caller_to_defer(self):
        today = date.today()
        result = garmin_client.fetch(today, today)
        self.assertEqual(result["_sync"]["end"], today.isoformat())
        self.client.get_user_summary.assert_called_once_with(today.isoformat())

    def test_optional_404_retains_partial_endpoint_and_marks_whole_incomplete(self):
        self.client.get_sleep_data.side_effect = [{"dailySleepDTO": {}}, NotFoundError("private response"),
                                                  {"dailySleepDTO": {"sleepTimeSeconds": 28000}}]
        result = self.fetch(days=3)
        self.assertEqual(len(result["sleep"]), 2)
        self.assertEqual(result["sleep"][-1]["day"], "2026-09-17")
        self.assertEqual(self.client.get_sleep_data.call_count, 3)
        self.assertEqual(result["_sync"]["endpoint_status"]["sleep"],
                         {"status": "unavailable", "http_status": 404, "rows": 2,
                          "unavailable_days": ["2026-09-16"]})
        self.assertEqual(len(result["hrv"]), 3)

    def test_daily_summary_404_aborts(self):
        self.client.get_user_summary.side_effect = NotFoundError("account details")
        with self.assertRaisesRegex(APIError, "no partial results"):
            self.fetch()
        self.client.get_sleep_data.assert_not_called()

    def test_auth_rate_limit_forbidden_and_transport_failures_abort_without_details(self):
        forbidden = RuntimeError("private-response-body")
        forbidden.response = SimpleNamespace(status_code=403)
        for error in (AuthenticationError("private-response-body"), RateLimitError("private-response-body"),
                      forbidden, TimeoutError("private-response-body")):
            self.client.get_sleep_data.side_effect = error
            with self.assertRaises(APIError) as raised:
                self.fetch()
            self.assertNotIn("private-response-body", str(raised.exception))
        self.client.get_hrv_data.assert_not_called()

    def test_rotations_are_persisted_before_next_endpoint_and_after_failure(self):
        def summary(_):
            self.client.client.dumps.return_value = session("rotated", "new-refresh")
            return {"totalSteps": 44}
        def sleep(_):
            self.assertIn("new-refresh", self.vault["garmin"]["session_json"])
            self.client.client.dumps.return_value = session("again", "latest-refresh")
            raise TimeoutError("private")
        self.client.get_user_summary.side_effect = summary
        self.client.get_sleep_data.side_effect = sleep
        with self.assertRaises(APIError):
            self.fetch()
        self.assertIn("latest-refresh", self.vault["garmin"]["session_json"])
        self.assertEqual(self.vault["oura"], {"refresh_token": "other-provider"})

    def test_invalid_session_dump_does_not_replace_existing_tokens(self):
        self.client.client.dumps.return_value = "{}"
        with patch.object(garmin_client.sys.stdin, "isatty", return_value=True), \
             patch.object(getpass, "getpass", side_effect=["mail", "password"]):
            with self.assertRaisesRegex(auth.AuthError, "reusable session"):
                garmin_client.connect()
        self.assertEqual(self.vault["garmin"]["session_json"], session())
        self.assertFalse(self.saves)

    def test_session_serialization_failure_is_sanitized(self):
        self.client.client.dumps.side_effect = RuntimeError("private token content")
        with self.assertRaisesRegex(auth.AuthError, "preserve the Garmin session") as error:
            self.fetch()
        self.assertNotIn("private token", str(error.exception))
        self.client.client._clear_mfa_pending_state.assert_called_once()

    def test_session_save_failure_blocks_next_endpoint(self):
        self.client.client.dumps.return_value = session("rotated", "new-refresh")
        with patch.object(auth, "_save", side_effect=auth.AuthError("Secure save failed")):
            with self.assertRaisesRegex(auth.AuthError, "Secure save failed"):
                self.fetch()
        self.client.get_user_summary.assert_not_called()

    def test_malformed_payloads_abort_without_publishing(self):
        for payload in ("unexpected", 17, ["unexpected"], {"value": float("nan")}):
            self.client.get_training_readiness.return_value = payload
            with self.assertRaisesRegex(APIError, "malformed records"):
                self.fetch()

    def test_oversized_response_aborts(self):
        with patch.object(auth, "MAX_RESPONSE_BYTES", 8):
            with self.assertRaisesRegex(APIError, "safe response size"):
                self.fetch()

    def test_date_validation_prevents_network_and_caps_daily_requests(self):
        for first, last in (("2026-09-15", self.first), (self.first, self.first - timedelta(days=1)),
                            (self.first, self.first + timedelta(days=366)), (self.first, date.max)):
            with self.assertRaises(APIError):
                garmin_client.fetch(first, last)
        self.library.Garmin.assert_not_called()

    def test_upstream_logs_are_suppressed_and_prior_logging_state_restored(self):
        logger = logging.getLogger("garminconnect")
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        logger.addHandler(handler)
        self.addCleanup(logger.removeHandler, handler)
        previous = logging.root.manager.disable
        def fail(_):
            logger.critical("secret response body")
            raise TimeoutError("secret response body")
        self.client.get_sleep_data.side_effect = fail
        with self.assertRaises(APIError):
            self.fetch()
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(logging.root.manager.disable, previous)


if __name__ == "__main__":
    unittest.main()
