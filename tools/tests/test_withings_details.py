"""Synthetic sleep-detail and ECG fixtures; no account access or report writes."""

import copy
from datetime import datetime
import unittest

from tools.health_sync.withings import (
    WITHINGS_METRICS, WITHINGS_SLEEP_DETAIL_FIELDS, check_detail_file_coverage,
    ecg_signal_inventory, parse_api,
)


def stamp(text):
    return int(datetime.fromisoformat(text).timestamp())


def sleep(key="night", start="2026-09-01T23:30:00+02:00", end="2026-09-02T07:30:00+02:00", **data):
    return {"id": key, "completed": True, "startdate": stamp(start), "enddate": stamp(end),
            "model_id": 63, "data": {"total_sleep_time": 7 * 3600, **data}}


def metrics(payload):
    return {record["metric"]: record for record in parse_api(payload)}


class WithingsDetailTests(unittest.TestCase):
    def test_schedule_keeps_local_midnight_and_elapsed_midpoint(self):
        original = {"series": [sleep()]}
        snapshot = copy.deepcopy(original)
        rows = metrics(original)
        self.assertEqual(original, snapshot)
        for marker, expected in (("Bedtime (Withings)", 1410), ("Wake-up Time (Withings)", 450),
                                 ("Sleep Midpoint (Withings)", 210)):
            row = rows[marker]
            self.assertEqual(row["value"], expected)
            self.assertEqual(row["unit"], "hh:mm")
            self.assertEqual(row["monthly_aggregation"], "circular_mean")
            self.assertEqual(row["day"], "2026-09-02")
            self.assertEqual(row["source_record_ids"], ["night"])
        self.assertEqual(rows["Short Sleep Nights (Withings)"]["value"], 0)
        self.assertNotIn("Sleep Midpoint Variability (Withings)", rows)
        self.assertEqual(WITHINGS_METRICS["Sleep Midpoint Variability (Withings)"], ("min", 0))

    def test_schedule_uses_elapsed_time_across_dst_not_naive_clock_average(self):
        row = metrics({"series": [sleep(start="2026-10-25T00:00:00+02:00",
                                        end="2026-10-25T08:00:00+01:00")]})
        # Nine elapsed hours, midpoint 03:30 CET, not 04:00 from wall-clock endpoints.
        self.assertEqual(row["Sleep Midpoint (Withings)"]["value"], 210)

    def test_adjacent_split_night_combines_sleep_before_short_sleep_flag(self):
        first = sleep("first", "2026-09-02T00:00:00+02:00", "2026-09-02T03:00:00+02:00",
                      total_sleep_time=3 * 3600, apnea_hypopnea_index=2)
        second = sleep("second", "2026-09-02T05:00:00+02:00", "2026-09-02T09:00:00+02:00",
                       total_sleep_time=4 * 3600, apnea_hypopnea_index=8)
        rows = metrics({"series": [second, first]})
        self.assertEqual(rows["Sleep Duration (Withings)"]["value"], 7)
        self.assertEqual(rows["Short Sleep Nights (Withings)"]["value"], 0)
        self.assertEqual(rows["Bedtime (Withings)"]["value"], 0)
        self.assertEqual(rows["Wake-up Time (Withings)"]["value"], 540)
        self.assertEqual(rows["Short Sleep Nights (Withings)"]["source_record_ids"], ["first", "second"])
        self.assertAlmostEqual(rows["Sleep Apnea AHI"]["value"], 38 / 7)
        self.assertEqual(rows["AHI ≥5 Nights (Withings)"]["value"], 100)

    def test_separate_nap_suppresses_schedule_and_short_flag_but_not_daily_sleep(self):
        nap = sleep("nap", "2026-09-02T15:00:00+02:00", "2026-09-02T16:00:00+02:00",
                    total_sleep_time=3600)
        rows = metrics({"series": [sleep(total_sleep_time=6 * 3600), nap]})
        self.assertEqual(rows["Sleep Duration (Withings)"]["value"], 7)
        self.assertNotIn("Bedtime (Withings)", rows)
        self.assertNotIn("Short Sleep Nights (Withings)", rows)
        long = sleep(start="2026-09-01T12:00:00+02:00", end="2026-09-02T07:00:00+02:00")
        self.assertNotIn("Bedtime (Withings)", metrics({"series": [long]}))

    def test_short_sleep_and_ahi_boundaries_do_not_impute_missing_nights(self):
        for seconds, expected in ((7 * 3600 - 1, 100), (7 * 3600, 0)):
            self.assertEqual(metrics({"series": [sleep(total_sleep_time=seconds)]})[
                "Short Sleep Nights (Withings)"]["value"], expected)
        for ahi, expected in ((4.99, 0), (5, 100), (10, 100)):
            self.assertEqual(metrics({"series": [sleep(apnea_hypopnea_index=ahi)]})[
                "AHI ≥5 Nights (Withings)"]["value"], expected)
        for invalid in (None, -1, "pending", True):
            rows = metrics({"series": [sleep(total_sleep_time=invalid, apnea_hypopnea_index=invalid)]})
            self.assertNotIn("Short Sleep Nights (Withings)", rows)
            self.assertNotIn("AHI ≥5 Nights (Withings)", rows)
        self.assertNotIn("AHI ≥5 Nights (Withings)", metrics({"series": [sleep()]}))
        self.assertEqual(metrics({"series": [{**sleep(), "completed": False}]}), {})

    def test_sampled_hrv_has_units_window_and_observed_time_coverage(self):
        night = sleep()
        first, second = night["startdate"] + 60, night["startdate"] + 120
        detail = {"startdate": night["startdate"], "enddate": night["enddate"], "state": 2,
                  "model_id": 63, "rmssd": {str(first): 30, str(second): 50},
                  "sdnn_1": {str(first): 45, str(second): 55},
                  "hrv_quality": {str(first): 0, str(second): 2}}
        payload = {"series": [night], "sleep_detail_series": [detail, copy.deepcopy(detail)]}
        snapshot = copy.deepcopy(payload)
        rows = metrics(payload)
        self.assertEqual(payload, snapshot)
        self.assertEqual(set(WITHINGS_SLEEP_DETAIL_FIELDS), {"rmssd", "sdnn_1", "hrv_quality"})
        for marker, value, window in (("Sampled Sleep RMSSD (Withings)", 40, "few_seconds"),
                                      ("Sampled Sleep SDNN1 (Withings)", 50, "one_minute")):
            row = rows[marker]
            self.assertEqual(row["value"], value)
            self.assertEqual(row["unit"], "ms")
            self.assertEqual(row["sample_count"], 2)
            self.assertEqual(row["sampled_minutes"], 2)
            self.assertEqual(row["quality_sample_count"], 2)
            self.assertEqual(row["quality_values"], [0, 2])
            self.assertEqual(row["sample_window"], window)
            self.assertEqual(row["day"], "2026-09-02")
            self.assertTrue(row["first_sample_at"].startswith("2026-09-01T23:31"))
            self.assertEqual(row["source_sample_timestamps"], [first, second])

    def test_hrv_rejects_sentinels_awake_unmatched_and_boundary_samples(self):
        night = sleep()
        start, end = night["startdate"], night["enddate"]
        for state in (0, 4, 5, 15, None, True):
            detail = {"startdate": start, "enddate": end, "state": state, "rmssd": {str(start): 50}}
            self.assertNotIn("Sampled Sleep RMSSD (Withings)", metrics({"series": [night], "sleep_detail_series": [detail]}))
        detail = {"startdate": start, "enddate": end, "state": 1, "rmssd": {
            str(start): -1, str(start + 1): 0, str(start + 2): True, str(start + 3): "pending",
            str(start + 4): float("nan"), str(start - 1): 20, str(end): 40, str(start + 5): 30,
        }}
        row = metrics({"series": [night], "sleep_detail_series": [detail]})["Sampled Sleep RMSSD (Withings)"]
        self.assertEqual(row["value"], 30)
        self.assertEqual(row["sample_count"], 1)
        self.assertNotIn("Sampled Sleep RMSSD (Withings)", metrics({"sleep_detail_series": [detail]}))
        self.assertNotIn("Sampled Sleep RMSSD (Withings)", metrics({"series": [night],
                        "sleep_detail_series": [{**detail, "model_id": 94}]}))

    def test_conflicting_duplicate_hrv_sample_fails_without_averaging(self):
        night = sleep()
        detail = {"startdate": night["startdate"], "enddate": night["enddate"], "state": 1,
                  "rmssd": {str(night["startdate"]): 30}}
        other = {**detail, "rmssd": {str(night["startdate"]): 60}}
        with self.assertRaisesRegex(ValueError, "Conflicting.*HRV"):
            parse_api({"series": [night], "sleep_detail_series": [detail, other]})

    def test_partial_detail_file_cannot_shrink_sample_or_session_coverage(self):
        night = sleep()
        start = night["startdate"]
        detail = {"startdate": start, "enddate": night["enddate"], "state": 1,
                  "rmssd": {str(start): 30, str(start + 60): 60}}
        full = metrics({"series": [night], "sleep_detail_series": [detail]})["Sampled Sleep RMSSD (Withings)"]
        partial = metrics({"series": [night], "sleep_detail_series": [
            {**detail, "rmssd": {str(start): 30}}]})["Sampled Sleep RMSSD (Withings)"]
        snapshot = copy.deepcopy([full, partial])
        with self.assertRaisesRegex(ValueError, "all known samples.*full API sync"):
            check_detail_file_coverage([full], [partial])
        self.assertEqual([full, partial], snapshot)
        # Even identical timestamp coverage must retain all contributing sessions.
        prior_sessions = {**full, "source_record_ids": ["night", "second"], "source_count": 2}
        with self.assertRaisesRegex(ValueError, "full API sync"):
            check_detail_file_coverage([prior_sessions], [full])

    def test_detail_file_accepts_complete_or_expanded_coverage_and_ignores_other_cells(self):
        record = {"provider": "withings", "id": "withings:sleep_detail:daily-2026-09-02:Sampled Sleep RMSSD (Withings)",
                  "day": "2026-09-02", "metric": "Sampled Sleep RMSSD (Withings)",
                  "source_record_ids": ["night"], "source_count": 1,
                  "source_sample_timestamps": [1000, 1060], "sample_count": 2}
        expanded = {**record, "source_record_ids": ["night", "second"], "source_count": 2,
                    "source_sample_timestamps": [1000, 1060, 1120], "sample_count": 3}
        check_detail_file_coverage([record], [copy.deepcopy(record)])
        check_detail_file_coverage([record], [expanded])
        check_detail_file_coverage([record], [])
        check_detail_file_coverage([record], [{**record, "day": "2026-09-03"}])
        check_detail_file_coverage([record], [{"provider": "oura", "metric": record["metric"]}])
        check_detail_file_coverage([record], [{"provider": "withings", "metric": "Body Mass"}])

    def test_detail_file_fails_closed_on_missing_provenance_or_competing_means(self):
        record = {"provider": "withings", "id": "withings:sleep_detail:daily-2026-09-02:Sampled Sleep RMSSD (Withings)",
                  "day": "2026-09-02", "metric": "Sampled Sleep RMSSD (Withings)",
                  "source_record_ids": ["night"], "source_count": 1,
                  "source_sample_timestamps": [1000, 1060], "sample_count": 2}
        invalid = [
            {**record, "source_sample_timestamps": []},
            {**record, "source_sample_timestamps": [1000, 1000]},
            {**record, "source_sample_timestamps": [True, 1060]},
            {**record, "sample_count": 1},
            {**record, "source_record_ids": ["night", "night"], "source_count": 2},
            {key: value for key, value in record.items() if key != "source_sample_timestamps"},
        ]
        for bad in invalid:
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "full API sync"):
                    check_detail_file_coverage([record], [bad])
                with self.assertRaisesRegex(ValueError, "full API sync"):
                    check_detail_file_coverage([bad], [record])
        with self.assertRaisesRegex(ValueError, "full API sync"):
            check_detail_file_coverage([], [record, copy.deepcopy(record)])

    def test_private_ecg_inventory_preserves_signal_and_does_not_create_monthly_values(self):
        entry = {"signalid": 123, "timestamp": stamp("2026-09-02T01:00:00+02:00"), "model": 44,
                 "data": {"signal": [-100, 0, 200, -50], "sampling_frequency": 500, "wearposition": 1}}
        payload = {"heart_signals": [entry, copy.deepcopy(entry)]}
        snapshot = copy.deepcopy(payload)
        result = ecg_signal_inventory(payload)
        self.assertEqual(payload, snapshot)
        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertEqual(row["signal_uv"], [-100, 0, 200, -50])
        self.assertEqual(row["amplitude_unit"], "uV")
        self.assertEqual(row["sampling_frequency_hz"], 500)
        self.assertEqual(row["sample_count"], 4)
        self.assertEqual(row["duration_seconds"], .008)
        self.assertEqual(row["day"], "2026-09-02")
        self.assertEqual(parse_api(payload), [])

    def test_ecg_inventory_rejects_unknown_frequency_bad_samples_and_conflicts(self):
        base = {"signalid": 123, "timestamp": stamp("2026-09-02T01:00:00+02:00")}
        for data in ({"signal": [1]}, {"signal": [1], "sampling_frequency": 0},
                     {"signal": [True], "sampling_frequency": 500},
                     {"signal": [], "sampling_frequency": 500}):
            self.assertEqual(ecg_signal_inventory({"heart_signals": [{**base, "data": data}]}), [])
        first = {**base, "data": {"signal": [1], "sampling_frequency": 500}}
        second = {**base, "data": {"signal": [2], "sampling_frequency": 500}}
        with self.assertRaisesRegex(ValueError, "Conflicting.*ECG"):
            ecg_signal_inventory({"heart_signals": [first, second]})

    def test_ecg_results_join_by_signal_id_even_when_heart_rate_timestamp_differs(self):
        at = stamp("2026-09-02T01:00:00+02:00")
        signal = {"signalid": 123, "timestamp": at,
                  "data": {"signal": [-100, 0, 200], "sampling_frequency": 500,
                           "heart_rate": {"value": 67, "date": at - 90, "is_deleted": False}}}
        for code, label in ((0, "Negative"), (1, "Positive"), (2, "Inconclusive")):
            with self.subTest(code=code):
                payload = {"heart_signals": [signal], "heart_series": [
                    {"timestamp": at, "heart_rate": 99, "ecg": {"signalid": 999, "afib": 1}},
                    {"timestamp": at, "heart_rate": 67, "ecg": {"signalid": "123", "afib": code}},
                ]}
                original = copy.deepcopy(payload)
                row = ecg_signal_inventory(payload)[0]
                self.assertEqual(row["heart_rate_bpm"], 67)
                self.assertEqual(row["af_classification"], label)
                self.assertEqual(row["recorded_at"], "2026-09-02T01:00:00+02:00")
                self.assertEqual(original, payload)
        unknown = ecg_signal_inventory({"heart_signals": [signal], "heart_series": [
            {"heart_rate": -1, "ecg": {"signalid": 123, "afib": 99}}]})[0]
        self.assertNotIn("heart_rate_bpm", unknown)
        self.assertNotIn("af_classification", unknown)
        with self.assertRaisesRegex(ValueError, "Conflicting.*ECG results"):
            ecg_signal_inventory({"heart_signals": [signal], "heart_series": [
                {"heart_rate": 67, "ecg": {"signalid": 123, "afib": 0}},
                {"heart_rate": 68, "ecg": {"signalid": 123, "afib": 0}},
            ]})


if __name__ == "__main__":
    unittest.main()
