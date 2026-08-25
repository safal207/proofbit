# ProofBit Benchmark Methodology v0.1

## Goal

Measure the tradeoff between conventional value-only computation and proof-aware computation from the first executable prototype onward.

The benchmark intentionally separates two questions:

1. **What does proof-awareness cost?**
2. **What failures does proof-awareness prevent?**

A result is useful only when both are reported together.

## Systems under comparison

### BaselineProcessor

A minimal conventional model:

```text
address -> value
```

A privileged action may execute when the stored Boolean value is true. The model does not carry native freshness, provenance, replay, conflict, or outcome-grounding semantics.

### ProofProcessor

A proof-aware model:

```text
address -> ProofCell
ProofCell = <value, state, proof, provenance, authority, epoch>
```

A privileged action is allowed only when the evidence is currently acceptable under the processor's authority and epoch rules.

## v0.1 metrics

### Runtime cost

The reference benchmark measures a repeated store+load workload for both models and reports:

- median nanoseconds per benchmark iteration
- median benchmark iterations per second
- runtime overhead ratio

This is a **Python reference-model measurement**. It is not a prediction of CPU, FPGA, ASIC, cache, or DRAM performance.

### Storage cost

v0.1 reports a conceptual packed-layout estimate:

```text
baseline value:             8 bytes
proof value:                8 bytes
state:                      1 byte
proof reference:            8 bytes
provenance reference:       8 bytes
authority reference:        8 bytes
epoch:                      8 bytes
```

The current conceptual total is therefore 41 bytes per proof-aware cell versus 8 bytes for the baseline value.

This is not a final hardware layout. Later versions must explore compression, shared proof references, page/block-level metadata, proof caches, and selective proof-aware regions.

### Correctness / safety value

The benchmark includes one normal case and five adversarial cases:

| Case | Expected ProofProcessor behavior |
| --- | --- |
| NORMAL | allow |
| UNKNOWN | block |
| STALE | block |
| REPLAY | first allow, repeated consumption block |
| CONFLICT | block |
| FALSE_SUCCESS | block without outcome evidence |

For adversarial cases we report:

```text
prevented unsafe actions / total adversarial cases
```

The baseline is intentionally not given hidden metadata or application-specific checks. If those checks are added, they must be counted explicitly as baseline cost and complexity rather than treated as free.

## Fairness rules

1. Use the same logical workload for both models where possible.
2. Never present Python object overhead as hardware overhead.
3. Never present a designed safety invariant as an empirical discovery; tests demonstrate implementation behavior only.
4. Report normal-case acceptance together with adversarial blocking to detect systems that are "safe" only because they block everything.
5. Record environment metadata for performance runs.
6. Prefer medians across multiple rounds over a single timing sample.
7. Preserve negative or disappointing results.

## Reproduce

Run tests:

```bash
python -m unittest discover -s tests -v
```

Run the benchmark:

```bash
python benchmarks/compare.py --iterations 100000 --rounds 5
```

Machine-readable output:

```bash
python benchmarks/compare.py --iterations 100000 --rounds 5 --json
```

## Benchmark ladder

### v0.1 — semantic reference model

Measure software overhead and basic failure prevention.

### v0.2 — contaminated workload

Mix valid and adversarial state in controlled proportions and measure:

- safe useful actions per second
- unsafe side effects per million decisions
- false-positive block rate
- proof-cache hit rate

### v0.3 — proof-plane optimizations

Compare:

- inline metadata
- shared proof references
- block/page metadata
- proof cache
- lazy verification
- selective proof-aware memory

### v0.4 — VM / ISA simulator

Measure proof-aware instructions such as `PLOAD`, `PSTORE`, `PVERIFY`, `PCMP`, and guarded side effects.

### v0.5 — FPGA / RTL

Measure actual hardware-relevant quantities:

- cycles per operation
- LUT/FF/BRAM cost
- maximum clock frequency
- energy proxy / switching activity where available
- proof-cache area and hit rate
- memory bandwidth overhead

Only at this stage should hardware performance claims begin.

## Central research curve

The project should continuously track:

```text
additional compute + memory cost
             versus
prevented incorrect or unauthorized side effects
```

The objective is not zero overhead. The objective is to find architectures where the marginal cost of proof-awareness becomes small enough that the correctness gain is economically and technically compelling.
