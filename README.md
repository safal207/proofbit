# ProofBit

**Proof-native computing primitives for memory and processors.**

> Bits should not only carry values. They should carry the evidence that makes those values usable as trusted state.

ProofBit is an experimental computing model for representing data together with verifiable evidence, provenance, authority, and freshness.

The project starts from a simple distinction:

```text
data != fact
```

A conventional bit stores a value:

```text
0 | 1
```

A ProofBit stores a value together with the basis on which a machine may rely on it:

```text
0^pi | 1^pi
```

where `pi` is verifiable evidence.

Absence of evidence is **not** the same as falsehood. ProofBit therefore separates four epistemic states:

```text
1^pi  PROVEN_TRUE
0^pi  PROVEN_FALSE
?     UNKNOWN
!     CONFLICT
```

## Core model

A minimal ProofBit can be represented as:

```text
PB = <statement, value, proof, provenance, authority, epoch>
```

A value may be consumed as verified state only when its proof validates against the statement, authority, and epoch.

```text
Verify(statement, value, proof, authority, epoch) -> {valid, invalid}
```

This gives the first chain of abstractions:

```text
ProofBit -> ProofCell -> ProofMemory -> ProofProcessor
```

## Why this matters

Modern systems already protect parts of computation with checksums, ECC, permissions, signatures, memory tags, capability systems, secure enclaves, and provenance metadata. ProofBit explores a different unifying question:

> What if the machine tracked not only the value of state, but whether computation is justified in treating that value as established?

That becomes especially interesting for:

- AI-agent memory and tool execution
- financial and smart-contract state transitions
- safety-critical control systems
- distributed systems with stale or conflicting observations
- auditability and deterministic evidence
- proof-aware processor and memory architecture research

## Proof-native memory

A ProofCell conceptually contains:

```text
VALUE
STATUS
PROOF_REF
PROVENANCE
AUTHORITY
EPOCH
```

The proof does not have to be stored inline with every byte. A practical design can separate a normal data plane from a proof plane:

```text
DATA PLANE                  PROOF PLANE
-----------                 ----------------
address -> value            address -> proof_ref
                            proof_ref -> evidence
                            authority / epoch / status
```

This keeps ordinary storage compact while allowing selected state to carry stronger semantics.

## Proof-native processing

A conventional processor computes:

```text
A + B -> C
```

A proof-aware processor could compute:

```text
(A, proof_A) + (B, proof_B) -> (C, derivation_C)
```

The important rule is that confidence cannot silently increase during computation. Unknown, stale, or conflicting inputs must not automatically become verified outputs.

A future ProofProcessor may therefore expose proof-aware operations such as:

```text
PLOAD
PSTORE
PVERIFY
PASSERT
PINVALIDATE
PAND
POR
PCMP
```

and gate sensitive side effects on verified state.

## Example

An AI agent writes:

```text
"The client approved payment."
```

A normal memory store may preserve the sentence without preserving whether it was observed, inferred, or fabricated.

ProofBit would instead distinguish:

```text
statement: client_approved(payment_42)
status:    PROVEN_TRUE
proof:     signed_message_8821
source:    client_identity_key
 epoch:     18432
```

from:

```text
statement: client_approved(payment_42)
status:    UNKNOWN
```

The second value exists as information, but it does not receive the same authority as a verified fact.

## Design principles

1. **No silent promotion** — unverified state cannot become verified merely because it was copied or transformed.
2. **False is not unknown** — `PROVEN_FALSE` requires evidence too.
3. **Conflict is first-class** — contradictory valid evidence is preserved rather than silently collapsed.
4. **Freshness matters** — a once-valid proof may become stale after its authority or epoch changes.
5. **Derivations preserve provenance** — verified outputs must retain a machine-checkable path to the evidence that justified them.
6. **Side effects require stronger grounding than internal computation** — privileged actions should be able to demand verified, fresh authority.

## Repository structure

```text
docs/spec-v0.1.md          Minimal semantic model
docs/architecture-v0.1.md  Memory and processor architecture sketch
docs/roadmap.md            Research and prototype plan
```

## Status

**v0.1 research seed.** This repository defines an experimental model and architecture direction. It is not yet a hardware implementation, a formal proof system, or a claim that every underlying mechanism is novel. The goal is to make the idea precise enough to compare against prior work, simulate, falsify, and eventually prototype.

## Near-term goal

Build the smallest executable ProofBit machine that can demonstrate:

```text
observation
  -> proof-aware memory
  -> derivation
  -> decision
  -> guarded side effect
  -> receipt
```

without allowing `UNKNOWN`, stale authority, replayed evidence, or conflicting evidence to masquerade as verified state.
