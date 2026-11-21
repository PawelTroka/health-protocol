"""Historical Egg arithmetic must not be presented as an active renewal plan."""

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import unittest

from tools.plan_diet_renewals import active_coverage, markdown, practical_alternatives, rate


class RetiredEggCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        model_path = Path(__file__).resolve().parents[2] / "diet" / "DIET_RENEWAL_MODEL.json"
        cls.model = json.loads(model_path.read_text(encoding="utf-8"))
        cls.alternatives = practical_alternatives(cls.model)

    def test_retired_stream_cannot_establish_current_egg_coverage(self):
        model = {
            "new_verified_oat500": {},
            "active_streams": [{"subscription": 399, "days": 30,
                                "foods": {"eggs_count": 10}}],
        }
        historical = practical_alternatives(model)["monthly_egg_clusters"]
        active_eggs = [
            {"quantity": item["foods"]["eggs_count"], "days": item["days"]}
            for item in model["active_streams"]
            if item["foods"].get("eggs_count", 0) > 0
        ]
        # The historical balance includes361's former10/14day Egg stream.
        # This example supplies only399's10/30day rate, as in the dated model.
        self.assertEqual(rate(active_eggs) * 28, Fraction(28, 3))
        self.assertEqual(rate(historical["streams"]) * 28, 48)
        self.assertEqual((rate(active_eggs) + rate(historical["streams"][1:])) * 28,
                         Fraction(112, 3))
        self.assertTrue(historical.get("retired"))
        self.assertIs(historical.get("accepted_for_activation"), False)

    def test_markdown_keeps_egg_clusters_in_historical_comparisons(self):
        result = deepcopy(self.model["derived_analysis"])
        result["practical_additional_alternatives"] = self.alternatives
        result["active_coverage_per_28_days"] = active_coverage(self.model)
        rendered = markdown(result)
        current, historical = rendered.split(
            "Historical arithmetic comparisons (not activation instructions):", 1)
        self.assertNotIn("Eggs10/14days + three10/30day cores", current)
        self.assertIn("Eggs10/14days + three10/30day cores", historical)
        self.assertIn(self.alternatives["monthly_egg_clusters"]["status"], historical)
        self.assertIn("Active Eggs", current)

    def test_cached_scenario_matches_generator_without_changing_source_model(self):
        original = deepcopy(self.model)
        generated = practical_alternatives(self.model)["monthly_egg_clusters"]
        self.assertEqual(self.model, original)
        self.assertEqual(
            self.model["derived_analysis"]["practical_additional_alternatives"]["monthly_egg_clusters"],
            generated,
        )


if __name__ == "__main__":
    unittest.main()
