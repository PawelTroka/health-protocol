"""Bounded requests and separate coverage for optional Withings detail data."""

from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch
from zoneinfo import ZoneInfo

from tools.health_sync import api, reconcile, withings


def sampled_night():
    start = int(datetime.fromisoformat("2026-09-01T23:30:00+02:00").timestamp())
    end = int(datetime.fromisoformat("2026-09-02T07:30:00+02:00").timestamp())
    return {
        "series": [{"id": "synthetic-night", "completed": True,
                    "startdate": start, "enddate": end, "data": {"total_sleep_time": 7 * 3600}}],
        "sleep_detail_series": [{"startdate": start, "enddate": end, "state": 1,
                                 "rmssd": {str(start + 60): 30}, "sdnn_1": {str(start + 60): 45}}],
    }


class DetailFetchTests(TestCase):
    def test_summary_access_gap_retains_sampled_hrv_while_other_measurements_refresh(self):
        day = date(2026, 9, 2)
        historical = withings.parse_api(sampled_night())
        group = {"grpid": 123, "category": 1, "attrib": 0,
                 "date": int(datetime.fromisoformat("2026-09-02T08:00:00+02:00").timestamp()),
                 "measures": [{"type": 1, "value": 80, "unit": 0}]}
        for code in (403, 404):
            with self.subTest(status=code), \
                    patch.object(api, "_withings_measure", return_value={"measuregrps": [group]}), \
                    patch.object(api, "_withings_daily", side_effect=[api.APIError("Unavailable", status=code), []]), \
                    patch.object(api, "_withings_signals", return_value=[]), \
                    patch.object(api, "_withings_sleep_details", return_value=sampled_night()["sleep_detail_series"]) as details:
                fetched = api.fetch("withings", day, day)
                updated = reconcile.merge_synced(historical, withings.parse_api(fetched), ["withings"],
                                                 day, day, {"withings": fetched["_sync"]})
                for marker in ("Sampled Sleep RMSSD (Withings)", "Sampled Sleep SDNN1 (Withings)"):
                    self.assertEqual([row for row in updated if row["metric"] == marker],
                                     [row for row in historical if row["metric"] == marker])
                self.assertEqual(next(row["value"] for row in updated if row["metric"] == "Body Mass"), 80)
                details.assert_not_called()
                coverage = fetched["_sync"]["endpoint_status"]
                self.assertEqual(coverage["sleep_details"]["status"], "unavailable")
                self.assertEqual(coverage["sleep_details"]["requires"], ["getsummary"])
                self.assertIn("summary", coverage["sleep_details"]["reason"])
                self.assertNotIn("sleep_detail_series", fetched)

    def test_complete_empty_sleep_collections_can_remove_obsolete_sampled_hrv(self):
        day = date(2026, 9, 2)
        with patch.object(api, "_withings_measure", return_value={"measuregrps": []}), \
                patch.object(api, "_withings_daily", return_value=[]), \
                patch.object(api, "_withings_signals", return_value=[]), \
                patch.object(api, "_withings_sleep_details", return_value=[]) as details:
            fetched = api.fetch("withings", day, day)
        details.assert_called_once_with(date(2026, 9, 1), day)
        for endpoint in ("getsummary", "sleep_details"):
            self.assertEqual(fetched["_sync"]["endpoint_status"][endpoint], {"status": "complete", "rows": 0})
        self.assertEqual(reconcile.merge_synced(withings.parse_api(sampled_night()), [], ["withings"],
                                               day, day, {"withings": fetched["_sync"]}), [])

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
