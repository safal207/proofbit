from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "pb_trust_compose_02.py"
SPEC = importlib.util.spec_from_file_location("pb_trust_compose_02", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
pb = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pb
SPEC.loader.exec_module(pb)


class PBTrustCompose02Tests(unittest.TestCase):
    def test_compact_codec_round_trips_all_fault_kinds(self) -> None:
        rows = pb.build_trials(700, 0.60)
        kinds = set()
        for row in rows:
            message = pb.envelope(row)
            restored = pb.decode_compact(pb.encode_compact(message))
            self.assertEqual(restored, message)
            kinds.add(row.kind)
        self.assertEqual(kinds, {"VALID", *pb.FAULT_KINDS})

    def test_json_codec_round_trips_envelope(self) -> None:
        row = pb.build_trials(10, 0.60)[-1]
        message = pb.envelope(row)
        self.assertEqual(pb.decode_json(pb.encode_json(message)), message)

    def test_compact_control_prevents_codec_strawman(self) -> None:
        row = pb.build_trials(100, 0.12)[0]
        message = pb.envelope(row)
        self.assertEqual(len(pb.encode_compact(message)), pb.COMPACT.size)
        self.assertLess(pb.COMPACT.size, len(pb.encode_json(message)))

    def test_real_ipc_all_competent_implementations_satisfy_oracle(self) -> None:
        report = pb.build_report(trials=120, contamination_rate=0.30, boundaries=(1, 2))
        self.assertTrue(report["no_single_winner_score"])
        for scale in report["scale"]:
            for name in ("software_json", "software_compact", "proofbit_compact"):
                system = scale["systems"][name]
                self.assertEqual(system["oracle_accuracy"], 1.0)
                self.assertEqual(system["unsafe_authorization_dispatches"], 0)
                self.assertEqual(system["false_success_claims"], 0)
                self.assertEqual(system["missed_valid_dispatches"], 0)

    def test_request_payload_cost_scales_with_boundary_count(self) -> None:
        report = pb.build_report(trials=60, contamination_rate=0.20, boundaries=(1, 2))
        one, two = report["scale"]
        for name in ("software_json", "software_compact", "proofbit_compact"):
            first = one["systems"][name]
            second = two["systems"][name]
            self.assertEqual(second["payload_bytes"], first["payload_bytes"])
            self.assertEqual(
                second["request_ipc_payload_bytes"],
                first["request_ipc_payload_bytes"] * 2,
            )
            self.assertEqual(
                second["response_ipc_payload_bytes"],
                first["response_ipc_payload_bytes"],
            )
            self.assertEqual(
                first["total_ipc_payload_bytes"],
                first["request_ipc_payload_bytes"] + first["response_ipc_payload_bytes"],
            )

    def test_transport_message_count_includes_result_edge(self) -> None:
        report = pb.build_report(trials=30, contamination_rate=0.20, boundaries=(1, 2))
        one, two = report["scale"]
        for name in ("software_json", "software_compact", "proofbit_compact"):
            self.assertEqual(one["systems"][name]["transport_messages"], 30 * 2)
            self.assertEqual(two["systems"][name]["transport_messages"], 30 * 3)

    def test_proofbit_and_compact_software_use_same_wire_size(self) -> None:
        report = pb.build_report(trials=60, contamination_rate=0.20, boundaries=(1,))
        systems = report["scale"][0]["systems"]
        self.assertEqual(
            systems["proofbit_compact"]["mean_payload_bytes"],
            systems["software_compact"]["mean_payload_bytes"],
        )
        self.assertEqual(
            systems["proofbit_compact"]["total_ipc_payload_bytes"],
            systems["software_compact"]["total_ipc_payload_bytes"],
        )


if __name__ == "__main__":
    unittest.main()
