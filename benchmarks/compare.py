from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit import BaselineProcessor, Evidence, ProofProcessor


def measure(fn, iterations: int, rounds: int) -> dict:
    samples = []
    for _ in range(rounds):
        start = time.perf_counter_ns()
        fn(iterations)
        elapsed_ns = time.perf_counter_ns() - start
        samples.append(elapsed_ns / iterations)

    median_ns = statistics.median(samples)
    return {
        "median_ns_per_iteration": median_ns,
        "median_iterations_per_sec": 1_000_000_000 / median_ns,
        "min_ns_per_iteration": min(samples),
        "max_ns_per_iteration": max(samples),
        "rounds": rounds,
    }


def baseline_memory_workload(iterations: int) -> None:
    cpu = BaselineProcessor()
    for i in range(iterations):
        address = i & 1023
        cpu.store(address, bool(i & 1))
        cpu.load(address)


def proof_memory_workload(iterations: int) -> None:
    cpu = ProofProcessor()
    for i in range(iterations):
        address = i & 1023
        ev = Evidence("bench", bool(i & 1), i + 1, 1, 1, i & 255)
        cpu.store_evidence(address, ev)
        cpu.load(address)


def safety_suite() -> dict:
    results = {}

    b = BaselineProcessor()
    b.store(0, True)
    p = ProofProcessor()
    p.store_evidence(0, Evidence("normal", True, 1, 1, 1))
    results["NORMAL"] = {
        "baseline_allowed": b.guarded_execute(0),
        "proof_allowed": p.guarded_execute(0),
        "expected": "allow",
    }

    b = BaselineProcessor()
    b.store(0, True)
    p = ProofProcessor()
    p.store_unknown(0, "unknown", True)
    results["UNKNOWN"] = {
        "baseline_allowed": b.guarded_execute(0),
        "proof_allowed": p.guarded_execute(0),
        "expected": "block",
    }

    b = BaselineProcessor()
    b.store(0, True)
    p = ProofProcessor(epoch=2)
    p.store_evidence(0, Evidence("stale", True, 2, 1, 1))
    results["STALE"] = {
        "baseline_allowed": b.guarded_execute(0),
        "proof_allowed": p.guarded_execute(0),
        "expected": "block",
    }

    b = BaselineProcessor()
    b.store(0, True)
    p = ProofProcessor()
    p.store_evidence(0, Evidence("single_use", True, 3, 1, 1))
    b_first = b.guarded_execute(0)
    b_second = b.guarded_execute(0)
    p_first = p.guarded_execute(0)
    p_second = p.guarded_execute(0)
    results["REPLAY"] = {
        "baseline_allowed": b_first and b_second,
        "proof_allowed": p_first and p_second,
        "proof_first_allowed": p_first,
        "proof_second_allowed": p_second,
        "expected": "first allow, second block",
    }

    b = BaselineProcessor()
    b.store(0, True)
    p = ProofProcessor()
    p.store_conflict(0, "conflict")
    results["CONFLICT"] = {
        "baseline_allowed": b.guarded_execute(0),
        "proof_allowed": p.guarded_execute(0),
        "expected": "block",
    }

    b = BaselineProcessor()
    b.store(0, True)
    p = ProofProcessor()
    p.record_claimed_success_without_outcome_evidence(0, "outcome_success")
    results["FALSE_SUCCESS"] = {
        "baseline_allowed": b.guarded_execute(0),
        "proof_allowed": p.guarded_execute(0),
        "expected": "block",
    }

    return results


def score_safety(results: dict) -> dict:
    adversarial = ["UNKNOWN", "STALE", "REPLAY", "CONFLICT", "FALSE_SUCCESS"]
    baseline_prevented = sum(not results[k]["baseline_allowed"] for k in adversarial)
    proof_prevented = sum(not results[k]["proof_allowed"] for k in adversarial)
    return {
        "adversarial_cases": len(adversarial),
        "baseline_prevented": baseline_prevented,
        "proof_prevented": proof_prevented,
        "baseline_prevention_rate": baseline_prevented / len(adversarial),
        "proof_prevention_rate": proof_prevented / len(adversarial),
        "normal_baseline_allowed": results["NORMAL"]["baseline_allowed"],
        "normal_proof_allowed": results["NORMAL"]["proof_allowed"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare value-only and proof-aware reference models.")
    parser.add_argument("--iterations", type=int, default=100_000)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    baseline_perf = measure(baseline_memory_workload, args.iterations, args.rounds)
    proof_perf = measure(proof_memory_workload, args.iterations, args.rounds)
    overhead = (
        proof_perf["median_ns_per_iteration"]
        / baseline_perf["median_ns_per_iteration"]
    )

    safety = safety_suite()
    scores = score_safety(safety)

    baseline_bytes = 8
    proof_bytes = 8 + 1 + (4 * 8)

    report = {
        "benchmark_version": "0.1",
        "benchmark_scope": "Python reference-model benchmark; not silicon performance",
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "iterations_per_round": args.iterations,
        "performance": {
            "workload": "one store + one load per iteration",
            "baseline": baseline_perf,
            "proof": proof_perf,
            "runtime_overhead_ratio": overhead,
        },
        "logical_storage_estimate": {
            "baseline_bytes_per_cell": baseline_bytes,
            "proof_bytes_per_cell": proof_bytes,
            "metadata_overhead_ratio": proof_bytes / baseline_bytes,
            "note": "Conceptual packed-layout estimate, not Python object memory or final hardware layout.",
        },
        "safety": scores,
        "cases": safety,
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("ProofBit benchmark v0.1")
    print(report["benchmark_scope"])
    print()
    print(f"iterations/round: {args.iterations:,} | rounds: {args.rounds}")
    print(
        "baseline: "
        f"{baseline_perf['median_iterations_per_sec']:,.0f} iterations/s | "
        f"{baseline_perf['median_ns_per_iteration']:,.1f} ns/iteration"
    )
    print(
        "proof:    "
        f"{proof_perf['median_iterations_per_sec']:,.0f} iterations/s | "
        f"{proof_perf['median_ns_per_iteration']:,.1f} ns/iteration"
    )
    print(f"runtime overhead ratio: {overhead:.2f}x")
    print()
    print(
        "adversarial prevention: "
        f"baseline {scores['baseline_prevented']}/{scores['adversarial_cases']} | "
        f"proof {scores['proof_prevented']}/{scores['adversarial_cases']}"
    )
    print(
        "normal work allowed: "
        f"baseline={scores['normal_baseline_allowed']} "
        f"proof={scores['normal_proof_allowed']}"
    )
    print(
        "logical bytes/cell estimate: "
        f"baseline={baseline_bytes} proof={proof_bytes} "
        f"({proof_bytes / baseline_bytes:.2f}x)"
    )


if __name__ == "__main__":
    main()
