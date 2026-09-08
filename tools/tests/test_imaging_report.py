"""Imaging catalogue, evidence boundaries and links; no patient source reads."""

from collections import Counter
from dataclasses import FrozenInstanceError, replace
from datetime import date
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import runpy
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote

from tools import imaging_report


class ReportLinks(HTMLParser):
    """Read real anchors and destinations, without treating text as a link."""

    def __init__(self):
        super().__init__()
        self.ids = []
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag == "a" and "href" in attributes:
            self.hrefs.append(unquote(attributes["href"]))


def markdown_links(rendered):
    return [
        unquote(angle_path or bare_path)
        for angle_path, bare_path in re.findall(
            r"\[[^\]]+\]\((?:<([^>]+)>|([^\s)]+))\)", rendered,
        )
    ]


class ImagingCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[2]
        cls.html = imaging_report.render_imaging_html()
        cls.md = imaging_report.render_imaging_md()
        cls.links = ReportLinks()
        cls.links.feed(cls.html)

    def test_catalogue_is_complete_and_sorted_by_exact_study_date(self):
        expected = [
            ("facial-ct-2026-08-14", "2026-08-14"),
            ("abdominal-wall-2026-05-19", "2026-05-19"),
            ("abdominal-wall-2025-12-04", "2025-12-04"),
            ("dental-cbct-2025-10-27", "2025-10-27"),
            ("dental-panoramic-2024-05-06", "2024-05-06"),
            ("dental-lateral-2024-05-06", "2024-05-06"),
        ]
        self.assertEqual([(study.id, study.date) for study in imaging_report.STUDIES], expected)
        self.assertEqual(
            [date.fromisoformat(study.date) for study in imaging_report.STUDIES],
            sorted((date.fromisoformat(study.date) for study in imaging_report.STUDIES), reverse=True),
        )

    def test_study_and_source_records_are_immutable(self):
        self.assertIsInstance(imaging_report.STUDIES, tuple)
        study = imaging_report.STUDIES[0]
        self.assertIsInstance(study.findings, tuple)
        self.assertIsInstance(study.sources, tuple)
        with self.assertRaises(FrozenInstanceError):
            study.date = "2026-01-01"
        with self.assertRaises(FrozenInstanceError):
            study.sources[0].path = "elsewhere.pdf"

    def test_every_local_source_is_a_file_and_clickable_in_both_formats(self):
        imaging_report.validate_imaging_sources(self.root)
        md_links = markdown_links(self.md)
        for study in imaging_report.STUDIES:
            self.assertTrue(study.sources, study.id)
            for rendered in (self.html, self.md):
                self.assertIn(study.date, rendered)
            for source in study.sources:
                with self.subTest(study=study.id, source=source.path):
                    path = self.root / source.path
                    self.assertFalse(Path(source.path).is_absolute())
                    self.assertTrue(path.resolve().is_relative_to(self.root))
                    self.assertTrue(path.is_file(), source.path)
                    self.assertIn(source.path, self.links.hrefs)
                    self.assertIn(source.path, md_links)

    def test_timeline_anchors_resolve_to_exactly_one_study_card(self):
        destinations = Counter(self.links.ids)
        self.assertEqual(destinations["imaging"], 1)
        for study in imaging_report.STUDIES:
            anchor = f"imaging-{study.id}"
            with self.subTest(study=study.id):
                self.assertEqual(destinations[anchor], 1)
                self.assertIn(f"#{anchor}", self.links.hrefs)
        for href in self.links.hrefs:
            if href.startswith("#imaging-"):
                self.assertEqual(destinations[href[1:]], 1)

    def test_written_reports_are_links_not_bracketed_plain_text(self):
        reports = [source for study in imaging_report.STUDIES
                   for source in study.sources if source.kind == "report"]
        self.assertGreaterEqual(len(reports), 3)
        for source in reports:
            with self.subTest(source=source.path):
                self.assertIn(source.path, self.links.hrefs)
                self.assertIn(source.path, markdown_links(self.md))
                self.assertNotIn(f"[{source.path}]", self.html)
                self.assertNotIn(f"[{source.path}]", self.md)

    def test_facial_ct_acquisition_and_report_dates_remain_distinct(self):
        study = next(study for study in imaging_report.STUDIES
                     if study.id == "facial-ct-2026-08-14")
        self.assertEqual(study.date, "2026-08-14")
        self.assertEqual(study.report_date, "2026-08-20")
        self.assertTrue(study.date_basis)
        for rendered in (self.html, self.md):
            self.assertIn(study.date, rendered)
            self.assertIn(study.report_date, rendered)

    def test_image_only_studies_explicitly_lack_reports_and_inferred_findings(self):
        ids = {
            "dental-cbct-2025-10-27",
            "dental-panoramic-2024-05-06",
            "dental-lateral-2024-05-06",
        }
        for study in imaging_report.STUDIES:
            if study.id not in ids:
                continue
            with self.subTest(study=study.id):
                self.assertRegex(study.availability.lower(), r"no (?:written )?report")
                self.assertEqual(study.findings, ())
                self.assertFalse(any(source.kind == "report" for source in study.sources))
                self.assertEqual(study.report_date, "")
                for rendered in (self.html, self.md):
                    self.assertIn(study.availability, rendered)

    def test_default_groups_cannot_omit_or_duplicate_a_study(self):
        groups = imaging_report.GROUPS
        invalid_groups = {
            "omitted": groups[1:],
            "duplicated": groups + (("Duplicate", (imaging_report.STUDIES[0].id,)),),
        }
        for case, value in invalid_groups.items():
            with self.subTest(case=case), patch.object(imaging_report, "GROUPS", value):
                with self.assertRaisesRegex(ValueError, "every examination exactly once"):
                    imaging_report.validate_imaging_sources(self.root)


class ImagingGeneratorIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load definitions without main, point monthly reads at synthetic data,
        # and write both reports only to a temporary directory. Keep one fake
        # laboratory row so this checks the imaging/measurement integration.
        with tempfile.TemporaryDirectory() as folder:
            output_dir = Path(folder)
            monthly = output_dir / "monthly.json"
            monthly.write_text(json.dumps({
                "schema_version": 1, "as_of": "2026-09-07", "months": {},
            }), encoding="utf-8")
            with patch.dict(os.environ, {
                "HEALTH_PROTOCOL_VITALS_MONTHLY": str(monthly),
                "HEALTH_PROTOCOL_REPORT_DIR": str(output_dir),
            }):
                report = runpy.run_path(
                    str(Path(__file__).resolve().parents[1] / "generate_colored_report.py"),
                    run_name="imaging_integration_test",
                )
                row = ("Synthetic marker", *("1" for _ in report["date_columns"]), "index", "-")
                cls.outputs = {}
                for output_format in ("html", "md"):
                    generate = report[f"generate_{output_format}_report"]
                    path = output_dir / f"results.{output_format}"
                    with patch.dict(generate.__globals__, {"data": {"Synthetic measurement": [row]}}):
                        generate(path)
                    cls.outputs[output_format] = path.read_text(encoding="utf-8")

    def test_full_reports_embed_the_shared_imaging_section_once(self):
        for output_format, rendered in self.outputs.items():
            imaging = getattr(imaging_report, f"render_imaging_{output_format}")()
            with self.subTest(output_format=output_format):
                self.assertEqual(rendered.count(imaging), 1)
                self.assertIn("Synthetic marker", rendered)
                self.assertLess(rendered.index("Synthetic marker"), rendered.index(imaging))
        self.assertIn(imaging_report.IMAGING_CSS, self.outputs["html"])

    def test_full_reports_preserve_every_study_anchor_and_clickable_source(self):
        for output_format, rendered in self.outputs.items():
            parsed = ReportLinks()
            parsed.feed(rendered)
            hrefs = parsed.hrefs if output_format == "html" else markdown_links(rendered)
            ids = Counter(parsed.ids)
            with self.subTest(output_format=output_format):
                self.assertEqual(ids["imaging"], 1)
                self.assertIn("#imaging", hrefs)
                self.assertEqual(ids["measurements"], 1)
                for study in imaging_report.STUDIES:
                    anchor = f"imaging-{study.id}"
                    self.assertEqual(ids[anchor], 1)
                    self.assertIn(f"#{anchor}", hrefs)
                    for source in study.sources:
                        self.assertIn(source.path, hrefs)


class ImagingSourceValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.source = self.root / "results" / "scan report.pdf"
        self.source.parent.mkdir()
        self.source.write_bytes(b"synthetic source")
        self.study = replace(
            imaging_report.STUDIES[0],
            sources=(imaging_report.Source("Report PDF", "results/scan report.pdf", "report"),),
        )

    def validate(self, *studies):
        return imaging_report.validate_imaging_sources(self.root, studies=studies or (self.study,))

    def test_existing_relative_file_with_spaces_is_accepted(self):
        self.validate()

    def test_missing_sources_and_directory_links_are_rejected(self):
        for path in ("results/missing.pdf", "results"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.validate(replace(self.study, sources=(replace(self.study.sources[0], path=path),)))

    def test_path_escape_and_absolute_sources_are_rejected_even_when_file_exists(self):
        outside = self.root.parent / "outside.pdf"
        outside.write_bytes(b"synthetic external source")
        for path in ("../outside.pdf", str(outside), str(self.source)):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.validate(replace(self.study, sources=(replace(self.study.sources[0], path=path),)))

    def test_duplicate_study_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(self.study, replace(self.study, title="Another study with the same id"))

    def test_invalid_or_incomplete_study_and_report_dates_are_rejected(self):
        for field in ("date", "report_date"):
            for value in ("2026-08", "2026-02-30", "20-08-2026"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.validate(replace(self.study, **{field: value}))

    def test_report_cannot_predate_acquisition(self):
        with self.assertRaises(ValueError):
            self.validate(replace(self.study, report_date="2026-08-13"))

    def test_same_day_or_missing_report_dates_are_valid(self):
        for report_date in (self.study.date, ""):
            with self.subTest(report_date=report_date):
                self.validate(replace(self.study, report_date=report_date))


if __name__ == "__main__":
    unittest.main()
