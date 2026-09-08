"""Curated imaging register and shared Markdown/HTML presentation.

Only narrative reports supply clinical findings. Image inventories and DICOM
metadata establish source availability, never a scan interpretation.
"""

from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path, PurePosixPath
import re
from urllib.parse import quote


@dataclass(frozen=True)
class Source:
    label: str
    path: str
    kind: str


@dataclass(frozen=True)
class Study:
    id: str
    date: str
    title: str
    modality: str
    availability: str
    summary: str
    findings: tuple[str, ...]
    sources: tuple[Source, ...]
    date_basis: str
    report_date: str = ""
    viewing: str = ""
    report_note: str = ""


STUDIES = (
    Study(
        id="facial-ct-2026-08-14", date="2026-08-14",
        title="Facial skeleton CT", modality="CT · without contrast",
        availability="Report transcription + DICOM",
        summary="The report concludes that bilateral bony infraorbital nerve canals are an anatomical variant.",
        findings=(
            "The infraorbital nerve canals run within both maxillary sinuses, with bony septa forming cells communicating with the ostiomeatal complexes.",
            "Mild mucosal thickening in all paranasal sinuses, greatest in the maxillary sinuses; swelling of both ostiomeatal complexes with segmental obstruction.",
            "Keros type II and slight left-convex nasal septal deviation. Nasal passages are patent; sinus bony boundaries show no lysis or sclerotic remodelling.",
            "Linear, streak-like calcifications in facial subcutaneous tissue, mainly the cheeks; the report queries a post-injection origin.",
        ),
        sources=(
            Source("Report transcription (PL / EN)", "results/FacialCT-2026-08-14/README.md", "report"),
            Source("DICOMDIR", "results/FacialCT-2026-08-14/DICOMDIR", "dicom"),
            *(Source(f"ZIP part {part}/3", f"results/FacialCT-2026-08-14/FacialCT-2026-08-14.zip.00{part}", "archive") for part in (1, 2, 3)),
        ),
        date_basis="Study date verified against DICOM metadata and the archived report transcription. The report was issued separately on August 20.",
        report_date="2026-08-20",
        report_note="Findings above summarize the archived transcription of the official report; the original report image is not stored here. The linked record separates the Polish report, English translation and later patient-history commentary. The report does not contain a formal cephalometric or surgical-planning analysis.",
        viewing="The archive has 905 DICOM objects in 9 series, including four 1mm reconstruction series. Locally, import DICOMDIR with the complete IMAGE hierarchy. For download, keep all three ZIP parts together and extract from .zip.001 with 7-Zip; import the extracted DICOMDIR in a DICOM viewer. DICOMDIR alone does not contain the scan images.",
    ),
    Study(
        id="abdominal-wall-2026-05-19", date="2026-05-19",
        title="Abdominal-wall ultrasound · after repair", modality="Ultrasound (USG)",
        availability="Report PDF + images",
        summary="The postoperative ultrasound reports no features of hernia and no pathological fluid collections.",
        findings=("Linea alba width at the operated site is up to ~4cm. This is a width measurement, not a residual hernia defect.",),
        sources=(
            Source("Report PDF", "results/AbdominalWallUltrasound-2026-05-19/Report.pdf", "report"),
            Source("Ultrasound images PDF", "results/AbdominalWallUltrasound-2026-05-19/UltrasoundImages.pdf", "images"),
        ),
        date_basis="Examination date printed on the original ultrasound report.",
    ),
    Study(
        id="abdominal-wall-2025-12-04", date="2025-12-04",
        title="Abdominal and abdominal-wall ultrasound · before repair", modality="Ultrasound (USG)",
        availability="Report PDF + images",
        summary="An 8×8mm defect in the upper linea alba is described, with a hernia sac containing a small-intestine loop.",
        findings=("The report also describes the abdominal organs; see the PDF for the complete organ-by-organ findings.",),
        sources=(
            Source("Report PDF", "results/AbdominalWallUltrasound-2025-12-04/Report.pdf", "report"),
            Source("Ultrasound images PDF", "results/AbdominalWallUltrasound-2025-12-04/UltrasoundImages.pdf", "images"),
        ),
        date_basis="Examination date printed on the original ultrasound report.",
    ),
    Study(
        id="dental-cbct-2025-10-27", date="2025-10-27",
        title="Dental CBCT", modality="Cone-beam CT (CBCT)",
        availability="Images only · no written report",
        summary="A dental 3D image set is archived. No written interpretation is present, so no reported clinical findings are entered.",
        findings=(),
        sources=(Source("DICOM ZIP archive", "results/DentalCBCT-2025-10-27/DentalCBCT-2025-10-27.zip", "archive"),),
        date_basis="Study and acquisition dates verified across all 347 DICOM files; metadata identifies the jaw and a 3D CBCT image set.",
        viewing="The ZIP contains 347 DICOM files in one 0.15mm series and two XML files, with no DICOMDIR. Extract the ZIP and import the complete folder in a DICOM-capable dental viewer. The files are scan data, not an interactive browser preview or a written report.",
    ),
    Study(
        id="dental-panoramic-2024-05-06", date="2024-05-06",
        title="Panoramic dental X-ray", modality="X-ray (RTG) · panoramic",
        availability="Images only · no written report",
        summary="A panoramic dental radiograph (pantomogram) is archived as a JPEG. No written interpretation or measurements are present.",
        findings=(),
        sources=(Source("Original panoramic JPEG", "results/DentalXRay-2024-05-06/PanoramicDentalXRay.jpg", "images"),),
        date_basis="Date verified from the 06.05.2024 overlay on the original JPEG.",
    ),
    Study(
        id="dental-lateral-2024-05-06", date="2024-05-06",
        title="Lateral cephalometric X-ray", modality="X-ray (RTG) · lateral",
        availability="Images only · no written report",
        summary="A lateral cephalometric radiograph is archived as a JPEG. No written interpretation or cephalometric measurements are present.",
        findings=(),
        sources=(Source("Original lateral JPEG", "results/DentalXRay-2024-05-06/LateralCephalometricXRay.jpg", "images"),),
        date_basis="Date verified from the 06.05.2024 overlay on the original JPEG.",
    ),
)

GROUPS = (
    ("Facial CT", ("facial-ct-2026-08-14",)),
    ("Abdominal wall · before and after repair", ("abdominal-wall-2025-12-04", "abdominal-wall-2026-05-19")),
    ("Dental imaging", ("dental-cbct-2025-10-27", "dental-panoramic-2024-05-06", "dental-lateral-2024-05-06")),
)
INTRO = (
    "Dated examinations and their source records, newest first. Written-report findings, "
    "image files and scan archives are identified separately. Imaging is not assigned a lab "
    "score or folded into monthly averages."
)
COMPARISON = (
    "The December 2025 and May 2026 reports document the abdominal wall before and after repair. "
    "The 8×8mm hernia defect and the later linea alba width up to ~4cm are different measurements; "
    "they are not a size trend. The postoperative finding is specific to the May 19 examination."
)


def validate_imaging_sources(root: Path, studies=STUDIES):
    """Fail before generating reports if the catalog contains broken/unsafe references."""
    root = Path(root).resolve()
    ids = set()
    for study in studies:
        if not re.fullmatch(r"[a-z0-9-]+", study.id) or study.id in ids:
            raise ValueError(f"Invalid or duplicate imaging ID: {study.id}")
        ids.add(study.id)
        for value in (study.date, study.report_date):
            if value and (not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) or not date.fromisoformat(value)):
                raise ValueError(f"Invalid imaging date: {value}")
        if not study.date or (study.report_date and study.report_date < study.date):
            raise ValueError(f"Invalid study/report chronology: {study.id}")
        if not study.sources:
            raise ValueError(f"Imaging study has no sources: {study.id}")
        for source in study.sources:
            path = PurePosixPath(source.path)
            if path.is_absolute() or ".." in path.parts or "\\" in source.path or ":" in source.path:
                raise ValueError(f"Imaging source must be repository-relative: {source.path}")
            target = (root / source.path).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Missing or invalid imaging source file: {source.path}")
    if studies is STUDIES:
        grouped_ids = [study_id for _, group in GROUPS for study_id in group]
        if len(grouped_ids) != len(ids) or set(grouped_ids) != ids:
            raise ValueError("Imaging groups must include every examination exactly once")


def _inventory_summary():
    reports = [source for study in STUDIES for source in study.sources if source.kind == "report"]
    pdfs = sum(source.path.lower().endswith(".pdf") for source in reports)
    transcriptions = len(reports) - pdfs
    image_only = sum(not any(source.kind == "report" for source in study.sources) for study in STUDIES)
    return f"{len(STUDIES)} examinations · {pdfs} original report PDFs · {transcriptions} report transcription · {image_only} image-only examinations"


def _links(study, *, html):
    if html:
        return " ".join(f"<a href='{quote(source.path, safe='/')}'>{escape(source.label)}</a>" for source in study.sources)
    return " · ".join(f"[{source.label}]({quote(source.path, safe='/')})" for source in study.sources)


def render_imaging_html():
    lookup = {study.id: study for study in STUDIES}
    parts = ["<section class='imaging' id='imaging' aria-labelledby='imaging-title'>",
             "<h2 id='imaging-title'>Structural &amp; Diagnostic Imaging</h2>",
             f"<p class='section-intro'>{escape(INTRO)}</p>",
             f"<p class='section-meta'>{_inventory_summary()}</p>",
             "<div class='table-scroll'><table class='imaging-index'><caption>Examination index · select an examination for findings and source files</caption>",
             "<thead><tr><th scope='col'>Date</th><th scope='col'>Examination</th><th scope='col'>Available records</th></tr></thead><tbody>"]
    for study in STUDIES:
        parts.append(f"<tr><td><time datetime='{study.date}'>{study.date}</time></td>"
                     f"<td><a href='#imaging-{study.id}'>{escape(study.title)}</a></td><td>{escape(study.availability)}</td></tr>")
    parts.append("</tbody></table></div>")
    for title, ids in GROUPS:
        parts.append(f"<section class='imaging-group'><h3>{escape(title)}</h3>")
        if title.startswith("Abdominal"):
            parts.append(f"<p class='imaging-context'>{escape(COMPARISON)}</p>")
        parts.append("<div class='imaging-cards'>")
        for study_id in ids:
            study = lookup[study_id]
            parts.append(f"<article class='imaging-card' id='imaging-{study.id}'>"
                         f"<p class='imaging-date'><time datetime='{study.date}'>{study.date}</time> · {escape(study.modality)}</p>"
                         f"<h4>{escape(study.title)}</h4><p class='imaging-availability'>{escape(study.availability)}</p>"
                         f"<p>{escape(study.summary)}</p>")
            if study.findings:
                parts.append("<ul>" + "".join(f"<li>{escape(finding)}</li>" for finding in study.findings) + "</ul>")
            if study.report_date or study.report_note:
                issued = f"Report issued <time datetime='{study.report_date}'>{study.report_date}</time>. " if study.report_date else ""
                parts.append(f"<p class='imaging-provenance'>{issued}{escape(study.report_note)}</p>")
            parts.append(f"<div class='imaging-links' aria-label='Source files'>{_links(study, html=True)}</div>")
            parts.append("<details><summary>Source details &amp; viewing</summary>")
            parts.append(f"<p>{escape(study.date_basis)}</p>")
            if study.viewing:
                parts.append(f"<p>{escape(study.viewing)}</p>")
            parts.append("</details><p class='imaging-back'><a href='#imaging'>Back to imaging index ↑</a></p></article>")
        parts.append("</div></section>")
    return "".join(parts) + "</section>"


def render_imaging_md():
    lookup = {study.id: study for study in STUDIES}
    parts = ["<a id='imaging'></a>\n\n## Structural & Diagnostic Imaging", INTRO,
             _inventory_summary() + ".",
             "| Date | Examination | Available records |\n| :--- | :--- | :--- |\n" + "\n".join(
                 f"| {study.date} | [{study.title}](#imaging-{study.id}) | {study.availability} |" for study in STUDIES)]
    for title, ids in GROUPS:
        parts.append(f"### {title}")
        if title.startswith("Abdominal"):
            parts.append(COMPARISON)
        for study_id in ids:
            study = lookup[study_id]
            parts.append(f"<a id='imaging-{study.id}'></a>\n\n#### {study.date} · {study.title}")
            parts.append(f"**{study.modality}** · {study.availability}")
            parts.append(study.summary)
            if study.findings:
                parts.append("\n".join(f"- {finding}" for finding in study.findings))
            if study.report_date or study.report_note:
                issued = f"**Report issued:** {study.report_date}. " if study.report_date else ""
                parts.append(issued + study.report_note)
            parts.append("**Source files:** " + _links(study, html=False))
            details = study.date_basis + ("\n\n" + study.viewing if study.viewing else "")
            parts.append(f"<details>\n<summary>Source details &amp; viewing</summary>\n\n{details}\n\n</details>")
            parts.append("[Back to imaging index ↑](#imaging)")
    return "\n\n".join(parts) + "\n\n"


IMAGING_CSS = """
.report-nav { display: flex; flex-wrap: wrap; gap: 10px 20px; margin: 12px 0 28px; padding: 12px 16px; background: #eef3f8; border-radius: 8px; }
.report-nav a, .imaging a { color: #24598c; text-underline-offset: 3px; }
.imaging { border-top: 2px solid #dce4ed; margin-top: 40px; padding-top: 4px; }
.imaging :target { scroll-margin-top: 20px; }
.imaging-index { font-size: .92rem; min-width: 550px; }
.imaging-index caption { text-align: left; color: #536278; font-size: .86rem; margin: 0 0 10px; }
.imaging-index th, .imaging-index td { padding: 12px 14px; border: 0; border-bottom: 1px solid #dce4ed; vertical-align: top; }
.imaging-index th { background: #eef3f8; }
.imaging-index td:first-child { white-space: nowrap; font-variant-numeric: tabular-nums; }
.imaging-group { margin: 30px 0; }
.imaging-group h3 { margin-bottom: 12px; font-size: 1.2rem; }
.imaging-context { border-left: 3px solid #87a5bf; padding: 10px 16px; background: #f4f7fa; color: #43576d; }
.imaging-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 390px), 1fr)); gap: 16px; align-items: start; }
.imaging-card { border: 1px solid #dce4ed; border-radius: 10px; padding: 20px 24px; min-width: 0; }
.imaging-card:target { border-color: #24598c; box-shadow: 0 0 0 2px #dbeafe; }
.imaging-date { color: #536278; font-size: .85rem; margin: 0 0 6px; font-variant-numeric: tabular-nums; }
.imaging-card h4 { font-size: 1.13rem; margin: 0 0 8px; }
.imaging-availability { color: #43576d; font-size: .82rem; margin: 0 0 16px; }
.imaging-card li { margin: 6px 0; }
.imaging-provenance { color: #536278; font-size: .88rem; }
.imaging-links { display: flex; flex-wrap: wrap; gap: 8px; margin: 20px 0 14px; }
.imaging-links a { border: 1px solid #cddaea; border-radius: 6px; padding: 7px 11px; background: #f6f9fc; font-size: .86rem; }
.imaging details { border-top: 1px solid #e2e8f0; padding-top: 12px; font-size: .87rem; color: #536278; }
.imaging summary { cursor: pointer; color: #344d6c; }
.imaging summary:focus-visible, .imaging a:focus-visible { outline: 2px solid #24598c; outline-offset: 3px; }
.imaging-back { font-size: .8rem; margin: 16px 0 0; }
@media(max-width: 700px) { .imaging-card { padding: 16px; } .imaging-index { min-width: 0; font-size: .82rem; } .imaging-index th, .imaging-index td { padding: 8px; } }
@media print { .imaging-card { break-inside: avoid; } .imaging-back, .report-nav { display: none; } }
"""
