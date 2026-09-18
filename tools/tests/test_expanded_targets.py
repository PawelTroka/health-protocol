"""Meaningful directions for newly exposed device measurements."""

import unittest

from tools.health_sync.vitals_targets import status, trend


class ExpandedTargetTests(unittest.TestCase):
    def test_night_frequency_uses_percentage_not_count_denominator(self):
        marker = "Short Sleep Nights (Oura)"
        self.assertEqual(status(marker, "0.0 (0/16)")[1], "🟢")
        self.assertEqual(status(marker, "25.0 (4/16)")[1], "🟡")
        self.assertEqual(trend(["25.0 (4/16)", "29.0 (9/31)"], marker), "🟢")
        self.assertEqual(trend(["29.0 (9/31)", "25.0 (4/16)"], marker), "🟡")

    def test_clock_time_has_no_universal_direction_but_lower_variability_does(self):
        self.assertIsNone(status("Bedtime (Oura)", "01:30"))
        self.assertEqual(trend(["01:30", "23:30"], "Bedtime (Oura)"), "-")
        self.assertEqual(trend(["65", "75"], "Sleep Midpoint Variability (Oura)"), "🟢")
        self.assertEqual(trend(["72", "75"], "Sleep Midpoint Variability (Oura)"), "⚪")

    def test_coaching_recovery_and_signed_temperature_keep_correct_direction(self):
        self.assertEqual(status("Sleep Coach Shortfall (Garmin)", "0")[1], "🟢")
        self.assertEqual(trend(["0.5", "1.5"], "Sleep Coach Shortfall (Garmin)"), "🟢")
        self.assertEqual(trend(["70", "60"], "Body Battery at Wakeup (Garmin)"), "🟢")
        self.assertEqual(trend(["20", "30"], "Average Sleeping Stress (Garmin)"), "🟢")
        self.assertEqual(trend(["-0.1", "-0.7"], "Skin Temperature Deviation (Garmin)"), "🟢")
        self.assertEqual(trend(["0.7", "0.1"], "Skin Temperature Deviation (Garmin)"), "🟡")

    def test_training_changes_do_not_assume_every_harder_workout_is_better(self):
        self.assertEqual(trend(["4", "2"], "Aerobic Training Effect per Workout (Garmin)"), "⚪")
        self.assertEqual(status("Aerobic Training Effect per Workout (Garmin)", "5")[1], "🟠")
        self.assertEqual(trend(["1.3", "1.0"], "Acute/Chronic Training Load Ratio (Garmin)"), "⚪")
        self.assertIsNone(status("Acute/Chronic Training Load Ratio (Garmin)", "1.5"))


if __name__ == "__main__":
    unittest.main()
