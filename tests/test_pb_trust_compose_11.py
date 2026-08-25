from __future__ import annotations

import unittest

from benchmarks import pb_trust_compose_11 as tc


class PBTrustCompose11Tests(unittest.TestCase):
    def test_frozen_isa_surface(self):
        self.assertEqual(len(tc.OPS), 8)
        self.assertEqual(len(tc.SCENARIOS), 6)
        self.assertIn("FORGE", tc.OPS)
        self.assertIn("EFFECT_B", tc.OPS)

    def test_flat_machine_has_bypass_surface(self):
        row = tc.exhaustive_search("flat_value_machine", 3)
        self.assertGreater(row["total_bypass_programs"], 0)
        self.assertEqual(row["scenarios_with_bypass"], len(tc.SCENARIOS))

    def test_tagged_capability_blocks_bounded_unprivileged_search(self):
        row = tc.exhaustive_search("tagged_capability_machine", 3)
        self.assertEqual(row["total_bypass_programs"], 0)
        self.assertEqual(row["scenarios_with_bypass"], 0)

    def test_proofbit_blocks_bounded_unprivileged_search(self):
        row = tc.exhaustive_search("proofbit_machine", 3)
        self.assertEqual(row["total_bypass_programs"], 0)
        self.assertEqual(row["scenarios_with_bypass"], 0)

    def test_privileged_escape_classes_are_explicit_and_unscored(self):
        for system in tc.SYSTEMS:
            row = tc.privileged_escape_probe(system)
            self.assertTrue(row["debug_bypass_effect"])
            self.assertTrue(row["dma_bypass_effect"])
            self.assertTrue(row["privileged_mint_effect"])
            self.assertFalse(row["scored"])

    def test_conventional_tagged_machine_is_primary_anti_strawman(self):
        r = tc.run(max_program_len=2, valid_iterations=10, rounds=1)
        self.assertEqual(r["primary_anti_strawman"], "tagged_capability_machine")
        self.assertTrue(r["logical_metadata"]["tagged_capability_machine"]["unforgeable_tag"])
        self.assertTrue(r["logical_metadata"]["proofbit_machine"]["unforgeable_tag"])
        self.assertIn("model axiom", r["tag_axiom"])

    def test_valid_path_remains_available(self):
        for system in tc.SYSTEMS:
            row = tc.valid_path(system, 20)
            self.assertEqual(row["effects"], 20)
            self.assertGreater(row["effects_per_sec"], 0)


if __name__ == "__main__":
    unittest.main()
