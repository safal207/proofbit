# PB-TRUST-COMPOSE-08 results

Official evidence: GitHub Actions run `32479522892`, job `96762705692`.

Environment:

```text
Ubuntu 24.04.4
CPython 3.12.14
Node 22.23.2
rustc 1.98.0
5 frozen release scenarios
250 repetitions/case
11 rotated-order rounds
```

All seven TC08 unit tests, the executable Python/Rust/Node benchmark, and the frozen release-skew oracle PASS.

## Safety and availability

Every system rejected every invalid vector in every scenario:

```text
unsafe accepts = 0
fault rejection accuracy = 100%
```

Valid-current-policy availability:

| Scenario | Per-language artifacts | Canonical software | ProofBit |
| --- | ---: | ---: | ---: |
| `ALIGNED_V3` | 100% | 100% | 100% |
| `SKEW_LATEST_V5` (`5/4/3`) | **33.3%** | **100%** | **100%** |
| `NEGOTIATED_DOWNGRADE_V3` (`5/4/3`) | 100% | 100% | 100% |
| `ALIGNED_V5` | 100% | 100% | 100% |
| `NEW_PRIMITIVE_V6` | **0%** | **0%** | **0%** |

Under direct v5 activation, per-language artifacts remain safe but disagree on the valid request: the v5 consumer accepts while v4/v3 consumers fail closed. With 250 repetitions this produces 250 cross-language decision disagreements per round. Canonical software and ProofBit produce zero disagreements and 100% valid availability because policy evolution stays inside the already-supported primitive set.

## Downgrade trade-off

The mixed `5/4/3` deployment can restore full availability by negotiating the active contract down to v3, but the downgrade is not free:

```text
v5 required primitives = 6
v3 required primitives = 4
relative guarantee coverage = 4/6 = 66.7%
lost guarantees = provenance + outcome
```

So availability recovery via downgrade explicitly weakens the trust contract.

## Release/update surface

For policy evolution v3 -> v4 -> v5:

| Metric | Per-language artifacts | Canonical software | ProofBit |
| --- | ---: | ---: | ---: |
| Managed trust-policy sources | 3 | **1** | **1** |
| Trust-source releases | **6** | **0** | **0** |
| Descriptor updates | 0 | **2** | **2** |
| Token bytes | 56 B | 56 B | 56 B |
| Policy descriptor | embedded | 16 B | 16 B |

This reduction belongs to canonical-contract architecture. The strongest conventional control exactly reproduces ProofBit's descriptor-only update surface inside the frozen primitive set.

## New primitive boundary

Policy v6 adds primitive bit `0x40`, outside the frozen validator set.

All current systems fail closed:

```text
valid v6 availability = 0%
unsafe accepts = 0
```

In this software fixture, both canonical software and ProofBit require semantic/runtime validator updates in all three languages before v6 can be accepted. Therefore the descriptor-only evolution advantage is explicitly bounded: it does not survive the introduction of a genuinely new primitive.

## Runtime medians

The benchmark includes five scenarios and hundreds of real subprocess validations per round, so process startup dominates these implementation-level numbers:

| System | Language validations/s |
| --- | ---: |
| per-language artifacts | **50,448/s** |
| canonical conventional | 49,052/s |
| ProofBit | 48,767/s |

ProofBit / canonical throughput = `0.9942x` (~0.6% lower). This is treated as process/runner noise, not a stable speed ordering.

## Main result

> Release skew creates a real safety/availability trade-off when trust semantics are embedded independently in application artifacts. A canonical version-bound runtime decouples descriptor-only policy evolution from application release cadence and preserves availability across the tested skew. ProofBit reproduces that architecture, but TC08 does not show a unique ProofBit correctness, update-surface, representation-size or runtime advantage over the strongest conventional canonical control.

The more important boundary is now explicit: when the trust contract introduces a genuinely new primitive, both canonical software and the current ProofBit software reference must evolve verifier semantics.

## Next falsifiable boundary

`PB-TRUST-COMPOSE-09`: enforcement bypass / trusted computing base.

Instead of asking whether conventional software can express the same contract, ask how many executable paths can bypass it. Compare:

1. application-level canonical validators;
2. centralized mandatory software enforcement at the side-effect boundary;
3. ProofBit-style proof-aware execution/memory boundary.

Exercise direct calls, stale cached validation, alternate transport, shell/native path, replay after validation, deserialization bypass and outcome self-report. Measure bypass surface, number of enforcement points, unsafe side effects, required trusted code, latency and auditability.

A conventional mandatory reference monitor matching ProofBit remains a valid negative result.

## Claim boundary

Real Python/Rust/Node subprocess parsing with frozen artifact-version configurations on one Linux checkout. Release counts model trust-policy ownership rather than package-registry telemetry, deployment traces or measured engineering hours. No network, cryptography, hardware, energy, novelty, patentability or universal-superiority claim.