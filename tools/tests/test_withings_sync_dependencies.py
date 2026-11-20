"""Synthetic sleep samples must survive an unavailable summary collection."""

import copy
from datetime import date, datetime
import unittest

from tools.health_sync.monthly import aggregate
from tools.health_sync.reconcile import merge_synced
from tools.health_sync.withings import parse_api


DAY = date(2026, 8, 1)
HRV_METRICS = {"Sampled Sleep RMSSD (Withings)", "Sampled Sleep SDNN1 (Withings)"}


def sleep_payload():
    start = int(datetime.fromisoformat("2026-07-31T23:30:00+02:00").timestamp())
    end = int(datetime.fromisoformat("2026-08-01T07:30:00+02:00").timestamp())
    return {
        "series": [{"id": "night", "completed": True, "startdate": start,
                    "enddate": end, "data": {"total_sleep_time": 7 * 3600}}],
        "sleep_detail_series": [{
            "startdate": start, "enddate": end, "state": 2,
            "rmssd": {str(start + 60): 30, str(start + 120): 50},
            "sdnn_1": {str(start + 60): 45, str(start + 120): 55},
        }],
    }


def coverage(**endpoints):
    return {"withings": {"start": DAY.isoformat(), "end": DAY.isoformat(),
                         "endpoint_status": {key: {"status": value}
                                             for key, value in endpoints.items()}}}


class WithingsSyncDependencyTests(unittest.TestCase):
    def test_unavailable_summaries_preserve_cached_hrv_despite_successful_samples(self):
        payload = sleep_payload()
        previous = parse_api(payload)
        samples_only = {"sleep_detail_series": payload["sleep_detail_series"]}
        incoming = parse_api(samples_only)
        # Samples need a completed summary before the parser can assign a night.
        self.assertEqual(incoming, [])
        snapshot = copy.deepcopy(previous)
        merged = merge_synced(previous, incoming, ["withings"], DAY, DAY,
                              coverage(getsummary="unavailable", sleep_details="complete"))
        self.assertEqual(merged, sorted(previous, key=lambda row: (
            row["day"], row["provider"], row["metric"], row["id"])))
        self.assertEqual(previous, snapshot)
        month = aggregate(merged, date(2026, 8, 2))["months"]["2026-08"]
        self.assertEqual(month["Sampled Sleep RMSSD (Withings)"]["value"], "40.0")
        self.assertEqual(month["Sampled Sleep SDNN1 (Withings)"]["value"], "50.0")

    def test_unknown_summary_coverage_does_not_authorize_hrv_deletion(self):
        previous = [row for row in parse_api(sleep_payload()) if row["metric"] in HRV_METRICS]
        for endpoint in ("sleep_details", "sleep_detail", "sleep_detail_series"):
            with self.subTest(endpoint=endpoint):
                merged = merge_synced(previous, [], ["withings"], DAY, DAY,
                                      coverage(**{endpoint: "complete"}))
                self.assertEqual({row["metric"] for row in merged}, HRV_METRICS)

    def test_unavailable_samples_preserve_hrv_while_summary_values_refresh(self):
        payload = sleep_payload()
        previous = parse_api(payload)
        payload["series"][0]["data"]["total_sleep_time"] = 6 * 3600
        incoming = parse_api({"series": payload["series"]})
        merged = merge_synced(previous, incoming, ["withings"], DAY, DAY,
                              coverage(getsummary="complete", sleep_details="unavailable"))
        values = {row["metric"]: row["value"] for row in merged}
        self.assertEqual(values["Sleep Duration (Withings)"], 6)
        self.assertEqual(values["Sampled Sleep RMSSD (Withings)"], 40)
        self.assertEqual(values["Sampled Sleep SDNN1 (Withings)"], 50)

    def test_both_complete_allow_empty_samples_to_remove_cached_hrv(self):
        payload = sleep_payload()
        previous = parse_api(payload)
        incoming = parse_api({"series": payload["series"], "sleep_detail_series": []})
        for summary_endpoint in ("getsummary", "sleep", "series"):
            with self.subTest(summary_endpoint=summary_endpoint):
                # Deliberately list samples first: dependency checks cannot rely
                # on the order of endpoint metadata in the saved response.
                merged = merge_synced(previous, incoming, ["withings"], DAY, DAY,
                                      coverage(sleep_details="complete", **{summary_endpoint: "complete"}))
                self.assertFalse(HRV_METRICS & {row["metric"] for row in merged})
                self.assertEqual(len(merged), len(incoming))

    def test_both_complete_accept_corrected_hrv_with_fewer_samples(self):
        payload = sleep_payload()
        previous = parse_api(payload)
        detail = payload["sleep_detail_series"][0]
        for field in ("rmssd", "sdnn_1"):
            first = min(detail[field])
            detail[field] = {first: 60}
        incoming = parse_api(payload)
        merged = merge_synced(previous, incoming, ["withings"], DAY, DAY,
                              coverage(getsummary="complete", sleep_details="complete"))
        hrv = [row for row in merged if row["metric"] in HRV_METRICS]
        self.assertEqual(len(hrv), 2)
        self.assertTrue(all(row["value"] == 60 and row["sample_count"] == 1 for row in hrv))


if __name__ == "__main__":
    unittest.main()
