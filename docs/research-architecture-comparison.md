# ProofBit Research Architecture Comparison

## Why include CaPU and COSMIC ORGANICS / MORPHOS

ProofBit should not compare only against conventional CPUs and commercial AI accelerators. The broader research question is which computation model gives the best tradeoff across:

1. Utility
2. Proof / justification
3. Cost
4. Speed

Two existing research architectures provide useful internal comparison points.

## ProofBit

Primary question:

> Can a machine carry enough evidence with state to prevent unsupported state or side effects from being silently treated as trusted?

Core emphasis:

```text
value + evidence + provenance + authority + epoch
```

Primary benchmark strength:

```text
proof coverage
stale / replay / conflict handling
outcome grounding
trusted useful throughput
```

## CaPU — Causal Processing Unit

Repository: `safal207/CaPU`

CaPU is a permission-first execution architecture. Its central pipeline is:

```text
Gate -> Incubate -> Commit -> Execute -> Effect
```

Its processor model, semantic ISA, microarchitecture and Causal Memory Controller make it appropriate as a research processor architecture comparison point.

Primary question:

> Did this transition have the right to happen before the side effect occurred?

Primary benchmark strength:

```text
transition legitimacy
commit-before-effect
maturity / hold behavior
replayable causal justification
execution-control latency
```

CaPU is currently a software/research processor model, not a silicon-performance claim.

## COSMIC ORGANICS / MORPHOS

Repository: `safal207/COSMIC-ORGANICS`

MORPHOS explores computation in which state transition is itself part of the computation.

Core model:

```text
state + interaction + constraint + energy + time
  -> transition
  -> function
```

Primary question:

> Can useful computation emerge from controlled structured-state transitions with favorable capacity, recovery and transition cost?

Primary benchmark strength:

```text
state capacity
transition cost
recovery
robustness
scale generalization
persistent physical-like state
```

MORPHOS is an alternative transition-computing research model, not a conventional CPU, GPU or current silicon processor.

## Comparison map

| Architecture | Primary object | Main guarantee / goal | Natural cost unit |
| --- | --- | --- | --- |
| Conventional CPU | value / instruction | compute requested transition | cycles, bytes, joules |
| ProofBit | justified state | do not overclaim evidence | proof bytes, verification latency |
| CaPU | legitimate transition | commit before effect | gate/commit latency, causal metadata |
| MORPHOS | state transition | compute through controlled state dynamics | transitions, recovery cost, energy/time model |

## Common benchmark rule

These systems must not be assigned a single overall rank until the same frozen workload has actually been adapted and executed.

For PB-AI-01 the registered targets are:

```text
ProofBit CPU reference   EXECUTED
CaPU / CMC               NOT RUN — adapter needed
MORPHOS                  NOT RUN — adapter needed
```

Future adapters:

```text
capu-cmc
cosmic-morphos
```

The adapter must preserve the benchmark oracle and measurement boundary. It may express the execution semantics differently, but it may not weaken the failure classes merely to improve the score.

## Four-axis comparison

Every architecture should eventually produce separate values for:

```text
UTILITY
  useful actions / tasks completed
  failures prevented

PROOF
  justified / legitimate / recoverable useful output
  provenance and transition evidence coverage

COST
  memory metadata
  transitions / cycles
  verification / gate cost
  energy and area when measurable

SPEED
  end-to-end latency
  throughput
  trusted / legitimate useful throughput
```

The purpose is not to force all architectures into one philosophy. The purpose is to identify the workloads where each computing principle occupies the best utility-proof-cost-speed frontier.
