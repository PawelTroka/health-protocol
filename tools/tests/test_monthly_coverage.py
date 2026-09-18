"""Observed-day identity is required before combining sparse monthly metrics."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from tools.health_sync.monthly import aggregate, load_monthly


def reading(day, value=100, *, provider="withings", metric=None, suffix=""):
    return {
        "id": f"{provider}:{day}:{suffix}",
        "day": day,
        "provider": provider,
        "metric": metric or f"Steps ({provider.title()})",
        "unit": "steps",
        "value": value,
        "source_kind": "api",
    }


class MonthlyCoverageTests(unittest.TestCase):
    def setUp(self):
        self.payload = aggregate([
            reading("2026-07-05", 500),
            reading("2026-07-01", 100),
            reading("2026-07-03", 300),
        ], date(2026, 8, 1))

    def load(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "monthly.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_monthly(path)

    def entry(self, payload=None):
        return (payload or self.payload)["months"]["2026-07"]["Steps (Withings)"]

    def test_aggregate_records_actual_sorted_unique_days(self):
        records = [reading("2026-07-05", 500), reading("2026-07-01", 100),
                   reading("2026-07-03", 300), reading("2026-07-03", 900, suffix="second")]
        result = aggregate(records, date(2026, 8, 1))
        entry = self.entry(result)
        self.assertEqual(entry["observed_days"], "2026-07-01,2026-07-03,2026-07-05")
        self.assertEqual(entry["n_days"], 3)
        self.assertEqual(entry["n_records"], 4)
        self.assertEqual(entry["value"], "400.0")  # Daily means: 100, 600, 500.
        self.assertEqual(result, aggregate(list(reversed(records)), date(2026, 8, 1)))

    def test_same_counts_and_endpoints_do_not_imply_same_days(self):
        alternate = aggregate([reading("2026-07-01"), reading("2026-07-04"),
                               reading("2026-07-05")], date(2026, 8, 1))
        left, right = self.entry(), self.entry(alternate)
        for key in ("n_days", "first_day", "last_day"):
            self.assertEqual(left[key], right[key])
        self.assertNotEqual(left["observed_days"], right["observed_days"])

    def test_current_day_deferral_is_preserved_in_metadata(self):
        records = [reading(day, provider=provider)
                   for provider in ("oura", "withings", "garmin")
                   for day in ("2026-09-15", "2026-09-17")]
        metrics = aggregate(records, date(2026, 9, 17))["months"]["2026-09"]
        self.assertEqual(metrics["Steps (Withings)"]["observed_days"],
                         "2026-09-15,2026-09-17")
        for marker in ("Steps (Oura)", "Steps (Garmin)"):
            self.assertEqual(metrics[marker]["observed_days"], "2026-09-15")

    def test_new_coverage_round_trips(self):
        self.assertEqual(self.load(self.payload), self.payload)

    def test_legacy_entries_without_day_list_remain_readable(self):
        payload = deepcopy(self.payload)
        del self.entry(payload)["observed_days"]
        self.assertEqual(self.load(payload), payload)

    def test_invalid_day_encoding_is_rejected(self):
        invalid = (
            None,
            "2026-07-01",
            [],
            ["2026-07-01", "2026-07-03", "2026-07-05"],
            "2026-07-01,2026-07-05",
            "2026-07-01,2026-07-01,2026-07-05",
            "2026-07-05,2026-07-03,2026-07-01",
            "2026-07-01,2026-07-03,2026-07-04",
            "2026-07-02,2026-07-03,2026-07-05",
            "2026-06-30,2026-07-03,2026-07-05",
            "2026-07-01,2026-07-03,2026-08-01",
            "2026-07-01,2026-07-3,2026-07-05",
            "2026-07-01,2026-07-32,2026-07-05",
            "2026-07-01, 2026-07-03,2026-07-05",
            "2026-07-01,,2026-07-05",
        )
        for observed_days in invalid:
            with self.subTest(observed_days=observed_days):
                payload = deepcopy(self.payload)
                self.entry(payload)["observed_days"] = observed_days
                with self.assertRaises(ValueError):
                    self.load(payload)

    def test_invalid_future_day_is_rejected(self):
        payload = aggregate([reading("2026-09-01"), reading("2026-09-03")], date(2026, 9, 5))
        entry = payload["months"]["2026-09"]["Steps (Withings)"]
        entry["observed_days"] = "2026-09-01,2026-09-06"
        with self.assertRaises(ValueError):
            self.load(payload)


if __name__ == "__main__":
    unittest.main()
