"""Stock forecasts must follow recorded model inputs, not historical literals."""

from copy import deepcopy
import unittest

from tools.plan_diet_renewals import forecast_reviews


class DietStockForecastTests(unittest.TestCase):
    def setUp(self):
        self.model = {
            "as_of": "2026-09-16",
            "opening_stock": {
                "reported_on": "2026-09-14",
                "estimated_g": {
                    "walnuts": 120, "macadamias": 80,
                    "morning_flax_chia_total": 140, "pumpkin": 70, "matcha": 50,
                },
                "phileos_remaining_ml_estimate": 100,
                "reported_counts": {"soy_milk_packs": 1},
            },
            "protocol_requirements": {"daily": {
                "nuts_g": 10, "morning_seeds_g": 7, "dinner_seeds_g": 5,
                "matcha_g": 4, "phileos_g": 9.15, "milk_ml": 250,
                "oats_dry_g": 25,
            }},
        }

    def forecasts(self, model=None):
        return {row["food"]: row for row in forecast_reviews(
            self.model if model is None else model)["reviews"]}

    def test_opening_balances_and_daily_use_come_from_the_model(self):
        rows = self.forecasts()
        expected = {
            "combined Nuts": (200, 180, "2026-10-04"),
            "combined Flax/Chia": (140, 126, "2026-10-04"),
            "Pumpkin": (70, 60, "2026-09-28"),
            "Matcha": (50, 42, "2026-09-26"),
            "Phileos": (91.5, 73.2, "2026-09-24"),
            "Soy Milk if chosen every day": (1000, 500, "2026-09-18"),
        }
        self.assertEqual(set(rows), set(expected))
        for food, (initial, remaining, first_gap) in expected.items():
            with self.subTest(food=food):
                self.assertEqual(rows[food]["stock_reference_quantity"], initial)
                self.assertEqual(rows[food]["forecast_remaining_before_today_use"], remaining)
                self.assertEqual(rows[food]["first_forecast_not_fully_supplied_day"], first_gap)

    def test_explicit_zero_is_not_replaced_with_a_historical_balance(self):
        self.model["opening_stock"]["estimated_g"].update(
            walnuts=0, macadamias=0, matcha=0)
        for food in ("combined Nuts", "Matcha"):
            with self.subTest(food=food):
                row = self.forecasts()[food]
                self.assertEqual(row["stock_reference_quantity"], 0)
                self.assertEqual(row["first_forecast_not_fully_supplied_day"], "2026-09-14")

    def test_missing_or_unknown_opening_stock_does_not_invent_a_forecast(self):
        self.model["opening_stock"] = {"reported_on": "2026-09-14"}
        self.assertEqual(self.forecasts(), {})
        self.model["opening_stock"]["estimated_g"] = {"matcha": None}
        self.assertEqual(self.forecasts(), {})

    def test_partial_nut_balance_is_unknown_until_a_combined_observation(self):
        del self.model["opening_stock"]["estimated_g"]["macadamias"]
        self.assertNotIn("combined Nuts", self.forecasts())
        self.model["stock_observations"] = [{
            "reported_on": "2026-09-15", "group": "combined Nuts",
            "quantity": 30, "unit": "g",
        }]
        self.assertEqual(self.forecasts()["combined Nuts"]["stock_reference_quantity"], 30)

    def test_latest_exact_unit_observation_overrides_opening_stock(self):
        self.model["stock_observations"] = [
            {"reported_on": "2026-09-15", "group": "Matcha", "quantity": 12,
             "unit": "g", "source": "Weighed balance"},
            {"reported_on": "2026-09-14", "group": "Matcha", "quantity": 99, "unit": "g"},
            {"reported_on": "2026-09-17", "group": "Matcha", "quantity": 100, "unit": "g"},
            {"reported_on": "2026-09-16", "group": "Matcha", "quantity": 9, "unit": "packs"},
        ]
        row = self.forecasts()["Matcha"]
        self.assertEqual(row["stock_reference_quantity"], 12)
        self.assertEqual(row["forecast_remaining_before_today_use"], 8)
        self.assertEqual(row["first_forecast_not_fully_supplied_day"], "2026-09-18")
        self.assertEqual(row["stock_source"], "Weighed balance")

    def test_unit_conversion_assumptions_only_apply_to_opening_estimates(self):
        rows = self.forecasts()
        self.assertIn("0.915g/ml", rows["Phileos"]["stock_conversion_assumption"])
        self.assertIn("1L", rows["Soy Milk if chosen every day"]["stock_conversion_assumption"])
        self.model["stock_observations"] = [
            {"reported_on": "2026-09-16", "group": "Phileos", "quantity": 20, "unit": "g"},
            {"reported_on": "2026-09-16", "group": "Soy Milk if chosen every day",
             "quantity": 100, "unit": "ml"},
        ]
        rows = self.forecasts()
        self.assertEqual(rows["Phileos"]["stock_reference_quantity"], 20)
        self.assertEqual(rows["Soy Milk if chosen every day"]["stock_reference_quantity"], 100)
        for food in ("Phileos", "Soy Milk if chosen every day"):
            self.assertNotIn("stock_conversion_assumption", rows[food])

    def test_decimal_portions_do_not_lose_a_complete_serving(self):
        self.model["opening_stock"]["estimated_g"]["matcha"] = 0.3
        self.model["protocol_requirements"]["daily"]["matcha_g"] = 0.1
        self.assertEqual(self.forecasts()["Matcha"]["first_forecast_not_fully_supplied_day"],
                         "2026-09-17")

    def test_later_receipts_still_qualify_without_crediting_stock(self):
        self.model["receipt_observations"] = [{
            "reported_on": "2026-09-16", "delivered_at": "2026-09-15T15:00:00+02:00",
            "received": True, "order_id": 42, "affected_groups": ["Matcha"],
        }]
        row = self.forecasts()["Matcha"]
        self.assertEqual(row["forecast_remaining_before_today_use"], 42)
        self.assertFalse(row["current_shortage_inference_supported"])
        self.assertEqual(row["subsequent_receipts_excluded"][0]["order_id"], 42)

    def test_invalid_known_stock_fails_clearly(self):
        for value in (-1, True, "NaN", "Infinity", "unknown"):
            with self.subTest(value=value):
                model = deepcopy(self.model)
                model["opening_stock"]["estimated_g"]["matcha"] = value
                with self.assertRaisesRegex(ValueError, "opening_stock.estimated_g.matcha"):
                    self.forecasts(model)

    def test_missing_or_nonpositive_daily_requirement_has_no_invented_date(self):
        for value in (None, 0, -1, True, "NaN", "Infinity"):
            with self.subTest(value=value):
                model = deepcopy(self.model)
                model["protocol_requirements"]["daily"]["matcha_g"] = value
                with self.assertRaisesRegex(ValueError, "protocol_requirements.daily.matcha_g"):
                    self.forecasts(model)

    def test_future_opening_stock_cannot_be_counted_as_available(self):
        self.model["as_of"] = "2026-09-13"
        with self.assertRaisesRegex(ValueError, "as_of must not precede"):
            self.forecasts()

    def test_forecast_does_not_mutate_the_input_model(self):
        original = deepcopy(self.model)
        self.forecasts()
        self.assertEqual(self.model, original)


if __name__ == "__main__":
    unittest.main()
