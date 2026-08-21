from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from .model import EpistemicState, Evidence, ProofProcessor


CacheKey = Tuple[str, bool, int, int, int, int, int]


@dataclass(frozen=True)
class ProofCacheStats:
    hits: int
    misses: int

    @property
    def requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        return self.hits / self.requests if self.requests else 0.0


class CachedProofProcessor(ProofProcessor):
    """ProofProcessor with a context-bound verification-result cache.

    The cache never bypasses replay/consumption checks. Cached entries are bound
    to the evidence payload and to the processor authority/epoch context, so a
    context change produces a cache miss rather than reusing stale trust.
    """

    def __init__(self, authority: int = 1, epoch: int = 1) -> None:
        super().__init__(authority=authority, epoch=epoch)
        self._proof_cache: Dict[CacheKey, EpistemicState] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def _cache_key(self, evidence: Evidence) -> CacheKey:
        return (
            evidence.statement,
            evidence.value,
            evidence.proof_id,
            evidence.authority,
            evidence.epoch,
            self.authority,
            self.epoch,
        )

    def _verify_without_replay(self, evidence: Evidence) -> EpistemicState:
        key = self._cache_key(evidence)
        cached = self._proof_cache.get(key)
        if cached is not None:
            self.cache_hits += 1
            return cached

        self.cache_misses += 1
        if evidence.authority != self.authority:
            state = EpistemicState.INVALID
        elif evidence.epoch != self.epoch:
            state = EpistemicState.STALE
        else:
            state = (
                EpistemicState.PROVEN_TRUE
                if evidence.value
                else EpistemicState.PROVEN_FALSE
            )
        self._proof_cache[key] = state
        return state

    def verify(self, evidence: Evidence, *, consume: bool) -> EpistemicState:
        # Replay state is consumption-specific and is intentionally not cached.
        if evidence.proof_id in self.consumed_proofs:
            return EpistemicState.REPLAYED

        state = self._verify_without_replay(evidence)
        if consume and state in (
            EpistemicState.PROVEN_TRUE,
            EpistemicState.PROVEN_FALSE,
        ):
            self.consumed_proofs.add(evidence.proof_id)
        return state

    def clear_proof_cache(self) -> None:
        self._proof_cache.clear()

    def cache_stats(self) -> ProofCacheStats:
        return ProofCacheStats(self.cache_hits, self.cache_misses)
