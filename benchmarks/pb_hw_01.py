from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

BENCHMARK_ID = "PB-HW-01"
VERSION = "0.1"
PROTOCOL = "PB-HW-01/v0.1 rtl-semantic-equivalence"

TOPS = {
    "raw": "pb_hw01_raw_pipeline",
    "capability": "pb_hw01_capability_pipeline",
    "proofbit": "pb_hw01_proofbit_pipeline",
}

LOGICAL_METADATA_BITS = {
    "raw": 2,
    "capability": 59,
    "proofbit": 59,
}
REPLAY_ENTRIES = 8
REPLAY_NONCE_BITS = 16
REPLAY_TABLE_BITS = REPLAY_ENTRIES * (REPLAY_NONCE_BITS + 1) + 3
REGISTERED_STAGES = 2
INPUT_TO_RESULT_LATENCY_CYCLES = 1
STEADY_STATE_CYCLES_PER_EFFECT = 1


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required tool not found: {name}")
    return path


def run_cmd(cmd: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout + proc.stderr


def parse_sim(text: str) -> dict:
    m = re.search(
        r"PB_HW01_SIM PASS safety=(\d+) raw_unsafe=(\d+) cap_fail=(\d+) "
        r"proof_fail=(\d+) stream=(\d+) latency_cycles=(\d+) stalls=(\d+)",
        text,
    )
    if not m:
        raise ValueError("PB_HW01_SIM PASS marker not found")
    keys = (
        "safety_cases",
        "raw_unsafe_accepts",
        "capability_failures",
        "proofbit_failures",
        "stream_effects",
        "latency_cycles",
        "stalls",
    )
    return {k: int(v) for k, v in zip(keys, m.groups())}


def parse_ltp(text: str) -> int:
    matches = re.findall(r"length\s*=?\s*(\d+)", text, flags=re.IGNORECASE)
    if not matches:
        raise ValueError("Yosys ltp path length not found")
    return max(int(x) for x in matches)


def cell_counts_from_json(path: Path, top: str) -> dict:
    data = json.loads(path.read_text())
    modules = data.get("modules", {})
    if top not in modules:
        raise ValueError(f"top module {top!r} absent from Yosys JSON: {list(modules)}")
    counts = Counter(cell.get("type", "") for cell in modules[top].get("cells", {}).values())
    lut_cells = sum(v for k, v in counts.items() if re.fullmatch(r"LUT[1-6]", k))
    ff_types = {"FDRE", "FDSE", "FDCE", "FDPE"}
    ff_cells = sum(v for k, v in counts.items() if k in ff_types)
    bram_cells = sum(v for k, v in counts.items() if k.startswith("RAMB18") or k.startswith("RAMB36"))
    return {
        "total_cells": sum(counts.values()),
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
    text = run_cmd([yosys, "-q", "-p", script])
    return {
        "logic_depth_proxy": parse_ltp(text),
        "method": "yosys ltp -noff after proc/memory_map/opt/flatten",
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
    rtl = root / "rtl" / "pb_hw_01.v"
    tb = root / "rtl" / "pb_hw_01_tb.v"
    iverilog = require_tool("iverilog")
    vvp = require_tool("vvp")
    yosys = require_tool("yosys")

    with tempfile.TemporaryDirectory(prefix="proofbit-pb-hw-01-") as tmp:
        tmp = Path(tmp)
        sim_bin = tmp / "pb_hw_01_tb.out"
        run_cmd([
            iverilog,
            "-g2012",
            "-s",
            "pb_hw01_tb",
            "-o",
            str(sim_bin),
            str(rtl),
            str(tb),
        ])
        sim_text = run_cmd([vvp, str(sim_bin)])
        simulation = parse_sim(sim_text)

        synthesis = {}
        for key, top in TOPS.items():
            row = {}
            row.update(yosys_depth(yosys, rtl, top))
            row.update(yosys_xilinx(yosys, rtl, top, tmp / f"{key}.json"))
            row["logical_metadata_bits"] = LOGICAL_METADATA_BITS[key]
            row["replay_table_bits"] = 0 if key == "raw" else REPLAY_TABLE_BITS
            row["registered_stages"] = REGISTERED_STAGES
            row["input_to_result_latency_cycles"] = INPUT_TO_RESULT_LATENCY_CYCLES
            row["steady_state_cycles_per_effect"] = STEADY_STATE_CYCLES_PER_EFFECT
            synthesis[key] = row

    cap = synthesis["capability"]
    proof = synthesis["proofbit"]
    equivalence = {
        "same_lut_cells": cap["lut_cells"] == proof["lut_cells"],
        "same_ff_cells": cap["ff_cells"] == proof["ff_cells"],
        "same_bram_cells": cap["bram_cells"] == proof["bram_cells"],
        "same_total_cells": cap["total_cells"] == proof["total_cells"],
        "same_logic_depth_proxy": cap["logic_depth_proxy"] == proof["logic_depth_proxy"],
        "same_metadata_bits": cap["logical_metadata_bits"] == proof["logical_metadata_bits"],
        "same_replay_table_bits": cap["replay_table_bits"] == proof["replay_table_bits"],
    }

    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "tools": {
            "iverilog": tool_version([iverilog, "-V"]),
            "yosys": tool_version([yosys, "-V"]),
        },
        "simulation": simulation,
        "synthesis": synthesis,
        "strong_control_equivalence": equivalence,
        "primary_anti_strawman": "capability",
        "logical_semantic_normalization": {
            "strong_metadata_bits": 59,
            "fields": {
                "tag": 1,
                "state": 2,
                "action_or_statement": 8,
                "authority": 8,
                "epoch": 8,
                "nonce_or_proof_id": 16,
                "provenance_or_source": 8,
                "context_or_domain": 8,
            },
            "replay_entries": REPLAY_ENTRIES,
            "replay_table_bits": REPLAY_TABLE_BITS,
        },
        "no_single_winner_score": True,
        "claim_boundary": (
            "Synthesizable Verilog simulated with Icarus and structurally synthesized by Yosys synth_xilinx. "
            "Yosys ltp is a logic-depth proxy, not post-place-and-route timing. No FPGA board, ASIC PPA, "
            "physical tag RAM, cache/coherence, speculative execution, IOMMU, firmware-root, energy, "
            "silicon-performance, novelty, patentability or universal-superiority claim."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    report = run()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report["simulation"], sort_keys=True))
        for key, row in report["synthesis"].items():
            print(key, row["lut_cells"], row["ff_cells"], row["logic_depth_proxy"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
