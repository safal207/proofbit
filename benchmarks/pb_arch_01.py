from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.ai_workload import FAILURE_KINDS, build_workload, run_baseline, run_proof


def _proofbit_reference(decisions: int, contamination_rate: float) -> dict:
    workload = build_workload(decisions, contamination_rate)
    scores = [1] * decisions

    baseline = run_baseline(workload, scores)
    proof = run_proof(workload, scores)
    normal = sum(row.kind == "NORMAL" for row in workload)
    adversarial = decisions - normal

    return {
        "baseline": {
            "architecture": "conventional-value-only-reference",
            "status": "executed_full_stream",
            "decisions": decisions,
            "normal_decisions": normal,
            "adversarial_decisions": adversarial,
            "safe_actions": baseline["safe_actions"],
            "unsafe_actions": baseline["unsafe_actions"],
            "blocked_valid_actions": baseline["blocked_valid_actions"],
            "elapsed_ns": baseline["guard_elapsed_ns"],
            "decisions_per_sec": baseline["guard_decisions_per_sec"],
            "useful_actions_per_sec": baseline["useful_actions_per_sec"],
            "failure_kind_coverage": 0.0,
            "failure_semantics": {
                kind: "collapsed_to_value_true" for kind in FAILURE_KINDS
            },
            "unsafe_actions_per_million": baseline["unsafe_actions_per_million"],
            "false_positive_block_rate": (
                baseline["blocked_valid_actions"] / normal if normal else 0.0
            ),
            "claim_boundary": (
                "The value-only baseline executes the full stream but does not "
                "represent the five fault classes as native execution semantics."
            ),
        },
        "proofbit": {
            "architecture": "ProofBit-ProofProcessor",
            "status": "executed_full_stream",
            "decisions": decisions,
            "normal_decisions": normal,
            "adversarial_decisions": adversarial,
            "safe_actions": proof["safe_actions"],
            "unsafe_actions": proof["unsafe_actions"],
            "blocked_valid_actions": proof["blocked_valid_actions"],
            "elapsed_ns": proof["guard_elapsed_ns"],
            "decisions_per_sec": proof["guard_decisions_per_sec"],
            "useful_actions_per_sec": proof["useful_actions_per_sec"],
            "failure_kind_coverage": 1.0,
            "failure_semantics": {kind: "supported_blocked" for kind in FAILURE_KINDS},
            "unsafe_actions_per_million": proof["unsafe_actions_per_million"],
            "false_positive_block_rate": (
                proof["blocked_valid_actions"] / normal if normal else 0.0
            ),
            "claim_boundary": (
                "Coverage refers only to the five frozen PB-ARCH-01 semantic "
                "fault classes in the current software reference model."
            ),
        },
    }


def _load_external(path: Path | None) -> dict | None:
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_report(
    decisions: int = 10_000,
    contamination_rate: float = 0.10,
    capu_json: Path | None = None,
) -> dict:
    if decisions <= 0:
        raise ValueError("decisions must be positive")
    if not 0 <= contamination_rate <= 1:
        raise ValueError("contamination_rate must be between 0 and 1")

    references = _proofbit_reference(decisions, contamination_rate)
    capu = _load_external(capu_json)

    if capu is not None:
        if capu.get("benchmark_id") != "PB-ARCH-01":
            raise ValueError("external CaPU result is not PB-ARCH-01")
        if capu.get("decisions") != decisions:
            raise ValueError("external CaPU decision count does not match")
        if abs(float(capu.get("contamination_rate")) - contamination_rate) > 1e-9:
            raise ValueError("external CaPU contamination rate does not match")

    return {
        "benchmark_id": "PB-ARCH-01",
        "version": "0.1",
        "scope": (
            "Cross-architecture execution-boundary comparison. Fault classes are "
            "never credited as prevented when an adapter reports them unsupported."
        ),
        "decisions": decisions,
        "contamination_rate": contamination_rate,
        "failure_kinds": list(FAILURE_KINDS),
        "systems": {
            "baseline": references["baseline"],
            "proofbit": references["proofbit"],
            "capu": capu
            if capu is not None
            else {
                "architecture": "CaPU",
                "status": "not_run",
                "reason": "No machine-readable CaPU PB-ARCH-01 result supplied.",
            },
        },
        "ranking_rule": (
            "Do not rank raw speed across systems with different semantic coverage. "
            "Compare coverage first, then safety within covered semantics, then speed/cost."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ProofBit PB-ARCH-01.")
    parser.add_argument("--decisions", type=int, default=10_000)
    parser.add_argument("--contamination", type=float, default=0.10)
    parser.add_argument("--capu-json", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report(args.decisions, args.contamination, args.capu_json)
    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("ProofBit PB-ARCH-01 v0.1")
    print(f"decisions={report['decisions']:,} contamination={report['contamination_rate']:.2%}")
    print()
    for key in ("baseline", "proofbit", "capu"):
        system = report["systems"][key]
        print(f"{key:10s} status={system['status']}")
        if system["status"] == "not_run":
            continue
        coverage = system.get("failure_kind_coverage")
        if coverage is not None:
            print(f"  failure-kind coverage={coverage:.0%}")
        if "unsafe_actions" in system:
            print(f"  unsafe_actions={system['unsafe_actions']}")
        elif "unsafe_actions_on_supported_semantics" in system:
            print(
                "  unsafe_actions_on_supported_semantics="
                f"{system['unsafe_actions_on_supported_semantics']}"
            )
        speed = system.get("decisions_per_sec", system.get("supported_decisions_per_sec"))
        if speed is not None:
            print(f"  measured_decisions_per_sec={speed:,.0f}")


if __name__ == "__main__":
    main()
