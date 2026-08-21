from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

BENCHMARK_ID = "PB-HW-03"
VERSION = "0.1"
PROTOCOL = "PB-HW-03/v0.1 composition-economics"

TOPS = {
    "scalar_conventional": "pb_hw03_scalar_conventional",
    "vector_conventional": "pb_hw03_vector_conventional",
    "proofbit_compose": "pb_hw03_proofbit_compose",
}

GUARANTEES = (
    "parent_epistemic_state",
    "parent_authority",
    "parent_freshness",
    "parent_provenance",
    "parent_execution_context",
    "parent_uniqueness",
    "parent_replay",
    "derived_statement_binding",
    "separate_outcome",
)

GUARANTEE_COVERAGE = {key: len(GUARANTEES) for key in TOPS}
LOGICAL_STATE_BITS = {
    "scalar_conventional": 454,
    "vector_conventional": 282,
    "proofbit_compose": 282,
}
INSTRUCTION_TRANSACTIONS_PER_TRUSTED_TERMINAL = {
    "scalar_conventional": 6,
    "vector_conventional": 2,
    "proofbit_compose": 2,
}
LOGICAL_PARENT_READS_PER_TERMINAL = {key: 4 for key in TOPS}
PARENT_READ_ISSUE_CYCLES = {
    "scalar_conventional": 4,
    "vector_conventional": 1,
    "proofbit_compose": 1,
}
LOGICAL_DERIVED_WRITES_PER_TERMINAL = {key: 1 for key in TOPS}
LOGICAL_OUTCOME_WRITES_PER_TERMINAL = {key: 1 for key in TOPS}
PARALLEL_PARENT_LANES = {
    "scalar_conventional": 1,
    "vector_conventional": 4,
    "proofbit_compose": 4,
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
    match = re.search(
        r"PB_HW03_SIM PASS safety=(\d+) scalar_fail=(\d+) conv_fail=(\d+) proof_fail=(\d+) "
        r"scalar_tx=(\d+) vector_tx=(\d+) scalar_terminal=(\d+) conv_terminal=(\d+) "
        r"proof_terminal=(\d+) stalls=(\d+)",
        text,
    )
    if not match:
        raise ValueError("PB_HW03_SIM PASS marker not found")
    keys = (
        "safety_cases",
        "scalar_failures",
        "conventional_failures",
        "proofbit_failures",
        "scalar_stream_transactions",
        "vector_stream_transactions",
        "scalar_trusted_terminals",
        "conventional_trusted_terminals",
        "proofbit_trusted_terminals",
        "stalls",
    )
    return {key: int(value) for key, value in zip(keys, match.groups())}


def parse_ltp(text: str) -> int:
    matches = re.findall(r"length\s*=?\s*(\d+)", text, flags=re.IGNORECASE)
    if not matches:
        raise ValueError("Yosys ltp path length not found")
    return max(int(value) for value in matches)


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
        "cell_count_method": "design hierarchy flattened before synth_xilinx; mapped primitives counted at top",
    }


def yosys_depth(yosys: str, rtl: Path, top: str) -> dict:
    script = (
        f"read_verilog -sv {rtl}; hierarchy -check -top {top}; "
        "proc; memory_map; opt; flatten; opt; ltp -noff"
    )
    text = run_cmd([yosys, "-p", script])
    return {
        "logic_depth_proxy": parse_ltp(text),
        "logic_depth_method": "yosys ltp -noff after proc/memory_map/opt/flatten",
    }


def yosys_xilinx(yosys: str, rtl: Path, top: str, out_json: Path) -> dict:
    # Flatten only our design hierarchy before technology mapping. This avoids
    # recursively walking into Xilinx simulation-library primitive definitions.
    script = (
        f"read_verilog -sv {rtl}; hierarchy -check -top {top}; flatten; "
        f"synth_xilinx -family xc7 -top {top}; write_json {out_json}"
    )
    run_cmd([yosys, "-q", "-p", script])
    return cell_counts_from_json(out_json, top)


def tool_version(cmd: list[str]) -> str:
    text = run_cmd(cmd)
    return text.strip().splitlines()[0] if text.strip() else "unknown"


def run() -> dict:
    root = Path(__file__).resolve().parents[1]
    rtl = root / "rtl" / "pb_hw_03.v"
    tb = root / "rtl" / "pb_hw_03_tb.v"
    iverilog = require_tool("iverilog")
    vvp = require_tool("vvp")
    yosys = require_tool("yosys")

    with tempfile.TemporaryDirectory(prefix="proofbit-pb-hw-03-") as tmp_dir:
        tmp = Path(tmp_dir)
        sim_bin = tmp / "pb_hw_03_tb.out"
        run_cmd([
            iverilog,
            "-g2012",
            "-s",
            "pb_hw03_tb",
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
            row["guarantee_coverage"] = GUARANTEE_COVERAGE[key]
            row["guarantee_total"] = len(GUARANTEES)
            row["logical_state_bits"] = LOGICAL_STATE_BITS[key]
            row["instruction_transactions_per_trusted_terminal"] = (
                INSTRUCTION_TRANSACTIONS_PER_TRUSTED_TERMINAL[key]
            )
            row["logical_parent_reads_per_terminal"] = LOGICAL_PARENT_READS_PER_TERMINAL[key]
            row["parent_read_issue_cycles"] = PARENT_READ_ISSUE_CYCLES[key]
            row["logical_derived_writes_per_terminal"] = LOGICAL_DERIVED_WRITES_PER_TERMINAL[key]
            row["logical_outcome_writes_per_terminal"] = LOGICAL_OUTCOME_WRITES_PER_TERMINAL[key]
            row["parallel_parent_lanes"] = PARALLEL_PARENT_LANES[key]
            row["trusted_terminals_per_input_transaction"] = 1.0 / INSTRUCTION_TRANSACTIONS_PER_TRUSTED_TERMINAL[key]
            synthesis[key] = row

    scalar = synthesis["scalar_conventional"]
    conventional = synthesis["vector_conventional"]
    proofbit = synthesis["proofbit_compose"]

    strong_equivalence = {
        "same_lut_cells": conventional["lut_cells"] == proofbit["lut_cells"],
        "same_ff_cells": conventional["ff_cells"] == proofbit["ff_cells"],
        "same_bram_cells": conventional["bram_cells"] == proofbit["bram_cells"],
        "same_core_cells": conventional["core_cells_excluding_io"] == proofbit["core_cells_excluding_io"],
        "same_logic_depth_proxy": conventional["logic_depth_proxy"] == proofbit["logic_depth_proxy"],
        "same_state_bits": conventional["logical_state_bits"] == proofbit["logical_state_bits"],
        "same_guarantee_coverage": conventional["guarantee_coverage"] == proofbit["guarantee_coverage"],
        "same_instruction_transactions": (
            conventional["instruction_transactions_per_trusted_terminal"]
            == proofbit["instruction_transactions_per_trusted_terminal"]
        ),
        "same_parent_reads": conventional["logical_parent_reads_per_terminal"] == proofbit["logical_parent_reads_per_terminal"],
        "same_parent_read_issue_cycles": conventional["parent_read_issue_cycles"] == proofbit["parent_read_issue_cycles"],
        "same_logical_writes": (
            conventional["logical_derived_writes_per_terminal"] == proofbit["logical_derived_writes_per_terminal"]
            and conventional["logical_outcome_writes_per_terminal"] == proofbit["logical_outcome_writes_per_terminal"]
        ),
    }

    primitive_vs_scalar = {
        "instruction_transaction_reduction_x": (
            scalar["instruction_transactions_per_trusted_terminal"]
            / conventional["instruction_transactions_per_trusted_terminal"]
        ),
        "parent_read_issue_cycle_reduction_x": (
            scalar["parent_read_issue_cycles"] / conventional["parent_read_issue_cycles"]
        ),
        "logical_parent_reads_delta": (
            conventional["logical_parent_reads_per_terminal"] - scalar["logical_parent_reads_per_terminal"]
        ),
        "logical_total_writes_delta": (
            conventional["logical_derived_writes_per_terminal"]
            + conventional["logical_outcome_writes_per_terminal"]
            - scalar["logical_derived_writes_per_terminal"]
            - scalar["logical_outcome_writes_per_terminal"]
        ),
        "lut_delta": conventional["lut_cells"] - scalar["lut_cells"],
        "ff_delta": conventional["ff_cells"] - scalar["ff_cells"],
        "core_cells_delta": conventional["core_cells_excluding_io"] - scalar["core_cells_excluding_io"],
        "logic_depth_delta": conventional["logic_depth_proxy"] - scalar["logic_depth_proxy"],
        "logical_state_bits_delta": conventional["logical_state_bits"] - scalar["logical_state_bits"],
    }

    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "tools": {
            "iverilog": tool_version([iverilog, "-V"]),
            "yosys": tool_version([yosys, "-V"]),
        },
        "parent_count": 4,
        "guarantees": list(GUARANTEES),
        "simulation": simulation,
        "synthesis": synthesis,
        "primitive_vs_scalar": primitive_vs_scalar,
        "vector_conventional_vs_proofbit": strong_equivalence,
        "primary_anti_strawman": "vector_conventional",
        "no_single_winner_score": True,
        "access_accounting": {
            "status": "logical protocol accounting",
            "physical_memory_instantiated": False,
            "note": (
                "Parent reads and derived/outcome writes are protocol-accounted logical proof-table accesses. "
                "PB-HW-03 does not instantiate a physical multi-ported proof RAM/cache; mapped LUT/FF counts cover the composition engines only."
            ),
        },
        "claim_boundary": (
            "Synthesizable reference Verilog simulated with Icarus and structurally synthesized by Yosys synth_xilinx. "
            "The vector conventional and ProofBit wrappers intentionally share one equally expressive four-parent composition core. "
            "Logical proof-table accesses are accounted but no physical multi-ported proof RAM/cache is instantiated. "
            "Yosys ltp is a logic-depth proxy, not routed timing. No FPGA board, ASIC PPA, energy, physical memory PPA, "
            "speculation, IOMMU/firmware root, silicon-performance, novelty, patentability or universal-superiority claim."
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
                "tx", row["instruction_transactions_per_trusted_terminal"],
                "read_issue", row["parent_read_issue_cycles"],
                "LUT", row["lut_cells"],
                "FF", row["ff_cells"],
                "depth", row["logic_depth_proxy"],
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
