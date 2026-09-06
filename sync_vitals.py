"""Import, average, validate and regenerate vitals on demand. See VITALS_SYNC.md."""

import argparse
from contextlib import contextmanager
from datetime import datetime
from getpass import getpass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo

from health_sync.monthly import MANAGED_START, aggregate, iso_date, merge_file_records, merge_records

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".health-sync"


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


@contextmanager
def sync_lock():
    """The OS releases this lock even if the process is interrupted."""
    CACHE.mkdir(exist_ok=True)
    with (CACHE / "sync.lock").open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("A vitals sync is already running.") from error
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def atomic_commit(changes):
    """Atomically replace each file; roll back completed replacements on error."""
    previous = {path: path.read_bytes() if path.exists() else None for path in changes}
    replaced = []
    try:
        for path, content in changes.items():
            if content == previous[path]:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
            replaced.append(path)
    except BaseException:
        for path in reversed(replaced):
            if previous[path] is None:
                path.unlink(missing_ok=True)
            else:
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                    stream.write(previous[path])
                    temporary = Path(stream.name)
                os.replace(temporary, path)
        raise


def archive(source, content, extension):
    digest = hashlib.sha256(content).hexdigest()
    relative = Path(".health-sync") / "raw" / source / (digest + extension)
    destination = ROOT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open("xb") as handle:
            handle.write(content)
    except FileExistsError:
        if destination.read_bytes() != content:
            raise RuntimeError("Raw archive hash conflict; source was not overwritten.")
    return relative.as_posix()


def load_cache():
    path = CACHE / "records.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("records"), list):
        raise ValueError("Unsupported local records cache; existing reports were preserved.")
    return payload["records"]


def reject_credentials(value):
    """Do not archive credentials accidentally included in a supplied JSON file."""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("_", "").replace("-", "")
            if normalized in {"accesstoken", "refreshtoken", "clientsecret", "authorization", "password", "idtoken"}:
                raise ValueError("The supplied JSON contains credential fields; export measurement data only.")
            reject_credentials(child)
    elif isinstance(value, list):
        for child in value:
            reject_credentials(child)


def parse_oura_snapshot(raw):
    """Parse exactly the bytes later archived, even if the download is replaced."""
    from health_sync.oura import parse_csv
    with tempfile.NamedTemporaryFile(dir=CACHE, suffix=".csv", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(raw)
    try:
        return parse_csv(temporary)
    finally:
        temporary.unlink(missing_ok=True)


def prepare_reports(monthly):
    """Deliberately run the generator from the repository root, in staging."""
    with tempfile.TemporaryDirectory(prefix="stage-", dir=CACHE) as directory:
        stage = Path(directory)
        source = stage / "vitals_monthly.json"
        source.write_bytes(json_bytes(monthly))
        env = dict(os.environ, HEALTH_PROTOCOL_VITALS_MONTHLY=str(source), HEALTH_PROTOCOL_REPORT_DIR=str(stage))
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "generate_colored_report.py")],
            cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60,
        )
        if result.returncode:
            raise RuntimeError("Report generation failed; existing reports were preserved.\n" + result.stderr[-2000:])
        return {ROOT / name: (stage / name).read_bytes() for name in ("results.md", "results.html")}


def print_summary(monthly):
    print(f"Monthly means through {monthly['as_of']} (missing days excluded):")
    for month, metrics in sorted(monthly["months"].items()):
        print(f"\n{month}")
        for metric, entry in sorted(metrics.items()):
            print(f"  {metric}: {entry['value']}{entry['unit']} | {entry['n_days']}/{entry['elapsed_days']} days, {entry['n_records']} readings ({entry['provider']})")


def run_import(args):
    from health_sync import api, oura, withings
    today = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    start = iso_date(args.start)
    end = iso_date(args.end) if args.end else today
    if start < MANAGED_START or start > end or end > today:
        raise ValueError("Use a date range from 2026-08-01 through today; July is preserved.")
    sources, incoming, providers = [], [], []
    if args.command == "sync":
        providers = ["oura", "withings"] if args.provider == "both" else [args.provider]
        for provider in providers:
            print(f"Fetching {provider.title()} readings for {start} through {end}...", flush=True)
            payload = api.fetch(provider, start, end)
            records = oura.parse_api(payload) if provider == "oura" else withings.parse_api(payload, height_cm=args.height_cm)
            sources.append((provider, json_bytes(payload), ".json", records))
    else:
        if args.oura_csv:
            path = Path(args.oura_csv).resolve(strict=True)
            raw = path.read_bytes()
            sources.append(("oura", raw, ".csv", parse_oura_snapshot(raw)))
        if args.withings_json:
            path = Path(args.withings_json).resolve(strict=True)
            raw = path.read_bytes()
            payload = json.loads(raw)
            reject_credentials(payload)
            if "status" in payload:
                if payload["status"] != 0:
                    raise ValueError("The Withings JSON contains an API error.")
                payload = {"measure": [payload]}
            sources.append(("withings", raw, ".json", withings.parse_api(payload, height_cm=args.height_cm)))
        if not sources:
            raise ValueError("Provide --oura-csv or --withings-json for a file import.")
        providers = [provider for provider, _, _, _ in sources]
    for provider, raw, extension, records in sources:
        # Archive only validated sources after the whole import has succeeded.
        digest = hashlib.sha256(raw).hexdigest()
        source_path = f".health-sync/raw/{provider}/{digest}{extension}"
        incoming.extend({**record, "source_file": source_path} for record in records if not (provider == "oura" and iso_date(record["day"]) >= today))
    merge = merge_records if args.command == "sync" else merge_file_records
    records = merge(load_cache(), incoming, providers, start, end)
    monthly = aggregate(records, today)
    reports = prepare_reports(monthly)
    print_summary(monthly)
    if args.dry_run:
        print("\nPreview only; records and reports were not changed.")
        return
    for provider, raw, extension, _ in sources:
        archive(provider, raw, extension)
    atomic_commit({
        CACHE / "records.json": json_bytes({"schema_version": 1, "records": records}),
        ROOT / "vitals_monthly.json": json_bytes(monthly),
        **reports,
    })
    print("\nUpdated results.md, results.html and vitals_monthly.json.")


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Show account connection and local data status without secrets")
    for name in ("connect", "authorize"):
        connection = commands.add_parser(name, help="One-time account setup" if name == "connect" else "Renew account consent")
        connection.add_argument("provider", choices=("oura", "withings"))
    for name in ("sync", "import"):
        command = commands.add_parser(name, help="Fetch connected services" if name == "sync" else "Import downloaded files")
        command.add_argument("--start", default=MANAGED_START.isoformat())
        command.add_argument("--end", help="Inclusive YYYY-MM-DD; defaults to today in Europe/Warsaw")
        command.add_argument("--height-cm", type=float, default=180.0, help="Recorded height for derived Withings BMI (default:180)")
        command.add_argument("--dry-run", action="store_true", help="Fetch, calculate and validate without updating reports")
        if name == "sync":
            command.add_argument("--provider", choices=("oura", "withings", "both"), default="both")
        else:
            command.add_argument("--oura-csv")
            command.add_argument("--withings-json", help="Saved official API JSON (all pages combined), not an arbitrary app CSV")
    return result


def main(argv=None):
    args = parser().parse_args(argv if argv is not None else (sys.argv[1:] or ["sync"]))
    try:
        from health_sync import auth
        with sync_lock():
            if args.command == "status":
                for provider, status in auth.status().items():
                    print(f"{provider}: configured={status['configured']}, authorized={status['authorized']}")
                records = load_cache()
                print(f"Local cache: {len(records)} normalized readings. July baseline protected.")
            elif args.command in ("connect", "authorize"):
                if args.command == "connect":
                    if not sys.stdin.isatty():
                        raise RuntimeError("Run connect in an interactive local terminal so the client secret can be entered privately.")
                    print("Enter the credentials from your registered developer app. Secrets are encrypted locally and never printed.")
                    client_id = input("Client ID: ").strip()
                    client_secret = getpass("Client secret: ").strip()
                    auth.configure(args.provider, client_id, client_secret)
                auth.authorize(args.provider)
                print(f"{args.provider} connected. Run Sync-Vitals.ps1 to sync.")
            else:
                run_import(args)
        return 0
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        print(f"Vitals sync stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
