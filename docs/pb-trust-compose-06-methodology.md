# PB-TRUST-COMPOSE-06 Methodology

## Question

When a trust contract evolves over time, how much update, regression, activation and runtime work is required to keep every component aligned without semantic drift?

TC06 does **not** assume conventional software is buggy. Its strongest conventional control is deliberately given the same data-driven policy primitives and the same-size propagated receipt representation as the ProofBit reference.

The experiment is falsifiable: if competent conventional shared-policy software matches ProofBit, that result must be reported as a negative ProofBit result.

## Frozen policy evolution

The benchmark defines five cumulative policy versions:

```text
v1  statement + authority
v2  + epoch
v3  + replay
v4  + provenance
v5  + separate outcome evidence for terminal success
```

The six primitives are frozen before measurement:

```text
statement
authority
epoch
replay
provenance
outcome
```

A policy change that requires a **new primitive outside this set** is explicitly outside the one-descriptor-update claim. Such a change would require verifier/component evolution in both conventional and ProofBit designs.

## Frozen workload

Each policy version receives a deterministic request stream containing:

```text
VALID
WRONG_STATEMENT
WRONG_AUTHORITY
STALE_EPOCH
REPLAY
MISSING_PROVENANCE
FALSE_SUCCESS
```

The default distribution is:

```text
70% VALID
5% each pressure case
```

The oracle is version-aware. For example, a stale epoch is not rejected by `v1`, because epoch is not yet part of that policy. Once `v2` activates, the same condition becomes a denial.

This avoids judging older policy versions by rules that did not yet exist.

## Compared systems

### `software_shared_registry`

Strongest conventional anti-strawman control.

- one authoritative data-driven policy descriptor;
- one ingress validation;
- one compact propagated validation receipt;
- every component checks request binding, policy version, required mask and stable policy digest;
- policy evolution within the frozen primitives requires one authoritative descriptor update.

This control intentionally captures the main benefit often attributed to proof-native propagation: centralized semantics plus a compact downstream receipt.

If it matches ProofBit, the result belongs to the architectural pattern rather than uniquely to ProofBit.

### `software_independent_copies`

Competent independently managed conventional policy copies.

- every component has its own byte-identical active policy descriptor after safe rollout;
- every component validates the propagated receipt against its local version/mask/digest;
- rollout is fail-closed;
- the primary safe strategy does **not** activate a new policy until every required copy is upgraded.

No component is intentionally buggy or permitted to silently ignore an unknown policy version.

This system measures replicated governance/update work rather than careless implementation.

### `proofbit_contract`

ProofBit software-reference contract propagation.

- one proof-plane policy descriptor;
- ingress produces a compact bound proof/decision token;
- every component validates request binding, policy version, required mask and policy digest;
- policy evolution inside the frozen primitive set changes the authoritative descriptor rather than each component policy copy.

The token is a semantic reference object, not a cryptographic proof and not a silicon instruction.

## Representation fairness

The frozen policy descriptor is exactly:

```text
16 bytes
```

The propagated receipt/proof token is exactly:

```text
32 bytes
```

for both `software_shared_registry` and `proofbit_contract`.

Therefore a runtime or storage result between those two systems cannot be credited to a smaller ProofBit wire representation.

## Safe rollout comparison

The primary rollout policy is correctness-first:

```text
upgrade policy copies
run frozen regression vectors
activate only when required copies are ready
```

For four policy evolutions (`v1 -> v2 -> v3 -> v4 -> v5`):

- shared conventional registry: one managed policy copy per evolution;
- independent conventional components: one managed copy per component per evolution;
- ProofBit contract: one proof-plane descriptor per evolution, **only because every change is inside the frozen primitive set**.

Metrics:

```text
managed policy copies
policy-copy updates
safe activation steps
regression-suite invocations
regression-suite failures
active policy descriptor bytes
semantic drift after safe activation
```

The regression metric counts actual executions of the frozen policy-vector suite against every managed policy copy. It is not a guessed LOC or engineering-hours score.

## Early-activation stress

TC06 also runs a secondary stress test for the independently managed system:

1. upgrade only part of the component path;
2. activate the new policy receipt early;
3. send valid new-version probes through the entire path.

Old components reject the unmatched policy version/digest.

This is expected to produce **availability loss, not unsafe acceptance**.

The stress test is not the primary rollout strategy. It exists to expose the correctness/availability tradeoff during mixed versions without inventing bugs.

## Runtime measurement

After each system has completed safe activation, all systems process the same versioned workload.

The benchmark runs multiple rounds and rotates execution order across all three systems.

Runtime metrics:

```text
oracle accuracy
unsafe accepts
false terminal success
missed valid requests
median elapsed time
median requests / second
raw per-round throughput
```

Small differences on a shared GitHub runner must not be presented as universal performance ordering.

## Four-axis interpretation

### Utility

Does the system preserve the versioned oracle while allowing valid work after safe activation?

### Proof / trust

Does every component know which exact trust contract authorized the decision, and does a terminal success require the outcome primitive once that policy version requires it?

### Cost

How many independently managed policy copies, updates, regression-suite executions and active descriptor bytes are required?

### Speed

What runtime cost remains after a safe rollout has completed?

No synthetic winner score combines these axes.

## Required negative-result discipline

The report must explicitly state if observed:

- `software_shared_registry` matches ProofBit correctness;
- shared conventional software matches ProofBit update surface;
- shared conventional software matches ProofBit propagated token size;
- independent software avoids semantic drift through fail-closed rollout;
- ProofBit does not produce a stable runtime advantage;
- any advantage disappears when conventional software adopts the same policy-registry/receipt architecture.

## Claim boundary

TC06 is Python software-reference evidence. It does not establish:

- organization-wide engineering-hours savings;
- deployment-system behavior outside the frozen model;
- polyglot ABI compatibility;
- cryptographic authenticity;
- distributed consensus;
- silicon cycles, energy or area;
- novelty or patentability;
- a universal advantage over shared policy services or conventional typed receipts.

The benchmark's strongest possible conclusion is narrower: it can show how policy-copy replication scales update/regression surface, and whether a single generic policy-contract mechanism reproduces that benefit in both conventional and ProofBit forms.
