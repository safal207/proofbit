# PB-TRUST-COMPOSE-05 Results

## Verdict

`PB-TRUST-COMPOSE-05` does **not** demonstrate a ProofBit-specific correctness, repair-work, storage, or recovery-speed advantage over a strong conventional indexed implementation with equivalent integrity and semantic-binding checks.

It does demonstrate a narrower and useful invariant:

> A recovery system that validates durable structure, statement binding, epoch binding, receipt identity and chain continuity — and that degrades invalid evidence to `UNKNOWN` or `CONFLICT` — can avoid silent false reconstruction under the frozen corruption matrix.

In TC05, both `software_indexed_integrity` and `proofbit_receipts` satisfy that invariant with the same frozen representation and repair policy.

## Reproducible environment

Official evidence:

- repository: `safal207/proofbit`
- branch: `feat/pb-trust-compose-05`
- workflow: `pb-trust-compose-05`
- run: `32476911767`
- job: `96755047833`
- measured head: `5d0227b6e32dcb1469668f342afb7e6d1ed42cc1`
- OS: Ubuntu 24.04.4
- Python: CPython 3.12.14
- rounds: 11
- execution order: rotated through all three system permutations

The job completed successfully with:

- 8 corruption-contract unit tests;
- 11-round executable benchmark;
- frozen epistemic-oracle assertions;
- strong conventional anti-strawman assertions.

## Frozen cases and oracle

| Case | Expected recovery |
| --- | --- |
| `CLEAN` | `PROVEN` |
| `JOURNAL_WRITTEN_HEAD_NOT_UPDATED` | `PROVEN` after repair |
| `HEAD_UPDATED_RECORD_TRUNCATED` | `UNKNOWN` |
| `STALE_HEAD_AFTER_RESTART` | `PROVEN` after repair |
| `BROKEN_PREV_POINTER` | `UNKNOWN` |
| `STATEMENT_REBOUND_IN_DURABLE_RECORD` | `UNKNOWN` |
| `EPOCH_REBOUND_IN_DURABLE_RECORD` | `UNKNOWN` |
| `DUPLICATE_CONFLICTING_OUTCOME_RECEIPT` | `CONFLICT` |

The statement- and epoch-rebound records have a freshly recomputed CRC after mutation. Passing those cases therefore requires semantic binding checks and cannot be explained by checksum failure alone.

## Correctness

### Primary strong controls

Both `software_indexed_integrity` and `proofbit_receipts` produced across all 11 rounds:

```text
oracle accuracy              = 100%
silent false reconstruction  = 0
full indexed case coverage   = 8 / 8 cases
detected conflicting outcome = 11 / 11 rounds
```

For both systems:

```text
HEAD_UPDATED_RECORD_TRUNCATED       -> UNKNOWN
BROKEN_PREV_POINTER                 -> UNKNOWN
STATEMENT_REBOUND_IN_DURABLE_RECORD -> UNKNOWN
EPOCH_REBOUND_IN_DURABLE_RECORD     -> UNKNOWN
CONFLICTING_OUTCOME                 -> CONFLICT
```

This is the primary TC05 result.

There is **no ProofBit-specific correctness advantage** over the strong conventional indexed control in the frozen matrix.

## Representation fairness

Both primary systems use exactly:

```text
56-byte CRC-protected durable record
8-byte durable head index
statement binding validation
epoch binding validation
non-zero receipt/proof identity validation
previous-record chain validation
sequential scan fallback
safe-head repair
```

Therefore a result cannot be attributed to a hidden smaller ProofBit record, a private index or omitted integrity checks in the conventional control.

## Official work profile

Median per 8-case round:

| Metric | Conventional indexed | ProofBit receipts |
| --- | ---: | ---: |
| Records inspected | **36** | **36** |
| Repair-scan records | **24** | **24** |
| Repair writes | **6** | **6** |
| Persisted bytes | **1,884 B** | **1,884 B** |
| Recovery elapsed | **3.094 ms** | 3.259 ms |
| Fresh-process wall | **5.782 ms** | 6.646 ms |

Primary ratios:

```text
ProofBit / indexed recovery elapsed   = 1.0533x
ProofBit / indexed persisted bytes    = 1.0000x
ProofBit / indexed repair scan work   = 1.0000x
```

The current ProofBit Python fixture is therefore about **5.3% slower by median measured recovery work time** than the conventional indexed control in this run.

The raw per-round latencies vary materially relative to that small gap, so TC05 makes **no universal speed-ordering claim**.

## What was detected

For each of the two indexed systems, the frozen first-round case packet shows:

- clean: no corruption detected;
- journal/head mismatch: detected, scan fallback, one head repair;
- truncated tail: detected, recovered `UNKNOWN`, one head repair;
- stale head: detected, scan fallback, one head repair;
- broken previous pointer: detected, recovered `UNKNOWN`, one head repair;
- statement rebound with valid CRC: detected by semantic binding, recovered `UNKNOWN`;
- epoch rebound with valid CRC: detected by semantic binding, recovered `UNKNOWN`;
- contradictory outcome receipts: represented as `CONFLICT`, not collapsed to success/failure.

Across 11 rounds each indexed system recorded the same aggregate detection counts and the same recovery decisions.

## Scan-only control

`software_scan_repair` is useful but not the primary competitor.

It has no durable head index, so two head-specific cases are marked not applicable. Its report therefore covers 6/8 total benchmark cases (the current JSON field `fault_coverage = 0.75` is case coverage including the clean control).

On its applicable cases it also achieves:

```text
oracle accuracy             = 100%
silent false reconstruction = 0
```

Its smaller/faster work profile cannot be directly treated as a win over indexed systems because it does not implement or exercise the two head-index fault classes.

## Four-axis interpretation

### Utility

Both primary systems avoid confident false reconstruction and return the frozen oracle state for every corruption case.

**Result: tie.**

### Proof / trust semantics

Both systems validate the same durable bindings in this benchmark. ProofBit makes those fields part of its proof-native semantic model; the conventional control implements them explicitly as recovery policy.

**Externally observed frozen result: tie.**

### Cost

Both primary systems persist 1,884 bytes across the frozen case packet and perform the same scan/repair work.

**Result: tie.**

### Speed

The conventional indexed implementation is slightly faster in the 11-round Python measurement, but the difference is small relative to raw run variation.

**Result: no ProofBit speed win.**

## What TC05 falsified

TC05 rejects several tempting claims:

1. **"Proof-native semantics are uniquely required to detect durable statement/epoch rebinding."**
   Not shown. Strong conventional software with explicit equivalent checks also detects it.

2. **"CRC/checksum alone explains rebound safety."**
   False for the frozen test: CRC is recomputed after the rebound mutation.

3. **"ProofBit repairs corrupted indexed state with less scan/write work."**
   Not shown. Both indexed systems use 24 repair-scan records and 6 repair writes per frozen round.

4. **"ProofBit is faster under durable corruption recovery."**
   Not shown. The conventional indexed control is slightly faster in this run.

## Current evidence-supported conclusion

The strongest statement supported by TC05 is:

> Explicit durable binding and integrity semantics prevent corrupted or rebound evidence from being silently promoted to a confident state. ProofBit expresses those semantics natively, but a strong conventional indexed recovery implementation with equivalent checks reproduces the same correctness, storage and repair-work profile in this software-reference benchmark.

That narrows the next research question away from "can software implement the rules?" — clearly it can — toward whether proof-native semantics reduce **engineering complexity, policy divergence, verification surface, or hardware cost** when the same invariant must be maintained across many independently implemented components.

## Next falsifiable experiment

The most useful next step is **PB-TRUST-COMPOSE-06 — Policy Divergence / Independent Implementations**.

Instead of giving one conventional helper to every component, freeze the same trust contract and implement it independently across several adapters/components. Then mutate the contract over versions/epochs and measure:

```text
policy copies that must change
components updated correctly
semantic drift / missed checks
regression cases required
lines / branches of trust plumbing
state/schema migration work
audit reconstruction steps
runtime and storage overhead
```

Required controls should include:

1. a shared centralized conventional library — strongest software control;
2. independent conventional implementations — realistic distributed-maintenance pressure;
3. ProofBit-native contract propagation.

The benchmark must not count deliberately buggy software as evidence. Divergence faults need to arise from a frozen change protocol and independently versioned adapters, with all source and expected behavior explicit.

## Claim boundary

TC05 is deterministic Python/Linux local-file corruption evidence. CRC32 is not cryptographic authenticity. The benchmark does not establish physical-media behavior, power-loss atomicity, distributed-network correctness, processor-cycle performance, silicon area/energy, novelty, patentability, or universal performance ordering.
