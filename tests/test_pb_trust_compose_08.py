from __future__ import annotations
import unittest
from benchmarks import pb_trust_compose_08 as tc
class PBTrustCompose08Tests(unittest.TestCase):
    def test_frozen_release_skew_scenarios(self):
        self.assertEqual([x[0] for x in tc.SCENARIOS],['ALIGNED_V3','SKEW_LATEST_V5','NEGOTIATED_DOWNGRADE_V3','ALIGNED_V5','NEW_PRIMITIVE_V6'])
        self.assertEqual(tc.SCENARIOS[1][1],{'python':5,'rust':4,'node':3})
    def test_wire_sizes_are_frozen(self):
        self.assertEqual(tc.TOKEN.size,56);self.assertEqual(tc.POLICY.size,16)
    def test_v3_to_v5_adds_two_guarantees(self):
        self.assertEqual(tc.policy_mask(3).bit_count(),4);self.assertEqual(tc.policy_mask(5).bit_count(),6)
    def test_v6_is_outside_frozen_primitive_set(self):
        self.assertTrue(tc.policy_mask(6)&~tc.KNOWN_MASK)
    def test_release_work_has_strong_canonical_control(self):
        w=tc.release_work();self.assertEqual(w['software_canonical_runtime'],w['proofbit_contract']);self.assertEqual(w['software_per_language_artifacts']['trust_source_releases_v3_to_v5'],6);self.assertEqual(w['software_canonical_runtime']['descriptor_updates_v3_to_v5'],2)
    def test_cases_include_valid_and_faults(self):
        names=[x[0] for x in tc.cases(5)];self.assertEqual(names,['VALID','DIGEST_MISMATCH','REPLAY_ZERO','PROVENANCE_ZERO','OUTCOME_ZERO','TRUNCATED'])
    def test_v3_does_not_require_later_guarantees(self):
        expected={n:ok for n,ok,_ in tc.cases(3)};self.assertTrue(expected['PROVENANCE_ZERO']);self.assertTrue(expected['OUTCOME_ZERO'])
if __name__=='__main__':unittest.main()