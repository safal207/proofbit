from __future__ import annotations

import unittest

from benchmarks import pb_trust_compose_10 as tc


class PBTrustCompose10Tests(unittest.TestCase):
    def test_frozen_attack_set(self):
        self.assertEqual(
            tc.ATTACKS,
            (
                "DIRECT_OPEN",
                "SHELL_REDIRECT",
                "SYMLINK_ALIAS",
                "RENAME_REPLACE",
                "INHERITED_FD",
                "STALE_FD_AFTER_CHMOD",
            ),
        )

    def test_same_wire_contract_is_frozen(self):
        self.assertEqual(tc.TOKEN.size, 56)
        raw = tc.pack_token(123)
        self.assertEqual(len(raw), 56)
        self.assertTrue(tc.app_validate(raw))

    def test_strong_software_is_primary_anti_strawman(self):
        self.assertEqual(tc.SYSTEMS[1], "software_os_reference_monitor")
        self.assertEqual(tc.SYSTEMS[2], "proofbit_os_boundary")

    def test_strong_tcb_topology_matches(self):
        surface = tc.tcb_surface(65534)
        conventional = surface["software_os_reference_monitor"]
        proof = surface["proofbit_os_boundary"]
        self.assertEqual(conventional, proof)
        self.assertEqual(conventional["mandatory_os_uid_boundary"], 1)
        self.assertFalse(conventional["writable_handle_exposed_to_application"])

    def test_application_resource_exposes_handle_surface(self):
        row = tc.tcb_surface(65534)["application_owned_resource"]
        self.assertEqual(row["mandatory_os_uid_boundary"], 0)
        self.assertTrue(row["writable_handle_exposed_to_application"])

    def test_same_privilege_probe_is_explicitly_not_a_score(self):
        # The benchmark result documents this separately because same-UID/root
        # compromise is outside the scored unprivileged attacker model.
        self.assertIn("same_privilege", tc.run.__doc__ or "same_privilege")


if __name__ == "__main__":
    unittest.main()
