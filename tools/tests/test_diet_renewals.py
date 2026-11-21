import copy
import unittest

from tools.plan_diet_renewals import active_coverage


def model_with(streams):
    return {
        "active_streams": streams,
        "protocol_requirements": {
            "dinner_rotation": {
                "tempeh_g": 200, "tempeh_meals": 3, "egg_meals": 12,
                "nominal_medium_eggs_per_meal": 4, "fish_meals": 10,
            },
            "daily": {"nuts_g": 20},
            "not_supplied_by_active_renewals": [],
        },
    }


class MushroomCoverageTests(unittest.TestCase):
    def coverage(self, streams):
        return active_coverage(model_with(streams))["mushrooms"]

    def test_no_recurring_mushrooms_cannot_supply_choices_or_remainders(self):
        for streams in ([], [{"days": 28, "foods": {"tomato_g": 1000},
                              "first_order": {"first_only": {"oyster_raw_g": 200}}}]):
            with self.subTest(streams=streams):
                result = self.coverage(streams)
                self.assertEqual(result["full_75g_choices"], 0)
                self.assertEqual(result["separate_oyster_remainder_g"], 0)
                self.assertEqual(result["separate_shiitake_remainder_g"], 0)
                self.assertNotIn("required", result)
                self.assertEqual(result["required_kind_count"], 4)
                self.assertEqual(result["active_kind_count"], 0)

    def test_current_two_species_delivery_retains_four_separate_choices(self):
        streams = [{"days": 28, "foods": {"oyster_raw_g": 200, "shiitake_raw_g": 200}}]
        before = copy.deepcopy(streams)
        result = self.coverage(streams)
        self.assertEqual(result["full_75g_choices"], 4)
        self.assertEqual(result["separate_oyster_remainder_g"], 50)
        self.assertEqual(result["separate_shiitake_remainder_g"], 50)
        self.assertEqual(result["active_kind_count"], 2)
        self.assertEqual(streams, before)

    def test_removing_a_species_updates_choices_and_its_remainder(self):
        result = self.coverage([{"days": 28, "foods": {"oyster_raw_g": 200}}])
        self.assertEqual(result["full_75g_choices"], 2)
        self.assertEqual(result["separate_oyster_remainder_g"], 50)
        self.assertEqual(result["separate_shiitake_remainder_g"], 0)

    def test_quantities_keep_species_remainders_out_of_full_choices(self):
        result = self.coverage([{"days": 28, "foods": {"oyster_raw_g": 250, "shiitake_raw_g": 125}}])
        self.assertEqual(result["full_75g_choices"], 4)
        self.assertEqual(result["separate_oyster_remainder_g"], 25)
        self.assertEqual(result["separate_shiitake_remainder_g"], 50)

    def test_delivery_intervals_scale_long_run_choices_and_remainders(self):
        fortnightly = self.coverage([{"days": 14, "foods": {"oyster_raw_g": 200}}])
        self.assertEqual(fortnightly["full_75g_choices"], 4)
        self.assertEqual(fortnightly["separate_oyster_remainder_g"], 100)
        monthly = self.coverage([{"days": 30, "foods": {"oyster_raw_g": 200}}])
        self.assertAlmostEqual(monthly["full_75g_choices"], 2 * 28 / 30, places=6)
        self.assertAlmostEqual(monthly["separate_oyster_remainder_g"], 50 * 28 / 30, places=6)

    def test_separate_deliveries_do_not_assume_usable_remainder_carryover(self):
        result = self.coverage([
            {"days": 28, "foods": {"oyster_raw_g": 50}},
            {"days": 28, "foods": {"oyster_raw_g": 25}},
        ])
        self.assertEqual(result["full_75g_choices"], 0)
        self.assertEqual(result["separate_oyster_remainder_g"], 75)


if __name__ == "__main__":
    unittest.main()
