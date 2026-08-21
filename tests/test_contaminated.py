import unittest

from benchmarks.contaminated import baseline_workload, proof_workload


class ContaminatedWorkloadTests(unittest.TestCase):
    def test_baseline_executes_adversarial_true_values(self):
        result = baseline_workload(1000)
        self.assertEqual(result["safe_actions"], 900)
        self.assertEqual(result["unsafe_actions"], 100)
        self.assertEqual(result["blocked_valid_actions"], 0)

    def test_proof_processor_blocks_adversarial_states_without_false_blocks(self):
        result = proof_workload(1000)
        self.assertEqual(result["safe_actions"], 900)
        self.assertEqual(result["unsafe_actions"], 0)
        self.assertEqual(result["blocked_valid_actions"], 0)


if __name__ == "__main__":
    unittest.main()
