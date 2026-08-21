from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "pb_trust_compose_03.py"
SPEC = importlib.util.spec_from_file_location("pb_trust_compose_03", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
pb = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pb
SPEC.loader.exec_module(pb)


class PBTrustCompose03Tests(unittest.TestCase):
    def test_frozen_records_round_trip(self) -> None:
        action = pb.ActionMessage(
            kind="REPLAY",
            flags=0,
            action_id=7,
            statement_id=7,
            proof_id=99,
            authority=1,
            issued_epoch=3,
            provenance=7,
        )
        self.assertEqual(pb.decode_action(pb.encode_action(action)), action)
        outcome = pb.OutcomeMessage(7, 1, 1001, 3, 7)
        self.assertEqual(pb.decode_outcome(pb.encode_outcome(outcome)), outcome)

    def test_all_systems_match_oracle(self) -> None:
        report = pb.build_report(
            trials=100,
            contamination_rate=0.25,
            boundaries=(1, 2),
            rounds=1,
        )
        self.assertTrue(report["no_single_winner_score"])
        for scale in report["scale"]:
            for name in pb.SYSTEMS:
                system = scale["systems"][name]
                self.assertEqual(system["oracle_accuracy"], 1.0)
                self.assertEqual(system["unsafe_authorization_dispatches"], 0)
                self.assertEqual(system["false_success_claims"], 0)
                self.assertEqual(system["missed_valid_dispatches"], 0)
                self.assertEqual(system["replay_duplicates_accepted"], 0)

    def test_eager_revocation_fans_out_but_lazy_does_not(self) -> None:
        report = pb.build_report(
            trials=100,
            contamination_rate=0.25,
            boundaries=(1, 4),
            rounds=1,
        )
        one, four = report["scale"]
        revocations = four["systems"]["software_eager"]["revocations"]
        self.assertGreater(revocations, 0)
        self.assertEqual(
            four["systems"]["software_eager"]["control_messages"],
            revocations * 4,
        )
        self.assertEqual(
            four["systems"]["software_lazy"]["control_messages"],
            revocations,
        )
        self.assertEqual(
            four["systems"]["proofbit_lazy"]["control_messages"],
            revocations,
        )
        self.assertEqual(
            one["systems"]["software_eager"]["control_messages"],
            one["systems"]["software_lazy"]["control_messages"],
        )

    def test_lazy_software_and_proofbit_have_identical_transport_payload(self) -> None:
        report = pb.build_report(
            trials=80,
            contamination_rate=0.25,
            boundaries=(3,),
            rounds=1,
        )
        systems = report["scale"][0]["systems"]
        self.assertEqual(
            systems["software_lazy"]["total_request_ipc_payload_bytes"],
            systems["proofbit_lazy"]["total_request_ipc_payload_bytes"],
        )
        self.assertEqual(
            systems["software_lazy"]["control_ipc_payload_bytes"],
            systems["proofbit_lazy"]["control_ipc_payload_bytes"],
        )
        self.assertEqual(
            systems["software_lazy"]["total_ipc_payload_bytes"],
            systems["proofbit_lazy"]["total_ipc_payload_bytes"],
        )

    def test_eager_executes_more_epoch_checks_at_depth(self) -> None:
        report = pb.build_report(
            trials=80,
            contamination_rate=0.25,
            boundaries=(4,),
            rounds=1,
        )
        systems = report["scale"][0]["systems"]
        eager_checks = systems["software_eager"]["validation_events"]["epoch_checks"]
        lazy_checks = systems["software_lazy"]["validation_events"]["epoch_checks"]
        proof_checks = systems["proofbit_lazy"]["validation_events"]["epoch_checks"]
        self.assertGreater(eager_checks, lazy_checks)
        self.assertEqual(lazy_checks, 0)
        self.assertEqual(proof_checks, 0)

    def test_dynamic_faults_are_exercised(self) -> None:
        report = pb.build_report(
            trials=100,
            contamination_rate=0.25,
            boundaries=(2,),
            rounds=1,
        )
        systems = report["scale"][0]["systems"]
        for name in pb.SYSTEMS:
            per_kind = systems[name]
            self.assertEqual(per_kind["replay_duplicates_accepted"], 0)
            self.assertGreater(per_kind["revocations"], 0)


if __name__ == "__main__":
    unittest.main()
