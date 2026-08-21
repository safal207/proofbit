# PB-TRANSITION-03 methodology

## Purpose

`PB-TRANSITION-03` extends the common transition benchmark from a single
sufficient/insufficient-support bit to five distinct trust failure classes:

- `UNKNOWN`
- `STALE_AUTHORITY`
- `REPLAY`
- `CONFLICT`
- `FALSE_SUCCESS`

The benchmark is designed to answer a narrower question than “which
architecture is fastest?”:

> On the same deterministic transition stream, which trust semantics are
> executable, which are correct when executable, what evidence category is
> carried, and what software cost is observed?

## Frozen protocol

`PB-T03/v0.1 authorization-freshness-replay-conflict-outcome`

Default run:

- 10,000 trials;
- 90% `VALID`;
- 10% adversarial;
- adversarial trials distributed equally and deterministically across the five
  fault classes;
- alternating binary transition direction (`0 -> 1`, `1 -> 0`).

No random number generator is used.

## Oracle

| Kind | Dispatch expected | Terminal success expected |
| --- | ---: | ---: |
| `VALID` | yes | yes |
| `UNKNOWN` | no | no |
| `STALE_AUTHORITY` | no | no |
| `REPLAY` | no | no |
| `CONFLICT` | no | no |
| `FALSE_SUCCESS` | **yes** | **no** |

The `FALSE_SUCCESS` row is essential. It prevents an implementation from
“solving” outcome grounding by simply refusing to dispatch. Authorization and
outcome are separate boundaries.

## Anti-strawman conventional software control

The guarded CPU control receives structured metadata rather than the benchmark
label itself:

- evidence present/missing;
- authority id;
- epoch;
- proof/grant id;
- conflict flag;
- outcome evidence present/missing.

It implements ordinary application-level checks with a replay set and a
separate outcome check. This is deliberately strong. Proof-native mechanisms
must earn their additional complexity against competent software enforcement,
not against an intentionally naïve baseline.

Correct software enforcement is not counted as native proof coverage.

## ProofBit mapping

- `VALID`: fresh statement/value/authority/epoch-bound authorization evidence;
- `UNKNOWN`: no authorization evidence;
- `STALE_AUTHORITY`: evidence from an older epoch;
- `REPLAY`: already-consumed proof id;
- `CONFLICT`: first-class conflict state;
- `FALSE_SUCCESS`: valid authorization allows dispatch, but a claimed outcome
  without outcome evidence remains `UNKNOWN` and cannot become terminal success.

The benchmark therefore keeps authorization evidence and outcome evidence
separate.

## External architecture adapters

An external adapter may report `executed_partial`.

Unsupported semantics are **unassessed**. They are never counted as prevented,
correct, or safe.

Every partial adapter reports both:

- `failure_kind_coverage`: fraction of the five adversarial kinds with an
  executable native mapping;
- `stream_semantic_coverage`: fraction of the full default stream that is
  actually assessed, including `VALID`.

Example: a system supporting `VALID + UNKNOWN` has:

- failure-kind coverage = `1/5 = 20%`;
- stream coverage at 10% contamination = `90% + 2% = 92%`.

## CaPU v0.1 adapter boundary

The current PB-T03 CaPU adapter credits only the executable P6 mappings:

- `VALID`: cause + durable commit -> accept;
- `UNKNOWN`: missing cause/commit -> reject.

`STALE_AUTHORITY`, execution-guard `REPLAY`, `CONFLICT`, and `FALSE_SUCCESS`
remain `UNSUPPORTED` in this exact adapter. Related behavior elsewhere in the
repository is not imported by assertion; it must be wired into this runnable
boundary before it can receive benchmark credit.

## MORPHOS v0.1 adapter boundary

The current PB-T03 MORPHOS adapter credits only the executable A/M/C mapping:

- `VALID`: two above-threshold pulses produce the requested endpoint transition;
- `UNKNOWN`: two sub-threshold pulses preserve the source endpoint.

Authority freshness, replay, logical conflict, and outcome grounding have no
current native mapping in the single-cell simulator and remain `UNSUPPORTED`.

A deterministic phase trace is transition evidence. It is not treated as
numerically equivalent to ProofBit authority evidence or CaPU cause+commit.

## Comparison order

Always compare in this order:

1. semantic coverage;
2. oracle correctness on assessed semantics;
3. unsafe authorization dispatches and false-success claims;
4. evidence category and boundary strength;
5. software speed/cost inside the measured implementation boundary.

Do **not** create one synthetic winner score.

## Metrics

Full-coverage implementations report:

- oracle accuracy over the full stream;
- unsafe authorization dispatches;
- false-success claims;
- missed valid dispatches;
- failure-kind coverage;
- stream semantic coverage;
- per-kind outcomes;
- elapsed time / trials per second;
- evidence category.

Partial implementations report:

- assessed and unassessed trials;
- oracle accuracy on assessed trials only;
- failure-kind and stream coverage;
- unsupported fault kinds explicitly;
- measured speed over assessed work;
- evidence category.

## Scientific boundaries

PB-T03 is a deterministic software research benchmark.

It does not establish:

- silicon performance;
- hardware energy or area;
- physical-material behavior;
- cryptographic security;
- universal architecture superiority;
- equivalence between different evidence ontologies;
- real-world frequencies of the five fault classes.

Negative results, partial coverage, and ordinary-software wins must be retained.
