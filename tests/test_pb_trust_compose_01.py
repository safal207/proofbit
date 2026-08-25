import unittest

from benchmarks.pb_trust_compose_01 import (
    FAULT_KINDS,
    SOFTWARE_METADATA_FIELDS,
    build_report,
    build_trials,
)


class PBTrustCompose01Tests(unittest.TestCase):
    def test_deterministic_fault_distribution(self):
        rows = build_trials(10_000, 0.12)
        counts = {kind: 0 for kind in ("VALID", *FAULT_KINDS)}
        for row in rows:
            counts[row.kind] += 1

        self.assertEqual(counts["VALID"], 8_800)
        for kind in FAULT_KINDS:
            self.assertEqual(counts[kind], 200)

    def test_all_competent_controls_satisfy_frozen_oracle(self):
        report = build_report(1_000, 0.12, (4,))
        systems = report["scale"][0]["systems"]
        for name in ("software_shared", "software_serialized", "proofbit"):
            with self.subTest(system=name):
                self.assertEqual(systems[name]["oracle_accuracy"], 1.0)
                self.assertEqual(systems[name]["unsafe_authorization_dispatches"], 0)
                self.assertEqual(systems[name]["false_success_claims"], 0)
                self.assertEqual(systems[name]["missed_valid_dispatches"], 0)

    def test_statement_rebinding_is_blocked_end_to_end(self):
        report = build_report(1_000, 0.12, (8,))
        systems = report["scale"][0]["systems"]
        for name in ("software_shared", "software_serialized", "proofbit"):
            row = systems[name]["per_kind"]["REBIND_STATEMENT"]
            self.assertGreater(row["trials"], 0)
            self.assertEqual(row["oracle_correct"], row["trials"])
            self.assertEqual(row["unsafe_dispatches"], 0)

    def test_serialized_metadata_work_scales_with_boundaries(self):
        trials = 100
        report = build_report(trials, 0.12, (1, 4, 8))
        for row in report["scale"]:
            boundaries = row["boundaries"]
            serialized = row["systems"]["software_serialized"]
            shared = row["systems"]["software_shared"]
            proofbit = row["systems"]["proofbit"]
            self.assertEqual(
                serialized["metadata_field_assignments"],
                trials * boundaries * SOFTWARE_METADATA_FIELDS,
            )
            self.assertEqual(shared["metadata_field_assignments"], 0)
            self.assertEqual(shared["object_ref_hops"], trials * boundaries)
            self.assertEqual(proofbit["proof_ref_hops"], trials * boundaries)

    def test_report_preserves_strong_software_control_and_no_winner_score(self):
        report = build_report(100, 0.12, (1,))
        self.assertTrue(report["no_single_winner_score"])
        systems = report["scale"][0]["systems"]
        self.assertEqual(systems["software_shared"]["oracle_accuracy"], 1.0)
        self.assertIn("strong conventional control", " ".join(report["caveats"]))


if __name__ == "__main__":
    unittest.main()
