# PB-HW-04 results — physical proof-memory / cache economics

Status: **GREEN on dedicated GitHub Actions with Icarus Verilog 12.0 + Yosys 0.33.**

PB-HW-04 replaces logical proof-table accounting with synthesizable physical evidence memories and measures the cycle/resource cost of supplying four-parent trust composition.

## Functional oracle

The final deterministic simulation executed **52 checks with 0 failures**.

| Scenario | Single-port conventional | Banked conventional | Multi-port conventional cache | ProofBit cache |
| --- | ---: | ---: | ---: | ---: |
| Cold conflict-free | 4 cycles | 2 | 2 | 2 |
| Warm conflict-free | 4 | 2 | **1** | **1** |
| Same-bank cold | 4 | 5 | **2** | **2** |
| Same-bank warm | 4 | 5 | **1** | **1** |
| Post-invalidation | 4 | 2 | 2 | 2 |

The strong conventional cache and ProofBit cache therefore match on every measured latency case. Cache hits reduce the four-parent composition path from 2 cycles to 1; replicated read ports avoid the 5-cycle same-bank conflict seen by the four-bank design.

## Physical memory mapping

The final RTL uses explicit synchronous physical read ports so Yosys does not silently replicate the baseline memories.

| System | Logical evidence bits | RAMB36 | RAMB18-equivalent | Cache data | Cache tag+valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| Single-port conventional | 65,536 | **2** | 4 | 0 | 0 |
| Banked conventional | 65,536 | **4** | 8 | 0 | 0 |
| Multi-port conventional cache | 262,144 | **8** | 16 | 1,024 bits | 112 bits |
| ProofBit cache | 262,144 | **8** | 16 | 1,024 bits | 112 bits |

The four-read cached architecture therefore pays **4× the logical evidence storage** of the single-port baseline through full-table replication. The banked design retains the same logical evidence bits as single-port but consumes four RAMB36 blocks because each 256×64 bank maps independently.

## Structural synthesis

Yosys `synth_xilinx -family xc7` results:

| Metric | Single-port | Banked | Conventional cache | ProofBit cache |
| --- | ---: | ---: | ---: | ---: |
| LUT | 6,966 | 7,645 | **10,213** | **10,213** |
| FF | 1,286 | 1,335 | **2,148** | **2,148** |
| Core cells excluding I/O | 8,943 | 10,018 | **13,213** | **13,213** |
| Logic-depth proxy (`ltp -noff`) | 36 | 59 | **100** | **100** |
| LUTRAM cells | 0 | 0 | **0** | **0** |
| RAMB36 | 2 | 4 | **8** | **8** |

Relative to single-port, the cached four-read design buys the lower warm/conflict latency with roughly **4× BRAM count**, **+46.6% LUT**, **+67.0% FF**, and **+47.7% core cells** in this structural mapping. These are synthesis-structure measurements, not placed/routed timing or silicon PPA.

## Strong conventional falsifier

`multiport_conventional_cache` and `proofbit_cache` are identical on every pre-registered comparison axis:

- LUT count;
- FF count;
- RAMB36/RAMB18 mapping;
- LUTRAM count;
- core cell count;
- logic-depth proxy;
- physical evidence bits;
- cache bits;
- all measured compose latencies;
- safety/oracle behavior.

Therefore the safe result is:

> **PB-HW-04 demonstrates a real physical memory/cache tradeoff for four-parent trust composition, but no ProofBit-specific memory/cache advantage.** Replicated read ports and a small cache reduce bank-conflict and warm-read latency, while the equally provisioned conventional cache reproduces the ProofBit result exactly.

The benefit belongs to the memory organization, not to the ProofBit label.

## Measurement hygiene

Two harness/physical-model issues were caught before these results were recorded:

1. a testbench `posedge` scheduling race was replaced by deterministic post-edge sampling;
2. multiple syntactic baseline read-sites caused Yosys to replicate BRAM unexpectedly, so the final RTL was rewritten with explicit synchronous physical read ports.

Only the post-fix GREEN run is treated as official evidence.

## Claim boundary

Synthesizable reference Verilog + Icarus simulation + Yosys structural Xilinx-7 mapping only. No placed/routed FPGA timing, board measurement, ASIC PPA, power/energy, ECC, full coherence fabric, speculation, IOMMU/firmware-root, silicon-performance, novelty/patentability or universal-superiority claim.
