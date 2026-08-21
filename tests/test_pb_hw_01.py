from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from benchmarks import pb_hw_01 as hw


class PBHW01Tests(unittest.TestCase):
    def test_contract_and_metadata_normalization(self):
        self.assertEqual(hw.BENCHMARK_ID, "PB-HW-01")
        self.assertEqual(hw.PROTOCOL, "PB-HW-01/v0.1 rtl-semantic-equivalence")
        self.assertEqual(hw.LOGICAL_METADATA_BITS["capability"], 59)
        self.assertEqual(hw.LOGICAL_METADATA_BITS["proofbit"], 59)
        self.assertEqual(hw.REPLAY_TABLE_BITS, 139)
        self.assertEqual(hw.REGISTERED_STAGES, 2)
        self.assertEqual(hw.INPUT_TO_RESULT_LATENCY_CYCLES, 1)
        self.assertEqual(hw.STEADY_STATE_CYCLES_PER_EFFECT, 1)

    def test_sim_marker_parser(self):
        row = hw.parse_sim(
            "PB_HW01_SIM PASS safety=10 raw_unsafe=7 cap_fail=0 proof_fail=0 "
            "stream=32 latency_cycles=1 stalls=0\n"
        )
        self.assertEqual(row["safety_cases"], 10)
        self.assertEqual(row["raw_unsafe_accepts"], 7)
        self.assertEqual(row["capability_failures"], 0)
        self.assertEqual(row["proofbit_failures"], 0)
        self.assertEqual(row["stream_effects"], 32)

    def test_ltp_parser_accepts_common_yosys_forms(self):
        self.assertEqual(hw.parse_ltp("Longest topological path has length 7."), 7)
        self.assertEqual(hw.parse_ltp("length=11"), 11)
        self.assertEqual(hw.parse_ltp("length 3\nlength 8"), 8)

    def test_xilinx_json_counter(self):
        data = {
            "modules": {
                "top": {
                    "cells": {
                        "a": {"type": "LUT6"},
                        "b": {"type": "LUT3"},
                        "c": {"type": "FDRE"},
                        "d": {"type": "FDCE"},
                        "e": {"type": "RAMB18E1"},
                        "f": {"type": "BUFG"},
                    }
                }
            }
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "netlist.json"
            path.write_text(json.dumps(data))
            row = hw.cell_counts_from_json(path, "top")
        self.assertEqual(row["lut_cells"], 2)
        self.assertEqual(row["ff_cells"], 2)
        self.assertEqual(row["bram_cells"], 1)
        self.assertEqual(row["total_cells"], 6)

    def test_replay_table_accounting(self):
        self.assertEqual(
            hw.REPLAY_TABLE_BITS,
            hw.REPLAY_ENTRIES * (hw.REPLAY_NONCE_BITS + 1) + 3,
        )


if __name__ == "__main__":
    unittest.main()
