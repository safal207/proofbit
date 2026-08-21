from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

from benchmarks import pb_hw_02 as hw


def recursive_cell_counts_from_json(path: Path, top: str) -> dict:
    data = json.loads(path.read_text())
    modules = data.get("modules", {})
    if top not in modules:
        raise ValueError(f"top module {top!r} absent from Yosys JSON")

    def walk(module_name: str) -> Counter:
        counts: Counter = Counter()
        module = modules[module_name]
        for cell in module.get("cells", {}).values():
            cell_type = cell.get("type", "")
            if cell_type in modules:
                counts.update(walk(cell_type))
            else:
                counts[cell_type] += 1
        return counts

    counts = walk(top)
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
        "cell_count_method": "recursive mapped-cell count through Yosys module hierarchy",
    }


hw.cell_counts_from_json = recursive_cell_counts_from_json

if __name__ == "__main__":
    raise SystemExit(hw.main())
