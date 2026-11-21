"""Measurement-group provenance for Withings body-component comparisons.

Equal dates and reading counts cannot establish that two monthly quantities
came from the same scale readings. Publish only an opaque membership digest;
the actual group identifiers remain in the private normalized records.
"""

from datetime import datetime
import hashlib
import json
import re


COMPOSITION_MASSES = frozenset({
    "Body Mass", "Fat Mass (Withings)", "Muscle Mass (Withings)",
    "Bone Mass (Withings)", "Fat-Free Mass (Withings)", "Water Mass (Withings)",
})
GROUP_DIGEST = "measurement_groups_sha256"


def _canonical_timestamp(value, day=None):
    if not isinstance(value, str):
        return False
    try:
        stamp = datetime.fromisoformat(value)
        return (stamp.utcoffset() is not None and stamp.isoformat() == value
                and (day is None or stamp.date().isoformat() == day))
    except ValueError:
        return False


def composition_group_digest(records):
    """Fingerprint every contributing group, or withhold incomplete provenance."""
    if not records or records[0]["metric"] not in COMPOSITION_MASSES:
        return None
    metric = records[0]["metric"]
    members = []
    for record in records:
        group = record.get("group_id")
        recorded = record.get("recorded_at")
        modified = record.get("source_modified_at")
        if (record["provider"] != "withings" or record["metric"] != metric
                or record.get("source_kind") != "api"
                or not isinstance(group, str) or not group or group != group.strip()
                or record["id"] != f"withings:measure:{group}:{metric}"
                or record.get("source_count", 1) != 1
                or not _canonical_timestamp(recorded, record["day"])
                or ("source_modified_at" in record and not _canonical_timestamp(modified))):
            return None
        # Unknown revision timestamps stay explicit nulls. A known revision
        # cannot match an unknown or different revision of the same group.
        members.append((record["day"], group, recorded, modified))
    if len({member[:2] for member in members}) != len(members):
        return None
    encoded = json.dumps(sorted(members), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def valid_group_provenance(entry):
    """Recognize the optional, complete API-group metadata on a monthly cell."""
    digest = entry.get(GROUP_DIGEST)
    return (entry.get("provider") == "withings"
            and entry.get("source_kinds") == ["api"]
            and type(entry.get("n_records")) is int and entry["n_records"] > 0
            and isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None)


def matched_composition_groups(first, second):
    return (valid_group_provenance(first) and valid_group_provenance(second)
            and first["n_records"] == second["n_records"]
            and first[GROUP_DIGEST] == second[GROUP_DIGEST])
