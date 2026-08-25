# PB-TRANSITION-03 results

## Official common run

`PB-TRANSITION-03` was executed in ProofBit GitHub Actions run `32471857739`,
job `96740116335`.

Environment:

- Ubuntu 24.04.4 hosted runner;
- CPython 3.12.14;
- Rust 1.98.0;
- ProofBit PR merge ref built from head `f90df24f325fdb1221bf27717ecef74940598559`;
- pinned CaPU adapter `a0da246b5fa52331b81e182767ccfe5cb7b5a95e`;
- pinned MORPHOS adapter `55ee39d9c248cb3b6f4f93359740e502ae9ad41e`.

Frozen protocol:

`PB-T03/v0.1 authorization-freshness-replay-conflict-outcome`

Default workload:

- 10,000 trials;
- 9,000 `VALID`;
- 200 `UNKNOWN`;
- 200 `STALE_AUTHORITY`;
- 200 `REPLAY`;
- 200 `CONFLICT`;
- 200 `FALSE_SUCCESS`.

`FALSE_SUCCESS` requires dispatch to occur but terminal success to remain false
without outcome evidence.

## Coverage first

| System | Fault-kind coverage | Stream semantic coverage | Unsupported kinds |
| --- | ---: | ---: | --- |
| Raw software control | 100% | 100% | none |
| Software trust guard | 100% | 100% | none |
| ProofBit | 100% | 100% | none |
| CaPU P6 adapter | 20% | 92% | stale authority, replay, conflict, false success |
| MORPHOS adapter | 20% | 92% | stale authority, replay, conflict, false success |

For CaPU and MORPHOS, the 800 unsupported trials are **unassessed**. They are not
counted as correct, safe, blocked, or prevented.

## Correctness and failure behavior

| System | Assessed correct | Unsafe auth dispatches | False-success claims | Missed valid | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| Raw software control | 9,000 / 10,000 | 800 | 200 | 0 | full |
| Software trust guard | 10,000 / 10,000 | 0 | 0 | 0 | full |
| ProofBit | 10,000 / 10,000 | 0 | 0 | 0 | full |
| CaPU P6 adapter | 9,200 / 9,200 | 0 | 0 on assessed semantics | 0 | partial |
| MORPHOS adapter | 9,200 / 9,200 | 0 | 0 on assessed semantics | 0 | partial |

The raw control's 1,000 incorrect trials decompose exactly into:

- 200 unsafe `UNKNOWN` dispatches;
- 200 unsafe `STALE_AUTHORITY` dispatches;
- 200 unsafe `REPLAY` dispatches;
- 200 unsafe `CONFLICT` dispatches;
- 200 incorrect terminal-success claims for `FALSE_SUCCESS`.

## Software-reference timing

These timings are implementation-level software measurements only. They are not
processor-cycle, silicon, energy, or area results.

| System | Measured work | Throughput |
| --- | --- | ---: |
| Raw software control | full 10,000-trial stream | ~4.915M trials/s |
| Software trust guard | full 10,000-trial stream | ~1.813M trials/s |
| ProofBit Python reference | full 10,000-trial stream | ~0.362M trials/s |
| CaPU Rust P6 | **assessed 9,200 trials only** | ~7.122M assessed trials/s |
| MORPHOS Python simulator | **assessed 9,200 trials only** | ~141.3k assessed trials/s |

Because CaPU and MORPHOS execute only 92% of the stream and use different
language/runtime mechanisms, their timing is not a full-coverage speed ranking
against the software guard or ProofBit.

On the two full-coverage guarded implementations, the ordinary Python software
trust guard is approximately **5.00x faster** than the current ProofBit Python
semantic reference on this run.

## Important negative result

PB-T03 does **not** show that proof-aware semantics are necessary to implement
these five policies correctly.

A competent conventional software implementation using:

- evidence presence;
- authority id;
- epoch;
- replay set;
- conflict flag;
- separate outcome-evidence check;

achieved 10,000 / 10,000 oracle-correct outcomes with zero unsafe dispatches,
zero false-success claims, and zero missed valid actions.

That result is retained deliberately.

The narrower ProofBit hypothesis is therefore:

> proof-native semantics may be valuable when the cost/risk of repeatedly
> implementing, composing, transporting, invalidating, and auditing these trust
> checks across software boundaries becomes larger than the cost of carrying the
> evidence semantics with the state itself.

PB-T03 does not yet establish that crossover.

## Evidence categories

The benchmark does not collapse different evidence mechanisms into one score.

- **software guard** — application-maintained structured policy state;
- **ProofBit** — statement/value/authority/epoch-bound authorization evidence
  plus distinct outcome evidence;
- **CaPU** — cause plus durable commit at the executable P6 boundary;
- **MORPHOS** — deterministic A/M/C transition trace.

Equal oracle correctness does not imply equal evidence strength, auditability,
composability, portability, or revocation behavior.

## ProofBit-specific result

ProofBit executed all five frozen fault classes:

- `UNKNOWN` remained non-authoritative;
- stale epoch evidence was not accepted;
- consumed proof ids were rejected as replay;
- conflict remained first-class and did not dispatch;
- `FALSE_SUCCESS` allowed the authorization dispatch but did not promote a
  terminal outcome without separate outcome evidence.

This is executable semantic-reference evidence, not a cryptographic security or
hardware-performance claim.

## CaPU-specific result

At the exact pinned PB-T03 boundary, CaPU supports:

- `VALID`: cause + durable commit -> accept;
- `UNKNOWN`: missing cause/commit -> reject.

It produced 9,200 / 9,200 correct assessed outcomes, with zero unsafe assessed
dispatches and zero missed valid actions.

`STALE_AUTHORITY`, execution-guard `REPLAY`, `CONFLICT`, and `FALSE_SUCCESS`
remain unassessed even if related mechanisms exist elsewhere in CaPU research.
They must be wired into this exact runnable adapter before receiving benchmark
credit.

## MORPHOS-specific result

At the exact pinned PB-T03 boundary, MORPHOS supports:

- `VALID`: two above-threshold A/M/C pulses reach the requested endpoint;
- `UNKNOWN`: two sub-threshold pulses preserve the source endpoint.

It produced 9,200 / 9,200 correct assessed outcomes, 18,400 lattice steps,
18,000 phase changes, and zero unsafe assessed transitions.

The reported simulated drive magnitude is dimensionless model data, not
physical energy.

## What PB-T03 establishes

Within the deterministic software-reference boundary:

1. one richer trust oracle can be shared without forcing identical internal
   semantics;
2. full coverage and partial coverage can be compared without crediting
   unsupported behavior;
3. ordinary software can correctly implement the complete frozen policy;
4. ProofBit can also represent the complete policy while preserving distinct
   authorization and outcome evidence;
5. current CaPU and MORPHOS PB-T03 adapters expose useful but partial executable
   semantic coverage;
6. speed must be interpreted after semantic coverage, not before it.

## Next experiment

The next useful benchmark should measure the **composition and maintenance
crossover**, not merely add more fault labels.

Candidate `PB-TRUST-COMPOSE-01`:

- multiple independent application components;
- evidence copied across boundaries;
- authority/epoch changes after caching;
- retries and duplicated messages;
- multiple derived decisions;
- dispatch and outcome separated by transport;
- one implementation using conventional software policy plumbing;
- one using proof-native state/evidence propagation.

Measure:

- oracle failures;
- policy code/metadata duplication;
- invalidation operations;
- evidence-loss/rebinding opportunities;
- runtime and memory cost;
- audit reconstruction work.

The hypothesis becomes falsifiable: if ordinary structured software stays
simpler, equally correct, and cheaper as the number of boundaries and trust
rules grows, ProofBit has not earned its added machinery.
