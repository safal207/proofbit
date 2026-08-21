# PB-TRUST-COMPOSE-04 Methodology

## Question

Can proof-native receipt semantics reduce the cost or ambiguity of reconstructing what happened after a real process crash, restart, retry and delayed outcome delivery — relative to competent conventional durable logging?

The experiment is intentionally falsifiable. A conventional implementation that reconstructs the same knowledge state with equal or less work is a valid negative ProofBit result.

## Frozen terminal knowledge states

Every transaction must reconstruct to exactly one of:

```text
NOT_AUTHORIZED
AUTHORIZED_NOT_EXECUTED
EXECUTED_OUTCOME_UNKNOWN
EXECUTED_OUTCOME_PROVEN
CONFLICT
```

The benchmark does not silently map `unknown` to `false`, and it does not treat dispatch/execution as terminal outcome proof.

## Real crash boundary

For each system and round:

1. a fresh writer process appends its pre-crash durable records;
2. journal/index files are explicitly `fsync`ed;
3. the writer terminates with `os._exit(97)`;
4. the parent verifies exit code `97` — graceful shutdown is not accepted as crash evidence;
5. a new process starts from persistent files only;
6. retry/duplicate delivery and late/conflicting outcome receipts are applied;
7. the new process reconstructs and audits the final durable state.

This is a real process death and fresh-process restart. It is **not** a machine power failure or storage-device fault.

## Frozen workload

The official run uses 500 transactions per round and five independent rounds. Transaction IDs deterministically rotate through the five terminal knowledge states, so each state has equal representation.

For `EXECUTED_OUTCOME_PROVEN`, half of outcome receipts are durable before the crash and half arrive after restart. `CONFLICT` receives one outcome before the crash and a contradictory outcome after restart.

For every transaction that had already executed, a retry is delivered after restart. A second side effect is always an error.

## Compared systems

### `software_scan`

A competent conventional append-only durable event log with no durable per-transaction index.

It is included to measure the reconstruction and targeted-audit cost of an unindexed log. It is **not** the primary ProofBit competitor.

### `software_indexed`

The primary anti-strawman conventional control:

- append-only fixed-width durable event log;
- per-transaction durable head index;
- linked previous-record offsets;
- same record width and index topology as the ProofBit implementation.

If this control matches or beats ProofBit, the result must be reported as such.

### `proofbit_receipts`

ProofBit semantic reference:

- append-only fixed-width typed receipt records;
- per-transaction durable head index;
- linked previous-receipt offsets;
- reconstruction validates statement binding, epoch and non-zero proof/receipt identity before accepting the chain.

The records are semantic proof references, not cryptographic proofs.

## Representation fairness

All systems use the exact same durable record width:

```text
48 bytes / journal record
```

`software_indexed` and `proofbit_receipts` also use the exact same:

```text
8 bytes / transaction durable head index
```

Therefore a storage or audit difference between those two systems cannot be attributed to giving ProofBit a smaller record format or a private index.

## Oracle

After restart and all frozen post-crash events:

- `NOT_AUTHORIZED`: no durable authorization;
- `AUTHORIZED_NOT_EXECUTED`: authorization exists, execution does not;
- `EXECUTED_OUTCOME_UNKNOWN`: execution exists, no outcome evidence exists;
- `EXECUTED_OUTCOME_PROVEN`: execution and exactly one non-conflicting outcome exist;
- `CONFLICT`: contradictory outcome evidence exists.

Retries after an already durable execution must not create another execution record/side effect.

## Metrics

Correctness is evaluated before runtime/cost:

```text
recovery oracle accuracy
duplicate side effects after retry
false terminal success
ambiguous terminal states
hard-crash exit code
```

Recovery/audit cost:

```text
restart wall latency
reconstruction latency
trusted recovered states / second
persisted journal bytes
persisted index bytes
total persisted bytes
full-recovery records inspected
targeted-audit records inspected
authority re-establishment messages
```

The official report uses medians over independent rounds for runtime and work-size metrics. Raw throughput values are retained.

## Targeted audit

A targeted audit asks for the histories of a small fixed sample of transactions after recovery.

- `software_scan` has no durable head and must search the log for each independent target;
- `software_indexed` follows its per-transaction head chain;
- `proofbit_receipts` follows its per-transaction receipt head chain.

The indexed conventional system is therefore expected to remove any advantage that comes only from indexing.

## Four-axis interpretation

### Utility

Can the system recover the correct post-crash knowledge state and avoid duplicate side effects?

### Proof / trust

What evidence/receipt semantics are preserved during reconstruction, and can the system distinguish execution from proven outcome?

### Cost

How many bytes are durable, how many records are inspected, and how much recovery work is required?

### Speed

How quickly does a fresh process reconstruct trusted terminal states after the crash?

No synthetic winner score combines these axes.

## Required negative-result discipline

The benchmark must explicitly report the following if observed:

- indexed conventional software matches ProofBit correctness;
- indexed conventional software uses the same or fewer persisted bytes;
- indexed conventional software inspects the same or fewer records;
- indexed conventional software recovers faster;
- any apparent crossover fails repeated measurement.

## Claim boundary

PB-TC04 is Python/Linux software-reference evidence from local files on a GitHub-hosted runner.

It does not measure or establish:

- machine/power-loss durability;
- storage-device atomicity beyond the exercised `fsync` process fixture;
- distributed-network partitions;
- cryptographic proof verification;
- processor cycles;
- silicon area or energy;
- novelty or patentability;
- universal performance ordering.
