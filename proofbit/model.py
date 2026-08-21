from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class EpistemicState(str, Enum):
    PROVEN_TRUE = "PROVEN_TRUE"
    PROVEN_FALSE = "PROVEN_FALSE"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"
    STALE = "STALE"
    REPLAYED = "REPLAYED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class Evidence:
    statement: str
    value: bool
    proof_id: int
    authority: int
    epoch: int
    provenance: int = 0


@dataclass
class ProofCell:
    statement: str
    value: Optional[bool]
    state: EpistemicState
    evidence: Optional[Evidence] = None


class BaselineProcessor:
    """Conventional value-only memory/decision model."""

    def __init__(self) -> None:
        self.memory: Dict[int, bool] = {}
        self.side_effects = 0

    def store(self, address: int, value: bool) -> None:
        self.memory[address] = value

    def load(self, address: int) -> bool:
        return self.memory[address]

    def guarded_execute(self, address: int) -> bool:
        if self.load(address):
            self.side_effects += 1
            return True
        return False


class ProofProcessor:
    """Small proof-aware reference model; not a hardware simulator."""

    def __init__(self, authority: int = 1, epoch: int = 1) -> None:
        self.memory: Dict[int, ProofCell] = {}
        self.authority = authority
        self.epoch = epoch
        self.consumed_proofs: set[int] = set()
        self.side_effects = 0

    def store_unknown(self, address: int, statement: str, value: Optional[bool]) -> None:
        self.memory[address] = ProofCell(statement, value, EpistemicState.UNKNOWN)

    def store_evidence(self, address: int, evidence: Evidence) -> None:
        state = self.verify(evidence, consume=False)
        self.memory[address] = ProofCell(
            evidence.statement,
            evidence.value,
            state,
            evidence,
        )

    def store_conflict(self, address: int, statement: str) -> None:
        self.memory[address] = ProofCell(statement, None, EpistemicState.CONFLICT)

    def load(self, address: int) -> ProofCell:
        return self.memory[address]

    def verify(self, evidence: Evidence, *, consume: bool) -> EpistemicState:
        if evidence.authority != self.authority:
            return EpistemicState.INVALID
        if evidence.epoch != self.epoch:
            return EpistemicState.STALE
        if evidence.proof_id in self.consumed_proofs:
            return EpistemicState.REPLAYED
        if consume:
            self.consumed_proofs.add(evidence.proof_id)
        return (
            EpistemicState.PROVEN_TRUE
            if evidence.value
            else EpistemicState.PROVEN_FALSE
        )

    def guarded_execute(self, address: int, *, single_use: bool = True) -> bool:
        cell = self.load(address)
        if cell.evidence is None:
            return False
        state = self.verify(cell.evidence, consume=single_use)
        cell.state = state
        if state is EpistemicState.PROVEN_TRUE:
            self.side_effects += 1
            return True
        return False

    def record_claimed_success_without_outcome_evidence(
        self, address: int, statement: str
    ) -> None:
        # A claimed outcome without execution/outcome evidence remains UNKNOWN.
        self.store_unknown(address, statement, True)
