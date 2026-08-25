# ProofBit Negative Results

Negative results are first-class output in ProofBit. They prevent the project from confusing a useful architecture pattern with a unique ProofBit advantage.

The permanent rule is:

> If a competent conventional control reproduces the benefit at equal semantic coverage and comparable cost, the benefit belongs to the shared architecture.

## Summary

Across software, IPC, crash recovery, policy evolution, cross-language release skew, OS isolation, ISA models, whole-system coherence, and RTL synthesis, strong conventional controls repeatedly matched ProofBit safety and often matched or exceeded current ProofBit runtime.

This narrows the project from a broad claim — “ordinary systems cannot do this” — to a sharper question:

> Can a standardized proof-aware contract reduce whole-system integration, atomicity, authenticity, composition, or audit cost enough to justify dedicated runtime or hardware support?

## Result ledger

| Benchmark | Strong conventional control | Negative result | What remains useful |
|---|---|---|---|
| PB-TRANSITION-03 | Full software trust guard | 100% correctness and zero unsafe/false-success results; roughly 5x faster than the Python ProofBit reference in the recorded run | Explicit epistemic/outcome semantics and a reusable fault oracle |
| PB-TC01 | Shared immutable trust envelope | Shared software remained faster at every boundary depth | Field-by-field trust reconstruction scales poorly; immutable contract propagation matters |
| PB-TC02 | Identical 42-byte compact software record | Compact software remained faster at 1/2/4/8 real IPC boundaries; ProofBit/compact ranged about 0.828x–0.973x | Compact binary transport and explicit outcome framing |
| PB-TC03 | Lazy authoritative software boundary | Same dynamic-trust correctness; focused depth-8 ProofBit/software-lazy ratio about 0.978x | Lazy final authority avoids eager revocation fanout |
| PB-TC04 | Indexed conventional durable log | Same recovery oracle, bytes, and targeted audit work; ProofBit about 0.978x recovery throughput | Indexed receipt chains reduced targeted audit work by 500x versus scanning |
| PB-TC05 | Indexed integrity log | Same corruption detection, repair scans/writes, and storage; ProofBit recovery about 5.3% slower by median in the fixture | Semantic binding prevents corrupted evidence from becoming confident truth |
| PB-TC06 | Shared canonical policy registry | Same correctness, descriptor size, and update surface as ProofBit | Independent copies paid 8x update/regression surface at eight components |
| PB-TC07 | Canonical Python/Rust/Node contract | Same 100% conformance and zero disagreements; runtime difference was noise | One version-bound descriptor prevents language drift |
| PB-TC08 | Canonical runtime under release skew | Same 100% availability for known primitives; both failed closed for a genuinely new primitive | Canonical runtime decouples policy updates from application releases |
| PB-TC09 | Mandatory software reference monitor | Same 100% safety against direct-call, stale-cache, replay, rebinding, malformed-frame, and false-success cases | Enforcement placement at the effect seam matters more than application validation |
| PB-TC10 | POSIX capability/UID reference monitor | Same 6/6 blocked unprivileged bypasses; both failed same-privilege compromise | Resource ownership and handle isolation are mandatory |
| PB-TC11 | Tagged capability ISA model | Zero bypasses for both strong machines across the bounded search; current Python ProofBit was materially slower | Non-forgeable metadata plus mandatory effect instruction closes the frozen user-mode attacks |
| PB-TC12 | Whole-system capability model | Same safety across CPU/debug/DMA/context/cache/rollback; current ProofBit reference slower | Whole-system coherence is required; CPU-only tags are insufficient |
| PB-HW-01 | Equal-semantics capability RTL | Identical LUT, FF, BRAM, total cells, metadata, replay state, and depth | Generic proof/capability tags have measurable cost but no naming advantage |
| PB-HW-02 | Full conventional evidence RTL | Identical rich-semantics hardware cost and coverage | Rich trust semantics cost substantial LUT/FF/state versus a minimal capability |
| PB-HW-03 | Conventional `COMPOSE4` primitive | Identical mapped hardware and economics to ProofBit `COMPOSE4` | Four-parent composition reduced transactions 6->2 and issue cycles 4->1 versus scalar |
| PB-HW-04 | Equal physical multi-read conventional cache | Identical RAMB36, LUT, FF, core cells, depth, latency, and safety | Four-read caching reduced warm composition to 1 cycle but paid 4x evidence storage |

## Strong claims that did not survive

### “ProofBit is required to implement authority, freshness, replay, provenance, and outcome checks”

False in the tested systems. Competent conventional software and capability designs implemented the same frozen contracts correctly.

### “ProofBit is inherently faster because proof metadata travels as one object”

Not supported. It beat explicit field-by-field reconstruction in TC01, but did not beat the strongest shared or compact conventional controls.

### “A proof tag is physically different from an equally expressive capability tag”

Not in the current RTL. Equal Boolean semantics and topology produced identical Yosys mappings.

### “Hardware caches or multi-parent operations are uniquely ProofBit”

Not supported. Conventional designs with the same primitive or memory organization reproduced the gains exactly.

### “Moving checks into hardware automatically creates a moat”

Not supported. Generic mandatory tagged enforcement closed the same attack classes. A moat requires a difference in semantics, atomicity, authenticity, integration economics, or ecosystem adoption — not merely a lower layer.

## What the negative results positively establish

The experiments still produced valuable general conclusions:

1. **Do not validate far from execution.** The authoritative effect seam must enforce the contract.
2. **Do not infer outcome from dispatch.** Outcome requires separate evidence.
3. **Do not duplicate policy semantics casually.** Canonical descriptors reduce drift and release coordination.
4. **Do not audit by full scan when an authenticated/indexed chain is available.**
5. **Do not treat parallel proof-memory reads as free.** Ports, replication, banks, conflicts, and caches have physical cost.
6. **Do not call a generic capability benefit a ProofBit benefit.**
7. **Do not hide noisy crossovers.** Repeated rotated runs supersede attractive one-off measurements.

## Current honest moat candidates

The current evidence does not support a moat from generic tags, policy checks, indexed logs, or caches alone.

Potential defensibility may instead come from:

- a canonical proof-carrying action contract;
- a high-quality conformance and adversarial benchmark suite;
- portable execution/outcome receipts;
- atomic data+evidence semantics;
- root-of-trust and rollback-resistant evidence minting;
- integrations at consequential AI-agent action boundaries;
- customer workflow data and policy packs;
- a future proof-aware coprocessor only where measurements justify it.

## Research integrity rule

Every future benchmark must include the strongest credible conventional anti-strawman.

A future ProofBit-specific claim is accepted only when:

```text
same semantic coverage
+ same threat model
+ same workload
+ comparable implementation quality
+ measurable advantage
```

and the advantage survives repeated measurement.
