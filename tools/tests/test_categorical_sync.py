from datetime import date
import unittest

from tools.health_sync import categorical


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
