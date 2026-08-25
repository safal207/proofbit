# PB-HW-01 — Official Results

## Verdict

`PB-HW-01/v0.1 rtl-semantic-equivalence` is **GREEN**.

The normalized conventional capability pipeline and ProofBit pipeline produce identical frozen safety behavior and, under Yosys 0.33 Xilinx-7-series structural synthesis, map to **exactly the same reported cell counts and logic-depth proxy**.

This is a deliberate and important **negative ProofBit-specific result**:

> When capability and ProofBit are given the same metadata width, replay structure, pipeline topology, and Boolean enforcement semantics, PB-HW-01 finds no hardware-structure advantage for naming that metadata a proof rather than a capability/evidence tag.

## Official environment

GitHub Actions run `32494630826`, job `96810026061`.

```text
Ubuntu 24.04.4
CPython 3.12.14
Icarus Verilog 12.0
Yosys 0.33 (git sha1 2584903a060)
```

The first run intentionally remains part of the history: run `32494493016` was RED only because `yosys -q` suppressed the `ltp` text that the harness attempted to parse. The RTL/parser tests were already green. Commit `abe41c1c56c82cf8f7cbb037c58e2787b854f910` removed quiet mode only from the logic-depth measurement. The frozen safety oracle and RTL semantics were unchanged.

## Functional simulation

Icarus Verilog result:

```text
PB_HW01_SIM PASS
safety=10
raw_unsafe=7
cap_fail=0
proof_fail=0
stream=32
latency_cycles=1
stalls=0
```

### Safety interpretation

| RTL | Frozen safety failures | Unsafe accepts observed |
| --- | ---: | ---: |
| raw state gate | n/a | **7** |
| tagged capability | **0** | **0** |
| ProofBit proof-tag | **0** | **0** |

The ten vectors cover:

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

The two strong modules agree on every vector.

### Pipeline behavior

After the safety vectors, the testbench streams 32 fresh valid authorizations on consecutive clocks.

All three RTL modules produce:

```text
32 / 32 valid effects
input-to-result latency = 1 cycle
steady-state issue      = 1 effect / cycle
modeled stalls          = 0
```

No clock-frequency claim is implied by this functional simulation.

## Semantic normalization

The capability and ProofBit pipelines each receive exactly **59 logical metadata bits**:

| Field | Bits |
| --- | ---: |
| tag | 1 |
| state | 2 |
| action / statement | 8 |
| authority | 8 |
| epoch | 8 |
| nonce / proof id | 16 |
| source / provenance | 8 |
| context / domain | 8 |
| **Total** | **59** |

Both use the same eight-entry consume-once replay structure:

```text
8 × (16-bit id + 1 valid bit) + 3-bit replacement pointer
= 139 logical bits
```

The raw baseline carries only the two-bit state used by its effect gate.

## Yosys structural synthesis

Each top was independently synthesized with:

```text
synth_xilinx -family xc7
```

### Summary

| Metric | Raw | Capability | ProofBit |
| --- | ---: | ---: | ---: |
| LUT cells | **1** | **314** | **314** |
| FF cells | **5** | **233** | **233** |
| BRAM cells | 0 | 0 | 0 |
| Total mapped cells | **103** | **837** | **837** |
| Yosys `ltp -noff` depth proxy | **2** | **19** | **19** |
| Logical metadata bits | 2 | **59** | **59** |
| Logical replay-state bits | 0 | **139** | **139** |
| Registered stages | 2 | 2 | 2 |
| Input-to-result latency | 1 cycle | 1 cycle | 1 cycle |
| Steady-state cycles/effect | 1 | 1 | 1 |

### Exact strong-control equivalence

Every recorded equality flag is true:

```text
same_lut_cells          = true
same_ff_cells           = true
same_bram_cells         = true
same_total_cells        = true
same_logic_depth_proxy  = true
same_metadata_bits      = true
same_replay_table_bits  = true
```

The exact mapped cell-type distribution is also identical:

```text
BUFG    1
CARRY4  1
FDRE  233
IBUF   94
INV    92
LUT2   95
LUT3    9
LUT4   30
LUT5    7
LUT6  173
MUXF7  70
MUXF8  30
OBUF    2
```

## What the raw delta means — and does not mean

Relative to the raw two-bit state gate, the full normalized trust contract uses much more logic and state. In this small frozen design:

```text
LUT:        314 vs 1
FF:         233 vs 5
Total cell: 837 vs 103
Depth proxy: 19 vs 2
```

That delta is **not** evidence that ProofBit specifically is expensive. The conventional capability control pays exactly the same delta because it implements exactly the same semantics.

The supported conclusion is only that statement/authority/freshness/provenance/context/replay enforcement has non-trivial hardware cost compared with a weak raw state gate.

## Main result

PB-HW-01 falsifies a broad hardware claim:

> A generic proof-tag gate is not intrinsically smaller, shallower, or faster than an equally expressive conventional capability/evidence gate. With normalized semantics and topology, Yosys maps the two PB-HW-01 strong designs identically.

Therefore the remaining ProofBit hardware hypothesis must come from a **semantic or compositional delta**, such as:

- richer epistemic states (`UNKNOWN`, `CONFLICT`, `STALE`, etc.);
- provenance composition;
- explicit outcome evidence;
- proof/reference caching and invalidation;
- reducing the number of instructions or transactions needed to preserve those semantics;
- a more efficient representation than an equally expressive conventional implementation.

## Next falsifiable experiment — PB-HW-02

Do **not** repeat another normalized tag-equivalence test.

Instead compare three intentionally different semantic tiers:

1. minimal tagged capability;
2. strongest conventional full-evidence machine implementing the same rich semantic contract;
3. ProofBit-native rich proof-state machine.

Measure incremental:

```text
metadata bits
LUT / FF / BRAM
logic-depth proxy
pipeline stages
cycles / effect
stalls
replay / proof-cache bits
invalidation traffic / operations
instructions or transactions per trusted effect
```

The strongest conventional full-evidence RTL remains the primary anti-strawman. If it again matches ProofBit, the generic hardware architecture claim narrows further.

## Claim boundary

These are open-source **structural synthesis** results from synthesizable reference Verilog.

`Yosys ltp -noff` is only a logic-depth proxy. `synth_xilinx -family xc7` cell counts are not post-place-and-route utilization for a named device.

No claim is made about:
- achieved MHz;
- FPGA-board performance;
- ASIC area/timing/power;
- energy per operation;
- physical replay/tag RAM design;
- cache/coherence integration;
- speculative execution;
- IOMMU/firmware/root of trust;
- silicon competitiveness;
- novelty or patentability;
- universal superiority.
