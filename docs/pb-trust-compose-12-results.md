# PB-TRUST-COMPOSE-12 — Results

## Official evidence

GitHub Actions run `32493138052`, job `96805239929`.

```text
Ubuntu 24.04.4
CPython 3.12.14
6 frozen scored cross-domain scenarios
11 rotated-order valid-path rounds
10,000 valid CPU/debug/DMA effects/system/round
```

All seven TC12 unit tests, the executable whole-system fixture, and the frozen oracle PASS.

## Safety result

| System | Blocked attacks | Unsafe effects | Oracle accuracy |
| --- | ---: | ---: | ---: |
| CPU-only tag machine | 0/6 | **6** | 0% |
| whole-system capability machine | **6/6** | **0** | **100%** |
| whole-system ProofBit machine | **6/6** | **0** | **100%** |

The CPU-only tag baseline fails every frozen cross-domain scenario:

```text
DEBUG_DIRECT_EFFECT
DMA_DIRECT_EFFECT
DEBUG_FORGED_TAG
CONTEXT_SWITCH_LEAK
CACHE_TAG_DATA_SPLIT
SNAPSHOT_REPLAY_ROLLBACK
```

Both strong whole-system architectures block all six while still accepting valid CPU, debug and DMA effects.

## Whole-system coherence surface

Both strong systems enforce the same modeled domains:

```text
cpu
debug
dma
cache
context
```

Both also have:

```text
global replay state       = true
context binding           = true
object-version binding    = true
```

This equality is deliberate. The conventional capability architecture receives the same whole-system unforgeable metadata assumption as ProofBit.

## Valid-path Python reference runtime

| System | Median valid effects/s |
| --- | ---: |
| CPU-only tag machine | **723,256/s** |
| whole-system capability machine | **600,703/s** |
| whole-system ProofBit machine | **187,927/s** |

Primary strong-control ratios:

```text
ProofBit / whole-system capability = 0.3128x
whole-system capability / ProofBit = 3.1965x
```

This is Python reference-model throughput only. The ProofBit path constructs/stores `Evidence` and executes `ProofProcessor` statement/authority/epoch/replay checks; the capability path uses a smaller direct metadata check. No cycle-accurate or silicon speed ordering is claimed.

## Explicit deeper escape boundary

The following probes remain intentionally unscored for every system:

```text
PHYSICAL_TAG_STORE_TAMPER
MALICIOUS_FIRMWARE
```

Both are defined as bypassing the modeled coherence root. TC12 therefore does not claim whole-machine security against physical metadata corruption or firmware that can rewrite/bypass the authority plane.

## Main negative result

> Extending an unforgeable authority-tag plane coherently across CPU, debug, DMA, cache/object version, context identity and monotonic replay state closes every frozen TC12 cross-domain bypass. A strong conventional whole-system capability architecture reproduces ProofBit's safety result exactly and is materially faster in the current Python reference implementation.

TC12 therefore does **not** establish a unique ProofBit advantage from whole-system tag/coherence enforcement alone.

The remaining ProofBit hypothesis must now become narrower and more concrete. A differentiator would need to come from one or more of:

- richer proof semantics that a capability tuple does not efficiently encode;
- proof derivation/composition rather than authority possession alone;
- evidence-backed outcome semantics across independent devices;
- lower implementation economics in actual RTL;
- a physical memory/ISA encoding that reduces proof cost enough to change the utility/cost frontier.

## Recommended next boundary

The next meaningful step is no longer another Python authority wrapper. It is an **RTL-oriented microarchitecture experiment** with an equally strong conventional tagged-capability baseline.

Candidate `PB-HW-01`:

```text
baseline tagged pipeline
vs
ProofBit proof-tag pipeline
```

Measure in simulation/synthesis terms:

```text
cycles / effect
critical-path depth
register / metadata bits
BRAM / LUT / FF estimates
proof-cache hit/miss cost
replay-table cost
throughput
stall rate
```

The safety oracle should reuse TC11/TC12 attack vectors. Any capability baseline matching ProofBit remains a valid negative result.

## Claim boundary

Executable Python whole-system coherence reference model. No RTL, physical DMA/IOMMU, real cache-coherence protocol, speculative execution, firmware measurement, physical tag RAM, cycle accuracy, transistor/area/energy, silicon performance, novelty, patentability or universal-superiority claim.
