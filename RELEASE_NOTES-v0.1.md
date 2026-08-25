# ProofBit v0.1 Release Notes

## Release type

**Research release candidate.**

ProofBit v0.1 consolidates the full software-to-RTL investigation into one reviewable branch. It is not a production processor release.

## What is included

### Semantic core

- explicit epistemic states;
- statement/action binding;
- authority and epoch/freshness binding;
- provenance and execution context;
- consume-once replay identity;
- separate authorization and outcome evidence;
- guarded side-effect model.

### Software and systems evidence

- deterministic trust-fault workloads;
- real same-host IPC;
- dynamic revocation;
- hard process crash/restart;
- durable indexed receipts;
- corruption and repair fixtures;
- policy evolution and release skew;
- Python/Rust/Node conformance;
- application and OS privilege-bypass tests;
- bounded ISA attacker search;
- whole-system CPU/debug/DMA/context/cache/rollback model.

### Hardware research evidence

- synthesizable Verilog;
- Icarus simulation;
- Yosys Xilinx-7 structural mapping;
- equal-semantics capability versus ProofBit comparison;
- semantic cost curve;
- scalar versus four-parent composition primitive;
- physical single-port, banked, and replicated cached evidence memory.

## Most important positive findings

1. Mandatory enforcement at the actual effect boundary closes bypasses that application-only validation misses.
2. Canonical version-bound contracts reduce cross-language and release-policy drift.
3. Indexed receipt chains dramatically reduce targeted audit work.
4. Rich trust semantics have measurable software and hardware cost.
5. A dedicated four-parent composition primitive reduces instruction issue work.
6. Physical multi-read evidence caches reduce latency but require real memory replication.

## Most important negative findings

1. Competent conventional software can implement the frozen ProofBit trust rules.
2. Strong conventional reference monitors match ProofBit effect-boundary safety.
3. Tagged/capability machines match ProofBit in the frozen ISA and whole-system safety models.
4. Equal-semantics conventional and ProofBit RTL maps identically.
5. Conventional `COMPOSE4` matches ProofBit `COMPOSE4`.
6. Equal physical conventional and ProofBit evidence caches match across latency and mapped resources.
7. Current evidence does not establish a unique speed, area, energy, or security moat for ProofBit hardware.

## PB-HW-04 release result

Final frozen Xilinx-7 structural mapping:

| Metric | Single-port | Banked | Conventional cache | ProofBit cache |
|---|---:|---:|---:|---:|
| Cold cycles | 4 | 2 | 2 | 2 |
| Warm cycles | 4 | 2 | 1 | 1 |
| Same-bank cold cycles | 4 | 5 | 2 | 2 |
| RAMB36 | 2 | 4 | 8 | 8 |
| LUT | 6,966 | 7,645 | 10,213 | 10,213 |
| FF | 1,286 | 1,335 | 2,148 | 2,148 |
| Core cells excluding I/O | 8,943 | 10,018 | 13,213 | 13,213 |
| Logic-depth proxy | 36 | 59 | 100 | 100 |

Functional oracle: `52 checks / 0 failures`.

## Positioning change

Previous broad framing:

```text
new processor that stores values with proof
```

Current evidence-based framing:

```text
proof-aware capability/evidence architecture
for consequential action and outcome boundaries,
software-first with a measured coprocessor research path
```

## Commercial direction

The initial product is **ProofPath Deployment Guard / Proof-Carrying Action Guard**, not a chip.

The pilot unit is one consequential AI-agent workflow with:

- exact request and artifact binding;
- authority and policy checks;
- mandatory gateway enforcement;
- replay/freshness/provenance tests;
- execution and outcome receipts;
- offline verification;
- retained regression fixtures.

## Next research gates

- PB-HW-05 — atomic data + evidence;
- PB-HW-06 — root of trust and authenticity;
- ProofBit-FPGA-01 — physical board demonstrator.

Hardware work continues only if a measurable advantage survives an equally strong conventional control.

## Review request

Reviewers should focus on:

- anti-strawman fairness;
- claim boundaries;
- capability/tagged-memory prior art;
- RTL memory inference and resource accounting;
- atomic data/evidence hypothesis;
- action/outcome usefulness in real AI-agent systems;
- missing threat boundaries.
