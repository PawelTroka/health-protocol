"""Oura schedule and confirmed short-sleep fixtures; no account or report writes."""

import copy
import unittest

from tools.health_sync.oura import OURA_METRICS, OuraParseError, parse_api
from tools.tests.test_oura_sync import by_metric, sleep_document


def short_sleep(identifier="nap", day="2026-08-01", **changes):
    return {"id": identifier, "day": day, "type": "sleep",
            "bedtime_start": day + "T14:00:00+02:00",
            "bedtime_end": day + "T14:40:00+02:00", "time_in_bed": 2400,
            "total_sleep_duration": 1800, **changes}


def complete_payload(*documents):
    return {"sleep": list(documents), "_sync": {"start": "2026-07-01", "end": "2026-10-31",
                                               "endpoint_status": {"sleep": {"status": "complete"}}}}


class OuraSleepDetailsTests(unittest.TestCase):
    def test_schedule_preserves_local_clock_and_midnight_elapsed_midpoint(self):
        night = sleep_document(bedtime_start="2026-07-31T23:30:00+02:00",
                               bedtime_end="2026-08-01T08:30:00+02:00")
        values = by_metric(parse_api({"sleep": [night]}))
        self.assertEqual(values["Bedtime (Oura)"]["value"], 1410)
        self.assertEqual(values["Wake-up Time (Oura)"]["value"], 510)
        middle = values["Sleep Midpoint (Oura)"]
        self.assertEqual((middle["value"], middle["unit"]), (240, "hh:mm"))
        self.assertEqual(middle["local_time"], "2026-08-01T04:00:00+02:00")
        self.assertEqual(middle["utc_offset_seconds"], 7200)
        self.assertEqual(middle["day"], "2026-08-01")
        self.assertNotIn("Sleep Midpoint Variability (Oura)", values)
        self.assertEqual(OURA_METRICS["Sleep Midpoint Variability (Oura)"], ("min", 0))

    def test_dst_midpoint_uses_elapsed_time_and_the_matching_home_zone(self):
        night = sleep_document(day="2026-10-25", bedtime_start="2026-10-25T00:00:00+02:00",
                               bedtime_end="2026-10-25T08:00:00+01:00")
        values = by_metric(parse_api({"sleep": [night]}))
        self.assertEqual(values["Bedtime (Oura)"]["value"], 0)
        self.assertEqual(values["Wake-up Time (Oura)"]["value"], 480)
        self.assertEqual(values["Sleep Midpoint (Oura)"]["value"], 210)
        self.assertEqual(values["Sleep Midpoint (Oura)"]["utc_offset_seconds"], 3600)

    def test_travel_offset_is_preserved_and_unresolved_offset_change_has_no_midpoint(self):
        night = sleep_document(bedtime_start="2026-07-31T23:30:00-04:00",
                               bedtime_end="2026-08-01T08:30:00-04:00")
        values = by_metric(parse_api({"sleep": [night]}))
        self.assertEqual(values["Bedtime (Oura)"]["value"], 1410)
        self.assertEqual(values["Sleep Midpoint (Oura)"]["value"], 240)
        self.assertEqual(values["Sleep Midpoint (Oura)"]["utc_offset_seconds"], -14400)
        night["bedtime_end"] = "2026-08-01T08:30:00-03:00"
        values = by_metric(parse_api({"sleep": [night]}))
        self.assertNotIn("Sleep Midpoint (Oura)", values)
        self.assertIn("Wake-up Time (Oura)", values)

    def test_short_night_indicator_is_strictly_below_seven_hours_and_primary_only(self):
        for total, expected in [(25199, 100), (25200, 0), (25201, 0)]:
            night = sleep_document(total_sleep_duration=total, light_sleep_duration=total - 9600)
            values = by_metric(parse_api({"sleep": [night, short_sleep()]}))
            with self.subTest(total=total):
                self.assertEqual(values["Short Sleep Nights (Oura)"]["value"], expected)
                self.assertEqual(values["Short Sleep Nights (Oura)"]["source_field"],
                                 "total_sleep_duration<25200")
        self.assertNotIn("Short Sleep Nights (Oura)", by_metric(parse_api({"sleep": [short_sleep()]})))

    def test_short_sleep_counts_deduplicate_ids_and_preserve_authoritative_late_nap_day(self):
        nap = short_sleep()
        late = short_sleep("late", type="late_nap", day="2026-08-02",
                           bedtime_start="2026-08-01T20:00:00+02:00",
                           bedtime_end="2026-08-01T20:30:00+02:00", time_in_bed=1800,
                           total_sleep_duration=1200)
        payload = complete_payload(sleep_document(), nap, nap, late,
                                   short_sleep("rejected", type="rest"),
                                   short_sleep("deleted", type="deleted"))
        before = copy.deepcopy(payload)
        records = parse_api(payload)
        counts = {r["day"]: r for r in records if r["metric"] == "Recorded Short-Sleep Periods (Oura)"}
        durations = {r["day"]: r["value"] for r in records if r["metric"] == "Recorded Short-Sleep Duration (Oura)"}
        self.assertEqual({day: row["value"] for day, row in counts.items()}, {"2026-08-01": 1, "2026-08-02": 1})
        self.assertEqual(durations, {"2026-08-01": 0.5, "2026-08-02": 1 / 3})
        self.assertEqual(counts["2026-08-02"]["source_period_types"], ["late_nap"])
        self.assertEqual(counts["2026-08-01"]["source_record_ids"], ["nap"])
        self.assertEqual(by_metric(records)["Sleep Duration"]["value"], 7.5)
        self.assertEqual(payload, before)
        self.assertEqual(records, parse_api({**payload, "sleep": list(reversed(payload["sleep"]))}))

    def test_two_distinct_nonoverlapping_naps_sum_before_monthly_totals(self):
        second = short_sleep("second", bedtime_start="2026-08-01T16:00:00+02:00",
                             bedtime_end="2026-08-01T16:40:00+02:00", total_sleep_duration=600)
        values = by_metric(parse_api({"sleep": [short_sleep(), second]}))
        self.assertEqual(values["Recorded Short-Sleep Periods (Oura)"]["value"], 2)
        self.assertEqual(values["Recorded Short-Sleep Duration (Oura)"]["value"], 2 / 3)
        self.assertNotIn("Sleep Duration", values)

    def test_zero_short_sleep_requires_complete_endpoint_and_completed_primary_night(self):
        values = by_metric(parse_api(complete_payload(sleep_document())))
        zero = values["Recorded Short-Sleep Periods (Oura)"]
        self.assertEqual(zero["value"], 0)
        self.assertEqual(zero["zero_evidence_primary_sleep_id"], "main")
        for payload in ({}, {"sleep": []}, {"sleep": [sleep_document()]},
                        complete_payload(sleep_document(total_sleep_duration=None)),
                        {**complete_payload(sleep_document()), "_sync": {"endpoint_status": {"sleep": {"status": "unavailable"}}}}):
            with self.subTest(payload=payload):
                self.assertNotIn("Recorded Short-Sleep Periods (Oura)", by_metric(parse_api(payload)))

    def test_incomplete_or_overlapping_short_period_does_not_create_a_false_zero_or_double_count(self):
        for nap in [short_sleep(total_sleep_duration=None),
                    short_sleep(bedtime_start="2026-08-01T08:30:00+02:00",
                                bedtime_end="2026-08-01T09:10:00+02:00")]:
            values = by_metric(parse_api(complete_payload(sleep_document(), nap)))
            self.assertNotIn("Recorded Short-Sleep Periods (Oura)", values)
            self.assertEqual(values["Sleep Duration"]["value"], 7.5)
        values = by_metric(parse_api(complete_payload(short_sleep(), short_sleep("duplicate-interval"))))
        self.assertNotIn("Recorded Short-Sleep Duration (Oura)", values)

    def test_short_sleep_invalid_durations_and_conflicting_ids_fail_closed(self):
        for nap in [short_sleep(total_sleep_duration=-1), short_sleep(total_sleep_duration=3000),
                    short_sleep(bedtime_end="2026-08-01T13:00:00+02:00")]:
            with self.subTest(nap=nap), self.assertRaises(OuraParseError):
                parse_api({"sleep": [nap]})
        with self.assertRaisesRegex(OuraParseError, "conflicting duplicate"):
            parse_api({"sleep": [short_sleep(), short_sleep(total_sleep_duration=1600)]})
