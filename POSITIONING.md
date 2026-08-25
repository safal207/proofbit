# ProofBit Positioning

## Current definition

The most accurate v0.1 definition is:

> **ProofBit is a proof-aware capability/evidence architecture for binding state, authority, freshness, provenance, replay, execution context, and observed outcome at a machine-enforced effect boundary.**

It is not currently positioned as a replacement for general-purpose CPUs, GPUs, TPUs, or wafer-scale AI accelerators.

The likely long-term form, if the remaining hardware hypotheses survive, is a **trust/action coprocessor or ISA/memory extension** attached to ordinary compute.

## What ProofBit resembles

### 1. Capability and tagged-memory architectures

This is the closest hardware family.

Shared ideas:

- non-forgeable metadata associated with values or references;
- mandatory checks near memory access or side effects;
- authority and scope carried with the object;
- isolation from ordinary unprivileged mutation;
- revocation, context, and replay concerns.

ProofBit's intended semantic extension is not merely “may this pointer access this object?” It asks:

```text
What exact statement is established?
Who authorized its use?
Is that authority still fresh?
Where did the evidence come from?
Has the authorization already been consumed?
Was the requested side effect the one that was authorized?
Did the external outcome actually occur?
```

The benchmark evidence so far says that an equally expressive conventional capability architecture can implement the same frozen contract. Therefore ProofBit should be treated as a **richer contract and composition model**, not assumed to be a fundamentally different transistor-level mechanism.

### 2. Taint tracking and provenance systems

Shared ideas:

- metadata follows data;
- transformations should preserve origin;
- derived results inherit restrictions or lineage;
- unsafe sinks can be gated.

Differences in emphasis:

- ProofBit distinguishes `PROVEN_FALSE`, `UNKNOWN`, `CONFLICT`, `STALE`, and replayed state;
- authority and epoch are first-class;
- evidence may authorize a particular action rather than merely label a data source;
- terminal outcome requires a separate receipt;
- consume-once semantics matter for consequential actions.

### 3. Proof-carrying code and verifiable computing

Shared ideas:

- a claim is accompanied by machine-checkable evidence;
- the consumer verifies before trusting the claim;
- verification should be portable and independently reproducible.

ProofBit's current focus is narrower than proving an entire program trace. It focuses on **selected state and consequential action boundaries**:

```text
proposal
-> evidence-bound authorization
-> mandatory guarded effect
-> observed outcome receipt
```

A future ProofBit system could consume cryptographic or formal proofs, but the v0.1 proof references are primarily semantic and architectural objects.

### 4. Trusted execution environments and attestation

Shared ideas:

- hardware-rooted identity;
- protected execution state;
- measured software/configuration;
- remote evidence that a trusted component ran.

ProofBit is complementary rather than substitutive.

Attestation can answer:

```text
Which measured component produced this receipt?
```

ProofBit aims to answer:

```text
Why was this exact action authorized?
Which statement, authority, epoch, context, and evidence were bound?
Was the authorization consumed once?
What outcome was observed?
```

PB-HW-06 should explicitly connect these layers.

### 5. Event sourcing, audit logs, and receipt chains

Shared ideas:

- append-only transitions;
- deterministic reconstruction;
- explicit authorization, execution, and outcome events;
- indexes for targeted audit;
- conflict and supersession rather than silent rewriting.

TC04 and TC05 showed that indexed conventional receipt chains can match ProofBit recovery and corruption behavior. The durable-log pattern is useful but not uniquely ProofBit.

### 6. Transactional and versioned memory

Shared ideas:

- atomic state transitions;
- version/epoch checks;
- stale-read detection;
- rollback and conflict handling;
- all-or-nothing visibility.

This is the most important adjacent family for PB-HW-05. The next claim is not “ProofBit invented atomicity.” It is whether treating value and evidence as one atomic trust state reduces transactions, torn windows, or recovery work compared with an equally strong tagged-memory design.

## What ProofBit does not resemble operationally

### Not an AI compute accelerator

NVIDIA, Google TPU, Cerebras, AMD, AWS Trainium, and similar systems optimize matrix compute, memory bandwidth, model execution, and interconnect.

ProofBit's plausible role is downstream or beside them:

```text
model / accelerator proposes action
-> ProofBit / action guard validates trust contract
-> consequential side effect executes or is blocked
-> outcome receipt is produced
```

### Not “blockchain for every bit”

ProofBit does not require global consensus, token economics, or an inline cryptographic object for every physical bit.

A practical implementation can use:

- shadow metadata;
- object/page/capability granularity;
- proof references;
- local caches;
- content-addressed evidence stores;
- selected guarded instructions only.

### Not a claim to metaphysical truth

ProofBit does not make a processor know reality. It preserves a narrower property:

> The machine must not claim stronger justification for a state or side effect than the evidence, authority, context, freshness, and observed outcome support.

## The architecture stack

A practical system can be divided into five layers:

```text
1. Evidence adapters
   identity, approvals, artifacts, state roots, signatures, attestations

2. Canonical trust contract
   statement, authority, policy, epoch, context, replay, provenance

3. Decision / composition engine
   derive ACCEPT / REJECT / HOLD or an authorized transition

4. Mandatory effect boundary
   consume the exact authorization once at the only authoritative writer

5. Outcome and audit plane
   observe result, issue receipt, preserve conflict and recovery history
```

ProofBit research primarily targets layers 2–4 and their memory/ISA representation.

ProofPath is the likely commercial product spanning layers 1–5.

## Where defensibility may come from

The current experiments do not support defensibility from generic tags, caches, canonical JSON/binary records, indexed logs, or ordinary policy checks alone.

Potential defensibility is more likely to come from the combination of:

1. **Canonical action/evidence contract**  
   A stable portable representation for intent, authority, state, authorization, and outcome.

2. **Conformance and adversarial corpus**  
   A benchmark set covering stale authority, replay, rebinding, false success, crash, corruption, privilege bypass, DMA/debug paths, and release skew.

3. **Mandatory integrations**  
   Gateways that physically control production deploys, wallets, IAM changes, smart-contract administration, and other consequential actions.

4. **Portable receipts**  
   Independently verifiable records that bind the decision and actual result.

5. **Policy packs and workflow evidence adapters**  
   Customer-specific knowledge that is expensive to reproduce.

6. **Atomic data+evidence or root-of-trust primitives**  
   Only if PB-HW-05/PB-HW-06 show an advantage not reproduced by strong tagged/capability controls.

7. **Real-world outcome data**  
   Which actions were blocked, which evidence was missing, which policies caused false holds, and how audits were accelerated.

## Product and research naming

Recommended separation:

| Name | Role |
|---|---|
| ProofBit | Research model, ISA/RTL primitives, benchmark and conformance core |
| ProofPath | Commercial proof-carrying action guard and managed assurance product |
| T-Trace | Adversarial verification, traceability, and independent evidence package |
| CaPU | Causal legitimacy / commit-before-effect research adapter |
| MORPHOS / Cosmic Organics | Transition/lattice computation research adapter |

The projects may share a `Trusted Transition Receipt` contract, but should remain separately testable rather than becoming one monolith.

## One-line descriptions

Research:

> **ProofBit investigates whether evidence-aware state and mandatory action boundaries deserve native runtime, memory, or processor support.**

Product:

> **ProofPath prevents consequential AI-agent actions from executing until intent, authority, policy, evidence, current state, and exact action binding have been checked, then records what actually happened.**

Investor-facing, without overclaiming:

> **We are building an assurance layer for autonomous actions: software-first today, with a measured path to proof-aware hardware acceleration only where the data justifies it.**
