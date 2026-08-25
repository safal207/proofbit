# PB-TRUST-COMPOSE-03 Results

## Verdict

`PB-TRUST-COMPOSE-03` does **not** demonstrate a ProofBit-specific correctness or runtime advantage over a competent conventional lazy trust design.

It does demonstrate a narrower architectural result:

> Centralizing authoritative revalidation at the dispatch seam avoids replicated invalidation work while preserving the frozen dynamic-trust oracle. The current ProofBit Python reference and a strong conventional lazy implementation have identical transport/control topology and correctness, while conventional lazy software remains slightly faster in the focused repeated runtime test.

This is a useful negative result. It separates the benefit of the **lazy authoritative-boundary pattern** from any claim that the benefit is uniquely ProofBit.

## Reproducible environment

Official GitHub Actions evidence:

- repository: `safal207/proofbit`
- branch: `feat/pb-trust-compose-03`
- workflow: `pb-trust-compose-03`
- run: `32474660658`
- job: `96748411273`
- benchmark head: `b585bee645f937824c9219f7f52f517ae3f6997e`
- OS: Ubuntu 24.04.4
- Python: CPython 3.12.14

The job completed successfully, including the frozen oracle checks and the focused depth-8 stability run.

## Frozen workload

Each full round contains 2,000 trials with 15% deterministic contamination:

| Kind | Trials |
| --- | ---: |
| VALID | 1,700 |
| IN_FLIGHT_REVOKE | 60 |
| REPLAY | 60 |
| REBIND_STATEMENT | 60 |
| PROVENANCE_DROP | 60 |
| FALSE_SUCCESS | 60 |

Compared systems:

- `software_eager` — replicated epoch cache at every worker; revocation fans out to every boundary and every boundary performs an epoch check;
- `software_lazy` — conventional software with authoritative revalidation only at the final dispatch seam;
- `proofbit_lazy` — the same lazy topology and compact records, with the final decision evaluated through `ProofProcessor`.

## Correctness

Across every tested depth and every repeated round, all three systems achieved:

- **100% oracle accuracy**;
- **0 unsafe authorization dispatches**;
- **0 false-success claims**;
- **0 missed valid dispatches**;
- **0 accepted replay duplicates**.

Therefore this workload shows **no correctness advantage** for ProofBit over a competent conventional implementation.

The result is stronger because `IN_FLIGHT_REVOKE` is synchronized after stage 0 has already received the old-epoch authorization frame. The authority change therefore occurs while the request is genuinely inside the process pipeline.

## Five-round full-depth runtime result

Median end-to-end throughput from the latest full run:

| IPC boundaries | software_eager | software_lazy | proofbit_lazy | PB / eager | PB / lazy |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 9,509.5/s | **11,007.3/s** | 9,938.4/s | 1.045x | **0.903x** |
| 2 | **6,572.3/s** | 6,490.1/s | 6,295.8/s | 0.958x | **0.970x** |
| 4 | 3,826.8/s | **3,870.9/s** | 3,702.9/s | 0.968x | **0.957x** |
| 8 | 2,016.9/s | **2,046.7/s** | 2,006.2/s | 0.995x | **0.980x** |

The one-process result is visibly noisy and should not be used as a crossover claim. More importantly, the earlier independent TC03 run produced `PB / software_lazy = 1.012x` at depth 8, while this repeated run produced `0.980x`. That sign change motivated the focused stability measurement below.

## Focused depth-8 stability result

The workflow reran only depth 8 for **11 independent full rounds**.

| System | Median trials/s | Min | Max |
| --- | ---: | ---: | ---: |
| software_eager | 2,021.1 | 1,896.9 | 2,075.7 |
| software_lazy | **2,055.8** | 2,007.5 | 2,130.1 |
| proofbit_lazy | 2,010.2 | 1,989.0 | 2,038.3 |

Stable median ratios:

```text
ProofBit / software_eager = 0.9946x
ProofBit / software_lazy  = 0.9778x
software_lazy / eager     = 1.0171x
```

The earlier `~1.012x` ProofBit/lazy crossover therefore **did not survive stability testing**.

The strongest current runtime statement is:

> At eight real local IPC boundaries, the current ProofBit Python reference is approximately 2.2% slower by median throughput than the strong conventional lazy control in the focused 11-round test.

That difference is small enough that this benchmark should not be used to claim a universal performance ordering outside the measured environment.

## Dynamic trust maintenance work

The more stable architectural difference appears in invalidation work rather than wall-clock throughput.

There are 60 in-flight authority revocations per round.

| Boundaries | eager control msgs | lazy/PB control msgs | eager epoch checks | lazy/PB intermediate epoch checks | eager control bytes | lazy/PB control bytes |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 60 | 60 | 2,060 | 0 | 300 | 300 |
| 2 | 120 | 60 | 4,120 | 0 | 600 | 300 |
| 4 | 240 | 60 | 8,240 | 0 | 1,200 | 300 |
| 8 | **480** | **60** | **16,480** | **0** | **2,400** | **300** |

At depth 8, eager replicated invalidation therefore performs:

- **8x the control messages** of either lazy design;
- **8x the control-update applications**;
- **16,480 extra intermediate epoch checks**;
- 2,100 additional application-payload control bytes for the same 60 revocations.

However, that work does **not** translate into a proportional wall-clock penalty in this Python/IPC workload. The data plane carries roughly 1 MB of application payload at depth 8, and process scheduling plus IPC dominate enough that the maintenance savings are mostly hidden in end-to-end runtime.

This distinction matters: lower trust-maintenance work is measured, but a material runtime win is not.

## Identical lazy transport/control cost

`software_lazy` and `proofbit_lazy` deliberately use the same compact record formats and the same one-gate control topology.

At depth 8 per round, both carry:

- total request IPC application payload: **1,001,600 bytes**;
- control payload: **300 bytes**;
- total IPC application payload: **1,009,540 bytes**;
- control messages: **60**;
- full authorization validations: **2,060**;
- outcome validations: **1,760**.

This prevents transport representation or invalidation fanout from being credited as a ProofBit-specific benefit.

## Four-axis interpretation

### Utility

All three systems deliver the same frozen useful behavior: valid actions execute and every tested dynamic fault is handled correctly.

**Result: tie.**

### Proof / trust semantics

ProofBit represents the trust state through its proof-aware reference model, but the strong conventional lazy control reproduces the same externally observed oracle on this workload.

**Result: no unique ProofBit advantage demonstrated.**

### Cost

Eager replicated trust caches incur substantially more invalidation messages and intermediate epoch checks as component count grows. Both lazy designs avoid that fanout.

**Result: lazy authoritative-boundary architecture wins over eager replication; this is not uniquely a ProofBit result.**

### Speed

Focused depth-8 repeated measurement leaves conventional lazy software slightly ahead of the current ProofBit Python reference.

**Result: no stable ProofBit speed crossover.**

## What TC03 falsified

TC03 falsifies several tempting but unsupported narratives:

1. **"ProofBit is needed to survive in-flight revocation."**
   Not shown. Strong conventional lazy software also achieves 100% oracle accuracy.

2. **"Proof-native transport automatically makes dynamic trust faster."**
   Not shown. The strongest conventional lazy control is slightly faster in the focused repeated run.

3. **"Replicating trust checks everywhere is necessary for correctness."**
   Falsified for this frozen workload. Authoritative revalidation at the final dispatch seam preserves correctness with much less invalidation work.

4. **"A one-run crossover is enough."**
   Falsified empirically. The earlier depth-8 `~1.012x` ProofBit/lazy result reversed under repeated measurement.

## Current evidence-supported conclusion

The evidence currently supports the following narrow statement:

> ProofBit can express the same dynamic authority, replay, statement-binding, provenance, and outcome-grounding rules as a strong conventional lazy trust boundary while remaining close to its runtime throughput. The measured reduction in distributed invalidation work belongs to the lazy authoritative-boundary architecture, not yet uniquely to ProofBit.

That is a stronger research position than claiming a premature win.

## Next falsifiable experiment: PB-TRUST-COMPOSE-04

The next experiment should move away from another steady-state throughput comparison and test **crash/recovery plus audit reconstruction**.

Proposed fixture:

1. authorization is issued and enters a multi-process pipeline;
2. an intermediate process forwards some evidence and then crashes;
3. execution may or may not have happened before the crash;
4. the process restarts with partial local state;
5. a retry or duplicate authorization arrives;
6. outcome evidence may arrive before or after restart;
7. the system must reconstruct exactly one of:
   - `NOT_AUTHORIZED`
   - `AUTHORIZED_NOT_EXECUTED`
   - `EXECUTED_OUTCOME_UNKNOWN`
   - `EXECUTED_OUTCOME_PROVEN`
   - `CONFLICT`

Compare a competent conventional event/receipt log against a proof-native receipt chain.

Measure:

- recovery oracle accuracy;
- duplicate side effects after retry;
- false terminal success;
- ambiguous terminal states;
- persisted bytes;
- records inspected during reconstruction;
- restart/recovery latency;
- messages required to re-establish authority;
- trusted recovered outcomes per second.

If the conventional control reconstructs the same state with equal or less work, that should again be recorded as a negative ProofBit result.

## Claim boundary

These measurements are software reference evidence from Python processes on a GitHub-hosted runner.

They are not evidence of:

- processor-cycle performance;
- silicon area or energy;
- network performance;
- cryptographic verifier cost;
- universal crossover behavior;
- novelty or patentability.
