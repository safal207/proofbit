from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

BENCHMARK_ID = "PB-HW-02"
VERSION = "0.1"
PROTOCOL = "PB-HW-02/v0.1 semantic-cost-curve"

TOPS = {
    "minimal_capability": "pb_hw02_min_cap_pipeline",
    "full_conventional": "pb_hw02_full_conventional_pipeline",
    "rich_proofbit": "pb_hw02_rich_proofbit_pipeline",
}

GUARANTEES = (
    "tag_integrity",
    "statement_binding",
    "authority",
    "freshness",
    "replay",
    "epistemic_state",
    "provenance",
    "execution_context",
    "separate_outcome",
)

LOGICAL_METADATA_BITS = {
    "minimal_capability": 41,
    "full_conventional": 60,
    "rich_proofbit": 60,
}
LOGICAL_STATE_BITS = {
    "minimal_capability": 139,
    "full_conventional": 278,
    "rich_proofbit": 278,
}
GUARANTEE_COVERAGE = {
    "minimal_capability": 5,
    "full_conventional": 9,
    "rich_proofbit": 9,
}
TRANSACTIONS_PER_TRUSTED_TERMINAL = {
    "minimal_capability": None,
    "full_conventional": 2,
    "rich_proofbit": 2,
}


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required tool not found: {name}")
    return path


def run_cmd(cmd: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout + proc.stderr


def parse_sim(text: str) -> dict:
    m = re.search(
        r"PB_HW02_SIM PASS safety=(\d+) min_fail=(\d+) semantic_gaps=(\d+) "
        r"conv_fail=(\d+) proof_fail=(\d+) min_stream=(\d+) rich_transactions=(\d+) "
        r"trusted_terminal=(\d+) stalls=(\d+)",
        text,
    )
    if not m:
        raise ValueError("PB_HW02_SIM PASS marker not found")
    keys = (
        "rich_safety_cases",
        "minimal_failures",
        "minimal_semantic_gap_accepts",
        "conventional_failures",
        "proofbit_failures",
        "minimal_stream_dispatches",
        "rich_transactions",
        "trusted_terminal_effects",
        "stalls",
    )
    return {key: int(value) for key, value in zip(keys, m.groups())}


def parse_ltp(text: str) -> int:
    matches = re.findall(r"length\s*=?\s*(\d+)", text, flags=re.IGNORECASE)
    if not matches:
        raise ValueError("Yosys ltp path length not found")
    return max(int(x) for x in matches)


def cell_counts_from_json(path: Path, top: str) -> dict:
    data = json.loads(path.read_text())
    module = data.get("modules", {}).get(top)
    if module is None:
        raise ValueError(f"top module {top!r} absent from Yosys JSON")
    counts = Counter(cell.get("type", "") for cell in module.get("cells", {}).values())
    lut_cells = sum(v for k, v in counts.items() if re.fullmatch(r"LUT[1-6]", k))
    ff_types = {"FDRE", "FDSE", "FDCE", "FDPE"}
    ff_cells = sum(v for k, v in counts.items() if k in ff_types)
    bram_cells = sum(v for k, v in counts.items() if k.startswith("RAMB18") or k.startswith("RAMB36"))
    io_types = {"IBUF", "OBUF", "IOBUF", "BUFG"}
    io_cells = sum(v for k, v in counts.items() if k in io_types)
    total = sum(counts.values())
    return {
        "total_cells": total,
        "core_cells_excluding_io": total - io_cells,
        "io_cells": io_cells,
        "lut_cells": lut_cells,
        "ff_cells": ff_cells,
        "bram_cells": bram_cells,
        "cell_types": dict(sorted(counts.items())),
    }


def yosys_depth(yosys: str, rtl: Path, top: str) -> dict:
    script = (
        f"read_verilog -sv {rtl}; "
        f"hierarchy -check -top {top}; proc; memory_map; opt; flatten; opt; ltp -noff"
    )
    text = run_cmd([yosys, "-p", script])
    return {
        "logic_depth_proxy": parse_ltp(text),
        "logic_depth_method": "yosys ltp -noff after proc/memory_map/opt/flatten",
    }


def yosys_xilinx(yosys: str, rtl: Path, top: str, out_json: Path) -> dict:
    script = (
        f"read_verilog -sv {rtl}; "
        f"synth_xilinx -family xc7 -top {top}; "
        f"write_json {out_json}"
    )
    run_cmd([yosys, "-q", "-p", script])
    return cell_counts_from_json(out_json, top)


def tool_version(cmd: list[str]) -> str:
    text = run_cmd(cmd)
    return text.strip().splitlines()[0] if text.strip() else "unknown"


def run() -> dict:
    root = Path(__file__).resolve().parents[1]
    rtl = root / "rtl" / "pb_hw_02.v"
    tb = root / "rtl" / "pb_hw_02_tb.v"
    iverilog = require_tool("iverilog")
    vvp = require_tool("vvp")
    yosys = require_tool("yosys")

    with tempfile.TemporaryDirectory(prefix="proofbit-pb-hw-02-") as tmp_dir:
        tmp = Path(tmp_dir)
        sim_bin = tmp / "pb_hw_02_tb.out"
        run_cmd([
            iverilog,
            "-g2012",
            "-s",
            "pb_hw02_tb",
            "-o",
            str(sim_bin),
            str(rtl),
            str(tb),
        ])
        simulation = parse_sim(run_cmd([vvp, str(sim_bin)]))

        synthesis = {}
        for key, top in TOPS.items():
            row = {}
            row.update(yosys_depth(yosys, rtl, top))
            row.update(yosys_xilinx(yosys, rtl, top, tmp / f"{key}.json"))
            row["logical_metadata_bits"] = LOGICAL_METADATA_BITS[key]
            row["logical_state_bits"] = LOGICAL_STATE_BITS[key]
            row["guarantee_coverage"] = GUARANTEE_COVERAGE[key]
            row["guarantee_total"] = len(GUARANTEES)
            row["transactions_per_trusted_terminal"] = TRANSACTIONS_PER_TRUSTED_TERMINAL[key]
            row["accepts_one_input_transaction_per_cycle"] = True
            synthesis[key] = row

    minimal = synthesis["minimal_capability"]
    conventional = synthesis["full_conventional"]
    proofbit = synthesis["rich_proofbit"]

    added_guarantees = conventional["guarantee_coverage"] - minimal["guarantee_coverage"]
    marginal = {
        "added_guarantees": added_guarantees,
        "metadata_bits_delta": conventional["logical_metadata_bits"] - minimal["logical_metadata_bits"],
        "state_bits_delta": conventional["logical_state_bits"] - minimal["logical_state_bits"],
        "lut_delta": conventional["lut_cells"] - minimal["lut_cells"],
        "ff_delta": conventional["ff_cells"] - minimal["ff_cells"],
        "core_cells_delta": conventional["core_cells_excluding_io"] - minimal["core_cells_excluding_io"],
        "logic_depth_delta": conventional["logic_depth_proxy"] - minimal["logic_depth_proxy"],
    }
    marginal["metadata_bits_per_added_guarantee"] = marginal["metadata_bits_delta"] / added_guarantees
    marginal["state_bits_per_added_guarantee"] = marginal["state_bits_delta"] / added_guarantees
    marginal["lut_per_added_guarantee"] = marginal["lut_delta"] / added_guarantees
    marginal["ff_per_added_guarantee"] = marginal["ff_delta"] / added_guarantees

    strong_equivalence = {
        "same_lut_cells": conventional["lut_cells"] == proofbit["lut_cells"],
        "same_ff_cells": conventional["ff_cells"] == proofbit["ff_cells"],
        "same_bram_cells": conventional["bram_cells"] == proofbit["bram_cells"],
        "same_core_cells": conventional["core_cells_excluding_io"] == proofbit["core_cells_excluding_io"],
        "same_logic_depth_proxy": conventional["logic_depth_proxy"] == proofbit["logic_depth_proxy"],
        "same_metadata_bits": conventional["logical_metadata_bits"] == proofbit["logical_metadata_bits"],
        "same_state_bits": conventional["logical_state_bits"] == proofbit["logical_state_bits"],
        "same_guarantee_coverage": conventional["guarantee_coverage"] == proofbit["guarantee_coverage"],
        "same_terminal_transaction_cost": (
            conventional["transactions_per_trusted_terminal"]
            == proofbit["transactions_per_trusted_terminal"]
        ),
    }

    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "tools": {
            "iverilog": tool_version([iverilog, "-V"]),
            "yosys": tool_version([yosys, "-V"]),
        },
        "guarantees": list(GUARANTEES),
        "coverage": {
            "minimal_capability": {
                "covered": list(GUARANTEES[:5]),
                "unsupported": list(GUARANTEES[5:]),
                "terminal_success_supported": False,
            },
            "full_conventional": {
                "covered": list(GUARANTEES),
                "unsupported": [],
                "terminal_success_supported": True,
            },
            "rich_proofbit": {
                "covered": list(GUARANTEES),
                "unsupported": [],
                "terminal_success_supported": True,
            },
        },
        "simulation": simulation,
        "synthesis": synthesis,
        "marginal_full_evidence_cost_over_minimal": marginal,
        "full_conventional_vs_proofbit": strong_equivalence,
        "trusted_terminal_protocol": {
            "full_conventional_transactions": 2,
            "rich_proofbit_transactions": 2,
            "minimal_capability_transactions": None,
            "minimal_reason": "terminal outcome evidence is outside the minimal capability contract",
            "amortized_trusted_terminal_effects_per_input_transaction": 0.5,
        },
        "primary_anti_strawman": "full_conventional",
        "no_single_winner_score": True,
        "claim_boundary": (
            "Synthesizable Verilog simulated with Icarus and structurally synthesized by Yosys synth_xilinx. "
            "The full conventional and ProofBit wrappers intentionally share an equally expressive compact full-evidence core. "
            "Yosys ltp is a logic-depth proxy, not routed timing. No FPGA board, ASIC PPA, physical cache/tag RAM, "
            "energy, speculation, IOMMU/firmware-root, silicon-performance, novelty, patentability or universal-superiority claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report["simulation"], sort_keys=True))
        for key, row in report["synthesis"].items():
            print(
                key,
                "coverage", f"{row['guarantee_coverage']}/{row['guarantee_total']}",
                "LUT", row["lut_cells"],
                "FF", row["ff_cells"],
                "depth", row["logic_depth_proxy"],
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
