"""FFMI uses the report's existing watch, acceptable, target and context colors."""

import unittest

from tools.health_sync import vitals_targets as targets
from tools.health_sync.report_guidance import guide_status, vitals_trend


class FFMIPhysiqueTests(unittest.TestCase):
    def test_shared_result_colors_at_each_band_boundary(self):
        cases = (
            ("17.9", "🟡"),
            ("18", "🟢"), ("19.9", "🟢"),
            ("20", "🟢"), ("21.9", "🟢"),
            ("22.0", "🔵"), ("23.9", "🔵"),
            ("24", "🔵"), ("25.9", "🔵"),
            ("26", "⚪"), ("29", "⚪"),
        )
        for value, emoji in cases:
            with self.subTest(value=value):
                status = guide_status("Vitals & Functional Health", "FFMI", value)
                self.assertEqual(status[1], emoji)
        self.assertEqual(targets.reference("FFMI"), "18–<26 (goal 22–<26)")

    def test_current_monthly_values_use_the_selected_comparison(self):
        for value, emoji in (("22.0", "🔵"), ("21.4", "🟢"),
                             ("21.9", "🟢"), ("22.1", "🔵")):
            with self.subTest(value=value):
                self.assertEqual(targets.status("FFMI", value)[1], emoji)
        self.assertEqual(vitals_trend(["22.0", "21.4"], "FFMI"), "🟢")

    def test_trend_approaches_target_and_stays_neutral_within_it(self):
        for values, expected in ((["22", "21.4"], "🟢"),
                                 (["21.4", "22"], "🟡"),
                                 (["24", "23.5"], "⚪"),
                                 (["23.5", "24"], "⚪"),
                                 (["25.9", "22"], "⚪"),
                                 (["22", "22"], "⚪")):
            with self.subTest(values=values):
                self.assertEqual(vitals_trend(values, "FFMI"), expected)

    def test_context_dependent_high_reading_keeps_either_trend_direction_neutral(self):
        for current, previous in (("26", "25.9"), ("26", "24"),
                                  ("29", "21.4"), ("29", "26")):
            for values in ([current, previous], [previous, current]):
                with self.subTest(values=values):
                    self.assertEqual(vitals_trend(values, "FFMI"), "⚪")

    def test_small_changes_remain_neutral_including_across_a_band_boundary(self):
        for current, previous in (("22", "21.95"), ("23.05", "23")):
            for values in ([current, previous], [previous, current]):
                with self.subTest(values=values):
                    self.assertEqual(vitals_trend(values, "FFMI"), "⚪")
        self.assertEqual(vitals_trend(["22", "21.9"], "FFMI"), "🟢")
        self.assertEqual(vitals_trend(["21.9", "22"], "FFMI"), "🟡")
        self.assertEqual(vitals_trend(["22.1", "22"], "FFMI"), "⚪")
        self.assertEqual(vitals_trend(["22", "22.1"], "FFMI"), "⚪")

    def test_invalid_or_unfinished_values_are_ungraded_and_block_stale_trends(self):
        for value in ("0", "-1", "pending", "inconclusive", "unknown", "NaN", "inf", "<22", "114/75"):
            with self.subTest(value=value):
                self.assertIsNone(targets.status("FFMI", value))
                self.assertEqual(vitals_trend([value, "22", "21.4"], "FFMI"), "-")
        for values in ([], ["22"], ["-", "22"]):
            self.assertEqual(vitals_trend(values, "FFMI"), "-")
        self.assertEqual(vitals_trend(["-", "22", "-", "21.4"], "FFMI"), "🟢")

    def test_index_policy_does_not_classify_fat_free_mass_kilograms(self):
        self.assertIsNone(targets.status("Fat-Free Mass (Withings)", "65"))
        self.assertIsNone(guide_status("Other category", "FFMI", "22"))


if __name__ == "__main__":
    unittest.main()
