"""Synthetic API fixtures: no patient data, account access, or report writes."""

import copy
from datetime import datetime, timezone
import math
import unittest

from tools.health_sync.withings import (
    WITHINGS_ACTIVITY_FIELDS, WITHINGS_METRICS, WITHINGS_SLEEP_FIELDS,
    categorical_inventory, parse_api,
)


def timestamp(text):
    return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp())


def measure(kind, value, unit=0):
    return {"type": kind, "value": value, "unit": unit}


def group(*measures, key=1, date="2026-09-05T20:36:00", **extra):
    return {"grpid": key, "date": timestamp(date), "category": 1,
            "attrib": 0, "measures": list(measures), **extra}


def by_metric(records):
    return {record["metric"]: record for record in records}


class WithingsParserTests(unittest.TestCase):
    def test_exponents_percentages_and_configured_bmi_are_traceable(self):
        raw = {"measuregrps": [group(measure(1, 80400, -3), measure(8, 109344, -4),
                                     measure(76, 661692, -4), measure(4, 180, -2))]}
        snapshot = copy.deepcopy(raw)
        result = by_metric(parse_api(raw))
        self.assertEqual(raw, snapshot)
        self.assertEqual(result["Body Mass"]["value"], 80.4)
        self.assertAlmostEqual(result["Body Fat"]["value"], 13.6)
        self.assertAlmostEqual(result["Muscle"]["value"], 82.3)
        self.assertEqual(result["Muscle"]["unit"], "%")
        self.assertNotIn("Height", result)
        self.assertAlmostEqual(result["BMI"]["value"], 80.4 / 1.8 ** 2)
        self.assertEqual(result["BMI"]["derived_from"]["configured_height_cm"], 180)
        self.assertEqual(result["Muscle"]["source_types"], [76, 1])
        self.assertEqual(result["Body Mass"]["recorded_at"], "2026-09-05T22:36:00+02:00")
        for record in result.values():
            self.assertEqual(record["provider"], "withings")
            self.assertEqual(record["source_kind"], "api")
            self.assertTrue(math.isfinite(record["value"]))

    def test_explicit_fat_ratio_wins_over_derived_mass(self):
        records = parse_api({"measuregrps": [group(measure(1, 80), measure(8, 20), measure(6, 136, -1))]})
        fats = [record for record in records if record["metric"] == "Body Fat"]
        self.assertEqual(len(fats), 1)
        self.assertEqual(fats[0]["value"], 13.6)
        self.assertEqual(fats[0]["source_types"], [6])

    def test_bone_mass_exponents_are_converted_to_traceable_percentage(self):
        result = by_metric(parse_api({"measuregrps": [group(
            measure(1, 80000, -3), measure(88, 3280, -3))]}))
        bone = result["Bone"]
        self.assertAlmostEqual(bone["value"], 4.1)
        self.assertEqual(bone["unit"], "%")
        self.assertEqual(bone["source_types"], [88, 1])
        self.assertEqual(bone["derived_from"], {
            "mass_kg": 3.28, "weight_kg": 80, "same_group": "1",
        })
        self.assertNotIn("Bone Mass", result)

    def test_bone_percentage_requires_positive_weight_in_the_same_group(self):
        for groups in (
            [group(measure(88, 3280, -3))],
            [group(measure(88, 3280, -3), measure(1, 0))],
            [group(measure(88, 3280, -3), key=1), group(measure(1, 80), key=2)],
        ):
            with self.subTest(groups=groups):
                self.assertNotIn("Bone", by_metric(parse_api({"measuregrps": groups})))

    def test_invalid_bone_mass_is_not_reported_as_a_percentage(self):
        for mass in (-1, 81, None, "pending", float("nan"), float("inf")):
            with self.subTest(mass=mass):
                result = by_metric(parse_api({"measuregrps": [group(
                    measure(1, 80), measure(88, mass))]}))
                self.assertNotIn("Bone", result)
                self.assertEqual(result["Body Mass"]["value"], 80)

    def test_visceral_fat_keeps_scaled_index_and_does_not_require_weight(self):
        records = parse_api({"measuregrps": [group(measure(170, 24, -1))]})
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["metric"], "Visceral Fat Index")
        self.assertEqual(records[0]["value"], 2.4)
        self.assertEqual(records[0]["unit"], "index")
        self.assertEqual(records[0]["source_types"], [170])

    def test_visceral_fat_index_bounds_missing_and_pending(self):
        for value in (-0.1, 20.1, None, "pending", True, float("nan"), float("inf")):
            with self.subTest(value=value):
                self.assertEqual(parse_api({"measuregrps": [group(measure(170, value))]}), [])
        valid = parse_api({"measuregrps": [group(measure(170, 0), key=1),
                                           group(measure(170, 200, -1), key=2)]})
        self.assertEqual([record["value"] for record in valid], [0, 20])
        self.assertTrue(all(record["unit"] == "index" for record in valid))

    def test_never_pairs_body_composition_or_bp_across_groups(self):
        records = parse_api({"measuregrps": [
            group(measure(1, 80), measure(10, 108), key=1),
            group(measure(8, 12), measure(76, 65), measure(9, 76), key=2),
        ]})
        self.assertEqual(set(by_metric(records)), {
            "Body Mass", "BMI", "Fat Mass (Withings)", "Muscle Mass (Withings)"
        })

    def test_bp_pair_and_temperature_body_priority(self):
        result = by_metric(parse_api({"measuregrps": [group(
            measure(10, 1080, -1), measure(9, 76), measure(11, 63),
            measure(12, 20), measure(71, 369, -1), measure(91, 61, -1))]}))
        self.assertEqual(result["Blood Pressure"]["value"], [108, 76])
        self.assertEqual(result["Blood Pressure"]["unit"], "mmHg")
        self.assertEqual(result["Temperature"]["value"], 36.9)
        self.assertEqual(result["PWV"]["value"], 6.1)
        self.assertNotIn("ECG Heart Rate", result)
        self.assertNotIn("Resting Heart Rate", result)

    def test_objectives_and_ambiguous_users_excluded_manual_preserved(self):
        records = parse_api({"measuregrps": [group(measure(1, 80), key=1, category=2),
                                             group(measure(1, 90), key=2, attrib=1),
                                             group(measure(1, 81), key=3, attrib=2),
                                             group(measure(1, 82), key=4, attrib=4)]})
        weights = [record for record in records if record["metric"] == "Body Mass"]
        self.assertEqual([record["value"] for record in weights], [81, 82])
        self.assertEqual([record["attribution"] for record in weights], [2, 4])

    def test_zero_and_missing_weight_never_create_percentages(self):
        result = by_metric(parse_api({"measuregrps": [group(measure(1, 0), measure(8, 0), measure(76, 0))]}))
        self.assertTrue(all(record["unit"] == "kg" for record in result.values()))
        standalone = by_metric(parse_api({"measuregrps": [group(measure(8, 10), measure(76, 60))]}))
        self.assertEqual(standalone["Fat Mass (Withings)"]["value"], 10)
        self.assertNotIn("Body Fat", standalone)
        self.assertNotIn("Muscle", standalone)

    def test_invalid_exponents_values_and_unknown_types_do_not_become_readings(self):
        bad = [measure(1, 80000, -3.5), {"type": 6, "value": 15},
               measure(76, None), measure(91, "NaN"), measure(12, float("inf")),
               measure(71, 1, 100000000), measure(4, True),
               measure(130, 0), measure(139, 0), measure(9999, 1)]
        self.assertEqual(parse_api({"measuregrps": [group(*bad)]}), [])

    def test_unit_is_integer_and_numeric_strings_work(self):
        good = group(measure("1", "80400", "-3"))
        bad = group(measure(1, 80400, -3.0), key=2)
        self.assertEqual(by_metric(parse_api({"measuregrps": [good, bad]}))["Body Mass"]["value"], 80.4)

    def test_percentages_outside_mass_bounds_are_not_reported(self):
        result = by_metric(parse_api({"measuregrps": [group(measure(1, 80), measure(8, 90),
                                                          measure(76, -1), measure(6, 101))]}))
        self.assertEqual(set(result), {"Body Mass", "BMI"})

    def test_height_can_be_disabled_and_invalid_configuration_rejected(self):
        raw = {"measuregrps": [group(measure(1, 80))]}
        self.assertEqual(set(by_metric(parse_api(raw, height_cm=None))), {"Body Mass"})
        for height in (0, -1, True, float("nan"), float("inf")):
            with self.subTest(height=height), self.assertRaises(ValueError):
                parse_api(raw, height_cm=height)

    def test_month_boundary_and_dst_offsets(self):
        records = parse_api({"measuregrps": [group(measure(1, 80), key=1, date="2026-09-30T22:30:00"),
                                             group(measure(1, 81), key=2, date="2026-12-31T23:30:00")]})
        weights = [record for record in records if record["metric"] == "Body Mass"]
        self.assertEqual([record["day"] for record in weights], ["2026-10-01", "2027-01-01"])
        self.assertTrue(weights[0]["recorded_at"].endswith("+02:00"))
        self.assertTrue(weights[1]["recorded_at"].endswith("+01:00"))

    def test_full_response_pages_deduplicate_and_updates_keep_stable_id(self):
        original = group(measure(1, 80), modified=100)
        updated = group(measure(1, 81), modified=200)
        def page(rows, more=0):
            return {"status": 0, "body": {"measuregrps": rows, "more": more, "offset": 10}}
        records = parse_api({"measure": [page([original], more=1), page([updated, updated])]})
        current = by_metric(records)["Body Mass"]
        previous = by_metric(parse_api({"measuregrps": [original]}))["Body Mass"]
        self.assertEqual(current["id"], previous["id"])
        self.assertEqual(current["value"], 81)
        self.assertEqual(len(records), 2)
        with self.assertRaisesRegex(ValueError, "pagination"):
            parse_api({"measure": [page([original], more=1)]})

    def test_explicit_multiple_users_and_api_errors_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "more than one user"):
            parse_api({"measuregrps": [group(measure(1, 80), userid=1),
                                       group(measure(1, 90), key=2, userid=2)]})
        with self.assertRaisesRegex(ValueError, "unsuccessful"):
            parse_api({"measure": [{"status": 401, "body": {}}]})

    def test_conflicting_revisions_do_not_silently_choose_by_input_order(self):
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            parse_api({"measuregrps": [group(measure(1, 80), modified=100),
                                       group(measure(1, 90), modified=100)]})
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            parse_api({"measuregrps": [group(measure(1, 80), measure(1, 90))]})

    def test_unknown_null_and_truncated_records_are_safe(self):
        truncated = {**group(measure(1, 80)), "date": None}
        self.assertEqual(parse_api({"measuregrps": [None, {}, truncated], "series": None}), [])
        self.assertEqual(parse_api({"unrecognized": [{"value": 80}]}), [])

    def test_ahi_is_completed_withings_medical_field_only_and_zero_is_valid(self):
        sleep = {"id": 7, "completed": True, "startdate": timestamp("2026-09-01T23:00:00"),
                 "enddate": timestamp("2026-09-02T07:17:00"),
                 "data": {"apnea_hypopnea_index": 0, "hr_average": 65, "withings_index": 10,
                          "total_sleep_time": 24000}}
        result = parse_api({"sleep": [{"status": 0, "body": {"series": [sleep], "more": False}}]})
        values = by_metric(result)
        self.assertEqual(len(result), 4)
        self.assertEqual(values["Sleep Apnea AHI"]["value"], 0)
        self.assertEqual(values["Sleep Apnea AHI"]["day"], "2026-09-02")
        self.assertEqual(values["Sleep Apnea AHI"]["unit"], "events/h")
        self.assertEqual(values["Sleep Rx Breathing Events Index (Withings)"]["value"], 10)
        sleep["completed"] = False
        self.assertEqual(parse_api({"series": [sleep]}), [])
        sleep["completed"] = True
        del sleep["data"]["apnea_hypopnea_index"]
        self.assertNotIn("Sleep Apnea AHI", by_metric(parse_api({"series": [sleep]})))

    def test_all_body_masses_and_water_keep_units_and_same_group_percentages(self):
        result = by_metric(parse_api({"measuregrps": [group(
            measure(1, 80), measure(5, 6800, -2), measure(8, 1200, -2),
            measure(76, 6500, -2), measure(77, 4700, -2), measure(88, 300, -2),
            measure(168, 2000, -2), measure(169, 2700, -2), measure(4, 180, -2)
        )]}))
        self.assertEqual(result["Fat-Free Mass (Withings)"]["value"], 68)
        self.assertEqual(result["Water Mass (Withings)"]["value"], 47)
        self.assertEqual(result["Lean Mass (Withings)"]["value"], 85)
        self.assertEqual(result["Body Water (Withings)"]["value"], 58.75)
        self.assertEqual(result["Bone Mass (Withings)"]["value"], 3)
        self.assertEqual(result["Height (Withings)"]["value"], 180)
        self.assertNotEqual(result["Muscle"]["value"], result["Lean Mass (Withings)"]["value"])
        for record in result.values():
            self.assertEqual(record["unit"], WITHINGS_METRICS[record["metric"]][0])

    def test_segment_positions_are_separate_and_unknown_position_never_summed(self):
        measures = [{**measure(174, 120, -2), "position": 2},
                    {**measure(174, 125, -2), "position": 3},
                    {**measure(173, 1100, -2), "position": 10},
                    {**measure(175, 1030, -2), "position": 11},
                    {**measure(175, 2300, -2), "position": 12},
                    {**measure(175, 9999, -2), "position": 999}]
        records = parse_api({"measuregrps": [group(*measures)]})
        result = by_metric(records)
        self.assertEqual(len(records), 5)
        self.assertEqual(result["Fat Mass - Right Arm (Withings)"]["value"], 1.2)
        self.assertEqual(result["Fat Mass - Left Arm (Withings)"]["value"], 1.25)
        self.assertEqual(result["Muscle Mass - Torso (Withings)"]["source_position"], 12)
        with self.assertRaisesRegex(ValueError, "Conflicting Withings segment"):
            parse_api({"measuregrps": [group(measures[0], {**measures[0], "value": 140})]})

    def test_vascular_age_nerve_scores_pulse_spo2_and_vo2_are_distinct(self):
        records = parse_api({"measuregrps": [group(
            measure(155, 315, -1), measure(158, 67000, -3), measure(159, 69000, -3),
            measure(167, 69000, -3), measure(196, 72), measure(11, 63), measure(54, 98),
            measure(123, 44), measure(226, 1750), measure(227, 32), measure(73, 35200, -3)
        )]})
        result = by_metric(records)
        self.assertEqual(result["Vascular Age (Withings)"]["value"], 31.5)
        self.assertEqual(result["Vascular Age (Withings)"]["unit"], "years")
        self.assertEqual(result["Nerve Health Score Feet (Withings)"]["value"], 69)
        self.assertEqual(result["Nerve Health Score Feet (Withings)"]["unit"], "score")
        self.assertEqual(result["Pulse Rate (Withings)"]["value"], 63)
        self.assertEqual(result["SpO2 (Withings)"]["unit"], "%")
        self.assertEqual(result["Basal Metabolic Rate (Withings)"]["unit"], "kcal/day")
        self.assertNotIn("Resting Heart Rate", result)
        self.assertNotIn("VO2max", result)

    def test_sleep_fields_convert_seconds_and_ratio_without_replacing_oura(self):
        sleep = {"id": 7, "completed": True, "startdate": timestamp("2026-09-01T23:00:00"),
                 "enddate": timestamp("2026-09-02T07:17:00"), "data": {
                     "total_sleep_time": 27000, "total_timeinbed": 30000,
                     "sleep_efficiency": 0.9, "sleep_latency": 450,
                     "remsleepduration": 6300, "deepsleepduration": 3600,
                     "hr_average": 63, "rr_average": 12.5, "snoring": 0,
                     "wakeupcount": 3, "sleep_score": 85, "rmssd_start_avg": 42,
                     "rmssd_end_avg": 51.5,
                     "breathing_quality_assessment": 2, "core_body_temperature_status": "usual",
                 }}
        result = by_metric(parse_api({"series": [sleep]}))
        self.assertEqual(result["Sleep Duration (Withings)"]["value"], 7.5)
        self.assertEqual(result["Sleep Efficiency (Withings)"]["value"], 90)
        self.assertEqual(result["Sleep Latency (Withings)"]["value"], 7.5)
        self.assertEqual(result["Snoring Duration (Withings)"]["value"], 0)
        self.assertEqual(result["HRV at Sleep Start (Withings)"]["value"], 42)
        self.assertEqual(result["HRV at Sleep End (Withings)"]["value"], 51.5)
        self.assertEqual(result["HRV at Sleep End (Withings)"]["unit"], "ms")
        self.assertNotIn("Sleep Duration", result)
        self.assertNotIn("Average HRV (Sleep)", result)
        self.assertTrue(all(r["metric"] in WITHINGS_METRICS for r in result.values()))
        sleep["data"]["sleep_efficiency"] = 90
        self.assertEqual(by_metric(parse_api({"series": [sleep]}))["Sleep Efficiency (Withings)"]["value"], 90)
        self.assertIn("rmssd_start_avg", WITHINGS_SLEEP_FIELDS)

    def test_activity_daily_revisions_replace_without_double_counting(self):
        activity = {"date": "2026-08-01", "timezone": "Europe/Warsaw", "modified": 100,
                    "steps": 1000, "distance": 750, "soft": 600, "moderate": 1200,
                    "active": 1800, "calories": 120, "totalcalories": 2100, "hr_average": 65,
                    "elevation": 2, "hr_zone_3": 0}
        revised = {**activity, "modified": 200, "steps": 1500}
        result = by_metric(parse_api({"activity": [{"status": 0, "body": {
            "activities": [activity, revised, revised], "more": False}}]}))
        self.assertEqual(result["Steps (Withings)"]["value"], 1500)
        self.assertEqual(result["Active Duration (Withings)"]["value"], 30)
        self.assertEqual(result["Floors Climbed (Withings)"]["unit"], "floors")
        self.assertEqual(result["HR Maximal Zone Duration (Withings)"]["value"], 0)
        self.assertEqual(result["Steps (Withings)"]["day"], "2026-08-01")
        self.assertEqual(len(WITHINGS_ACTIVITY_FIELDS), 16)

    def test_split_sleep_sums_durations_and_weights_rates_before_monthly_mean(self):
        first = {"id": 1, "completed": True, "startdate": timestamp("2026-09-01T00:00:00"),
                 "enddate": timestamp("2026-09-01T01:30:00"), "hash_deviceid": "a", "data": {
                     "total_sleep_time": 3600, "total_timeinbed": 5400, "hr_average": 60,
                     "rr_average": 10, "apnea_hypopnea_index": 2, "hr_min": 50, "hr_max": 90,
                     "wakeupcount": 2, "sleep_latency": 30, "sleep_score": 60, "rmssd_start_avg": 20}}
        second = {"id": 2, "completed": True, "startdate": timestamp("2026-09-01T03:00:00"),
                  "enddate": timestamp("2026-09-01T07:30:00"), "hash_deviceid": "a", "data": {
                      "total_sleep_time": 10800, "total_timeinbed": 16200, "hr_average": 80,
                      "rr_average": 14, "apnea_hypopnea_index": 6, "hr_min": 55, "hr_max": 110,
                      "wakeupcount": 3, "sleep_latency": 90, "sleep_score": 80, "rmssd_start_avg": 60}}
        result = by_metric(parse_api({"series": [second, first, first]}))
        self.assertEqual(result["Sleep Duration (Withings)"]["value"], 4)
        self.assertEqual(result["Time in Bed (Withings)"]["value"], 6)
        self.assertAlmostEqual(result["Sleep Efficiency (Withings)"]["value"], 200 / 3)
        self.assertEqual(result["Average Sleeping HR (Withings)"]["value"], 75)
        self.assertEqual(result["Respiratory Rate During Sleep (Withings)"]["value"], 13)
        self.assertEqual(result["Sleep Apnea AHI"]["value"], 5)
        self.assertEqual(result["Mean Nightly Lowest HR (Withings)"]["value"], 50)
        self.assertEqual(result["Mean Nightly Highest HR (Withings)"]["value"], 110)
        self.assertEqual(result["Wakeup Count (Withings)"]["value"], 5)
        self.assertEqual(result["Sleep Latency (Withings)"]["value"], 1)
        self.assertEqual(result["Sleep Score (Withings)"]["value"], 70)
        self.assertEqual(result["HRV at Sleep Start (Withings)"]["value"], 40)
        self.assertEqual(result["HRV at Sleep Start (Withings)"]["daily_aggregation"], "mean_of_sessions")
        for record in result.values():
            self.assertEqual(record["source_count"], 2)
            self.assertEqual(record["source_record_ids"], ["1", "2"])
            self.assertEqual(len(record["source_intervals"]), 2)
            self.assertTrue(record["id"].startswith("withings:sleep:daily-2026-09-01:"))
        del second["data"]["hr_average"]
        partial = by_metric(parse_api({"series": [first, second]}))
        self.assertEqual(partial["Average Sleeping HR (Withings)"]["source_count"], 1)
        self.assertEqual(partial["Average Sleeping HR (Withings)"]["value"], 60)

    def test_sleep_overlaps_fail_closed_but_same_id_revisions_replace(self):
        first = {"id": 1, "completed": True, "startdate": timestamp("2026-09-01T00:00:00"),
                 "enddate": timestamp("2026-09-01T03:00:00"), "hash_deviceid": "a",
                 "modified": 1, "data": {"total_sleep_time": 7200}}
        second = {**first, "id": 2, "hash_deviceid": "b"}
        with self.assertRaisesRegex(ValueError, "Overlapping Withings sleep"):
            parse_api({"series": [first, second]})
        revised = {**first, "modified": 2, "data": {"total_sleep_time": 10800}}
        record = by_metric(parse_api({"series": [first, revised]}))["Sleep Duration (Withings)"]
        self.assertEqual(record["value"], 3)
        self.assertEqual(record["source_count"], 1)

    def test_sleep_weighted_fields_need_valid_sleep_duration_and_efficiency_pair(self):
        sleep = {"id": 1, "completed": True, "startdate": timestamp("2026-09-01T00:00:00"),
                 "enddate": timestamp("2026-09-01T03:00:00"),
                 "data": {"hr_average": 65, "total_timeinbed": 10800, "sleep_efficiency": 0.8}}
        result = by_metric(parse_api({"series": [sleep]}))
        self.assertNotIn("Average Sleeping HR (Withings)", result)
        self.assertNotIn("Sleep Efficiency (Withings)", result)
        self.assertEqual(result["Time in Bed (Withings)"]["value"], 3)

    def test_fall_back_sleep_sessions_use_elapsed_time_despite_reversed_wall_clock(self):
        first = {"id": 1, "completed": True, "startdate": timestamp("2026-10-25T00:50:00"),
                 "enddate": timestamp("2026-10-25T01:10:00"), "data": {"total_sleep_time": 1200}}
        second = {"id": 2, "completed": True, "startdate": timestamp("2026-10-25T01:20:00"),
                  "enddate": timestamp("2026-10-25T01:40:00"), "data": {"total_sleep_time": 1200}}
        record = by_metric(parse_api({"series": [second, first]}))["Sleep Duration (Withings)"]
        self.assertAlmostEqual(record["value"], 2 / 3)
        self.assertEqual(record["source_record_ids"], ["1", "2"])
        self.assertEqual(record["source_count"], 2)
        self.assertEqual(record["day"], "2026-10-25")

    def test_categorical_observations_are_retained_and_heart_avoids_af_duplicate(self):
        stamp = timestamp("2026-09-05T20:36:00")
        heart = {"ecg": {"signalid": 55, "afib": 2}, "timestamp": stamp, "heart_rate": 65}
        payload = {
            "measuregrps": [group(measure(130, 0), measure(139, 1))],
            "heart": [{"status": 0, "body": {"series": [heart], "more": False}}],
            "stetho": [{"status": 0, "body": {"series": [
                {"signalid": 77, "timestamp": stamp, "vhd": 2}
            ], "more": False}}],
        }
        numbers = by_metric(parse_api(payload))
        self.assertEqual(set(numbers), {"ECG Recorded Heart Rate (Withings)"})
        events = categorical_inventory(payload)
        af = [event for event in events if event["metric"] == "ECG AF Classification (Withings)"]
        self.assertEqual(len(af), 1)
        self.assertEqual(af[0]["value"], "Inconclusive")
        self.assertTrue(af[0]["id"].startswith("withings:event:heart:"))
        sounds = next(e for e in events if e["metric"] == "Heart Sounds Classification (Withings)")
        self.assertEqual(sounds["value"], "Device code 2")
        self.assertEqual(sounds["source_value"], 2)

    def test_bpm_ecg_timestamp_lag_deduplicates_only_unique_matching_reading(self):
        measured = group(measure(130, 9), measure(9, 75), measure(10, 115), measure(11, 65), deviceid="a")
        heart = {"ecg": {"signalid": 55, "afib": 0}, "timestamp": measured["date"] + 55,
                 "deviceid": "a", "heart_rate": 65, "bloodpressure": {"diastole": 75, "systole": 115}}
        payload = {"measuregrps": [measured], "heart_series": [heart]}
        self.assertEqual(len(categorical_inventory(payload)), 1)
        payload["heart_series"] = [heart, {**heart, "ecg": {"signalid": 56, "afib": 0}}]
        self.assertEqual(len(categorical_inventory(payload)), 3)
        payload["heart_series"] = [{**heart, "deviceid": "b"}]
        self.assertEqual(len(categorical_inventory(payload)), 2)
        payload["heart_series"] = [{**heart, "heart_rate": 66}]
        self.assertEqual(len(categorical_inventory(payload)), 2)
        payload["heart_series"] = [{**heart, "timestamp": measured["date"] + 121}]
        self.assertEqual(len(categorical_inventory(payload)), 2)


if __name__ == "__main__":
    unittest.main()
