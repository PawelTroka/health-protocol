"""Synthetic Garmin parser fixtures; never reads credentials or contacts Garmin."""

import copy
import unittest

from tools.health_sync.garmin import (
    GARMIN_CATEGORICAL_METRICS,
    GARMIN_ENDPOINTS,
    GARMIN_METRICS,
    GarminParseError,
    categorical_inventory,
    parse_api,
)


DAY = "2026-09-16"


def payload(endpoint, data, day=DAY):
    return {endpoint: [{"day": day, "data": data}]}


def by_metric(records):
    return {record["metric"]: record for record in records}


def morning(**changes):
    result = {"calendarDate": DAY, "inputContext": "AFTER_WAKEUP_RESET",
              "timestamp": DAY + "T07:00:00.000Z", "score": 83, "recoveryTime": 90}
    result.update(changes)
    return result


class GarminParserTests(unittest.TestCase):
    def test_registry_covers_only_verified_fields_with_provider_suffixes(self):
        self.assertEqual(GARMIN_ENDPOINTS, ["daily_summary", "sleep", "hrv", "training_readiness"])
        self.assertEqual(len(GARMIN_METRICS), 32)
        self.assertTrue(all(name.endswith(" (Garmin)") for name in GARMIN_METRICS))
        self.assertEqual(GARMIN_CATEGORICAL_METRICS, {"HRV Status (Garmin)"})
        self.assertEqual(GARMIN_METRICS["Morning Recovery Time (Garmin)"], ("h", 2))
        self.assertEqual(parse_api({"max_metrics": [{"vo2Max": 55}]}), [])

    def test_daily_field_mapping_and_exact_source_units(self):
        values = by_metric(parse_api(payload("daily_summary", {
            "calendarDate": DAY, "totalSteps": 12345, "totalDistanceMeters": 9123.5,
            "totalKilocalories": 2432.1, "activeKilocalories": 530.2,
            "bmrKilocalories": 1901.9, "restingHeartRate": 51, "minHeartRate": 45,
            "maxHeartRate": 143, "moderateIntensityMinutes": 12,
            "vigorousIntensityMinutes": 34, "floorsAscended": 7.2,
            "floorsDescended": 8.3, "averageStressLevel": 22, "maxStressLevel": 91,
            "bodyBatteryHighestValue": 89, "bodyBatteryLowestValue": 15,
            "bodyBatteryChargedValue": 64, "bodyBatteryDrainedValue": 78,
        })))
        expected = {
            "Steps": (12345, "steps"), "Distance": (9.1235, "km"),
            "Total Energy Expenditure": (2432.1, "kcal"), "Active Energy": (530.2, "kcal"),
            "Basal Energy Expenditure": (1901.9, "kcal"), "Resting HR": (51, "bpm"),
            "Daily Minimum HR": (45, "bpm"), "Daily Maximum HR": (143, "bpm"),
            "Moderate Intensity Minutes": (12, "min"), "Vigorous Intensity Minutes": (34, "min"),
            "Floors Ascended": (7.2, "floors"), "Floors Descended": (8.3, "floors"),
            "Average Stress": (22, "score"), "Maximum Stress": (91, "score"),
            "Body Battery Highest": (89, "score"), "Body Battery Lowest": (15, "score"),
            "Body Battery Charged": (64, "points"), "Body Battery Drained": (78, "points"),
        }
        self.assertEqual(len(values), len(expected))
        for name, (value, unit) in expected.items():
            with self.subTest(name=name):
                record = values[name + " (Garmin)"]
                self.assertAlmostEqual(record["value"], value)
                self.assertEqual(record["unit"], unit)
                self.assertEqual(record["provider"], "garmin")
                self.assertEqual(record["source_kind"], "api")
                self.assertEqual(record["source_endpoint"], "daily_summary")
                self.assertEqual(record["id"], f"garmin:api:daily_summary:{DAY}:{record['metric']}")

    def test_zero_activity_and_stress_are_kept_on_observed_days(self):
        result = by_metric(parse_api(payload("daily_summary", {
            "restingHeartRate": 52, "totalSteps": 0, "averageStressLevel": 0,
            "activeKilocalories": 0, "vigorousIntensityMinutes": 0,
        })))
        self.assertEqual(len(result), 5)
        self.assertEqual(result["Steps (Garmin)"]["value"], 0)
        self.assertEqual(result["Average Stress (Garmin)"]["value"], 0)

    def test_all_zero_daily_placeholder_is_omitted(self):
        self.assertEqual(parse_api(payload("daily_summary", {
            "totalSteps": 0, "restingHeartRate": 0, "activeKilocalories": 0,
            "averageStressLevel": -1, "bodyBatteryChargedValue": None,
        })), [])

    def test_sleep_observation_also_qualifies_legitimate_zero_activity(self):
        data = payload("daily_summary", {"totalSteps": 0, "activeKilocalories": 0})
        data.update(payload("sleep", {"dailySleepDTO": {"sleepTimeSeconds": 25200}}))
        values = by_metric(parse_api(data))
        self.assertEqual(values["Steps (Garmin)"]["value"], 0)
        self.assertEqual(values["Sleep Duration (Garmin)"]["value"], 7)

    def test_modeled_calories_do_not_establish_wear_for_zero_activity(self):
        values = by_metric(parse_api(payload("daily_summary", {
            "bmrKilocalories": 1700, "totalKilocalories": 1700, "totalSteps": 0,
            "activeKilocalories": 0, "averageStressLevel": 0,
        })))
        self.assertEqual(set(values), {
            "Basal Energy Expenditure (Garmin)", "Total Energy Expenditure (Garmin)"})

    def test_sleep_units_nested_fields_and_no_timestamp_timezone_guessing(self):
        result = by_metric(parse_api(payload("sleep", {"dailySleepDTO": {
            "calendarDate": DAY, "sleepTimeSeconds": 27030, "deepSleepSeconds": 4500,
            "lightSleepSeconds": 15000, "remSleepSeconds": 7530, "awakeSleepSeconds": 300,
            "napTimeSeconds": 1800, "sleepScores": {"overall": {"value": 84}},
            "avgSpO2": 96.5, "averageRespirationValue": 13.25,
            "sleepEndTimestampLocal": 1789542000000,
        }})))
        self.assertEqual(len(result), 9)
        self.assertEqual(result["Sleep Duration (Garmin)"]["value"], 27030 / 3600)
        self.assertEqual(result["Deep Sleep (Garmin)"]["value"], 1.25)
        self.assertEqual(result["Nap Duration (Garmin)"]["value"], 0.5)
        self.assertEqual(result["Sleep Score (Garmin)"]["value"], 84)
        self.assertEqual(result["Average Sleeping SpO2 (Garmin)"]["unit"], "%")
        self.assertEqual(result["Respiratory Rate (Sleep) (Garmin)"]["unit"], "/min")
        self.assertTrue(all("recorded_at" not in item for item in result.values()))

    def test_explicit_zero_main_sleep_excludes_nightly_placeholder_but_keeps_nap(self):
        result = by_metric(parse_api(payload("sleep", {"dailySleepDTO": {
            "sleepTimeSeconds": 0, "deepSleepSeconds": 0, "sleepScores": {"overall": {"value": 0}},
            "napTimeSeconds": 1200,
        }})))
        self.assertEqual(set(result), {"Nap Duration (Garmin)"})
        self.assertEqual(result["Nap Duration (Garmin)"]["value"], 1 / 3)

    def test_optional_total_sleep_missing_does_not_hide_real_sleep_score(self):
        result = parse_api(payload("sleep", {"dailySleepDTO": {
            "sleepScores": {"overall": {"value": 91}},
        }}))
        self.assertEqual(result[0]["metric"], "Sleep Score (Garmin)")

    def test_missing_and_negative_sentinels_do_not_become_zero(self):
        values = by_metric(parse_api(payload("daily_summary", {
            "totalSteps": 1700, "restingHeartRate": 0, "minHeartRate": -1,
            "averageStressLevel": -1, "maxStressLevel": -2,
            "bodyBatteryLowestValue": None,
        })))
        self.assertEqual(set(values), {"Steps (Garmin)"})
        self.assertEqual(parse_api(payload("hrv", {"hrvSummary": {
            "lastNightAvg": 0, "lastNight5MinHigh": -1, "weeklyAvg": None,
        }})), [])

    def test_empty_and_nullable_responses_are_omitted(self):
        data = {endpoint: [{"day": DAY, "data": None}] for endpoint in GARMIN_ENDPOINTS}
        self.assertEqual(parse_api(data), [])
        self.assertEqual(categorical_inventory(data), [])
        self.assertEqual(parse_api(payload("training_readiness", [])), [])
        self.assertEqual(parse_api(payload("sleep", {"dailySleepDTO": None})), [])

    def test_numeric_values_require_finite_json_numbers(self):
        for invalid in ["123", True, False, [], {}, float("nan"), float("inf"), -float("inf")]:
            with self.subTest(value=repr(invalid)), self.assertRaises(GarminParseError):
                parse_api(payload("daily_summary", {"totalSteps": invalid}))

    def test_bounded_percentage_and_score_fields_reject_overflow(self):
        for endpoint, data in [
            ("daily_summary", {"averageStressLevel": 101}),
            ("sleep", {"dailySleepDTO": {"avgSpO2": 100.1}}),
            ("training_readiness", morning(score=101)),
        ]:
            with self.subTest(endpoint=endpoint), self.assertRaises(GarminParseError):
                parse_api(payload(endpoint, data))

    def test_hrv_fields_preserve_nightly_and_rolling_distinctions(self):
        values = by_metric(parse_api(payload("hrv", {"hrvSummary": {
            "calendarDate": DAY, "lastNightAvg": 43.3, "lastNight5MinHigh": 61.2,
            "weeklyAvg": 39.4, "status": "BALANCED",
        }})))
        self.assertEqual(values["Average Nightly HRV (Garmin)"]["value"], 43.3)
        self.assertEqual(values["Highest 5-minute Nightly HRV (Garmin)"]["value"], 61.2)
        self.assertEqual(values["7-day Average HRV (Garmin)"]["value"], 39.4)
        self.assertTrue(all(record["unit"] == "ms" for record in values.values()))

    def test_categorical_status_preserves_text_including_future_values(self):
        for status in ["BALANCED", "NEW_VENDOR_STATUS"]:
            with self.subTest(status=status):
                data = payload("hrv", {"hrvSummary": {"status": status}})
                result = categorical_inventory(data)
                self.assertEqual(len(result), 1)
                self.assertEqual(result[0]["value"], status)
                self.assertEqual(result[0]["source_value"], status)
                self.assertEqual(result[0]["source_endpoint"], "hrv")
                self.assertNotIn("unit", result[0])
                self.assertEqual(parse_api(data), [])
        for invalid in ["", "  ", 1, True, []]:
            with self.subTest(value=invalid), self.assertRaises(GarminParseError):
                categorical_inventory(payload("hrv", {"hrvSummary": {"status": invalid}}))

    def test_readiness_uses_latest_explicit_morning_snapshot_only(self):
        result = by_metric(parse_api(payload("training_readiness", [
            morning(score=70), morning(timestamp=DAY + "T08:00:00Z", score=81),
            morning(timestamp=DAY + "T22:00:00Z", inputContext="AFTER_ACTIVITY", score=20),
        ])))
        self.assertEqual(result["Morning Training Readiness (Garmin)"]["value"], 81)
        self.assertEqual(result["Morning Recovery Time (Garmin)"]["value"], 1.5)

    def test_readiness_without_morning_context_is_not_guessed(self):
        for data in [morning(inputContext=None), [morning(inputContext="AFTER_ACTIVITY")]]:
            with self.subTest(data=data):
                self.assertEqual(parse_api(payload("training_readiness", data)), [])

    def test_recovery_reached_zero_overrides_stale_remaining_minutes(self):
        data = payload("training_readiness", morning(recoveryTime=1440, recoveryTimeChangePhrase="REACHED_ZERO"))
        values = by_metric(parse_api(data))
        self.assertEqual(values["Morning Recovery Time (Garmin)"]["value"], 0)
        values = by_metric(parse_api(payload("training_readiness", morning(recoveryTime=None))))
        self.assertNotIn("Morning Recovery Time (Garmin)", values)

    def test_ambiguous_multiple_morning_readings_fail_instead_of_double_weighting(self):
        pairs = [
            [morning(timestamp=None), morning(score=70)],
            [morning(score=70), morning(score=80)],
            [morning(timestamp=DAY + "T07:00:00"), morning()],
        ]
        for entries in pairs:
            with self.subTest(entries=entries), self.assertRaises(GarminParseError):
                parse_api(payload("training_readiness", entries))
        self.assertEqual(len(parse_api(payload("training_readiness", [morning(), morning()]))), 2)

    def test_morning_selection_accounts_for_timestamp_offsets(self):
        data = payload("training_readiness", [
            morning(timestamp=DAY + "T08:00:00+02:00", score=70),
            morning(timestamp=DAY + "T07:00:00Z", score=80),
        ])
        values = by_metric(parse_api(data))
        self.assertEqual(values["Morning Training Readiness (Garmin)"]["value"], 80)

    def test_source_calendar_date_must_match_requested_date_for_all_endpoints(self):
        wrong = "2026-09-15"
        for endpoint, data in [
            ("daily_summary", {"calendarDate": wrong, "totalSteps": 10}),
            ("sleep", {"dailySleepDTO": {"calendarDate": wrong, "sleepTimeSeconds": 18000}}),
            ("hrv", {"hrvSummary": {"calendarDate": wrong, "lastNightAvg": 20}}),
            ("training_readiness", morning(calendarDate=wrong)),
        ]:
            with self.subTest(endpoint=endpoint), self.assertRaises(GarminParseError):
                parse_api(payload(endpoint, data))
        with self.assertRaises(GarminParseError):
            categorical_inventory(payload("hrv", {"hrvSummary": {"calendarDate": wrong, "status": "BALANCED"}}))

    def test_invalid_envelope_dates_and_shapes_are_rejected(self):
        invalid = [
            [], {"hrv": None}, {"daily_summary": [None]},
            {"daily_summary": [{"day": DAY}]}, payload("daily_summary", 3),
            payload("daily_summary", {}, day="2026-02-30"),
            payload("daily_summary", {}, day="2026-9-16"),
            payload("sleep", {"dailySleepDTO": []}),
            payload("sleep", {"dailySleepDTO": {"sleepScores": "bad"}}),
            payload("training_readiness", [42]),
        ]
        for data in invalid:
            with self.subTest(data=data), self.assertRaises(GarminParseError):
                parse_api(data)

    def test_duplicate_envelopes_deduplicate_but_conflicts_fail(self):
        data = payload("daily_summary", {"totalSteps": 10})
        data["daily_summary"].append(copy.deepcopy(data["daily_summary"][0]))
        self.assertEqual(len(parse_api(data)), 1)
        data["daily_summary"][1]["data"]["totalSteps"] = 11
        with self.assertRaises(GarminParseError):
            parse_api(data)

    def test_private_summary_cannot_be_interpreted_as_measurement(self):
        with self.assertRaises(GarminParseError):
            parse_api(payload("daily_summary", {"privacyProtected": True, "totalSteps": 0}))
        for endpoint, key in [("sleep", "dailySleepDTO"), ("hrv", "hrvSummary")]:
            with self.subTest(endpoint=endpoint), self.assertRaises(GarminParseError):
                parse_api(payload(endpoint, {"privacyProtected": True, key: {}}))

    def test_sync_metadata_is_ignored_and_inputs_are_not_mutated(self):
        data = payload("training_readiness", [morning()])
        data["_sync"] = {"endpoint_status": {"training_readiness": {"status": "complete"}}}
        before = copy.deepcopy(data)
        first = parse_api(data)
        self.assertEqual(data, before)
        self.assertEqual(first, parse_api(data))


if __name__ == "__main__":
    unittest.main()
