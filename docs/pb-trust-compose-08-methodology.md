# PB-TRUST-COMPOSE-08 methodology

`PB-TC08/v0.1 independent-release-skew` tests whether a trust contract stays safe and available while application artifacts are on different release levels.

## Systems

- `software_per_language_artifacts`: Python/Rust/Node own trust-policy logic in their release artifacts. New policy versions require language artifact releases, but newer artifacts remain backward-compatible with older policy versions.
- `software_canonical_runtime`: strongest conventional control. A generic validator in every language consumes the same 16-byte policy descriptor and 56-byte token. Descriptor-only changes inside the frozen primitive set do not require source releases.
- `proofbit_contract`: same descriptor and wire sizes as the canonical conventional control, interpreted as a proof-contract token.

Any result reproduced by `software_canonical_runtime` is a canonical-contract architecture result, not uniquely ProofBit.

## Frozen release scenarios

1. `ALIGNED_V3`: Python/Rust/Node artifacts all v3; active policy v3.
2. `SKEW_LATEST_V5`: artifacts Python v5, Rust v4, Node v3; producer activates v5.
3. `NEGOTIATED_DOWNGRADE_V3`: same skewed artifacts, but active policy is negotiated down to v3.
4. `ALIGNED_V5`: all artifacts v5; active policy v5.
5. `NEW_PRIMITIVE_V6`: all current artifacts v5; policy v6 adds primitive bit `0x40`, outside the frozen validator set.

The direct v5 skew therefore tests availability under safe fail-closed behavior. The v3 downgrade tests the cost of restoring availability by weakening the active guarantee set.

## Policy generations

```text
v3 = statement + authority + epoch + replay
v4 = v3 + provenance
v5 = v4 + outcome
v6 = v5 + a new primitive outside the frozen validator set
```

For the negotiated v3 window, guarantee coverage relative to v5 is `4/6`; `provenance` and `outcome` are intentionally not guaranteed.

## Frozen vector family

Every active policy is exercised with:

```text
VALID
DIGEST_MISMATCH
REPLAY_ZERO
PROVENANCE_ZERO
OUTCOME_ZERO
TRUNCATED
```

A field is only required when its policy bit is active. This prevents the v3 compatibility window from being incorrectly scored against v5-only guarantees.

## Primary metrics

- valid availability per release scenario;
- unsafe accepts;
- fault rejection accuracy;
- cross-language decision disagreement;
- trust-policy source releases versus descriptor updates;
- guarantee coverage during negotiated downgrade;
- runtime throughput as a secondary implementation metric.

No single winner score is computed.

## Fairness / claim boundary

The conventional canonical runtime and ProofBit receive the same descriptor size, token size, primitive set, policy digests, compatibility model and frozen vectors. A new primitive invalidates the descriptor-only update advantage for both systems: in this software fixture all three language validators require semantic/runtime updates before v6 can be accepted.

This is real Python/Rust/Node subprocess parsing with frozen artifact-version configurations on one Linux checkout. Release counts model trust-policy ownership; they are not package-registry telemetry, deployment traces or measured engineering hours. The benchmark does not establish network, cryptographic, silicon, energy, novelty, patentability or universal superiority claims.