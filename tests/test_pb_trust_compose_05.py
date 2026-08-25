from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "pb_trust_compose_05.py"
SPEC = importlib.util.spec_from_file_location("pb_trust_compose_05", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
pb = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pb
SPEC.loader.exec_module(pb)


class PBTrustCompose05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = pb.run_benchmark(rounds=1)

    def test_equal_integrity_record_and_index_widths(self) -> None:
        self.assertEqual(pb.RECORD.size, 56)
        self.assertEqual(pb.HEAD.size, 8)
        self.assertIn("same 56-byte", self.report["fairness"])

    def test_fault_matrix_is_frozen(self) -> None:
        self.assertEqual(len(pb.FAULTS), 8)
        self.assertEqual(pb.EXPECTED["CLEAN"], "PROVEN")
        self.assertEqual(
            pb.EXPECTED["HEAD_UPDATED_RECORD_TRUNCATED"], "UNKNOWN"
        )
        self.assertEqual(
            pb.EXPECTED["STATEMENT_REBOUND_IN_DURABLE_RECORD"], "UNKNOWN"
        )
        self.assertEqual(
            pb.EXPECTED["EPOCH_REBOUND_IN_DURABLE_RECORD"], "UNKNOWN"
        )
        self.assertEqual(
            pb.EXPECTED["DUPLICATE_CONFLICTING_OUTCOME_RECEIPT"], "CONFLICT"
        )

    def test_head_faults_are_not_falsely_scored_against_scan_only_system(self) -> None:
        self.assertFalse(
            pb.fault_applicable(
                "software_scan_repair", "JOURNAL_WRITTEN_HEAD_NOT_UPDATED"
            )
        )
        self.assertFalse(
            pb.fault_applicable(
                "software_scan_repair", "STALE_HEAD_AFTER_RESTART"
            )
        )
        self.assertTrue(
            pb.fault_applicable(
                "software_indexed_integrity", "STALE_HEAD_AFTER_RESTART"
            )
        )

    def test_all_applicable_cases_avoid_silent_false_reconstruction(self) -> None:
        for system in self.report["systems"].values():
            self.assertEqual(system["oracle_accuracy"], 1.0)
            self.assertEqual(system["silent_false_reconstruction"], 0)

    def test_strong_indexed_control_matches_proofbit_correctness(self) -> None:
        indexed = self.report["systems"]["software_indexed_integrity"]
        proof = self.report["systems"]["proofbit_receipts"]
        self.assertEqual(indexed["oracle_accuracy"], proof["oracle_accuracy"])
        self.assertEqual(
            indexed["silent_false_reconstruction"],
            proof["silent_false_reconstruction"],
        )
        self.assertEqual(
            indexed["applicable_cases_per_round"], proof["applicable_cases_per_round"]
        )

    def test_semantic_rebinding_degrades_to_unknown(self) -> None:
        for system_name in ("software_indexed_integrity", "proofbit_receipts"):
            cases = {
                case["fault"]: case
                for case in self.report["systems"][system_name]["case_results"]
            }
            self.assertEqual(
                cases["STATEMENT_REBOUND_IN_DURABLE_RECORD"]["recovered_state"],
                "UNKNOWN",
            )
            self.assertEqual(
                cases["EPOCH_REBOUND_IN_DURABLE_RECORD"]["recovered_state"],
                "UNKNOWN",
            )
            self.assertGreater(
                cases["STATEMENT_REBOUND_IN_DURABLE_RECORD"]["detected_corruption"],
                0,
            )

    def test_conflicting_outcome_is_not_silently_collapsed(self) -> None:
        for system in self.report["systems"].values():
            cases = {case["fault"]: case for case in system["case_results"]}
            self.assertEqual(
                cases["DUPLICATE_CONFLICTING_OUTCOME_RECEIPT"]["recovered_state"],
                "CONFLICT",
            )

    def test_no_single_winner_score(self) -> None:
        self.assertTrue(self.report["no_single_winner_score"])
        self.assertEqual(
            self.report["primary_comparison"],
            "software_indexed_integrity vs proofbit_receipts",
        )


if __name__ == "__main__":
    unittest.main()
