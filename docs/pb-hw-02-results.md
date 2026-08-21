# PB-HW-02 Results — Semantic Cost Curve

## Official executable evidence

GitHub Actions run `32496642917`, job `96816504544`.

Environment:

```text
Ubuntu 24.04.4
CPython 3.12.14
Icarus Verilog 12.0
Yosys 0.33 (git sha1 2584903a060)
```

The final measurement uses design-hierarchy flattening **before** `synth_xilinx -family xc7`, then counts mapped Xilinx primitives at the synthesized top. This avoids both earlier accounting failure modes: counting only the wrapper and recursively descending into Xilinx primitive simulation models.

## Functional oracle

Icarus result:

```text
rich safety cases          = 14
minimal promised failures  = 0
minimal semantic gaps      = 4
conventional failures      = 0
ProofBit failures          = 0
minimal stream dispatches  = 32
rich input transactions    = 32
trusted terminal effects   = 16
stalls                     = 0
```

The four minimal-capability accepts are **coverage gaps**, not violations of promises made by the minimal design. They correspond to semantics absent from its contract:

```text
epistemic state
provenance
execution context
separate outcome evidence
```

Coverage:

| Design | Guarantees covered | Terminal success evidence |
| --- | ---: | --- |
| Minimal capability | 5 / 9 | unsupported |
| Full conventional evidence | 9 / 9 | supported |
| Rich ProofBit | 9 / 9 | supported |

Both full designs produce 16 trusted terminal outcomes from 32 input transactions because authorization and outcome are separate facts: `AUTHORIZATION -> OUTCOME`.

## Structural synthesis

| Metric | Minimal capability | Full conventional | Rich ProofBit |
| --- | ---: | ---: | ---: |
| Guarantee coverage | 5 / 9 | **9 / 9** | **9 / 9** |
| Logical metadata | 41 bits | **60 bits** | **60 bits** |
| Logical state | 139 bits | **278 bits** | **278 bits** |
| LUT cells | **200** | **614** | **614** |
| FF cells | **207** | **375** | **375** |
| BRAM | 0 | 0 | 0 |
| Core cells excluding I/O | **544** | **1,166** | **1,166** |
| Total mapped cells | 615 | 1,266 | 1,266 |
| Yosys `ltp -noff` depth proxy | **18** | **18** | **18** |
| Input acceptance rate | 1 transaction/cycle | 1 transaction/cycle | 1 transaction/cycle |
| Transactions / trusted terminal result | unsupported | **2** | **2** |

The complete mapped primitive distribution is identical between `full_conventional` and `rich_proofbit`.

## Marginal cost of the four added guarantees

Measured `full_conventional - minimal_capability`:

```text
metadata          +19 bits   (+46.3%)
logical state     +139 bits  (+100%)
LUT               +414       (+207%)
FF                +168       (+81.2%)
core cells        +622       (+114.3%)
logic-depth proxy +0
```

Descriptive averages over the four bundled additional guarantees:

```text
4.75 metadata bits / added guarantee
34.75 state bits   / added guarantee
103.5 LUT          / added guarantee
42 FF              / added guarantee
```

These averages are **not causal attribution per individual guarantee**. PB-HW-02 adds the four guarantees as one frozen bundle; interactions between them and synthesis optimization are not decomposed here.

## Strong conventional vs ProofBit

Every frozen equality check is true:

```text
same LUT cells
same FF cells
same BRAM cells
same core cells
same logic-depth proxy
same metadata bits
same state bits
same guarantee coverage
same terminal transaction cost
```

Therefore PB-HW-02 does **not** demonstrate a ProofBit-specific hardware-efficiency advantage.

## Main result

> Moving from the frozen 5/9 minimal authorization contract to the 9/9 rich evidence contract has a substantial measurable structural cost in this RTL: +414 LUT, +168 FF, +622 non-I/O mapped cells, +19 token bits and +139 logical state bits, while the measured combinational depth proxy remains unchanged at 18. An equally expressive conventional full-evidence design reproduces the rich ProofBit safety, representation, transaction cost and synthesis result exactly.

This separates two questions that were previously conflated:

1. **Does richer trust semantics cost hardware?** Yes, materially in this frozen design.
2. **Is that cost uniquely lower for ProofBit?** No evidence of that in PB-HW-02.

## Harness history

Three measurement-only corrections were made without changing the frozen trust contract:

1. testbench task argument `context` was renamed because `context` is a SystemVerilog keyword;
2. recursive wrapper accounting was introduced after top-only counting missed the shared rich core;
3. recursive accounting was replaced by **pre-map design flattening** after it descended into Xilinx primitive simulation models (`$specify2`).

The final run passes the functional oracle, structural non-zero checks and coverage/accounting assertions.

## Next falsifiable experiment

`PB-HW-03`: composition / instruction-transaction economics.

Do not compare two identical Boolean gates again. Give both strong designs equally optimized mechanisms for deriving a trusted authorization from multiple parent evidences, then measure:

- instructions / transactions per trusted derived effect;
- memory/proof-table reads and writes;
- parent-proof composition work;
- cache hits/misses;
- invalidation/revocation work;
- replay/provenance state;
- pipeline stalls and cycles;
- LUT/FF/BRAM and logic-depth deltas.

A conventional composition instruction that matches a ProofBit composition instruction remains a valid negative result. Any claimed ProofBit benefit must survive that control.

## Claim boundary

Synthesizable reference Verilog + Icarus simulation + Yosys structural synthesis only. `ltp` is not post-route timing, and `synth_xilinx` counts are not placed/routed utilization for a named FPGA. No FPGA-board measurement, ASIC PPA, energy, physical tag/cache RAM, speculative execution, IOMMU/firmware root, silicon-performance, novelty/patentability or universal-superiority claim.
