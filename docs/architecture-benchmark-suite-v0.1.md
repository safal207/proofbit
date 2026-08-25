# Architecture Benchmark Suite v0.1

The benchmark suite compares architectures by **executed benchmark family**, not by a universal synthetic score.

## Current league table

| Architecture | PB-ARCH-01 | PB-TRANSITION-01 | Current demonstrated strength |
| --- | --- | --- | --- |
| conventional value-only CPU reference | `EXECUTED_FULL` | `HOST_ONLY` | raw decision throughput / ordinary value execution |
| ProofBit ProofProcessor | `EXECUTED_FULL` | `ADAPTER_NEEDED` | explicit proof/fault semantics across all five frozen PB-ARCH-01 fault kinds |
| CaPU P6 software reference | `EXECUTED_PARTIAL` | `ADAPTER_NEEDED` | high-speed commit-before-effect boundary on currently wired semantics |
| COSMIC ORGANICS / MORPHOS W8.5 | `NOT_RUN` | `EXECUTED` | causal transition/recovery on frozen A/M/C lattice semantics |

## Executed evidence

### PB-ARCH-01

Frozen workload: 10,000 decisions, 10% contamination, five fault kinds:

`UNKNOWN / STALE / REPLAY / CONFLICT / FALSE_SUCCESS`

First cross-repository run:

- value-only reference: ~4.17M decisions/s, 0/5 fault-kind coverage, 1,000 unsafe actions;
- ProofBit: ~0.434M decisions/s, 5/5 fault-kind coverage, 0 unsafe actions;
- CaPU P6: ~4.17M supported decisions/s, 1/5 fault-kind coverage, 0 unsafe actions on supported semantics, 800 decisions unassessed.

Raw speed is not ranked between ProofBit and CaPU without accounting for the different semantic coverage.

### PB-TRANSITION-01

Frozen MORPHOS native transition/recovery workload:

`verified source + exactly two M cells + unique GF(2) committed-parity solution + full virtual parity replay -> early ownership`

First adapter run:

- 864 fresh trials;
- 2 predecessor failures;
- 2/2 causal rescues;
- 100% exact recovery at ticks 8 and 12;
- 0 previous-success regressions;
- ~34.527 s complete protocol wall time;
- ~25.024 trials/s on CPython 3.12 / Ubuntu GitHub Actions;
- frozen mechanism blob matched exactly.

The MORPHOS speed is native-workload simulator throughput and is not numerically comparable with PB-ARCH-01 decisions/sec.

## Four axes

Every benchmark family reports the same high-level axes while preserving workload-specific units:

1. **Utility** — useful work, recovery, failures prevented.
2. **Proof** — provenance, authority, causal evidence, freshness, outcome or transition justification.
3. **Cost** — compute, memory, simulator steps/cycles, energy/area when available.
4. **Speed** — latency, throughput and time-to-result for the same frozen workload.

## Ranking rule

```text
same frozen workload
    -> semantic coverage
    -> false acceptance / false rejection
    -> utility
    -> speed / cost
```

Cross-family comparison is a **capability map**, not a raw-speed ranking.

## Next common benchmark

`PB-TRANSITION-02` should be an architecture-neutral state-transition task with adapters for ProofBit, CaPU and MORPHOS.

The task should freeze:

- initial state;
- requested transition;
- admissibility/constraint data;
- stale, replayed, conflicting and incomplete evidence variants;
- optional perturbation/recovery path;
- exact terminal state;
- evidence required to claim completion.

Every adapter must emit:

- allowed/rejected/recovered result;
- terminal correctness;
- false accepts;
- false rejects;
- evidence/authority consumed;
- transition/recovery latency;
- metadata/state bytes;
- operations, steps or cycles;
- wall-clock throughput.

That is the first benchmark where ProofBit, CaPU and MORPHOS can be ranked directly on one state-transition problem without deleting what makes each architecture different.
