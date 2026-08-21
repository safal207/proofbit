from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.ai_workload import BACKENDS, run_pb_ai_01


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the frozen PB-AI-01 proof-aware agent-action benchmark."
    )
    parser.add_argument("--backend", default="cpu-python")
    parser.add_argument("--decisions", type=int, default=10_000)
    parser.add_argument("--contamination", type=float, default=0.10)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list-backends", action="store_true")
    args = parser.parse_args()

    if args.list_backends:
        payload = [asdict(BACKENDS[key]) for key in sorted(BACKENDS)]
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            for backend in payload:
                print(
                    f"{backend['id']:18s} "
                    f"status={backend['status']:25s} "
                    f"target={backend['target_system']}"
                )
        return

    report = run_pb_ai_01(
        decisions=args.decisions,
        contamination_rate=args.contamination,
        backend_id=args.backend,
    )

    if args.json:
        print(json.dumps(report, indent=2))
        return

    if report["status"] != "executed":
        print(f"PB-AI-01 backend={args.backend}: NOT RUN")
        print(report["reason"])
        return

    baseline = report["baseline"]
    proof = report["proof"]

    print("ProofBit PB-AI-01 v0.1")
    print(report["scope"])
    print(
        f"backend={report['backend']['id']} decisions={report['decisions']:,} "
        f"contamination={report['contamination_rate']:.2%}"
    )
    print()
    print(
        "unsafe actions / 1M: "
        f"baseline={baseline['unsafe_actions_per_million']:,.0f} "
        f"proof={proof['unsafe_actions_per_million']:,.0f}"
    )
    print(
        "proof coverage: "
        f"baseline={baseline['proof_coverage']:.2%} "
        f"proof={proof['proof_coverage']:.2%}"
    )
    print(
        "trusted useful throughput: "
        f"baseline={baseline['trusted_useful_throughput']:,.0f}/s "
        f"proof={proof['trusted_useful_throughput']:,.0f}/s"
    )
    print(
        "end-to-end decisions/s: "
        f"baseline={baseline['end_to_end_decisions_per_sec']:,.0f} "
        f"proof={proof['end_to_end_decisions_per_sec']:,.0f}"
    )
    print(f"proof guard overhead: {report['proof_guard_overhead_ratio']:.2f}x")
    print(f"end-to-end overhead: {report['end_to_end_overhead_ratio']:.2f}x")


if __name__ == "__main__":
    main()
