from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "market_matrix.py"
SPEC = importlib.util.spec_from_file_location("market_matrix", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
market_matrix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(market_matrix)


class MarketMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = market_matrix.load_registry()
        self.summary = market_matrix.market_summary(self.registry)

    def test_reference_set_contains_major_accelerator_families(self) -> None:
        ids = {system["id"] for system in self.registry["systems"]}
        expected = {
            "nvidia-gb200-nvl72",
            "google-tpu7x-ironwood",
            "cerebras-wse3",
            "aws-trainium3",
            "amd-mi450-series",
            "openai-jalapeno",
        }
        self.assertTrue(expected.issubset(ids))

    def test_only_common_workload_entries_are_executable_tier(self) -> None:
        for system in self.registry["systems"]:
            tier = market_matrix.classify(system)
            if tier == "EXECUTABLE":
                self.assertTrue(system["common_workload_ready"])
            else:
                self.assertFalse(system["common_workload_ready"])

    def test_market_registry_does_not_fake_hardware_proof_scores(self) -> None:
        for system in self.registry["systems"]:
            if system["vendor"] != "ProofBit":
                self.assertIsNone(system.get("proof_native"))

    def test_current_executable_comparison_is_only_reference_models(self) -> None:
        self.assertEqual(self.summary["executable_common_workload_count"], 2)
        executable = {
            system["id"]
            for system in self.summary["systems"]
            if system["benchmark_tier"] == "EXECUTABLE"
        }
        self.assertEqual(
            executable,
            {"proofbit-baseline", "proofbit-proofprocessor"},
        )


if __name__ == "__main__":
    unittest.main()
