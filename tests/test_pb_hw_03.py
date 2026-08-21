import unittest

from benchmarks import pb_hw_03 as hw


class PBHW03Tests(unittest.TestCase):
    def test_protocol_identity(self):
        self.assertEqual(hw.BENCHMARK_ID, "PB-HW-03")
        self.assertEqual(hw.VERSION, "0.1")
        self.assertEqual(hw.PROTOCOL, "PB-HW-03/v0.1 composition-economics")
        self.assertEqual(len(hw.GUARANTEES), 9)

    def test_strong_anti_strawman_has_same_semantic_contract(self):
        self.assertEqual(hw.GUARANTEE_COVERAGE["vector_conventional"], 9)
        self.assertEqual(hw.GUARANTEE_COVERAGE["proofbit_compose"], 9)
        self.assertEqual(
            hw.INSTRUCTION_TRANSACTIONS_PER_TRUSTED_TERMINAL["vector_conventional"],
            hw.INSTRUCTION_TRANSACTIONS_PER_TRUSTED_TERMINAL["proofbit_compose"],
        )
        self.assertEqual(hw.PARENT_READ_ISSUE_CYCLES["vector_conventional"], 1)
        self.assertEqual(hw.PARENT_READ_ISSUE_CYCLES["proofbit_compose"], 1)

    def test_scalar_vs_primitive_economics_are_frozen(self):
        self.assertEqual(hw.INSTRUCTION_TRANSACTIONS_PER_TRUSTED_TERMINAL["scalar_conventional"], 6)
        self.assertEqual(hw.INSTRUCTION_TRANSACTIONS_PER_TRUSTED_TERMINAL["vector_conventional"], 2)
        self.assertEqual(hw.LOGICAL_PARENT_READS_PER_TERMINAL["scalar_conventional"], 4)
        self.assertEqual(hw.LOGICAL_PARENT_READS_PER_TERMINAL["vector_conventional"], 4)
        self.assertEqual(hw.PARENT_READ_ISSUE_CYCLES["scalar_conventional"], 4)
        self.assertEqual(hw.PARENT_READ_ISSUE_CYCLES["vector_conventional"], 1)
        self.assertEqual(hw.LOGICAL_DERIVED_WRITES_PER_TERMINAL["scalar_conventional"], 1)
        self.assertEqual(hw.LOGICAL_DERIVED_WRITES_PER_TERMINAL["vector_conventional"], 1)
        self.assertEqual(hw.LOGICAL_OUTCOME_WRITES_PER_TERMINAL["scalar_conventional"], 1)
        self.assertEqual(hw.LOGICAL_OUTCOME_WRITES_PER_TERMINAL["vector_conventional"], 1)

    def test_sim_marker_parser(self):
        sample = (
            "PB_HW03_SIM PASS safety=14 scalar_fail=0 conv_fail=0 proof_fail=0 "
            "scalar_tx=96 vector_tx=32 scalar_terminal=16 conv_terminal=16 "
            "proof_terminal=16 stalls=0"
        )
        parsed = hw.parse_sim(sample)
        self.assertEqual(parsed["safety_cases"], 14)
        self.assertEqual(parsed["scalar_stream_transactions"], 96)
        self.assertEqual(parsed["vector_stream_transactions"], 32)
        self.assertEqual(parsed["proofbit_trusted_terminals"], 16)

    def test_ltp_parser(self):
        self.assertEqual(hw.parse_ltp("Longest topological path: length 27"), 27)
        self.assertEqual(hw.parse_ltp("length 9\nlength 14"), 14)


if __name__ == "__main__":
    unittest.main()
