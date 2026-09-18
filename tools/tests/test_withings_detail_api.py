"""Bounded requests and separate coverage for optional Withings detail data."""

from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch
from zoneinfo import ZoneInfo

from tools.health_sync import api


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
