# ProofBit Market Benchmark Methodology v0.2

## Purpose

ProofBit is entering a market that already contains highly optimized CPUs and AI accelerators. The project therefore needs a permanent external benchmark frame, not only an internal `BaselineProcessor` comparison.

The comparison has four primary axes:

1. **Utility** — useful work completed and failures prevented.
2. **Proof** — how much of the useful work is backed by evidence strong enough for the requested action.
3. **Cost** — memory, compute, energy, silicon area, infrastructure cost, and proof overhead.
4. **Speed** — latency, throughput, time-to-result, and trusted useful throughput.

The target is not to claim that ProofBit wins every workload. The target is to find where proof-aware computation produces a better utility/proof/cost/speed tradeoff than conventional systems.

## Market reference set

The initial reference set is deliberately broad:

- conventional value-only ProofBit baseline
- ProofBit ProofProcessor
- NVIDIA GB200 NVL72
- Google TPU7x Ironwood
- Cerebras WSE-3 / CS-3
- AWS Trainium3
- AMD Instinct MI450 Series
- OpenAI + Broadcom Jalapeno

The machine-readable registry lives in `benchmarks/hardware_reference.json`.

## Why two benchmark tiers are required

### Tier A — executable common workload

A system belongs in Tier A only after the same ProofBit workload has actually been run with a frozen configuration and measurement boundary.

Examples of Tier A metrics:

```text
raw throughput
p50 / p95 / p99 latency
trusted useful actions / second
unsafe actions / million decisions
false-positive block rate
proof verification latency
memory overhead
energy / trusted useful action
cost / trusted useful action
```

The current Tier A contains the ProofBit software reference models and the dependency-free CPU execution of PB-AI-01. External accelerator targets remain `NOT RUN` until the same frozen workload actually executes there.

### Tier B — published hardware reference

Vendor-published specifications are useful for understanding the market but are not an apples-to-apples ProofBit benchmark.

Examples:

```text
peak FLOPS at a stated precision
memory capacity
memory bandwidth
interconnect bandwidth
accelerator count / pod scale
published power or efficiency metrics
published LLM latency or tokens/s
```

Tier B values MUST NOT be collapsed into an overall ranking because:

- chip, wafer, server, and rack scales differ;
- FP4, FP8, BF16, and vendor-defined AI metrics differ;
- peak FLOPS are not application throughput;
- training and inference optimize for different objectives;
- vendor benchmark shapes and batch sizes differ;
- proof semantics are not measured by conventional AI benchmarks.

## ProofBit common workload suite

The long-term cross-hardware suite uses frozen workload definitions.

### PB-MEM-01 — proof-aware memory

Measures data-plane and proof-plane store/load overhead.

### PB-VERIFY-01 — proof verification

Measures verification latency and throughput for explicit verifier implementations.

### PB-CACHE-01 — proof cache

Measures cold/warm hit rate, invalidation cost, working-set sensitivity, and speedup as verification cost changes.

### PB-GUARD-01 — contaminated decision stream

Feeds identical valid, unknown, stale, replayed, conflicting, and false-success states to each implementation.

Primary outputs:

```text
safe useful actions / second
unsafe actions / million decisions
false-positive block rate
```

### PB-AI-01 — proof-aware inference / agent workload

PB-AI-01 v0.1 is now executable. Its frozen contract is documented in `docs/pb-ai-01.md` and implemented by `proofbit/ai_workload.py` plus `benchmarks/pb_ai_01.py`.

Version 0.1 deliberately uses a deterministic inference-like fixed-point kernel rather than pretending to be an LLM quality benchmark. The same scores are passed through both a value-only execution boundary and a ProofBit execution boundary.

Primary outputs:

```text
inference elapsed time
end-to-end task latency
useful actions / second
trusted useful actions / second
unsafe actions / million tool decisions
proof coverage
proof guard overhead
end-to-end proof overhead
```

The first reproducible scorecard is `docs/benchmark-results-pb-ai-01-v0.1.md`.

Reserved adapter IDs:

```text
nvidia-cuda
google-tpu-jax
cerebras
aws-neuron
amd-rocm
openai-jalapeno
```

These remain `NOT RUN` until the adapter and target environment actually exist. No synthetic competitor score is substituted.

## Four-axis scorecard

Every frozen run reports the four axes separately before any composite score.

### Utility

Candidate metrics:

```text
useful actions completed
prevented unsafe actions
expected loss avoided
successful tasks / second
```

### Proof

Candidate metrics:

```text
verified useful action rate
provenance coverage
authority freshness coverage
replay resistance
outcome-grounding coverage
```

### Cost

Candidate metrics:

```text
bytes / protected state
joules / trusted useful action
accelerator-hours / workload
USD / million trusted actions
silicon area overhead
```

### Speed

Candidate metrics:

```text
operations / second
tokens / second
p50 / p99 latency
trusted useful actions / second
```

## North-star metric

The strongest cross-system metric is not raw operations per second. It is:

```text
Trusted Useful Throughput
  = correctly permitted useful actions with sufficient proof / second
```

A related economic metric is:

```text
Net Proof Utility
  = Useful Value
  + Expected Failure Loss Avoided
  - Proof Compute Cost
  - Proof Memory Cost
  - Proof Energy Cost
  - Proof Latency Cost
```

These values remain decomposable. A single scalar score is secondary and must never hide the underlying measurements.

## Executable PB-AI-01 baseline — August 2026

GitHub Actions run `32465900273` executed PB-AI-01 v0.1 with 10,000 decisions and 10% contamination on the dependency-free CPU/Python reference backend.

Observed CPython 3.12.14 results included:

```text
Value-only boundary:
  9,000 safe actions
  1,000 unsafe actions
  100,000 unsafe / 1M decisions
  452,392 end-to-end decisions/s

ProofBit boundary:
  9,000 safe and proven actions
  0 unsafe actions
  0 false-positive valid blocks
  235,746 end-to-end decisions/s
  212,171 trusted useful actions/s

proof guard overhead: 9.76x
end-to-end overhead:  1.92x
```

These are software reference numbers. Their purpose is to create the first common-workload coordinate, not to predict silicon performance.

## Current market context — August 2026

OpenAI publicly describes a heterogeneous silicon strategy spanning NVIDIA, AMD, AWS Trainium, Cerebras, and its own accelerator developed with Broadcom. OpenAI also states that its Abilene Stargate site runs NVIDIA GB200 systems and has announced 750 MW of Cerebras ultra-low-latency inference capacity. This makes heterogeneous benchmarking directly relevant to ProofBit rather than speculative market comparison.

## Source policy

Each external hardware entry MUST include a first-party source where possible and a capture date. Published specifications are historical reference points and should be refreshed before a release, paper, investor claim, or external benchmark announcement.

No externally published number becomes a ProofBit performance claim until the same frozen workload has been run under a documented measurement protocol.
