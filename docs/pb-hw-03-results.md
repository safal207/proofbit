# PB-HW-03 results — composition economics

Status: **GREEN**.

Official evidence:

- GitHub Actions run: `32498895006`
- job: `96823763156` (`composition-economics`)
- Ubuntu 24.04.4
- CPython 3.12.14
- Icarus Verilog 12.0
- Yosys 0.33 (`2584903a060`)

## Functional oracle

```text
safety cases                 = 14
scalar failures              = 0
vector conventional failures = 0
ProofBit failures            = 0
scalar stream transactions   = 96
vector stream transactions   = 32
scalar trusted terminals     = 16
conventional trusted terminals = 16
ProofBit trusted terminals   = 16
stalls                       = 0
```

All three engines therefore satisfy the same 9 / 9 composition guarantees in the frozen fixture.

## Official economics and synthesis

| Metric | Scalar conventional | Vector conventional | ProofBit compose |
| --- | ---: | ---: | ---: |
| Guarantee coverage | 9 / 9 | **9 / 9** | **9 / 9** |
| Logical parent reads / terminal | 4 | 4 | 4 |
| Parent-read issue cycles | 4 | **1** | **1** |
| Logical derived writes | 1 | 1 | 1 |
| Logical outcome writes | 1 | 1 | 1 |
| Instruction transactions / trusted terminal | 6 | **2** | **2** |
| Trusted terminals / input transaction | 0.1667 | **0.5** | **0.5** |
| Parallel parent lanes | 1 | **4** | **4** |
| Logical state bits | 454 | **282** | **282** |
| LUT cells | 1,726 | **1,702** | **1,702** |
| FF cells | 458 | **286** | **286** |
| BRAM cells | 0 | 0 | 0 |
| Core cells excluding I/O | 3,086 | **2,923** | **2,923** |
| Total mapped cells | 3,188 | **3,148** | **3,148** |
| `ltp -noff` depth proxy | 14 | **13** | **13** |

The vector conventional and ProofBit primitive distributions are structurally identical in this run.

## Primitive versus scalar

Measured `vector_conventional - scalar_conventional`:

```text
instruction transactions     6 -> 2     (3.0× reduction)
parent-read issue cycles      4 -> 1     (4.0× reduction)
logical parent reads          4 -> 4     (no reduction)
logical total writes          2 -> 2     (no reduction)
logical state bits          454 -> 282   (-172, -37.9%)
LUT                         1726 -> 1702  (-24, -1.4%)
FF                           458 -> 286   (-172, -37.6%)
core cells                  3086 -> 2923  (-163, -5.3%)
total mapped cells          3188 -> 3148  (-40, -1.3%)
logic-depth proxy             14 -> 13    (-1)
```

This is stronger than the preregistered protocol result: in the frozen reference RTL, the four-lane primitive not only reduces instruction issue work but also removes the scalar engine's four-parent staging state, resulting in fewer FFs and slightly fewer LUT/core cells.

The wider primitive does expose more top-level I/O cells (225 versus 102), so the core-cell comparison intentionally excludes I/O. Even including I/O, total mapped cells remain slightly lower in this specific run.

## Strong conventional anti-strawman

Every equality check between `vector_conventional` and `proofbit_compose` is true:

- LUT,
- FF,
- BRAM,
- non-I/O core cells,
- logic-depth proxy,
- logical state bits,
- guarantee coverage,
- instruction transactions,
- logical parent reads,
- parent-read issue cycles,
- logical writes.

Therefore PB-HW-03 does **not** establish a ProofBit-specific hardware or composition-efficiency advantage.

## Main result

> PB-HW-03 shows that, for this bounded four-parent trust-composition contract, a dedicated `COMPOSE4` primitive can reduce instruction transactions 3× and parent-read issue cycles 4× relative to a one-parent-at-a-time scalar engine while consuming the same four logical parent evidences and producing the same derived/outcome writes. In the synthesized reference RTL it also uses fewer FFs and slightly fewer LUT/core cells because it eliminates scalar staging state. An equally expressive conventional `COMPOSE4` primitive exactly matches the ProofBit primitive, so the demonstrated benefit belongs to the composition primitive, not uniquely to ProofBit.

## What this does and does not prove

It **does** demonstrate a concrete hardware/instruction frontier for serial versus four-lane trust composition under one frozen bounded contract.

It does **not** demonstrate that ProofBit is uniquely necessary for composition. The strongest conventional control reproduces the same semantics and the same mapped structure.

It also does **not** yet measure physical proof-memory economics. The four parent reads and two result writes are logical protocol accounting; no physical multi-ported proof RAM/cache is instantiated.

## Next falsifiable boundary

`PB-HW-04`: physical proof-memory / cache economics.

Instantiate the bounded parent-evidence table for real and compare:

- one-port/banked conventional table,
- equally strong multi-port conventional composition cache,
- ProofBit-oriented proof table/cache,
- bank conflicts and stalls,
- read/write ports,
- cache hit/miss behavior,
- invalidation/replay state,
- BRAM/LUTRAM/FF mapping,
- cycles per trusted terminal effect,
- mapped resource cost.

If a strong conventional proof table matches ProofBit again, preserve that negative result.

## Claim boundary

Synthesizable reference Verilog + Icarus simulation + Yosys structural synthesis only. Logical proof-table accesses are accounted, but no physical multi-ported proof RAM/cache is instantiated. `ltp` is not routed timing. No FPGA-board timing, ASIC PPA, energy, silicon performance, novelty/patentability or universal-superiority claim.
