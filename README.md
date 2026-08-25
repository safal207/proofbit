# ProofBit

**Proof-aware state and effect-boundary architecture for trustworthy computing.**

> A machine should not treat a value as trusted state without preserving why that value may be relied on for a specific action, authority, context, and moment in time.

ProofBit is an executable research project for binding data and actions to explicit trust semantics:

```text
statement
+ epistemic state
+ authority
+ epoch / freshness
+ provenance
+ replay identity
+ execution context
+ observed outcome
```

The core distinction is:

```text
data != established fact

authorized dispatch != proven outcome
```

## Status

**v0.1 research release candidate.**

The repository now includes:

- a dependency-free Python semantic model;
- deterministic adversarial benchmarks;
- crash/recovery and durable-corruption fixtures;
- Python/Rust/Node conformance tests;
- OS privilege and effect-boundary experiments;
- executable ISA/memory attack models;
- synthesizable Verilog;
- Icarus simulation;
- Yosys Xilinx-7 structural mapping;
- explicit positive, negative, and still-open claims.

This is no longer only a concept sketch. It is also **not** a production processor, a cryptographic proof system, a formal proof of universal safety, or evidence that ProofBit is faster than CPUs, GPUs, TPUs, Cerebras, or other AI accelerators.

Start with:

- [`CLAIMS.md`](CLAIMS.md) — what is established, rejected, and still open;
- [`NEGATIVE_RESULTS.md`](NEGATIVE_RESULTS.md) — results that narrowed or falsified stronger claims;
- [`BENCHMARK_MATRIX.md`](BENCHMARK_MATRIX.md) — the executable evidence map;
- [`POSITIONING.md`](POSITIONING.md) — how ProofBit relates to capabilities, tagged memory, attestation, and verifiable computing;
- [`COMMERCIAL_WEDGE.md`](COMMERCIAL_WEDGE.md) — the near-term product and revenue path;
- [`docs/roadmap.md`](docs/roadmap.md) — the engineering and go/no-go plan.

## Honest positioning

The closest current description is:

> **ProofBit is a proof-aware capability/evidence architecture for binding state, authority, freshness, provenance, replay, and outcome at a machine-enforced effect boundary.**

The benchmark program has repeatedly shown that strong conventional software, capability systems, tagged architectures, indexed logs, canonical contracts, and reference monitors can reproduce many individual ProofBit guarantees.

Therefore the project does **not** claim that ordinary systems are incapable of implementing these checks.

The remaining research question is narrower and more useful:

> Can a standard proof-aware state and action contract reduce integration, composition, recovery, audit, or trusted-computing-base cost enough to justify a dedicated runtime, coprocessor, memory primitive, or ISA extension?

## Core semantics

A minimal logical ProofBit is:

```text
PB = <statement, state, evidence_ref, provenance, authority, epoch, context, identity>
```

Canonical epistemic states include:

```text
PROVEN_TRUE
PROVEN_FALSE
UNKNOWN
CONFLICT
STALE
REPLAYED
INVALID
```

Absence of evidence is not falsehood. Authorization is not outcome. A value may remain readable for reasoning while being forbidden from driving a protected side effect.

The architectural chain is:

```text
ProofBit
  -> ProofCell
  -> ProofMemory
  -> ProofProcessor
  -> mandatory effect boundary
  -> outcome evidence
  -> receipt
```

A practical design does not need to widen every physical bit. The current architecture uses a dual-plane model:

```text
DATA PLANE                  PROOF PLANE
-----------                 -------------------------
values                      statement / state
registers                   evidence references
ordinary caches             authority / epoch
ordinary memory             provenance / context
                            replay / outcome receipts
```

## What v0.1 has established

The strongest results are architectural rather than brand-specific:

| Finding | Executable evidence |
|---|---|
| Validation separated from execution is bypassable | Application-only validation failed direct-call, stale-cache, replay, rebinding, and false-success cases |
| Mandatory enforcement at the authoritative effect seam works | Conventional reference monitor and ProofBit both closed the frozen bypass set |
| Canonical contracts reduce policy drift and release coordination | Shared conventional descriptors and ProofBit matched across Python, Rust, and Node |
| Rich trust semantics have measurable RTL cost | Full evidence semantics required substantially more LUT/FF/state than a minimal capability |
| A four-parent composition primitive is useful | `6 -> 2` instruction transactions and `4 -> 1` parent-read issue cycles versus scalar composition |
| Physical parallel evidence access is not free | Four-read cached designs paid 4x logical evidence storage |
| Caching reduces composition latency | Warm four-parent composition reached 1 cycle in the frozen RTL fixture |
| Generic capability/cache benefits are not unique to ProofBit | Equally expressive conventional controls repeatedly matched ProofBit |

See [`BENCHMARK_MATRIX.md`](BENCHMARK_MATRIX.md) and [`NEGATIVE_RESULTS.md`](NEGATIVE_RESULTS.md).

## Benchmark discipline

Every architecture is evaluated on separate axes:

```text
Utility
Proof
Cost
Speed
```

The north-star metric is:

```text
Trusted Useful Throughput
  = correctly permitted useful actions with sufficient evidence
    / end-to-end second
```

Comparison order:

```text
semantic coverage
-> correctness and safety inside that coverage
-> evidence / audit quality
-> cost and speed
```

Raw throughput is not ranked across unlike workloads. Unsupported semantics are reported as unassessed, never counted as prevented. Strong conventional anti-strawman controls are mandatory.

## Research track

The remaining hardware work is deliberately short and decisive:

1. **PB-HW-05 — Atomic Data + Evidence**  
   Compare sidecar evidence memory, strong atomic tagged memory, and an integrated ProofBit cell under torn updates, rollback, DMA modification, and cache eviction.

2. **PB-HW-06 — Root of Trust / Authenticity**  
   Define who may mint evidence, how epochs remain monotonic, how rollback is blocked, and how device attestation binds to action and outcome receipts.

3. **ProofBit-FPGA-01 — Board demonstrator**  
   Measure real place-and-route fit, Fmax, latency, utilization, and an end-to-end guarded action on physical FPGA hardware.

If strong conventional tagged memory again matches ProofBit and no system-level advantage appears, the hardware thesis will be narrowed to a protocol/runtime/conformance product rather than forced into a processor claim.

## Commercial track

The near-term product is **not a chip**.

The commercial wedge is a proof-carrying action guard for consequential AI-agent operations:

```text
agent intent
-> authority and policy evidence
-> exact request binding
-> ACCEPT / REJECT / HOLD
-> guarded execution
-> observed outcome
-> independently verifiable receipt
```

Initial workflows:

- production deployment;
- IAM and infrastructure changes;
- wallet and agentic-payment operations;
- smart-contract administration;
- critical automation and release actions.

See [`COMMERCIAL_WEDGE.md`](COMMERCIAL_WEDGE.md).

## Quick start

Python reference tests:

```bash
python -m unittest discover -s tests -v
```

Example trust-fault benchmark:

```bash
python benchmarks/pb_transition_03.py --json
```

RTL tools on Ubuntu/Debian:

```bash
sudo apt-get install -y iverilog yosys
python benchmarks/pb_hw_04.py --json
```

Dedicated GitHub Actions workflows freeze the important benchmark oracles and resource mappings.

## Repository map

```text
proofbit/                      semantic reference model
benchmarks/                    executable software, IPC, ISA, and RTL benchmarks
rtl/                           synthesizable ProofBit research RTL and testbenches
tests/                         regression and anti-strawman assertions
docs/                          specifications, methodology, results, and roadmap
.github/workflows/             reproducible benchmark jobs
```

Architecture details:

- [`docs/spec-v0.1.md`](docs/spec-v0.1.md)
- [`docs/architecture-v0.1.md`](docs/architecture-v0.1.md)

## Claim discipline

ProofBit uses a claim ledger rather than marketing-by-benchmark:

```text
ESTABLISHED
SUPPORTED BUT LIMITED
NOT ESTABLISHED
OPEN HYPOTHESIS
```

Negative results are first-class project output. If a conventional design reproduces a benefit, the benefit is attributed to the shared architecture, not renamed as a ProofBit win.

The long-term objective remains:

```text
Utility up
Proof up
Cost down
Speed up
```

but only where the evidence supports it.
