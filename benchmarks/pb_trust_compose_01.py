#!/usr/bin/env python3
"""PB-TRUST-COMPOSE-01 composition/propagation benchmark.

The experiment compares three *software reference* implementations of the same
frozen trust oracle while the number of component boundaries grows:

1. competent conventional software with one shared immutable message object;
2. competent conventional software that explicitly reconstructs metadata at
   every serialization-style boundary;
3. the current ProofBit semantic reference carrying bound evidence to the
   final guarded side-effect boundary.

This is intentionally not a hardware benchmark and does not assume ProofBit
wins. The strongest conventional-software control is kept in the report even
when it is faster or simpler.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys
import time
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.model import EpistemicState, Evidence, ProofProcessor

BENCHMARK_ID = "PB-TRUST-COMPOSE-01"
VERSION = "0.1"
PROTOCOL = "PB-TC01/v0.1 composed-trust-propagation"
FAULT_KINDS = (
    "UNKNOWN",
    "STALE_AUTHORITY",
    "REPLAY",
    "CONFLICT",
    "REBIND_STATEMENT",
    "FALSE_SUCCESS",
)
AUTHORIZATION_FAULTS = {
    "UNKNOWN",
    "STALE_AUTHORITY",
    "REPLAY",
    "CONFLICT",
    "REBIND_STATEMENT",
}
DEFAULT_BOUNDARIES = (1, 2, 4, 8, 16, 32)
SOFTWARE_METADATA_FIELDS = 9


@dataclass(frozen=True)
class Trial:
    index: int
    kind: str
    action: str
    evidence_statement: str


@dataclass(frozen=True)
class SoftwareMessage:
    action: str
    evidence_present: bool
    evidence_statement: str
    value: bool
    proof_id: int
    authority: int
    epoch: int
    conflict: bool
    outcome_evidence: bool


class SoftwareTrustGuard:
    def __init__(self, authority: int = 1, epoch: int = 1) -> None:
        self.authority = authority
        self.epoch = epoch
        self.consumed: set[int] = set()

    def authorize(self, message: SoftwareMessage) -> bool:
        if not message.evidence_present or message.conflict:
            return False
        if message.evidence_statement != message.action:
            return False
        if message.authority != self.authority or message.epoch != self.epoch:
            return False
        if message.proof_id in self.consumed:
            return False
        self.consumed.add(message.proof_id)
        return message.value

    @staticmethod
    def terminal_success(message: SoftwareMessage, dispatched: bool) -> bool:
        return dispatched and message.outcome_evidence


def _validate_inputs(trials: int, contamination_rate: float, boundaries: Iterable[int]) -> tuple[int, tuple[int, ...]]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= contamination_rate <= 1:
        raise ValueError("contamination_rate must be between 0 and 1")
    normalized = tuple(boundaries)
    if not normalized or any(item <= 0 for item in normalized):
        raise ValueError("boundaries must contain positive integers")
    return round(trials * contamination_rate), normalized


def build_trials(trials: int, contamination_rate: float) -> list[Trial]:
    bad_count, _ = _validate_inputs(trials, contamination_rate, (1,))
    bad_seen = 0
    rows: list[Trial] = []
    for index in range(trials):
        contaminated = ((index + 1) * bad_count) // trials > (index * bad_count) // trials
        if contaminated:
            kind = FAULT_KINDS[bad_seen % len(FAULT_KINDS)]
            bad_seen += 1
        else:
            kind = "VALID"
        action = f"release:{index}"
        evidence_statement = f"other:{index}" if kind == "REBIND_STATEMENT" else action
        rows.append(Trial(index, kind, action, evidence_statement))
    return rows


def expected(kind: str) -> tuple[bool, bool]:
    if kind == "VALID":
        return True, True
    if kind == "FALSE_SUCCESS":
        return True, False
    if kind in AUTHORIZATION_FAULTS:
        return False, False
    raise ValueError(kind)


def _message(row: Trial) -> SoftwareMessage:
    proof_id = row.index + 1
    return SoftwareMessage(
        action=row.action,
        evidence_present=row.kind != "UNKNOWN",
        evidence_statement=row.evidence_statement,
        value=True,
        proof_id=proof_id,
        authority=1,
        epoch=0 if row.kind == "STALE_AUTHORITY" else 1,
        conflict=row.kind == "CONFLICT",
        outcome_evidence=row.kind == "VALID",
    )


def _copy_message(message: SoftwareMessage) -> SoftwareMessage:
    # Explicit mapping models an application/RPC boundary where trust metadata
    # is reconstructed field-by-field rather than carried by a native proof ref.
    return SoftwareMessage(
        action=message.action,
        evidence_present=message.evidence_present,
        evidence_statement=message.evidence_statement,
        value=message.value,
        proof_id=message.proof_id,
        authority=message.authority,
        epoch=message.epoch,
        conflict=message.conflict,
        outcome_evidence=message.outcome_evidence,
    )


def _new_kind_metrics() -> dict[str, int]:
    return {
        "trials": 0,
        "oracle_correct": 0,
        "unsafe_dispatches": 0,
        "false_success_claims": 0,
        "missed_valid_dispatches": 0,
    }


def _score(per_kind: dict[str, dict[str, int]], kind: str, dispatched: bool, terminal: bool) -> None:
    expected_dispatch, expected_terminal = expected(kind)
    item = per_kind[kind]
    item["trials"] += 1
    if (dispatched, terminal) == (expected_dispatch, expected_terminal):
        item["oracle_correct"] += 1
    if kind in AUTHORIZATION_FAULTS and dispatched:
        item["unsafe_dispatches"] += 1
    if kind == "FALSE_SUCCESS" and terminal:
        item["false_success_claims"] += 1
    if kind == "VALID" and not dispatched:
        item["missed_valid_dispatches"] += 1


def _finish(
    *,
    architecture: str,
    implementation: str,
    evidence_kind: str,
    rows: list[Trial],
    per_kind: dict[str, dict[str, int]],
    elapsed_ns: int,
    boundaries: int,
    metadata_field_assignments: int,
    object_ref_hops: int,
    proof_ref_hops: int,
    claim_boundary: str,
) -> dict[str, Any]:
    trials = len(rows)
    correct = sum(item["oracle_correct"] for item in per_kind.values())
    unsafe = sum(item["unsafe_dispatches"] for item in per_kind.values())
    false_success = sum(item["false_success_claims"] for item in per_kind.values())
    missed = sum(item["missed_valid_dispatches"] for item in per_kind.values())
    seconds = elapsed_ns / 1_000_000_000
    return {
        "architecture": architecture,
        "implementation": implementation,
        "evidence_kind": evidence_kind,
        "boundaries": boundaries,
        "trials": trials,
        "oracle_correct_trials": correct,
        "oracle_accuracy": correct / trials,
        "unsafe_authorization_dispatches": unsafe,
        "false_success_claims": false_success,
        "missed_valid_dispatches": missed,
        "per_kind": per_kind,
        "elapsed_ns": elapsed_ns,
        "trials_per_sec": trials / seconds if seconds else 0.0,
        "metadata_field_assignments": metadata_field_assignments,
        "object_ref_hops": object_ref_hops,
        "proof_ref_hops": proof_ref_hops,
        "claim_boundary": claim_boundary,
    }


def run_software_shared(rows: list[Trial], boundaries: int) -> dict[str, Any]:
    guard = SoftwareTrustGuard()
    per_kind = {kind: _new_kind_metrics() for kind in ("VALID", *FAULT_KINDS)}
    started = time.perf_counter_ns()
    object_ref_hops = 0
    for row in rows:
        message = _message(row)
        if row.kind == "REPLAY":
            guard.consumed.add(message.proof_id)
        for _ in range(boundaries):
            # Strong conventional control: shared immutable object, no metadata
            # reconstruction at the component hop.
            message = message
            object_ref_hops += 1
        dispatched = guard.authorize(message)
        terminal = guard.terminal_success(message, dispatched)
        _score(per_kind, row.kind, dispatched, terminal)
    elapsed_ns = time.perf_counter_ns() - started
    return _finish(
        architecture="Conventional CPU / shared software trust helper",
        implementation="CPython immutable SoftwareMessage + centralized guard",
        evidence_kind="application_structured_guard",
        rows=rows,
        per_kind=per_kind,
        elapsed_ns=elapsed_ns,
        boundaries=boundaries,
        metadata_field_assignments=0,
        object_ref_hops=object_ref_hops,
        proof_ref_hops=0,
        claim_boundary=(
            "Best-case same-process software control: one immutable trust envelope is "
            "shared by reference across component hops."
        ),
    )


def run_software_serialized(rows: list[Trial], boundaries: int) -> dict[str, Any]:
    guard = SoftwareTrustGuard()
    per_kind = {kind: _new_kind_metrics() for kind in ("VALID", *FAULT_KINDS)}
    started = time.perf_counter_ns()
    field_assignments = 0
    for row in rows:
        message = _message(row)
        if row.kind == "REPLAY":
            guard.consumed.add(message.proof_id)
        for _ in range(boundaries):
            message = _copy_message(message)
            field_assignments += SOFTWARE_METADATA_FIELDS
        dispatched = guard.authorize(message)
        terminal = guard.terminal_success(message, dispatched)
        _score(per_kind, row.kind, dispatched, terminal)
    elapsed_ns = time.perf_counter_ns() - started
    return _finish(
        architecture="Conventional CPU / serialized software trust plumbing",
        implementation="CPython field-by-field trust-envelope reconstruction + centralized guard",
        evidence_kind="application_structured_guard",
        rows=rows,
        per_kind=per_kind,
        elapsed_ns=elapsed_ns,
        boundaries=boundaries,
        metadata_field_assignments=field_assignments,
        object_ref_hops=0,
        proof_ref_hops=0,
        claim_boundary=(
            "Models serialization-style component boundaries by explicitly reconstructing "
            "all trust fields at every hop. This is not claimed to represent all software architectures."
        ),
    )


def _install_proof(cpu: ProofProcessor, row: Trial) -> None:
    proof_id = row.index + 1
    if row.kind == "UNKNOWN":
        cpu.store_unknown(0, row.evidence_statement, True)
    elif row.kind == "CONFLICT":
        cpu.store_conflict(0, row.evidence_statement)
    else:
        if row.kind == "REPLAY":
            cpu.consumed_proofs.add(proof_id)
        cpu.store_evidence(
            0,
            Evidence(
                row.evidence_statement,
                True,
                proof_id,
                1,
                0 if row.kind == "STALE_AUTHORITY" else 1,
                row.index,
            ),
        )


def run_proofbit(rows: list[Trial], boundaries: int) -> dict[str, Any]:
    cpu = ProofProcessor()
    per_kind = {kind: _new_kind_metrics() for kind in ("VALID", *FAULT_KINDS)}
    started = time.perf_counter_ns()
    proof_ref_hops = 0
    for row in rows:
        _install_proof(cpu, row)
        for _ in range(boundaries):
            # The current reference does not implement hardware transport. This
            # counter models logical propagation of one proof reference; timing
            # remains ordinary Python loop/object timing.
            proof_ref_hops += 1
        dispatched = cpu.guarded_execute(0, expected_statement=row.action)
        if row.kind == "VALID" and dispatched:
            outcome = Evidence(
                f"outcome:{row.index}",
                True,
                1_000_000 + row.index,
                1,
                1,
                row.index,
            )
            terminal = cpu.verify(outcome, consume=False) is EpistemicState.PROVEN_TRUE
        elif row.kind == "FALSE_SUCCESS" and dispatched:
            cpu.record_claimed_success_without_outcome_evidence(1, f"outcome:{row.index}")
            terminal = cpu.load(1).state is EpistemicState.PROVEN_TRUE
        else:
            terminal = False
        _score(per_kind, row.kind, dispatched, terminal)
    elapsed_ns = time.perf_counter_ns() - started
    return _finish(
        architecture="ProofBit",
        implementation="ProofProcessor Python semantic reference + bound side-effect statement",
        evidence_kind="bound proof object plus separate outcome evidence",
        rows=rows,
        per_kind=per_kind,
        elapsed_ns=elapsed_ns,
        boundaries=boundaries,
        metadata_field_assignments=0,
        object_ref_hops=0,
        proof_ref_hops=proof_ref_hops,
        claim_boundary=(
            "Proof reference propagation is a logical model counter, not measured hardware transport. "
            "Python timing includes evidence construction and verification."
        ),
    )


def _ratios(shared: dict[str, Any], serialized: dict[str, Any], proofbit: dict[str, Any]) -> dict[str, float]:
    shared_rate = float(shared["trials_per_sec"])
    serialized_rate = float(serialized["trials_per_sec"])
    proof_rate = float(proofbit["trials_per_sec"])
    return {
        "proofbit_vs_shared_throughput": proof_rate / shared_rate if shared_rate else 0.0,
        "proofbit_vs_serialized_throughput": proof_rate / serialized_rate if serialized_rate else 0.0,
        "serialized_vs_shared_throughput": serialized_rate / shared_rate if shared_rate else 0.0,
    }


def build_report(
    trials: int = 10_000,
    contamination_rate: float = 0.12,
    boundaries: Iterable[int] = DEFAULT_BOUNDARIES,
) -> dict[str, Any]:
    _, normalized = _validate_inputs(trials, contamination_rate, boundaries)
    rows = build_trials(trials, contamination_rate)
    scale = []
    first_serialized_crossover: int | None = None
    for boundary_count in normalized:
        shared = run_software_shared(rows, boundary_count)
        serialized = run_software_serialized(rows, boundary_count)
        proofbit = run_proofbit(rows, boundary_count)
        ratios = _ratios(shared, serialized, proofbit)
        if first_serialized_crossover is None and ratios["proofbit_vs_serialized_throughput"] >= 1.0:
            first_serialized_crossover = boundary_count
        scale.append(
            {
                "boundaries": boundary_count,
                "systems": {
                    "software_shared": shared,
                    "software_serialized": serialized,
                    "proofbit": proofbit,
                },
                "throughput_ratios": ratios,
            }
        )
    fault_counts = {kind: 0 for kind in ("VALID", *FAULT_KINDS)}
    for row in rows:
        fault_counts[row.kind] += 1
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "scope": (
            "multi-boundary trust composition on software reference models; correctness first, "
            "then explicit plumbing work and Python runtime"
        ),
        "trials": trials,
        "contamination_rate": contamination_rate,
        "fault_kinds": list(FAULT_KINDS),
        "fault_counts": fault_counts,
        "boundaries": list(normalized),
        "software_metadata_fields_per_serialized_hop": SOFTWARE_METADATA_FIELDS,
        "scale": scale,
        "first_measured_proofbit_vs_serialized_python_crossover_boundary": first_serialized_crossover,
        "no_single_winner_score": True,
        "comparison_order": [
            "oracle correctness",
            "unsafe authorization / false-success behavior",
            "statement binding",
            "explicit metadata plumbing work",
            "Python runtime",
        ],
        "caveats": [
            "software_shared is an intentional strong conventional control",
            "software_serialized models explicit field reconstruction, not every possible software architecture",
            "proof_ref_hops are logical model counts, not hardware measurements",
            "Python throughput is not processor, silicon, energy, area, or cryptographic performance",
            "a crossover, if observed, applies only to this frozen reference implementation",
        ],
    }


def _parse_boundaries(raw: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in raw.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=10_000)
    parser.add_argument("--contamination", type=float, default=0.12)
    parser.add_argument("--boundaries", default=",".join(str(item) for item in DEFAULT_BOUNDARIES))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(args.trials, args.contamination, _parse_boundaries(args.boundaries))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for row in report["scale"]:
            systems = row["systems"]
            print(
                f"boundaries={row['boundaries']:>2} "
                f"shared={systems['software_shared']['trials_per_sec']:.0f}/s "
                f"serialized={systems['software_serialized']['trials_per_sec']:.0f}/s "
                f"proofbit={systems['proofbit']['trials_per_sec']:.0f}/s"
            )
        print(
            "first ProofBit>=serialized Python crossover:",
            report["first_measured_proofbit_vs_serialized_python_crossover_boundary"],
        )


if __name__ == "__main__":
    main()
