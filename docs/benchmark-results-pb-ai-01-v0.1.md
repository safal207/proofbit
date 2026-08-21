# PB-AI-01 Benchmark Scorecard v0.1

## Status

First reproducible portable AI/agent workload result for ProofBit.

This is a software reference-model result, **not a silicon-performance claim and not an LLM quality benchmark**.

Reference CI run:

```text
GitHub Actions run: 32465900273
Ubuntu 24.04
CPython 3.12.14
x86_64
PB-AI-01: 10,000 decisions, 10% contamination
```

The PB-AI-01 workload and full test suite passed on Python 3.11, 3.12, and 3.13. The run contained 21 passing unit tests.

## Frozen workload

```text
10,000 decisions
32 fixed-point features / decision
9,000 NORMAL
1,000 adversarial
failure classes:
  UNKNOWN
  STALE
  REPLAY
  CONFLICT
  FALSE_SUCCESS
```

The same deterministic inference-like scores are fed to both execution boundaries.

## Inference phase

```text
inference elapsed: 19,785,906 ns
```

## Value-only BaselineProcessor

| Metric | Result |
| --- | ---: |
| safe actions | 9,000 |
| unsafe actions | 1,000 |
| prevented unsafe actions | 0 |
| proof coverage | 0% |
| unsafe actions / 1M | 100,000 |
| end-to-end decisions / second | 452,392 |
| end-to-end useful actions / second | 407,153 |
| trusted useful throughput | 0 / second |

The zero trusted throughput is a property of the ProofBit `BaselineProcessor`: it carries no ProofBit evidence. It is **not** a claim that external commercial accelerators lack security, provenance, attestation, or verification mechanisms.

## ProofProcessor

| Metric | Result |
| --- | ---: |
| safe actions | 9,000 |
| proven safe actions | 9,000 |
| unsafe actions | 0 |
| prevented unsafe actions | 1,000 |
| proof coverage | 100% |
| false-positive block rate | 0% |
| unsafe actions / 1M | 0 |
| end-to-end decisions / second | 235,746 |
| trusted useful throughput | 212,171 / second |

## Cost / speed relationship

```text
proof guard overhead ratio: 9.76x
end-to-end overhead ratio:  1.92x
```

The important observation is the separation between isolated proof-boundary cost and total application cost. The Python ProofBit guard is still expensive in isolation, but once identical inference work is included, the measured end-to-end slowdown is materially smaller.

This is why PB-AI-01 treats the main accelerator-facing metric as:

```text
Trusted Useful Throughput
  = proven useful actions / end-to-end second
```

rather than using only a standalone guard microbenchmark.

## External accelerator adapter status

The frozen backend registry currently contains:

```text
cpu-python          EXECUTED
nvidia-cuda         NOT RUN
google-tpu-jax      NOT RUN
cerebras            NOT RUN
aws-neuron          NOT RUN
amd-rocm            NOT RUN
openai-jalapeno     NOT RUN — no public adapter
```

Reference targets are NVIDIA GB200 NVL72, Google TPU7x Ironwood, Cerebras WSE-3 / CS-3, AWS Trainium3, AMD Instinct MI450 Series, and OpenAI + Broadcom Jalapeno.

No vendor-published FLOPS, bandwidth, tokens/s, or latency number is converted into a PB-AI-01 score. A competitor receives an executable score only after the same frozen workload runs on the target environment under a documented measurement boundary.

## Next experiment

The next useful step is not another synthetic vendor ranking. It is the **first real accelerator adapter**, ideally one that is broadly accessible enough to reproduce independently.

Candidate order:

1. CUDA/NVIDIA or ROCm/AMD if accelerator access is available;
2. JAX/TPU through a reproducible cloud TPU environment;
3. AWS Neuron/Trainium;
4. Cerebras SDK / hosted execution;
5. OpenAI Jalapeno only if a public execution surface becomes available.

At the same time, ProofBit should optimize its side of the equation with compact proof tags and cached verification, then rerun the exact same PB-AI-01 version to show movement on:

```text
Utility up
Proof up
Cost down
Speed up
```
