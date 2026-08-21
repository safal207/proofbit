# PB-TRUST-COMPOSE-07 results

Protocol: `PB-TC07/v0.1 cross-language-conformance`.

Official GitHub Actions evidence:

- run `32478612985`;
- job `96760035396`;
- Ubuntu 24.04.4;
- CPython 3.12.14;
- Node 22.23.2;
- rustc 1.98.0;
- 14 frozen conformance cases;
- 1,000 repetitions per case;
- 11 rotated-order rounds.

## Correctness

All three compared systems, in all three language runtimes, matched the frozen oracle:

```text
oracle accuracy              = 100%
unsafe accepts               = 0
missed valid                 = 0
cross-language disagreements = 0
```

This includes the valid statement ID `0xFEDCBA9876543210`, which is above JavaScript's safe integer range. The Node validator preserves it with `BigInt`.

The fault set rejected unknown versions/bits, digest mismatch, little-endian re-encoding, an old v4 token, replay/provenance/outcome omissions, authority/epoch mismatch, reserved-field mutation, trailing bytes and truncation.

## Runtime medians

The metric counts individual language validations across Python + Rust + Node and includes process/file I/O in this software fixture.

| System | Median language validations/s | Median elapsed |
| --- | ---: | ---: |
| `software_per_language` | **278,572/s** | **150.769 ms** |
| `software_canonical_contract` | 262,157/s | 160.210 ms |
| `proofbit_contract` | 264,666/s | 158.691 ms |

ProofBit / canonical conventional throughput is about `1.0096x` (~+1.0%). This is small relative to ordinary runner/process noise and is not treated as a stable speed advantage. The manual per-language path is also faster in this run; TC07 makes no runtime-winner claim.

## Evolution / update surface

For four policy transitions across three languages:

| Metric | Per-language software | Canonical software | ProofBit |
| --- | ---: | ---: | ---: |
| Managed policy sources | 3 | **1** | **1** |
| Validator-source updates | 12 | **0** | **0** |
| Descriptor updates | 0 | **4** | **4** |
| Language conformance invocations | **12** | **12** | **12** |
| Wire token | **56 B** | **56 B** | **56 B** |
| Policy descriptor | embedded | **16 B** | **16 B** |

The strongest conventional canonical control exactly reproduces ProofBit's frozen update surface and representation size. Therefore the reduction from 12 per-language validator updates to four descriptor updates is a canonical-contract architecture benefit, not uniquely a ProofBit result.

Crucially, canonicalization does **not** remove cross-language regression work: all systems still require 12 language-level conformance invocations in the frozen v1->v5 evolution model.

## Main negative result

A competent conventional canonical binary contract with strict version/digest/binding checks reproduces ProofBit's cross-language correctness, representation size, and frozen policy-update surface in TC07.

The evidence-supported statement is narrower:

> A canonical version-bound trust contract prevents Python/Rust/Node semantic drift across the tested integer-width, byte-order, version and evidence-presence boundaries. ProofBit can make that contract a native proof abstraction, but TC07 does not show a unique correctness, cost, or speed advantage over an equally canonical conventional design.

## What remains untested

TC07 does not model real separate code owners, independently released SDKs/packages, stale dependency graphs, generated-code drift, network transport, cryptographic authenticity or heterogeneous hardware boundaries.

The next falsifiable experiment should therefore move from one repository/one CI runner to **release skew**: independently versioned artifacts with delayed upgrades and a compatibility window. The strong conventional control remains a canonical schema/contract with generated or runtime validators.
