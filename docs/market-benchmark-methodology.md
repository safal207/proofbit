# ProofBit Market Benchmark Methodology v0.1

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
- OpenAI + Broadcom Jalapeño

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

The current Tier A contains only the software reference models. This is intentional.

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

The long-term cross-hardware suite should use frozen workload definitions.

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

Runs a model or agent loop where retrieved state carries proof metadata and selected external actions require proof-aware gating.

Primary outputs:

```text
tokens / second
first-token latency
end-to-end task latency
trusted actions / second
unsafe actions / million tool decisions
proof overhead / token
proof overhead / tool call
```

This is the workload that can eventually compare ProofBit-enabled execution with GPU, TPU, Trainium, Cerebras, and custom inference accelerators in the market context that matters most.

## Four-axis scorecard

Every frozen run should report the four axes separately before any composite score.

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

These values should remain decomposable. A single scalar score is secondary and must never hide the underlying measurements.

## Current market context — August 2026

OpenAI publicly describes a heterogeneous silicon strategy spanning NVIDIA, AMD, AWS Trainium, Cerebras, and its own accelerator developed with Broadcom. OpenAI also states that its Abilene Stargate site runs NVIDIA GB200 systems and has announced 750 MW of Cerebras ultra-low-latency inference capacity. This makes heterogeneous benchmarking directly relevant to ProofBit rather than speculative market comparison.

## Source policy

Each external hardware entry MUST include a first-party source where possible and a capture date. Published specifications are historical reference points and should be refreshed before a release, paper, investor claim, or external benchmark announcement.

No externally published number becomes a ProofBit performance claim until the same frozen workload has been run under a documented measurement protocol.
