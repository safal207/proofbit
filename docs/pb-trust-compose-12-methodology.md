# PB-TRUST-COMPOSE-12 — Whole-System Tag / Proof Coherence

## Question

TC11 showed that a conventional mandatory tagged-capability instruction matches ProofBit on the bounded user-mode ISA when both receive an equally unforgeable metadata plane. TC12 asks whether that result survives when authority must stay coherent across **CPU, debug, DMA, cache state, context switches and rollback**.

A tie between the strongest conventional whole-system capability design and ProofBit is a valid negative result.

## Compared systems

### `cpu_only_tag_machine`

Baseline only. CPU execution checks a tag/action/epoch/nonce, but debug and DMA remain outside that enforcement domain. Replay state is context-local and the tag is not bound to context or object version.

### `whole_system_capability_machine`

Primary conventional anti-strawman. One coherent authority plane covers:

```text
CPU
debug
DMA
cache/object version
context identity
global consume-once replay state
```

The logical capability is bound to action, issuer, epoch, context, object version and nonce.

### `whole_system_proofbit_machine`

The same whole-system enforcement topology, with authority expressed through ProofBit evidence. The proof is bound to statement + object version, authority, epoch, proof id and provenance/context. Global `ProofProcessor` consume-once state survives guest snapshot rollback.

## Frozen scored scenarios

```text
DEBUG_DIRECT_EFFECT
DMA_DIRECT_EFFECT
DEBUG_FORGED_TAG
CONTEXT_SWITCH_LEAK
CACHE_TAG_DATA_SPLIT
SNAPSHOT_REPLAY_ROLLBACK
```

All six are expected to be blocked.

### Cache split

A proof/capability is minted for object version 1, while the current object state advances to version 2 without minting new authority. The effect must not treat the old tag as authority for the new object state.

### Snapshot rollback

One valid single-use authorization is consumed. Guest/context-local replay state is rolled back. The old authorization must remain consumed because the strong machines keep monotonic replay state outside that snapshot.

## Coherence axiom

The capability and ProofBit machines are granted the **same** whole-system unforgeable metadata assumption:

> Untrusted CPU/debug/DMA/cache/context operations cannot forge or silently preserve authority metadata when the bound action/context/object state changes.

This is a model axiom, not measured hardware behavior.

## Valid-path availability

The runtime workload round-robins legitimate effects through:

```text
cpu
debug
dma
```

Both strong machines must accept all valid paths. A whole-system design that merely disables debug or DMA is not considered a fair solution.

## Explicit deeper escape probes

The following remain intentionally unscored:

```text
PHYSICAL_TAG_STORE_TAMPER
MALICIOUS_FIRMWARE
```

TC12 defines both as outside the modeled coherence root. If either can directly rewrite the authority metadata plane, both strong models can be bypassed.

## Metrics

- blocked attacks / 6;
- unsafe effects;
- oracle accuracy;
- enforced domains;
- presence of context/object-version/global-replay binding;
- median valid effects/second over 11 rotated-order rounds;
- exact raw runtime rates.

No physical bit count or chip-area estimate is inferred from logical fields.

## Anti-strawman rule

The primary comparison is:

```text
whole_system_capability_machine
vs
whole_system_proofbit_machine
```

The CPU-only machine is only a baseline showing why a tag restricted to one execution domain is insufficient.

Any TC12 safety result reproduced by the whole-system capability design belongs to coherent mandatory metadata enforcement, not uniquely to ProofBit.

## Falsifier

ProofBit shows no unique TC12 safety advantage if the conventional whole-system capability design blocks all six scored cross-domain attacks while retaining the same valid CPU/debug/DMA availability.

## Claim boundary

Executable Python whole-system coherence reference model. No RTL, physical DMA/IOMMU, real cache-coherence protocol, speculative execution, firmware measurement, physical tag RAM, cycle accuracy, transistor/area/energy, silicon performance, novelty, patentability or universal-superiority claim.
