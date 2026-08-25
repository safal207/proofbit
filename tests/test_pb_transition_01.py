from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.pb_transition_01 import build_report


class ProofBitTransitionBenchmarkTests(unittest.TestCase):
    def _write(self, payload: dict) -> Path:
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        with handle:
            json.dump(payload, handle)
        return Path(handle.name)

    def test_morphos_is_not_credited_when_not_executed(self) -> None:
        report = build_report()
        self.assertEqual(report["systems"]["morphos"]["status"], "not_run")
        self.assertEqual(
            report["systems"]["proofbit"]["status"], "not_run_adapter_needed"
        )
        self.assertEqual(
            report["systems"]["capu"]["status"], "not_run_adapter_needed"
        )

    def test_external_result_requires_frozen_provenance(self) -> None:
        path = self._write(
            {
                "benchmark_id": "PB-TRANSITION-01",
                "status": "executed",
                "frozen_provenance": {"mechanism_blob_matches_frozen": False},
            }
        )
        with self.assertRaises(ValueError):
            build_report(path)

    def test_valid_external_result_is_preserved(self) -> None:
        payload = {
            "benchmark_id": "PB-TRANSITION-01",
            "status": "executed",
            "frozen_provenance": {"mechanism_blob_matches_frozen": True},
            "utility": {
                "predecessor_failures": 2,
                "causal_rescues": 2,
                "minimum_exact_recovery_at_8": 1.0,
            },
            "cost_speed": {"trials_per_sec": 1.0},
        }
        path = self._write(payload)
        report = build_report(path)
        self.assertEqual(report["systems"]["morphos"], payload)


if __name__ == "__main__":
    unittest.main()
