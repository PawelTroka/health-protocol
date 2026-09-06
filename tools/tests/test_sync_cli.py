"""Isolated sync transactions; all fixtures are synthetic and networking is mocked."""

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import sync_vitals as cli
from tools.health_sync import api, auth, oura


class FixedDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        current = cls(2026, 9, 6, 12, tzinfo=timezone.utc)
        return current.astimezone(tz) if tz else current.replace(tzinfo=None)


def reading(identifier, day, value, *, provider="withings", metric="Body Mass", unit="kg"):
    return {
        "id": identifier, "provider": provider, "day": day, "metric": metric,
        "value": value, "unit": unit, "source_kind": "api",
    }


def withings_group(identifier=101, weight=80400):
    return {
        "grpid": identifier,
        "category": 1,
        "attrib": 0,
        "date": int(datetime(2026, 8, 3, 12, tzinfo=timezone.utc).timestamp()),
        "measures": [{"type": 1, "value": weight, "unit": -3}],
    }


class SyncCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="synthetic-vitals-cli-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cache = self.root / ".health-sync"
        self.cache.mkdir()
        for target, value in (("ROOT", self.root), ("CACHE", self.cache),
                              ("datetime", FixedDateTime)):
            patcher = patch.object(cli, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.previous_records = [
            reading("withings:measure:101:Body Mass", "2026-08-03", 90),
            reading("untouched-withings-day", "2026-08-04", 82),
            reading("july-history", "2026-07-31", 83),
            reading("untouched-provider", "2026-08-05", 7.25,
                    provider="oura", metric="Sleep Duration", unit="h"),
        ]
        (self.cache / "records.json").write_bytes(cli.json_bytes({
            "schema_version": 1, "records": self.previous_records,
        }))
        (self.root / "results").mkdir()
        (self.root / "results" / "vitals_monthly.json").write_bytes(b'{"previous": true}\n')
        (self.root / "results.md").write_bytes(b"Existing Markdown report\n")
        (self.root / "results.html").write_bytes(b"<p>Existing HTML report</p>\n")
        (self.root / "README.md").write_bytes(b"Unrelated canonical protocol\n")
        old_archive = self.cache / "raw" / "oura" / "existing.csv"
        old_archive.parent.mkdir(parents=True)
        old_archive.write_bytes(b"Existing immutable source\n")
        patcher = patch.object(cli, "prepare_reports", side_effect=self.prepared_reports)
        self.prepare = patcher.start()
        self.addCleanup(patcher.stop)
        # A missed API mock must fail immediately, never access a real account.
        patcher = patch.object(api, "fetch", side_effect=AssertionError("Unexpected API access"))
        self.fetch = patcher.start()
        self.addCleanup(patcher.stop)

    def prepared_reports(self, monthly):
        data = cli.json_bytes(monthly)
        return {
            self.root / "results.md": b"Synthetic Markdown\n" + data,
            self.root / "results.html": b"Synthetic HTML\n" + data,
        }

    def snapshot(self):
        return {path.relative_to(self.root).as_posix(): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def args(self, *arguments):
        return cli.parser().parse_args(list(arguments))

    def import_file(self, payload=None, **options):
        path = self.root / "withings-input.json"
        if payload is None:
            payload = {"measuregrps": [withings_group()]}
        path.write_bytes(cli.json_bytes(payload))
        arguments = ["import", "--withings-json", str(path),
                     "--start", "2026-08-01", "--end", "2026-09-05"]
        if options.get("dry_run"):
            arguments.append("--dry-run")
        return self.args(*arguments)

    def run_quietly(self, args):
        with redirect_stdout(io.StringIO()):
            cli.run_import(args)

    def test_second_provider_failure_preserves_cache_reports_and_raw_archives(self):
        self.fetch.side_effect = [{"sleep": [], "daily_sleep": []}, RuntimeError("Withings unavailable")]
        parsed = [reading("incoming-oura", "2026-08-03", 8,
                          provider="oura", metric="Sleep Duration", unit="h")]
        before = self.snapshot()
        args = self.args("sync", "--provider", "both", "--end", "2026-09-05")
        with patch.object(oura, "parse_api", return_value=parsed):
            with self.assertRaisesRegex(RuntimeError, "Withings unavailable"):
                self.run_quietly(args)
        self.assertEqual(self.fetch.call_count, 2)
        self.assertEqual(self.snapshot(), before)
        self.prepare.assert_not_called()

    def test_report_preparation_failure_preserves_every_existing_output(self):
        args = self.import_file()
        before = self.snapshot()
        self.prepare.side_effect = RuntimeError("Synthetic generator failure")
        with self.assertRaisesRegex(RuntimeError, "generator failure"):
            self.run_quietly(args)
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_validates_reports_but_creates_no_outputs_or_archives(self):
        args = self.import_file(dry_run=True)
        before = self.snapshot()
        self.run_quietly(args)
        self.prepare.assert_called_once()
        self.fetch.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_file_import_preserves_unrepresented_data_and_reimport_is_idempotent(self):
        args = self.import_file()
        original_input = Path(args.withings_json).read_bytes()
        original_readme = (self.root / "README.md").read_bytes()
        self.run_quietly(args)
        records = json.loads((self.cache / "records.json").read_bytes())["records"]
        for retained in self.previous_records[1:]:
            self.assertIn(retained, records)
        weights = [record for record in records
                   if record["id"] == "withings:measure:101:Body Mass"]
        self.assertEqual(len(weights), 1)
        self.assertEqual(weights[0]["value"], 80.4)
        monthly = json.loads((self.root / "results" / "vitals_monthly.json").read_bytes())
        weight_mean = monthly["months"]["2026-08"]["Body Mass"]
        self.assertEqual(weight_mean["value"], "81.2")
        self.assertEqual(weight_mean["n_records"], 2)
        archive = self.root / weights[0]["source_file"]
        self.assertEqual(archive.read_bytes(), original_input)
        self.assertEqual((self.root / "README.md").read_bytes(), original_readme)
        after_first = self.snapshot()
        self.run_quietly(args)
        self.assertEqual(self.snapshot(), after_first)
        self.assertEqual(len(json.loads((self.cache / "records.json").read_bytes())["records"]), len(records))
        self.assertEqual(len(list((self.cache / "raw" / "withings").glob("*.json"))), 1)
        self.fetch.assert_not_called()

    def test_nested_json_credentials_are_rejected_before_parsing_or_archiving(self):
        for field in ("access_token", "REFRESH-TOKEN", "client_secret", "Authorization", "password", "idToken"):
            with self.subTest(field=field):
                args = self.import_file({"measuregrps": [withings_group()],
                                         "metadata": {"nested": [{field: "synthetic-secret"}]}})
                before = self.snapshot()
                with patch.object(cli, "archive") as archive:
                    with self.assertRaisesRegex(ValueError, "credential fields") as raised:
                        self.run_quietly(args)
                    archive.assert_not_called()
                self.assertNotIn("synthetic-secret", str(raised.exception))
                self.prepare.assert_not_called()
                self.assertEqual(self.snapshot(), before)

    def test_wrapped_withings_response_with_more_pages_is_not_imported(self):
        args = self.import_file({"status": 0, "body": {
            "measuregrps": [withings_group()], "more": 1, "offset": 42,
        }})
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "pagination is incomplete"):
            self.run_quietly(args)
        self.prepare.assert_not_called()
        self.assertEqual(self.snapshot(), before)

    def test_atomic_commit_restores_prior_first_file_when_second_replace_fails(self):
        first = self.root / "results.md"
        second = self.root / "results.html"
        before = self.snapshot()
        actual_replace = cli.os.replace
        calls = []

        def fail_second(source, destination):
            calls.append(Path(destination))
            if len(calls) == 2:
                raise OSError("Synthetic second replacement failure")
            return actual_replace(source, destination)

        with patch.object(cli.os, "replace", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "second replacement"):
                cli.atomic_commit({first: b"Changed first\n", second: b"Changed second\n"})
        self.assertEqual(calls, [first, second, first])
        self.assertEqual(self.snapshot(), before)

    def test_atomic_commit_removes_new_first_file_when_later_replace_fails(self):
        first = self.root / "new-output.json"
        second = self.root / "results.md"
        before = self.snapshot()
        actual_replace = cli.os.replace

        def fail_second(source, destination):
            if Path(destination) == second:
                raise OSError("Synthetic later replacement failure")
            return actual_replace(source, destination)

        with patch.object(cli.os, "replace", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "later replacement"):
                cli.atomic_commit({first: b"New file\n", second: b"Changed existing\n"})
        self.assertFalse(first.exists())
        self.assertEqual(self.snapshot(), before)

    def test_noninteractive_connect_returns_without_prompting_or_touching_credentials(self):
        error = io.StringIO()
        with patch.object(cli.sys, "stdin", io.StringIO()), \
                patch("builtins.input", side_effect=AssertionError("Unexpected prompt")) as prompt, \
                patch.object(cli, "getpass", side_effect=AssertionError("Unexpected secret prompt")) as secret, \
                patch.object(auth, "configure") as configure, \
                patch.object(auth, "authorize") as authorize, \
                redirect_stdout(io.StringIO()), redirect_stderr(error):
            result = cli.main(["connect", "oura"])
        self.assertEqual(result, 1)
        self.assertIn("interactive local terminal", error.getvalue())
        prompt.assert_not_called()
        secret.assert_not_called()
        configure.assert_not_called()
        authorize.assert_not_called()


if __name__ == "__main__":
    unittest.main()
