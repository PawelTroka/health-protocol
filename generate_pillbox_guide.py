"""Generate the printable supplement pillbox guide linked from README.md."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "Supplement-Pillbox-Guide.docx"
PILLBOX_URL = "https://gymbeam.com/adjustable-pillbox-gymbeam.html"


COLORS = {
    "ink": "162236",
    "muted": "536176",
    "line": "C9D3DF",
    "empty": "EFF3F7",
    "empty_ink": "7B8797",
    "morning": "176B87",
    "morning_fill": "E8F5F8",
    "lunch": "B66B14",
    "lunch_fill": "FFF3DF",
    "before": "8A3FFC",
    "before_fill": "F2ECFF",
    "after": "087F5B",
    "after_fill": "E7F7F0",
    "evening": "344E8C",
    "evening_fill": "EBF0FB",
    "rx": "9D2449",
    "rx_fill": "FBE9F0",
    "warning": "A64B00",
    "warning_fill": "FFF0D8",
    "white": "FFFFFF",
}


def item(code, name, dose="", qty="1 pill", icons="", note="", kind="active"):
    return {
        "code": code,
        "name": name,
        "dose": dose,
        "qty": qty,
        "icons": icons,
        "note": note,
        "kind": kind,
    }


def empty(code):
    return item(code, "EMPTY", qty="Available compartment", kind="empty")


PAGES = [
    {
        "title": "MORNING • BOX 1",
        "range": "M.1–M.9",
        "accent": "morning",
        "callout": "Breakfast pill organizer • Row-major placement: left to right, top to bottom.",
        "cells": [
            item("M.1", "B. longum 35624®", "1 bln CFU", icons="🦠 🚽"),
            item("M.2", "L. reuteri Gastrus®", "200 mln CFU", icons="🦠 🚽"),
            empty("M.3"),
            item("M.4", "Co Q10", "100 mg", icons="❤️ 🧠"),
            item("M.5", "Acetyl-L-Carnitine", "750 mg", qty="large tablet • 1 of 2", icons="🧠 ⚡"),
            item("M.6", "Acetyl-L-Carnitine", "750 mg", qty="large tablet • 2 of 2", icons="🧠 ⚡"),
            empty("M.7"),
            item("M.8", "Silicon", "14 mg", icons="💇‍♂️ 🦴"),
            item("M.9", "Lion’s Mane Extract", "600 mg", icons="🧠 🛡️", note="Polysaccharides 180 mg"),
        ],
    },
    {
        "title": "MORNING • BOX 2",
        "range": "M.10–M.18",
        "accent": "morning",
        "callout": "M.15 holds all three small NR capsules together; ranges elsewhere mean separate compartments.",
        "cells": [
            item("M.10", "L-Ergothioneine", "25 mg", icons="🧠 👨‍🦳", note="ErgoActive® • Vitamin C 5 mg"),
            item("M.11", "NAC", "1,000 mg", icons="🛡️ 🫁"),
            empty("M.12"),
            item("M.13", "Astaxanthin", "18 mg", icons="👁️ 👨‍🦳"),
            item("M.14", "Vitamin K complex", "K1 1.5 mg • MK-4 1 mg\nMK-7 0.2 mg", icons="🦴 ❤️"),
            item("M.15", "Nicotinamide Riboside", "3 × 300 mg • 900 mg total", qty="3 small capsules • same slot", icons="🧠 ⚡"),
            item("M.16", "Spermidine HCl", "50 mg", icons="⏰ 🧠", note="Spermidine 28 mg"),
            empty("M.17"),
            item("M.18", "Fisetin", "400 mg", icons="⏰ 🛡️"),
        ],
    },
    {
        "title": "LUNCH • BOX 1",
        "range": "L.1–L.9",
        "accent": "lunch",
        "callout": "L.1 is one divided compartment. Omega-3 is conditional and occupies three large-softgel slots.",
        "cells": [
            {
                "code": "L.1",
                "name": "SHARED PRESCRIPTION SLOT",
                "kind": "shared",
                "parts": [
                    item("L.1.1", "Ezetimibe", "10 mg", icons="❤️ ⚕️", kind="rx"),
                    item("L.1.2", "Tadalafil", "5 mg", icons="🍆 ❤️ ⚕️", kind="rx"),
                ],
            },
            item("L.2", "Omega-3", "EPA 500 mg • DHA 250 mg", qty="large softgel • 1 of 3", icons="❤️ 🧠", note="NON-FATTY-FISH DAYS ONLY", kind="warning"),
            item("L.3", "Omega-3", "EPA 500 mg • DHA 250 mg", qty="large softgel • 2 of 3", icons="❤️ 🧠", note="NON-FATTY-FISH DAYS ONLY", kind="warning"),
            item("L.4", "Omega-3", "EPA 500 mg • DHA 250 mg", qty="large softgel • 3 of 3", icons="❤️ 🧠", note="NON-FATTY-FISH DAYS ONLY", kind="warning"),
            item("L.5", "Sodium Butyrate", "500 mg", icons="🦠 🚽", note="Butyric acid 400 mg"),
            item("L.6", "Cocoa Flavanols", "250 mg", qty="large capsule • 1 of 2", icons="❤️ 🧠"),
            item("L.7", "Cocoa Flavanols", "250 mg", qty="large capsule • 2 of 2", icons="❤️ 🧠"),
            empty("L.8"),
            item("L.9", "Lycopene", "20 mg", icons="🍅 👨‍🦳"),
        ],
    },
    {
        "title": "LUNCH • BOX 2",
        "range": "L.10–L.18",
        "accent": "lunch",
        "callout": "Evidence-weighted order continues from Lunch Box 1; each cell is one physical compartment.",
        "cells": [
            item("L.10", "Curcumin • Longvida®", "400 mg", icons="🔥 🧠", note="Curcuminoids ≥80 mg"),
            item("L.11", "Ceratiq® Wheat Oil Extract", "350 mg", icons="👨‍🦳 💧"),
            item("L.12", "Ginger", "400 mg", icons="🔥 🚽", note="Gingerols 40 mg • Shogaols 6.72 mg"),
            item("L.13", "Broccoli Seed Extract", "200 mg", icons="🛡️ 🔥", note="Glucoraphanin 20 mg • Myrosinase"),
            item("L.14", "Berberine HCl", "490 mg", icons="🩸 🚽"),
            item("L.15", "ABG10+® Black Garlic", "400 mg", icons="❤️ 🛡️", note="DER 10:1 • SAC ≈0.4 mg"),
            item("L.16", "Phosphatidylserine", "300 mg", icons="🧠 😌"),
            item("L.17", "Milk Thistle", "380 mg", icons="🛡️ 🚽"),
            item("L.18", "DIM", "200 mg", icons="🛡️ 🍆"),
        ],
    },
    {
        "title": "EVENING • BOX 1",
        "range": "E.1–E.9",
        "accent": "evening",
        "callout": "E.1 is one divided compartment. E.2 remains intentionally empty. Follow the frequency labels exactly.",
        "cells": [
            {
                "code": "E.1",
                "name": "SHARED PRESCRIPTION SLOT",
                "kind": "shared",
                "parts": [
                    item("E.1.1", "Isotretinoin", "10 mg", icons="👨‍🦳 ⚕️", note="WEEKLY ONLY", kind="rx"),
                    item("E.1.2", "Dutasteride", "0.5 mg", icons="💇‍♂️ ⚕️", note="EVERY 2ND DAY", kind="rx"),
                ],
            },
            empty("E.2"),
            item("E.3", "Oral Minoxidil", "5 mg", icons="💇‍♂️ 🧔 ⚕️", kind="rx"),
            item("E.4", "L. reuteri Gastrus®", "200 mln CFU", icons="🦠 🚽"),
            item("E.5", "Sodium Butyrate", "500 mg", icons="🦠 🚽", note="Butyric acid 400 mg"),
            item("E.6", "Melisen", "Melatonin 1 mg", icons="😴 😌"),
            item("E.7", "Glycine", "1,000 mg", qty="capsule • 1 of 3", icons="😴 🧠"),
            item("E.8", "Glycine", "1,000 mg", qty="capsule • 2 of 3", icons="😴 🧠"),
            item("E.9", "Glycine", "1,000 mg", qty="capsule • 3 of 3", icons="😴 🧠"),
        ],
    },
    {
        "title": "EVENING • BOX 2",
        "range": "E.10–E.18",
        "accent": "evening",
        "callout": "One cell per physical compartment; two Inositol capsules remain separated because of size.",
        "cells": [
            item("E.10", "L-Theanine", "400 mg", icons="😴 😌"),
            item("E.11", "Berberine HCl", "490 mg", icons="🩸 🚽"),
            item("E.12", "Magnesium Glycinate", "133.3 mg elemental", icons="💪 🧠"),
            item("E.13", "PharmaGABA®", "250 mg", icons="😴 😌", note="Magnesium citrate 20 mg"),
            item("E.14", "Milk Thistle", "380 mg", icons="🛡️ 🚽"),
            item("E.15", "Ashwagandha KSM-66", "500 mg", icons="😌 😴", note="Withanolides 25 mg"),
            item("E.16", "Inositol", "1,000 mg", qty="capsule • 1 of 2", icons="🧠 😌"),
            item("E.17", "Inositol", "1,000 mg", qty="capsule • 2 of 2", icons="🧠 😌"),
            item("E.18", "Apigenin", "200 mg", icons="😴 😌"),
        ],
    },
    {
        "title": "BEFORE WORKOUT",
        "range": "BW.1–BW.9",
        "accent": "before",
        "callout": "Take with the normal pre-workout drink. Powders use BW.0 codes and are not pillbox compartments.",
        "cells": [
            item("BW.1", "Pycnogenol®", "100 mg", icons="🫀 ❤️", note="OPC 65 mg"),
            item("BW.2", "Rhodiola Rosea", "600 mg", icons="🧠 ⚡"),
            item("BW.3", "Taurine", "1,500 mg", icons="❤️ 💪"),
            item("BW.4", "Maca Root Extract", "500 mg", icons="🍆 ⚡", note="DER 10:1"),
            item("BW.5", "Fenugreek", "750 mg", icons="🍆 🚽"),
            item("BW.6", "CaAKG", "500 mg", qty="capsule • 1 of 3", icons="⏰ 💪"),
            item("BW.7", "CaAKG", "500 mg", qty="capsule • 2 of 3", icons="⏰ 💪"),
            item("BW.8", "CaAKG", "500 mg", qty="capsule • 3 of 3", icons="⏰ 💪"),
            item("BW.9", "Tribulus Terrestris", "1,500 mg", icons="🍆"),
        ],
    },
    {
        "title": "AFTER WORKOUT",
        "range": "AW.1–AW.9",
        "accent": "after",
        "callout": "Swallow these pills first; then start the AW.0 WPI/EAA drink. Empty cells are intentional.",
        "cells": [
            item("AW.1", "UC-II® Type II Collagen", "40 mg", icons="🦴 💪"),
            item("AW.2", "Urolithin A", "500 mg", icons="⏰ 💪"),
            item("AW.3", "MSM", "1,500 mg", qty="tablet • 1 of 2", icons="🦴 🔥"),
            item("AW.4", "MSM", "1,500 mg", qty="tablet • 2 of 2", icons="🦴 🔥"),
            empty("AW.5"),
            empty("AW.6"),
            empty("AW.7"),
            empty("AW.8"),
            item("AW.9", "Glucosamine Sulfate 2KCl", "1,400 mg", icons="🦴 🛡️"),
        ],
    },
]


def shade(element, fill: str):
    tc_pr = element._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=95, start=115, bottom=85, end=115):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_borders(cell, color="C9D3DF", size="10"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right"):
        tag = f"w:{edge}"
        edge_el = borders.find(qn(tag))
        if edge_el is None:
            edge_el = OxmlElement(tag)
            borders.append(edge_el)
        edge_el.set(qn("w:val"), "single")
        edge_el.set(qn("w:sz"), size)
        edge_el.set(qn("w:color"), color)


def set_repeatable_font(run, size, bold=False, color=None, name="Aptos"):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn(f"w:{attr}"), name)


def add_hyperlink(paragraph, text, url, color="176B87"):
    part = paragraph.part
    rel_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), rel_id)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    run.append(r_pr)
    color_el = OxmlElement("w:color")
    color_el.set(qn("w:val"), color)
    r_pr.append(color_el)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)
    text_el = OxmlElement("w:t")
    text_el.text = text
    run.append(text_el)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def add_page_field(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Page ")
    set_repeatable_font(run, 7.5, color=COLORS["muted"])
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_begin, instr, fld_end])
    run = paragraph.add_run(" / ")
    set_repeatable_font(run, 7.5, color=COLORS["muted"])
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " NUMPAGES "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_begin, instr, fld_end])


def compact_paragraph(paragraph, before=0, after=0, line=1.0):
    fmt = paragraph.paragraph_format
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.line_spacing = line


def fill_simple_cell(cell, data, accent_key):
    cell.text = ""
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_margins(cell)
    kind = data.get("kind", "active")
    if kind == "empty":
        shade(cell, COLORS["empty"])
        border = COLORS["line"]
        accent = COLORS["empty_ink"]
    elif kind == "rx":
        shade(cell, COLORS["rx_fill"])
        border = COLORS["rx"]
        accent = COLORS["rx"]
    elif kind == "warning":
        shade(cell, COLORS["warning_fill"])
        border = COLORS["warning"]
        accent = COLORS["warning"]
    else:
        shade(cell, COLORS[f"{accent_key}_fill"])
        border = COLORS[accent_key]
        accent = COLORS[accent_key]
    set_cell_borders(cell, border, "11")

    p = cell.paragraphs[0]
    compact_paragraph(p, after=3)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(data["code"])
    set_repeatable_font(run, 10.5, bold=True, color=accent)

    p = cell.add_paragraph()
    compact_paragraph(p, after=2, line=0.95)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(data["name"])
    set_repeatable_font(run, 12.2 if kind != "empty" else 15, bold=True, color=COLORS["ink"] if kind != "empty" else COLORS["empty_ink"])

    if data.get("dose"):
        p = cell.add_paragraph()
        compact_paragraph(p, after=2, line=0.95)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(data["dose"])
        set_repeatable_font(run, 9.3, bold=True, color=accent)

    p = cell.add_paragraph()
    compact_paragraph(p, after=2, line=0.95)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(data.get("qty", ""))
    set_repeatable_font(run, 8.2, color=COLORS["muted"])

    if data.get("icons"):
        p = cell.add_paragraph()
        compact_paragraph(p, after=1)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(data["icons"])
        set_repeatable_font(run, 10, name="Segoe UI Emoji")

    if data.get("note"):
        p = cell.add_paragraph()
        compact_paragraph(p, before=1, line=0.95)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(data["note"])
        note_color = COLORS["warning"] if kind in ("warning", "rx") else COLORS["muted"]
        set_repeatable_font(run, 7.5, bold=kind in ("warning", "rx"), color=note_color)


def fill_shared_cell(cell, data, accent_key):
    cell.text = ""
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_margins(cell, top=75, start=70, bottom=65, end=70)
    shade(cell, COLORS["rx_fill"])
    set_cell_borders(cell, COLORS["rx"], "11")

    p = cell.paragraphs[0]
    compact_paragraph(p, after=1)
    run = p.add_run(f"{data['code']} • SHARED SLOT")
    set_repeatable_font(run, 9.5, bold=True, color=COLORS["rx"])

    nested = cell.add_table(rows=1, cols=2)
    nested.alignment = WD_TABLE_ALIGNMENT.CENTER
    nested.autofit = False
    for idx, part in enumerate(data["parts"]):
        sub = nested.cell(0, idx)
        sub.width = Inches(1.47)
        fill_simple_cell(sub, part, accent_key)
        set_cell_margins(sub, top=60, start=45, bottom=55, end=45)


def add_page(document, page_data, page_index):
    accent_key = page_data["accent"]
    accent = COLORS[accent_key]

    title_table = document.add_table(rows=1, cols=2)
    title_table.autofit = False
    title_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    title_table.columns[0].width = Inches(7.95)
    title_table.columns[1].width = Inches(2.1)
    left = title_table.cell(0, 0)
    right = title_table.cell(0, 1)
    for cell in (left, right):
        set_cell_margins(cell, top=0, start=0, bottom=0, end=0)
        set_cell_borders(cell, COLORS["white"], "0")
    left.text = ""
    p = left.paragraphs[0]
    compact_paragraph(p, after=0)
    run = p.add_run(page_data["title"])
    set_repeatable_font(run, 18, bold=True, color=COLORS["ink"])
    right.text = ""
    p = right.paragraphs[0]
    compact_paragraph(p, after=0)
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run(page_data["range"])
    set_repeatable_font(run, 16, bold=True, color=accent)

    p = document.add_paragraph()
    compact_paragraph(p, before=1, after=4)
    run = p.add_run(page_data["callout"])
    set_repeatable_font(run, 8.2, color=COLORS["muted"])

    table = document.add_table(rows=3, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.allow_autofit = False
    width = Inches(3.31)
    for col in table.columns:
        col.width = width
    for row in table.rows:
        row.height = Inches(2.08)
        row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    for index, data in enumerate(page_data["cells"]):
        cell = table.cell(index // 3, index % 3)
        cell.width = width
        if data.get("kind") == "shared":
            fill_shared_cell(cell, data, accent_key)
        else:
            fill_simple_cell(cell, data, accent_key)

    p = document.add_paragraph()
    compact_paragraph(p, before=3, after=0)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("One numbered cell = one physical compartment • ")
    set_repeatable_font(run, 7.3, color=COLORS["muted"])
    add_hyperlink(p, "GymBeam Adjustable PillBox", PILLBOX_URL, color=accent)
    run = p.add_run(" • Full doses and evidence notes: README.md")
    set_repeatable_font(run, 7.3, color=COLORS["muted"])

    if page_index < len(PAGES) - 1:
        p = document.add_paragraph()
        p.add_run().add_break(WD_BREAK.PAGE)


def build_document():
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Inches(11)
    section.page_height = Inches(8.5)
    section.top_margin = Inches(0.31)
    section.bottom_margin = Inches(0.30)
    section.left_margin = Inches(0.39)
    section.right_margin = Inches(0.39)
    section.header_distance = Inches(0.12)
    section.footer_distance = Inches(0.14)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(9)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0

    doc.core_properties.title = "Supplement Pillbox Guide"
    doc.core_properties.subject = "Physical slot map for the health protocol"
    doc.core_properties.author = "Health Protocol"
    doc.core_properties.keywords = "pillbox, supplements, organizer, protocol"

    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    compact_paragraph(p)
    run = p.add_run("HEALTH PROTOCOL • PHYSICAL SLOT MAP • 22 AUG 2026")
    set_repeatable_font(run, 6.5, bold=True, color=COLORS["muted"])

    footer = section.footer
    p = footer.paragraphs[0]
    compact_paragraph(p)
    add_page_field(p)

    for index, page_data in enumerate(PAGES):
        add_page(doc, page_data, index)

    doc.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build_document())
