from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks import pb_hw_02 as hw


def flat_yosys_xilinx(yosys: str, rtl: Path, top: str, out_json: Path) -> dict:
    # Flatten only the benchmark's design hierarchy before technology mapping.
    # This makes the wrapper/core hierarchy comparable without recursively
    # descending into Yosys/Xilinx primitive simulation models such as FDRE.
    script = (
        f"read_verilog -sv {rtl}; "
        f"hierarchy -check -top {top}; "
        f"flatten; "
        f"synth_xilinx -family xc7 -top {top}; "
        f"write_json {out_json}"
    )
    hw.run_cmd([yosys, "-q", "-p", script])
    row = hw.cell_counts_from_json(out_json, top)
    row["cell_count_method"] = "design hierarchy flattened before synth_xilinx; mapped primitives counted at top"
    return row


hw.yosys_xilinx = flat_yosys_xilinx

if __name__ == "__main__":
    raise SystemExit(hw.main())
