# Proof-Native Processor Architecture v0.1

## 1. Architectural thesis

ProofBit does not require replacing every physical bit with a cryptographic object.

The practical starting point is a dual-plane machine:

```text
+----------------------+      +----------------------+
|      DATA PLANE      |      |      PROOF PLANE     |
|----------------------|      |----------------------|
| values               | <--> | proof references     |
| registers            |      | epistemic status     |
| ordinary cache       |      | authority / epoch    |
| ordinary memory      |      | derivation metadata  |
+----------------------+      +----------------------+
```

The data plane stays fast and conventional. The proof plane records whether selected state is justified for a given use.

## 2. High-level processor

```text
                  +-------------------------+
                  |      ProofProcessor     |
                  |                         |
 input ---------->|  Decode / Control       |
                  |          |              |
                  |    +-----v------+       |
                  |    | Data ALU   |       |
                  |    +-----+------+       |
                  |          |              |
                  |    +-----v------+       |
                  |    | Proof Unit |       |
                  |    +-----+------+       |
                  |          |              |
                  |    +-----v------+       |
                  |    | Gate Unit  |------>| side effect
                  |    +------------+       |
                  +-----------+-------------+
                              |
                   +----------v----------+
                   | Proof-aware memory  |
                   +---------------------+
```

## 3. Major components

### 3.1 Data execution unit

Performs normal computation. ProofBit does not require all arithmetic to become cryptographic proof generation.

### 3.2 Proof Verification Unit (PVU)

Validates proof references and derivations against:

```text
statement
value
authority
epoch
consumption policy
```

The PVU may be implemented partly in hardware and partly in privileged firmware or runtime software during early prototypes.

### 3.3 Proof Status Registers

A register carrying protected state can have associated metadata such as:

```text
VALID
UNKNOWN
CONFLICT
STALE
REPLAYED
```

Early implementations may represent this as shadow registers rather than widening every general-purpose register.

### 3.4 Proof Cache

A small cache stores recently validated proof metadata.

```text
proof_ref -> verification result + authority + epoch
```

A proof cache entry becomes unusable when its authority or epoch no longer satisfies current policy.

This introduces a second coherence problem alongside ordinary cache coherence:

> proof coherence

If data changes, authority changes, or an epoch advances, the machine must not continue consuming the old proof as current authority.

### 3.5 Proof Store

Large evidence objects do not need to live beside data.

```text
address/value -> proof_ref
proof_ref      -> evidence / derivation DAG / receipt
```

The Proof Store may live in RAM, persistent storage, a trusted service, secure hardware, or a content-addressed store.

### 3.6 Consumption Gate Unit

This is the key architectural boundary.

Before selected instructions or external side effects, the gate checks a policy such as:

```text
require status == PROVEN_TRUE
require authority == payment_policy_v7
require epoch >= current_epoch
require not replayed
```

Failure does not necessarily halt the processor. It denies that protected transition.

## 4. Candidate instruction concepts

The v0.1 ISA is deliberately schematic.

```text
PLOAD      dst, address
PSTORE     address, src
PVERIFY    proof_ref, policy
PASSERT    src, required_state
PINVALIDATE proof_ref
PJOIN      dst, proof_a, proof_b, rule
PGUARD     policy, target_instruction
```

Possible semantics:

### PLOAD

Loads a value and its proof metadata into a register/shadow-register pair.

### PVERIFY

Asks the Proof Verification Unit to validate evidence under the current context.

### PASSERT

Requires an epistemic state before execution proceeds through a protected path.

### PJOIN

Creates or references a derivation joining parent proofs under an allowed rule.

### PGUARD

Binds a policy check to an instruction or side-effect boundary.

## 5. Proof-aware memory hierarchy

```text
CPU registers
    |
    +-- shadow proof status
    |
L1 data cache
    |
    +-- L1 proof metadata cache
    |
L2/L3 data cache
    |
    +-- proof metadata / proof refs
    |
RAM ------------------------+
    |                        |
    +-- data plane           +-- proof plane
                                 |
                                 +-- Proof Store
```

Not every byte must have proof metadata. Memory regions can opt into stronger semantics through page, segment, object, or capability-level configuration.

## 6. Protected side-effect example

Consider releasing a payment.

```text
PB1 = authorization_is_current
PB2 = amount_matches
PB3 = destination_matches
PB4 = request_not_replayed
```

A policy derives:

```text
PB5 = may_release_payment
```

The machine may freely inspect all inputs, but the external release instruction is guarded:

```text
PGUARD require(PB5 == PROVEN_TRUE, fresh, correct_authority)
RELEASE_PAYMENT
```

If `PB5` is `UNKNOWN`, `CONFLICT`, `STALE`, or `REPLAYED`, execution is denied at the protected boundary.

## 7. AI-agent memory example

An agent memory may contain:

```text
"customer approved refund"
```

The value can remain readable to a model while the proof plane marks it:

```text
UNKNOWN
```

A tool call that actually issues the refund can require:

```text
PROVEN_TRUE
+ customer authority
+ current refund-policy epoch
+ unused action token
```

This separates:

```text
memory available for reasoning
```

from:

```text
memory authorized to drive side effects
```

## 8. Failure classes the architecture should expose

A prototype should make these states observable rather than silently collapsing them:

```text
NORMAL
UNKNOWN
CONFLICT
STALE_AUTHORITY
REPLAY
FALSE_SUCCESS
```

`FALSE_SUCCESS` is especially important: successful authorization or dispatch does not itself prove successful external outcome.

## 9. Software-first implementation path

Before custom silicon, the model can be prototyped as:

1. a ProofBit software library
2. shadow metadata for ordinary values
3. a proof store
4. a verifier
5. guarded side-effect APIs
6. a tiny virtual machine with proof-aware instructions
7. FPGA or architectural simulator experiments
8. only then, hardware acceleration candidates

This path lets the semantics be attacked and falsified before hardware cost is incurred.

## 10. Hardware research questions

- How much metadata should be tracked per byte, word, page, object, or capability?
- Which verification operations deserve dedicated hardware?
- How should proof-cache invalidation interact with ordinary cache coherence?
- Can derivation DAGs be compacted without losing auditability?
- What is the minimum state required to prevent replay at the consumption boundary?
- How are authority and epoch changes broadcast efficiently?
- Which workloads gain enough safety or audit value to justify overhead?
- Can proof metadata survive DMA, accelerators, GPUs, NICs, and distributed memory boundaries?

## 11. North-star architecture

The long-term target is a machine where this chain is mechanically inspectable:

```text
Observation
  -> Evidence
  -> ProofCell
  -> Computation
  -> Derivation
  -> Decision
  -> Guarded execution
  -> Outcome
  -> Receipt
```

The processor is not asked to know metaphysical truth. It is asked to preserve a narrower and testable property:

> the machine must not claim stronger justification for a state or side effect than its evidence and derivation actually support.
