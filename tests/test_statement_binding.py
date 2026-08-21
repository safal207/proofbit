import unittest

from proofbit import Evidence, ProofProcessor


class StatementBindingTests(unittest.TestCase):
    def test_valid_proof_for_action_a_cannot_authorize_action_b(self):
        cpu = ProofProcessor()
        cpu.store_evidence(
            0,
            Evidence(
                "release_invoice_A",
                True,
                proof_id=101,
                authority=1,
                epoch=1,
            ),
        )

        self.assertFalse(
            cpu.guarded_execute(
                0,
                expected_statement="release_invoice_B",
            )
        )
        self.assertEqual(cpu.side_effects, 0)

    def test_matching_statement_remains_allowed(self):
        cpu = ProofProcessor()
        cpu.store_evidence(
            0,
            Evidence(
                "release_invoice_A",
                True,
                proof_id=102,
                authority=1,
                epoch=1,
            ),
        )

        self.assertTrue(
            cpu.guarded_execute(
                0,
                expected_statement="release_invoice_A",
            )
        )
        self.assertEqual(cpu.side_effects, 1)


if __name__ == "__main__":
    unittest.main()
