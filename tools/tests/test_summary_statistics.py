"""Boundary tests for clock summaries, observed-night rates and event totals."""

import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from tools.health_sync.monthly import aggregate, apply_report_overlay, load_monthly, validate_records
from tools.health_sync.oura import OURA_METRICS
from tools.health_sync.summary_statistics import circular_summary, clock_text, report_value


MIDPOINT = "Sleep Midpoint (Oura)"
VARIABILITY = "Sleep Midpoint Variability (Oura)"
SHORT_NIGHTS = "Short Sleep Nights (Oura)"
PERIODS = "Recorded Short-Sleep Periods (Oura)"
DURATION = "Recorded Short-Sleep Duration (Oura)"


def observation(metric, value, day="2026-08-01", identifier=None):
    return {"provider": "oura", "id": identifier or f"oura:api:sleep:{day}:{metric}",
            "metric": metric, "value": value, "unit": OURA_METRICS[metric][0],
            "day": day, "source_kind": "api"}


class SummaryStatisticsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "monthly.json"

    def load(self, payload):
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        return load_monthly(self.path)

    def test_circular_mean_straddles_midnight_and_sd_is_in_minutes(self):
        payload = aggregate([observation(MIDPOINT, 1430),
                             observation(MIDPOINT, 10, "2026-08-02")], date(2026, 9, 1))
        rows = payload["months"]["2026-08"]
        self.assertEqual(rows[MIDPOINT]["value"], "00:00")
        self.assertEqual(rows[MIDPOINT]["aggregation"], "circular_mean_local_time")
        self.assertEqual(rows[VARIABILITY]["value"], "10")
        self.assertEqual(rows[VARIABILITY]["unit"], "min")
        self.assertEqual(rows[VARIABILITY]["derived_from"], MIDPOINT)
        self.assertEqual(rows[VARIABILITY]["observed_days"], "2026-08-01,2026-08-02")
        self.assertEqual(self.load(payload), payload)

    def test_clock_rounding_wraps_at_midnight(self):
        self.assertEqual(clock_text(1439.5), "00:00")
        self.assertEqual(clock_text(1439.49), "23:59")
        self.assertEqual(clock_text(0.5), "00:01")
        value = aggregate([observation("Bedtime (Oura)", 1439.5)], date(2026, 9, 1))
        self.assertEqual(value["months"]["2026-08"]["Bedtime (Oura)"]["value"], "00:00")

    def test_one_night_has_no_variability_but_two_identical_nights_have_zero(self):
        single = observation(MIDPOINT, 240)
        one = aggregate([single, copy.deepcopy(single)], date(2026, 9, 1))["months"]["2026-08"]
        self.assertEqual(one[MIDPOINT]["n_days"], 1)
        self.assertNotIn(VARIABILITY, one)
        two = aggregate([single, observation(MIDPOINT, 240, "2026-08-02")], date(2026, 9, 1))
        self.assertEqual(two["months"]["2026-08"][VARIABILITY]["value"], "0")
        self.assertEqual(self.load(two), two)

    def test_opposite_or_uniform_clocks_have_no_defensible_mean_or_variability(self):
        for minutes in ([0, 720], [0, 360, 720, 1080]):
            with self.subTest(minutes=minutes):
                self.assertEqual(circular_summary(minutes), (None, None))
                records = [observation(MIDPOINT, value, f"2026-08-{index:02d}")
                           for index, value in enumerate(minutes, 1)]
                self.assertEqual(aggregate(records, date(2026, 9, 1))["months"], {})

    def test_raw_clock_and_event_inputs_are_validated_before_aggregation(self):
        cases = [(MIDPOINT, value) for value in (-1, 1440, "12:00", True, float("nan"))]
        cases += [(SHORT_NIGHTS, value) for value in (-1, 1, 50, 101, True)]
        cases += [(PERIODS, -1), (PERIODS, 0.5), (DURATION, -0.1)]
        cases.append((VARIABILITY, 10))
        for metric, value in cases:
            with self.subTest(metric=metric, value=value), self.assertRaises(ValueError):
                validate_records([observation(metric, value)])

    def test_loaded_clock_text_requires_a_real_24_hour_time(self):
        payload = aggregate([observation(MIDPOINT, 240)], date(2026, 9, 1))
        for invalid in ("24:00", "1:00", "00:60", "-01:00", "240", "01:30:00"):
            altered = copy.deepcopy(payload)
            altered["months"]["2026-08"][MIDPOINT]["value"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.load(altered)

    def test_night_frequency_keeps_observed_denominator_and_displays_matching_count(self):
        records = [observation(SHORT_NIGHTS, 100, "2026-08-01"),
                   observation(SHORT_NIGHTS, 0, "2026-08-05"),
                   observation(SHORT_NIGHTS, 100, "2026-08-31")]
        payload = aggregate(records, date(2026, 9, 1))
        entry = payload["months"]["2026-08"][SHORT_NIGHTS]
        self.assertEqual((entry["value"], entry["n_matching_days"], entry["n_days"]), ("66.7", 2, 3))
        self.assertEqual(entry["calendar_days"], 31)
        self.assertEqual(report_value(SHORT_NIGHTS, entry), "66.7 (2/3)")
        self.assertEqual(self.load(payload), payload)
        for indicator, expected in ((0, "0.0 (0/2)"), (100, "100.0 (2/2)")):
            rows = [observation(SHORT_NIGHTS, indicator, f"2026-08-0{day}") for day in (1, 2)]
            entry = aggregate(rows, date(2026, 9, 1))["months"]["2026-08"][SHORT_NIGHTS]
            self.assertEqual(report_value(SHORT_NIGHTS, entry), expected)

    def test_loaded_event_rates_cannot_disagree_with_their_counts(self):
        payload = aggregate([observation(SHORT_NIGHTS, 100),
                             observation(SHORT_NIGHTS, 0, "2026-08-02")], date(2026, 9, 1))
        for changes in ({"n_matching_days": -1}, {"n_matching_days": 3},
                        {"n_matching_days": True}, {"n_matching_days": 1.0},
                        {"value": "49.9"}, {"value": "50.0 (1/2)"}):
            altered = copy.deepcopy(payload)
            altered["months"]["2026-08"][SHORT_NIGHTS].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.load(altered)

    def test_recorded_short_sleep_is_an_observed_total_not_a_daily_average(self):
        records = []
        for day, count, hours in ((1, 0, 0), (2, 2, 0.75), (10, 1, 0.5)):
            records.extend([observation(PERIODS, count, f"2026-08-{day:02d}"),
                            observation(DURATION, hours, f"2026-08-{day:02d}")])
        payload = aggregate(records, date(2026, 9, 1))
        rows = payload["months"]["2026-08"]
        self.assertEqual(rows[PERIODS]["value"], "3")
        self.assertEqual(rows[DURATION]["value"], "1.25")
        for metric in (PERIODS, DURATION):
            self.assertEqual(rows[metric]["n_days"], 3)
            self.assertEqual(rows[metric]["aggregation"], "sum_of_daily_totals")
        self.assertEqual(self.load(payload), payload)

    def test_distinct_observations_for_one_day_cannot_double_weight_special_metrics(self):
        for metric, value in ((MIDPOINT, 300), (SHORT_NIGHTS, 100), (PERIODS, 1), (DURATION, 0.5)):
            readings = [observation(metric, value, identifier="one"),
                        observation(metric, value, identifier="two")]
            with self.subTest(metric=metric), self.assertRaisesRegex(ValueError, "one normalized daily"):
                aggregate(readings, date(2026, 9, 1))

    def test_current_day_future_and_pre_july_values_do_not_enter_coverage(self):
        records = [observation(SHORT_NIGHTS, 100, day) for day in
                   ("2026-06-30", "2026-07-01", "2026-07-03", "2026-07-04", "2026-07-05")]
        payload = aggregate(records, date(2026, 7, 4))
        entry = payload["months"]["2026-07"][SHORT_NIGHTS]
        self.assertEqual((entry["n_days"], entry["elapsed_days"], entry["calendar_days"]), (2, 4, 31))
        self.assertEqual(entry["observed_days"], "2026-07-01,2026-07-03")
        self.assertEqual(entry["first_day"], "2026-07-01")
        self.assertEqual(entry["last_day"], "2026-07-03")
        self.assertTrue(entry["partial_month"])
        self.assertEqual(self.load(payload), payload)

    def test_aggregate_and_overlay_are_repeatable_without_mutating_source_payload(self):
        records = [observation(MIDPOINT, 1430), observation(MIDPOINT, 10, "2026-08-02"),
                   observation(SHORT_NIGHTS, 100), observation(SHORT_NIGHTS, 0, "2026-08-02")]
        before = copy.deepcopy(records)
        payload = aggregate(records, date(2026, 9, 1))
        self.assertEqual(payload, aggregate(list(reversed(records)), date(2026, 9, 1)))
        self.assertEqual(records, before)
        original_payload = copy.deepcopy(payload)
        followups, notes = {"2026-07": {"Unrelated": "preserved"}}, []
        apply_report_overlay(followups, notes, payload)
        first_overlay = copy.deepcopy((followups, notes))
        apply_report_overlay(followups, notes, payload)
        self.assertEqual((followups, notes), first_overlay)
        self.assertEqual(payload, original_payload)
        self.assertEqual(followups["2026-08"][SHORT_NIGHTS], "50.0 (1/2)")
        self.assertEqual(followups["2026-08"][MIDPOINT], "00:00")
        self.assertEqual(followups["2026-07"], {"Unrelated": "preserved"})

    def test_loaded_variability_requires_multiple_nights_and_matching_source_metric(self):
        payload = aggregate([observation(MIDPOINT, 240),
                             observation(MIDPOINT, 260, "2026-08-02")], date(2026, 9, 1))
        for changes in ({"n_days": 1}, {"value": "-1"}, {"derived_from": "Bedtime (Oura)"},
                        {"aggregation": "mean_of_daily_means"}):
            altered = copy.deepcopy(payload)
            altered["months"]["2026-08"][VARIABILITY].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.load(altered)

    def test_loaded_short_sleep_totals_cannot_be_negative(self):
        payload = aggregate([observation(PERIODS, 1), observation(DURATION, 0.5)], date(2026, 9, 1))
        for metric in (PERIODS, DURATION):
            altered = copy.deepcopy(payload)
            altered["months"]["2026-08"][metric]["value"] = "-1"
            with self.subTest(metric=metric), self.assertRaises(ValueError):
                self.load(altered)


if __name__ == "__main__":
    unittest.main()
