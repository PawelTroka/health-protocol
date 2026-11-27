"""Laboratory grouping checks with synthetic observations only."""

from collections import Counter
import unittest

from tools.health_sync.lab_layout import lab_groups


def row(name, september="-", july="1", march="-", january="-"):
    return (name, september, july, march, january, "unit", "reference")


class LabLayoutTests(unittest.TestCase):
    def test_empty_input_has_no_empty_table(self):
        for category in ("Metabolic Health", "Cardiac Health & Coagulation", "Micronutrients",
                         "Infectious Diseases", "Hormonal Panel", "Future Panel"):
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
            ("Infectious Diseases", "HIV", ["SARS-CoV-2 RT-PCR"]),
            ("Urine Chemistry", "Urine Protein", ["Urine Creatinine", "Urine Cystine/Creatinine"]),
            ("Immunology & Inflammation", "CRP (hs)", ["CRP (Conventional)", "Anti-TPO", "IgA (Serum)"]),
        )
        for category, main_name, followup_names in cases:
            with self.subTest(category=category):
                main = row(main_name)
                followups = [row(name, september="pending") for name in followup_names]
                rows = [followups[0], main, *followups[1:]]
                groups = lab_groups(category, rows)
                self.assertEqual(len(groups), 2)
                self.assertEqual(groups[0]["rows"], [main])
                self.assertEqual(groups[1]["rows"], followups)
                self.assertTrue(groups[1]["title"])

    def test_sparse_panels_keep_distinct_marker_families_and_unknown_rows_visible(self):
        cases = (
            ("Metabolic Health", ("Insulin", "ALT", "eGFR"), "Additional Metabolic Markers"),
            ("Cardiac Health & Coagulation", ("Cholesterol LDL", "Homocysteine", "INR"),
             "Additional Cardiac Markers"),
            ("Micronutrients", ("Vitamin D3", "Vitamin B12", "Ferritin", "Sodium", "Zinc"),
             "Additional Micronutrient Markers"),
        )
        for category, names, fallback_title in cases:
            with self.subTest(category=category):
                known = [row(name) for name in names]
                future = [row("Future Marker", september="pending"), row("Another Future Marker")]
                rows = [future[0], *reversed(known), future[1]]
                groups = lab_groups(category, rows)
                self.assertEqual(len(groups), len(names) + 1)
                self.assertTrue(all(group["title"] and group["rows"] for group in groups))
                self.assertEqual([group["rows"] for group in groups[:-1]], [[item] for item in known])
                self.assertEqual(groups[-1], {"title": fallback_title, "rows": future})
                self.assertEqual(lab_groups(category, future),
                                 [{"title": fallback_title, "rows": future}])

    def test_unpartitioned_panels_keep_unknown_markers_in_the_main_table(self):
        for category, marker in (("Infectious Diseases", "HIV"), ("Urine Chemistry", "Urine Protein")):
            with self.subTest(category=category):
                rows = [row(marker), row("Future Marker")]
                self.assertEqual(lab_groups(category, rows), [{"title": None, "rows": rows}])

    def test_hormonal_groups_preserve_rows_and_keep_unknown_markers_separate(self):
        rows = [row(name) for name in (
            "TSH", "Cortisol", "Testosterone (Total)", "Future Marker", "IGF-1",
            "SHBG", "DHEA-SO4", "Free T4 (FT4)", "Another Future Marker",
        )]
        groups = lab_groups("Hormonal Panel", rows)
        self.assertEqual([(group["title"], [item[0] for item in group["rows"]])
                          for group in groups], [
            ("Reproductive Hormones & Markers", ["Testosterone (Total)", "SHBG"]),
            ("Adrenal Hormones & Precursors", ["Cortisol", "DHEA-SO4"]),
            ("Growth Axis", ["IGF-1"]),
            ("Thyroid Function", ["TSH", "Free T4 (FT4)"]),
            ("Additional Hormonal Markers", ["Future Marker", "Another Future Marker"]),
        ])
        self.assertEqual(Counter(id(item) for group in groups for item in group["rows"]),
                         Counter(map(id, rows)))
        self.assertEqual(lab_groups("Hormonal Panel", [rows[4]]),
                         [{"title": "Growth Axis", "rows": [rows[4]]}])

    def test_immunoblot_has_its_own_table_and_preserves_all_other_markers(self):
        rows = [row(name, september="negative", july="-") for name in (
            "DFS70", "CRP (hs)", "Centromere B", "Anti-TPO", "Sm", "Future Marker",
            "Sm, RNP/Sm", "IgA (Serum)",
        )]
        groups = lab_groups("Immunology & Inflammation", rows)
        self.assertEqual([(group["title"], [item[0] for item in group["rows"]])
                          for group in groups], [
            (None, ["CRP (hs)", "Future Marker"]),
            ("Immune Markers & Antibodies", ["Anti-TPO", "IgA (Serum)"]),
            ("ANA/ENA Immunoblot", ["DFS70", "Centromere B", "Sm", "Sm, RNP/Sm"]),
        ])
        self.assertEqual(Counter(id(item) for group in groups for item in group["rows"]),
                         Counter(map(id, rows)))
        self.assertEqual(lab_groups("Immunology & Inflammation", [rows[2]]),
                         [{"title": "ANA/ENA Immunoblot", "rows": [rows[2]]}])

    def test_partition_preserves_objects_duplicates_values_and_order(self):
        cases = (
            ("Metabolic Health", "Insulin", "Glucose", "LDH"),
            ("Cardiac Health & Coagulation", "Cholesterol LDL", "Cholesterol HDL", "Creatine Kinase (CK)"),
            ("Micronutrients", "Vitamin D3", "Vitamin C", "Selenium"),
            ("Infectious Diseases", "HIV", "HCV", "SARS-CoV-2 RT-PCR"),
        )
        for category, marker, related, followup in cases:
            with self.subTest(category=category):
                first = row(marker, september="3.0", july="3.8")
                second = row(marker, september="3.1", july="3.9")
                rows = [first, row(related), row(followup, september="pending"),
                        second, first, row("Future Marker")]
                before = list(rows)
                groups = lab_groups(category, rows)
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
        fat_soluble, water_soluble, selenium = lab_groups("Micronutrients", rows)
        dates = ("2026-09", "2026-07", "2026-03", "2026-01")

        def populated_dates(group):
            return [month for index, month in enumerate(dates, start=1)
                    if any(item[index] != "-" for item in group["rows"])]

        self.assertEqual(populated_dates(fat_soluble), ["2026-07", "2026-03", "2026-01"])
        self.assertEqual(populated_dates(water_soluble), ["2026-07", "2026-03"])
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
