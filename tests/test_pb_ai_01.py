import unittest

from proofbit.ai_workload import BACKENDS, build_workload, run_pb_ai_01


class ProofBitAIWorkloadTests(unittest.TestCase):
    def test_workload_has_exact_deterministic_contamination(self) -> None:
        first = build_workload(10_000, 0.10)
        second = build_workload(10_000, 0.10)
        self.assertEqual(first, second)
        self.assertEqual(sum(row.kind == "NORMAL" for row in first), 9_000)
        adversarial = [row.kind for row in first if row.kind != "NORMAL"]
        self.assertEqual(len(adversarial), 1_000)
        self.assertEqual(
            set(adversarial),
            {"UNKNOWN", "STALE", "REPLAY", "CONFLICT", "FALSE_SUCCESS"},
        )

    def test_cpu_reference_contrasts_value_only_and_proof_boundaries(self) -> None:
        report = run_pb_ai_01(10_000, 0.10, "cpu-python")
        baseline = report["baseline"]
        proof = report["proof"]

        self.assertEqual(report["status"], "executed")
        self.assertEqual(baseline["safe_actions"], 9_000)
        self.assertEqual(proof["safe_actions"], 9_000)
        self.assertEqual(baseline["unsafe_actions"], 1_000)
        self.assertEqual(proof["unsafe_actions"], 0)
        self.assertEqual(baseline["proof_coverage"], 0.0)
        self.assertEqual(proof["proof_coverage"], 1.0)
        self.assertEqual(proof["blocked_valid_actions"], 0)
        self.assertEqual(proof["false_positive_block_rate"], 0.0)
        self.assertEqual(proof["prevented_unsafe_actions"], 1_000)

    def test_external_backends_are_explicitly_not_run(self) -> None:
        for backend_id, info in BACKENDS.items():
            if info.executable:
                continue
            report = run_pb_ai_01(100, 0.10, backend_id)
            self.assertEqual(report["status"], "not-run")
            self.assertEqual(report["backend"]["id"], backend_id)

    def test_invalid_inputs_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            build_workload(0, 0.10)
        with self.assertRaises(ValueError):
            build_workload(100, -0.01)
        with self.assertRaises(ValueError):
            build_workload(100, 1.01)
        with self.assertRaises(ValueError):
            run_pb_ai_01(100, 0.10, "not-a-backend")


if __name__ == "__main__":
    unittest.main()
