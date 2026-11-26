"""Compare a local Family Finder Build 37 export with a local GRCh37 ClinVar VCF."""

import argparse
import csv
import gzip
import json
import re
from collections import Counter


CHROMOSOMES = {str(n) for n in range(1, 23)} | {"X"}
BUILD_37 = {
    "rs4988235": ("2", 136608646),
    "rs2228479": ("16", 89985940),
    "rs7412": ("19", 45412079),
}
REVIEW_LEVELS = {
    "criteria_provided,_multiple_submitters,_no_conflicts",
    "reviewed_by_expert_panel",
    "practice_guideline",
}
CLASSIFICATIONS = {
    "Pathogenic", "Likely_pathogenic",
    "Pathogenic,_low_penetrance", "Likely_pathogenic,_low_penetrance",
    "Established_risk_allele", "Likely_risk_allele",
}
RSID = re.compile(r"rs[0-9]+")
BASES = set("ACGT")


def read_export(path):
    calls = {}
    seen_ids = set()
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream)
        if next(rows, []) != ["RSID", "CHROMOSOME", "POSITION", "RESULT"]:
            raise ValueError("Expected the Family Finder CSV header")
        for marker, chrom, position, call in rows:
            locus = (chrom, int(position))
            if chrom not in CHROMOSOMES or locus[1] < 1:
                raise ValueError("Expected autosomal and X-chromosome coordinates")
            if locus in calls or marker in seen_ids:
                raise ValueError(f"Duplicate export coordinate or marker at {chrom}:{position}")
            if marker in BUILD_37 and locus != BUILD_37[marker]:
                raise ValueError(f"{marker} does not match GRCh37")
            seen_ids.add(marker)
            calls[locus] = (marker, call)
    if not seen_ids.intersection(BUILD_37):
        raise ValueError("No recognized GRCh37 marker found to check the export build")
    return calls


def match_call(probe, chrom, ref, alt, ref_ids):
    if probe is None:
        return "absent_coordinate"
    marker, call = probe
    if not RSID.fullmatch(marker):
        return "custom_probe"
    if marker[2:] not in ref_ids:
        return "rsid_mismatch_or_missing"
    if call in {"--", "-", "", "00"}:
        return "no_call"
    if {ref, alt} in ({"A", "T"}, {"C", "G"}):
        return "palindromic_site"
    valid_length = len(call) == 2 or (chrom == "X" and len(call) == 1)
    if not valid_length or not set(call) <= {ref, alt}:
        return "incompatible_call"
    return "alternate_candidate" if alt in call else "reference_only"


def review(export_path, clinvar_path, *, single_submitter=False):
    calls = read_export(export_path)
    review_levels = {"criteria_provided,_single_submitter"} if single_submitter else REVIEW_LEVELS
    counts = Counter(alternate_candidate=0, reference_only=0)
    candidates = []
    seen_alleles = set()
    metadata = {}
    header = False
    records = 0
    with gzip.open(clinvar_path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if line.startswith("##"):
                name, _, value = line[2:].rstrip().partition("=")
                if name in {"source", "reference", "fileDate"}:
                    metadata[name] = value
                continue
            if line.startswith("#CHROM"):
                if metadata.get("source") != "ClinVar" or metadata.get("reference") != "GRCh37":
                    raise ValueError("Expected a ClinVar VCF with ##reference=GRCh37")
                if line.rstrip().split("\t") != [
                    "#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO",
                ]:
                    raise ValueError("Unexpected ClinVar VCF columns")
                header = True
                continue
            if not header:
                raise ValueError("Missing ClinVar VCF header")
            records += 1
            chrom, pos, variation_id, ref, alt, _, _, info = line.rstrip().split("\t", 7)
            if chrom not in CHROMOSOMES or ref not in BASES or alt not in BASES or ref == alt:
                continue
            if not any(review_level in info for review_level in review_levels):
                continue
            fields = dict(part.split("=", 1) for part in info.split(";") if "=" in part)
            classification = fields.get("CLNSIG", "")
            if fields.get("CLNREVSTAT") not in review_levels:
                continue
            if not CLASSIFICATIONS.intersection(re.split(r"[|/]", classification)):
                continue
            locus = (chrom, int(pos))
            allele = (*locus, ref, alt)
            if allele in seen_alleles:
                raise ValueError(f"Duplicate eligible ClinVar allele at {chrom}:{pos}")
            seen_alleles.add(allele)
            probe = calls.get(locus)
            status = match_call(probe, chrom, ref, alt, re.split(r"[,|]", fields.get("RS", "")))
            counts[status] += 1
            if status == "alternate_candidate":
                candidates.append({
                    "rsid": probe[0], "chromosome": chrom, "position": locus[1],
                    "call": probe[1], "ref": ref, "alt": alt, "variation_id": variation_id,
                    "classification": classification, "review_status": fields["CLNREVSTAT"],
                })
    if not header or not records:
        raise ValueError("Empty or incomplete ClinVar VCF")
    return {
        "reference": metadata, "germline_review_levels": sorted(review_levels),
        "export_rows": len(calls), "vcf_records": records,
        "eligible_autosomal_x_snv_records": sum(counts.values()),
        "status_counts": counts, "alternate_candidates": candidates,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", help="Local Family Finder autosomal/X CSV.gz")
    parser.add_argument("clinvar", help="Local GRCh37 ClinVar VCF.gz")
    parser.add_argument("--single-submitter", action="store_true",
                        help="Review only the separate one-star, single-submitter group")
    args = parser.parse_args()
    try:
        result = review(args.export, args.clinvar, single_submitter=args.single_submitter)
    except (OSError, EOFError, ValueError, csv.Error) as error:
        parser.exit(1, f"Review failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
