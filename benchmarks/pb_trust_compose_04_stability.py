from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "pb_trust_compose_04.py"
SPEC = importlib.util.spec_from_file_location("pb_trust_compose_04_base", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
pb = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pb
SPEC.loader.exec_module(pb)


def run_stability(
    transactions: int = 500,
    rounds: int = 11,
    audit_sample: int = 25,
) -> dict:
    if rounds <= 0:
        raise ValueError("rounds must be positive")

    canonical = ("software_scan", "software_indexed", "proofbit_receipts")
    per_system: dict[str, list[dict]] = {name: [] for name in canonical}
    orders: list[list[str]] = []

    for round_index in range(rounds):
        shift = round_index % len(canonical)
        order = canonical[shift:] + canonical[:shift]
        orders.append(list(order))
        pb.SYSTEMS = order
        report = pb.run_benchmark(
            transactions=transactions,
            rounds=1,
            audit_sample=audit_sample,
        )
        for name in canonical:
            system = report["systems"][name]
            median = system["median"]
            per_system[name].append(
                {
                    "oracle_accuracy": system["oracle_accuracy"],
                    "duplicate_side_effects_after_retry": system[
                        "duplicate_side_effects_after_retry"
                    ],
                    "false_terminal_success": system["false_terminal_success"],
                    "ambiguous_terminal_states": system[
                        "ambiguous_terminal_states"
                    ],
                    "hard_crash_exit_code": system["hard_crash_exit_codes"][0],
                    "trusted_recovered_states_per_sec": median[
                        "trusted_recovered_states_per_sec"
                    ],
                    "recovery_elapsed_ns": median["recovery_elapsed_ns"],
                    "restart_wall_ns": median["restart_wall_ns"],
                    "persisted_total_bytes": median["persisted_total_bytes"],
                    "full_recovery_records_inspected": median[
                        "full_recovery_records_inspected"
                    ],
                    "targeted_audit_records_inspected": median[
                        "targeted_audit_records_inspected"
                    ],
                }
            )

    summary = {}
    for name in canonical:
        rows = per_system[name]
        summary[name] = {
            "oracle_accuracy": min(row["oracle_accuracy"] for row in rows),
            "duplicate_side_effects_after_retry": sum(
                row["duplicate_side_effects_after_retry"] for row in rows
            ),
            "false_terminal_success": sum(
                row["false_terminal_success"] for row in rows
            ),
            "ambiguous_terminal_states": sum(
                row["ambiguous_terminal_states"] for row in rows
            ),
            "hard_crash_exit_codes": [
                row["hard_crash_exit_code"] for row in rows
            ],
            "median_trusted_recovered_states_per_sec": statistics.median(
                row["trusted_recovered_states_per_sec"] for row in rows
            ),
            "median_recovery_elapsed_ns": statistics.median(
                row["recovery_elapsed_ns"] for row in rows
            ),
            "median_restart_wall_ns": statistics.median(
                row["restart_wall_ns"] for row in rows
            ),
            "median_persisted_total_bytes": statistics.median(
                row["persisted_total_bytes"] for row in rows
            ),
            "median_full_recovery_records_inspected": statistics.median(
                row["full_recovery_records_inspected"] for row in rows
            ),
            "median_targeted_audit_records_inspected": statistics.median(
                row["targeted_audit_records_inspected"] for row in rows
            ),
            "raw_trusted_recovered_states_per_sec": [
                row["trusted_recovered_states_per_sec"] for row in rows
            ],
        }

    indexed = summary["software_indexed"]
    proof = summary["proofbit_receipts"]
    return {
        "benchmark_id": "PB-TRUST-COMPOSE-04-STABILITY",
        "version": "0.1",
        "base_protocol": pb.PROTOCOL,
        "transactions_per_round": transactions,
        "rounds": rounds,
        "audit_sample_transactions": min(audit_sample, transactions),
        "measurement_orders": orders,
        "systems": summary,
        "primary_ratios": {
            "proofbit_vs_software_indexed_recovery_throughput": (
                proof["median_trusted_recovered_states_per_sec"]
                / indexed["median_trusted_recovered_states_per_sec"]
            ),
            "proofbit_vs_software_indexed_persisted_bytes": (
                proof["median_persisted_total_bytes"]
                / indexed["median_persisted_total_bytes"]
            ),
            "proofbit_vs_software_indexed_targeted_audit_records": (
                proof["median_targeted_audit_records_inspected"]
                / indexed["median_targeted_audit_records_inspected"]
            ),
        },
        "fairness": (
            "system execution order rotates every round; software_indexed and "
            "proofbit_receipts retain identical 48-byte journal records and "
            "8-byte per-transaction head indexes"
        ),
        "no_single_winner_score": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", type=int, default=500)
    parser.add_argument("--rounds", type=int, default=11)
    parser.add_argument("--audit-sample", type=int, default=25)
    args = parser.parse_args()
    print(
        json.dumps(
            run_stability(args.transactions, args.rounds, args.audit_sample),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
