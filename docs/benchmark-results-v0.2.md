# ProofBit Benchmark Scorecard v0.2

## Status

This scorecard records an early reproducible reference-model result. It is intentionally not a silicon-performance claim.

Reference CI run:

```text
GitHub Actions run: 32463427223
Ubuntu 24.04
CPython 3.12.14
x86_64
commit: 147b4257cdfbd982c4f23060f3dd3bbba5bcf001
```

The same test/benchmark smoke suite also passed on Python 3.11 and 3.13.

## 1. Value-only vs proof-aware store/load

Workload: one store + one load per iteration, 10,000 iterations per round, 3 rounds.

| Metric | BaselineProcessor | ProofProcessor |
| --- | ---: | ---: |
| median ns / iteration | 196.51 | 1,981.82 |
| iterations / second | 5.09M | 0.505M |
| runtime ratio | 1.00x | 10.09x |
| logical bytes / cell estimate | 8 | 41 |

The logical storage estimate is a conceptual packed-layout estimate, not Python object size and not a final hardware layout.

### Safety contrast

For the modeled adversarial cases:

```text
UNKNOWN
STALE
REPLAY
CONFLICT
FALSE_SUCCESS
```

Baseline prevented:

```text
0 / 5
```

ProofProcessor prevented:

```text
5 / 5
```

Both processors allowed the modeled NORMAL case.

## 2. 90/10 contaminated-memory workload

Composition:

```text
90% valid
10% adversarial, split across:
UNKNOWN / STALE / REPLAY / CONFLICT / FALSE_SUCCESS
```

10,000 decisions, 2 rounds:

| Metric | BaselineProcessor | ProofProcessor |
| --- | ---: | ---: |
| safe actions | 9,000 | 9,000 |
| unsafe actions | 1,000 | 0 |
| unsafe actions / 1M decisions | 100,000 | 0 |
| false-positive block rate | 0% | 0% |
| safe useful actions / sec | 3.90M | 0.401M |

This is the core cost-versus-correctness contrast for the current semantic model: the proof-aware system is substantially slower in Python, but blocks all modeled unsafe cases without blocking modeled valid actions.

## 3. Contamination sweep

The deterministic sweep varies the fraction of adversarial states while keeping the same semantic fault classes.

| Contamination | Baseline unsafe / 1M | Proof unsafe / 1M | Proof false-positive blocks |
| ---: | ---: | ---: | ---: |
| 0.01% | 100 | 0 | 0% |
| 0.1% | 1,000 | 0 | 0% |
| 1% | 10,000 | 0 | 0% |
| 5% | 50,000 | 0 | 0% |
| 10% | 100,000 | 0 | 0% |
| 25% | 250,000 | 0 | 0% |
| 50% | 500,000 | 0 | 0% |

These numbers follow directly from the deterministic workload construction. They demonstrate semantic separation, not a real-world defect prevalence estimate.

## 4. Proof Cache v0.2.1

The cache benchmark starts each timed round with a cold cache. Cache entries are bound to statement, value, proof id, evidence authority/epoch, and current processor authority/epoch. Replay consumption is never bypassed by the cache.

10,000 requests per case, 2 rounds:

| Working set | Hit rate | Raw uncached ns | Raw cached ns |
| ---: | ---: | ---: | ---: |
| 1 | 99.99% | 181.22 | 409.95 |
| 8 | 99.92% | 183.38 | 419.63 |
| 64 | 99.36% | 180.85 | 460.93 |
| 1024 | 89.76% | 204.69 | 468.20 |

With effectively free verification, the Python cache lookup is slower than direct semantic verification. That is an important negative result.

The benchmark therefore also exposes an explicit verifier-cost model. It does not claim that these costs equal any specific cryptographic scheme.

### Modeled speedup if one uncached verification costs 1 microsecond

| Working set | Speedup |
| ---: | ---: |
| 1 | 2.88x |
| 8 | 2.81x |
| 64 | 2.53x |
| 1024 | 2.11x |

### Modeled speedup if one uncached verification costs 10 microseconds

| Working set | Speedup |
| ---: | ---: |
| 1 | 24.77x |
| 8 | 23.81x |
| 64 | 19.39x |
| 1024 | 6.84x |

This establishes the first ProofBit cache break-even question:

> At what real verification cost and evidence-reuse rate does proof caching amortize its own metadata and lookup cost?

## 5. What these results do and do not show

They show:

- the current semantic model distinguishes value from justified state;
- the modeled negative cases are blocked while modeled valid actions remain allowed;
- the current Python implementation has substantial runtime and metadata overhead;
- proof caching has a measurable fixed cost;
- caching becomes attractive in the explicit cost model when verification is non-trivial and evidence is reused.

They do not show:

- that a ProofBit hardware processor would be 10x slower;
- that real systems have the contamination rates used here;
- that any particular cryptographic proof costs 1 or 10 microseconds;
- that the current memory layout is close to optimal;
- that ProofBit is already superior to established hardware security architectures.

## 6. Next benchmark targets

The optimization program should try to move several curves at once:

```text
runtime overhead              down
metadata bytes / protected cell down
cache lookup cost             down
unsafe actions / 1M           stay near zero for covered faults
false-positive blocks         stay near zero for valid modeled cases
safe useful actions / sec     up
```

Next concrete experiments:

1. compact proof tags instead of Python tuple keys;
2. address-indexed proof cache;
3. generation/epoch tag invalidation;
4. read-heavy vs write-heavy workloads;
5. hot/cold evidence distributions;
6. explicit verifier implementations rather than only a verifier-cost model;
7. VM/ISA cycle accounting;
8. RTL/FPGA area, timing, power, and memory-overhead measurements.
