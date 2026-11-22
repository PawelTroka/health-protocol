"""Read-only pillbox parity checks with independent synthetic protocol entries."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
from pathlib import Path
import runpy
import tempfile
import unittest

from tools.validate_pillbox_guide import PAGE_CODES, ROOT, main, validate


def fixture():
    """Keep synthetic health content independent of future protocol decisions."""
    cells = {code: {"code": code, "name": "EMPTY", "kind": "empty", "dose": "",
                    "note": "", "same_slot_count": 1}
             for page in PAGE_CODES for code in page}
    rows = {code: f"- **{code}** (empty)" for code in cells}

    def active(code, name, dose, count=1, note="", kind="active"):
        cells[code] = {"code": code, "name": name, "dose": dose, "kind": kind,
                       "same_slot_count": count, "note": note}

    rows["M.1"] = "- 🥇 **M.1** [Bacterium strain 35624® 1bln CFU](https://example.org/strain)"
    active("M.1", "Bacterium strain 35624®", "1 bln CFU")
    rows["M.5"] = "- **M.5-6** 2x [Compound Alpha 750mg](https://example.org/alpha)"
    rows["M.6"] = ""
    for code in ("M.5", "M.6"):
        active(code, "Compound Alpha", "750mg")
    rows["M.13"] = "- **M.13** [Compound Beta (Brand®) 12mg](https://example.org/beta)"
    active("M.13", "Compound Beta (Brand®)", "12mg")
    rows["M.14"] = "- **M.14** [Vitamin K1 1.5mg + K2 MK-4 1mg + K2 MK-7 0.2mg](https://example.org/k)"
    active("M.14", "Vitamin K1 + K2 MK-4 + K2 MK-7", "K1 1.5mg • K2 MK-4 1mg\nK2 MK-7 0.2mg")
    rows["M.15"] = "- **M.15** 3x [Compound Gamma 300mg](https://example.org/gamma)"
    active("M.15", "Compound Gamma", "300mg", count=3)
    rows["L.1"] = ("- **L.1.1** [Medicine One 10mg](https://example.org/one)\n"
                   "- **L.1.2** [Medicine Two 5mg](https://example.org/two)")
    cells["L.1"] = {"code": "L.1", "name": "PRESCRIPTIONS", "kind": "shared", "parts": [
        {"code": "L.1.1", "name": "Medicine One", "dose": "10mg", "kind": "rx"},
        {"code": "L.1.2", "name": "Medicine Two", "dose": "5mg", "kind": "rx"},
    ]}
    rows["L.2"] = "- **L.2-3** 2x [Omega 3 690mg EPA 310mg DHA](https://example.org/omega) (conditional)"
    rows["L.3"] = ""
    for code in ("L.2", "L.3"):
        active(code, "Omega 3", "690mg EPA • 310mg DHA", kind="warning")
    rows["L.5"] = "- **L.5** [Compound Salt 500mg (Active compound 400mg)](https://example.org/salt)"
    active("L.5", "Compound Salt", "500mg", note="Active compound 400mg")
    rows["L.10"] = ("- **L.10** [Curcumin + Ginger + Turmerones](https://example.org/blend)\n"
                    "  - Blend 500mg (Curcuminoids 200mg; Turmerones 15mg); Gingerols 60mg")
    active("L.10", "Curcumin + Ginger + Turmerones", "Curcuminoids 200mg")
    # A non-prescription shared compartment, shaped like the Affron/Melatonin PR.
    rows["E.5"] = ("- **E.5.1** [Saffron Stigma Extract Affron® 28mg](https://example.org/affron)\n"
                   "  - Lepticrosalides® 1mg (3.5%)\n"
                   "- **E.5.2** [Melatonin 1mg](https://example.org/melatonin)")
    cells["E.5"] = {"code": "E.5", "name": "SAFFRON + MELATONIN", "kind": "shared", "parts": [
        {"code": "E.5.1", "name": "Saffron Stigma Extract Affron®", "dose": "28mg", "kind": "active"},
        {"code": "E.5.2", "name": "Melatonin", "dose": "1mg", "kind": "active"},
    ]}
    rows["E.8"] = "- **E.8-10** 3x [Glycine 1g](https://example.org/glycine)"
    rows["E.9"] = rows["E.10"] = ""
    for code in ("E.8", "E.9", "E.10"):
        active(code, "Glycine", "1g")
    rows["B.8"] = "- **B.8-9** 4x [Compound Delta 500mg](https://example.org/delta)"
    rows["B.9"] = ""
    for code in ("B.8", "B.9"):
        active(code, "Compound Delta", "500mg", count=2)
    lines = ["# Synthetic protocol", "## 5. Supplements and drugs"]
    for title, prefix, capacity in [("Morning", "M", 18), ("Lunch", "L", 18),
                                    ("Before workout", "B", 9), ("After workout", "A", 9),
                                    ("Evening", "E", 18)]:
        lines.append(f"### {title}")
        lines.extend(rows[f"{prefix}.{number}"] for number in range(1, capacity + 1))
    lines.extend(["## Notes", "- **M.13** unrelated note; not an active entry"])
    pages = [{"cells": [cells[code] for code in codes]} for codes in PAGE_CODES]
    return "\n".join(lines), pages


class PillboxValidationTests(unittest.TestCase):
    def setUp(self):
        self.readme, self.pages = fixture()

    def cell(self, code):
        for page in self.pages:
            for cell in page["cells"]:
                if cell["code"] == code:
                    return cell
                for part in cell.get("parts", []):
                    if part["code"] == code:
                        return part
        self.fail(f"Missing fixture cell {code}")

    def fails(self, message):
        errors = validate(self.readme, self.pages)
        self.assertTrue(any(message in error for error in errors), errors)

    def test_current_repository_passes(self):
        pages = runpy.run_path(str(ROOT / "tools/generate_pillbox_guide.py"))["PAGES"]
        self.assertEqual(validate((ROOT / "README.md").read_text(encoding="utf-8"), pages), [])

    def test_synthetic_ranges_shared_rx_and_non_rx_and_counts_pass(self):
        before = deepcopy(self.pages)
        self.assertEqual(validate(self.readme, self.pages), [])
        self.assertEqual(self.pages, before, "validator must not normalize or change source data")

    def test_wrong_dose_and_wrong_unit_fail(self):
        for dose in ("999mg", "12g", "", "112mg"):
            with self.subTest(dose=dose):
                self.cell("M.13")["dose"] = dose
                self.fails("M.13 (README:")

    def test_standalone_million_and_billion_counts_pass(self):
        for dose, displayed in (("500mln", "500 mln"), ("1bln", "1 bln"),
                                ("2.5bln", "2.5 bln")):
            with self.subTest(dose=dose):
                self.readme, self.pages = fixture()
                self.readme = self.readme.replace("35624® 1bln CFU", f"35624® {dose}")
                self.cell("M.1")["dose"] = displayed
                self.assertEqual(validate(self.readme, self.pages), [])

    def test_biological_counts_preserve_amount_and_unit_identity(self):
        doses = ("500mln", "499mln", "1bln", "500mln CFU", "1bln CFU",
                 "500mln heat-inactivated cells")
        for expected in doses:
            with self.subTest(expected=expected):
                self.readme, self.pages = fixture()
                self.readme = self.readme.replace("35624® 1bln CFU", f"35624® {expected}")
                self.cell("M.1")["dose"] = expected
                self.assertEqual(validate(self.readme, self.pages), [])
                for displayed in doses:
                    if displayed != expected:
                        with self.subTest(displayed=displayed):
                            self.cell("M.1")["dose"] = displayed
                            self.fails("dose:")

    def test_bare_counts_do_not_match_qualified_formulation_details(self):
        for qualified in ("500mln CFU", "500mln heat-inactivated cells", "1bln CFU"):
            with self.subTest(qualified=qualified):
                self.readme, self.pages = fixture()
                self.readme = self.readme.replace("35624® 1bln CFU", "35624®")
                self.readme = self.readme.replace("https://example.org/strain)",
                                                f"https://example.org/strain)\n  - {qualified}")
                self.cell("M.1")["dose"] = qualified
                self.assertEqual(validate(self.readme, self.pages), [])
                self.cell("M.1")["dose"] = qualified.split()[0]
                self.fails("formulation details")

    def test_bare_count_annotations_do_not_match_qualified_units(self):
        for qualified in ("500mln CFU", "500mln heat-inactivated cells"):
            with self.subTest(qualified=qualified):
                self.readme, self.pages = fixture()
                self.readme = self.readme.replace("(Brand®) 12mg", "(Brand®) 12mg (Count 500mln)")
                self.cell("M.13")["note"] = "Count 500mln"
                self.assertEqual(validate(self.readme, self.pages), [])
                self.cell("M.13")["note"] = f"Count {qualified}"
                self.fails("dose annotation:")

    def test_wrong_name_and_lost_brand_fail(self):
        for name in ("Unrelated product", "Compound Beta", "Compound Beta (Other®)"):
            with self.subTest(name=name):
                self.cell("M.13")["name"] = name
                self.fails("name:")

    def test_same_slot_multiplier_must_agree(self):
        for count in (1, 2, 4, 0, -1, True, 3.0, "3"):
            with self.subTest(count=count):
                self.cell("M.15")["same_slot_count"] = count
                self.fails("M.15: multiplier")

    def test_rendered_quantity_cannot_override_the_multiplier(self):
        self.cell("M.15")["qty"] = "99capsules"
        self.fails("M.15: rendered qty count")
        self.cell("M.15")["qty"] = "3capsules"
        self.assertEqual(validate(self.readme, self.pages), [])

    def test_rendered_quantity_rejects_free_text_and_non_pill_units(self):
        for quantity in ("Take 10mg", "3mL", "3capsules whenever desired", "3", None):
            with self.subTest(quantity=quantity):
                self.cell("M.15")["qty"] = quantity
                self.fails("qty")

    def test_explicit_quantity_form_must_match(self):
        self.readme = self.readme.replace("https://example.org/gamma)", "https://example.org/gamma) — 3capsules")
        self.cell("M.15")["qty"] = "3tablets"
        self.fails("rendered qty form")

    def test_rendered_frequency_needs_matching_explicit_row_instruction(self):
        self.cell("M.15")["qty"] = "3capsules/day"
        self.fails("lacks a matching explicit")
        self.readme = self.readme.replace("https://example.org/gamma)", "https://example.org/gamma) — 3capsules daily with Breakfast")
        self.assertEqual(validate(self.readme, self.pages), [])
        self.cell("M.15")["qty"] = "3capsules/week"
        self.fails("lacks a matching explicit")

    def test_quantity_without_frequency_does_not_invent_daily_use(self):
        self.cell("L.1.1")["qty"] = "1tablet"
        self.assertEqual(validate(self.readme, self.pages), [])
        self.cell("L.1.1")["qty"] = "1tablet/day"
        self.fails("lacks a matching explicit")

    def test_range_multiplier_is_distributed_per_cell(self):
        self.cell("B.8")["same_slot_count"] = 4
        self.fails("B.8: multiplier: README 2x")

    def test_range_readme_count_must_divide_compartments(self):
        self.readme = self.readme.replace("**B.8-9** 4x", "**B.8-9** 3x")
        self.fails("cannot be distributed equally")

    def test_wrong_slot_and_swapped_positions_fail(self):
        self.pages[0]["cells"][0], self.pages[0]["cells"][1] = self.pages[0]["cells"][1], self.pages[0]["cells"][0]
        self.fails("expected slot M.1")

    def test_duplicate_guide_slot_fails(self):
        self.cell("M.2")["code"] = "M.3"
        self.fails("duplicate guide entry")

    def test_missing_page_or_cell_fails(self):
        self.pages[0]["cells"].pop()
        self.fails("expected nine physical cells")
        self.pages.pop()
        self.fails("expected exactly eight pages")

    def test_malformed_leaf_kind_is_reported(self):
        self.cell("M.13")["kind"] = []
        self.fails("unsupported leaf kind")

    def test_wrong_empty_state_in_both_directions_fails(self):
        self.cell("M.2")["kind"] = "active"
        self.fails("M.2: empty/occupied state differs")
        self.cell("M.13")["kind"] = "empty"
        self.fails("M.13: empty/occupied state differs")

    def test_hidden_dose_in_empty_cell_fails(self):
        self.cell("M.2")["dose"] = "1mg"
        self.fails("an empty cell must say EMPTY and have no dose/note")

    def test_empty_quantity_cannot_render_a_dosing_instruction(self):
        self.cell("M.2")["qty"] = "Available compartment"
        self.assertEqual(validate(self.readme, self.pages), [])
        for quantity in ("Take 10mg", "1capsule", "EMPTY — take later"):
            with self.subTest(quantity=quantity):
                self.cell("M.2")["qty"] = quantity
                self.fails("empty qty must be blank")

    def test_shared_non_rx_parts_are_checked_individually(self):
        for code in ("E.5.1", "E.5.2"):
            with self.subTest(code=code):
                self.readme, self.pages = fixture()
                self.cell(code)["dose"] = "999mg"
                self.fails(f"{code} (README:")

    def test_shared_rx_dose_is_checked(self):
        self.cell("L.1.2")["dose"] = "10mg"
        self.fails("L.1.2 (README:")

    def test_shared_parts_order_and_missing_part_fail(self):
        self.cell("E.5")["parts"].reverse()
        self.fails("shared part codes/order")
        self.cell("E.5")["parts"].pop()
        self.fails("shared cell needs exactly two parts")

    def test_combination_dose_values_and_labels_fail(self):
        for dose in ("K1 1mg • K2 MK-4 1.5mg\nK2 MK-7 0.2mg",
                     "K2 MK-4 1.5mg • K1 1mg\nK2 MK-7 0.2mg",
                     "K1 1.5mg • K2 MK-4 1mg"):
            with self.subTest(dose=dose):
                self.cell("M.14")["dose"] = dose
                self.fails("dose:")

    def test_constituent_amounts_keep_their_labels(self):
        self.cell("L.2")["dose"] = "310mg EPA • 690mg DHA"
        self.fails("L.2 (README:")

    def test_quantity_annotations_must_match(self):
        self.cell("L.5")["note"] = "Active compound 401mg"
        self.fails("dose annotation:")

    def test_unexpected_dose_annotation_fails(self):
        self.cell("M.13")["dose"] = "12mg (Other active 2mg)"
        self.fails("dose annotation:")

    def test_blend_detail_dose_cannot_match_a_numeric_substring(self):
        self.readme = self.readme.replace("Curcuminoids 200mg", "Curcuminoids 1,200mg")
        self.fails("absent from the README entry's formulation details")

    def test_blend_detail_amount_cannot_match_a_concentration(self):
        for amount in ("200mg/g", "200mg / g", "200mg per g", "200mg–400mg",
                       "200mg – 400mg", "200mg to 400mg"):
            with self.subTest(amount=amount):
                self.readme, self.pages = fixture()
                self.readme = self.readme.replace("Curcuminoids 200mg", "Curcuminoids " + amount)
                self.fails("absent from the README entry's formulation details")

    def test_whitespace_and_guide_bullets_are_supported(self):
        self.cell("M.13")["dose"] = "12 mg"
        self.cell("L.2")["dose"] = "690 mg EPA\n310 mg DHA"
        self.assertEqual(validate(self.readme, self.pages), [])

    def test_enzyme_units_and_trailing_brand_are_supported(self):
        self.readme = self.readme.replace("Compound Beta (Brand®) 12mg", "Lactase 10,000FCC (Intoleran)")
        self.cell("M.13").update(name="Lactase (Intoleran)", dose="10,000FCC")
        self.assertEqual(validate(self.readme, self.pages), [])

    def test_powders_and_notes_do_not_consume_physical_slots(self):
        self.readme = self.readme.replace("### Morning", "### Morning\n- **M.0.3** [Drink 26g](https://example.org/drink)\n  - Ingredient 1mg<sup>M.13</sup>")
        self.assertEqual(validate(self.readme, self.pages), [])

    def test_wrong_timing_and_unknown_physical_prefix_fail(self):
        self.readme = self.readme.replace("### Morning", "### Lunch", 1)
        self.fails("wrong timing heading")
        self.readme, _ = fixture()
        self.readme = self.readme.replace("**B.1**", "**BW.1**", 1)
        self.fails("unsupported physical code")

    def test_missing_or_duplicate_readme_row_fails(self):
        self.readme = self.readme.replace("- **M.2** (empty)", "")
        self.fails("missing physical compartments")
        self.readme, _ = fixture()
        self.readme = self.readme.replace("- **M.2** (empty)", "- **M.2** (empty)\n- **M.2** (empty)")
        self.fails("duplicate entry M.2")

    def test_unsupported_slot_rows_do_not_hide_conflicting_duplicates(self):
        for prefix in ("*", "+", "1.", "  -", "> -", "- [ ]", "- [x]"):
            with self.subTest(prefix=prefix):
                self.readme, self.pages = fixture()
                row = f"{prefix} **M.13** [Different product 999mg](https://example.org/wrong)"
                self.readme = self.readme.replace("### Morning", "### Morning\n" + row)
                self.fails("unsupported slot-bearing row")

    def test_hidden_active_rows_and_hidden_section_are_rejected(self):
        for opening, closing in (("```markdown", "```"), ("~~~markdown", "~~~"), ("<!--", "-->")):
            for start in ("### Morning", "## 5. Supplements and drugs"):
                with self.subTest(opening=opening, start=start):
                    self.readme, self.pages = fixture()
                    self.readme = self.readme.replace(start, opening + "\n" + start)
                    self.readme = self.readme.replace("## Notes", closing + "\n## Notes")
                    self.fails("fence")

    def test_fences_and_comments_outside_active_section_are_unrelated(self):
        self.readme = ("<!-- unrelated introductory comment -->\n```markdown\nExample\n```\n"
                       + self.readme + "\n* **M.13** a note\n<!-- other notes -->\n```\nexample\n```")
        self.assertEqual(validate(self.readme, self.pages), [])

    def test_product_link_must_be_closed(self):
        self.readme = self.readme.replace("](https://example.org/beta)", "](https://example.org/beta")
        self.fails("missing its closing parenthesis")

    def test_unknown_dose_notation_fails_instead_of_skipping(self):
        self.readme = self.readme.replace("Compound Beta (Brand®) 12mg", "Compound Beta (Brand®) 12unknownunits")
        self.fails("name:")

    def test_unknown_unit_cannot_use_blend_detail_fallback(self):
        self.readme = self.readme.replace("Compound Beta (Brand®) 12mg", "Compound Beta (Brand®) 12unknownunits")
        self.readme = self.readme.replace("https://example.org/beta)", "https://example.org/beta)\n  - 999unknownunits")
        self.cell("M.13").update(name="Compound Beta (Brand®) 12unknownunits", dose="999unknownunits")
        self.fails("no supported quantity/unit")

    def test_cli_pass_failure_and_no_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tools").mkdir()
            (root / "README.md").write_text(self.readme, encoding="utf-8")
            generator = root / "tools/generate_pillbox_guide.py"
            generator.write_text(f"PAGES = {self.pages!r}\nif __name__ == '__main__':\n    raise AssertionError('must not generate')\n", encoding="utf-8")
            before = set(root.rglob("*"))
            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(output):
                self.assertEqual(main(["--root", str(root)]), 0)
                self.assertEqual(set(root.rglob("*")), before)
                self.cell("M.13")["dose"] = "999mg"
                generator.write_text(f"PAGES = {self.pages!r}\n", encoding="utf-8")
                self.assertEqual(main(["--root", str(root)]), 1)
            self.assertIn("M.13", output.getvalue())


if __name__ == "__main__":
    unittest.main()
