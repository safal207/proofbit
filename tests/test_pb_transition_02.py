from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "pb_transition_02.py"
SPEC = importlib.util.spec_from_file_location("pb_transition_02", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
pb_transition_02 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pb_transition_02)


class PBTransition02Tests(unittest.TestCase):
    def test_deterministic_schedule_has_exact_counts_and_directions(self) -> None:
        report = pb_transition_02.run_benchmark(1_000, 0.10)
        raw = report["systems"]["baseline_raw"]
        self.assertEqual(raw["valid_trials"], 900)
        self.assertEqual(raw["insufficient_support_trials"], 100)
        self.assertEqual(raw["source_0_trials"], 500)
        self.assertEqual(raw["source_1_trials"], 500)

    def test_raw_baseline_exposes_unchecked_transition_failure(self) -> None:
        report = pb_transition_02.run_benchmark(1_000, 0.10)
        raw = report["systems"]["baseline_raw"]
        self.assertEqual(raw["correct_valid_transitions"], 900)
        self.assertEqual(raw["unsafe_invalid_transitions"], 100)
        self.assertEqual(raw["invalid_transitions_preserved"], 0)
        self.assertEqual(raw["missed_valid_transitions"], 0)
        self.assertEqual(raw["oracle_accuracy"], 0.9)
        self.assertEqual(raw["native_justification_coverage"], 0.0)

    def test_software_guard_is_fair_non_proof_control(self) -> None:
        report = pb_transition_02.run_benchmark(1_000, 0.10)
        guarded = report["systems"]["baseline_software_guarded"]
        self.assertEqual(guarded["correct_valid_transitions"], 900)
        self.assertEqual(guarded["invalid_transitions_preserved"], 100)
        self.assertEqual(guarded["unsafe_invalid_transitions"], 0)
        self.assertEqual(guarded["missed_valid_transitions"], 0)
        self.assertEqual(guarded["oracle_accuracy"], 1.0)
        self.assertEqual(guarded["native_justification_coverage"], 0.0)
        self.assertEqual(guarded["evidence_kind"], "application_boolean_guard")

    def test_proofbit_satisfies_oracle_with_native_evidence(self) -> None:
        report = pb_transition_02.run_benchmark(1_000, 0.10)
        proof = report["systems"]["proofbit"]
        self.assertEqual(proof["correct_valid_transitions"], 900)
        self.assertEqual(proof["invalid_transitions_preserved"], 100)
        self.assertEqual(proof["unsafe_invalid_transitions"], 0)
        self.assertEqual(proof["missed_valid_transitions"], 0)
        self.assertEqual(proof["oracle_accuracy"], 1.0)
        self.assertEqual(proof["native_justification_coverage"], 1.0)

    def test_external_report_must_match_frozen_protocol(self) -> None:
        report = pb_transition_02.run_benchmark(100, 0.10)["systems"]["proofbit"].copy()
        report["architecture"] = "External Test Architecture"
        validated = pb_transition_02.validate_external(report, 100, 0.10)
        self.assertEqual(validated["architecture"], "External Test Architecture")

        drifted = report.copy()
        drifted["protocol"] = "PB-T02/drifted"
        with self.assertRaises(ValueError):
            pb_transition_02.validate_external(drifted, 100, 0.10)

    def test_report_does_not_collapse_architectures_to_winner_score(self) -> None:
        report = pb_transition_02.run_benchmark(100, 0.10)
        self.assertTrue(report["proof_semantics_not_numerically_equivalent"])
        self.assertTrue(report["no_single_winner_score"])
        self.assertNotIn("winner", report)
        self.assertNotEqual(
            report["systems"]["baseline_software_guarded"]["evidence_kind"],
            report["systems"]["proofbit"]["evidence_kind"],
        )

    def test_invalid_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            pb_transition_02.run_benchmark(0, 0.10)
        with self.assertRaises(ValueError):
            pb_transition_02.run_benchmark(100, -0.01)
        with self.assertRaises(ValueError):
            pb_transition_02.run_benchmark(100, 1.01)


if __name__ == "__main__":
    unittest.main()
