# ProofBit Claim Ledger — v0.1

This file is the canonical boundary between what the repository has established, what it merely suggests, what repeated experiments have rejected, and what remains open.

## Status labels

- **ESTABLISHED** — directly supported by a frozen executable benchmark or RTL synthesis in this repository.
- **SUPPORTED, LIMITED** — supported inside a defined fixture, but not generalized beyond it.
- **NOT ESTABLISHED** — the repository does not contain sufficient evidence for the claim.
- **REJECTED IN CURRENT FORM** — a stronger claim was contradicted by a competent control.
- **OPEN HYPOTHESIS** — intentionally unresolved and tied to a future falsifiable experiment.

## Established claims

### C1 — Epistemic states must remain distinct

**ESTABLISHED as a software contract.**

The reference model and regression suite distinguish:

```text
PROVEN_TRUE
PROVEN_FALSE
UNKNOWN
CONFLICT
STALE
REPLAYED
INVALID
```

The project does not silently equate missing evidence with falsehood or successful authorization with successful outcome.

### C2 — Exact statement/action binding is necessary

**ESTABLISHED in the frozen rebinding tests.**

A proof or authorization for action A must not authorize action B. Statement binding must be checked before consume-once evidence is burned.

### C3 — Enforcement must occur at the authoritative side-effect seam

**ESTABLISHED in the TC09/TC10 fixtures.**

A competent validator on a normal application path can still be bypassed by alternate entrypoints, cached approvals, replayed dispatches, direct calls, inherited handles, or same-privilege resource access.

A mandatory reference monitor at the only authoritative effect boundary closed every frozen unprivileged bypass. ProofBit closed the same set.

### C4 — Canonical trust contracts reduce semantic drift and release coordination

**ESTABLISHED inside the TC06–TC08 ownership and release fixtures.**

A single version-bound descriptor plus generic validators reduced policy-copy updates and preserved cross-language agreement across Python, Rust, and Node.

The benefit was reproduced by conventional canonical software and therefore is not unique to ProofBit.

### C5 — Indexed receipt chains reduce targeted audit work

**ESTABLISHED in TC04.**

For the frozen crash/recovery workload, a durable head index reduced targeted audit inspection from 45,000 records to 90 records.

Conventional indexed software and ProofBit used the same work and storage, so the gain belongs to the indexed-chain topology.

### C6 — Rich trust semantics have measurable hardware cost

**ESTABLISHED in PB-HW-02.**

Adding epistemic state, provenance, execution context, and separate outcome evidence to the minimal capability increased metadata/state and mapped RTL resources substantially in the frozen design.

An equally expressive conventional full-evidence design paid exactly the same cost.

### C7 — A dedicated multi-parent composition primitive reduces issue work

**ESTABLISHED in PB-HW-03.**

Compared with a scalar `PARENT x4 -> COMPOSE -> OUTCOME` engine, a four-parent composition primitive reduced:

```text
instruction transactions: 6 -> 2
parent-read issue cycles:  4 -> 1
```

without reducing logical parent reads or logical writes.

A conventional `COMPOSE4` primitive and ProofBit `COMPOSE4` mapped identically.

### C8 — Parallel evidence-memory access has a physical cost

**ESTABLISHED in PB-HW-04.**

The frozen four-read cached architecture used four replicated `1024 x 64` evidence tables, paying 4x logical evidence storage versus the single-port and banked baselines.

It reduced warm four-parent composition to 1 cycle and avoided the 5-cycle same-bank conflict of the banked design.

The conventional and ProofBit cached designs were structurally identical.

## Supported but limited claims

### L1 — ProofBit is a useful semantic reference model

**SUPPORTED, LIMITED.**

The model has repeatedly exposed ambiguous states, rebinding gaps, false-success assumptions, replay problems, and enforcement-placement errors. This demonstrates research and QA value, not production completeness.

### L2 — Proof-native representation may reduce repeated trust plumbing

**SUPPORTED, LIMITED by TC01 only.**

ProofBit outperformed a deliberately explicit field-by-field serialized trust envelope as boundary depth increased. A stronger shared immutable software envelope remained faster, and real IPC with identical compact encoding did not produce a stable ProofBit speed win.

### L3 — Proof-aware coprocessing is technically feasible

**SUPPORTED, LIMITED by synthesizable reference RTL.**

PB-HW-01 through PB-HW-04 synthesize and simulate. This does not establish place-and-route timing, FPGA-board operation, ASIC PPA, power, or production viability.

## Claims rejected in their stronger form

### R1 — “Ordinary software cannot implement ProofBit guarantees”

**REJECTED IN CURRENT FORM.**

Competent conventional controls repeatedly matched the frozen correctness and safety oracle.

### R2 — “ProofBit is inherently faster than conventional trust software”

**REJECTED IN CURRENT FORM.**

Compact software, lazy software, indexed recovery, and capability/reference-monitor controls were often equal or faster in the current implementations.

### R3 — “A ProofBit tag is inherently cheaper than a capability tag”

**REJECTED IN CURRENT FORM.**

With normalized semantics and topology, Yosys mapped the capability and ProofBit RTL identically.

### R4 — “Canonical contracts, indexed logs, or multi-read caches are uniquely ProofBit”

**REJECTED IN CURRENT FORM.**

Strong conventional controls reproduced every measured benefit.

### R5 — “ProofBit is already a new general-purpose processor competing with GPU/TPU/Cerebras”

**REJECTED AS CURRENT POSITIONING.**

The repository contains trust/action-boundary research, not competitive model-training or inference silicon.

## Not established

The repository does **not** currently establish:

- lower energy or power than conventional designs;
- better placed-and-routed timing;
- an ASIC area advantage;
- cryptographic authenticity of every proof reference;
- resistance to malicious firmware or physical tag-store tampering;
- full speculative-execution safety;
- complete cache-coherence or IOMMU integration;
- superiority over CHERI-like capability architectures;
- universal AI-agent safety;
- formal verification of the whole design;
- patent novelty;
- production reliability;
- customer willingness to pay;
- any performance ranking against NVIDIA, Google TPU, Cerebras, AMD, AWS Trainium, or future OpenAI accelerators.

## Open hypotheses

### H1 — Atomic data + evidence may reduce torn-state risk or transaction cost

Future experiment: **PB-HW-05**.

Compare:

1. sidecar data and evidence writes;
2. strong conventional atomic tagged memory;
3. integrated ProofBit atomic cell.

Attack crash-between-writes, torn update, DMA mutation, cache eviction, stale-proof/new-data, new-proof/stale-data, rollback, and snapshot replay.

ProofBit earns a hardware-specific result only if it improves unsafe windows, transactions, recovery work, or mapped cost relative to an equally strong conventional atomic tagged design.

### H2 — A proof-aware root of trust may bind attestation to action and outcome

Future experiment: **PB-HW-06**.

Define who may mint evidence, how epochs remain monotonic, how rollback is blocked, and how device identity/attestation binds authorization and outcome receipts.

### H3 — A small proof-aware coprocessor may be practical on real FPGA hardware

Future experiment: **ProofBit-FPGA-01**.

Required evidence:

- place-and-route success;
- named FPGA target;
- real Fmax;
- measured latency;
- utilization;
- stable host interface;
- end-to-end valid/stale/replay/rebind/outcome demonstration.

### H4 — Customers may pay for proof-carrying action assurance before hardware exists

Commercial experiment: one production-deploy or agentic-action pilot with explicit willingness-to-pay, intercepted faults, audit-time reduction, false-block rate, and reusable receipts.

## Go / no-go rules

Continue the hardware thesis only if at least one of PB-HW-05, PB-HW-06, or ProofBit-FPGA-01 produces a measurable system-level advantage that a strong conventional control does not reproduce at equal cost.

If not, preserve the useful result and narrow the project to:

```text
canonical proof-carrying action protocol
+ conformance suite
+ adversarial benchmark corpus
+ deployment/action guard
```

That outcome is a valid product and research result, not a failure.
