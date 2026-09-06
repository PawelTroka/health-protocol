"""Synthetic API fixtures: no patient data, account access, or report writes."""

import copy
from datetime import datetime, timezone
import math
import unittest

from tools.health_sync.withings import parse_api


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
        self.assertEqual(set(by_metric(records)), {"Body Mass", "BMI"})

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
        self.assertEqual(result, {})
        self.assertEqual(parse_api({"measuregrps": [group(measure(8, 10), measure(76, 60))]}), [])

    def test_invalid_exponents_values_and_unknown_types_do_not_become_readings(self):
        bad = [measure(1, 80000, -3.5), {"type": 6, "value": 15},
               measure(76, None), measure(91, "NaN"), measure(12, float("inf")),
               measure(71, 1, 100000000), measure(4, True), measure(167, 70),
               measure(196, 99), measure(130, 0), measure(123, 44), measure(9999, 1)]
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
                 "data": {"apnea_hypopnea_index": 0, "hr_average": 65, "withings_index": 10}}
        result = parse_api({"sleep": [{"status": 0, "body": {"series": [sleep], "more": False}}]})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric"], "Sleep Apnea AHI")
        self.assertEqual(result[0]["value"], 0)
        self.assertEqual(result[0]["day"], "2026-09-02")
        self.assertEqual(result[0]["unit"], "events/h")
        sleep["completed"] = False
        self.assertEqual(parse_api({"series": [sleep]}), [])
        sleep["completed"] = True
        del sleep["data"]["apnea_hypopnea_index"]
        self.assertEqual(parse_api({"series": [sleep]}), [])


if __name__ == "__main__":
    unittest.main()
