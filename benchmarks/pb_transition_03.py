#!/usr/bin/env python3
"""PB-TRANSITION-03 richer common trust-boundary benchmark.

PB-T03 keeps one external oracle while separating authorization failures from
outcome grounding. In particular FALSE_SUCCESS is not modeled as an
authorization denial: dispatch is allowed, but terminal success must not be
recorded without outcome evidence.

This is a deterministic software research benchmark, not a hardware benchmark.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.model import EpistemicState, Evidence, ProofProcessor

BENCHMARK_ID = "PB-TRANSITION-03"
VERSION = "0.1"
PROTOCOL = "PB-T03/v0.1 authorization-freshness-replay-conflict-outcome"
FAULT_KINDS = (
    "UNKNOWN",
    "STALE_AUTHORITY",
    "REPLAY",
    "CONFLICT",
    "FALSE_SUCCESS",
)
AUTHORIZATION_FAULTS = {"UNKNOWN", "STALE_AUTHORITY", "REPLAY", "CONFLICT"}


@dataclass(frozen=True)
class Trial:
    index: int
    kind: str
    source: int
    target: int


@dataclass
class SoftwareGuard:
    authority: int = 1
    epoch: int = 1

    def __post_init__(self) -> None:
        self.consumed: set[int] = set()

    def authorize(
        self,
        *,
        evidence_present: bool,
        authority: int,
        epoch: int,
        proof_id: int,
        conflict: bool,
    ) -> bool:
        if conflict or not evidence_present:
            return False
        if authority != self.authority or epoch != self.epoch:
            return False
        if proof_id in self.consumed:
            return False
        self.consumed.add(proof_id)
        return True

    @staticmethod
    def terminal_success(*, dispatched: bool, outcome_evidence: bool) -> bool:
        return dispatched and outcome_evidence


def _validate_inputs(trials: int, contamination_rate: float) -> int:
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= contamination_rate <= 1:
        raise ValueError("contamination_rate must be between 0 and 1")
    return round(trials * contamination_rate)


def build_trials(trials: int, contamination_rate: float) -> list[Trial]:
    bad_count = _validate_inputs(trials, contamination_rate)
    bad_seen = 0
    rows: list[Trial] = []
    for index in range(trials):
        contaminated = ((index + 1) * bad_count) // trials > (
            index * bad_count
        ) // trials
        if contaminated:
            kind = FAULT_KINDS[bad_seen % len(FAULT_KINDS)]
            bad_seen += 1
        else:
            kind = "VALID"
        source = index % 2
        rows.append(Trial(index, kind, source, 1 - source))
    return rows


def expected(kind: str) -> tuple[bool, bool]:
    """Return expected (dispatch, terminal_success)."""

    if kind == "VALID":
        return True, True
    if kind == "FALSE_SUCCESS":
        return True, False
    if kind in AUTHORIZATION_FAULTS:
        return False, False
    raise ValueError(f"unknown PB-T03 kind: {kind}")


def _new_kind_metrics() -> dict[str, int]:
    return {
        "trials": 0,
        "oracle_correct": 0,
        "unsafe_dispatches": 0,
        "false_success_claims": 0,
        "missed_valid_dispatches": 0,
    }


def _score(
    per_kind: dict[str, dict[str, int]], kind: str, dispatched: bool, terminal: bool
) -> None:
    expected_dispatch, expected_terminal = expected(kind)
    row = per_kind[kind]
    row["trials"] += 1
    if (dispatched, terminal) == (expected_dispatch, expected_terminal):
        row["oracle_correct"] += 1
    if kind in AUTHORIZATION_FAULTS and dispatched:
        row["unsafe_dispatches"] += 1
    if kind == "FALSE_SUCCESS" and terminal:
        row["false_success_claims"] += 1
    if kind == "VALID" and not dispatched:
        row["missed_valid_dispatches"] += 1


def _finish(
    *,
    architecture: str,
    implementation: str,
    evidence_kind: str,
    rows: list[Trial],
    per_kind: dict[str, dict[str, int]],
    elapsed_ns: int,
    native_steps_total: int,
    claim_boundary: str,
    cost_note: str,
) -> dict[str, Any]:
    trials = len(rows)
    correct = sum(item["oracle_correct"] for item in per_kind.values())
    unsafe = sum(item["unsafe_dispatches"] for item in per_kind.values())
    false_success = sum(item["false_success_claims"] for item in per_kind.values())
    missed = sum(item["missed_valid_dispatches"] for item in per_kind.values())
    valid_trials = per_kind["VALID"]["trials"]
    adversarial_trials = trials - valid_trials
    seconds = elapsed_ns / 1_000_000_000
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "architecture": architecture,
        "implementation": implementation,
        "status": "executed_full",
        "trials": trials,
        "valid_trials": valid_trials,
        "adversarial_trials": adversarial_trials,
        "oracle_correct_trials": correct,
        "oracle_accuracy": correct / trials,
        "unsafe_authorization_dispatches": unsafe,
        "false_success_claims": false_success,
        "missed_valid_dispatches": missed,
        "failure_kind_coverage": 1.0,
        "stream_semantic_coverage": 1.0,
        "supported_fault_kinds": list(FAULT_KINDS),
        "unsupported_fault_kinds": [],
        "evidence_kind": evidence_kind,
        "per_kind": per_kind,
        "elapsed_ns": elapsed_ns,
        "trials_per_sec": trials / seconds if seconds else 0.0,
        "correct_trials_per_sec": correct / seconds if seconds else 0.0,
        "native_steps_total": native_steps_total,
        "claim_boundary": claim_boundary,
        "cost_note": cost_note,
    }


def run_raw(rows: list[Trial]) -> dict[str, Any]:
    per_kind = {kind: _new_kind_metrics() for kind in ("VALID", *FAULT_KINDS)}
    started = time.perf_counter_ns()
    for row in rows:
        # Raw control dispatches and records success unconditionally.
        _score(per_kind, row.kind, True, True)
    elapsed_ns = time.perf_counter_ns() - started
    return _finish(
        architecture="Conventional CPU / raw software baseline",
        implementation="CPython unconditional dispatch + success claim",
        evidence_kind="none",
        rows=rows,
        per_kind=per_kind,
        elapsed_ns=elapsed_ns,
        native_steps_total=len(rows),
        claim_boundary=(
            "Raw control does not inspect evidence, freshness, replay, conflict, or "
            "outcome grounding."
        ),
        cost_note="CPython control timing only; not processor hardware performance",
    )


def _software_inputs(row: Trial) -> tuple[bool, int, int, int, bool, bool]:
    proof_id = row.index + 1
    if row.kind == "UNKNOWN":
        return False, 1, 1, proof_id, False, False
    if row.kind == "STALE_AUTHORITY":
        return True, 1, 0, proof_id, False, False
    if row.kind == "REPLAY":
        return True, 1, 1, proof_id, False, False
    if row.kind == "CONFLICT":
        return True, 1, 1, proof_id, True, False
    if row.kind == "FALSE_SUCCESS":
        return True, 1, 1, proof_id, False, False
    if row.kind == "VALID":
        return True, 1, 1, proof_id, False, True
    raise ValueError(row.kind)


def run_software_guarded(rows: list[Trial]) -> dict[str, Any]:
    guard = SoftwareGuard()
    per_kind = {kind: _new_kind_metrics() for kind in ("VALID", *FAULT_KINDS)}
    started = time.perf_counter_ns()
    for row in rows:
        present, authority, epoch, proof_id, conflict, outcome = _software_inputs(row)
        if row.kind == "REPLAY":
            # A replay arrives with an already-consumed grant.
            guard.consumed.add(proof_id)
        dispatched = guard.authorize(
            evidence_present=present,
            authority=authority,
            epoch=epoch,
            proof_id=proof_id,
            conflict=conflict,
        )
        terminal = guard.terminal_success(
            dispatched=dispatched,
            outcome_evidence=outcome,
        )
        _score(per_kind, row.kind, dispatched, terminal)
    elapsed_ns = time.perf_counter_ns() - started
    return _finish(
        architecture="Conventional CPU / explicit software trust guard",
        implementation="CPython application metadata + replay set + outcome check",
        evidence_kind="application_structured_guard",
        rows=rows,
        per_kind=per_kind,
        elapsed_ns=elapsed_ns,
        native_steps_total=len(rows),
        claim_boundary=(
            "This anti-strawman control implements the full frozen PB-T03 policy in "
            "ordinary application software. Correct behavior is not native proof "
            "coverage or a hardware claim."
        ),
        cost_note="CPython application-guard timing; metadata allocation is benchmark code",
    )


def _install_authorization(cpu: ProofProcessor, row: Trial) -> None:
    proof_id = row.index + 1
    statement = f"transition_{row.source}_to_{row.target}_authorized"
    if row.kind == "UNKNOWN":
        cpu.store_unknown(0, statement, True)
    elif row.kind == "STALE_AUTHORITY":
        cpu.store_evidence(0, Evidence(statement, True, proof_id, 1, 0, row.index))
    elif row.kind == "REPLAY":
        cpu.consumed_proofs.add(proof_id)
        cpu.store_evidence(0, Evidence(statement, True, proof_id, 1, 1, row.index))
    elif row.kind == "CONFLICT":
        cpu.store_conflict(0, statement)
    elif row.kind in {"VALID", "FALSE_SUCCESS"}:
        cpu.store_evidence(0, Evidence(statement, True, proof_id, 1, 1, row.index))
    else:
        raise ValueError(row.kind)


def run_proofbit(rows: list[Trial]) -> dict[str, Any]:
    cpu = ProofProcessor()
    per_kind = {kind: _new_kind_metrics() for kind in ("VALID", *FAULT_KINDS)}
    started = time.perf_counter_ns()
    for row in rows:
        _install_authorization(cpu, row)
        dispatched = cpu.guarded_execute(0)

        outcome_statement = f"transition_{row.source}_to_{row.target}_outcome"
        if row.kind == "VALID" and dispatched:
            outcome = Evidence(
                outcome_statement,
                True,
                1_000_000 + row.index,
                1,
                1,
                row.index,
            )
            terminal = cpu.verify(outcome, consume=False) is EpistemicState.PROVEN_TRUE
        elif row.kind == "FALSE_SUCCESS" and dispatched:
            cpu.record_claimed_success_without_outcome_evidence(1, outcome_statement)
            terminal = cpu.load(1).state is EpistemicState.PROVEN_TRUE
        else:
            terminal = False

        _score(per_kind, row.kind, dispatched, terminal)
    elapsed_ns = time.perf_counter_ns() - started
    return _finish(
        architecture="ProofBit",
        implementation="ProofProcessor Python semantic reference",
        evidence_kind=(
            "statement/value/authority/epoch-bound authorization plus separate outcome evidence"
        ),
        rows=rows,
        per_kind=per_kind,
        elapsed_ns=elapsed_ns,
        native_steps_total=len(rows),
        claim_boundary=(
            "Authorization evidence and outcome evidence are separate. FALSE_SUCCESS "
            "permits authorized dispatch but terminal success remains unproven without "
            "outcome evidence."
        ),
        cost_note=(
            "Python semantic-reference timing includes evidence construction, storage, "
            "verification, replay checks, and outcome grounding; not silicon performance"
        ),
    )


def validate_external(report: dict[str, Any], trials: int, contamination_rate: float) -> dict[str, Any]:
    if report.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError("external benchmark_id mismatch")
    if report.get("version") != VERSION or report.get("protocol") != PROTOCOL:
        raise ValueError("external PB-T03 version/protocol mismatch")
    if report.get("trials") != trials:
        raise ValueError("external PB-T03 trial count mismatch")
    if abs(float(report.get("contamination_rate")) - contamination_rate) > 1e-12:
        raise ValueError("external PB-T03 contamination mismatch")
    if report.get("status") not in {"executed_partial", "executed_full"}:
        raise ValueError("external PB-T03 report is not executable evidence")
    required = {
        "failure_kind_coverage",
        "stream_semantic_coverage",
        "supported_fault_kinds",
        "unsupported_fault_kinds",
        "assessed_trials",
        "unassessed_trials",
        "oracle_correct_assessed_trials",
        "oracle_accuracy_on_assessed",
        "unsafe_authorization_dispatches_on_assessed",
        "false_success_claims_on_assessed",
        "evidence_kind",
        "per_kind",
        "elapsed_ns",
        "assessed_trials_per_sec",
        "claim_boundary",
        "cost_note",
    }
    missing = sorted(required - report.keys())
    if missing:
        raise ValueError(f"external PB-T03 report missing: {missing}")
    if report["assessed_trials"] + report["unassessed_trials"] != trials:
        raise ValueError("external assessed/unassessed total mismatch")
    return report


def _not_run(architecture: str) -> dict[str, Any]:
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "architecture": architecture,
        "status": "not_run",
        "reason": "adapter JSON not supplied",
    }


def build_report(
    trials: int = 10_000,
    contamination_rate: float = 0.10,
    *,
    capu_report: dict[str, Any] | None = None,
    morphos_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = build_trials(trials, contamination_rate)
    systems = {
        "baseline_raw": run_raw(rows),
        "baseline_software_guarded": run_software_guarded(rows),
        "proofbit": run_proofbit(rows),
        "capu": validate_external(capu_report, trials, contamination_rate)
        if capu_report is not None
        else _not_run("CaPU"),
        "morphos": validate_external(morphos_report, trials, contamination_rate)
        if morphos_report is not None
        else _not_run("COSMIC ORGANICS / MORPHOS"),
    }
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "scope": (
            "common authorization/freshness/replay/conflict/outcome oracle; software "
            "research benchmark, not a universal architecture ranking"
        ),
        "fault_kinds": list(FAULT_KINDS),
        "oracle": {
            "VALID": {"dispatch": True, "terminal_success": True},
            "UNKNOWN": {"dispatch": False, "terminal_success": False},
            "STALE_AUTHORITY": {"dispatch": False, "terminal_success": False},
            "REPLAY": {"dispatch": False, "terminal_success": False},
            "CONFLICT": {"dispatch": False, "terminal_success": False},
            "FALSE_SUCCESS": {"dispatch": True, "terminal_success": False},
        },
        "comparison_order": [
            "semantic coverage",
            "oracle correctness on assessed semantics",
            "unsafe authorization and false-success behavior",
            "evidence category",
            "speed/cost only within the measured software boundary",
        ],
        "unsupported_never_counted_as_prevented": True,
        "no_single_winner_score": True,
        "systems": systems,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PB-TRANSITION-03.")
    parser.add_argument("--trials", type=int, default=10_000)
    parser.add_argument("--contamination", type=float, default=0.10)
    parser.add_argument("--capu-json", type=Path)
    parser.add_argument("--morphos-json", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    capu = json.loads(args.capu_json.read_text()) if args.capu_json else None
    morphos = json.loads(args.morphos_json.read_text()) if args.morphos_json else None
    report = build_report(
        args.trials,
        args.contamination,
        capu_report=capu,
        morphos_report=morphos,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
