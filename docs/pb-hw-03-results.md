# PB-HW-03 results — composition economics

Status: **executable benchmark added; official mapped-resource numbers pending the dedicated GitHub Actions run for this branch.**

The frozen protocol and pass/fail conditions are already fixed in `docs/pb-hw-03-methodology.md`.

## Protocol-level expectations (not synthesis results)

| Metric | Scalar conventional | Vector conventional | ProofBit compose |
| --- | ---: | ---: | ---: |
| Guarantee coverage | 9 / 9 | 9 / 9 | 9 / 9 |
| Parent count | 4 | 4 | 4 |
| Logical parent reads / terminal | 4 | 4 | 4 |
| Parent-read issue cycles | 4 | 1 | 1 |
| Logical derived writes | 1 | 1 | 1 |
| Logical outcome writes | 1 | 1 | 1 |
| Instruction transactions / trusted terminal | 6 | 2 | 2 |
| Logical state bits | 454 | 282 | 282 |

The 6→2 transaction difference is a property of the frozen instruction protocol, not an observed clock-rate speedup. The same four parents and the same two logical result writes remain required.

## Result acceptance rule

Official PB-HW-03 interpretation will be written only from an executable green run containing:

- 14 / 14 common safety scenarios,
- zero scalar, conventional-vector and ProofBit oracle failures,
- scalar stream = 96 transactions → 16 trusted terminal effects,
- vector conventional stream = 32 transactions → 16 trusted terminal effects,
- ProofBit stream = 32 transactions → 16 trusted terminal effects,
- mapped LUT/FF/core-cell results for all three tops,
- strong-control structural equality checks between vector conventional and ProofBit.

## Pre-registered interpretation

If the expected strong-control tie survives synthesis, the safe conclusion is:

> PB-HW-03 demonstrates that a dedicated four-parent composition primitive can reduce instruction issue work relative to a serial one-parent-at-a-time engine while preserving the same evidence consumption and outcome accounting. An equally expressive conventional `COMPOSE4` primitive matches the ProofBit primitive, so the measured instruction-economics benefit belongs to the composition primitive, not uniquely to ProofBit.

If the two vector wrappers differ after synthesis, that difference must be treated as a harness/toolchain anomaly until explained because both instantiate the same core.

## Claim boundary

Logical proof-table accesses are accounted, but no physical multi-ported proof RAM/cache is instantiated. Yosys structural synthesis and `ltp` do not establish board timing, ASIC PPA, energy, or silicon performance.
