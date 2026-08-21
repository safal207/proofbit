from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.pb_arch_01 import build_report as build_arch_report


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_morphos(report: dict) -> None:
    if report.get("benchmark_id") != "PB-TRANSITION-01":
        raise ValueError("MORPHOS result is not PB-TRANSITION-01")
    if report.get("architecture") != "COSMIC ORGANICS / MORPHOS":
        raise ValueError("unexpected MORPHOS architecture identity")
    if report.get("status") != "executed":
        raise ValueError("MORPHOS PB-TRANSITION-01 was not executed")
    if report.get("frozen_provenance", {}).get("mechanism_blob_matches_frozen") is not True:
        raise ValueError("MORPHOS frozen mechanism provenance does not match")
    if report.get("proof", {}).get("decision") != "TRANSFER_PASS":
        raise ValueError("MORPHOS frozen transfer contract did not pass")


def build_scorecard(
    capu_json: Path,
    morphos_json: Path,
    decisions: int = 10_000,
    contamination_rate: float = 0.10,
) -> dict:
    arch = build_arch_report(decisions, contamination_rate, capu_json)
    morphos = _load_json(morphos_json)
    _validate_morphos(morphos)

    baseline = arch["systems"]["baseline"]
    proofbit = arch["systems"]["proofbit"]
    capu = arch["systems"]["capu"]

    return {
        "benchmark_id": "PB-RESEARCH-01",
        "version": "0.1",
        "scope": (
            "Cross-domain research architecture scorecard. Systems retain their native "
            "workload semantics; raw throughput is rankable only inside the same "
            "comparability group."
        ),
        "systems": {
            "baseline": {
                "architecture": baseline["architecture"],
                "workload": "PB-ARCH-01",
                "utility": {
                    "safe_actions": baseline["safe_actions"],
                    "unsafe_actions": baseline["unsafe_actions"],
                    "blocked_valid_actions": baseline["blocked_valid_actions"],
                },
                "proof": {
                    "fault_kind_coverage": baseline["failure_kind_coverage"],
                    "semantics": baseline["failure_semantics"],
                },
                "speed": {
                    "decisions_per_sec": baseline["decisions_per_sec"],
                    "comparability_group": "PB-ARCH-01-boundary-decisions",
                },
            },
            "proofbit": {
                "architecture": proofbit["architecture"],
                "workload": "PB-ARCH-01",
                "utility": {
                    "safe_actions": proofbit["safe_actions"],
                    "unsafe_actions": proofbit["unsafe_actions"],
                    "blocked_valid_actions": proofbit["blocked_valid_actions"],
                },
                "proof": {
                    "fault_kind_coverage": proofbit["failure_kind_coverage"],
                    "semantics": proofbit["failure_semantics"],
                },
                "speed": {
                    "decisions_per_sec": proofbit["decisions_per_sec"],
                    "comparability_group": "PB-ARCH-01-boundary-decisions",
                },
            },
            "capu": {
                "architecture": capu["architecture"],
                "workload": "PB-ARCH-01",
                "utility": {
                    "safe_actions": capu["safe_actions"],
                    "unsafe_actions_on_supported_semantics": capu[
                        "unsafe_actions_on_supported_semantics"
                    ],
                    "unsupported_decisions": capu["unsupported_decisions"],
                },
                "proof": {
                    "fault_kind_coverage": capu["failure_kind_coverage"],
                    "failure_kind_support": capu["failure_kind_support"],
                },
                "speed": {
                    "supported_decisions_per_sec": capu[
                        "supported_decisions_per_sec"
                    ],
                    "comparability_group": "PB-ARCH-01-boundary-decisions",
                },
            },
            "morphos": {
                "architecture": morphos["architecture"],
                "workload": "PB-TRANSITION-01",
                "utility": morphos["utility"],
                "proof": {
                    "decision": morphos["proof"]["decision"],
                    "recovery_and_controls_pass": morphos["proof"][
                        "recovery_and_controls_pass"
                    ],
                    "mechanism_blob_matches_frozen": morphos[
                        "frozen_provenance"
                    ]["mechanism_blob_matches_frozen"],
                    "continuation_only_no_retuning": morphos[
                        "frozen_provenance"
                    ]["continuation_only_no_retuning"],
                },
                "speed": {
                    "trials_per_sec": morphos["cost_speed"]["trials_per_sec"],
                    "comparability_group": "PB-TRANSITION-01-morphos-trials",
                },
                "claim_boundary": morphos["claim_boundary"],
            },
        },
        "comparability": {
            "PB-ARCH-01-boundary-decisions": ["baseline", "proofbit", "capu"],
            "PB-TRANSITION-01-morphos-trials": ["morphos"],
            "rule": (
                "Never rank decisions/sec against MORPHOS trials/sec or against "
                "accelerator FLOPS. Compare utility/proof coverage across domains, "
                "then compare speed/cost only within a frozen common workload."
            ),
        },
        "four_axis_rule": ["utility", "proof", "cost", "speed"],
        "no_synthetic_overall_score": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the ProofBit research architecture scorecard.")
    parser.add_argument("--capu-json", type=Path, required=True)
    parser.add_argument("--morphos-json", type=Path, required=True)
    parser.add_argument("--decisions", type=int, default=10_000)
    parser.add_argument("--contamination", type=float, default=0.10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_scorecard(
        args.capu_json,
        args.morphos_json,
        args.decisions,
        args.contamination,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print("ProofBit PB-RESEARCH-01 v0.1")
    for key, system in report["systems"].items():
        speed = system["speed"]
        print(f"{key:10s} workload={system['workload']} speed={speed}")


if __name__ == "__main__":
    main()
