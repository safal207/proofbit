# PB-HW-02 Methodology — Semantic Cost Curve

## Question

What is the structural RTL cost of moving from a minimal authorization capability to a full trust/evidence contract, and does ProofBit reduce that cost relative to an equally expressive conventional hardware implementation?

## Compared designs

1. `minimal_capability` — tag, statement/action binding, authority, epoch freshness, consume-once replay.
2. `full_conventional` — strongest conventional anti-strawman. Adds epistemic state, provenance, execution context, and separate outcome evidence.
3. `rich_proofbit` — ProofBit interpretation of the same full contract.

The minimal design is not scored as wrong for guarantees it does not represent. Unsupported semantics are reported as coverage gaps.

## Frozen guarantee vocabulary

- tag integrity
- statement binding
- authority
- freshness
- replay
- epistemic state (`UNKNOWN / PROVEN_TRUE / PROVEN_FALSE / CONFLICT`)
- provenance
- execution context
- separate outcome evidence

Coverage is therefore `5/9` for minimal capability and `9/9` for both full designs.

## Representation

Minimal token metadata: 41 logical bits.

Full token metadata: 60 logical bits.

Minimal replay state: 139 logical bits (8 x 16-bit identities + valid bits + pointer).

Full state: 278 logical bits: the same replay table plus an equally sized pending-outcome table.

These are logical accounting quantities, not SRAM/macros or physical layout.

## Terminal-success rule

Authorization and terminal outcome are separate facts. A successful authorization may dispatch an effect but cannot establish terminal success. A trusted terminal outcome therefore requires two transactions in the full contract:

`AUTHORIZATION -> OUTCOME`

The minimal capability has no terminal-outcome claim. Its transactions-per-trusted-terminal metric is `unsupported`, not `1`.

## Functional oracle

Icarus simulation covers rich-state rejection, statement/authority/freshness binding, provenance/context, replay, outcome-without-authorization, valid separate outcome, duplicate outcome, and false outcome.

The conventional full-evidence and ProofBit wrappers receive the exact same vectors.

A continuous workload also checks 32 minimal authorization inputs and 32 rich transactions (16 authorization/outcome pairs).

## Structural synthesis

Each top is synthesized independently with Yosys `synth_xilinx -family xc7`.

Reported metrics:
- LUT cells
- FF cells
- BRAM cells
- core cells excluding I/O buffers/clock buffer
- total mapped cells
- Yosys `ltp -noff` logic-depth proxy
- logical metadata/state bits
- transactions per trusted terminal outcome

The conventional and ProofBit full designs deliberately share an equally expressive compact physical core. If they synthesize identically, that is a valid negative ProofBit result: generic rich-evidence enforcement has the same hardware cost when encoded the same way.

## Marginal cost curve

The primary curve is full conventional minus minimal capability. It reports the incremental metadata/state bits, LUTs, FFs, core cells and logic-depth proxy required for four additional guarantees.

Per-added-guarantee ratios are descriptive only; no synthetic winner score is formed.

## Claim boundary

This is synthesizable reference Verilog, Icarus simulation and Yosys structural synthesis. It is not post-route timing, FPGA-board measurement, ASIC PPA, energy, physical tag RAM/cache-coherence, speculation, IOMMU/firmware-root, silicon performance, novelty, patentability or universal superiority evidence.
