# PB-HW-01 — RTL Semantic-Equivalence Benchmark

## Question

TC11 and TC12 showed that a strong conventional tagged/capability architecture can reproduce ProofBit safety when both are granted an equally non-forgeable metadata plane and mandatory effect boundary.

PB-HW-01 moves from Python machine models to **synthesizable RTL** and asks:

> When the safety semantics are deliberately normalized, do a conventional capability pipeline and a ProofBit proof-tag pipeline have materially different hardware structure or cost?

A hardware tie is a valid negative ProofBit result.

## Compared RTL modules

1. `pb_hw01_raw_pipeline`
   - value/state-only baseline;
   - only the two-bit state gates the effect;
   - no tag, statement, authority, freshness, provenance, context, or replay enforcement.

2. `pb_hw01_capability_pipeline`
   - primary conventional anti-strawman;
   - tag + state + action + authority + epoch + nonce + source/provenance + context;
   - mandatory final effect check;
   - eight-entry consume-once replay table.

3. `pb_hw01_proofbit_pipeline`
   - same physical fields and pipeline topology;
   - fields are interpreted as proof tag + epistemic state + statement + authority + epoch + proof id + provenance + execution context;
   - same eight-entry consume-once replay table.

The two strong modules are intentionally separate RTL modules but implement the same Boolean safety contract. This is the experiment, not an accident.

## Logical metadata normalization

Both strong designs receive exactly **59 logical metadata bits**:

```text
tag                  1
state                2
action / statement   8
authority            8
epoch                8
nonce / proof_id    16
source / provenance  8
context / domain     8
----------------------
total               59 bits
```

The replay structure is also identical:

```text
8 entries × (16-bit id + valid bit) + 3-bit FIFO pointer
= 139 logical bits
```

This prevents ProofBit from winning or losing merely because one side was given richer metadata.

## Pipeline model

Both strong pipelines use:
- two registered stages in the reference RTL;
- one cycle from accepted input to result;
- one accepted valid effect per cycle after pipeline fill;
- zero modeled stalls on the valid stream;
- an eight-entry fully scanned replay table.

This is a small reference microarchitecture, not an optimized production core.

## Frozen simulation vectors

Icarus Verilog exercises ten cases:

```text
VALID
BAD_TAG
BAD_STATE
STATEMENT_REBIND
WRONG_AUTHORITY
STALE_EPOCH
MISSING_PROVENANCE
WRONG_CONTEXT
VALID_SINGLE_USE
REPLAY_SAME_NONCE
```

The capability and ProofBit modules must agree on every case and must produce zero frozen-oracle failures.

The raw baseline is expected to accept at least one unsafe vector.

After the safety vectors, the testbench streams 32 fresh valid authorizations on consecutive cycles. All three modules must produce all 32 valid effects; the strong designs must demonstrate one-effect-per-cycle steady-state issue with no modeled stalls.

## Synthesis methodology

The workflow installs open-source `iverilog` and `yosys` on Ubuntu.

### Functional simulation

```text
iverilog -g2012
vvp
```

The benchmark parses one frozen PASS marker from the testbench.

### Structural synthesis

Each top module is independently synthesized with:

```text
synth_xilinx -family xc7
```

The Yosys JSON netlist is used to count:
- LUT1..LUT6 cells;
- Xilinx FF primitives;
- RAMB18/RAMB36 primitives;
- total cells.

These are open-source generic Xilinx-7-series mapping estimates. They are **not** post-place-and-route utilization numbers for a named FPGA device.

### Critical-path proxy

The benchmark also runs Yosys `ltp -noff` after generic process/memory lowering and optimization.

The returned topological path length is treated only as a **structural logic-depth proxy**. It is not frequency, nanoseconds, slack, or post-route timing.

## Primary falsifier

`pb_hw01_capability_pipeline` is the primary anti-strawman.

If capability and ProofBit produce:
- identical safety results;
- identical metadata width;
- identical replay storage;
- identical cycles/effect;
- and identical or near-identical synthesized structure,

then PB-HW-01 does **not** establish a ProofBit-specific advantage for the generic tag/effect gate.

That result would move the hypothesis to hardware cost of **semantic differences**, not generic metadata enforcement.

## What PB-HW-01 does not test

Because the two strong designs are deliberately semantically normalized, this experiment does not test the extra value of richer ProofBit epistemic states, provenance graphs, conflict composition, outcome receipts, proof caching, or invalidation primitives.

Those belong in a later differential hardware experiment.

## Next experiment if strong designs map equivalently

`PB-HW-02` should introduce a controlled semantic delta:

```text
minimal capability tag
vs
full conventional evidence metadata
vs
ProofBit epistemic/provenance/outcome machinery
```

Then measure incremental:
- metadata bits;
- comparator / state-machine depth;
- replay/proof-cache storage;
- cycles and stalls;
- LUT/FF/BRAM estimates;
- instructions/transactions needed to preserve the semantics.

## Claim boundary

PB-HW-01 uses synthesizable Verilog, Icarus simulation, and Yosys structural synthesis only.

It does **not** provide:
- FPGA-board measurement;
- place-and-route timing;
- ASIC PPA;
- transistor or energy estimates;
- physical tag RAM;
- cache/coherence implementation;
- speculative/transient execution analysis;
- IOMMU/firmware/root-of-trust implementation;
- silicon performance;
- novelty or patentability evidence;
- universal superiority evidence.
