"""Synthetic Oura fixtures: no credentials or personal exports are required."""

import csv
import tempfile
import unittest
from pathlib import Path

from health_sync.oura import OURA_ENDPOINTS, OuraParseError, parse_api, parse_csv


def sleep_document(identifier="main", day="2026-08-01", **changes):
    document = {
        "id": identifier,
        "day": day,
        "type": "long_sleep",
        "bedtime_start": day + "T00:00:00+02:00",
        "bedtime_end": day + "T09:00:00+02:00",
        "total_sleep_duration": 27000,
        "time_in_bed": 32400,
        "deep_sleep_duration": 3600,
        "rem_sleep_duration": 6000,
        "light_sleep_duration": 17400,
        "average_heart_rate": 65.25,
        "lowest_heart_rate": 55,
        "average_hrv": 24,
        "average_breath": 12.375,
        "efficiency": 83,
        "latency": 450,
        "readiness": {"score": 12},
        "contributors": {"deep_sleep": 99, "rem_sleep": 95},
    }
    document.update(changes)
    return document


def daily_document(identifier="daily", day="2026-08-01", score=81, **changes):
    document = {
        "id": identifier,
        "day": day,
        "score": score,
        "timestamp": day + "T09:01:00+02:00",
        "contributors": {"total_sleep": 98, "deep_sleep": 99, "latency": 97},
    }
    document.update(changes)
    return document


def by_metric(records):
    return {record["metric"]: record for record in records}


class OuraCSVTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "oura.csv"

    def write_csv(self, rows, headers=None):
        if headers is None:
            headers = list(rows[0])
        with self.path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return self.path

    def test_exact_field_mapping_seconds_and_no_contributor_scores(self):
        row = {
            " date ": "2026-08-01", "Total Sleep Duration": "27030",
            "REM Sleep Duration": "6300", "Deep Sleep Duration": "3630",
            "Light Sleep Duration": "17100", "Average Resting Heart Rate": "65.53",
            "Lowest Resting Heart Rate": "58", "Average HRV": "23",
            "Respiratory Rate": "12.375", "Sleep Efficiency": "90",
            "Sleep Latency": "390", "Sleep Score": "81", "Total Bedtime ": "32400",
            "Bedtime End": "2026-08-01T09:00:00+02:00",
            "Deep Sleep Score": "99", "REM Sleep Score": "98",
            "Sleep Latency Score": "97", "Total Sleep Score": "96",
        }
        records = parse_csv(self.write_csv([row]))
        values = by_metric(records)
        self.assertEqual(len(records), 11)
        self.assertEqual(values["Sleep Duration"]["value"], 27030 / 3600)
        self.assertEqual(values["REM Sleep"]["value"], 1.75)
        self.assertEqual(values["Deep Sleep"]["value"], 3630 / 3600)
        self.assertEqual(values["Sleep Latency"]["value"], 6.5)
        self.assertEqual(values["Time in Bed"]["value"], 9)
        self.assertEqual(values["Sleep Score"]["value"], 81)
        self.assertEqual(values["Average Sleeping HR (Oura)"]["value"], 65.53)
        self.assertEqual(values["Respiratory Rate (Sleep)"]["unit"], "/min")
        self.assertEqual(values["Sleep Duration"]["source_kind"], "csv")
        self.assertTrue(all(record["provider"] == "oura" for record in records))

    def test_blank_incomplete_days_omitted_and_optional_null_not_zero(self):
        rows = [
            {"date": "2026-08-01", "Total Sleep Duration": "27000", "Average HRV": ""},
            {"date": "2026-08-02", "Total Sleep Duration": "", "Average HRV": ""},
            {"date": "2026-08-03", "Total Sleep Duration": "0", "Average HRV": ""},
        ]
        result = parse_csv(self.write_csv(rows))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["day"], "2026-08-01")
        self.assertNotIn("recorded_at", result[0])

    def test_identical_duplicate_days_deduplicate_and_ids_stable(self):
        row = {"date": "2026-08-01", "Total Sleep Duration": "27000"}
        once = parse_csv(self.write_csv([row]))
        twice = parse_csv(self.write_csv([row, row]))
        self.assertEqual(once, twice)

    def test_conflicting_duplicate_days_rejected(self):
        rows = [
            {"date": "2026-08-01", "Total Sleep Duration": "27000"},
            {"date": "2026-08-01", "Total Sleep Duration": "28000"},
        ]
        with self.assertRaisesRegex(OuraParseError, "conflicting duplicate"):
            parse_csv(self.write_csv(rows))

    def test_malformed_dates_nonfinite_and_negative_values_rejected(self):
        for day, duration in [("2026-02-30", "27000"), ("20260801", "27000"),
                              ("2026-08-01", "NaN"), ("2026-08-01", "Infinity"),
                              ("2026-08-01", "-1"), ("2026-08-01", "unknown")]:
            with self.subTest(day=day, duration=duration), self.assertRaises(OuraParseError):
                parse_csv(self.write_csv([{"date": day, "Total Sleep Duration": duration}]))

    def test_duplicate_headers_missing_required_header_and_ragged_rows(self):
        for text in ["date,date,Total Sleep Duration\n2026-08-01,2026-08-01,27000\n",
                     "date,Sleep Score\n2026-08-01,81\n",
                     "date,Total Sleep Duration\n2026-08-01,27000,extra\n"]:
            with self.subTest(text=text), self.assertRaises(OuraParseError):
                self.path.write_text(text, encoding="utf-8")
                parse_csv(self.path)

    def test_impossible_stage_sum_rejected(self):
        row = {"date": "2026-08-01", "Total Sleep Duration": "27000",
               "REM Sleep Duration": "100", "Deep Sleep Duration": "100",
               "Light Sleep Duration": "100"}
        with self.assertRaisesRegex(OuraParseError, "stages do not sum"):
            parse_csv(self.write_csv([row]))

    def test_calendar_filtering_and_rounding_belong_to_caller(self):
        rows = [
            {"date": "2099-09-01", "Total Sleep Duration": "27030"},
            {"date": "2026-08-31", "Total Sleep Duration": "27000"},
        ]
        values = parse_csv(self.write_csv(rows))
        self.assertEqual([row["day"] for row in values], ["2026-08-31", "2099-09-01"])
        self.assertEqual(values[1]["value"], 7.508333333333334)


class OuraAPITests(unittest.TestCase):
    def test_primary_sleep_mapping_and_daily_score(self):
        result = by_metric(parse_api({"sleep": [sleep_document()],
                                      "daily_sleep": [daily_document()]}))
        self.assertEqual(len(result), 11)
        self.assertEqual(OURA_ENDPOINTS, ["sleep", "daily_sleep"])
        self.assertEqual(result["Sleep Duration"]["value"], 7.5)
        self.assertEqual(result["Deep Sleep"]["value"], 1)
        self.assertEqual(result["Sleep Latency"]["value"], 7.5)
        self.assertEqual(result["Sleep Score"]["value"], 81)
        self.assertEqual(result["Average Sleeping HR (Oura)"]["value"], 65.25)
        self.assertEqual(result["Mean Nightly Lowest HR (Oura)"]["value"], 55)
        self.assertEqual(result["Time in Bed"]["unit"], "h")
        self.assertEqual(result["Sleep Duration"]["source_kind"], "api")

    def test_largest_long_sleep_chosen_once_independent_of_input_order(self):
        shorter = sleep_document("shorter", total_sleep_duration=18000,
                                 light_sleep_duration=8400, average_heart_rate=70)
        longer = sleep_document("longer")
        nap = sleep_document("nap", type="sleep", total_sleep_duration=35000)
        rejected = sleep_document("rejected", type="rest")
        deleted = sleep_document("deleted", type="deleted")
        records = [shorter, nap, rejected, longer, deleted]
        first = parse_api({"sleep": records})
        second = parse_api({"sleep": list(reversed(records))})
        self.assertEqual(first, second)
        self.assertEqual(len(first), 10)
        self.assertEqual(by_metric(first)["Average Sleeping HR (Oura)"]["value"], 65.25)

    def test_tied_periods_choose_latest_end_then_stable_id(self):
        early = sleep_document("z-early")
        later_a = sleep_document("a-later", bedtime_end="2026-08-01T10:00:00+02:00")
        later_b = sleep_document("b-later", bedtime_end="2026-08-01T10:00:00+02:00")
        records = parse_api({"sleep": [later_b, early, later_a]})
        self.assertTrue(all(":sleep:b-later:" in record["id"] for record in records))

    def test_missing_sleep_total_or_bedtime_excludes_incomplete_day_and_score(self):
        for changes in [{"total_sleep_duration": None}, {"time_in_bed": None},
                        {"bedtime_end": None}, {"bedtime_start": None}]:
            with self.subTest(changes=changes):
                result = parse_api({"sleep": [sleep_document(**changes)],
                                    "daily_sleep": [daily_document()]})
                self.assertEqual(result, [])

    def test_optional_null_fields_omitted_and_valid_zero_preserved(self):
        result = by_metric(parse_api({
            "sleep": [sleep_document(average_hrv=None, average_breath=None, latency=0)],
            "daily_sleep": [daily_document(score=0)],
        }))
        self.assertNotIn("Average HRV (Sleep)", result)
        self.assertNotIn("Respiratory Rate (Sleep)", result)
        self.assertEqual(result["Sleep Latency"]["value"], 0)
        self.assertEqual(result["Sleep Score"]["value"], 0)

    def test_null_daily_score_never_uses_contributors_or_readiness(self):
        result = by_metric(parse_api({"sleep": [sleep_document()],
                                      "daily_sleep": [daily_document(score=None)]}))
        self.assertNotIn("Sleep Score", result)
        self.assertEqual(result["Deep Sleep"]["value"], 1)

    def test_identical_ids_deduplicate_conflicting_ids_rejected(self):
        document = sleep_document()
        result = parse_api({"sleep": [document, document]})
        self.assertEqual(len(result), 10)
        with self.assertRaisesRegex(OuraParseError, "conflicting duplicate"):
            parse_api({"sleep": [document, sleep_document(average_hrv=99)]})
        with self.assertRaisesRegex(OuraParseError, "conflicting duplicate"):
            parse_api({"daily_sleep": [daily_document(), daily_document(score=90)]})

    def test_daily_documents_same_day_choose_latest_without_double_weighting(self):
        early = daily_document("early", score=75)
        late = daily_document("late", score=85, timestamp="2026-08-01T10:00:00+02:00")
        payload = {"sleep": [sleep_document()], "daily_sleep": [late, early]}
        result = by_metric(parse_api(payload))
        self.assertEqual(result["Sleep Score"]["value"], 85)

    def test_invalid_shapes_dates_and_nonnumeric_or_impossible_values_rejected(self):
        for payload in [{"sleep": {}}, {"sleep": [None]},
                        {"sleep": [sleep_document(day="2026-02-30")]},
                        {"sleep": [sleep_document(id="")]},
                        {"sleep": [sleep_document(average_hrv=float("nan"))]},
                        {"sleep": [sleep_document(average_hrv=True)]},
                        {"sleep": [sleep_document(average_hrv="23")]},
                        {"sleep": [sleep_document(efficiency=101)]},
                        {"sleep": [sleep_document(average_heart_rate=0)]},
                        {"sleep": [sleep_document(total_sleep_duration=40000)]},
                        {"sleep": [sleep_document(bedtime_end="2026-08-01T00:00:00+02:00")]},
                        {"sleep": [sleep_document(bedtime_end="2026-08-01T09:00:00")]},
                        {"sleep": [sleep_document(type=[])]},
                        {"sleep": [sleep_document(type="unknown")]}]:
            with self.subTest(payload=payload), self.assertRaises(OuraParseError):
                parse_api(payload)

    def test_sleep_day_is_authoritative_across_timezones(self):
        document = sleep_document(day="2026-08-02",
                                  bedtime_start="2026-08-01T15:00:00-10:00",
                                  bedtime_end="2026-08-02T00:00:00-10:00")
        self.assertEqual({row["day"] for row in parse_api({"sleep": [document]})},
                         {"2026-08-02"})


if __name__ == "__main__":
    unittest.main()
