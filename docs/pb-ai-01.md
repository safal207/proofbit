# PB-AI-01 — Proof-aware inference / agent action benchmark v0.1

## Goal

PB-AI-01 is the first ProofBit workload designed to become executable across conventional CPUs and major AI accelerator families without changing the proof semantics between systems.

It measures four axes separately:

1. **Utility** — useful actions completed and unsafe actions prevented.
2. **Proof** — useful actions that carry evidence sufficient for the action boundary.
3. **Cost** — proof overhead, memory overhead, and later energy / infrastructure cost.
4. **Speed** — inference latency, guard latency, end-to-end throughput, and trusted useful throughput.

PB-AI-01 is not an LLM quality benchmark. Version 0.1 uses a deterministic inference-like scoring kernel so the execution boundary can be compared before model quality, tokenization, framework, and vendor runtime differences are introduced.

## Frozen pipeline

```text
frozen DecisionInput stream
        |
        v
inference-like backend kernel
        |
        v
action score (> 0 proposes an action)
        |
        +------------------------+
        |                        |
        v                        v
value-only boundary        ProofBit boundary
BaselineProcessor          ProofProcessor
        |                        |
        v                        v
outcome accounting        proof-aware accounting
```

The inference kernel and DecisionInput stream are identical for both execution boundaries.

## Input generator

Each decision contains:

```text
decision_id
32 signed small-integer features
state kind
```

The feature generator is deterministic and dependency-free. The scoring kernel is a fixed 32-element dot product plus a fixed bias. All v0.1 scores are intentionally positive so every row proposes an external action and the benchmark isolates the guard boundary.

The arithmetic uses small integers so hardware adapters can reproduce it exactly or with trivial validation tolerance in native accelerator frameworks.

## Contamination states

The stream contains `NORMAL` rows and an exact configured proportion of adversarial rows distributed deterministically across the workload.

Adversarial rows cycle through:

```text
UNKNOWN
STALE
REPLAY
CONFLICT
FALSE_SUCCESS
```

For the default `10%` contamination workload:

```text
10,000 decisions
9,000 NORMAL
1,000 adversarial
```

## Two execution modes

### Value-only mode

`BaselineProcessor` receives the positive action score and executes based on the value alone.

A benchmark oracle can later identify which actions were correct, but the value-only processor does not carry ProofBit evidence. Therefore:

```text
oracle-correct useful actions > 0
ProofBit proof coverage = 0
trusted useful throughput = 0
```

This statement applies to the ProofBit baseline model only. It MUST NOT be generalized into a claim that NVIDIA, Google, Cerebras, AWS, AMD, OpenAI, or any other external system has zero security, provenance, or verification mechanisms.

### Proof-aware mode

`ProofProcessor` receives the same action score plus proof state. `NORMAL` rows receive current evidence. The five adversarial kinds exercise unknown state, stale epoch, consumed proof, unresolved conflict, and outcome claims without outcome evidence.

A protected action is counted as trusted only when it is both useful under the workload oracle and permitted by the ProofBit boundary.

## Primary metrics

### Utility

```text
safe_actions
unsafe_actions
prevented_unsafe_actions
blocked_valid_actions
false_positive_block_rate
```

### Proof

```text
proven_safe_actions
proof_coverage
unsafe_actions_per_million
```

### Speed

```text
inference_elapsed_ns
guard_elapsed_ns
guard_decisions_per_sec
end_to_end_decisions_per_sec
end_to_end_useful_actions_per_sec
trusted_useful_throughput
```

### Cost proxy in v0.1

```text
proof_guard_overhead_ratio
end_to_end_overhead_ratio
```

Later hardware runs add:

```text
joules / decision
joules / trusted useful action
USD / million decisions
USD / million trusted useful actions
accelerator memory footprint
proof metadata footprint
```

## North-star metric

```text
Trusted Useful Throughput
  = proven useful actions / end-to-end second
```

This metric is intentionally different from raw inference throughput. A system can be extremely fast while the benchmark has not established proof coverage for its action boundary.

## Backend contract

The current executable backend is:

```text
cpu-python
```

The registry already reserves the following adapter IDs:

```text
nvidia-cuda       -> NVIDIA GB200 NVL72 reference target
google-tpu-jax    -> Google TPU7x Ironwood reference target
cerebras          -> Cerebras WSE-3 / CS-3 reference target
aws-neuron        -> AWS Trainium3 reference target
amd-rocm          -> AMD Instinct MI450 reference target
openai-jalapeno   -> OpenAI + Broadcom Jalapeno reference target
```

Until an adapter and the target execution environment are actually available, the runner returns `status: not-run`. No synthetic hardware score is substituted.

## Apples-to-apples rule

A hardware result becomes `EXECUTABLE` only when all of the following are frozen and recorded:

```text
PB-AI-01 version
backend adapter version
hardware SKU and scale
runtime / driver / framework versions
batch size
precision or exact arithmetic mode
warmup policy
measurement boundary
number of decisions
contamination rate
raw result artifact
```

Published peak FLOPS, vendor tokens/s, or rack-level marketing numbers remain reference data and are not converted into PB-AI-01 scores.

## Current interpretation

PB-AI-01 v0.1 is deliberately small. Its purpose is to establish a portable experiment in which accelerator speed and proof-aware execution can be measured independently and then recombined into end-to-end utility / proof / cost / speed results.

The next versions should add:

1. batch-size sweep;
2. explicit NumPy / CUDA / JAX adapters where hardware is available;
3. token-stream and first-token latency phases;
4. proof metadata movement across host/device boundaries;
5. cached proof verification;
6. real energy and cost measurements;
7. frozen small-model inference while preserving the same action-state contamination protocol.
