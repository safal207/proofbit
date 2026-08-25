# ProofBit Roadmap — post-v0.1

## Strategic decision

ProofBit now has enough software, systems, ISA, and RTL evidence to stop expanding horizontally through an endless sequence of wrappers.

The project moves on two parallel tracks:

```text
COMMERCIAL TRACK
ProofPath action assurance -> paid pilots -> recurring product

RESEARCH TRACK
PB-HW-05 -> PB-HW-06 -> FPGA board demonstrator -> hardware go/no-go
```

The software product must not wait for a chip. The hardware thesis must not be kept alive by marketing if strong conventional controls continue to match it.

## Completed frontier

### Semantic and software model — complete for v0.1

- [x] `PROVEN_TRUE`, `PROVEN_FALSE`, `UNKNOWN`, `CONFLICT`, `STALE`, replay and invalid states
- [x] statement/action binding
- [x] authority and epoch binding
- [x] consume-once evidence
- [x] separate authorization and outcome evidence
- [x] guarded side-effect model
- [x] proof cache experiments

### Distributed and durable systems — complete for v0.1

- [x] real IPC transport
- [x] dynamic revocation
- [x] replay and rebinding across boundaries
- [x] hard process crash and restart
- [x] indexed audit reconstruction
- [x] durable corruption and safe repair
- [x] policy evolution and release skew
- [x] Python/Rust/Node conformance

### Enforcement and TCB — complete for v0.1

- [x] application-validation bypass
- [x] mandatory software reference monitor
- [x] POSIX resource/privilege boundary
- [x] bounded attacker ISA model
- [x] CPU/debug/DMA/context/cache/rollback coherence model

### RTL and memory economics — complete through PB-HW-04

- [x] synthesizable equal-semantics capability/ProofBit pipelines
- [x] rich semantic cost curve
- [x] scalar versus four-parent composition primitive
- [x] physical single-port, banked, and replicated cached evidence memories
- [x] Icarus functional simulation
- [x] Yosys Xilinx-7 structural mapping
- [x] frozen negative-result discipline

## Immediate milestone — v0.1 release consolidation

Goal: turn the stacked research history into one reviewable release candidate.

- [x] create `release/proofbit-v0.1` from the clean PB-HW-04 head
- [x] add canonical claim ledger
- [x] add negative-results ledger
- [x] add benchmark matrix
- [x] add technical positioning
- [x] add commercial wedge
- [x] update project roadmap and README
- [ ] complete final release-branch CI
- [ ] obtain external review
- [ ] merge one release PR into `main`
- [ ] mark stacked PRs as superseded only after the release PR is accepted
- [ ] tag `v0.1.0`

Do not merge automatically. Do not close the research PRs before the consolidated release is safely represented in `main`.

## Track A — commercial product

### A1. Canonical deployment/action contract

Deliver:

```text
Action Request
Evidence Manifest
Policy Pack
ACCEPT / REJECT / HOLD
Permit / Clearance
Execution Receipt
Offline verifier
```

Exit criteria:

- schemas are versioned;
- exact request and artifact binding are enforced;
- state/epoch drift invalidates the permit;
- replay cannot execute twice;
- outcome is independent from dispatch;
- one demo fixture is reproducible outside the repository author’s machine.

### A2. First production-deploy pilot

Scope:

- one repository;
- one deployment workflow;
- one environment;
- one policy pack;
- one mandatory gateway;
- six to twelve frozen fault scenarios.

Exit criteria:

- first paid design partner;
- unsafe injected actions executed = 0;
- false-block and HOLD rates measured;
- audit/reconstruction time measured before and after;
- customer receives a portable evidence package.

### A3. Repeatable assurance product

- standard adapters;
- managed policy and evidence ingestion;
- certificate/receipt registry;
- dashboard and audit export;
- continuous trust regression;
- usage and subscription billing.

Exit criteria:

- at least two paid pilots;
- at least one recurring customer;
- installation no longer depends on bespoke founder intervention;
- buyer renews based on workflow value rather than research novelty.

## Track B — decisive hardware experiments

### PB-HW-05 — Atomic Data + Evidence

Question:

> Does making value and evidence one atomic visible state reduce transactions, torn windows, repair work, or hardware cost relative to an equally strong conventional atomic tagged-memory design?

Compared systems:

1. sidecar data and evidence memory;
2. strong conventional atomic tagged cell;
3. ProofBit atomic cell.

Frozen attacks:

```text
CRASH_BETWEEN_DATA_AND_EVIDENCE
TORN_UPDATE
NEW_DATA_STALE_PROOF
STALE_DATA_NEW_PROOF
DMA_DATA_ONLY_WRITE
CACHE_EVICTION_DURING_UPDATE
ROLLBACK
SNAPSHOT_REPLAY
```

Metrics:

- unsafe visible states;
- atomic transactions per trusted update;
- recovery scan/write work;
- metadata bits;
- LUT / FF / BRAM;
- cycles and stalls;
- rollback state;
- conventional-versus-ProofBit structural equality.

Go criterion:

- a measurable advantage survives an equally strong conventional atomic tagged control.

No-go criterion:

- conventional atomic tagged memory reproduces all safety and economics.

### PB-HW-06 — Root of Trust / Authenticity

Question:

> Who is allowed to mint trusted evidence, and how is freshness preserved against rollback, malicious firmware, and stale device state?

Required components:

- measured implementation identity;
- proof/evidence mint authority;
- monotonic epoch or rollback-resistant counter;
- receipt signature abstraction;
- device/action/outcome binding;
- firmware update and revocation model;
- explicit trust-root compromise boundary.

Compared systems:

1. software-signed receipts;
2. conventional hardware attestation + capability enforcement;
3. ProofBit action/outcome attestation contract.

The goal is not to replace attestation. It is to determine whether ProofBit contributes a useful action-semantic layer above it.

### ProofBit-FPGA-01 — physical demonstrator

Target:

A small coprocessor profile, not a general-purpose CPU replacement.

Minimal demo:

```text
host sends action + evidence
-> FPGA checks statement / authority / epoch / replay / context
-> valid action emits authorized effect token
-> stale / replay / rebind are blocked
-> separate outcome is accepted or rejected
-> receipt returned to host
```

Required measurements:

- named board and FPGA;
- toolchain and constraint files;
- place-and-route success;
- Fmax;
- end-to-end latency;
- LUT / FF / BRAM utilization;
- stable host ABI;
- repeated valid throughput;
- fault-vector behavior;
- board power observation if practical.

Exit criterion:

> One reproducible physical profile fits, meets timing, and performs an end-to-end guarded action against the software oracle.

## External review gate

Before making strong hardware or novelty claims, obtain at least three independent reviews:

1. capability / hardware-security reviewer;
2. FPGA / RTL implementation reviewer;
3. AI-agent runtime or platform-security reviewer.

Review questions:

- Which semantics are genuinely additional to capabilities/tagged memory?
- Are anti-strawman controls strong enough?
- Are memory/RTL mappings measured correctly?
- Is the action/outcome distinction useful in real systems?
- Where can the mandatory boundary still be bypassed?
- Is any claimed novelty already present in prior art?

## Product / hardware decision matrix

| Outcome | Decision |
|---|---|
| Paid software pilots succeed; hardware shows no unique advantage | Build ProofPath protocol/runtime/conformance business; keep ProofBit as research core |
| Paid pilots succeed; atomic/root/FPGA hardware shows clear advantage | Pursue coprocessor/IP design partnerships in parallel |
| Hardware is interesting but customers do not pay for action assurance | Pause product expansion; seek research grant or OEM partner only |
| Neither customers nor decisive benchmarks show value | Archive the broad processor thesis and preserve the benchmark corpus |

## Hard stop rules

Stop creating new benchmark families when they only rename a conventional mechanism.

Do not proceed to ASIC claims before:

- physical FPGA demonstration;
- real workload and buyer demand;
- placed/routed timing;
- measured power/energy evidence;
- stable ISA/ABI;
- explicit root of trust;
- independent review.

Do not promise financial coverage, absolute safety, or cryptographic guarantees that the implementation does not provide.

## 30 / 60 / 90-day operating plan

### First 30 days

- consolidate and review v0.1;
- freeze one deployment policy;
- ship offline verifier and short demo;
- contact 30 relevant design partners;
- open PB-HW-05 specification before coding;
- obtain one hardware-security review.

### Days 31–60

- close first paid pilot;
- execute PB-HW-05 with strong conventional control;
- begin root-of-trust threat model;
- select FPGA board/profile;
- define host ABI.

### Days 61–90

- complete two or three pilots;
- convert one customer to recurring assurance;
- finish PB-HW-06 architecture;
- attempt FPGA place-and-route;
- publish a decision memo: product-only, coprocessor path, or stop.

## Final north star

The project succeeds if it produces either or both of these outcomes:

```text
A useful proof-carrying action assurance product
```

```text
A measured proof-aware hardware primitive that earns its physical cost
```

It does not need to become a universal processor to create value.
