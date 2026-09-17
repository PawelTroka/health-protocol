"""Limit comparisons must preserve censoring and strict boundary semantics."""

import unittest

from tools.health_sync.result_bounds import (
    bound_within_reference, bounded_comparison, is_bounded,
)


class ResultBoundsTests(unittest.TestCase):
    def test_identifies_only_valid_numeric_limits(self):
        for value in ("<30.0", " <= 30 ", ">60", ">=200", "≤ .5", "≥ -2.5", "< 1e-3"):
            with self.subTest(value=value):
                self.assertTrue(is_bounded(value))
        for value in ("30", "pending", "-", "<unknown", "<30 extra", "<NaN", "<Infinity", None):
            with self.subTest(value=value):
                self.assertFalse(is_bounded(value))

    def test_matching_or_stricter_bounds_are_within_reference(self):
        for value, reference in (
            ("< 30.0", "<30"), ("< 10", "<14"), ("≤30", "<=30"),
            ("<30", "≤30"), (">60", ">60"), (">60", ">=60"),
            (">=200", ">=200"), (">201", ">200"),
            ("<0.14", "<0.550: negative; >=0.550: positive"),
            (">60", ">60; target 90 - 120"),
        ):
            with self.subTest(value=value, reference=reference):
                self.assertIs(bound_within_reference(value, reference), True)

    def test_unknown_or_overlapping_intervals_do_not_establish_normality(self):
        for value, reference in (
            ("<30", "<20"), ("≤30", "<30"), (">=60", ">60"),
            (">60", "90 - 120"), ("<5", "0 - 10"),
            (">=10", "0 - 10"), ("pending", "<30"),
            ("<5", "not detected"), ("<5", "10 - 0"),
        ):
            with self.subTest(value=value, reference=reference):
                self.assertIsNone(bound_within_reference(value, reference))

    def test_disjoint_intervals_are_outside_reference(self):
        for value, reference in (
            (">30", "<30"), (">=30", "<30"), ("<30", ">=30"),
            (">30", "0 - 30"), ("<0", "0 - 30"),
            ("30", "<30"), ("-2", "0 - 30"),
        ):
            with self.subTest(value=value, reference=reference):
                self.assertIs(bound_within_reference(value, reference), False)

    def test_scalars_and_signed_reference_ranges(self):
        for value, reference in (("600", ">=200"), ("200", ">=200"), ("0", "0–30"), ("-2", "-3 - -1")):
            with self.subTest(value=value, reference=reference):
                self.assertIs(bound_within_reference(value, reference), True)

    def test_same_bound_means_equivalent_reported_limit(self):
        for current, previous in (("<1.5", " < 1.50 "), ("≤30", "<=30.0"), ("≥200", ">=2e2")):
            with self.subTest(current=current, previous=previous):
                self.assertEqual(bounded_comparison(current, previous), "same_bound")
        self.assertIsNone(bounded_comparison("<30", "<=30"))
        self.assertIsNone(bounded_comparison("30", "30"))

    def test_calprotectin_change_is_established_but_egfr_change_is_unknown(self):
        self.assertEqual(bounded_comparison("<5.0", "291.70"), "lower")
        self.assertEqual(bounded_comparison("291.70", "<5.0"), "higher")
        self.assertIsNone(bounded_comparison("101.5", ">60"))
        self.assertIsNone(bounded_comparison(">60", "101.5"))
        self.assertIsNone(bounded_comparison("<10", "<30"))

    def test_ordering_respects_open_and_closed_touching_endpoints(self):
        for current, previous in (("<5", "5"), ("<5", ">=5"), ("<=5", ">5"), ("5", ">5")):
            with self.subTest(current=current, previous=previous):
                self.assertEqual(bounded_comparison(current, previous), "lower")
                self.assertEqual(bounded_comparison(previous, current), "higher")
        for current, previous in (("<=5", "5"), ("<=5", ">=5"), ("5", ">=5"), ("pending", "<5")):
            with self.subTest(current=current, previous=previous):
                self.assertIsNone(bounded_comparison(current, previous))


if __name__ == "__main__":
    unittest.main()
