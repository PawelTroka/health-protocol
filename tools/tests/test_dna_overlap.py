import gzip
import tempfile
import unittest
from pathlib import Path

from tools.review_dna_overlap import review


ARRAY_HEADER = "RSID,CHROMOSOME,POSITION,RESULT\n"
SENTINEL = "rs7412,19,45412079,--\n"
MULTIPLE = "criteria_provided,_multiple_submitters,_no_conflicts"


def variant(pos, marker, ref="A", alt="G", classification="Pathogenic",
            level=MULTIPLE, chrom="1", extra=""):
    info = f"RS={marker};CLNREVSTAT={level};CLNSIG={classification}{extra}"
    return f"{chrom}\t{pos}\t{pos}\t{ref}\t{alt}\t.\t.\t{info}\n"


class DnaOverlapTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.array = Path(temp.name) / "array.gz"
        self.vcf = Path(temp.name) / "clinvar.gz"

    def check(self, probes, variants, build="GRCh37", sentinel=SENTINEL):
        with gzip.open(self.array, "wt", encoding="utf-8") as output:
            output.write(ARRAY_HEADER + sentinel + probes)
        with gzip.open(self.vcf, "wt", encoding="utf-8") as output:
            output.write(f"##source=ClinVar\n##reference={build}\n")
            output.write("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n")
            output.write("".join(variants))
        return review(self.array, self.vcf)

    def test_only_exact_compatible_calls_are_reported(self):
        result = self.check(
            "rs1,1,1,AG\nrs2,1,2,AA\nprobe,1,3,GG\nrs4,1,4,GG\n"
            "rs5,1,5,--\nrs6,1,6,AT\nrs7,1,7,CT\nrs9,1,9,G\nrs10,X,10,G\n",
            [variant(1, "999|1"), variant(2, 2), variant(3, 3), variant(4, 444),
             variant(5, 5), variant(6, 6, alt="T"), variant(7, 7), variant(8, 8),
             variant(9, 9), variant(10, 10, chrom="X")],
        )
        self.assertEqual(result["eligible_autosomal_x_snv_records"], 10)
        self.assertEqual(result["status_counts"], {
            "alternate_candidate": 2, "reference_only": 1, "custom_probe": 1,
            "rsid_mismatch_or_missing": 1, "no_call": 1, "palindromic_site": 1,
            "incompatible_call": 2, "absent_coordinate": 1,
        })
        self.assertEqual([item["rsid"] for item in result["alternate_candidates"]], ["rs1", "rs10"])

    def test_germline_evidence_filters_and_distinct_alleles_at_one_locus(self):
        result = self.check("rs1,1,1,AG\n", [
            variant(1, 1, classification="drug_response|Pathogenic/Likely_pathogenic"),
            variant(1, 1, alt="C", classification="Likely_pathogenic,_low_penetrance"),
            variant(2, 2, classification="Pathogenic,_low_penetrance"),
            variant(3, 3, classification="Established_risk_allele", level="reviewed_by_expert_panel"),
            variant(4, 4, classification="Likely_risk_allele", level="practice_guideline"),
            variant(5, 5, classification="Uncertain_risk_allele"),
            variant(6, 6, classification="risk_factor"),
            variant(7, 7, level="criteria_provided,_single_submitter",
                    extra=";ONCREVSTAT=reviewed_by_expert_panel"),
            variant(8, 8, ref="AA"), variant(9, 9, alt="G,T"), variant(10, 10, chrom="Y"),
        ])
        self.assertEqual(result["vcf_records"], 11)
        self.assertEqual(result["status_counts"], {
            "alternate_candidate": 1, "incompatible_call": 1, "absent_coordinate": 3,
            "reference_only": 0,
        })

    def test_requires_matching_build_and_recognized_export(self):
        for build, sentinel in [
            ("GRCh38", SENTINEL),
            ("GRCh37", "rs7412,19,44908822,AA\n"),
            ("GRCh37", ""),
        ]:
            with self.subTest(build=build, sentinel=sentinel), self.assertRaises(ValueError):
                self.check("rs1,1,1,AG\n", [variant(1, 1)], build, sentinel)

    def test_single_submitter_comparison_keeps_evidence_groups_separate(self):
        primary = self.check("rs1,1,1,AG\nrs2,1,2,GG\n", [
            variant(1, 1, level="criteria_provided,_single_submitter"),
            variant(2, 2, level="reviewed_by_expert_panel"),
        ])
        secondary = review(self.array, self.vcf, single_submitter=True)
        self.assertEqual([row["rsid"] for row in primary["alternate_candidates"]], ["rs2"])
        self.assertEqual([row["rsid"] for row in secondary["alternate_candidates"]], ["rs1"])

    def test_somatic_only_and_below_threshold_records_do_not_create_candidates(self):
        result = self.check("rs1,1,1,AG\n", [
            variant(1, 1, classification="Uncertain_significance",
                    extra=";ONC=Oncogenic;ONCREVSTAT=reviewed_by_expert_panel"),
            variant(2, 2, classification="Conflicting_classifications_of_pathogenicity"),
        ])
        self.assertEqual(result["eligible_autosomal_x_snv_records"], 0)
        self.assertEqual(result["status_counts"]["alternate_candidate"], 0)
        self.assertEqual(result["alternate_candidates"], [])

    def test_duplicate_input_does_not_overwrite_evidence(self):
        for probes, variants in [
            ("rs1,1,1,AG\nrs2,1,1,GG\n", [variant(1, 1)]),
            ("rs1,1,1,AG\nrs1,2,1,GG\n", [variant(1, 1)]),
            ("rs1,1,1,AG\n", [variant(1, 1), variant(1, 1)]),
        ]:
            with self.subTest(probes=probes, variants=variants), self.assertRaisesRegex(ValueError, "Duplicate"):
                self.check(probes, variants)


if __name__ == "__main__":
    unittest.main()
