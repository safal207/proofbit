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

    def test_external_hardware_has_explicit_pb_ai_01_adapter_target(self) -> None:
        expected = {
            "nvidia-gb200-nvl72": ("nvidia-cuda", "not_run"),
            "google-tpu7x-ironwood": ("google-tpu-jax", "not_run"),
            "cerebras-wse3": ("cerebras", "not_run"),
            "aws-trainium3": ("aws-neuron", "not_run"),
            "amd-mi450-series": ("amd-rocm", "not_run"),
            "openai-jalapeno": (
                "openai-jalapeno",
                "not_run_no_public_adapter",
            ),
        }
        by_id = {system["id"]: system for system in self.registry["systems"]}
        for system_id, (adapter, status) in expected.items():
            self.assertEqual(by_id[system_id]["pb_ai_01_adapter"], adapter)
            self.assertEqual(by_id[system_id]["pb_ai_01_status"], status)


if __name__ == "__main__":
    unittest.main()
