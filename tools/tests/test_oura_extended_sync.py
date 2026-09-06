"""Public API-schema fixtures exercising extended Oura units and provenance."""

import unittest

from tools.health_sync.oura import (
    OURA_CATEGORICAL_METRICS, OURA_METRICS, OuraParseError, categorical_inventory, parse_api,
)
from tools.tests.test_oura_sync import by_metric, sleep_document


def document(identifier="daily", day="2026-08-01", **fields):
    return {"id": identifier, "day": day, **fields}


def samples(items, interval=300, timestamp="2026-08-01T23:55:00+02:00"):
    return {"items": items, "interval": interval, "timestamp": timestamp}


class ExtendedOuraTests(unittest.TestCase):
    def test_categories_are_label_observations_with_original_source_values(self):
        records = categorical_inventory({
            "daily_stress": [document(day_summary="stressful")],
            "daily_resilience": [document(level="solid")],
        })
        values = by_metric(records)
        self.assertEqual(set(values), OURA_CATEGORICAL_METRICS)
        self.assertEqual(values["Stress Day Summary (Oura)"]["value"], "Stressful")
        self.assertEqual(values["Resilience Level (Oura)"]["source_value"], "solid")
        self.assertTrue(all("unit" not in row and "recorded_at" not in row for row in records))
        self.assertEqual(records, categorical_inventory({
            "daily_stress": [document(day_summary="stressful"), document(day_summary="stressful")],
            "daily_resilience": [document(level="solid")],
        }))

    def test_latest_missing_category_does_not_revive_older_status_and_unknown_is_unranked(self):
        old = document("old", day_summary="normal", timestamp="2026-08-01T07:00:00Z")
        latest = document("new", day_summary=None, timestamp="2026-08-01T08:00:00Z")
        self.assertEqual(categorical_inventory({"daily_stress": [old, latest]}), [])
        unknown = categorical_inventory({"daily_resilience": [document(level="future-label")]})
        self.assertEqual(unknown[0]["value"], "Unmapped category: future-label")
        self.assertEqual(unknown[0]["source_value"], "future-label")
        for bad in (1, True, [], ""):
            with self.subTest(bad=bad), self.assertRaises(OuraParseError):
                categorical_inventory({"daily_resilience": [document(level=bad)]})

    def test_readiness_signed_temperature_and_contributors_are_distinct(self):
        records = parse_api({"daily_readiness": [document(
            score=82, temperature_deviation=-0.31, temperature_trend_deviation=0,
            contributors={"body_temperature": 96, "resting_heart_rate": 88,
                          "sleep_regularity": None}, timestamp="2026-08-01T09:00:00+02:00",
        )]})
        values = by_metric(records)
        self.assertEqual(values["Readiness Score (Oura)"]["value"], 82)
        self.assertEqual(values["Temperature Deviation (Oura)"]["value"], -0.31)
        self.assertEqual(values["Temperature Deviation (Oura)"]["unit"], "°C")
        self.assertEqual(values["Temperature Trend Deviation (Oura)"]["value"], 0)
        contributor = values["Readiness Resting HR Contributor Score (Oura)"]
        self.assertEqual(contributor["unit"], "score")
        self.assertEqual(contributor["source_field"], "contributors.resting_heart_rate")
        self.assertEqual(contributor["source_endpoint"], "daily_readiness")
        self.assertNotIn("Mean Nightly Lowest HR (Oura)", values)

    def test_activity_converts_source_units_and_does_not_average_class_codes(self):
        values = by_metric(parse_api({"daily_activity": [document(
            score=90, steps=12345, active_calories=550, total_calories=2450,
            average_met_minutes=1.25, high_activity_time=900,
            low_activity_time=10800, medium_activity_time=3600,
            sedentary_time=18000, resting_time=25200, non_wear_time=0,
            equivalent_walking_distance=8500, target_calories=600, target_meters=9000,
            meters_to_target=-500, inactivity_alerts=0,
            high_activity_met_minutes=120, sedentary_met_minutes=300,
            class_5_min="012345", contributors={"training_volume": 95},
        )]}))
        self.assertEqual(values["High Activity Time (Oura)"]["value"], 0.25)
        self.assertEqual(values["Equivalent Walking Distance (Oura)"]["value"], 8.5)
        self.assertEqual(values["Distance Remaining to Activity Target (Oura)"]["value"], -0.5)
        self.assertEqual(values["High Activity MET Minutes (Oura)"]["unit"], "MET-min")
        self.assertEqual(values["Active Energy (Oura)"]["unit"], "kcal")
        self.assertEqual(values["Non-wear Time (Oura)"]["value"], 0)
        self.assertFalse(any("class" in row["source_field"] for row in values.values()))

    def test_spo2_bdi_and_cardio_estimates_preserve_independent_units(self):
        values = by_metric(parse_api({
            "daily_spo2": [document(spo2_percentage={"average": 97.25},
                                    breathing_disturbance_index=0)],
            "daily_cardiovascular_age": [document(vascular_age=35, pulse_wave_velocity=7.35)],
            "vO2_max": [document(vo2_max=44, timestamp="2026-08-01T12:00:00Z")],
        }))
        self.assertEqual(values["Average Sleeping SpO2 (Oura)"]["value"], 97.25)
        self.assertEqual(values["Breathing Disturbance Index (Oura)"]["unit"], "index")
        self.assertEqual(values["Breathing Disturbance Index (Oura)"]["value"], 0)
        self.assertEqual(values["Cardiovascular Age (Oura)"]["unit"], "years")
        self.assertEqual(values["Estimated PWV (Oura)"]["unit"], "m/s")
        self.assertEqual(values["VO2 Max (Oura)"]["unit"], "ml/kg/min")
        self.assertNotIn("AHI", values)
        self.assertNotIn("PWV", values)

    def test_stress_and_resilience_categories_never_become_numeric_levels(self):
        values = by_metric(parse_api({
            "daily_stress": [document(stress_high=7200, recovery_high=0,
                                      day_summary="stressful")],
            "daily_resilience": [document(level="solid", contributors={
                "sleep_recovery": 75.5, "daytime_recovery": 80, "stress": 42.25,
            })],
        }))
        self.assertEqual(len(values), 5)
        self.assertEqual(values["High Stress Time (Oura)"]["value"], 2)
        self.assertEqual(values["High Recovery Time (Oura)"]["value"], 0)
        self.assertEqual(values["Resilience Sleep Recovery Contributor Score (Oura)"]["value"], 75.5)
        self.assertTrue(all(isinstance(row["value"], float) for row in values.values()))
        self.assertEqual(parse_api({"daily_resilience": [document(level="exceptional")]}), [])

    def test_daily_sleep_is_independent_and_contributor_does_not_replace_score(self):
        values = by_metric(parse_api({"daily_sleep": [document(
            score=None, contributors={"total_sleep": 90, "restfulness": 75},
        )]}))
        self.assertEqual(len(values), 2)
        self.assertNotIn("Sleep Score", values)
        self.assertEqual(values["Sleep Total Sleep Contributor Score (Oura)"]["value"], 90)

    def test_primary_sleep_extras_and_signed_score_changes(self):
        values = by_metric(parse_api({"sleep": [sleep_document(
            awake_time=5400, restless_periods=5, readiness_score_delta=-2,
            sleep_score_delta=3,
        )]}))
        self.assertEqual(values["Light Sleep (Oura)"]["value"], 17400 / 3600)
        self.assertEqual(values["Awake Time During Sleep (Oura)"]["value"], 1.5)
        self.assertEqual(values["Primary Sleep Readiness Score Change (Oura)"]["value"], -2)
        self.assertEqual(values["Primary Sleep Score Change (Oura)"]["unit"], "points")

    def test_latest_daily_document_does_not_revive_an_older_missing_field(self):
        older = document("older", score=90, temperature_deviation=0.2,
                         timestamp="2026-08-01T07:00:00Z")
        newer = document("newer", score=None, temperature_deviation=-0.2,
                         timestamp="2026-08-01T08:00:00Z")
        first = parse_api({"daily_readiness": [older, newer]})
        self.assertEqual(first, parse_api({"daily_readiness": [newer, older]}))
        self.assertNotIn("Readiness Score (Oura)", by_metric(first))
        self.assertEqual(by_metric(first)["Temperature Deviation (Oura)"]["value"], -0.2)

    def test_source_specific_hr_uses_local_day_and_deduplicates_utc_instants(self):
        first = {"timestamp": "2026-07-31T22:30:00Z", "bpm": 61, "source": "awake"}
        same = {"timestamp": "2026-08-01T00:30:00+02:00", "bpm": 61, "source": "awake"}
        sleep = {**first, "source": "sleep", "bpm": 56}
        records = parse_api({"heartrate": [first, same, sleep]})
        self.assertEqual(len(records), 2)
        self.assertEqual({row["day"] for row in records}, {"2026-08-01"})
        self.assertEqual({row["metric"] for row in records},
                         {"Sampled Awake HR (Oura)", "Sampled Sleeping HR (Oura)"})
        self.assertEqual(records, parse_api({"heartrate": [sleep, same, first]}))
        with self.assertRaisesRegex(OuraParseError, "conflicting duplicate"):
            parse_api({"heartrate": [first, {**first, "bpm": 62}]})

    def test_hr_rejects_unknown_source_invalid_numbers_and_disagreeing_timestamps(self):
        valid = {"timestamp": "2026-08-01T12:00:00Z", "bpm": 65, "source": "rest"}
        for changes in ({"bpm": 0}, {"bpm": True}, {"bpm": float("inf")},
                        {"source": "unknown"}, {"timestamp": None}, {"timestamp_unix": 0}):
            with self.subTest(changes=changes), self.assertRaises(OuraParseError):
                parse_api({"heartrate": [{**valid, **changes}]})

    def test_workouts_retain_per_event_quantities_and_offset_aware_duration(self):
        event = document("first", day="2026-10-25", calories=450, distance=5000,
                         start_datetime="2026-10-25T02:30:00+02:00",
                         end_datetime="2026-10-25T02:30:00+01:00",
                         intensity="hard", source="manual", activity="running")
        second = {**event, "id": "second", "calories": None, "distance": 0}
        records = parse_api({"workout": [event, second]})
        durations = [row for row in records if row["metric"] == "Duration per Recorded Workout (Oura)"]
        self.assertEqual(len(durations), 2)
        self.assertEqual([row["value"] for row in durations], [1, 1])
        self.assertEqual(durations[0]["derived_from"], ["start_datetime", "end_datetime"])
        self.assertEqual(len([row for row in records if row["unit"] == "kcal"]), 1)
        self.assertEqual(sorted(row["value"] for row in records if row["unit"] == "km"), [0, 5])

    def test_session_samples_skip_null_and_preserve_indices_intervals_and_day(self):
        records = parse_api({"session": [document(
            start_datetime="2026-08-01T23:55:00+02:00",
            end_datetime="2026-08-02T00:10:00+02:00", type="meditation", mood="great",
            heart_rate=samples([60, None, 62]),
            heart_rate_variability=samples([0, 25]), motion_count=samples([0]),
        )]})
        hr = [row for row in records if row["metric"] == "Sampled HR During Sessions (Oura)"]
        self.assertEqual([row["value"] for row in hr], [60, 62])
        self.assertEqual([row["sample_index"] for row in hr], [0, 2])
        self.assertEqual(hr[1]["recorded_at"], "2026-08-02T00:05:00+02:00")
        self.assertEqual({row["day"] for row in records}, {"2026-08-01"})
        self.assertEqual(by_metric(records)["Duration per Recorded Session (Oura)"]["value"], 15)

    def test_sampled_activity_and_primary_sleep_have_distinct_provenance(self):
        records = parse_api({
            "daily_activity": [document(met=samples([1.2, None, 2.5]))],
            "sleep": [sleep_document(heart_rate=samples([55, 57]), hrv=samples([22]))],
        })
        values = by_metric(records)
        self.assertEqual(values["Sampled Activity MET (Oura)"]["unit"], "MET")
        self.assertEqual(values["Sampled HR During Primary Sleep (Oura)"]["source_endpoint"], "sleep")
        self.assertIn("Average Sleeping HR (Oura)", values)

    def test_extended_structural_and_source_range_errors_are_rejected(self):
        invalid = [
            {"daily_spo2": [document(spo2_percentage=97)]},
            {"daily_spo2": [document(spo2_percentage={"average": 101})]},
            {"daily_spo2": [document(breathing_disturbance_index=-1)]},
            {"daily_cardiovascular_age": [document(vascular_age=17)]},
            {"daily_readiness": [document(contributors={"body_temperature": 101})]},
            {"daily_readiness": [document(temperature_deviation=float("nan"))]},
            {"daily_stress": [document(stress_high="3600")]},
            {"daily_activity": [document(met=samples([1], interval=0))]},
            {"daily_activity": [document(met=samples([True]))]},
            {"daily_activity": [document(met=samples([1], timestamp="2026-08-01T12:00:00"))]},
            {"session": [document(start_datetime="2026-08-01T12:00:00Z",
                                  end_datetime="2026-08-01T11:00:00Z")]},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(OuraParseError):
                parse_api(payload)

    def test_all_emitted_metrics_have_a_unique_registered_unit_and_no_categories(self):
        records = parse_api({
            "sleep": [sleep_document()], "daily_readiness": [document(score=90)],
            "daily_activity": [document(steps=100)],
            "daily_spo2": [document(spo2_percentage=None)],
            "daily_stress": [document(day_summary="normal")],
            "daily_resilience": [document(level="strong")],
        })
        for row in records:
            self.assertEqual(OURA_METRICS[row["metric"]][0], row["unit"])
            self.assertEqual(row["source_kind"], "api")
        self.assertGreater(len(OURA_METRICS), 70)


if __name__ == "__main__":
    unittest.main()
