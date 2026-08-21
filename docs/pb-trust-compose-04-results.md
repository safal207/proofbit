# PB-TRUST-COMPOSE-04 Results

## Verdict

`PB-TRUST-COMPOSE-04` does **not** demonstrate a ProofBit-specific correctness, storage, audit-work, or recovery-speed advantage over a competent conventional indexed durable log.

It does demonstrate two narrower results:

1. all three systems can reconstruct the frozen post-crash knowledge states correctly after a real hard process death and fresh-process restart;
2. a durable per-transaction head index reduces targeted audit work dramatically relative to an unindexed append-only log, but that benefit is reproduced exactly by conventional indexed software and therefore is not uniquely ProofBit.

The strongest anti-strawman comparison remains:

```text
software_indexed vs proofbit_receipts
```

They use the same 48-byte journal record width, the same 8-byte per-transaction durable head-index topology, the same number of durable records, and the same frozen recovery oracle.

## Reproducible environment

Official stability evidence:

- repository: `safal207/proofbit`
- branch: `feat/pb-trust-compose-04`
- workflow: `pb-trust-compose-04`
- run: `32475679143`
- job: `96751385441`
- measured benchmark head: `ada39cfa1cd95e80f849fbb9510f8f8b64ce3681`
- OS: Ubuntu 24.04.4
- Python: CPython 3.12.14

The job completed successfully, including:

- crash-recovery unit tests;
- five-round full TC04 run;
- frozen recovery-oracle assertions;
- **11-round rotated-order stability run**;
- stability anti-strawman assertions.

## Frozen workload

Each round contains 500 transactions, evenly divided across:

| Terminal knowledge state | Transactions |
| --- | ---: |
| `NOT_AUTHORIZED` | 100 |
| `AUTHORIZED_NOT_EXECUTED` | 100 |
| `EXECUTED_OUTCOME_UNKNOWN` | 100 |
| `EXECUTED_OUTCOME_PROVEN` | 100 |
| `CONFLICT` | 100 |

For `EXECUTED_OUTCOME_PROVEN`, half of outcome evidence is durable before the crash and half arrives after restart.

For `CONFLICT`, one outcome is durable before the crash and a contradictory outcome arrives after restart.

Every transaction that had already executed receives a retry after restart. A duplicate side effect is always an error.

## Real crash evidence

For every system and every stability round:

```text
pre-crash process -> fsync -> os._exit(97)
```

The parent verifies the crash exit code before starting a fresh recovery process.

Across 11 stability rounds, every system produced:

```text
[97, 97, 97, 97, 97, 97, 97, 97, 97, 97, 97]
```

This is real process death, not a graceful shutdown. It is not a machine/power-loss durability test.

## Correctness

Across `software_scan`, `software_indexed`, and `proofbit_receipts`:

- **100% recovery oracle accuracy**;
- **0 duplicate side effects after retry**;
- **0 false terminal success**;
- **0 ambiguous terminal states**.

Therefore TC04 shows **no ProofBit-specific correctness advantage** over the strong conventional controls.

## Stability methodology

The first five-round run briefly produced a noisy apparent ProofBit recovery-throughput advantage. It was not accepted as a claim.

The stability run performs 11 independent one-round fixtures and rotates system execution order across all three permutations:

```text
scan -> indexed -> proof
indexed -> proof -> scan
proof -> scan -> indexed
```

This removes the fixed-order bias from the exploratory run.

## Official 11-round stability result

| System | Median recovered states/s | Median recovery latency | Median restart wall | Persisted bytes | Targeted audit records |
| --- | ---: | ---: | ---: | ---: | ---: |
| `software_scan` | **39,375.4/s** | 12.698 ms | 93.811 ms | **86,400 B** | **45,000** |
| `software_indexed` | **26,523.1/s** | **18.852 ms** | **21.591 ms** | 90,400 B | **90** |
| `proofbit_receipts` | 25,940.7/s | 19.275 ms | 21.974 ms | 90,400 B | **90** |

Primary strong-control ratios:

```text
ProofBit / indexed recovery throughput = 0.9780x
ProofBit / indexed persisted bytes      = 1.0000x
ProofBit / indexed targeted audit work  = 1.0000x
```

The current ProofBit Python semantic reconstruction is therefore about **2.2% slower by median recovery throughput** than the strong conventional indexed implementation in this stability run.

The difference is small enough that no universal performance ordering is claimed.

## Targeted audit result

The unindexed log inspected:

```text
45,000 records
```

for the frozen 25-transaction targeted audit sample.

Both indexed systems inspected:

```text
90 records
```

That is a **500x reduction in records inspected** relative to the unindexed scan.

However:

```text
software_indexed = 90
proofbit_receipts = 90
```

So the evidence supports:

> A durable per-transaction head/chain index is extremely valuable for targeted audit reconstruction in this workload.

It does **not** support:

> ProofBit uniquely provides that audit advantage.

## Persisted storage

The unindexed software log persists:

```text
86,400 bytes
```

The two indexed designs persist:

```text
86,400 B journal + 4,000 B head index = 90,400 B
```

The index therefore costs 4,000 bytes for 500 transactions, about **4.63%** over the journal-only representation in this workload.

`software_indexed` and `proofbit_receipts` have exactly the same persisted footprint.

## Full recovery work

All systems inspect a median of:

```text
3,150 records
```

across the two full reconstruction passes in the fixture.

So the per-transaction chain does **not** reduce complete-recovery record work in this frozen workload; its measured work benefit appears in targeted audit queries.

## Four-axis interpretation

### Utility

All systems reconstruct every terminal knowledge state correctly and prevent retry duplication.

**Result: tie.**

### Proof / trust semantics

ProofBit validates statement binding, epoch and non-zero receipt identity while traversing its chain. The conventional indexed control reaches the same frozen external recovery oracle without those semantics being native to its record type.

**Result: richer native semantics are represented, but no externally observable correctness advantage is demonstrated by this workload.**

### Cost

Indexed conventional software and ProofBit use the same 90,400-byte durable representation and inspect the same number of targeted-audit records.

**Result: tie between the strong controls.**

The unindexed log is 4,000 bytes smaller but pays 500x more record inspections for the targeted audit sample.

### Speed

The rotated 11-round stability run leaves conventional indexed software slightly ahead of the current ProofBit Python reference.

**Result: no ProofBit speed win.**

## What TC04 falsified

TC04 falsifies several tempting narratives:

1. **"ProofBit is required to reconstruct execution/outcome state after a crash."**
   Not shown. Competent conventional durable logs also reconstruct all five states correctly.

2. **"Receipt chains automatically reduce audit work."**
   Too broad. A conventional indexed event chain gets the same 500x targeted-audit work reduction.

3. **"The first +6% recovery-throughput result proves a crossover."**
   Falsified. After rotating execution order and using 11 rounds, the ratio becomes `0.978x`.

4. **"More persisted metadata necessarily improves full recovery speed."**
   Not shown. Full recovery record work is equal in this fixture.

## Current evidence-supported conclusion

The evidence supports the following narrow statement:

> ProofBit can carry explicit statement/epoch/receipt semantics through a crash/restart recovery chain while matching the storage and audit-work profile of a strong conventional indexed durable log. In the stable software-reference measurement, the conventional indexed control remains slightly faster, and the large targeted-audit improvement belongs to the shared indexed-chain topology rather than uniquely to ProofBit.

## Next falsifiable experiment: PB-TRUST-COMPOSE-05

The next useful experiment should target **partial durable corruption / torn metadata**, not another clean-crash throughput run.

Proposed fault matrix:

```text
JOURNAL_WRITTEN_HEAD_NOT_UPDATED
HEAD_UPDATED_RECORD_TRUNCATED
STALE_HEAD_AFTER_RESTART
BROKEN_PREV_POINTER
STATEMENT_REBOUND_IN_DURABLE_RECORD
EPOCH_REBOUND_IN_DURABLE_RECORD
DUPLICATE_OUTCOME_RECEIPT
```

The question becomes:

> When durable metadata itself is incomplete, contradictory, or incorrectly rebound, can the system detect that it does not know the truth rather than reconstructing a confident but false terminal state?

Compare:

- conventional scan log with repair;
- conventional indexed log with scan fallback and integrity checks;
- ProofBit receipt chain with explicit binding/integrity semantics.

Measure:

- silent false reconstruction;
- detected corruption;
- recovery-to-`UNKNOWN`/`CONFLICT` rate;
- repair records scanned;
- repair writes;
- recovery latency;
- storage overhead required for integrity metadata.

A conventional implementation with equivalent integrity checks remains a required anti-strawman control.

## Claim boundary

These results are Python/Linux software-reference evidence from local files on a GitHub-hosted runner.

They are not evidence of:

- power-loss or storage-device atomicity;
- distributed-network behavior;
- cryptographic proof verification;
- processor-cycle performance;
- silicon area or energy;
- novelty or patentability;
- universal recovery-speed ordering.
