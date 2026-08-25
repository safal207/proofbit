# PB-HW-03 methodology — composition economics

Protocol: `PB-HW-03/v0.1 composition-economics`.

## Question

When one trusted derived authorization depends on four parent evidences, what is the hardware and instruction-transaction cost of serial composition versus a dedicated four-parent composition primitive? Does a ProofBit-labelled primitive retain any advantage after giving conventional hardware the same semantic contract and the same four-parent issue width?

## Compared engines

1. **scalar_conventional** — one parent evidence is supplied per input transaction. The terminal protocol is `PARENT ×4 -> COMPOSE -> OUTCOME`.
2. **vector_conventional** — strong conventional anti-strawman. Four parent evidences are supplied to one `COMPOSE4` transaction, followed by a separate `OUTCOME` transaction.
3. **proofbit_compose** — ProofBit interpretation of the same `COMPOSE4 -> OUTCOME` protocol. It intentionally instantiates the same equally expressive vector core as the strong conventional control.

The vector conventional control is primary. A structural tie with ProofBit is a valid negative result.

## Frozen semantic guarantees

Every engine must preserve all nine:

- parent epistemic state (`PROVEN_TRUE` required),
- parent authority,
- parent freshness/epoch,
- parent provenance presence,
- parent execution context,
- uniqueness of all four parent identities within the composition,
- consume-once parent replay protection across successful compositions,
- derived statement binding,
- separate terminal outcome evidence.

`UNKNOWN`, `CONFLICT`, `PROVEN_FALSE`, stale authority epoch, wrong authority, provenance loss, context rebound, duplicate parent, statement rebound, parent replay, outcome-without-authorization, duplicate outcome and false outcome are executable negative cases.

## Fixed economics

For one trusted terminal result:

| Metric | Scalar conventional | Vector conventional | ProofBit compose |
| --- | ---: | ---: | ---: |
| Parent count | 4 | 4 | 4 |
| Logical parent reads | 4 | 4 | 4 |
| Parent-read issue cycles | 4 | 1 | 1 |
| Derived writes | 1 | 1 | 1 |
| Outcome writes | 1 | 1 | 1 |
| Input instruction transactions | 6 | 2 | 2 |
| Parallel parent lanes | 1 | 4 | 4 |

The protocol therefore freezes a **3× instruction-transaction reduction** and **4× parent-read issue-cycle reduction** for either four-lane primitive versus the scalar engine, without changing the number of logical evidences consumed or durable/logical results produced.

## Logical access accounting vs physical memory

PB-HW-03 accounts proof-table reads/writes as **logical protocol accesses**. It does not instantiate a physical multi-ported proof RAM/cache. This is deliberate: the experiment isolates composition-engine economics first. Mapped LUT/FF counts therefore cover the composition engines, replay state and control logic, not physical proof-memory PPA.

A later memory experiment may replace logical access accounting with an actual bounded proof table/cache and explicit port/bank conflicts.

## State model

The bounded reference RTL uses exact 8-bit parent identities and a 256-bit consume-once parent replay set. Scalar conventional additionally holds four staged parent records. Vector conventional and ProofBit validate the four lanes directly.

Logical state accounting:

- scalar conventional: 454 bits,
- vector conventional: 282 bits,
- ProofBit compose: 282 bits.

These are logical reference-model state bits, not post-place-and-route storage utilization.

## Simulation oracle

Icarus Verilog executes 14 safety cases and two deterministic streams:

- scalar stream: 16 trusted terminal effects from exactly 96 input transactions,
- vector/ProofBit stream: 16 trusted terminal effects from exactly 32 input transactions,
- zero stalls in the frozen no-contention interface.

Correctness is primary. A performance/resource result is not accepted if any architecture fails the common oracle.

## Structural synthesis

Each top is synthesized separately with Yosys `synth_xilinx -family xc7`. The benchmark's own hierarchy is flattened before technology mapping so custom wrappers/cores cannot hide mapped primitives from accounting.

Reported structural metrics:

- LUT cells,
- FF cells,
- BRAM cells,
- non-I/O core cells,
- total mapped cells,
- `ltp -noff` logic-depth proxy.

`ltp` is not routed timing and `synth_xilinx` counts are not placed/routed utilization for a named board.

## Falsification rules

- If vector conventional matches ProofBit correctness and economics, ProofBit has **no demonstrated unique composition advantage** in PB-HW-03.
- If both vector primitives beat scalar instruction economics, that result belongs to the **dedicated four-parent composition primitive**, not automatically to ProofBit.
- If a resource difference appears between the two vector wrappers, investigate the harness/toolchain before treating it as architecture evidence because they intentionally share the same core.
- No single winner score is produced.

## Claim boundary

Synthesizable reference Verilog + Icarus simulation + Yosys structural synthesis only. No physical multi-ported proof RAM/cache, FPGA-board timing, ASIC PPA, energy, speculation, IOMMU/firmware-root, silicon-performance, novelty, patentability or universal-superiority claim.
