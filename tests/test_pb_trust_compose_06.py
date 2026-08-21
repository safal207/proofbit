from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "pb_trust_compose_06.py"
SPEC = importlib.util.spec_from_file_location("pb_trust_compose_06", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
pb = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pb
SPEC.loader.exec_module(pb)


class PBTrustCompose06Tests(unittest.TestCase):
    def test_policy_evolution_is_cumulative_and_frozen(self) -> None:
        expected = [
            pb.STATEMENT | pb.AUTHORITY,
            pb.STATEMENT | pb.AUTHORITY | pb.EPOCH,
            pb.STATEMENT | pb.AUTHORITY | pb.EPOCH | pb.REPLAY,
            pb.STATEMENT | pb.AUTHORITY | pb.EPOCH | pb.REPLAY | pb.PROVENANCE,
            pb.STATEMENT
            | pb.AUTHORITY
            | pb.EPOCH
            | pb.REPLAY
            | pb.PROVENANCE
            | pb.OUTCOME,
        ]
        self.assertEqual([policy.required_mask for policy in pb.POLICIES], expected)
        self.assertEqual([policy.version for policy in pb.POLICIES], [1, 2, 3, 4, 5])

    def test_workload_contains_every_pressure_case(self) -> None:
        workloads = pb.build_workload(700)
        for rows in workloads.values():
            self.assertEqual(len(rows), 700)
            self.assertEqual({row.fault for row in rows}, set(pb.FAULTS))

    def test_all_strong_controls_match_oracle_after_safe_activation(self) -> None:
        report = pb.run_benchmark(requests_per_version=700, components=4, rounds=1)
        for name, result in report["runtime"].items():
            self.assertEqual(result["oracle_accuracy"], 1.0, name)
            self.assertEqual(result["unsafe_accepts"], 0, name)
            self.assertEqual(result["false_terminal_success"], 0, name)
            self.assertEqual(result["missed_valid"], 0, name)

    def test_shared_software_is_equal_representation_anti_strawman(self) -> None:
        self.assertEqual(pb.POLICY_STRUCT.size, 16)
        self.assertEqual(pb.TOKEN_STRUCT.size, 32)
        report = pb.run_benchmark(requests_per_version=140, components=4, rounds=1)
        shared = report["evolution_work"]["software_shared_registry"]
        proof = report["evolution_work"]["proofbit_contract"]
        self.assertEqual(shared["active_policy_descriptor_bytes"], proof["active_policy_descriptor_bytes"])
        self.assertEqual(shared["propagated_receipt_bytes"], proof["propagated_receipt_bytes"])
        self.assertEqual(shared["policy_copy_updates"], proof["policy_copy_updates"])
        self.assertEqual(shared["regression_suite_invocations"], proof["regression_suite_invocations"])

    def test_independent_policy_copies_pay_replication_work_not_silent_drift(self) -> None:
        work = pb.evolution_work(components=4)
        shared = work["software_shared_registry"]
        independent = work["software_independent_copies"]
        proof = work["proofbit_contract"]

        self.assertEqual(shared["policy_copy_updates"], 4)
        self.assertEqual(proof["policy_copy_updates"], 4)
        self.assertEqual(independent["policy_copy_updates"], 16)
        self.assertEqual(independent["safe_activation_steps"], 16)
        self.assertEqual(independent["regression_suite_invocations"], 16)
        self.assertEqual(independent["regression_suite_failures"], 0)
        self.assertEqual(independent["semantic_drift_after_safe_activation"], 0)

    def test_early_activation_probe_fails_closed(self) -> None:
        stress = pb.evolution_work(components=4)["software_independent_copies"]["early_activation_stress"]
        self.assertEqual(stress["phases"], 12)
        self.assertEqual(stress["valid_probes"], 1200)
        self.assertEqual(stress["valid_blocks"], 1200)
        self.assertEqual(stress["unsafe_accepts"], 0)

    def test_new_primitive_is_outside_claim_boundary(self) -> None:
        report = pb.run_benchmark(requests_per_version=70, components=2, rounds=1)
        self.assertIn("new trust primitive", report["claim_boundary"])
        self.assertTrue(report["no_single_winner_score"])
        self.assertEqual(report["primary_anti_strawman"], "software_shared_registry")


if __name__ == "__main__":
    unittest.main()
