"""Endpoint completeness must not leak across providers or discard access gaps."""

from datetime import date
import unittest

from tools.health_sync.reconcile import infer_endpoint, merge_synced


START, END = date(2026, 7, 1), date(2026, 9, 5)


def record(provider, identifier, metric, value, unit, day="2026-08-01", **extra):
    return {"provider": provider, "id": identifier, "metric": metric, "value": value,
            "unit": unit, "day": day, "source_kind": "api", **extra}


def sleep(identifier="oura:api:sleep:night:Sleep Duration", value=7, **extra):
    return record("oura", identifier, "Sleep Duration", value, "h", **extra)


def weight(identifier="withings:measure:group:Body Mass", value=80, **extra):
    return record("withings", identifier, "Body Mass", value, "kg", **extra)


def coverage(**endpoints):
    return {"start": START.isoformat(), "end": END.isoformat(), "endpoint_status": {
        endpoint: {"status": status} for endpoint, status in endpoints.items()
    }}


def classification(kind, identifier, value="Negative", day="2026-08-01"):
    return {"provider": "withings", "id": f"withings:event:{kind}:{identifier}:ECG AF Classification (Withings)",
            "day": day, "metric": "ECG AF Classification (Withings)", "value": value,
            "source_kind": "api", "recorded_at": day + "T09:00:00+02:00"}


class ReconciliationTests(unittest.TestCase):
    def test_endpoint_inference_covers_metadata_legacy_ids_csv_and_categories(self):
        cases = [
            (sleep(), "sleep"),
            (sleep("legacy", source_endpoint="sleep"), "sleep"),
            (sleep("oura:csv:2026-08-01:Sleep Duration", source_kind="csv"), "sleep"),
            (record("oura", "oura:csv:2026-08-01:Sleep Score", "Sleep Score", 90, "score",
                    source_kind="csv"), "daily_sleep"),
            (weight(), "measure"),
            ({"provider": "withings", "id": "withings:sleep:x:marker"}, "getsummary"),
            ({"provider": "withings", "id": "withings:activity:x:marker"}, "getactivity"),
            (classification("heart", "signal"), "heart"),
            (classification("stetho", "signal"), "stetho"),
            ({"provider": "oura", "id": "oura:event:daily_stress:x:marker"}, "daily_stress"),
            (sleep("unknown-old-origin"), None),
        ]
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(infer_endpoint(value), expected)

    def test_complete_sleep_clears_removed_values_while_unavailable_daily_score_survives(self):
        old_score = record("oura", "oura:api:daily_sleep:old:Sleep Score", "Sleep Score", 81, "score")
        new_sleep = sleep("oura:api:sleep:new:Sleep Duration", 8, day="2026-08-02")
        result = merge_synced([sleep(), old_score], [new_sleep], ["oura"], START, END,
                              {"oura": coverage(sleep="complete", daily_sleep="unavailable")})
        self.assertEqual({row["id"] for row in result}, {old_score["id"], new_sleep["id"]})

    def test_unavailable_oura_does_not_preserve_deleted_complete_withings_measurements(self):
        old_oura = sleep()
        result = merge_synced([old_oura, weight()], [], ["oura", "withings"], START, END, {
            "oura": coverage(sleep="unavailable"),
            "withings": coverage(measure="complete", stetho="unavailable"),
        })
        self.assertEqual(result, [old_oura])

    def test_complete_empty_endpoint_is_allowed_and_unknown_origins_are_conservative(self):
        unknown = weight("unknown-manual-origin")
        result = merge_synced([weight(), unknown], [], ["withings"], START, END,
                              {"withings": coverage(measure="complete")})
        self.assertEqual(result, [unknown])

    def test_unknown_coverage_amends_represented_oura_days_without_mixing_csv_and_samples(self):
        csv = sleep("oura:csv:2026-08-01:Sleep Duration", source_kind="csv")
        old_other_day = sleep("oura:api:sleep:other:Sleep Duration", day="2026-08-02")
        incoming = [sleep("oura:api:sleep:new-a:Sleep Duration", 8),
                    sleep("oura:api:sleep:new-b:Sleep Duration", 9)]
        result = merge_synced([csv, old_other_day], incoming, ["oura"], START, END, {})
        self.assertEqual({row["id"] for row in result}, {row["id"] for row in [old_other_day, *incoming]})

    def test_unknown_coverage_preserves_distinct_same_day_withings_events(self):
        first = weight("withings:measure:first:Body Mass")
        second = weight("withings:measure:second:Body Mass", 81)
        updated = {**second, "value": 82, "source_file": "new-source.json"}
        result = merge_synced([first, second], [updated], ["withings"], START, END, {})
        self.assertEqual(result, [first, updated])

    def test_categorical_complete_heart_and_unavailable_stetho_are_independent(self):
        old_heart = classification("heart", "old")
        old_stetho = classification("stetho", "old")
        new_heart = classification("heart", "new", "Inconclusive")
        result = merge_synced([old_heart, old_stetho], [new_heart], ["withings"], START, END,
                              {"withings": coverage(heart="complete", stetho="unavailable")},
                              classifications=True)
        self.assertEqual({row["id"] for row in result}, {old_stetho["id"], new_heart["id"]})

    def test_range_boundaries_and_unrequested_providers_are_preserved(self):
        before = weight("withings:measure:before:Body Mass", day="2026-06-30")
        after = weight("withings:measure:after:Body Mass", day="2026-09-06")
        first = weight("withings:measure:first:Body Mass", day="2026-07-01")
        last = weight("withings:measure:last:Body Mass", day="2026-09-05")
        other = sleep()
        result = merge_synced([before, after, first, last, other], [], ["withings"], START, END,
                              {"withings": coverage(measure="complete")})
        self.assertEqual({row["id"] for row in result}, {before["id"], after["id"], other["id"]})

    def test_mismatched_coverage_malformed_status_and_unexpected_provider_rejected(self):
        invalid = [
            {"withings": {**coverage(measure="complete"), "start": "2026-08-01"}},
            {"withings": {"endpoint_status": {"measure": "complete"}}},
            {"withings": {"endpoint_status": []}},
        ]
        for statuses in invalid:
            with self.subTest(statuses=statuses), self.assertRaises(ValueError):
                merge_synced([weight()], [], ["withings"], START, END, statuses)
        with self.assertRaises(ValueError):
            merge_synced([], [sleep()], ["withings"], START, END, {})
        with self.assertRaises(ValueError):
            merge_synced([], [], ["withings"], date(2026, 6, 1), END, {})


if __name__ == "__main__":
    unittest.main()
