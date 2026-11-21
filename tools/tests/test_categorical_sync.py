import copy
from datetime import date
import unittest

from tools.health_sync import categorical, garmin, monthly


def event(key, day, value="Negative", provider="withings"):
    return {"id": key, "day": day, "provider": provider,
            "metric": "ECG AF Classification (Withings)", "value": value,
            "recorded_at": day + "T12:00:00+02:00"}


class ClassificationTests(unittest.TestCase):
    def test_each_garmin_workout_reaches_monthly_counts_and_report_overlay(self):
        def activity(identifier, hour, label="AEROBIC_BASE"):
            return {"activityId": identifier, "startTimeLocal": f"2026-07-02 {hour}:00:00",
                    "trainingEffectLabel": label}

        morning = activity(1, "09")
        payload = {"activities": [{"day": "2026-07-02", "data": [
            morning, activity(2, "18"), activity(3, "20", "RECOVERY"), copy.deepcopy(morning),
        ]}]}
        records = garmin.categorical_inventory(payload)
        self.assertEqual(len(records), 3)  # An exact repeated source object is still one workout.
        before = copy.deepcopy(records)
        summaries = categorical.aggregate(records, date(2026, 7, 3))
        marker = "Workout Training Effect (Garmin)"
        entry = summaries["2026-07"][marker]
        self.assertEqual(entry["counts"], {"AEROBIC_BASE": 2, "RECOVERY": 1})
        self.assertEqual(entry["n_records"], 3)
        self.assertEqual(entry["n_days"], 1)
        followups, notes = {}, []
        monthly.apply_report_overlay(followups, notes, {"months": {}, "categorical_months": summaries})
        self.assertEqual(followups["2026-07"][marker], "AEROBIC_BASE: 2; RECOVERY: 1")
        self.assertEqual(records, before)

    def test_garmin_activity_ids_remain_distinct_even_with_equal_timestamps(self):
        records = garmin.categorical_inventory({"activities": [{"day": "2026-07-02", "data": [
            {"activityId": identifier, "startTimeLocal": "2026-07-02 09:00:00",
             "trainingEffectLabel": "AEROBIC_BASE"} for identifier in (1, 2)
        ]}]})
        for record in records:
            record["recorded_at"] = "2026-07-02T09:00:00+02:00"
        entry = categorical.aggregate(records + [copy.deepcopy(records[0])], date(2026, 7, 3))[
            "2026-07"]["Workout Training Effect (Garmin)"]
        self.assertEqual(entry["counts"], {"AEROBIC_BASE": 2})

    def test_missing_withings_timestamp_does_not_make_distinct_tests_duplicates(self):
        for stamp in (None, ""):
            records = [event("first", "2026-07-02"), event("second", "2026-07-02")]
            for record in records:
                if stamp is None:
                    record.pop("recorded_at")
                else:
                    record["recorded_at"] = stamp
            with self.subTest(timestamp=stamp):
                entry = categorical.aggregate(records, date(2026, 7, 3))[
                    "2026-07"]["ECG AF Classification (Withings)"]
                self.assertEqual(entry["counts"], {"Negative": 2})
                self.assertEqual(entry["n_days"], 1)

    def test_daily_garmin_statuses_still_count_completed_days_once(self):
        records = garmin.categorical_inventory({"hrv": [
            {"day": day, "data": {"hrvSummary": {"calendarDate": day, "status": "BALANCED"}}}
            for day in ("2026-07-01", "2026-07-02", "2026-07-03")
        ]})
        entry = categorical.aggregate(records + [copy.deepcopy(records[0])], date(2026, 7, 3))[
            "2026-07"]["HRV Status (Garmin)"]
        self.assertEqual(entry["counts"], {"BALANCED": 2})
        self.assertEqual(entry["n_days"], 2)
        self.assertEqual(entry["last_day"], "2026-07-02")

    def test_same_test_exposed_by_two_collections_is_counted_once(self):
        data = categorical.aggregate([event("measure", "2026-07-02"), event("heart", "2026-07-02"),
                                      event("later", "2026-07-03", "Inconclusive")], date(2026, 9, 6))
        entry = data["2026-07"]["ECG AF Classification (Withings)"]
        self.assertEqual(entry["counts"], {"Inconclusive": 1, "Negative": 1})
        self.assertEqual(entry["n_records"], 2)
        self.assertEqual(entry["aggregation"], "observed_classification_counts")

    def test_complete_month_replacement_and_partial_retention(self):
        old = [event("july", "2026-07-02"), event("aug", "2026-08-01")]
        args = [old, [], ["withings"], date(2026, 7, 1), date(2026, 7, 31)]
        self.assertEqual(categorical.merge(*args, complete=True), [old[1]])
        self.assertEqual(categorical.merge(*args, complete=False), old)

    def test_old_and_incomplete_oura_days_are_excluded(self):
        records = [event("old", "2026-06-30"), event("today", "2026-09-06", provider="oura"),
                   event("complete", "2026-09-05", provider="oura")]
        data = categorical.aggregate(records, date(2026, 9, 6))
        self.assertEqual(list(data), ["2026-09"])
        self.assertEqual(next(iter(data["2026-09"].values()))["n_records"], 1)

    def test_conflicting_identifier_is_rejected(self):
        with self.assertRaises(ValueError):
            categorical.validate([event("same", "2026-07-02"), event("same", "2026-07-02", "Positive")])

    def test_partial_file_keeps_other_tests_from_same_day(self):
        earlier = event("earlier", "2026-07-02")
        earlier["recorded_at"] = "2026-07-02T10:00:00+02:00"
        later = event("later", "2026-07-02", "Inconclusive")
        merged = categorical.merge([earlier], [later], ["withings"], date(2026, 7, 1),
                                   date(2026, 7, 31), complete=False)
        self.assertEqual(len(merged), 2)

    def test_classification_amendment_cannot_move_history_from_outside_requested_dates(self):
        incoming = [event("revised", "2026-08-15", "Inconclusive")]
        for day in ("2026-07-31", "2026-09-01"):
            for complete in (False, True):
                with self.subTest(day=day, complete=complete):
                    existing = [event("revised", day), event("untouched", "2026-08-01")]
                    before = copy.deepcopy(existing)
                    with self.assertRaisesRegex(ValueError, "outside.*requested date range"):
                        categorical.merge(existing, incoming, {"withings"},
                                          date(2026, 8, 1), date(2026, 8, 31), complete=complete)
                    self.assertEqual(existing, before)

    def test_classification_date_corrections_work_when_both_dates_are_in_range(self):
        for old_day, start in (("2026-08-01", date(2026, 8, 1)),
                               ("2026-07-31", date(2026, 7, 31))):
            with self.subTest(old_day=old_day):
                old = event("revised", old_day)
                corrected = event("revised", "2026-08-31", "Inconclusive")
                unrelated = {**event("revised", "2026-07-01"), "metric": "PPG AF Classification (Withings)"}
                existing = [old, unrelated]
                before = copy.deepcopy(existing)
                merged = categorical.merge(existing, [corrected], {"withings"},
                                           start, date(2026, 8, 31), complete=False)
                self.assertCountEqual(merged, [corrected, unrelated])
                self.assertEqual(existing, before)

    def test_legacy_breathing_codes_remain_in_cache_but_are_not_averaged_or_reported(self):
        old = [event("ecg", "2026-07-02")]
        for name in ("Breathing Disturbance Intensity (Withings)", "Breathing Quality Assessment (Withings)"):
            old.append({**event(name, "2026-07-02", "Device code -1"), "metric": name, "source_value": -1})
        before = copy.deepcopy(old)
        merged = categorical.merge(old, [], ["withings"], date(2026, 7, 1),
                                   date(2026, 7, 31), complete=False)
        self.assertEqual(len(merged), 3)
        summaries = categorical.aggregate(merged, date(2026, 9, 6))
        self.assertEqual(set(summaries["2026-07"]), {"ECG AF Classification (Withings)"})
        self.assertEqual(old, before)
