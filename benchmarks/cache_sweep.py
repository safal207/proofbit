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

from proofbit import CachedProofProcessor, Evidence, ProofProcessor


def measure_uncached(evidence_set, requests: int, rounds: int) -> dict:
    samples = []
    for _ in range(rounds):
        cpu = ProofProcessor()
        start = time.perf_counter_ns()
        for i in range(requests):
            cpu.verify(evidence_set[i % len(evidence_set)], consume=False)
        elapsed = time.perf_counter_ns() - start
        samples.append(elapsed / requests)

    median = statistics.median(samples)
    return {
        "median_ns_per_request": median,
        "requests_per_sec": 1_000_000_000 / median,
        "min_ns_per_request": min(samples),
        "max_ns_per_request": max(samples),
    }


def measure_cached(evidence_set, requests: int, rounds: int) -> dict:
    samples = []
    total_hits = 0
    total_misses = 0

    for _ in range(rounds):
        # New processor per round: cold-cache misses are counted every time.
        cpu = CachedProofProcessor()
        start = time.perf_counter_ns()
        for i in range(requests):
            cpu.verify(evidence_set[i % len(evidence_set)], consume=False)
        elapsed = time.perf_counter_ns() - start
        samples.append(elapsed / requests)
        stats = cpu.cache_stats()
        total_hits += stats.hits
        total_misses += stats.misses

    median = statistics.median(samples)
    total = total_hits + total_misses
    return {
        "median_ns_per_request": median,
        "requests_per_sec": 1_000_000_000 / median,
        "min_ns_per_request": min(samples),
        "max_ns_per_request": max(samples),
        "cache_hits": total_hits,
        "cache_misses": total_misses,
        "cache_hit_rate": total_hits / total if total else 0.0,
    }


def modeled_total_ns(raw_ns: float, verification_cost_ns: int, miss_rate: float) -> float:
    return raw_ns + verification_cost_ns * miss_rate


def run_case(working_set: int, requests: int, rounds: int, verifier_costs: list[int]) -> dict:
    evidence = [
        Evidence(f"cached-{i}", True, i + 1, 1, 1, i)
        for i in range(working_set)
    ]

    uncached_perf = measure_uncached(evidence, requests, rounds)
    cached_perf = measure_cached(evidence, requests, rounds)
    miss_rate = 1.0 - cached_perf["cache_hit_rate"]

    modeled = []
    for cost in verifier_costs:
        uncached_total = modeled_total_ns(
            uncached_perf["median_ns_per_request"], cost, 1.0
        )
        cached_total = modeled_total_ns(
            cached_perf["median_ns_per_request"], cost, miss_rate
        )
        modeled.append(
            {
                "verification_cost_ns": cost,
                "uncached_effective_ns_per_request": uncached_total,
                "cached_effective_ns_per_request": cached_total,
                "speedup": uncached_total / cached_total,
            }
        )

    return {
        "working_set": working_set,
        "requests": requests,
        "uncached": uncached_perf,
        "cached": cached_perf,
        "cache_hits": cached_perf["cache_hits"],
        "cache_misses": cached_perf["cache_misses"],
        "cache_hit_rate": cached_perf["cache_hit_rate"],
        "modeled_verifier_costs": modeled,
    }


def run(requests: int, rounds: int) -> dict:
    working_sets = [1, 8, 64, 1024]
    verifier_costs = [0, 1_000, 10_000, 100_000]
    return {
        "benchmark_version": "0.2.1",
        "scope": (
            "Cold-start-per-round Python cache microbenchmark plus explicit "
            "verifier-cost model; not silicon performance or a cryptographic benchmark"
        ),
        "requests_per_case": requests,
        "rounds": rounds,
        "verifier_costs_ns": verifier_costs,
        "cases": [
            run_case(size, requests, rounds, verifier_costs)
            for size in working_sets
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=100_000)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run(args.requests, args.rounds)
    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("ProofBit proof-cache sweep")
    print(report["scope"])
    print()
    for case in report["cases"]:
        print(
            f"working_set={case['working_set']:4d} "
            f"hit_rate={case['cache_hit_rate']:.2%} "
            f"raw_uncached={case['uncached']['median_ns_per_request']:.1f}ns "
            f"raw_cached={case['cached']['median_ns_per_request']:.1f}ns"
        )
        for modeled in case["modeled_verifier_costs"]:
            print(
                "  verifier="
                f"{modeled['verification_cost_ns']:>6d}ns "
                f"modeled_speedup={modeled['speedup']:.2f}x"
            )


if __name__ == "__main__":
    main()
