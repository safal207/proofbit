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


RATES = [0.0001, 0.001, 0.01, 0.05, 0.10, 0.25, 0.50]


def execute_baseline(iterations: int, contamination: float) -> dict:
    cpu = BaselineProcessor()
    unsafe = 0
    safe = 0
    cutoff = int((1.0 - contamination) * 10_000)

    for i in range(iterations):
        adversarial = (i % 10_000) >= cutoff
        cpu.store(0, True)
        if cpu.guarded_execute(0):
            if adversarial:
                unsafe += 1
            else:
                safe += 1

    return {"safe": safe, "unsafe": unsafe, "blocked_valid": 0}


def execute_proof(iterations: int, contamination: float) -> dict:
    cpu = ProofProcessor()
    unsafe = 0
    safe = 0
    blocked_valid = 0
    cutoff = int((1.0 - contamination) * 10_000)

    for i in range(iterations):
        bucket = i % 10_000
        adversarial = bucket >= cutoff
        proof_id = i + 50_000_000

        if not adversarial:
            cpu.store_evidence(0, Evidence("sweep_valid", True, proof_id, 1, 1))
        else:
            bad_index = (bucket - cutoff) % 5
            if bad_index == 0:
                cpu.store_unknown(0, "sweep_unknown", True)
            elif bad_index == 1:
                cpu.store_evidence(
                    0, Evidence("sweep_stale", True, proof_id, 1, 0)
                )
            elif bad_index == 2:
                cpu.consumed_proofs.add(proof_id)
                cpu.store_evidence(
                    0, Evidence("sweep_replay", True, proof_id, 1, 1)
                )
            elif bad_index == 3:
                cpu.store_conflict(0, "sweep_conflict")
            else:
                cpu.record_claimed_success_without_outcome_evidence(
                    0, "sweep_false_success"
                )

        allowed = cpu.guarded_execute(0)
        if allowed:
            if adversarial:
                unsafe += 1
            else:
                safe += 1
        elif not adversarial:
            blocked_valid += 1

    return {"safe": safe, "unsafe": unsafe, "blocked_valid": blocked_valid}


def measure(fn, iterations: int, contamination: float, rounds: int) -> dict:
    samples = []
    result = None
    for _ in range(rounds):
        start = time.perf_counter_ns()
        current = fn(iterations, contamination)
        elapsed = time.perf_counter_ns() - start
        samples.append(elapsed)
        if result is None:
            result = current
        elif result != current:
            raise RuntimeError("non-deterministic result")

    assert result is not None
    median_ns = statistics.median(samples)
    expected_valid = iterations - int(iterations * contamination)
    return {
        **result,
        "decisions_per_sec": iterations / (median_ns / 1_000_000_000),
        "safe_actions_per_sec": result["safe"] / (median_ns / 1_000_000_000),
        "unsafe_actions_per_million": result["unsafe"] / iterations * 1_000_000,
        "false_positive_block_rate": result["blocked_valid"] / max(1, expected_valid),
    }


def run(iterations: int, rounds: int) -> dict:
    cases = []
    for rate in RATES:
        cases.append(
            {
                "contamination_rate": rate,
                "baseline": measure(execute_baseline, iterations, rate, rounds),
                "proof": measure(execute_proof, iterations, rate, rounds),
            }
        )
    return {
        "benchmark_version": "0.2",
        "scope": "Deterministic Python semantic model; not silicon performance",
        "iterations_per_rate": iterations,
        "rounds": rounds,
        "rates": RATES,
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run(args.iterations, args.rounds)
    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("ProofBit contamination sweep")
    print(report["scope"])
    print()
    for case in report["cases"]:
        baseline = case["baseline"]
        proof = case["proof"]
        print(
            f"contamination={case['contamination_rate']:.2%} "
            f"unsafe/1M baseline={baseline['unsafe_actions_per_million']:.0f} "
            f"proof={proof['unsafe_actions_per_million']:.0f} "
            f"false_blocks={proof['false_positive_block_rate']:.3%}"
        )


if __name__ == "__main__":
    main()
