import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.research_architecture_scorecard import build_scorecard


CAPU = {
    "benchmark_id": "PB-ARCH-01",
    "architecture": "CaPU",
    "status": "executed_partial",
    "decisions": 100,
    "contamination_rate": 0.10,
    "safe_actions": 90,
    "unsafe_actions_on_supported_semantics": 0,
    "unsupported_decisions": 8,
    "failure_kind_coverage": 0.2,
    "failure_kind_support": {
        "UNKNOWN": "supported_missing_commit_mapping",
        "STALE": "unsupported",
        "REPLAY": "unsupported",
        "CONFLICT": "unsupported",
        "FALSE_SUCCESS": "unsupported",
    },
    "supported_decisions_per_sec": 1_000_000.0,
}

MORPHOS = {
    "benchmark_id": "PB-TRANSITION-01",
    "version": "0.1",
    "architecture": "COSMIC ORGANICS / MORPHOS",
    "status": "executed",
    "frozen_provenance": {
        "mechanism_blob_matches_frozen": True,
        "continuation_only_no_retuning": True,
    },
    "proof": {
        "decision": "TRANSFER_PASS",
        "recovery_and_controls_pass": True,
    },
    "utility": {
        "predecessor_failures": 2,
        "causal_rescues": 2,
        "causal_rescue_rate": 1.0,
        "minimum_exact_recovery_at_8": 1.0,
        "minimum_exact_recovery_at_12": 1.0,
        "previous_successes_regressed": 0,
    },
    "cost_speed": {"trials_per_sec": 25.0},
    "claim_boundary": "frozen transition/recovery evidence only",
}


class ResearchArchitectureScorecardTests(unittest.TestCase):
    def _write(self, directory: Path, name: str, payload: dict) -> Path:
        path = directory / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_four_architectures_keep_separate_speed_domains(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capu = self._write(root, "capu.json", CAPU)
            morphos = self._write(root, "morphos.json", MORPHOS)
            report = build_scorecard(capu, morphos, decisions=100, contamination_rate=0.10)

        self.assertEqual(
            set(report["systems"]), {"baseline", "proofbit", "capu", "morphos"}
        )
        self.assertEqual(
            report["systems"]["baseline"]["speed"]["comparability_group"],
            "PB-ARCH-01-boundary-decisions",
        )
        self.assertEqual(
            report["systems"]["morphos"]["speed"]["comparability_group"],
            "PB-TRANSITION-01-morphos-trials",
        )
        self.assertTrue(report["no_synthetic_overall_score"])

    def test_morphos_requires_frozen_transfer_pass(self):
        bad = dict(MORPHOS)
        bad["proof"] = dict(MORPHOS["proof"])
        bad["proof"]["decision"] = "FAIL"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capu = self._write(root, "capu.json", CAPU)
            morphos = self._write(root, "morphos.json", bad)
            with self.assertRaises(ValueError):
                build_scorecard(capu, morphos, decisions=100, contamination_rate=0.10)


if __name__ == "__main__":
    unittest.main()
