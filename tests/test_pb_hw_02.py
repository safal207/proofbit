import unittest

from benchmarks import pb_hw_02 as hw


class PBHW02Tests(unittest.TestCase):
    def test_contract_identity(self):
        self.assertEqual(hw.BENCHMARK_ID, "PB-HW-02")
        self.assertEqual(hw.VERSION, "0.1")
        self.assertEqual(hw.PROTOCOL, "PB-HW-02/v0.1 semantic-cost-curve")

    def test_semantic_curve_is_not_a_strawman(self):
        self.assertEqual(len(hw.GUARANTEES), 9)
        self.assertEqual(hw.GUARANTEE_COVERAGE["minimal_capability"], 5)
        self.assertEqual(hw.GUARANTEE_COVERAGE["full_conventional"], 9)
        self.assertEqual(hw.GUARANTEE_COVERAGE["rich_proofbit"], 9)
        self.assertEqual(hw.LOGICAL_METADATA_BITS["minimal_capability"], 41)
        self.assertEqual(hw.LOGICAL_METADATA_BITS["full_conventional"], 60)
        self.assertEqual(hw.LOGICAL_METADATA_BITS["rich_proofbit"], 60)
        self.assertEqual(hw.LOGICAL_STATE_BITS["minimal_capability"], 139)
        self.assertEqual(hw.LOGICAL_STATE_BITS["full_conventional"], 278)
        self.assertEqual(hw.LOGICAL_STATE_BITS["rich_proofbit"], 278)

    def test_terminal_outcome_accounting(self):
        self.assertIsNone(hw.TRANSACTIONS_PER_TRUSTED_TERMINAL["minimal_capability"])
        self.assertEqual(hw.TRANSACTIONS_PER_TRUSTED_TERMINAL["full_conventional"], 2)
        self.assertEqual(hw.TRANSACTIONS_PER_TRUSTED_TERMINAL["rich_proofbit"], 2)

    def test_sim_marker_parser(self):
        row = hw.parse_sim(
            "PB_HW02_SIM PASS safety=14 min_fail=0 semantic_gaps=4 conv_fail=0 "
            "proof_fail=0 min_stream=32 rich_transactions=32 trusted_terminal=16 stalls=0"
        )
        self.assertEqual(row["rich_safety_cases"], 14)
        self.assertEqual(row["minimal_semantic_gap_accepts"], 4)
        self.assertEqual(row["trusted_terminal_effects"], 16)
        self.assertEqual(row["stalls"], 0)

    def test_ltp_parser(self):
        self.assertEqual(hw.parse_ltp("Longest topological path in pb: length 17"), 17)
        self.assertEqual(hw.parse_ltp("path length=3\npath length 19"), 19)


if __name__ == "__main__":
    unittest.main()
