# PB-TRANSITION-01 — MORPHOS result

Status: **EXECUTED / CROSS-REPOSITORY ADAPTER**

This benchmark records transition/recovery behavior without pretending that MORPHOS lattice dynamics are equivalent to ProofBit guard decisions or accelerator FLOPS.

## Pinned provenance

- MORPHOS repository: `safal207/COSMIC-ORGANICS`
- adapter commit: `5ff088d647e315893a38a082ed27af07669177a1`
- adapter PR: `safal207/COSMIC-ORGANICS#55`
- first adapter CI run: `32468585556`
- runner: Ubuntu 24.04, CPython 3.12.14
- W8.5 development head: `be557b50810391f97b6d943196e0e47e5d67676c`
- frozen mechanism blob: `2594268e8ab5bdbfec284beb76c13a01c0548667`
- frozen mechanism blob match: `true`

## Frozen transition contract

```text
one verified source
+ exactly two M transition cells
+ unique GF(2) committed-parity solution
+ full virtual parity replay
-> early ownership
```

## Executed result

| Axis | Result |
| --- | ---: |
| observed batches | 1 |
| observed corpora | 18 |
| observed fresh trials | 864 |
| predecessor W8.4 failures | 2 |
| causal W8.5 rescues | 2 / 2 |
| minimum exact recovery @ tick 8 | 100% |
| minimum exact recovery @ tick 12 | 100% |
| previous successes regressed | 0 |
| multi-erasure decode events | 8 |
| multi-erasure-added targets | 16 |
| minimum corrupted-witness causal drop | 87.5 percentage points |
| complete protocol wall time | 34.527 s |
| complete protocol trials/sec | 25.024 |

The `25.024 trials/sec` number is Python simulator throughput for the full frozen continuation and control evaluation. It is **not** a silicon-performance claim and must not be compared numerically with PB-ARCH-01 decisions/sec.

## Architecture capability map

| Architecture | PB-TRANSITION-01 status | Meaning |
| --- | --- | --- |
| conventional CPU | `HOST_ONLY` | executes the simulator; no native transition semantics credited |
| ProofBit v0.1 | `NOT_RUN_ADAPTER_NEEDED` | justified-state/guard model has not executed this frozen A/M/C workload |
| CaPU | `NOT_RUN_ADAPTER_NEEDED` | causal-legitimacy model has not executed this frozen A/M/C workload |
| MORPHOS W8.5 | `EXECUTED` | native frozen transition/recovery protocol executed |

## Comparison rule

The benchmark suite ranks only within a common workload boundary:

```text
same workload
-> semantic coverage
-> safety / utility
-> speed / cost
```

Across different benchmark families we report capability and evidence, not a fake universal speed winner.

## Next experiment

Create a smaller architecture-neutral transition task that can be implemented by ProofBit, CaPU, and MORPHOS without deleting their native semantics. That common task should report:

- successful legitimate transitions;
- rejected or unrecoverable transitions;
- evidence/authority used to justify the transition;
- recovery latency;
- state and metadata bytes;
- operations or simulator steps;
- wall-clock throughput;
- false acceptance / false rejection.

Only after all three adapters execute the same frozen task should raw transition throughput be ranked.
