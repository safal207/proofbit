#!/usr/bin/env python3
"""Aggregate repeated PB-TRUST-COMPOSE-02 runs using medians."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
from typing import Any

SYSTEMS = ("software_json", "software_compact", "proofbit_compact")


def load_reports(paths: list[Path]) -> list[dict[str, Any]]:
    if len(paths) < 3:
        raise ValueError("PB-TC02 median summary requires at least 3 rounds")
    reports = [json.loads(path.read_text()) for path in paths]
    first = reports[0]
    for report in reports:
        if report.get("benchmark_id") != "PB-TRUST-COMPOSE-02":
            raise ValueError("benchmark_id mismatch")
        if report.get("version") != first.get("version"):
            raise ValueError("version mismatch")
        if report.get("protocol") != first.get("protocol"):
            raise ValueError("protocol mismatch")
        if report.get("trials") != first.get("trials"):
            raise ValueError("trial count mismatch")
        if report.get("boundaries") != first.get("boundaries"):
            raise ValueError("boundary set mismatch")
        if report.get("fault_counts") != first.get("fault_counts"):
            raise ValueError("fault schedule mismatch")
    return reports


def summarize(reports: list[dict[str, Any]]) -> dict[str, Any]:
    first = reports[0]
    boundary_rows: list[dict[str, Any]] = []

    for boundary_index, boundary in enumerate(first["boundaries"]):
        systems: dict[str, Any] = {}
        for name in SYSTEMS:
            samples = [report["scale"][boundary_index]["systems"][name] for report in reports]
            for sample in samples:
                if sample["oracle_accuracy"] != 1.0:
                    raise ValueError(f"{name} lost oracle correctness")
                if sample["unsafe_authorization_dispatches"] != 0:
                    raise ValueError(f"{name} produced unsafe dispatch")
                if sample["false_success_claims"] != 0:
                    raise ValueError(f"{name} produced false-success claim")
                if sample["missed_valid_dispatches"] != 0:
                    raise ValueError(f"{name} missed valid dispatch")

            invariant_fields = (
                "mean_payload_bytes",
                "request_ipc_payload_bytes",
                "response_ipc_payload_bytes",
                "total_ipc_payload_bytes",
                "transport_messages",
            )
            for field in invariant_fields:
                values = {sample[field] for sample in samples}
                if len(values) != 1:
                    raise ValueError(f"{name} changed deterministic field {field}: {values}")

            throughputs = [float(sample["trials_per_sec"]) for sample in samples]
            elapsed = [int(sample["elapsed_ns"]) for sample in samples]
            systems[name] = {
                "rounds": len(samples),
                "median_trials_per_sec": statistics.median(throughputs),
                "min_trials_per_sec": min(throughputs),
                "max_trials_per_sec": max(throughputs),
                "median_elapsed_ns": statistics.median(elapsed),
                "mean_payload_bytes": samples[0]["mean_payload_bytes"],
                "request_ipc_payload_bytes": samples[0]["request_ipc_payload_bytes"],
                "response_ipc_payload_bytes": samples[0]["response_ipc_payload_bytes"],
                "total_ipc_payload_bytes": samples[0]["total_ipc_payload_bytes"],
                "transport_messages": samples[0]["transport_messages"],
                "oracle_accuracy": 1.0,
                "unsafe_authorization_dispatches": 0,
                "false_success_claims": 0,
                "missed_valid_dispatches": 0,
                "raw_trials_per_sec": throughputs,
            }

        proof = systems["proofbit_compact"]["median_trials_per_sec"]
        compact = systems["software_compact"]["median_trials_per_sec"]
        json_sw = systems["software_json"]["median_trials_per_sec"]
        boundary_rows.append(
            {
                "boundaries": boundary,
                "systems": systems,
                "median_throughput_ratios": {
                    "proofbit_vs_software_compact": proof / compact,
                    "proofbit_vs_software_json": proof / json_sw,
                },
            }
        )

    return {
        "benchmark_id": "PB-TRUST-COMPOSE-02",
        "version": first["version"],
        "protocol": first["protocol"],
        "summary_method": "median of independent full pipeline rounds",
        "rounds": len(reports),
        "trials_per_round": first["trials"],
        "contamination_rate": first["contamination_rate"],
        "boundaries": first["boundaries"],
        "fault_counts": first["fault_counts"],
        "compact_record_bytes": first["compact_record_bytes"],
        "result_record_bytes": first["result_record_bytes"],
        "scale": boundary_rows,
        "no_single_winner_score": True,
        "interpretation_rule": (
            "Compare compact ProofBit against compact conventional software for semantic overhead; "
            "JSON comparisons primarily expose encoding/payload effects."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = summarize(load_reports(args.reports))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for row in report["scale"]:
            systems = row["systems"]
            print(
                f"boundaries={row['boundaries']} "
                f"json={systems['software_json']['median_trials_per_sec']:.1f}/s "
                f"compact={systems['software_compact']['median_trials_per_sec']:.1f}/s "
                f"proofbit={systems['proofbit_compact']['median_trials_per_sec']:.1f}/s "
                f"PB/compact={row['median_throughput_ratios']['proofbit_vs_software_compact']:.3f}x"
            )


if __name__ == "__main__":
    main()
