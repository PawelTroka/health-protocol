"""Calendar aggregation and report-overlay regression tests using synthetic data."""

import copy
import json
import os
import runpy
import tempfile
import unittest
from unittest.mock import patch
from datetime import date
from pathlib import Path

from tools.health_sync.monthly import (
    aggregate,
    apply_report_overlay,
    load_monthly,
    merge_file_records,
    merge_records,
    report_note,
    validate_records,
)
from tools.tests.test_report_layout import rendered_table_rows


def measurement(identifier, day="2026-08-01", value=80, metric="Body Mass",
                provider="withings", unit="kg", source_kind="api"):
    return {
        "provider": provider, "id": identifier, "day": day, "metric": metric,
        "value": value, "unit": unit, "source_kind": source_kind,
    }


def oura(identifier, day="2026-08-01", value=7.5, source_kind="csv"):
    return measurement(identifier, day, value, "Sleep Duration", "oura", "h", source_kind)


def classification_payload(label="Relaxed"):
    return {"schema_version": 1, "as_of": "2026-09-06", "months": {}, "categorical_months": {
        "2026-07": {"Stress Day Summary (Oura)": {
            "provider": "oura", "unit": "Status", "aggregation": "observed_classification_counts",
            "counts": {label: 2}, "n_records": 2, "n_days": 2,
            "first_day": "2026-07-01", "last_day": "2026-07-02", "value": f"{label}: 2",
        }}
    }}


class MonthlyAggregationTests(unittest.TestCase):
    def test_repeated_withings_readings_have_equal_day_weight_not_pooled_weight(self):
        readings = [measurement("a", value=80), measurement("b", value=82),
                    measurement("c", value=84), measurement("d", "2026-08-02", 90)]
        entry = aggregate(readings, date(2026, 8, 31))["months"]["2026-08"]["Body Mass"]
        # Day one averages 82; day two is 90: (82 + 90) / 2 = 86, not 84.
        self.assertEqual(entry["value"], "86.0")
        self.assertEqual(entry["n_days"], 2)
        self.assertEqual(entry["n_records"], 4)
        self.assertEqual(entry["aggregation"], "mean_of_daily_means")

    def test_blood_pressure_averages_paired_components_then_days(self):
        readings = [
            measurement("a", value=[120, 80], metric="Blood Pressure", unit="mmHg"),
            measurement("b", value=[140, 100], metric="Blood Pressure", unit="mmHg"),
            measurement("c", "2026-08-02", [100, 60], "Blood Pressure", unit="mmHg"),
        ]
        entry = aggregate(readings, date(2026, 8, 31))["months"]["2026-08"]["Blood Pressure"]
        self.assertEqual(entry["value"], "115.0/75.0")
        self.assertEqual((entry["n_days"], entry["n_records"]), (2, 3))

    def test_missing_days_are_excluded_and_full_month_coverage_is_explicit(self):
        records = [oura("a", "2026-08-01", 6), oura("b", "2026-08-31", 8)]
        entry = aggregate(records, date(2026, 9, 5))["months"]["2026-08"]["Sleep Duration"]
        self.assertEqual(entry["value"], "7.00")
        self.assertEqual(entry["n_days"], 2)
        self.assertEqual(entry["calendar_days"], 31)
        self.assertEqual(entry["elapsed_days"], 31)
        self.assertFalse(entry["partial_month"])
        self.assertEqual((entry["first_day"], entry["last_day"]), ("2026-08-01", "2026-08-31"))

    def test_partial_month_excludes_future_records_and_preserves_metric_specific_counts(self):
        records = [oura("a", "2026-09-01", 7), oura("b", "2026-09-04", 8),
                   oura("current", "2026-09-05", 10),
                   oura("future", "2026-09-06", 15),
                   measurement("weight", "2026-09-05", 80)]
        payload = aggregate(records, date(2026, 9, 5))
        sleep = payload["months"]["2026-09"]["Sleep Duration"]
        weight = payload["months"]["2026-09"]["Body Mass"]
        self.assertEqual(sleep["value"], "7.50")
        self.assertEqual(sleep["n_days"], 2)
        self.assertEqual(weight["n_days"], 1)
        self.assertEqual(sleep["last_day"], "2026-09-04")
        self.assertEqual(weight["last_day"], "2026-09-05")
        self.assertEqual((sleep["elapsed_days"], sleep["calendar_days"]), (5, 30))
        self.assertTrue(sleep["partial_month"])

    def test_leap_year_february_has_29_calendar_days(self):
        readings = [measurement("a", "2028-02-01", 80), measurement("b", "2028-02-29", 82)]
        full = aggregate(readings, date(2028, 3, 1))["months"]["2028-02"]["Body Mass"]
        partial = aggregate(readings, date(2028, 2, 28))["months"]["2028-02"]["Body Mass"]
        self.assertEqual((full["calendar_days"], full["elapsed_days"]), (29, 29))
        self.assertEqual(full["value"], "81.0")
        self.assertFalse(full["partial_month"])
        self.assertEqual((partial["calendar_days"], partial["elapsed_days"]), (29, 28))
        self.assertTrue(partial["partial_month"])
        self.assertEqual(partial["n_days"], 1)

    def test_final_rounding_preserves_daily_precision_and_is_half_up(self):
        values = [measurement("a", value=80.03), measurement("b", value=80.05),
                  measurement("c", "2026-08-02", 80.05)]
        # Daily means 80.04 and 80.05 give 80.045 -> 80.0. Rounding each daily mean
        # first would instead give (80.0 + 80.1) / 2 -> 80.1.
        result = aggregate(values, date(2026, 8, 31))["months"]["2026-08"]
        self.assertEqual(result["Body Mass"]["value"], "80.0")
        half = aggregate([oura("half", value=7.505)], date(2026, 8, 31))
        self.assertEqual(half["months"]["2026-08"]["Sleep Duration"]["value"], "7.51")

    def test_july_included_and_earlier_history_excluded_from_managed_aggregates(self):
        values = [measurement("june", "2026-06-30", 110),
                  measurement("july", "2026-07-31", 100), measurement("august", value=80)]
        payload = aggregate(values, date(2026, 8, 31))
        self.assertEqual(list(payload["months"]), ["2026-07", "2026-08"])
        self.assertEqual(payload["months"]["2026-07"]["Body Mass"]["value"], "100.0")
        self.assertEqual(payload["months"]["2026-08"]["Body Mass"]["value"], "80.0")


class MonthlyValidationAndMergeTests(unittest.TestCase):
    def test_null_nonfinite_boolean_and_invalid_pair_rejected(self):
        invalid = [measurement("a", value=value) for value in
                   [None, float("nan"), float("inf"), float("-inf"), True, "80"]]
        invalid += [measurement("bp", value=value, metric="Blood Pressure", unit="mmHg")
                    for value in [120, [120], [120, 80, 70], [120, None], [120, float("nan")]]]
        for record in invalid:
            with self.subTest(record=record), self.assertRaises(ValueError):
                validate_records([record])

    def test_exact_duplicate_ids_deduplicate_but_conflicting_values_raise(self):
        first = measurement("reading", value=80)
        self.assertEqual(validate_records([first, copy.deepcopy(first)]), [first])
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate"):
            validate_records([first, measurement("reading", value=82)])
        different_metric = measurement("reading", value=15, metric="Body Fat", unit="%")
        self.assertEqual(len(validate_records([first, different_metric])), 2)

    def test_provider_range_replacement_prevents_csv_api_double_counting(self):
        july = oura("july", "2026-07-31", 8)
        before = oura("before", "2026-08-01", 7)
        old_csv = oura("old-csv", "2026-08-02", 6)
        removed_day = oura("old-deleted", "2026-08-03", 9)
        other_provider = measurement("weight", "2026-08-02", 80)
        after = oura("after", "2026-08-04", 8)
        incoming = oura("new-api", "2026-08-02", 7.5, "api")
        existing = [july, before, old_csv, removed_day, other_provider, after]
        original = copy.deepcopy(existing)
        merged = merge_records(existing, [incoming], {"oura"}, date(2026, 8, 2), date(2026, 8, 3))
        self.assertEqual({item["id"] for item in merged}, {"july", "before", "weight", "after", "new-api"})
        self.assertEqual(existing, original)
        self.assertEqual(sum(item["day"] == "2026-08-02" and item["provider"] == "oura"
                             for item in merged), 1)

    def test_before_july_import_rejected_and_empty_import_does_not_erase_existing(self):
        existing = [measurement("existing")]
        before = copy.deepcopy(existing)
        with self.assertRaisesRegex(ValueError, "2026-07-01"):
            merge_records(existing, [measurement("new")], {"withings"},
                          date(2026, 6, 30), date(2026, 8, 1))
        with self.assertRaisesRegex(ValueError, "No usable"):
            merge_records(existing, [], {"withings"}, date(2026, 8, 1), date(2026, 8, 31))
        self.assertEqual(existing, before)

    def test_authorized_july_fetch_replaces_july_cells_and_retains_june(self):
        existing = [measurement("june", "2026-06-30", 85), measurement("july-old", "2026-07-03", 83)]
        new = measurement("july-new", "2026-07-03", 80)
        result = merge_records(existing, [new], {"withings"}, date(2026, 7, 1), date(2026, 7, 31))
        self.assertEqual([record["id"] for record in result], ["june", "july-new"])

    def test_unrequested_provider_rejected_and_out_of_range_incoming_ignored(self):
        with self.assertRaisesRegex(ValueError, "outside this import"):
            merge_records([], [measurement("weight"), oura("sleep")], {"oura"},
                          date(2026, 8, 1), date(2026, 8, 31))
        result = merge_records([], [measurement("inside"), measurement("outside", "2026-09-01")],
                               {"withings"}, date(2026, 8, 1), date(2026, 8, 31))
        self.assertEqual([item["id"] for item in result], ["inside"])

    def test_partial_file_import_preserves_unrepresented_dates_metrics_and_readings(self):
        existing = [
            oura("old-api", value=7, source_kind="api"),
            oura("untouched-day", "2026-08-02", 8),
            measurement("hrv", value=25, metric="Average HRV (Sleep)", provider="oura", unit="ms"),
            measurement("scale-one", value=80),
            measurement("scale-two", value=82),
            measurement("scale-one", value=15, metric="Body Fat", unit="%"),
        ]
        incoming = [oura("new-csv", value=7.5), measurement("scale-one", value=79, source_kind="csv")]
        before = copy.deepcopy(existing)
        result = merge_file_records(existing, incoming, {"oura", "withings"},
                                    date(2026, 8, 1), date(2026, 8, 31))
        self.assertEqual(existing, before)
        self.assertEqual(len(result), 6)
        lookup = {(item["id"], item["metric"]): item["value"] for item in result}
        self.assertNotIn(("old-api", "Sleep Duration"), lookup)
        self.assertEqual(lookup[("new-csv", "Sleep Duration")], 7.5)
        self.assertEqual(lookup[("untouched-day", "Sleep Duration")], 8)
        self.assertEqual(lookup[("hrv", "Average HRV (Sleep)")], 25)
        self.assertEqual(lookup[("scale-one", "Body Mass")], 79)
        self.assertEqual(lookup[("scale-two", "Body Mass")], 82)
        self.assertEqual(lookup[("scale-one", "Body Fat")], 15)

    def test_competing_csv_and_api_values_for_one_oura_day_rejected(self):
        with self.assertRaisesRegex(ValueError, "Competing daily Oura"):
            merge_file_records([], [oura("csv", value=7), oura("api", value=8, source_kind="api")],
                               {"oura"}, date(2026, 8, 1), date(2026, 8, 31))

    def test_file_amendment_cannot_move_history_from_outside_requested_dates(self):
        incoming = [measurement("revised", "2026-08-15", 79)]
        for day in ("2026-07-31", "2026-09-01"):
            for partial_api in (False, True):
                with self.subTest(day=day, partial_api=partial_api):
                    existing = [measurement("revised", day), measurement("untouched")]
                    before = copy.deepcopy(existing)
                    with self.assertRaisesRegex(ValueError, "outside.*requested date range"):
                        merge_file_records(existing, incoming, {"withings"},
                                           date(2026, 8, 1), date(2026, 8, 31),
                                           partial_api=partial_api)
                    self.assertEqual(existing, before)

    def test_file_date_corrections_work_when_both_dates_are_in_range(self):
        for old_day, start in (("2026-08-01", date(2026, 8, 1)),
                               ("2026-07-31", date(2026, 7, 31))):
            with self.subTest(old_day=old_day):
                # Another metric with the same ID is a distinct observation.
                unrelated = measurement("revised", "2026-07-01", 15, "Body Fat", unit="%")
                old = measurement("revised", old_day)
                corrected = measurement("revised", "2026-08-31", 79)
                existing = [old, unrelated]
                before = copy.deepcopy(existing)
                merged = merge_file_records(existing, [corrected], {"withings"},
                                            start, date(2026, 8, 31))
                self.assertCountEqual(merged, [corrected, unrelated])
                self.assertEqual(existing, before)

    def test_partial_api_replaces_oura_observation_set_without_mixing_csv(self):
        existing = [oura("old-csv", value=6), oura("unavailable-day", "2026-08-02", 7)]
        incoming = [oura("sample-one", value=7, source_kind="api"),
                    oura("sample-two", value=9, source_kind="api")]
        result = merge_file_records(existing, incoming, {"oura"}, date(2026, 8, 1), date(2026, 8, 31), partial_api=True)
        self.assertEqual({record["id"] for record in result}, {"sample-one", "sample-two", "unavailable-day"})
        entry = aggregate(result, date(2026, 9, 1))["months"]["2026-08"]["Sleep Duration"]
        self.assertEqual(entry["value"], "7.50")
        with self.assertRaisesRegex(ValueError, "only API"):
            merge_file_records([], [oura("csv")], {"oura"}, date(2026, 8, 1), date(2026, 8, 31), partial_api=True)


class MonthlyReportOverlayTests(unittest.TestCase):
    def test_overlay_changes_only_imported_cells_and_their_value_footnotes(self):
        followups = {
            "2026-07": {"Body Mass": "85", "Body Fat": "20"},
            "2026-08": {"Body Mass": "81", "Body Fat": "16"},
            "2026-09": {"Body Mass": "80", "Body Fat": "15", "ECG": "Normal"},
        }
        notes = [
            {"text": "General baseline", "markers": []},
            {"text": "Old scale snapshot", "markers": [
                {"rows": ["Body Mass", "Body Fat"], "target": "value", "dates": ["2026-08", "2026-09"]}
            ]},
            {"text": "Only imported snapshot", "markers": [
                {"row": "Body Mass", "target": "value", "dates": ["2026-09"]}
            ]},
            {"text": "Unit explanation", "markers": [
                {"row": "Body Mass", "target": "unit", "dates": ["2026-09"]}
            ]},
            {"text": "Undated explanation", "markers": [
                {"row": "Body Mass", "target": "value"}
            ]},
        ]
        payload = aggregate([measurement("new", "2026-09-03", 79.4)], date(2026, 9, 5))
        apply_report_overlay(followups, notes, payload)
        self.assertEqual(followups["2026-09"], {"Body Mass": "79.4", "Body Fat": "15", "ECG": "Normal"})
        self.assertEqual(followups["2026-08"], {"Body Mass": "81", "Body Fat": "16"})
        self.assertEqual(followups["2026-07"], {"Body Mass": "85", "Body Fat": "20"})
        texts = [note["text"] for note in notes]
        self.assertNotIn("Only imported snapshot", texts)
        self.assertIn("General baseline", texts)
        self.assertIn("Unit explanation", texts)
        self.assertIn("Undated explanation", texts)
        old = next(note for note in notes if note["text"] == "Old scale snapshot")
        self.assertEqual(old["markers"], [
            {"row": "Body Mass", "target": "value", "dates": ["2026-08"]},
            {"row": "Body Fat", "target": "value", "dates": ["2026-08", "2026-09"]},
        ])
        self.assertEqual(notes[-1]["markers"], [{"target": "monthly_measurements"}])

    def test_empty_overlay_is_noop(self):
        followups = {"2026-07": {"Body Mass": "85"}}
        notes = [{"text": "Keep", "markers": []}]
        before = copy.deepcopy((followups, notes))
        apply_report_overlay(followups, notes, {"schema_version": 1, "months": {}})
        self.assertEqual((followups, notes), before)

    def test_coverage_note_has_metric_specific_count_range_and_partial_window(self):
        records = [measurement("one", "2026-09-01"), measurement("two", "2026-09-04"),
                   measurement("fat", "2026-09-02", 15, "Body Fat", unit="%")]
        note = report_note(aggregate(records, date(2026, 9, 5)))
        self.assertIn("Withings: 1-2/5 elapsed days (month to date)", note["text"])
        self.assertEqual(note["markers"], [{"target": "monthly_measurements"}])


class MonthlyFileValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "monthly.json"

    def write(self, payload):
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        return self.path

    def test_valid_generated_payload_roundtrips_and_missing_file_is_empty(self):
        self.assertEqual(load_monthly(self.path)["months"], {})
        payload = aggregate([measurement("a"), measurement("b", "2026-08-02", 82)], date(2026, 9, 5))
        self.assertEqual(load_monthly(self.write(payload)), payload)

    def test_nonfinite_or_unparseable_monthly_value_rejected_as_value_error(self):
        for value in ["NaN", "Infinity", "not a number"]:
            payload = aggregate([measurement("a")], date(2026, 9, 5))
            payload["months"]["2026-08"]["Body Mass"]["value"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                load_monthly(self.write(payload))

    def test_observation_dates_must_belong_to_their_month(self):
        payload = aggregate([measurement("a")], date(2026, 9, 5))
        payload["months"]["2026-08"]["Body Mass"]["last_day"] = "2026-09-01"
        with self.assertRaises(ValueError):
            load_monthly(self.write(payload))

    def test_calendar_length_and_record_count_cannot_contradict_coverage(self):
        payload = aggregate([measurement("a", "2028-02-01"), measurement("b", "2028-02-02")], date(2028, 3, 1))
        for changes in [{"calendar_days": 28, "elapsed_days": 28}, {"n_records": 1}]:
            modified = copy.deepcopy(payload)
            modified["months"]["2028-02"]["Body Mass"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                load_monthly(self.write(modified))

    def test_classification_payload_roundtrips_with_explicit_count_semantics(self):
        payload = classification_payload()
        self.assertEqual(load_monthly(self.write(payload)), payload)

    def test_numeric_breathing_indices_roundtrip_and_old_code_counts_require_rebuild(self):
        names = ("Breathing Disturbance Intensity (Withings)", "Breathing Quality Assessment (Withings)")
        payload = aggregate([measurement(name, value=12, metric=name, unit="index") for name in names],
                            date(2026, 9, 5))
        self.assertEqual(load_monthly(self.write(payload)), payload)
        for name in names:
            legacy = classification_payload("Device code 12")
            entry = legacy["categorical_months"]["2026-07"].pop("Stress Day Summary (Oura)")
            entry["provider"] = "withings"
            legacy["categorical_months"]["2026-07"][name] = entry
            with self.subTest(metric=name), self.assertRaisesRegex(ValueError, "rebuilding from the raw sleep source"):
                load_monthly(self.write(legacy))

    def test_classification_count_schema_and_provider_cannot_be_forged(self):
        changes = [{"unit": "score"}, {"aggregation": "mean_of_daily_means"}, {"provider": "withings"},
                   {"counts": {"Relaxed": True}}, {"counts": {"Relaxed": 0}}, {"counts": {}},
                   {"counts": {"bad\nlabel": 2}}, {"n_records": 3}, {"n_records": True},
                   {"n_days": 3}, {"n_days": True}, {"value": "2.0"}, {"last_day": "2026-08-01"}]
        for change in changes:
            payload = classification_payload()
            payload["categorical_months"]["2026-07"]["Stress Day Summary (Oura)"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                load_monthly(self.write(payload))

    def test_unknown_classification_marker_and_before_july_date_are_rejected(self):
        payload = classification_payload()
        original = payload["categorical_months"]["2026-07"].pop("Stress Day Summary (Oura)")
        payload["categorical_months"]["2026-07"]["Invented Result (Oura)"] = original
        with self.assertRaisesRegex(ValueError, "Unknown"):
            load_monthly(self.write(payload))
        payload = classification_payload()
        payload["categorical_months"]["2026-06"] = payload["categorical_months"].pop("2026-07")
        with self.assertRaisesRegex(ValueError, "date range"):
            load_monthly(self.write(payload))


class GeneratorMonthlyIntegrationTests(unittest.TestCase):
    """Load generator data in memory; rendering checks write only temporary files."""

    def load_generator(self, payload):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "monthly.json"
            source.write_text(json.dumps(payload), encoding="utf-8")
            with patch.dict(os.environ, {"HEALTH_PROTOCOL_VITALS_MONTHLY": str(source)}):
                return runpy.run_path(str(Path(__file__).parents[1] / "generate_colored_report.py"), run_name="report_data_test")

    def test_body_composition_shows_ffmi_directions_and_omits_old_bmi_snapshots(self):
        metric = "Fat-Free Mass (Withings)"
        payload = aggregate([measurement("first", "2026-07-01", 60, metric),
                             measurement("second", "2026-09-01", 61, metric)], date(2026, 9, 6))
        payload["ffmi_trend"] = {"2026-07": "baseline", "2026-09": "up"}
        report = self.load_generator(payload)
        rows = report["data"]["Vitals & Functional Health"]
        html = report["render_vitals_html"](rows)
        md = report["render_vitals_md"](rows)
        self.assertIn("<b>FFMI</b>", html)
        self.assertNotIn("<b>BMI</b>", html)
        self.assertNotIn("| **BMI** |", md)
        self.assertNotIn("<b>Height</b>", html)
        self.assertNotIn("| **Height** |", md)
        index_row = next(line for line in md.splitlines() if line.startswith("| **FFMI** |"))
        self.assertIn("| Up | - | Baseline | - | Prior mean | Withings |", index_row)

    def test_numeric_ffmi_shows_monthly_means_and_physique_colors(self):
        readings = [measurement("first", "2026-07-01", 20.2, "FFMI", unit="kg/m²"),
                    measurement("second", "2026-09-01", 20.7, "FFMI", unit="kg/m²")]
        report = self.load_generator(aggregate(readings, date(2026, 9, 6)))
        rows = report["data"]["Vitals & Functional Health"]
        html = report["render_vitals_html"](rows)
        md = report["render_vitals_md"](rows)
        index_row = next(line for line in md.splitlines() if line.startswith("| **FFMI** |"))
        self.assertIn("| 🟢 | 🟡 20.7 | - | 🟡 20.2 | kg/m² | Physique scale (180cm) | Withings |", index_row)
        ffmi_row = next(row for row in rows if row[0] == "FFMI")
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = report[f"render_result_table_{output_format}"](
                    "Vitals & Functional Health", [ffmi_row], compact=True)
                header, result = rendered_table_rows(rendered, output_format)
                self.assertEqual(result[header.index("Trend")], "🟢")
                self.assertEqual(result[header.index("2026-09")], "🟡 20.7")
                self.assertEqual(result[header.index("2026-07")], "🟡 20.2")
                self.assertEqual(result[header.index("Unit")], "kg/m²")
                self.assertNotRegex(rendered, "[↑↓→]")
        self.assertNotIn("<b>Height</b>", html)
        self.assertNotIn("| **Height** |", md)

    def test_july_replaces_existing_column_once_without_changing_labs(self):
        baseline = self.load_generator({"schema_version": 1, "as_of": "2026-09-06", "months": {}})
        payload = aggregate([measurement("actual", "2026-07-15", 79.2)], date(2026, 9, 6))
        current = self.load_generator(payload)
        self.assertEqual(current["date_columns"].count("2026-07"), 1)
        self.assertEqual(current["date_columns"], baseline["date_columns"])
        row = next(row for row in current["data"]["Vitals & Functional Health"] if row[0] == "Body Mass")
        july_index = current["date_columns"].index("2026-07") + 1
        self.assertEqual(row[july_index], "79.2")
        original = next(row for row in baseline["data"]["Vitals & Functional Health"] if row[0] == "Body Mass")
        self.assertNotEqual(row[july_index], original[july_index])
        for category in current["data"]:
            if category != "Vitals & Functional Health":
                self.assertEqual(current["data"][category], baseline["data"][category])
        category = "Vitals & Functional Health"
        self.assertEqual(current["note_numbers"](category, "Body Mass", "value", "2026-07"), [])
        self.assertTrue(current["note_numbers"](category, "Body Mass", "value", "2026-08"))

    def test_registry_addition_creates_only_observed_row_without_invented_target(self):
        from tools.health_sync import monthly
        metric = "Synthetic Measurement (Oura)"
        registry = {"oura": {metric: ("ms", 1)}, "withings": {}}
        with patch.object(monthly, "METRICS", registry):
            record = measurement("synthetic", "2026-07-15", 12.3, metric, "oura", "ms")
            current = self.load_generator(aggregate([record], date(2026, 9, 6)))
        row = next(row for row in current["data"]["Vitals & Functional Health"] if row[0] == metric)
        self.assertEqual(row[-2:], ("ms", "-"))
        self.assertEqual(row[current["date_columns"].index("2026-07") + 1], "12.3")
        self.assertIn(("Vitals & Functional Health", metric), current["no_score_markers"])

    def test_classification_row_uses_counts_and_keeps_labs_and_manual_states(self):
        baseline = self.load_generator({"schema_version": 1, "as_of": "2026-09-06", "months": {}})
        current = self.load_generator(classification_payload())
        row = next(row for row in current["data"]["Vitals & Functional Health"] if row[0] == "Stress Day Summary (Oura)")
        self.assertEqual(row[-2:], ("Status", "-"))
        self.assertEqual(row[current["date_columns"].index("2026-07") + 1], "Relaxed: 2")
        self.assertEqual(current["date_columns"].count("2026-07"), 1)
        self.assertIn(("Vitals & Functional Health", row[0]), current["no_score_markers"])
        for category in current["data"]:
            if category != "Vitals & Functional Health":
                self.assertEqual(current["data"][category], baseline["data"][category])
        for name in ("Stress", "ECG Rhythm", "Heart Sounds"):
            self.assertEqual(next(r for r in current["data"]["Vitals & Functional Health"] if r[0] == name),
                             next(r for r in baseline["data"]["Vitals & Functional Health"] if r[0] == name))
        category = "Vitals & Functional Health"
        self.assertEqual(current["note_numbers"](category, None, "monthly_measurements"), [])
        self.assertEqual(current["note_numbers"](category, row[0], "value", "2026-07"), [])
        number, = current["note_numbers"](category, None, "classification_counts")
        note = current["result_notes"][category][number - 1]
        self.assertIn("counts of observed labels", note["text"])
        self.assertEqual(note["markers"], [{"target": "classification_counts"}])

    def test_partial_import_shares_each_source_once_but_keeps_manual_readings_marked(self):
        payload = classification_payload()
        payload["months"] = aggregate([measurement("actual", "2026-07-15", 79.2)],
                                      date(2026, 9, 6))["months"]
        followups, notes = {}, []
        apply_report_overlay(followups, notes, payload)
        first_overlay = copy.deepcopy((followups, notes))
        apply_report_overlay(followups, notes, payload)
        self.assertEqual((followups, notes), first_overlay)
        report = self.load_generator(payload)
        category = "Vitals & Functional Health"
        manual, = report["note_numbers"](category, "Body Mass", "value", "2026-08")
        for output_format in ("html", "md"):
            with self.subTest(output_format=output_format):
                rendered = report[f"render_vitals_{output_format}"](report["data"][category])
                row_end = "</tr>" if output_format == "html" else "\n"
                body_mass = rendered.split("Body Mass", 1)[1].split(row_end, 1)[0]
                self.assertIn(f"<sup>{manual}</sup>", body_mass)
                for target, label, definition in (
                    ("monthly_measurements", "Monthly device summaries", "Imported monthly summaries"),
                    ("classification_counts", "classification counts", "Imported device classifications"),
                ):
                    number, = report["note_numbers"](category, None, target)
                    marker = f"<sup>{number}</sup>"
                    self.assertIn(label + marker, rendered)
                    self.assertIn(f"{marker} {definition}", rendered)
                    self.assertEqual(rendered.count(marker), 2)

    def test_classification_labels_are_escaped_in_both_report_formats(self):
        label = '<script>alert("x")</script>|[a](javascript:1)'
        current = self.load_generator(classification_payload(label))
        with tempfile.TemporaryDirectory() as folder:
            html_path, md_path = Path(folder) / "test.html", Path(folder) / "test.md"
            current["generate_html_report"](html_path)
            current["generate_md_report"](md_path)
            html_text, md_text = html_path.read_text(encoding="utf-8"), md_path.read_text(encoding="utf-8")
        self.assertNotIn("<script>", html_text)
        self.assertNotIn("<script>", md_text)
        self.assertIn("&lt;script&gt;", html_text)
        self.assertIn("\\|\\[a\\]", md_text)
        self.assertNotIn("[a](javascript:1)", md_text)


if __name__ == "__main__":
    unittest.main()
