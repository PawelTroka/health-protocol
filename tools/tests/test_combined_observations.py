from datetime import date
import unittest

from tools.health_sync.monthly import aggregate
from tools.health_sync.withings import parse_api


class CombinedObservationTests(unittest.TestCase):
    def test_unavailable_zero_pulse_does_not_lower_monthly_mean(self):
        records = parse_api({"activities": [
            {"date": "2026-07-01", "hr_average": 0, "hr_min": 0, "hr_max": 0, "steps": 0},
            {"date": "2026-07-02", "hr_average": 65, "hr_min": 50, "hr_max": 90, "steps": 1200},
        ]})
        metrics = aggregate(records, date(2026, 9, 6))["months"]["2026-07"]
        self.assertEqual(metrics["Average Daily HR (Withings)"]["value"], "65.0")
        self.assertEqual(metrics["Average Daily HR (Withings)"]["n_days"], 1)
        self.assertEqual(metrics["Steps (Withings)"]["value"], "600.0")

    def test_combined_daily_value_keeps_underlying_session_coverage(self):
        record = {"provider": "withings", "id": "withings:sleep:daily-1:Sleep Duration (Withings)",
                  "day": "2026-07-02", "metric": "Sleep Duration (Withings)", "value": 8,
                  "unit": "h", "source_kind": "api", "source_count": 2,
                  "daily_aggregation": "sum_nonoverlapping_sessions"}
        entry = aggregate([record], date(2026, 9, 6))["months"]["2026-07"][record["metric"]]
        self.assertEqual(entry["value"], "8.00")
        self.assertEqual((entry["n_days"], entry["n_records"]), (1, 2))
        self.assertEqual(entry["daily_aggregation"], ["sum_nonoverlapping_sessions"])

    def test_invalid_combined_source_count_is_rejected(self):
        record = {"provider": "withings", "id": "weight", "day": "2026-07-02",
                  "metric": "Body Mass", "value": 80, "unit": "kg", "source_kind": "api", "source_count": 0}
        with self.assertRaises(ValueError):
            aggregate([record], date(2026, 9, 6))
