"""Synthetic target-policy regressions; no private data, network or report writes."""

from copy import deepcopy
from decimal import Decimal
import unittest

from tools.health_sync import vitals_targets as targets
from tools.health_sync.garmin import GARMIN_METRICS
from tools.health_sync.oura import OURA_METRICS
from tools.health_sync.withings import WITHINGS_METRICS


def context(provider, values, days=("2026-08-01", "2026-08-03")):
    return {
        marker: {
            "value": str(value), "provider": provider,
            "observed_days": list(days), "first_day": days[0],
            "last_day": days[-1], "n_days": len(days),
        }
        for marker, value in values.items()
    }


class TargetDirectionTests(unittest.TestCase):
    def test_same_band_provider_score_changes_retain_their_direction(self):
        for marker, current, previous in (
            ("Readiness Score (Oura)", "83.1", "82.8"),
            ("Activity Recovery Time Contributor Score (Oura)", "97.2", "86.7"),
            ("Morning Training Readiness (Garmin)", "64.5", "62.0"),
            ("Resilience Sleep Recovery Contributor Score (Oura)", "66.4", "65.6"),
        ):
            with self.subTest(marker=marker):
                self.assertEqual(targets.trend([current, previous], marker), "🟢")
                self.assertEqual(targets.trend([previous, current], marker), "🟡")
                self.assertEqual(targets.trend([current, current], marker), "⚪")

    def test_target_plateaus_do_not_reward_arbitrary_midpoints(self):
        for marker, values in (
            ("Body Fat", ["12", "15"]),
            ("Bone", ["4.2", "4.1"]),
            ("Sleep Efficiency", ["95", "90"]),
            ("Steps (Garmin)", ["11000", "8500"]),
            ("Sleep Duration", ["8", "7.2"]),
        ):
            with self.subTest(marker=marker):
                self.assertEqual(targets.trend(values, marker), "⚪")

    def test_overshooting_a_target_can_worsen_despite_numerical_decrease(self):
        self.assertEqual(targets.trend(["5", "22"], "Sleep Latency"), "🟡")
        self.assertEqual(targets.trend(["7", "16"], "Body Fat"), "🟡")
        self.assertEqual(targets.trend(["16", "22"], "Sleep Latency"), "🟢")
        self.assertEqual(targets.trend(["16", "22"], "Body Fat"), "🟢")

    def test_temperature_deviation_uses_distance_from_zero_in_both_directions(self):
        marker = "Temperature Deviation (Oura)"
        self.assertEqual(targets.trend(["-0.05", "-0.20"], marker), "🟢")
        self.assertEqual(targets.trend(["-0.20", "0.10"], marker), "🟡")
        self.assertEqual(targets.trend(["0.10", "-0.10"], marker), "⚪")
        self.assertIsNone(targets.status(marker, "0.05"))

    def test_hrv_recovery_direction_does_not_create_a_universal_ms_grade(self):
        self.assertEqual(targets.trend(["25.0", "25.8"], "Average HRV (Sleep)"), "🟡")
        self.assertEqual(targets.trend(["44.6", "41.3"], "HRV at Sleep End (Withings)"), "🟢")
        self.assertIsNone(targets.status("Average HRV (Sleep)", "25.0"))
        self.assertIsNone(targets.status("Average HRV (Sleep)", "90"))
        self.assertEqual(targets.trend(["90", "40"], "7-day Average HRV (Garmin)"), "⚪")
        self.assertEqual(targets.trend(["90", "40"], "Max HRV"), "⚪")

    def test_uninterpretable_latest_data_never_revive_an_older_trend(self):
        for latest in ("pending", "unknown", "<70", "Normal: 3", "101"):
            with self.subTest(latest=latest):
                self.assertEqual(targets.trend([latest, "80", "70"], "Sleep Score"), "-")
        self.assertEqual(targets.trend(["-", "80", "-", "70"], "Sleep Score"), "🟢")


class ProviderBandTests(unittest.TestCase):
    def test_providers_keep_distinct_sleep_score_scales(self):
        for marker, value, emoji in (
            ("Sleep Score", "85", "🔵"),
            ("Sleep Score (Garmin)", "85", "🟢"),
            ("Sleep Score (Garmin)", "90", "🔵"),
            ("Sleep Score (Garmin)", "79.9", "🟡"),
            ("Sleep Score (Withings)", "85", "🟢"),
            ("Sleep Score (Withings)", "60", "🟡"),
        ):
            with self.subTest(marker=marker, value=value):
                self.assertEqual(targets.status(marker, value)[1], emoji)
        self.assertIsNone(targets.status("Sleep Score (Withings)", "75"))
        for marker in ("Sleep Score", "Sleep Score (Garmin)", "Sleep Score (Withings)"):
            self.assertIsNone(targets.status(marker, "101"))

    def test_stress_and_training_readiness_are_not_the_same_direction(self):
        self.assertEqual(targets.status("Average Stress (Garmin)", "28.4")[1], "🟢")
        self.assertEqual(targets.status("Average Stress (Garmin)", "76")[1], "🟠")
        self.assertEqual(targets.status("Morning Training Readiness (Garmin)", "64.5")[1], "🟢")
        self.assertEqual(targets.status("Morning Training Readiness (Garmin)", "24")[1], "🔴")
        self.assertEqual(targets.trend(["30", "40"], "Average Stress (Garmin)"), "🟢")
        self.assertEqual(targets.trend(["30", "40"], "Morning Training Readiness (Garmin)"), "🟡")

    def test_nerve_api_means_are_comparisons_not_confirmed_monthly_grades(self):
        self.assertEqual(targets.status("Nerve Health Score", "47")[1], "🟠")
        self.assertEqual(targets.status("Nerve Health Score Feet (Withings)", "47")[1], "🟡")
        self.assertEqual(targets.status("Nerve Health Score Feet (Withings)", "52")[1], "🟢")
        for marker in ("Nerve Health Score", "Nerve Health Score Feet (Withings)"):
            self.assertIsNone(targets.status(marker, "50"))
            self.assertIsNone(targets.status(marker, "pending"))

    def test_recovery_flows_and_algorithm_deltas_are_not_quality_scores(self):
        for marker in ("Body Battery Charged (Garmin)", "Body Battery Drained (Garmin)",
                       "Primary Sleep Score Change (Oura)",
                       "Resilience Stress Contributor Score (Oura)"):
            with self.subTest(marker=marker):
                self.assertIsNone(targets.status(marker, "40"))
                self.assertEqual(targets.trend(["40", "30"], marker), "⚪")


class MatchedObservationTests(unittest.TestCase):
    def test_equal_counts_and_endpoints_do_not_prove_equal_gapped_days(self):
        first = context("oura", {"REM Sleep": 2}, ("2026-08-01", "2026-08-02", "2026-08-04"))["REM Sleep"]
        other = context("oura", {"Sleep Duration": 8}, ("2026-08-01", "2026-08-03", "2026-08-04"))["Sleep Duration"]
        self.assertFalse(targets.matched_days([first, other]))
        del first["observed_days"], other["observed_days"]
        self.assertFalse(targets.matched_days([first, other]))

    def test_complete_legacy_intervals_can_prove_matching_days(self):
        ctx = context("oura", {"REM Sleep": 2, "Sleep Duration": 8},
                      ("2026-08-01", "2026-08-02"))
        for entry in ctx.values():
            del entry["observed_days"]
        self.assertTrue(targets.matched_days(list(ctx.values())))
        self.assertEqual(targets.status("REM Sleep", "2", ctx)[1], "🟢")

    def test_stage_hours_are_compared_as_percentages_of_their_own_provider(self):
        for provider, marker, total in (
            ("oura", "REM Sleep", "Sleep Duration"),
            ("withings", "REM Sleep (Withings)", "Sleep Duration (Withings)"),
            ("garmin", "REM Sleep (Garmin)", "Sleep Duration (Garmin)"),
        ):
            with self.subTest(provider=provider):
                ctx = context(provider, {marker: 2, total: 8})
                self.assertEqual(targets.evaluated_value(marker, "2", ctx), Decimal("25"))
                self.assertEqual(targets.status(marker, "2", ctx)[1], "🟢")
                ctx[total]["provider"] = "other"
                self.assertIsNone(targets.status(marker, "2", ctx))

    def test_stage_percentage_can_worsen_while_stage_hours_decrease(self):
        current = context("oura", {"REM Sleep": 1.5, "Sleep Duration": 5})
        previous = context("oura", {"REM Sleep": 2, "Sleep Duration": 8})
        self.assertEqual(targets.trend(["1.5", "2"], "REM Sleep", [current, previous]), "🟡")

    def test_ratio_requires_matched_coverage_and_a_physical_denominator(self):
        for stage, duration in (("2", "0"), ("2", "-8"), ("9", "8"), ("2", "pending")):
            with self.subTest(stage=stage, duration=duration):
                ctx = context("oura", {"REM Sleep": stage, "Sleep Duration": duration})
                self.assertIsNone(targets.status("REM Sleep", stage, ctx))
        ctx = context("oura", {"REM Sleep": 2, "Sleep Duration": 8})
        ctx["Sleep Duration"]["observed_days"] = ["2026-08-02", "2026-08-04"]
        self.assertIsNone(targets.status("REM Sleep", "2", ctx))
        self.assertIsNone(targets.status("REM Sleep", "2"))

    def test_component_mass_compares_with_paired_body_mass_and_does_not_mutate_data(self):
        ctx = context("withings", {"Fat Mass (Withings)": 10, "Body Mass": 80})
        original = deepcopy(ctx)
        self.assertEqual(targets.evaluated_value("Fat Mass (Withings)", "10", ctx), Decimal("12.5"))
        self.assertEqual(targets.status("Fat Mass (Withings)", "10", ctx)[1], "🔵")
        self.assertEqual(ctx, original)
        ctx["Body Mass"]["observed_days"] = ["2026-08-02", "2026-08-03"]
        self.assertIsNone(targets.status("Fat Mass (Withings)", "10", ctx))


class CombinedActivityTests(unittest.TestCase):
    def test_hours_and_minutes_produce_identical_moderate_equivalent_doses(self):
        for provider, moderate, vigorous, moderate_value, vigorous_value in (
            ("oura", "Medium Activity Time (Oura)", "High Activity Time (Oura)", "0.1", "0.2"),
            ("withings", "Moderate Activity Duration (Withings)", "Intense Activity Duration (Withings)", "6", "12"),
            ("garmin", "Moderate Intensity Minutes (Garmin)", "Vigorous Intensity Minutes (Garmin)", "6", "12"),
        ):
            ctx = context(provider, {moderate: moderate_value, vigorous: vigorous_value})
            for marker, value in ((moderate, moderate_value), (vigorous, vigorous_value)):
                with self.subTest(marker=marker):
                    self.assertEqual(targets.evaluated_value(marker, value, ctx), Decimal("30"))
                    self.assertEqual(targets.status(marker, value, ctx)[1], "🟢")

    def test_vigorous_alternative_does_not_penalize_zero_moderate_minutes(self):
        moderate = "Moderate Intensity Minutes (Garmin)"
        vigorous = "Vigorous Intensity Minutes (Garmin)"
        ctx = context("garmin", {moderate: 0, vigorous: 25})
        self.assertEqual(targets.status(moderate, "0", ctx)[1], "🔵")
        self.assertEqual(targets.status(vigorous, "25", ctx)[1], "🔵")
        # A missing component differs from an observed zero.
        del ctx[moderate]
        self.assertIsNone(targets.status(vigorous, "25", ctx))

    def test_intensity_components_require_the_same_observed_days(self):
        moderate = "Moderate Intensity Minutes (Garmin)"
        vigorous = "Vigorous Intensity Minutes (Garmin)"
        ctx = context("garmin", {moderate: 10, vigorous: 20})
        ctx[vigorous]["observed_days"] = ["2026-08-02", "2026-08-04"]
        self.assertIsNone(targets.status(moderate, "10", ctx))

    def test_active_duration_cannot_borrow_unmatched_component_days(self):
        marker = "Active Duration (Withings)"
        ctx = context("withings", {
            marker: 25, "Moderate Activity Duration (Withings)": 0,
            "Intense Activity Duration (Withings)": 25,
        })
        self.assertEqual(targets.status(marker, "25", ctx)[1], "🔵")
        ctx[marker]["observed_days"] = ["2026-08-02", "2026-08-04"]
        self.assertIsNone(targets.status(marker, "25", ctx))

    def test_met_minutes_are_added_without_a_second_vigorous_multiplier(self):
        moderate = "Medium Activity MET Minutes (Oura)"
        vigorous = "High Activity MET Minutes (Oura)"
        ctx = context("oura", {moderate: 100, vigorous: 100})
        self.assertEqual(targets.evaluated_value(moderate, "100", ctx), Decimal("200"))
        self.assertEqual(targets.status(moderate, "100", ctx)[1], "🟢")
        self.assertIsNone(targets.rule_for("Low Activity MET Minutes (Oura)"))


class RegistryIdentityTests(unittest.TestCase):
    def test_rule_names_match_the_provider_registry_or_a_specific_manual_row(self):
        registry = set(OURA_METRICS) | set(WITHINGS_METRICS) | set(GARMIN_METRICS)
        manual = {
            "Sleeping Heart Rate", "Resting Heart Rate", "ECG Heart Rate",
            "Cardiovascular Age Difference (Oura)", "Nerve Health Score", "Max HRV", "VO2max",
        }
        self.assertEqual(set(targets.TARGETS) - registry - manual, set())

    def test_sampled_overnight_and_resting_hr_rules_use_exact_registry_names(self):
        for marker in ("Sampled HR During Primary Sleep (Oura)",
                       "Sampled Sleeping HR (Oura)", "Sampled Rest HR (Oura)"):
            with self.subTest(marker=marker):
                self.assertIn(marker, OURA_METRICS)
                self.assertIsNotNone(targets.rule_for(marker))


class ClassificationAndCoverageTests(unittest.TestCase):
    def test_categorical_trends_use_proportions_not_partial_month_counts(self):
        marker = "Resilience Level (Oura)"
        self.assertEqual(targets.classification_trend(["Strong: 5", "Strong: 30"], marker), "⚪")
        self.assertEqual(targets.classification_trend(["Solid: 1; Strong: 15", "Solid: 16; Strong: 15"], marker), "🟢")

    def test_mixed_or_unknown_categorical_changes_do_not_invent_a_rank(self):
        marker = "Stress Day Summary (Oura)"
        self.assertEqual(targets.classification_trend(["Normal: 16", "Normal: 27; Restored: 3; Stressful: 1"], marker), "⚪")
        self.assertEqual(targets.classification_trend(["Device code 2: 16", "Normal: 31"], marker), "-")

    def test_categorical_status_colors_labels_without_changing_counts(self):
        result = targets.classification_parts("ECG AF Classification (Withings)", "Negative: 5; Unknown: 1")
        self.assertEqual(result[0][0], "Negative: 5")
        self.assertEqual(result[0][1][1], "🔵")
        self.assertEqual(result[1], ("Unknown: 1", None))

    def test_matching_days_with_different_record_counts_do_not_prove_pairing(self):
        ctx = context("withings", {"Body Mass": 80, "Fat Mass (Withings)": 12})
        ctx["Body Mass"]["n_records"] = 4
        ctx["Fat Mass (Withings)"]["n_records"] = 2
        self.assertIsNone(targets.status("Fat Mass (Withings)", "12", ctx))


if __name__ == "__main__":
    unittest.main()
