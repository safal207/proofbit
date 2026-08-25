from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "pb_trust_compose_04.py"
SPEC = importlib.util.spec_from_file_location("pb_trust_compose_04", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
pb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pb)


class PBTrustCompose04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = pb.run_benchmark(transactions=50, rounds=1, audit_sample=5)

    def test_fixed_record_and_head_sizes(self) -> None:
        self.assertEqual(pb.RECORD.size, 48)
        self.assertEqual(pb.HEAD.size, 8)

    def test_workload_covers_all_terminal_states_equally(self) -> None:
        rows = pb.build_workload(50)
        counts = {state: 0 for state in pb.STATES}
        for row in rows:
            counts[row["expected_state"]] += 1
        self.assertEqual(set(counts), set(pb.STATES))
        self.assertEqual(set(counts.values()), {10})

    def test_all_systems_survive_real_hard_crash_and_match_oracle(self) -> None:
        for system in self.report["systems"].values():
            self.assertEqual(system["oracle_accuracy"], 1.0)
            self.assertEqual(system["duplicate_side_effects_after_retry"], 0)
            self.assertEqual(system["false_terminal_success"], 0)
            self.assertEqual(system["ambiguous_terminal_states"], 0)
            self.assertEqual(system["hard_crash_exit_codes"], [pb.CRASH_EXIT_CODE])

    def test_indexed_software_is_strong_anti_strawman(self) -> None:
        systems = self.report["systems"]
        software = systems["software_indexed"]["median"]
        proof = systems["proofbit_receipts"]["median"]
        self.assertEqual(software["persisted_journal_bytes"], proof["persisted_journal_bytes"])
        self.assertEqual(software["persisted_index_bytes"], proof["persisted_index_bytes"])
        self.assertEqual(software["persisted_total_bytes"], proof["persisted_total_bytes"])

    def test_targeted_audit_penalizes_only_unindexed_scan(self) -> None:
        systems = self.report["systems"]
        scan = systems["software_scan"]["median"]["targeted_audit_records_inspected"]
        indexed = systems["software_indexed"]["median"]["targeted_audit_records_inspected"]
        proof = systems["proofbit_receipts"]["median"]["targeted_audit_records_inspected"]
        self.assertGreater(scan, indexed)
        self.assertEqual(indexed, proof)

    def test_no_single_winner_score(self) -> None:
        self.assertTrue(self.report["no_single_winner_score"])
        self.assertIn("software_indexed", self.report["comparison_rule"])


if __name__ == "__main__":
    unittest.main()
