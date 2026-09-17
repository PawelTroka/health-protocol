"""Laboratory grouping checks with synthetic observations only."""

from collections import Counter
import unittest

from tools.health_sync.lab_layout import lab_groups


def row(name, september="-", july="1", march="-", january="-"):
    return (name, september, july, march, january, "unit", "reference")


class LabLayoutTests(unittest.TestCase):
    def test_empty_input_has_no_empty_table(self):
        for category in ("Cardiac Health & Coagulation", "Hormonal Panel", "Future Panel"):
            with self.subTest(category=category):
                self.assertEqual(lab_groups(category, []), [])

    def test_unrecognized_panel_remains_one_untitled_table(self):
        rows = [row("Known"), row("New")]
        self.assertEqual(lab_groups("Future Panel", rows), [{"title": None, "rows": rows}])

    def test_requested_followups_are_separate_from_main_panel(self):
        cases = (
            ("Cardiac Health & Coagulation", "Cholesterol LDL", ["Creatine Kinase (CK)"]),
            ("Metabolic Health", "Glucose", ["LDH", "Uric Acid"]),
            ("Micronutrients", "Vitamin D3", ["Selenium"]),
            ("Immunology & Inflammation", "CRP (hs)", ["CRP (Conventional)", "Anti-TPO", "IgA (Serum)"]),
            ("Hormonal Panel", "Testosterone (Total)", ["TSH", "Free T3 (FT3)", "Free T4 (FT4)"]),
        )
        for category, main_name, followup_names in cases:
            with self.subTest(category=category):
                future = row("Future Marker")
                main = row(main_name)
                followups = [row(name, september="pending") for name in followup_names]
                rows = [followups[0], main, future, *followups[1:]]
                groups = lab_groups(category, rows)
                self.assertEqual(len(groups), 2)
                self.assertEqual(groups[0]["rows"], [main, future])
                self.assertEqual(groups[1]["rows"], followups)
                self.assertTrue(groups[1]["title"])

    def test_partition_preserves_objects_duplicates_values_and_order(self):
        first = row("Uric Acid", september="3.0", july="3.8")
        second = row("Uric Acid", september="3.1", july="3.9")
        rows = [first, row("Glucose"), row("LDH", september="130"), second, first, row("Future Marker")]
        before = list(rows)
        groups = lab_groups("Metabolic Health", rows)
        flattened = [item for group in groups for item in group["rows"]]
        self.assertEqual(rows, before)
        self.assertEqual(Counter(map(id, flattened)), Counter(map(id, rows)))
        for group in groups:
            included_ids = {id(item) for item in group["rows"]}
            self.assertEqual(group["rows"], [item for item in rows if id(item) in included_ids])

    def test_date_coverage_is_separate_and_pending_stays_visible(self):
        rows = [
            row("Vitamin D3", july="46", march="26", january="53"),
            row("Selenium", september="pending", july="108.75"),
            row("Vitamin C", july="5.0", march="4.6"),
        ]
        main, selenium = lab_groups("Micronutrients", rows)
        dates = ("2026-09", "2026-07", "2026-03", "2026-01")

        def populated_dates(group):
            return [month for index, month in enumerate(dates, start=1)
                    if any(item[index] != "-" for item in group["rows"])]

        self.assertEqual(populated_dates(main), ["2026-07", "2026-03", "2026-01"])
        self.assertEqual(populated_dates(selenium), ["2026-09", "2026-07"])
        self.assertEqual(selenium["rows"][0][1], "pending")

    def test_single_remaining_group_has_no_empty_companion(self):
        for rows in ([row("LDH")], [row("Glucose")]):
            with self.subTest(rows=rows):
                groups = lab_groups("Metabolic Health", rows)
                self.assertEqual(len(groups), 1)
                self.assertEqual(groups[0]["rows"], rows)


if __name__ == "__main__":
    unittest.main()
