from __future__ import annotations

import unittest

from benchmarks import pb_trust_compose_12 as tc


class PBTrustCompose12Tests(unittest.TestCase):
    def test_frozen_whole_system_scenarios(self):
        self.assertEqual(len(tc.SCENARIOS), 6)
        self.assertEqual(tc.CHANNELS, ("cpu", "debug", "dma"))
        self.assertIn("CACHE_TAG_DATA_SPLIT", tc.SCENARIOS)
        self.assertIn("SNAPSHOT_REPLAY_ROLLBACK", tc.SCENARIOS)

    def test_cpu_only_tag_machine_fails_cross_domain_matrix(self):
        row = tc.scored_matrix("cpu_only_tag_machine")
        self.assertEqual(row["unsafe_effects"], 6)
        self.assertEqual(row["blocked_attacks"], 0)
        self.assertEqual(row["oracle_accuracy"], 0.0)

    def test_whole_system_capability_blocks_all_scored_attacks(self):
        row = tc.scored_matrix("whole_system_capability_machine")
        self.assertEqual(row["unsafe_effects"], 0)
        self.assertEqual(row["blocked_attacks"], 6)
        self.assertEqual(row["oracle_accuracy"], 1.0)

    def test_whole_system_proofbit_blocks_all_scored_attacks(self):
        row = tc.scored_matrix("whole_system_proofbit_machine")
        self.assertEqual(row["unsafe_effects"], 0)
        self.assertEqual(row["blocked_attacks"], 6)
        self.assertEqual(row["oracle_accuracy"], 1.0)

    def test_strong_conventional_control_gets_equal_coherence_axiom(self):
        report = tc.run(rounds=1, valid_iterations=12)
        self.assertEqual(
            report["primary_anti_strawman"],
            "whole_system_capability_machine",
        )
        cap = report["logical_metadata"]["whole_system_capability_machine"]
        proof = report["logical_metadata"]["whole_system_proofbit_machine"]
        self.assertEqual(cap["enforced_domains"], proof["enforced_domains"])
        self.assertTrue(cap["global_replay_state"])
        self.assertTrue(proof["global_replay_state"])
        self.assertIn("model axiom", report["coherence_axiom"])

    def test_deeper_escape_boundary_is_explicit(self):
        for system in tc.SYSTEMS:
            probe = tc.deeper_escape_probe(system)
            self.assertTrue(probe["physical_tag_store_tamper_bypass"])
            self.assertTrue(probe["malicious_firmware_bypass"])
            self.assertFalse(probe["scored"])

    def test_valid_cpu_debug_dma_paths_remain_available(self):
        for system in tc.SYSTEMS:
            row = tc.valid_path(system, 30)
            self.assertEqual(row["effects"], 30)
            self.assertGreater(row["effects_per_sec"], 0)


if __name__ == "__main__":
    unittest.main()
