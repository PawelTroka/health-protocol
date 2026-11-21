import copy
from datetime import date
import unittest

from tools.health_sync import categorical, garmin


def event(key, day, value="Negative", provider="withings"):
    return {"id": key, "day": day, "provider": provider,
            "metric": "ECG AF Classification (Withings)", "value": value,
            "recorded_at": day + "T12:00:00+02:00"}


class ClassificationTests(unittest.TestCase):
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


class WorkoutClassificationTests(unittest.TestCase):
    def inventory(self, day, activities):
        return garmin.categorical_inventory({"activities": [{"day": day, "data": activities}]})

    def workout(self, identifier, day="2026-07-02", label="AEROBIC_BASE", **fields):
        return {"activityId": identifier, "startTimeLocal": day + " 12:00:00",
                "trainingEffectLabel": label, **fields}

    def summary(self, events):
        return categorical.aggregate(events, date(2026, 8, 1))["2026-07"]["Workout Training Effect (Garmin)"]

    def test_same_label_workouts_count_individually_with_distinct_day_coverage(self):
        events = self.inventory("2026-07-02", [self.workout(1), self.workout(2)])
        events += self.inventory("2026-07-03", [self.workout(3, "2026-07-03")])
        before = copy.deepcopy(events)
        entry = self.summary(events)
        self.assertEqual(entry["counts"], {"AEROBIC_BASE": 3})
        self.assertEqual(entry["value"], "AEROBIC_BASE: 3")
        self.assertEqual(entry["n_records"], 3)
        self.assertEqual(entry["n_days"], 2)
        self.assertEqual((entry["first_day"], entry["last_day"]), ("2026-07-02", "2026-07-03"))
        self.assertEqual(events, before)

    def test_same_timestamp_does_not_merge_distinct_garmin_workout_ids(self):
        events = self.inventory("2026-07-02", [self.workout(1), self.workout(2)])
        for record in events:
            record["recorded_at"] = "2026-07-02T12:00:00+02:00"
        self.assertEqual(self.summary(events)["counts"], {"AEROBIC_BASE": 2})

    def test_repeated_activity_and_multisport_component_do_not_inflate_counts(self):
        parent = self.workout(1)
        activities = [parent, copy.deepcopy(parent), self.workout(2),
                      self.workout(3, label="ANAEROBIC_CAPACITY"), self.workout(4, parentId=1)]
        events = self.inventory("2026-07-02", activities)
        # An exact repeated normalized observation is also harmless.
        entry = self.summary(events + [copy.deepcopy(events[0])])
        self.assertEqual(entry["counts"], {"AEROBIC_BASE": 2, "ANAEROBIC_CAPACITY": 1})
        self.assertEqual(entry["n_records"], 3)
        self.assertEqual(entry["n_days"], 1)

    def test_partial_amendment_updates_one_workout_without_recounting_or_losing_others(self):
        old = self.inventory("2026-07-02", [self.workout(1), self.workout(2), self.workout(3)])
        incoming = self.inventory("2026-07-02", [self.workout(1, label="RECOVERY")])
        merged = categorical.merge(old, incoming, ["garmin"], date(2026, 7, 1),
                                   date(2026, 7, 31), complete=False)
        entry = self.summary(merged)
        self.assertEqual(entry["counts"], {"AEROBIC_BASE": 2, "RECOVERY": 1})
        self.assertEqual(entry["n_records"], 3)
        self.assertEqual(len(merged), 3)

    def test_untimestamped_withings_records_do_not_become_same_day_duplicates(self):
        events = [event("first", "2026-07-02"), event("second", "2026-07-02")]
        for record in events:
            del record["recorded_at"]
        entry = categorical.aggregate(events, date(2026, 8, 1))["2026-07"]["ECG AF Classification (Withings)"]
        self.assertEqual(entry["counts"], {"Negative": 2})
        self.assertEqual(entry["n_records"], 2)
        self.assertEqual(entry["n_days"], 1)
