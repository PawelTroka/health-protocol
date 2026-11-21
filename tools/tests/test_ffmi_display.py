"""The selected FFMI physique scale is separate from clinical result grading."""

import unittest

from tools.health_sync import vitals_targets as targets
from tools.health_sync.report_guidance import guide_status, vitals_trend


class FFMIPhysiqueTests(unittest.TestCase):
    def test_physique_colors_at_each_band_boundary(self):
        cases = (
            ("17.9", "🔴", "below average"),
            ("18", "🟠", "average"), ("19.9", "🟠", "average"),
            ("20", "🟡", "above average"), ("21.9", "🟡", "above average"),
            ("22.0", "🟢", "excellent"), ("23.9", "🟢", "excellent"),
            ("24", "🔵", "superior"), ("25.9", "🔵", "superior"),
            ("26", "🟣", "very high"), ("29", "🟣", "very high"),
        )
        for value, emoji, label in cases:
            with self.subTest(value=value):
                status = guide_status("Vitals & Functional Health", "FFMI", value)
                self.assertEqual(status[1], emoji)
                self.assertEqual(status[2], f"FFMI physique comparison: {label}")

    def test_current_monthly_values_use_the_selected_comparison(self):
        for value, emoji in (("22.0", "🟢"), ("21.4", "🟡"),
                             ("21.9", "🟡"), ("22.1", "🟢")):
            with self.subTest(value=value):
                self.assertEqual(targets.status("FFMI", value)[1], emoji)
        self.assertEqual(vitals_trend(["22.0", "21.4"], "FFMI"), "🟢")

    def test_trend_approaches_superior_band_without_rewarding_unlimited_increases(self):
        for values, expected in ((["22", "21.4"], "🟢"),
                                 (["21.4", "22"], "🟡"),
                                 (["24", "23.5"], "🟢"),
                                 (["23.5", "24"], "🟡"),
                                 (["26", "24"], "⚪"),
                                 (["24", "29"], "⚪"),
                                 (["22", "22"], "⚪")):
            with self.subTest(values=values):
                self.assertEqual(vitals_trend(values, "FFMI"), expected)

    def test_small_changes_remain_neutral_including_across_a_band_boundary(self):
        for current, previous in (("22", "21.95"), ("23.05", "23")):
            for values in ([current, previous], [previous, current]):
                with self.subTest(values=values):
                    self.assertEqual(vitals_trend(values, "FFMI"), "⚪")
        self.assertEqual(vitals_trend(["22.1", "22"], "FFMI"), "🟢")
        self.assertEqual(vitals_trend(["22", "22.1"], "FFMI"), "🟡")

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
