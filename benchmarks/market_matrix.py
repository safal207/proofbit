from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "hardware_reference.json"


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "systems" not in data or not isinstance(data["systems"], list):
        raise ValueError("hardware registry must contain a systems list")
    return data


def classify(system: dict[str, Any]) -> str:
    return "EXECUTABLE" if system.get("common_workload_ready") else "REFERENCE_ONLY"


def market_summary(registry: dict[str, Any]) -> dict[str, Any]:
    systems = registry["systems"]
    executable = [s for s in systems if classify(s) == "EXECUTABLE"]
    reference = [s for s in systems if classify(s) == "REFERENCE_ONLY"]
    competitors = [s for s in systems if s.get("vendor") != "ProofBit"]

    return {
        "schema_version": registry["schema_version"],
        "captured_at": registry["captured_at"],
        "ranking_rule": registry["rule"],
        "system_count": len(systems),
        "competitor_count": len(competitors),
        "executable_common_workload_count": len(executable),
        "reference_only_count": len(reference),
        "systems": [
            {
                "id": s["id"],
                "vendor": s["vendor"],
                "product": s["product"],
                "class": s["class"],
                "scale": s["scale"],
                "benchmark_tier": classify(s),
                "proof_native": s.get("proof_native"),
            }
            for s in systems
        ],
    }


def print_table(summary: dict[str, Any]) -> None:
    print("ProofBit market benchmark matrix")
    print(f"captured_at: {summary['captured_at']}")
    print(summary["ranking_rule"])
    print()
    print(f"{'Vendor':<18} {'Product':<28} {'Scale':<18} {'Tier':<16}")
    print("-" * 84)
    for system in summary["systems"]:
        print(
            f"{system['vendor']:<18} "
            f"{system['product']:<28} "
            f"{system['scale']:<18} "
            f"{system['benchmark_tier']:<16}"
        )
    print()
    print(
        "Only EXECUTABLE entries may currently be compared on ProofBit workload "
        "results. REFERENCE_ONLY entries are architectural market anchors until "
        "the same workload is run on real hardware."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    summary = market_summary(load_registry())
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print_table(summary)


if __name__ == "__main__":
    main()
