import unittest

from proofbit import BaselineProcessor, Evidence, EpistemicState, ProofProcessor


class ProofBitSafetyTests(unittest.TestCase):
    def test_normal_is_allowed(self):
        cpu = ProofProcessor()
        cpu.store_evidence(0, Evidence("ok", True, 1, 1, 1))
        self.assertTrue(cpu.guarded_execute(0))

    def test_unknown_is_blocked(self):
        cpu = ProofProcessor()
        cpu.store_unknown(0, "unknown", True)
        self.assertFalse(cpu.guarded_execute(0))

    def test_stale_is_blocked(self):
        cpu = ProofProcessor(epoch=2)
        cpu.store_evidence(0, Evidence("stale", True, 2, 1, 1))
        self.assertEqual(cpu.load(0).state, EpistemicState.STALE)
        self.assertFalse(cpu.guarded_execute(0))

    def test_replay_is_blocked(self):
        cpu = ProofProcessor()
        cpu.store_evidence(0, Evidence("once", True, 3, 1, 1))
        self.assertTrue(cpu.guarded_execute(0))
        self.assertFalse(cpu.guarded_execute(0))
        self.assertEqual(cpu.load(0).state, EpistemicState.REPLAYED)

    def test_conflict_is_blocked(self):
        cpu = ProofProcessor()
        cpu.store_conflict(0, "conflict")
        self.assertFalse(cpu.guarded_execute(0))

    def test_false_success_without_outcome_evidence_is_blocked(self):
        cpu = ProofProcessor()
        cpu.record_claimed_success_without_outcome_evidence(0, "success")
        self.assertFalse(cpu.guarded_execute(0))


class BaselineContrastTests(unittest.TestCase):
    def test_value_only_model_cannot_distinguish_unknown_true_claim(self):
        cpu = BaselineProcessor()
        cpu.store(0, True)
        self.assertTrue(cpu.guarded_execute(0))


if __name__ == "__main__":
    unittest.main()
