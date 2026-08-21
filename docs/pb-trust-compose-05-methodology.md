# PB-TRUST-COMPOSE-05 Methodology

## Question

When durable trust metadata is incomplete, contradictory, or rebound after it was originally written, can a system avoid reconstructing a confident false state?

TC05 is deliberately falsifiable. If strong conventional software with equivalent integrity checks matches ProofBit, that is a valid negative ProofBit result.

## Compared systems

### `software_scan_repair`

Conventional append-only durable log recovered by sequential scan. It has no durable per-transaction head index, so head-specific faults are marked not applicable rather than counted as failures.

### `software_indexed_integrity`

Primary anti-strawman control:

- fixed-width CRC-protected durable records;
- durable head index;
- previous-record chain;
- statement binding check;
- epoch binding check;
- non-zero proof/receipt identity check;
- chain-continuity validation;
- sequential scan fallback;
- safe-head repair after fallback.

This is intentionally a competent conventional implementation. It is not weakened to manufacture a ProofBit advantage.

### `proofbit_receipts`

ProofBit receipt-chain reference using the same record width, head width, validation fields, fallback scan and repair policy.

The difference under test is therefore architectural placement/semantics, not hidden access to stronger checks or a smaller record.

## Representation fairness

Every system uses a 56-byte durable record:

```text
48-byte TC04 semantic payload
+ 4-byte CRC32
+ 4 reserved bytes
= 56 bytes
```

Both indexed systems use the same:

```text
8-byte durable head
```

CRC32 is used only as a deterministic corruption detector. It is not cryptographic authenticity evidence.

## Frozen cases

TC05 runs one clean control plus seven deterministic corruption/anomaly cases:

```text
CLEAN
JOURNAL_WRITTEN_HEAD_NOT_UPDATED
HEAD_UPDATED_RECORD_TRUNCATED
STALE_HEAD_AFTER_RESTART
BROKEN_PREV_POINTER
STATEMENT_REBOUND_IN_DURABLE_RECORD
EPOCH_REBOUND_IN_DURABLE_RECORD
DUPLICATE_CONFLICTING_OUTCOME_RECEIPT
```

### Semantic rebound control

For `STATEMENT_REBOUND_IN_DURABLE_RECORD` and `EPOCH_REBOUND_IN_DURABLE_RECORD`, CRC is recomputed after the mutation.

Therefore these cases cannot be passed merely by detecting a checksum mismatch. The recovery path must evaluate statement/epoch binding itself.

## Frozen epistemic oracle

```text
CLEAN                                  -> PROVEN
JOURNAL_WRITTEN_HEAD_NOT_UPDATED       -> PROVEN after safe repair
HEAD_UPDATED_RECORD_TRUNCATED          -> UNKNOWN
STALE_HEAD_AFTER_RESTART               -> PROVEN after safe repair
BROKEN_PREV_POINTER                    -> UNKNOWN
STATEMENT_REBOUND_IN_DURABLE_RECORD    -> UNKNOWN
EPOCH_REBOUND_IN_DURABLE_RECORD        -> UNKNOWN
DUPLICATE_CONFLICTING_OUTCOME_RECEIPT  -> CONFLICT
```

`UNKNOWN` is a correct result when durable evidence is insufficient to justify a stronger state.

A reconstruction that returns `PROVEN` when the oracle requires `UNKNOWN` or `CONFLICT` is a **silent false reconstruction**.

## Fault applicability

A scan-only architecture has no durable head index. Therefore:

```text
JOURNAL_WRITTEN_HEAD_NOT_UPDATED
STALE_HEAD_AFTER_RESTART
```

are marked not applicable for `software_scan_repair` rather than scored as successes or failures.

All seven corruption/anomaly cases apply to the two indexed systems.

## Fresh recovery boundary

For each system and round:

1. deterministic durable case files are written and `fsync`ed;
2. corruption/anomaly is injected into the durable representation;
3. all writer file handles are closed;
4. a fresh recovery process starts from those files only;
5. the process reconstructs state and performs any allowed scan fallback/head repair;
6. results are returned to the parent process.

TC05 is a deterministic file-corruption benchmark. It is not a physical-media fault injector or power-loss test.

## Integrity and repair policy

An indexed chain first attempts direct head-chain reconstruction.

Fallback scan is triggered by conditions such as:

```text
head points outside a complete record
durable bytes exist beyond the head
broken/cyclic/non-backward chain pointer
CRC failure
wrong statement
wrong epoch
invalid receipt identity
```

Fallback may repair the durable head to the last safely accepted record. It must not invent an outcome from invalid durable evidence.

## Metrics

Correctness first:

```text
oracle accuracy
silent false reconstruction
detected corruption
detected conflict
UNKNOWN recoveries
CONFLICT recoveries
fault applicability / coverage
```

Work/cost:

```text
records inspected
repair-scan records
repair writes
recovery latency
fresh-process wall latency
persisted bytes
```

Runtime is secondary to correctness. The workflow rotates system execution order across rounds and reports medians.

## Four-axis interpretation

### Utility

Does recovery return the correct epistemic state without inventing a successful outcome?

### Proof / trust

Can durable statement/epoch/receipt binding failures be distinguished from trustworthy evidence?

### Cost

What integrity bytes, repair scans, records inspected and writes are required?

### Speed

How quickly can a fresh process recover after corruption detection and any required repair?

No synthetic winner score combines these dimensions.

## Required negative-result discipline

The report must explicitly state if:

- conventional indexed integrity checks match ProofBit correctness;
- both systems degrade to `UNKNOWN`/`CONFLICT` identically;
- both systems require the same fallback scan/repair work;
- conventional indexed software is faster;
- any apparent speed crossover is unstable or small relative to run variance.

A tie means the benchmark supports the value of the **integrity semantics/pattern**, not a unique ProofBit performance claim.

## Claim boundary

TC05 provides Python/Linux software-reference evidence from deterministic local-file corruption on GitHub-hosted runners.

It does not establish:

- physical storage-device failure behavior;
- power-loss atomicity;
- cryptographic authenticity;
- malicious resistance beyond the frozen mutations;
- network/distributed recovery;
- processor cycles, silicon area or energy;
- novelty or patentability;
- universal performance ordering.
