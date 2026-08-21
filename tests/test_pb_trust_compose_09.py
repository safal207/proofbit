from __future__ import annotations
import unittest
from benchmarks import pb_trust_compose_09 as tc

class PBTrustCompose09Tests(unittest.TestCase):
    def test_wire_size_and_frozen_cases(self):
        self.assertEqual(tc.TOKEN.size,56)
        self.assertEqual(tc.ATTACK_CASES,(
            "VALID_API","DIRECT_CALL_INVALID_AUTHORITY","ALTERNATE_ENTRYPOINT_STALE",
            "CACHED_APPROVAL_AFTER_EPOCH_CHANGE","MUTATE_AFTER_VALIDATE_REBIND",
            "REPLAY_AFTER_VALIDATE","DESERIALIZATION_BYPASS","FALSE_SUCCESS_SELF_REPORT"))

    def test_application_validator_is_not_mandatory_boundary(self):
        s=tc.tcb_surface()
        self.assertEqual(s["application_validator"]["mandatory_effect_boundary_checks"],0)
        self.assertEqual(s["software_reference_monitor"]["mandatory_effect_boundary_checks"],1)
        self.assertEqual(s["proofbit_execution_boundary"]["mandatory_effect_boundary_checks"],1)

    def test_strong_software_is_primary_anti_strawman(self):
        r=tc.run(rounds=1,valid_count=3)
        self.assertEqual(r["primary_anti_strawman"],"software_reference_monitor")
        app=r["attack_results"]["application_validator"]
        mon=r["attack_results"]["software_reference_monitor"]
        pb=r["attack_results"]["proofbit_execution_boundary"]
        self.assertGreater(app["unsafe_side_effects"],0)
        self.assertGreater(app["false_successes"],0)
        for strong in (mon,pb):
            self.assertEqual(strong["oracle_accuracy"],1.0)
            self.assertEqual(strong["unsafe_side_effects"],0)
            self.assertEqual(strong["false_successes"],0)
            self.assertEqual(strong["bypass_failures"],0)

    def test_host_escape_is_explicitly_out_of_scope(self):
        r=tc.run(rounds=1,valid_count=1)
        self.assertIn("NOT_MODELED",r["host_escape_status"])
        self.assertIn("worker process",r["resource_isolation_assumption"])

if __name__=="__main__":
    unittest.main()
