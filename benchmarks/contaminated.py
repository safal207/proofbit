from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit import BaselineProcessor, Evidence, ProofProcessor


COMPOSITION = (
    "90% valid + 10% adversarial "
    "(UNKNOWN/STALE/REPLAY/CONFLICT/FALSE_SUCCESS)"
)


def baseline_workload(iterations: int) -> dict:
    cpu = BaselineProcessor()
    safe_actions = 0
    unsafe_actions = 0

    for i in range(iterations):
        adversarial = (i % 100) >= 90
        cpu.store(0, True)
        if cpu.guarded_execute(0):
            if adversarial:
                unsafe_actions += 1
            else:
                safe_actions += 1

    return {
        "safe_actions": safe_actions,
        "unsafe_actions": unsafe_actions,
        "blocked_valid_actions": 0,
    }


def proof_workload(iterations: int) -> dict:
    cpu = ProofProcessor()
    safe_actions = 0
    unsafe_actions = 0
    blocked_valid_actions = 0

    for i in range(iterations):
        bucket = i % 100
        proof_id = i + 10_000_000
        is_valid = bucket < 90

        if is_valid:
            cpu.store_evidence(0, Evidence("mixed", True, proof_id, 1, 1))
        elif bucket < 92:
            cpu.store_unknown(0, "mixed_unknown", True)
        elif bucket < 94:
            cpu.store_evidence(0, Evidence("mixed_stale", True, proof_id, 1, 0))
        elif bucket < 96:
            replay = Evidence("mixed_replay", True, proof_id, 1, 1)
            cpu.consumed_proofs.add(proof_id)
            cpu.store_evidence(0, replay)
        elif bucket < 98:
            cpu.store_conflict(0, "mixed_conflict")
        else:
            cpu.record_claimed_success_without_outcome_evidence(
                0, "mixed_false_success"
            )

        allowed = cpu.guarded_execute(0)
        if allowed:
            if is_valid:
                safe_actions += 1
            else:
                unsafe_actions += 1
        elif is_valid:
            blocked_valid_actions += 1

    return {
        "safe_actions": safe_actions,
        "unsafe_actions": unsafe_actions,
        "blocked_valid_actions": blocked_valid_actions,
    }


def measure(fn, iterations: int, rounds: int) -> dict:
    elapsed_samples = []
    result = None

    for _ in range(rounds):
        start = time.perf_counter_ns()
        current = fn(iterations)
        elapsed = time.perf_counter_ns() - start
        elapsed_samples.append(elapsed)
        if result is None:
            result = current
        elif result != current:
            raise RuntimeError("deterministic benchmark produced inconsistent counts")

    assert result is not None
    median_elapsed_ns = statistics.median(elapsed_samples)
    valid_actions = int(iterations * 0.90)

    return {
        **result,
        "median_elapsed_ns": median_elapsed_ns,
        "decisions_per_sec": iterations / (median_elapsed_ns / 1_000_000_000),
        "safe_actions_per_sec": result["safe_actions"]
        / (median_elapsed_ns / 1_000_000_000),
        "unsafe_actions_per_million_decisions": result["unsafe_actions"]
        / iterations
        * 1_000_000,
        "false_positive_block_rate": result["blocked_valid_actions"]
        / max(1, valid_actions),
    }


def run(iterations: int, rounds: int) -> dict:
    return {
        "benchmark_version": "0.2-seed",
        "scope": "Python semantic reference model; not hardware performance",
        "composition": COMPOSITION,
        "iterations_per_round": iterations,
        "rounds": rounds,
        "baseline": measure(baseline_workload, iterations, rounds),
        "proof": measure(proof_workload, iterations, rounds),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run(args.iterations, args.rounds)
    if args.json:
        print(json.dumps(report, indent=2))
        return

    baseline = report["baseline"]
    proof = report["proof"]
    print("ProofBit contaminated-memory benchmark")
    print(report["scope"])
    print(report["composition"])
    print()
    print(
        "unsafe actions / 1M decisions: "
        f"baseline={baseline['unsafe_actions_per_million_decisions']:,.0f} "
        f"proof={proof['unsafe_actions_per_million_decisions']:,.0f}"
    )
    print(
        "safe useful actions/s: "
        f"baseline={baseline['safe_actions_per_sec']:,.0f} "
        f"proof={proof['safe_actions_per_sec']:,.0f}"
    )
    print(
        "false-positive block rate: "
        f"baseline={baseline['false_positive_block_rate']:.3%} "
        f"proof={proof['false_positive_block_rate']:.3%}"
    )


if __name__ == "__main__":
    main()
