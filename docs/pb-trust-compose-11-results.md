# PB-TRUST-COMPOSE-11 — Results

## Official evidence

GitHub Actions run `32492301425`, job `96802556689`.

```text
Ubuntu 24.04.4
CPython 3.12.14
8 frozen attacker opcodes
6 frozen attack scenarios
max attacker program length = 5
224,688 exhaustive programs/system
11 rotated-order valid-path rounds
10,000 valid effects/system/round
```

All seven TC11 unit tests, the bounded exhaustive search, and the frozen oracle PASS.

## Safety search

| Machine | Programs tested | Bypass programs | Scenarios with bypass |
| --- | ---: | ---: | ---: |
| flat value machine | 224,688 | **60,025** | **6/6** |
| tagged capability machine | 224,688 | **0** | **0/6** |
| ProofBit machine | 224,688 | **0** | **0/6** |

### Flat-machine bypass distribution

| Scenario | Bypass programs | Shortest bypass |
| --- | ---: | ---: |
| `FORGE_NO_AUTH` | 3,883 | 2 instructions |
| `REBIND_VALID_A_TO_B` | 15,385 | 1 instruction |
| `STALE_AFTER_EPOCH` | 15,385 | 1 instruction |
| `REPLAY_CONSUMED` | 15,385 | 1 instruction |
| `DUPLICATE_ONE_AUTH` | 3,525 | 2 instructions |
| `RAW_RECONSTRUCTION` | 6,462 | 2 instructions |

Both strong machines produced zero bypass programs in every frozen scenario.

## Valid-path Python reference runtime

| Machine | Median valid effects/s |
| --- | ---: |
| flat value machine | **923,392/s** |
| tagged capability machine | **800,972/s** |
| ProofBit machine | **216,902/s** |

Primary strong-control ratio:

```text
ProofBit / tagged capability = 0.2708x
tagged capability / ProofBit = 3.6928x
```

This is Python reference-model throughput, not cycle-accurate or hardware performance. The current ProofBit path constructs `Evidence`, stores it in `ProofProcessor`, and runs statement/authority/epoch/replay verification; the conventional capability path performs a smaller direct tagged-authority check. No silicon speed ordering is claimed.

## Logical metadata surface

TC11 records fields, not packed hardware bits.

```text
flat:
  allow

capability:
  tag + action + issuer + epoch + nonce

ProofBit:
  tag + statement + authority + epoch + proof_id + provenance
```

The capability machine receives the same unforgeable-tag model assumption as ProofBit.

## Explicit privileged escape result

The following probes are intentionally unscored:

```text
DEBUG_EFFECT
DMA_EFFECT
PRIVILEGED_MINT
```

For **all three** machines:

```text
debug bypass effect   = true
dma bypass effect     = true
privileged mint effect = true
```

Therefore TC11 does not claim protection once debug/DMA/privileged authority is defined to bypass the scored user-mode machine boundary.

## Main negative result

> A conventional mandatory tagged-capability `EFFECT` instruction exactly reproduces ProofBit's frozen unprivileged safety result: zero bypasses across 224,688 bounded attacker programs. In this Python reference implementation it is also materially faster. TC11 therefore does not demonstrate a unique ProofBit advantage from unforgeable tagged memory + mandatory effect enforcement alone.

The evidence-supported architectural conclusion is narrower:

> Mandatory lower-level authority tags bound to action, epoch and consume-once identity close the tested forge/rebind/stale/replay/raw-reconstruction paths. ProofBit can encode richer proof semantics at that boundary, but TC11 has not yet shown a scenario where those richer semantics outperform a strong conventional tagged-capability control.

## What TC11 actually pushes next

The remaining boundary is no longer ordinary unprivileged ISA execution.

A stronger next experiment should extend enforcement across paths that TC11 explicitly allows to escape:

```text
debug / privileged execution
DMA / peripheral writes
tag/proof coherence across caches
context switches / virtualization
speculative or transient execution
```

A conventional whole-system tagged architecture remains the required anti-strawman.

## Claim boundary

Executable deterministic Python ISA/memory reference model. The exhaustive claim is only over the frozen 8-opcode alphabet, six scenarios, and program length <= 5. Unforgeable tags are a model axiom. No RTL, cycle accuracy, physical tag storage, cache/coherence, speculative execution, IOMMU, cryptography, transistor/area/energy, silicon performance, novelty, patentability, or universal-superiority claim.
