from __future__ import annotations

import unittest

from benchmarks.pb_transition_03 import FAULT_KINDS, build_report, build_trials, expected


class PBTransition03Tests(unittest.TestCase):
    def test_workload_has_exact_deterministic_fault_counts(self) -> None:
        rows = build_trials(10_000, 0.10)
        counts = {kind: 0 for kind in ("VALID", *FAULT_KINDS)}
        for row in rows:
            counts[row.kind] += 1
        self.assertEqual(counts["VALID"], 9000)
        for kind in FAULT_KINDS:
            self.assertEqual(counts[kind], 200)

    def test_false_success_is_dispatch_without_terminal_success(self) -> None:
        self.assertEqual(expected("FALSE_SUCCESS"), (True, False))
        for kind in ("UNKNOWN", "STALE_AUTHORITY", "REPLAY", "CONFLICT"):
            self.assertEqual(expected(kind), (False, False))

    def test_full_local_references_preserve_frozen_oracle(self) -> None:
        report = build_report(10_000, 0.10)
        raw = report["systems"]["baseline_raw"]
        guarded = report["systems"]["baseline_software_guarded"]
        proof = report["systems"]["proofbit"]

        self.assertEqual(raw["oracle_correct_trials"], 9000)
        self.assertEqual(raw["unsafe_authorization_dispatches"], 800)
        self.assertEqual(raw["false_success_claims"], 200)

        for system in (guarded, proof):
            self.assertEqual(system["oracle_correct_trials"], 10_000)
            self.assertEqual(system["unsafe_authorization_dispatches"], 0)
            self.assertEqual(system["false_success_claims"], 0)
            self.assertEqual(system["missed_valid_dispatches"], 0)
            self.assertEqual(system["failure_kind_coverage"], 1.0)
            self.assertEqual(system["stream_semantic_coverage"], 1.0)

    def test_external_unsupported_semantics_are_not_credited(self) -> None:
        partial = {
            "benchmark_id": "PB-TRANSITION-03",
            "version": "0.1",
            "protocol": "PB-T03/v0.1 authorization-freshness-replay-conflict-outcome",
            "architecture": "Example",
            "status": "executed_partial",
            "trials": 100,
            "contamination_rate": 0.10,
            "failure_kind_coverage": 0.2,
            "stream_semantic_coverage": 0.92,
            "supported_fault_kinds": ["UNKNOWN"],
            "unsupported_fault_kinds": [
                "STALE_AUTHORITY",
                "REPLAY",
                "CONFLICT",
                "FALSE_SUCCESS",
            ],
            "assessed_trials": 92,
            "unassessed_trials": 8,
            "oracle_correct_assessed_trials": 92,
            "oracle_accuracy_on_assessed": 1.0,
            "unsafe_authorization_dispatches_on_assessed": 0,
            "false_success_claims_on_assessed": 0,
            "evidence_kind": "example",
            "per_kind": {},
            "elapsed_ns": 1,
            "assessed_trials_per_sec": 92_000_000_000.0,
            "claim_boundary": "test",
            "cost_note": "test",
        }
        report = build_report(100, 0.10, capu_report=partial)
        capu = report["systems"]["capu"]
        self.assertEqual(capu["failure_kind_coverage"], 0.2)
        self.assertEqual(capu["unassessed_trials"], 8)
        self.assertNotIn("oracle_accuracy", capu)


if __name__ == "__main__":
    unittest.main()
