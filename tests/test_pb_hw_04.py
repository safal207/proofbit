from __future__ import annotations
import unittest
from benchmarks import pb_hw_04 as hw

class PBHW04Tests(unittest.TestCase):
    def test_protocol_identity(self):
        self.assertEqual(hw.BENCHMARK_ID,'PB-HW-04')
        self.assertEqual(hw.VERSION,'0.1')
        self.assertEqual(hw.PROTOCOL,'PB-HW-04/v0.1 physical-proof-memory-cache-economics')

    def test_physical_memory_bits_are_frozen(self):
        self.assertEqual(hw.PHYSICAL_EVIDENCE_BITS['single_port_conventional'],65536)
        self.assertEqual(hw.PHYSICAL_EVIDENCE_BITS['banked_conventional'],65536)
        self.assertEqual(hw.PHYSICAL_EVIDENCE_BITS['multiport_conventional_cache'],262144)
        self.assertEqual(hw.PHYSICAL_EVIDENCE_BITS['proofbit_cache'],262144)
        self.assertEqual(hw.CACHE_DATA_BITS['multiport_conventional_cache'],1024)
        self.assertEqual(hw.CACHE_TAG_VALID_BITS['multiport_conventional_cache'],112)

    def test_strong_control_has_identical_logical_memory_budget(self):
        c='multiport_conventional_cache';p='proofbit_cache'
        self.assertEqual(hw.PHYSICAL_EVIDENCE_BITS[c],hw.PHYSICAL_EVIDENCE_BITS[p])
        self.assertEqual(hw.CACHE_DATA_BITS[c],hw.CACHE_DATA_BITS[p])
        self.assertEqual(hw.CACHE_TAG_VALID_BITS[c],hw.CACHE_TAG_VALID_BITS[p])
        self.assertEqual(hw.REPLAY_STATE_BITS[c],hw.REPLAY_STATE_BITS[p])

    def test_sim_parser(self):
        text='PB_HW04_SIM PASS checks=40 failures=0 cold=4,2,2,2 warm=4,2,1,1 conflict=4,5,2,2 conflict_warm=4,5,1,1 invalidated=4,2,2,2'
        r=hw.parse_sim(text)
        self.assertEqual(r['failures'],0)
        self.assertEqual(r['warm_latency_cycles']['proofbit_cache'],1)
        self.assertGreater(r['same_bank_conflict_latency_cycles']['banked_conventional'],r['cold_latency_cycles']['banked_conventional'])

    def test_ltp_parser(self):
        self.assertEqual(hw.parse_ltp('Longest topological path in pb: length 17'),17)

if __name__=='__main__': unittest.main()
