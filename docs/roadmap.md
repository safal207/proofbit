# ProofBit Roadmap

## Phase 0 — Semantic seed

Goal: make the idea precise enough to criticize.

- [x] Define ProofBit
- [x] Separate `PROVEN_FALSE` from `UNKNOWN`
- [x] Make `CONFLICT` first-class
- [x] Define authority and epoch binding
- [x] Define no-silent-promotion invariant
- [x] Sketch dual-plane memory and processor architecture

Exit criterion:

> Another engineer can identify a concrete invariant and construct a counterexample against it.

## Phase 1 — Executable model

Build a tiny software implementation with:

- `ProofBit`
- `ProofCell`
- `ProofStore`
- verification results
- derivation DAGs
- guarded side-effect API

Required adversarial tests:

```text
NORMAL
UNKNOWN
CONFLICT
STALE_AUTHORITY
REPLAY
FALSE_SUCCESS
```

Exit criterion:

> A protected action executes only when the required state is proven under the current authority and epoch.

## Phase 2 — ProofBit virtual machine

Create a minimal VM with a small proof-aware instruction set:

```text
PLOAD
PSTORE
PVERIFY
PASSERT
PJOIN
PGUARD
```

Measure:

- metadata overhead
- verification latency
- proof-cache hit rate
- derivation growth
- invalidation cost

Exit criterion:

> The VM demonstrates proof propagation and side-effect gating independently of application-specific code.

## Phase 3 — Memory architecture experiments

Compare metadata granularity:

- per bit
- per word
- per cache line
- per object
- per page
- capability-scoped

Explore:

- shadow memory
- proof reference compression
- proof cache
- epoch invalidation
- content-addressed evidence

Exit criterion:

> We have measured trade-offs rather than intuition about storage and coherence cost.

## Phase 4 — AI-agent reference workload

Reference flow:

```text
external observation
  -> agent memory
  -> reasoning
  -> tool decision
  -> guarded tool execution
  -> external outcome
  -> receipt
```

Attack cases:

- hallucinated approval
- stale approval
- replayed approval
- conflicting sources
- successful dispatch with failed outcome
- copied memory that loses provenance

Exit criterion:

> Unverified agent memory remains readable but cannot silently become authority for a protected side effect.

## Phase 5 — Architectural simulator / FPGA exploration

Candidate acceleration targets:

- proof-reference lookup
- verification result cache
- epoch comparison
- replay-consumption tracking
- proof metadata propagation
- guard evaluation

Exit criterion:

> At least one proof-plane operation shows a measurable reason to move below the software layer.

## Phase 6 — Prior-art map and research positioning

Systematically compare ProofBit with adjacent ideas including:

- ECC and integrity metadata
- memory tagging
- information-flow / taint tracking
- capability machines
- proof-carrying code
- authenticated data structures
- TPM / trusted execution
- secure enclaves
- provenance systems
- formal verification
- transactional and versioned memory

The objective is not to force a novelty claim. It is to determine exactly which combination, semantics, or consumption boundary is genuinely distinct and useful.

Exit criterion:

> The project can state what is inherited, what is combined, what is different, and what remains unproven.

## Phase 7 — Hardware research proposal

Only after the software and simulator stages:

- define candidate ISA extension
- define register/shadow-register representation
- define proof-cache behavior
- define coherence and invalidation semantics
- define privileged action gating
- estimate area / power / latency overhead
- select benchmark workloads

Exit criterion:

> A hardware proposal is justified by measured workloads and explicit invariants, not by metaphor.

## Immediate next milestone

**ProofBit v0.2 — executable reference model.**

The next commit should introduce a small implementation and tests for the six canonical scenarios:

```text
NORMAL
UNKNOWN
CONFLICT
STALE_AUTHORITY
REPLAY
FALSE_SUCCESS
```
