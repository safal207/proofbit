import unittest

from proofbit import CachedProofProcessor, Evidence, EpistemicState


class ProofCacheTests(unittest.TestCase):
    def test_repeated_verification_hits_cache(self) -> None:
        cpu = CachedProofProcessor()
        evidence = Evidence("approved", True, 1, 1, 1)

        self.assertEqual(
            cpu.verify(evidence, consume=False), EpistemicState.PROVEN_TRUE
        )
        self.assertEqual(
            cpu.verify(evidence, consume=False), EpistemicState.PROVEN_TRUE
        )

        stats = cpu.cache_stats()
        self.assertEqual(stats.misses, 1)
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.hit_rate, 0.5)

    def test_epoch_change_does_not_reuse_old_trust(self) -> None:
        cpu = CachedProofProcessor(epoch=1)
        evidence = Evidence("approved", True, 2, 1, 1)

        self.assertEqual(
            cpu.verify(evidence, consume=False), EpistemicState.PROVEN_TRUE
        )
        cpu.epoch = 2
        self.assertEqual(cpu.verify(evidence, consume=False), EpistemicState.STALE)

        stats = cpu.cache_stats()
        self.assertEqual(stats.misses, 2)
        self.assertEqual(stats.hits, 0)

    def test_cache_never_bypasses_replay(self) -> None:
        cpu = CachedProofProcessor()
        evidence = Evidence("single_use", True, 3, 1, 1)

        # Warm the non-consuming cache first.
        self.assertEqual(
            cpu.verify(evidence, consume=False), EpistemicState.PROVEN_TRUE
        )
        self.assertEqual(
            cpu.verify(evidence, consume=True), EpistemicState.PROVEN_TRUE
        )
        self.assertEqual(cpu.verify(evidence, consume=True), EpistemicState.REPLAYED)

    def test_wrong_authority_can_be_cached_but_not_promoted(self) -> None:
        cpu = CachedProofProcessor(authority=1)
        evidence = Evidence("approved", True, 4, 2, 1)

        self.assertEqual(cpu.verify(evidence, consume=False), EpistemicState.INVALID)
        self.assertEqual(cpu.verify(evidence, consume=False), EpistemicState.INVALID)
        self.assertEqual(cpu.cache_stats().hits, 1)


if __name__ == "__main__":
    unittest.main()
