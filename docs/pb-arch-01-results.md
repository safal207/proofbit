# PB-ARCH-01 v0.1 — First Cross-Architecture Result

## Status

This document records the first automated cross-repository execution-boundary comparison between the ProofBit software reference and CaPU's Rust P6 software reference.

Reference run:

```text
ProofBit GitHub Actions run: 32467398497
Ubuntu 24.04
CPython 3.12.14
Rust 1.98.0
ProofBit head: 6827c2401c3f7268407554e1ec03ec1d98f1c4fb
Pinned CaPU adapter: 8d0fb9d85415a53863ead80c4604c981b517fb5a
Decisions: 10,000
Contamination: 10%
```

The Python reference suite passed on Python 3.11, 3.12 and 3.13. The cross-architecture CaPU job also passed.

## Frozen fault classes

```text
UNKNOWN
STALE
REPLAY
CONFLICT
FALSE_SUCCESS
```

The workload contains 9,000 normal decisions and 1,000 adversarial decisions, split equally across the five fault classes.

## Result

| Metric | Value-only reference | ProofBit ProofProcessor | CaPU P6 Rust reference |
| --- | ---: | ---: | ---: |
| normal decisions | 9,000 | 9,000 | 9,000 |
| adversarial decisions | 1,000 | 1,000 | 1,000 |
| native fault-kind coverage | 0 / 5 | 5 / 5 | 1 / 5 |
| fault-kind coverage | 0% | 100% | 20% |
| semantic decision coverage | full stream, faults collapsed to value | 100% | 92% |
| safe / legitimate normal actions | 9,000 | 9,000 | 9,000 |
| unsafe actions | 1,000 | 0 | 0 on supported semantics |
| unsupported / unassessed decisions | 0* | 0 | 800 |
| false-positive blocks | 0 | 0 | 0 |
| measured boundary throughput | 4.17M decisions/s | 0.434M decisions/s | 4.17M supported decisions/s |
| useful / legitimate useful throughput | 3.75M actions/s | 0.391M actions/s | 4.08M actions/s |

`*` The value-only reference does not report the fault classes as unsupported because it executes them after collapsing them to the same `true` value. Its native fault semantic coverage is therefore 0%, and the resulting 1,000 adversarial actions are counted as unsafe by the benchmark oracle.

## Exact measured values

### Value-only reference

```text
elapsed_ns: 2,396,837
decisions_per_sec: 4,172,165.23
useful_actions_per_sec: 3,754,948.71
unsafe_actions_per_million: 100,000
fault-kind coverage: 0%
```

### ProofBit ProofProcessor

```text
elapsed_ns: 23,037,354
decisions_per_sec: 434,077.63
useful_actions_per_sec: 390,669.87
unsafe_actions_per_million: 0
fault-kind coverage: 100%
```

### CaPU P6 software reference

```text
supported_decisions: 9,200
unsupported_decisions: 800
elapsed_ns: 2,203,868
supported_decisions_per_sec: 4,174,478.69
legitimate_useful_actions_per_sec: 4,083,729.15
unsafe_actions_per_million_supported_decisions: 0
fault-kind coverage: 20%
semantic decision coverage: 92%
```

CaPU's executable mapping in this adapter is:

```text
NORMAL        supported
UNKNOWN       supported through missing-commit / missing-cause rejection
STALE         unsupported in this P6 adapter
REPLAY        unsupported as the frozen execution-guard semantic in this P6 adapter
CONFLICT      unsupported in this P6 adapter
FALSE_SUCCESS unsupported as an outcome-grounding boundary
```

## Interpretation

This result does **not** establish a single winner.

The value-only reference is fast but does not distinguish any of the five frozen fault classes and executes all adversarial `true` values.

ProofBit covers all five frozen fault classes and blocks all 1,000 modeled adversarial decisions without blocking modeled normal decisions, but its current Python semantic implementation is about one order of magnitude slower at this isolated execution boundary.

CaPU's Rust P6 boundary is roughly as fast as the value-only Python reference on this runner and safely rejects the fault semantics it currently represents in the adapter, but four of the five frozen fault classes remain unassessed rather than prevented.

Therefore the meaningful frontier is:

```text
semantic coverage
    x safety within covered semantics
    x throughput
    x implementation cost
```

Raw throughput alone is not a valid cross-architecture rank when semantic coverage differs.

## CaPU v0.33 note

CaPU has a separately verified v0.33 candidate with stale checkpoint, queue epoch/incarnation and replay-related capability evidence. Those capabilities are not credited to this PB-ARCH-01 result because the benchmark pins the stable P6 adapter commit and requires every claimed capability to be exercised inside the same executable measurement boundary.

The next CaPU benchmark objective is therefore measurable:

```text
20% frozen fault-kind coverage
  -> extend adapter using verified CaPU capabilities
  -> preserve zero unsafe actions on covered semantics
  -> measure throughput change
```

## Next architecture target

After extending CaPU coverage, the next internal architecture adapter is COSMIC ORGANICS / MORPHOS. MORPHOS requires a different mapping because its native computational object is state transition rather than an execution permission decision. Unsupported semantics must remain explicit there as well.
