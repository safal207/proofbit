from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "pb_arch_01.py"
SPEC = importlib.util.spec_from_file_location("pb_arch_01", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
pb_arch_01 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pb_arch_01)


class ProofBitArchitectureBenchmarkTests(unittest.TestCase):
    def test_baseline_collapses_fault_semantics_while_proofbit_covers_them(self) -> None:
        report = pb_arch_01.build_report(decisions=1000, contamination_rate=0.10)
        baseline = report["systems"]["baseline"]
        proof = report["systems"]["proofbit"]

        self.assertEqual(baseline["failure_kind_coverage"], 0.0)
        self.assertGreater(baseline["unsafe_actions"], 0)
        self.assertTrue(
            all(
                value == "collapsed_to_value_true"
                for value in baseline["failure_semantics"].values()
            )
        )

        self.assertEqual(proof["failure_kind_coverage"], 1.0)
        self.assertEqual(proof["unsafe_actions"], 0)
        self.assertEqual(proof["blocked_valid_actions"], 0)
        self.assertTrue(
            all(
                value == "supported_blocked"
                for value in proof["failure_semantics"].values()
            )
        )

    def test_capu_is_not_credited_when_not_executed(self) -> None:
        report = pb_arch_01.build_report(decisions=1000, contamination_rate=0.10)
        self.assertEqual(report["systems"]["capu"]["status"], "not_run")

    def test_external_capu_result_must_match_frozen_workload(self) -> None:
        payload = {
            "benchmark_id": "PB-ARCH-01",
            "decisions": 999,
            "contamination_rate": 0.10,
            "status": "executed_partial",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capu.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ValueError):
                pb_arch_01.build_report(
                    decisions=1000,
                    contamination_rate=0.10,
                    capu_json=path,
                )


if __name__ == "__main__":
    unittest.main()
