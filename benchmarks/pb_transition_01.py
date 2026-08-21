from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path | None) -> dict | None:
    if path is None:
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_report(morphos_json: Path | None = None) -> dict:
    morphos = _load(morphos_json)
    if morphos is not None:
        if morphos.get("benchmark_id") != "PB-TRANSITION-01":
            raise ValueError("external MORPHOS result is not PB-TRANSITION-01")
        if morphos.get("status") != "executed":
            raise ValueError("external MORPHOS PB-TRANSITION-01 result was not executed")
        provenance = morphos.get("frozen_provenance", {})
        if provenance.get("mechanism_blob_matches_frozen") is not True:
            raise ValueError("external MORPHOS mechanism does not match frozen provenance")

    return {
        "benchmark_id": "PB-TRANSITION-01",
        "version": "0.1",
        "scope": (
            "Cross-architecture transition/recovery capability map. Native MORPHOS "
            "lattice throughput is not ranked against PB-ARCH-01 guard throughput."
        ),
        "systems": {
            "conventional_cpu": {
                "architecture": "conventional host CPU",
                "status": "host_only_no_transition_adapter",
                "reason": (
                    "The CPU executes the simulator but does not by itself define "
                    "the frozen MORPHOS transition/recovery semantics."
                ),
            },
            "proofbit": {
                "architecture": "ProofBit ProofProcessor",
                "status": "not_run_adapter_needed",
                "reason": (
                    "ProofBit v0.1 models justified state and guarded execution, "
                    "not the frozen A/M/C lattice transition workload."
                ),
            },
            "capu": {
                "architecture": "CaPU",
                "status": "not_run_adapter_needed",
                "reason": (
                    "CaPU models causal legitimacy and commit-before-effect, but "
                    "has not yet executed the frozen MORPHOS lattice workload."
                ),
            },
            "morphos": morphos
            if morphos is not None
            else {
                "architecture": "COSMIC ORGANICS / MORPHOS",
                "status": "not_run",
                "reason": "No machine-readable MORPHOS PB-TRANSITION-01 result supplied.",
            },
        },
        "comparison_dimensions": [
            "transition recovery utility",
            "causal evidence / frozen provenance",
            "regression rate",
            "software simulation cost",
            "native-workload speed",
        ],
        "ranking_rule": (
            "First compare whether the architecture executed the same transition "
            "workload and which semantics it covers. Rank raw speed only after "
            "common adapters exist for the same frozen task."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate ProofBit PB-TRANSITION-01.")
    parser.add_argument("--morphos-json", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report(args.morphos_json)
    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("ProofBit PB-TRANSITION-01 v0.1")
    for name, system in report["systems"].items():
        print(f"{name:18s} status={system['status']}")
        if name == "morphos" and system["status"] == "executed":
            utility = system["utility"]
            speed = system["cost_speed"]
            print(
                "  causal_rescues="
                f"{utility['causal_rescues']}/{utility['predecessor_failures']}"
            )
            print(
                "  exact@8="
                f"{utility['minimum_exact_recovery_at_8']:.2%}"
            )
            print(f"  trials_per_sec={speed['trials_per_sec']:,.2f}")


if __name__ == "__main__":
    main()
