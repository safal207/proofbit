from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
bench=load(ROOT/'benchmarks/pb_trust_compose_07.py','tc07bench')
pyv=load(ROOT/'benchmarks/tc07_python_validator.py','tc07pyv')

class PBTrustCompose07Tests(unittest.TestCase):
 def test_wire_and_policy_sizes_are_frozen(self):
  self.assertEqual(bench.TOKEN.size,56);self.assertEqual(bench.POLICY.size,16)
 def test_high64_statement_exceeds_javascript_safe_integer(self):
  self.assertGreater(bench.STATEMENT,2**53-1)
 def test_frozen_case_names(self):
  self.assertEqual([x[0] for x in bench.conformance_vectors()],['VALID_HIGH64','UNKNOWN_VERSION','UNKNOWN_REQUIRED_BIT','DIGEST_MISMATCH','LITTLE_ENDIAN_REENCODE','OLD_CONSUMER_V4','REPLAY_ZERO','PROVENANCE_ZERO','OUTCOME_MISSING','AUTHORITY_MISMATCH','EPOCH_MISMATCH','RESERVED_FLAGS_NONZERO','TRAILING_BYTES','TRUNCATED'])
 def test_python_reference_matches_oracle_in_all_modes(self):
  for mode in ('manual','canonical','proofbit'):
   phex=None if mode=='manual' else bench.policy_hex()
   for name,expected,raw in bench.conformance_vectors():
    self.assertEqual(pyv.validate(raw,mode,phex),expected,(mode,name))
 def test_canonical_software_is_equal_update_surface_control(self):
  work=bench.evolution_work();soft=work['software_canonical_contract'];proof=work['proofbit_contract']
  self.assertEqual(soft,proof)
  self.assertEqual(soft['descriptor_updates'],4);self.assertEqual(soft['language_conformance_invocations'],12)
 def test_manual_per_language_surface_scales_by_language(self):
  manual=bench.evolution_work()['software_per_language'];self.assertEqual(manual['managed_policy_sources'],3);self.assertEqual(manual['validator_source_updates'],12);self.assertEqual(manual['language_conformance_invocations'],12)
 def test_current_digest_is_derived_from_frozen_contract(self):
  self.assertEqual(bench.policy_digest(5,0x3F),bench.CURRENT_DIGEST)

if __name__=='__main__':unittest.main()
