# PB-TRUST-COMPOSE-01 results

Protocol: `PB-TC01/v0.1 composed-trust-propagation`

Official run: GitHub Actions `32472674141`, job `96742559859`.

Environment:

- Ubuntu 24.04.4
- CPython 3.12.14
- 10,000 trials
- 12% contamination
- boundaries: `1, 2, 4, 8, 16, 32`

## Correctness

All three competent implementations satisfied the frozen oracle at every boundary depth:

- 10,000 / 10,000 oracle-correct
- 0 unsafe authorization dispatches
- 0 false-success claims
- 0 missed valid dispatches
- 200 / 200 correct for each fault class: `UNKNOWN`, `STALE_AUTHORITY`, `REPLAY`, `CONFLICT`, `REBIND_STATEMENT`, `FALSE_SUCCESS`

This is important: PB-TC01 does **not** show that conventional software cannot implement the trust policy correctly.

## RED -> GREEN preflight

Before the benchmark, CI run `32472400101` exposed a missing executable statement-binding boundary: the two new tests failed because `ProofProcessor.guarded_execute()` had no `expected_statement` binding.

Minimal fix `6e92208ced1c446934efc4a4dcec042a2ecce795` added optional expected-statement validation before proof consumption. The regression then passed.

The composition benchmark therefore includes one concrete semantic hardening discovered by the experiment: a valid proof for action A cannot silently authorize action B.

## Throughput scale

Measured CPython trials per second:

| Boundaries | Software shared | Software serialized | ProofBit | ProofBit / serialized | ProofBit / shared |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 321,596 | 198,864 | 232,014 | 1.17x | 0.72x |
| 2 | 331,096 | 141,123 | 236,655 | 1.68x | 0.71x |
| 4 | 327,139 | 88,161 | 230,047 | 2.61x | 0.70x |
| 8 | 307,551 | 51,713 | 225,151 | 4.35x | 0.73x |
| 16 | 287,539 | 28,130 | 213,514 | 7.59x | 0.74x |
| 32 | 248,090 | 14,608 | 191,608 | 13.12x | 0.77x |

The measured Python crossover against the explicit serialization-style implementation occurs at the first tested boundary (`1`). That is a property of this reference implementation, not a universal architecture threshold.

The strongest conventional control remains faster than ProofBit at every tested depth. At 32 boundaries, shared software is still about `1 / 0.7723 ~= 1.29x` faster than the ProofBit Python reference.

## Explicit plumbing work

The serialized control reconstructs nine trust fields per hop:

| Boundaries | Metadata field assignments |
| ---: | ---: |
| 1 | 90,000 |
| 2 | 180,000 |
| 4 | 360,000 |
| 8 | 720,000 |
| 16 | 1,440,000 |
| 32 | 2,880,000 |

The shared software control avoids this reconstruction entirely by passing one immutable object reference.

ProofBit records one logical proof-reference hop per component boundary, but that counter is a **model of a future proof plane**, not measured hardware transport. Current timing is ordinary Python object/loop/verification cost.

## What this result supports

A narrower composition hypothesis now has executable support:

> When trust metadata is explicitly reconstructed field-by-field at every component boundary, composition cost grows roughly with boundary count and metadata width; the current ProofBit reference avoids that particular reconstruction pattern and is faster on this frozen Python benchmark.

## What this result does not support

It does **not** show:

- that ProofBit is faster than conventional software in general;
- that ordinary software cannot achieve identical safety/correctness;
- that proof references are free across real RPC/process/machine boundaries;
- hardware, silicon, area, energy, cache, network, or cryptographic performance;
- a universal crossover point;
- proof of novelty or superiority.

The shared-object software control is the key negative control: when conventional software can preserve one immutable trust envelope without repeated reconstruction, it remains both fully correct and faster than the current ProofBit Python reference.

## Next falsifiable step

`PB-TRUST-COMPOSE-02` should replace modeled boundary hops with actual serialization/transport implementations:

1. JSON or MessagePack structured software envelope;
2. compact ProofBit proof/tag encoding;
3. process boundary or socket/pipe transport;
4. epoch invalidation during flight;
5. duplicate/retry delivery;
6. statement rebinding attempt after deserialization;
7. separate outcome receipt channel.

Then measure bytes transferred, encode/decode time, allocations, validation work, audit reconstruction, and correctness.

That experiment can test whether the v0.1 crossover survives when both approaches pay real transport costs.
