# PB-TRUST-COMPOSE-11 — ISA / Memory Enforcement

## Question

After TC09/TC10 showed that mandatory software + OS boundaries can reproduce ProofBit safety until their privilege boundary is bypassed, TC11 asks a lower-level question:

> If authorization is made a mandatory property of the machine's `EFFECT` instruction and memory-carried authority is protected by an unforgeable tag, does ProofBit show a unique advantage over a strong conventional tagged/capability machine?

A tie is a valid negative result.

## Compared machines

### `flat_value_machine`

A value-only control. An authorization-like object is ordinary mutable data. The effect instruction trusts its `allow` value and does not enforce an unforgeable authority tag, action binding, epoch freshness, or consume-once nonce semantics.

This is a baseline, not the primary competitor.

### `tagged_capability_machine`

The strongest conventional anti-strawman.

A tagged capability contains logical authority fields:

```text
tag
action
issuer
epoch
nonce
```

The `EFFECT` instruction itself checks all of them. The tag cannot be created or preserved by ordinary unprivileged field mutation or raw reconstruction. A copied valid capability preserves its tag, but consume-once nonce state blocks replay.

### `proofbit_machine`

A proof-tagged memory reference using the repository's actual `ProofProcessor` / `Evidence` path.

Logical proof authority includes:

```text
tag
statement
authority
epoch
proof_id
provenance
```

`EFFECT` requires a valid proof tag, exact `expected_statement` binding, matching authority, current epoch, nonzero provenance, and consume-once proof id.

## Attacker ISA

The bounded unprivileged search enumerates every instruction sequence up to the configured maximum length over:

```text
FORGE
MUTATE_B
MUTATE_EPOCH
RAW_ROUNDTRIP
CLONE
SWAP
EFFECT_A
EFFECT_B
```

This is exhaustive over this frozen instruction alphabet and bounded program length. It is **not** a proof over all possible ISAs or arbitrary-length programs.

## Frozen attack scenarios

```text
FORGE_NO_AUTH
REBIND_VALID_A_TO_B
STALE_AFTER_EPOCH
REPLAY_CONSUMED
DUPLICATE_ONE_AUTH
RAW_RECONSTRUCTION
```

The official run searches programs up to length 5.

With 8 attack opcodes:

```text
8 + 8^2 + 8^3 + 8^4 + 8^5 = 37,448 programs/scenario
37,448 * 6 scenarios = 224,688 programs/system
```

## Tag axiom

The central TC11 assumption is explicit:

> Ordinary unprivileged `FORGE`, field mutation, and `RAW_ROUNDTRIP` cannot mint or preserve the authority tag of either strong machine.

This is a **model axiom**. It is not measured silicon behavior.

The conventional capability machine receives exactly the same strength of tag-unforgeability assumption as ProofBit. Therefore a tie is expected if proof-specific semantics add no safety advantage inside the frozen scenario set.

## Mutation semantics

For either tagged machine:
- `CLONE` preserves an existing valid tag;
- `MUTATE_B` clears the tag;
- `MUTATE_EPOCH` clears the tag;
- `RAW_ROUNDTRIP` clears the tag;
- `FORGE` produces an untagged object.

Copied tagged authority is still not infinitely reusable: nonce/proof-id consumption is tracked globally by the machine.

## Privileged / debug / DMA escape classes

TC11 also contains explicit **unscored** escape probes:

```text
DEBUG_EFFECT
DMA_EFFECT
PRIVILEGED_MINT
```

They bypass the ordinary unprivileged enforcement model.

All machines are expected to permit these escape probes in TC11 because they are defined outside the scored user-mode ISA.

This is intentional. If ProofBit only protects ordinary CPU instructions while debug, DMA, or privileged tag minting can bypass the boundary, the remaining hypothesis moves deeper toward whole-system tag enforcement, IOMMU/device integration, privilege design, or physical hardware.

## Metrics

### Safety
- exhaustive bounded programs tested;
- bypass-producing programs;
- shortest bypass length;
- bypass examples;
- scenarios with at least one bypass.

### Speed
- median valid effects/second over rotated-order rounds;
- exact raw per-round rates.

Runtime is Python reference-model throughput only.

### Cost / representation
The report records **logical metadata fields**, not physical bits or chip area.

No packed hardware representation is claimed.

## Anti-strawman rule

The primary comparison is:

```text
tagged_capability_machine
vs
proofbit_machine
```

Not:

```text
flat machine
vs
ProofBit
```

Any safety result reproduced by the tagged capability machine is a lower-level mandatory-tag architecture benefit, not uniquely a ProofBit result.

## Falsifiers

ProofBit does not show unique TC11 safety value if the conventional tagged capability machine yields zero bypass programs across the same exhaustive bounded search, preserves the same valid-path availability, and only differs in proof vocabulary rather than enforcement power.

A ProofBit-specific result would require a frozen scenario that passes the conventional tagged/capability checks but is rejected correctly by proof semantics without weakening the conventional control.

## Claim boundary

TC11 is executable, deterministic for safety search, exhaustive only over the frozen 8-opcode alphabet and configured bounded program length, and a Python ISA/memory reference model.

TC11 is **not** RTL, cycle accurate, a cache/coherence model, a speculative-execution model, cryptographic verification, a physical tag-storage experiment, a DMA/IOMMU implementation, transistor/area/energy evidence, a novelty or patentability analysis, or evidence of universal hardware superiority.
