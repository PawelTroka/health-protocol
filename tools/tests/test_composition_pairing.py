"""Synthetic scale readings: group provenance must survive monthly reporting."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from tools.health_sync.monthly import aggregate, load_monthly
from tools.health_sync import vitals_targets as targets
from tools.health_sync.withings import parse_api
from tools.tests.test_withings_sync import group, measure, timestamp


DIGEST = "measurement_groups_sha256"
COMPONENTS = {
    "Fat Mass (Withings)": (8, 12),
    "Muscle Mass (Withings)": (76, 65),
    "Bone Mass (Withings)": (88, 3.2),
    "Fat-Free Mass (Withings)": (5, 68),
    "Water Mass (Withings)": (77, 48),
}


def component_measures():
    return [measure(kind, value) for kind, value in COMPONENTS.values()]


def monthly(groups):
    records = parse_api({"measuregrps": groups})
    return records, aggregate(records, date(2026, 10, 1))


class CompositionPairingTests(unittest.TestCase):
    def assert_ungraded(self, context):
        for marker in COMPONENTS:
            with self.subTest(marker=marker):
                value = context[marker]["value"]
                self.assertIsNone(targets.evaluated_value(marker, value, context))
                self.assertIsNone(targets.status(marker, value, context))

    def test_same_day_equal_counts_from_disjoint_groups_do_not_establish_percentages(self):
        records, payload = monthly([
            group(measure(1, 80), key=100),
            group(*component_measures(), key=200),
        ])
        # The importer correctly refuses to derive a percentage here. The
        # report must not reconstruct one from two unrelated monthly means.
        self.assertFalse(any(record["unit"] == "%" for record in records))
        context = payload["months"]["2026-09"]
        self.assertEqual({entry["n_records"] for entry in context.values()}, {1})
        self.assertEqual({entry["observed_days"] for entry in context.values()}, {"2026-09-05"})
        self.assert_ungraded(context)

    def test_partial_group_overlap_with_equal_dates_and_counts_is_not_pairing(self):
        _, payload = monthly([
            group(measure(1, 80), *component_measures(), key=100),
            group(measure(1, 80), key=200),
            group(*component_measures(), key=300),
        ])
        context = payload["months"]["2026-09"]
        self.assertEqual(context["Body Mass"]["n_records"], 2)
        self.assertTrue(all(context[marker]["n_records"] == 2 for marker in COMPONENTS))
        self.assert_ungraded(context)

    def test_complete_paired_groups_retain_existing_statuses_without_changing_records(self):
        records, payload = monthly([
            group(measure(1, 80), *component_measures(), key="SYNTHETIC-SCALE-GROUP-A"),
            group(measure(1, 80), *component_measures(), key="SYNTHETIC-SCALE-GROUP-B",
                  date="2026-09-06T20:36:00"),
        ])
        before = deepcopy(records)
        self.assertEqual(aggregate(list(reversed(records)), date(2026, 10, 1)), payload)
        self.assertEqual(records, before)
        context = payload["months"]["2026-09"]
        for marker, emoji in zip(COMPONENTS, ("🔵", "🟢", "🟢", "🔵", "🟢")):
            with self.subTest(marker=marker):
                self.assertEqual(context[marker][DIGEST], context["Body Mass"][DIGEST])
                self.assertEqual(targets.status(marker, context[marker]["value"], context)[1], emoji)
        self.assertNotIn("SYNTHETIC-SCALE-GROUP", json.dumps(payload))
        self.assertNotIn(DIGEST, context["BMI"])
        self.assertNotIn(DIGEST, context["Muscle"])

    def test_missing_or_untrusted_contributor_metadata_withholds_the_entire_digest(self):
        records, _ = monthly([
            group(measure(1, 80), *component_measures(), key=100),
            group(measure(1, 80), *component_measures(), key=200),
        ])
        for field, value in (("group_id", None), ("group_id", ""), ("group_id", 200),
                             ("group_id", " 200"), ("group_id", "wrong"),
                             ("id", "legacy-record"), ("source_kind", "csv"),
                             ("source_count", 2), ("recorded_at", None),
                             ("recorded_at", "2026-09-05T22:36:00"),
                             ("recorded_at", "2026-09-06T22:36:00+02:00"),
                             ("source_modified_at", "unknown")):
            for marker in ("Body Mass", *COMPONENTS):
                with self.subTest(field=field, value=value, marker=marker):
                    changed = deepcopy(records)
                    record = next(record for record in changed
                                  if record["metric"] == marker and record["group_id"] == "200")
                    if value is None:
                        record.pop(field)
                    else:
                        record[field] = value
                    context = aggregate(changed, date(2026, 10, 1))["months"]["2026-09"]
                    self.assertNotIn(DIGEST, context[marker])
                    affected = COMPONENTS if marker == "Body Mass" else (marker,)
                    for component in affected:
                        self.assertIsNone(targets.status(component, context[component]["value"], context))

    def test_same_group_with_conflicting_recording_or_revision_metadata_is_not_paired(self):
        records, _ = monthly([group(measure(1, 80), *component_measures(), key=100,
                                    modified=timestamp("2026-09-06T20:36:00"))])
        for field, value in (("recorded_at", "2026-09-05T22:37:00+02:00"),
                             ("source_modified_at", "2026-09-06T22:37:00+02:00"),
                             ("source_modified_at", None)):
            with self.subTest(field=field, value=value):
                changed = deepcopy(records)
                weight = next(record for record in changed if record["metric"] == "Body Mass")
                if value is None:
                    weight.pop(field)
                else:
                    weight[field] = value
                context = aggregate(changed, date(2026, 10, 1))["months"]["2026-09"]
                self.assertIn(DIGEST, context["Body Mass"])
                self.assert_ungraded(context)

    def test_membership_digest_covers_each_date_but_does_not_change_numeric_aggregation(self):
        groups = [
            group(measure(1, 80), *component_measures(), key=100),
            group(measure(1, 90), *component_measures(), key=200,
                  date="2026-09-06T20:36:00"),
        ]
        records, payload = monthly(groups)
        without_provenance = deepcopy(records)
        for record in without_provenance:
            record.pop("group_id", None)
        legacy = aggregate(without_provenance, date(2026, 10, 1))
        stripped = deepcopy(payload)
        for entry in stripped["months"]["2026-09"].values():
            entry.pop(DIGEST, None)
        self.assertEqual(stripped, legacy)
        digest = payload["months"]["2026-09"]["Body Mass"][DIGEST]
        changed_day = deepcopy(records)
        for record in changed_day:
            if record["group_id"] == "200":
                record["day"] = "2026-09-07"
                record["recorded_at"] = record["recorded_at"].replace("2026-09-06", "2026-09-07")
        changed = aggregate(changed_day, date(2026, 10, 1))
        self.assertNotEqual(changed["months"]["2026-09"]["Body Mass"][DIGEST], digest)

    def test_newest_or_previous_unpaired_month_blocks_component_trends(self):
        previous = [measure(kind, value) for kind, value in
                    ((8, 24), (76, 64), (88, 3.2), (5, 68), (77, 32))]
        current = [measure(kind, value) for kind, value in
                   ((8, 16), (76, 65), (88, 3.4), (5, 69), (77, 40))]
        for unpaired_month in (None, "2026-08", "2026-09"):
            groups = []
            for key, month, components in ((10, "2026-08", previous), (20, "2026-09", current)):
                if month == unpaired_month:
                    groups += [group(measure(1, 80), key=key, date=month + "-05T20:36:00"),
                               group(*components, key=key + 1, date=month + "-05T20:36:00")]
                else:
                    groups.append(group(measure(1, 80), *components, key=key, date=month + "-05T20:36:00"))
            _, payload = monthly(groups)
            contexts = [payload["months"][month] for month in ("2026-09", "2026-08")]
            for marker in COMPONENTS:
                with self.subTest(unpaired_month=unpaired_month, marker=marker):
                    values = [context[marker]["value"] for context in contexts]
                    expected = "🟢" if unpaired_month is None else "-"
                    self.assertEqual(targets.trend(values, marker, contexts), expected)

    def test_legacy_monthly_cells_remain_readable_without_inferred_pairing(self):
        _, payload = monthly([group(measure(1, 80), *component_measures(), key=100)])
        for removed in (("Body Mass",), tuple(COMPONENTS), ("Body Mass", *COMPONENTS)):
            with self.subTest(removed=removed):
                legacy = deepcopy(payload)
                for marker in removed:
                    legacy["months"]["2026-09"][marker].pop(DIGEST, None)
                self.assert_ungraded(self.roundtrip(legacy)["months"]["2026-09"])

    def test_group_provenance_roundtrips_and_rejects_malformed_or_mixed_source_metadata(self):
        _, payload = monthly([group(measure(1, 80), *component_measures(), key=100)])
        self.assertEqual(self.roundtrip(payload), payload)
        for invalid in (None, "", "a" * 63, "A" * 64, "g" * 64, "a" * 65, 123, []):
            with self.subTest(invalid=invalid):
                changed = deepcopy(payload)
                context = changed["months"]["2026-09"]
                context["Body Mass"][DIGEST] = invalid
                self.assert_ungraded(context)
                with self.assertRaisesRegex(ValueError, "measurement-group provenance"):
                    self.roundtrip(changed)
        changed = deepcopy(payload)
        changed["months"]["2026-09"]["Body Mass"]["source_kinds"] = ["api", "csv"]
        self.assert_ungraded(changed["months"]["2026-09"])
        with self.assertRaisesRegex(ValueError, "measurement-group provenance"):
            self.roundtrip(changed)
        changed = deepcopy(payload)
        context = changed["months"]["2026-09"]
        context["BMI"][DIGEST] = context["Body Mass"][DIGEST]
        with self.assertRaisesRegex(ValueError, "measurement-group provenance"):
            self.roundtrip(changed)

    @staticmethod
    def roundtrip(payload):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "monthly.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_monthly(path)


if __name__ == "__main__":
    unittest.main()
