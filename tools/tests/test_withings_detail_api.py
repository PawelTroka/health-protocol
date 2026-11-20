"""Bounded requests and separate coverage for optional Withings detail data."""

from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch
from zoneinfo import ZoneInfo

from tools.health_sync import api, reconcile, withings


class DetailFetchTests(TestCase):
    def test_sleep_details_cover_dst_day_in_windows_no_longer_than_24h(self):
        captured = []
        def request(provider, url, *, form):
            captured.append(dict(form))
            return {"status": 0, "body": {"model": 16, "series": [{"startdate": form["startdate"]}]}}
        with patch.object(api, "_request", side_effect=request):
            rows = api._withings_sleep_details(date(2026, 10, 25), date(2026, 10, 25))
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["model"] == 16 for row in rows))
        self.assertTrue(all(0 < row["enddate"] - row["startdate"] + 1 <= 86400 for row in captured))
        self.assertEqual(captured[0]["enddate"] + 1, captured[1]["startdate"])
        zone = ZoneInfo("Europe/Warsaw")
        self.assertEqual(captured[0]["startdate"], int(datetime(2026, 10, 25, tzinfo=zone).timestamp()))
        self.assertEqual(captured[-1]["enddate"] + 1, int(datetime(2026, 10, 26, tzinfo=zone).timestamp()))
        self.assertIn("rmssd", captured[0]["data_fields"])

    def test_sleep_detail_repeated_pagination_is_rejected(self):
        with patch.object(api, "_request", return_value={"status": 0, "body": {"series": [], "more": 1, "offset": 0}}):
            with self.assertRaises(api.APIError):
                api._withings_sleep_details(date(2026, 9, 1), date(2026, 9, 1))

    def test_ecg_fetch_deduplicates_signal_ids_and_retains_original_date(self):
        recording = {"timestamp": 1788321600, "model": 44, "ecg": {"signalid": 12}}
        body = {"signal": [0, 1, -1], "sampling_frequency": 300}
        with patch.object(api, "_request", return_value={"status": 0, "body": body}) as request:
            rows, unavailable = api._withings_heart_details([recording, recording, {"timestamp": 1788321660}])
        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.kwargs["form"], {"action": "get", "signalid": "12"})
        self.assertEqual(rows, [{"signalid": "12", "timestamp": 1788321600, "model": 44, "data": body}])
        self.assertEqual(unavailable, [])

    def test_ecg_optional_gap_keeps_successful_signals_but_transport_failure_stops(self):
        recordings = [{"timestamp": 1, "ecg": {"signalid": i}} for i in (1, 2)]
        with patch.object(api, "_request", side_effect=[api.APIError("missing", status=404), {"status": 0, "body": {"signal": []}}]):
            rows, unavailable = api._withings_heart_details(recordings)
        self.assertEqual([row["signalid"] for row in rows], ["2"])
        self.assertEqual(unavailable, [{"signalid": "1", "http_status": 404}])
        with patch.object(api, "_request", side_effect=api.APIError("rate limit", status=429)):
            with self.assertRaises(api.APIError):
                api._withings_heart_details(recordings)


class SleepDetailCoverageTests(TestCase):
    day = date(2026, 9, 2)

    def setUp(self):
        zone = ZoneInfo("Europe/Warsaw")
        start = int(datetime(2026, 9, 1, 23, tzinfo=zone).timestamp())
        end = int(datetime(2026, 9, 2, 7, tzinfo=zone).timestamp())
        self.sleep = {"id": "synthetic-night", "completed": True,
                      "startdate": start, "enddate": end, "data": {"total_sleep_time": 7 * 3600}}
        self.detail = {"startdate": start, "enddate": end, "state": 2,
                       "rmssd": {str(start + 60): 40}, "sdnn_1": {str(start + 60): 50}}
        previous = withings.parse_api({"series": [self.sleep], "sleep_detail_series": [self.detail]})
        self.previous = [row for row in previous if row["metric"].startswith("Sampled Sleep")]
        self.assertEqual(len(self.previous), 2)

    def fetch(self, summaries, details):
        def daily(endpoint, action, key, fields, start, end):
            if action == "getsummary":
                if isinstance(summaries, Exception):
                    raise summaries
                return summaries
            return []

        with patch.object(api, "_withings_measure", return_value={"measuregrps": []}), \
                patch.object(api, "_withings_daily", side_effect=daily), \
                patch.object(api, "_withings_signals", return_value=[]), \
                patch.object(api, "_withings_sleep_details", return_value=details) as samples:
            payload = api.fetch("withings", self.day, self.day)
        return payload, samples

    def reconcile(self, payload):
        return reconcile.merge_synced(
            self.previous, withings.parse_api(payload), ["withings"], self.day, self.day,
            {"withings": payload["_sync"]},
        )

    def test_unavailable_summary_preserves_cached_hrv_and_marks_dependency_gap(self):
        for status in (403, 404):
            with self.subTest(status=status):
                payload, samples = self.fetch(api.APIError("summary unavailable", status=status), [self.detail])
                self.assertEqual(self.reconcile(payload), self.previous)
                samples.assert_not_called()
                coverage = payload["_sync"]["endpoint_status"]
                self.assertEqual(coverage["getsummary"]["http_status"], status)
                self.assertEqual(coverage["sleep_details"]["status"], "unavailable")
                self.assertIn("summary", coverage["sleep_details"]["reason"])
                self.assertEqual(coverage["measure"]["status"], "complete")

    def test_complete_empty_sleep_samples_still_remove_old_hrv(self):
        for summaries in ([], [self.sleep]):
            with self.subTest(has_summary=bool(summaries)):
                payload, samples = self.fetch(summaries, [])
                result = self.reconcile(payload)
                self.assertFalse(any(row["metric"].startswith("Sampled Sleep") for row in result))
                samples.assert_called_once()
                self.assertEqual(payload["_sync"]["endpoint_status"]["sleep_details"]["status"], "complete")

    def test_complete_summary_and_samples_refresh_cached_hrv(self):
        updated = {**self.detail, "rmssd": {stamp: 60 for stamp in self.detail["rmssd"]}}
        payload, samples = self.fetch([self.sleep], [updated])
        result = {row["metric"]: row["value"] for row in self.reconcile(payload)}
        self.assertEqual(result["Sampled Sleep RMSSD (Withings)"], 60)
        self.assertEqual(result["Sampled Sleep SDNN1 (Withings)"], 50)
        samples.assert_called_once()
