"""Dated historical laboratory observations, separate from current trends.

The source inventory and deduplication decisions are documented in
results/Historical-Labs/Sources.md. Values preserve the primary report's
precision; presentation compaction belongs to the shared result formatter.
"""

from html import escape
import re

from tools.health_sync.number_display import compact_reference


HISTORICAL_LABS_TITLE = "Historical Laboratory Results"
HISTORICAL_LABS_ANCHOR = "results-historical-laboratory-results"
HISTORICAL_LABS_SOURCE = "results/Historical-Labs/Sources.md"
HISTORICAL_LABS_INTRO = (
    "13 observations from three historical collection dates. Duplicate PDF, CSV "
    "and CDA exports are counted once. Original units and laboratory references "
    "are retained; these records do not enter the current trend comparisons. "
    "Colors use an unambiguous historical reference only. Risk-dependent targets "
    "and multi-band interpretations remain unscored."
)

# reference is the visible historical reference/interpretation. score_reference
# is deliberately absent where the source supplies multiple conditional bands.
# A missing printed unit/reference is displayed as a dash, never a numeric zero.
HISTORICAL_LABS = (
    {
        "date": "2023-10-02",
        "specimen": "Serum lipid panel",
        "note": (
            "Collected at 10:02; fasting status is not stated. LDL and non-HDL "
            "were calculated by the laboratory; LDL used the Friedewald formula. "
            "LDL is 73mg/dl in the PDF/CDA and 73.20mg/dl in the CSV, representing "
            "one result. Risk categories below reproduce this report's targets."
        ),
        "records": (
            {"test": "Total cholesterol", "value": "125", "unit": "mg/dl",
             "reference": "115 - 190", "score_reference": "115 - 190"},
            {"test": "HDL cholesterol", "value": "41", "unit": "mg/dl",
             "reference": ">40 (laboratory recommendation)", "score_reference": ">40"},
            {"test": "Non-HDL cholesterol", "value": "84", "unit": "mg/dl",
             "reference": "<130 (moderate risk); <100 (high); <85 (very high); <70 (extreme)",
             "calculated": True},
            {"test": "LDL cholesterol", "value": "73", "unit": "mg/dl",
             "reference": "<115 (low risk); <100 (moderate); <70 (high); <55 (very high); <40 (extreme)",
             "calculated": True, "alternate_csv_value": "73.20"},
            {"test": "Triglycerides", "value": "54", "unit": "mg/dl",
             "reference": "<150 (fasting); <175 (non-fasting)"},
        ),
    },
    {
        "date": "2022-03-17",
        "specimen": "Swab",
        "note": (
            "Collected at 19:32 (19:32:48 in the certificate/CDA). Three PDFs "
            "and one CDA describe the same negative PCR. Reports were issued "
            "on March 17-18, 2022; the CDA document timestamp in 2025 is not "
            "the collection date."
        ),
        "records": (
            {"test": "SARS-CoV-2 RT-PCR", "value": "Negative", "unit": "-",
             "reference": "-", "score_reference": "negative"},
        ),
    },
    {
        "date": "2015-01-14",
        "specimen": "Serum",
        "note": (
            "The printed 00:00 collection time is treated as unspecified. "
            "Fasting status is not stated. Homocysteine was reported on "
            "January 15 and vitamin D on January 16; both belong to the "
            "January 14 collection. Vitamin D bands reproduce the historical "
            "laboratory interpretation."
        ),
        "records": (
            {"test": "Sodium", "value": "141", "unit": "mmol/l",
             "reference": "136 - 145", "score_reference": "136 - 145"},
            {"test": "Potassium", "value": "4.2", "unit": "mmol/l",
             "reference": "3.5 - 5.1", "score_reference": "3.5 - 5.1"},
            {"test": "Calcium, total", "value": "9.9", "unit": "mg/dl",
             "reference": "8.4 - 10.2", "score_reference": "8.4 - 10.2"},
            {"test": "Insulin", "value": "16.4", "unit": "µIU/ml",
             "reference": "2.6 - 24.9", "score_reference": "2.6 - 24.9"},
            {"test": "Ferritin", "value": "118.3", "unit": "ng/ml",
             "reference": "30.0 - 400.0", "score_reference": "30.0 - 400.0"},
            {"test": "Homocysteine", "value": "10.74", "unit": "µmol/l",
             "reference": "0.00 - 12.00", "score_reference": "0.00 - 12.00"},
            {"test": "Vitamin D, 25-OH", "value": "18.40", "unit": "ng/ml",
             "reference": "<10 deficient; 10-30 insufficient; 30-100 sufficient; >100 toxic"},
        ),
    },
)


def _marker(record):
    return record["test"] + (" (calculated)" if record.get("calculated") else "")


def _markdown_literal(value):
    """Keep source strings literal in Markdown text and table cells."""
    text = escape(str(value), quote=False).replace("\n", " ")
    return re.sub(r"([\\`*_{}\[\]()#!|])", r"\\\1", text)


def render_historical_html(format_cell):
    """Reuse the report formatter without passing current category targets."""
    html = f"<section id='{HISTORICAL_LABS_ANCHOR}'>"
    html += f"<h2>{escape(HISTORICAL_LABS_TITLE)}</h2>"
    html += f"<p class='section-intro'>{escape(HISTORICAL_LABS_INTRO)} "
    html += f"<a href='{HISTORICAL_LABS_SOURCE}'>Sources and transcription notes</a>.</p>"
    for panel in HISTORICAL_LABS:
        html += f"<h3>{escape(panel['date'])} - {escape(panel['specimen'])}</h3>"
        html += f"<p class='section-intro'>{escape(panel['note'])}</p>"
        html += "<div class='table-scroll'><table><tr><th>Metric</th><th>Result</th>"
        html += "<th>Unit</th><th>Laboratory reference / interpretation</th></tr>"
        for record in panel["records"]:
            cell = format_cell(record["value"], record.get("score_reference", "-"))
            html += f"<tr><td><b>{escape(_marker(record))}</b></td><td>{cell}</td>"
            html += f"<td>{escape(record['unit'])}</td>"
            html += f"<td>{escape(compact_reference(record['reference']))}</td></tr>"
        html += "</table></div>"
    return html + "</section>"


def render_historical_md(format_cell):
    """Render the same dated archive and source note in Markdown."""
    md = f"## {HISTORICAL_LABS_TITLE}\n\n{HISTORICAL_LABS_INTRO} "
    md += f"[Sources and transcription notes]({HISTORICAL_LABS_SOURCE}).\n\n"
    for panel in HISTORICAL_LABS:
        md += f"### {_markdown_literal(panel['date'])} - {_markdown_literal(panel['specimen'])}\n\n"
        md += _markdown_literal(panel["note"]) + "\n\n"
        md += "| Metric | Result | Unit | Laboratory reference / interpretation |\n"
        md += "| :--- | :--- | :--- | :--- |\n"
        for record in panel["records"]:
            cell = format_cell(record["value"], record.get("score_reference", "-"))
            md += f"| **{_markdown_literal(_marker(record))}** | {cell} | "
            md += f"{_markdown_literal(record['unit'])} | "
            md += f"{_markdown_literal(compact_reference(record['reference']))} |\n"
        md += "\n"
    return md
