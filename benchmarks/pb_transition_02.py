#!/usr/bin/env python3
"""PB-TRANSITION-02 common binary-endpoint transition benchmark.

The benchmark freezes one external oracle across conventional software,
ProofBit, CaPU, and MORPHOS while preserving each architecture's native
justification semantics. It intentionally does not collapse those semantics
into a single synthetic score.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.model import Evidence, ProofProcessor


PROTOCOL = (
    "PB-T02/v0.1 binary-endpoint alternating-direction "
    "deterministic-insufficient-support"
)
BENCHMARK_ID = "PB-TRANSITION-02"
VERSION = "0.1"


def _validate_inputs(trials: int, insufficient_rate: float) -> int:
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= insufficient_rate <= 1:
        raise ValueError("insufficient_rate must be between 0 and 1")
    return round(trials * insufficient_rate)


def _is_insufficient(index: int, trials: int, insufficient_count: int) -> bool:
    """Spread an exact number of insufficient-support trials deterministically."""

    return ((index + 1) * insufficient_count) // trials > (
        index * insufficient_count
    ) // trials


def _base_metrics(
    *,
    architecture: str,
    implementation: str,
    evidence_kind: str,
    trials: int,
    insufficient_rate: float,
    valid_trials: int,
    insufficient_trials: int,
    source_0_trials: int,
    source_1_trials: int,
    correct_valid: int,
    invalid_preserved: int,
    unsafe_invalid: int,
    missed_valid: int,
    justified_valid: int,
    elapsed_ns: int,
    native_steps_total: int | None,
    cost_note: str,
    claim_boundary: str,
) -> dict[str, Any]:
    seconds = elapsed_ns / 1_000_000_000
    oracle_correct = correct_valid + invalid_preserved
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "architecture": architecture,
        "implementation": implementation,
        "status": "executed",
        "trials": trials,
        "insufficient_support_rate": insufficient_rate,
        "valid_trials": valid_trials,
        "insufficient_support_trials": insufficient_trials,
        "source_0_trials": source_0_trials,
        "source_1_trials": source_1_trials,
        "correct_valid_transitions": correct_valid,
        "invalid_transitions_preserved": invalid_preserved,
        "unsafe_invalid_transitions": unsafe_invalid,
        "missed_valid_transitions": missed_valid,
        "oracle_correct_trials": oracle_correct,
        "oracle_accuracy": oracle_correct / trials,
        "native_justified_valid_transitions": justified_valid,
        "native_justification_coverage": (
            justified_valid / valid_trials if valid_trials else 0.0
        ),
        "evidence_kind": evidence_kind,
        "elapsed_ns": elapsed_ns,
        "trials_per_sec": trials / seconds if seconds else 0.0,
        "correct_useful_transitions_per_sec": (
            correct_valid / seconds if seconds else 0.0
        ),
        "justified_useful_throughput": (
            justified_valid / seconds if seconds else 0.0
        ),
        "native_steps_total": native_steps_total,
        "cost_note": cost_note,
        "claim_boundary": claim_boundary,
    }


def run_raw_baseline(trials: int, insufficient_rate: float) -> dict[str, Any]:
    insufficient_count = _validate_inputs(trials, insufficient_rate)
    valid_trials = insufficient_trials = 0
    source_0_trials = source_1_trials = 0
    correct_valid = invalid_preserved = unsafe_invalid = missed_valid = 0

    started = time.perf_counter_ns()
    for index in range(trials):
        insufficient = _is_insufficient(index, trials, insufficient_count)
        source = index % 2
        target = 1 - source
        if source == 0:
            source_0_trials += 1
        else:
            source_1_trials += 1

        # The raw baseline executes the requested transition unconditionally.
        final_state = target
        if insufficient:
            insufficient_trials += 1
            if final_state == source:
                invalid_preserved += 1
            else:
                unsafe_invalid += 1
        else:
            valid_trials += 1
            if final_state == target:
                correct_valid += 1
            else:
                missed_valid += 1
    elapsed_ns = time.perf_counter_ns() - started

    return _base_metrics(
        architecture="Conventional CPU / raw software baseline",
        implementation="CPython unconditional binary state transition",
        evidence_kind="none",
        trials=trials,
        insufficient_rate=insufficient_rate,
        valid_trials=valid_trials,
        insufficient_trials=insufficient_trials,
        source_0_trials=source_0_trials,
        source_1_trials=source_1_trials,
        correct_valid=correct_valid,
        invalid_preserved=invalid_preserved,
        unsafe_invalid=unsafe_invalid,
        missed_valid=missed_valid,
        justified_valid=0,
        elapsed_ns=elapsed_ns,
        native_steps_total=trials,
        cost_note=(
            "CPython loop timing only; not CPU hardware cycles, energy, area, or "
            "a processor microbenchmark"
        ),
        claim_boundary=(
            "Raw baseline has no support check. It is retained only as a control "
            "for the cost and consequence of unconditional transition execution."
        ),
    )


def run_software_guarded_baseline(
    trials: int, insufficient_rate: float
) -> dict[str, Any]:
    insufficient_count = _validate_inputs(trials, insufficient_rate)
    valid_trials = insufficient_trials = 0
    source_0_trials = source_1_trials = 0
    correct_valid = invalid_preserved = unsafe_invalid = missed_valid = 0

    started = time.perf_counter_ns()
    for index in range(trials):
        insufficient = _is_insufficient(index, trials, insufficient_count)
        source = index % 2
        target = 1 - source
        if source == 0:
            source_0_trials += 1
        else:
            source_1_trials += 1

        support = not insufficient
        final_state = target if support else source
        if insufficient:
            insufficient_trials += 1
            if final_state == source:
                invalid_preserved += 1
            else:
                unsafe_invalid += 1
        else:
            valid_trials += 1
            if final_state == target:
                correct_valid += 1
            else:
                missed_valid += 1
    elapsed_ns = time.perf_counter_ns() - started

    return _base_metrics(
        architecture="Conventional CPU / software guarded",
        implementation="CPython application boolean support guard",
        evidence_kind="application_boolean_guard",
        trials=trials,
        insufficient_rate=insufficient_rate,
        valid_trials=valid_trials,
        insufficient_trials=insufficient_trials,
        source_0_trials=source_0_trials,
        source_1_trials=source_1_trials,
        correct_valid=correct_valid,
        invalid_preserved=invalid_preserved,
        unsafe_invalid=unsafe_invalid,
        missed_valid=missed_valid,
        justified_valid=0,
        elapsed_ns=elapsed_ns,
        native_steps_total=trials,
        cost_note=(
            "CPython application-guard timing only; this is the anti-strawman "
            "software control, not a native proof mechanism"
        ),
        claim_boundary=(
            "The software guard can satisfy this simple binary oracle without a "
            "proof object. Correct behavior is not counted as native proof coverage."
        ),
    )


def run_proofbit(trials: int, insufficient_rate: float) -> dict[str, Any]:
    insufficient_count = _validate_inputs(trials, insufficient_rate)
    cpu = ProofProcessor()
    valid_trials = insufficient_trials = 0
    source_0_trials = source_1_trials = 0
    correct_valid = invalid_preserved = unsafe_invalid = missed_valid = 0
    justified_valid = 0

    started = time.perf_counter_ns()
    for index in range(trials):
        insufficient = _is_insufficient(index, trials, insufficient_count)
        source = index % 2
        target = 1 - source
        statement = f"transition_{source}_to_{target}_allowed"
        if source == 0:
            source_0_trials += 1
        else:
            source_1_trials += 1

        if insufficient:
            insufficient_trials += 1
            cpu.store_unknown(0, statement, True)
        else:
            valid_trials += 1
            cpu.store_evidence(
                0,
                Evidence(
                    statement=statement,
                    value=True,
                    proof_id=index + 1,
                    authority=1,
                    epoch=1,
                    provenance=index,
                ),
            )

        allowed = cpu.guarded_execute(0)
        final_state = target if allowed else source

        if insufficient:
            if final_state == source:
                invalid_preserved += 1
            else:
                unsafe_invalid += 1
        elif final_state == target:
            correct_valid += 1
            justified_valid += 1
        else:
            missed_valid += 1
    elapsed_ns = time.perf_counter_ns() - started

    return _base_metrics(
        architecture="ProofBit",
        implementation="ProofProcessor Python semantic reference",
        evidence_kind="evidence_bound_statement_authority_epoch",
        trials=trials,
        insufficient_rate=insufficient_rate,
        valid_trials=valid_trials,
        insufficient_trials=insufficient_trials,
        source_0_trials=source_0_trials,
        source_1_trials=source_1_trials,
        correct_valid=correct_valid,
        invalid_preserved=invalid_preserved,
        unsafe_invalid=unsafe_invalid,
        missed_valid=missed_valid,
        justified_valid=justified_valid,
        elapsed_ns=elapsed_ns,
        native_steps_total=trials,
        cost_note=(
            "Python semantic-reference timing includes evidence construction, store, "
            "verification, and guard; it is not silicon performance"
        ),
        claim_boundary=(
            "Valid transitions carry statement/value/authority/epoch-bound evidence. "
            "Insufficient support is represented as UNKNOWN and cannot execute."
        ),
    )


def _not_run(architecture: str, reason: str) -> dict[str, Any]:
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "architecture": architecture,
        "status": "not-run",
        "reason": reason,
    }


def validate_external(
    report: dict[str, Any], trials: int, insufficient_rate: float
) -> dict[str, Any]:
    insufficient_count = _validate_inputs(trials, insufficient_rate)
    expected_valid = trials - insufficient_count
    expected_source_0 = (trials + 1) // 2
    expected_source_1 = trials // 2

    required = {
        "benchmark_id",
        "version",
        "protocol",
        "architecture",
        "status",
        "trials",
        "insufficient_support_rate",
        "valid_trials",
        "insufficient_support_trials",
        "source_0_trials",
        "source_1_trials",
        "correct_valid_transitions",
        "invalid_transitions_preserved",
        "unsafe_invalid_transitions",
        "missed_valid_transitions",
        "oracle_accuracy",
        "native_justification_coverage",
        "evidence_kind",
        "elapsed_ns",
        "trials_per_sec",
        "correct_useful_transitions_per_sec",
        "justified_useful_throughput",
        "cost_note",
        "claim_boundary",
    }
    missing = sorted(required - report.keys())
    if missing:
        raise ValueError(f"external PB-TRANSITION-02 report missing: {missing}")
    if report["benchmark_id"] != BENCHMARK_ID:
        raise ValueError("external benchmark_id mismatch")
    if report["version"] != VERSION:
        raise ValueError("external benchmark version mismatch")
    if report["protocol"] != PROTOCOL:
        raise ValueError("external protocol mismatch")
    if report["status"] != "executed":
        raise ValueError("external report is not executed")
    if report["trials"] != trials:
        raise ValueError("external trial count mismatch")
    if abs(float(report["insufficient_support_rate"]) - insufficient_rate) > 1e-12:
        raise ValueError("external insufficient-support rate mismatch")
    if report["valid_trials"] != expected_valid:
        raise ValueError("external valid-trial count mismatch")
    if report["insufficient_support_trials"] != insufficient_count:
        raise ValueError("external insufficient-trial count mismatch")
    if report["source_0_trials"] != expected_source_0:
        raise ValueError("external source-0 count mismatch")
    if report["source_1_trials"] != expected_source_1:
        raise ValueError("external source-1 count mismatch")
    return report


def _load_external(
    path: str | None,
    architecture: str,
    trials: int,
    insufficient_rate: float,
) -> dict[str, Any]:
    if path is None:
        return _not_run(architecture, "adapter JSON not supplied")
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_external(report, trials, insufficient_rate)


def run_benchmark(
    trials: int = 10_000,
    insufficient_rate: float = 0.10,
    *,
    capu_report: dict[str, Any] | None = None,
    morphos_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_inputs(trials, insufficient_rate)
    systems: dict[str, dict[str, Any]] = {
        "baseline_raw": run_raw_baseline(trials, insufficient_rate),
        "baseline_software_guarded": run_software_guarded_baseline(
            trials, insufficient_rate
        ),
        "proofbit": run_proofbit(trials, insufficient_rate),
        "capu": (
            validate_external(capu_report, trials, insufficient_rate)
            if capu_report is not None
            else _not_run("CaPU", "adapter JSON not supplied")
        ),
        "morphos": (
            validate_external(morphos_report, trials, insufficient_rate)
            if morphos_report is not None
            else _not_run("COSMIC ORGANICS / MORPHOS", "adapter JSON not supplied")
        ),
    }
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "scope": (
            "common binary-endpoint state-transition oracle with deterministic "
            "sufficient/insufficient support; software research benchmark, not a "
            "hardware-performance or universal architecture ranking"
        ),
        "oracle": {
            "valid": "final_state == target",
            "insufficient_support": "final_state == source",
        },
        "comparison_order": [
            "same workload",
            "oracle correctness",
            "false accept/reject behavior",
            "native evidence semantics",
            "speed and cost within the measured software boundary",
        ],
        "proof_semantics_not_numerically_equivalent": True,
        "no_single_winner_score": True,
        "unavailable_cost_metrics": [
            "hardware_energy",
            "silicon_area",
            "physical_memory_overhead",
        ],
        "systems": systems,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PB-TRANSITION-02.")
    parser.add_argument("--trials", type=int, default=10_000)
    parser.add_argument("--insufficient", type=float, default=0.10)
    parser.add_argument("--capu-json")
    parser.add_argument("--morphos-json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    capu = (
        json.loads(Path(args.capu_json).read_text(encoding="utf-8"))
        if args.capu_json
        else None
    )
    morphos = (
        json.loads(Path(args.morphos_json).read_text(encoding="utf-8"))
        if args.morphos_json
        else None
    )
    report = run_benchmark(
        args.trials,
        args.insufficient,
        capu_report=capu,
        morphos_report=morphos,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print(f"{BENCHMARK_ID} {VERSION} — {PROTOCOL}")
    for key, item in report["systems"].items():
        if item["status"] != "executed":
            print(f"{key:28} NOT RUN — {item['reason']}")
            continue
        print(
            f"{key:28} accuracy={item['oracle_accuracy']:.3f} "
            f"unsafe={item['unsafe_invalid_transitions']} "
            f"missed={item['missed_valid_transitions']} "
            f"speed={item['trials_per_sec']:.1f}/s "
            f"evidence={item['evidence_kind']}"
        )


if __name__ == "__main__":
    main()
