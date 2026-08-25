# ProofBit Semantic Model v0.1

## 1. Scope

This document defines the smallest semantic contract for ProofBit. It intentionally avoids committing to a particular cryptographic scheme, ISA, memory layout, or hardware implementation.

The objective is to answer one question precisely:

> When may a machine treat a stored or derived value as established rather than merely present?

## 2. Basic object

A ProofBit is modeled as:

```text
PB = <S, V, Q, Pi, P, A, E>
```

where:

- `S` — statement or proposition being represented
- `V` — Boolean value when known: `0` or `1`
- `Q` — epistemic state
- `Pi` — proof/evidence reference or evidence bundle
- `P` — provenance
- `A` — authority under which the claim may be accepted
- `E` — epoch/freshness domain

## 3. Epistemic states

`Q` is one of:

```text
PROVEN_TRUE
PROVEN_FALSE
UNKNOWN
CONFLICT
```

Interpretation:

### PROVEN_TRUE

The statement is accepted as true because evidence validates under the required authority and epoch.

```text
V = 1
Verify(S, 1, Pi, A, E) = valid
```

### PROVEN_FALSE

The statement is accepted as false because evidence validates under the required authority and epoch.

```text
V = 0
Verify(S, 0, Pi, A, E) = valid
```

### UNKNOWN

The system does not possess sufficient valid evidence to establish either truth or falsehood.

`UNKNOWN` MUST NOT be interpreted as false.

### CONFLICT

The system possesses valid evidence supporting incompatible values under a context that has not yet been resolved.

A conflict MUST NOT be silently collapsed by last-write-wins unless an explicit resolution policy is part of the authority contract.

## 4. Verification function

A verifier is abstractly defined as:

```text
Verify(S, V, Pi, A, E, C) -> VerificationResult
```

where `C` is the current verification context.

A minimal result may distinguish:

```text
VALID
INVALID
STALE
REPLAYED
WRONG_AUTHORITY
WRONG_STATEMENT
```

The exact mechanism may be cryptographic, deterministic, observational, replicated, policy-based, or hybrid.

## 5. Core invariants

### I-1 — No silent promotion

An operation MUST NOT convert `UNKNOWN` into a proven state without introducing sufficient new evidence or a valid derivation from already proven premises.

### I-2 — Proven false requires evidence

Absence of evidence for `S = 1` does not prove `S = 0`.

### I-3 — Statement binding

Evidence valid for one statement MUST NOT establish another statement unless an explicit derivation rule proves the relationship.

### I-4 — Authority binding

Evidence valid under authority `A1` MUST NOT be consumed as if it were authorized under `A2` without a valid rebinding or delegation rule.

### I-5 — Epoch binding

Evidence MUST be evaluated against the freshness domain in which it is consumed. Evidence from an obsolete epoch may become `STALE` without becoming intrinsically false.

### I-6 — Replay resistance

Evidence whose semantics permit only one consumption MUST NOT authorize repeated side effects.

### I-7 — Conflict preservation

If the verifier accepts contradictory evidence that has not been resolved by policy, the resulting state is `CONFLICT`.

### I-8 — Derivation traceability

A derived proven state MUST retain enough information to reconstruct or validate the rule and parent evidence that established it.

## 6. Derivation

A derivation is:

```text
D = <rule, inputs, output_statement, output_value, context>
```

and is valid when:

```text
VerifyDerivation(D, input_proofs) = valid
```

A derived ProofBit may therefore contain a proof reference that points to a derivation DAG rather than to a single external receipt.

Example:

```text
PB1: payment_authorized = PROVEN_TRUE
PB2: balance_sufficient  = PROVEN_TRUE

rule R7:
  PB1 AND PB2 -> payment_may_dispatch = PROVEN_TRUE

PB3.proof -> derivation(R7, PB1.proof, PB2.proof)
```

## 7. Conservative logical propagation

ProofBit logic is evidence-aware rather than merely value-aware.

Examples:

```text
PROVEN_FALSE AND UNKNOWN -> PROVEN_FALSE
```

is permissible when the proof of the false operand alone is sufficient to establish the conjunction as false.

Likewise:

```text
PROVEN_TRUE OR UNKNOWN -> PROVEN_TRUE
```

may be valid when the proven true operand alone establishes the disjunction.

By contrast:

```text
PROVEN_TRUE AND UNKNOWN -> UNKNOWN
PROVEN_FALSE OR UNKNOWN -> UNKNOWN
```

unless additional evidence is introduced.

Any propagation rule MUST emit a derivation showing why the output state is justified.

## 8. ProofCell

A ProofCell is the storage form of one proof-aware value:

```text
PC = <Value, Status, ProofRef, ProvenanceRef, AuthorityRef, Epoch>
```

A practical implementation may keep `Value` in ordinary memory and store the rest in metadata structures.

## 9. Consumption

Reading data and consuming data are distinct operations.

A machine may permit:

```text
READ UNKNOWN
```

for analysis while refusing:

```text
EXECUTE_PRIVILEGED_ACTION UNKNOWN
```

A consumption gate is therefore:

```text
CanConsume(PB, RequiredPolicy, CurrentContext) -> allow | deny
```

This distinction is essential for AI-agent systems: a model may inspect an unverified memory without being allowed to treat it as authority for an external side effect.

## 10. Outcome grounding

A successful decision does not prove that an external side effect occurred.

ProofBit therefore distinguishes at least:

```text
authorization evidence
execution evidence
outcome evidence
```

A terminal success claim MUST be grounded in evidence appropriate to the side effect being claimed.

## 11. Non-goals of v0.1

This version does not define:

- a universal proof language
- a cryptographic standard
- a physical memory cell design
- transistor-level implementation
- a complete processor ISA
- a theorem prover
- a claim of novelty over all adjacent research

Those are later research questions.

## 12. Minimal falsifiable claim

The v0.1 research program should be considered useful only if a prototype can demonstrate that ordinary computation can proceed while selected decisions are prevented from treating stale, replayed, unknown, or conflicting evidence as verified authority.
