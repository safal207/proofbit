# PB-TRUST-COMPOSE-06 Results

## Verdict

`PB-TRUST-COMPOSE-06` does **not** demonstrate a ProofBit-specific correctness, update-surface, representation-size, or stable runtime advantage over a strong conventional shared-policy registry with a propagated typed receipt.

It does demonstrate a narrower scaling result:

> When the same trust policy is replicated as independently managed copies across N components, safe policy evolution requires update and regression work proportional to N. A single authoritative generic policy-contract mechanism avoids that replication cost — and TC06 shows that both conventional shared-registry software and the ProofBit reference can realize that pattern.

The result therefore belongs to the **single authoritative contract + propagated receipt** architecture, not uniquely to ProofBit.

## Reproducible environment

Official evidence:

- repository: `safal207/proofbit`
- branch: `feat/pb-trust-compose-06`
- workflow: `pb-trust-compose-06`
- run: `32477696244`
- job: `96757360137`
- measured branch head: `7c0a2e69897328283fe8adc56ee25b9a5f3e184d`
- OS: Ubuntu 24.04.4
- Python: CPython 3.12.14
- components: 8
- requests per policy version: 10,000
- policy versions: 5
- requests per system per round: 50,000
- rounds: 11
- execution order: rotated across all three system orderings

The job completed successfully, including seven TC06 regression tests, the full 11-round benchmark, the versioned oracle, representation-equality assertions and rollout anti-strawman assertions.

## Frozen policy evolution

```text
v1  statement + authority
v2  + epoch
v3  + replay
v4  + provenance
v5  + separate outcome evidence
```

Every change is expressible inside the six primitives frozen before measurement.

This matters: a genuinely new trust primitive is outside the one-descriptor-update claim and would require verifier/component evolution.

## Correctness

After correctness-first safe activation, all three systems produced:

```text
oracle accuracy          = 100%
unsafe accepts           = 0
false terminal success   = 0
missed valid requests    = 0
semantic drift           = 0
```

Therefore TC06 shows no ProofBit-specific correctness advantage over either competent conventional control after safe rollout.

## Update and regression surface

There are four policy evolutions (`v1 -> v2 -> v3 -> v4 -> v5`) and eight pipeline components.

| Metric | Shared software registry | Independent policy copies | ProofBit contract |
| --- | ---: | ---: | ---: |
| Managed active policy copies | **1** | 8 | **1** |
| Policy-copy updates | **4** | 32 | **4** |
| Safe activation steps | **4** | 32 | **4** |
| Regression-suite invocations | **4** | 32 | **4** |
| Regression-suite failures | 0 | 0 | 0 |
| Active descriptor bytes | **16 B** | 128 B | **16 B** |
| Propagated token bytes | **32 B** | 32 B | **32 B** |

For the independently managed design:

```text
32 / 4 = 8x policy-copy update work
32 / 4 = 8x regression-suite invocations
128 / 16 = 8x active descriptor footprint
```

That is the expected N-component replication cost in this frozen model.

However:

```text
software_shared_registry == proofbit_contract
```

on update count, safe activation steps, regression-suite invocations, active descriptor bytes and propagated token bytes.

So the one-contract benefit is **not uniquely ProofBit**.

## Mixed-version early-activation stress

The primary independent rollout waits until every required component has the new policy before activation and therefore has no availability loss.

A secondary stress intentionally activates the new receipt during partial rollout.

Across four evolutions and seven intermediate phases per evolution:

```text
mixed-version phases = 28
valid probes         = 2,800
valid probes blocked = 2,800
unsafe accepts       = 0
```

The old policy copies fail closed on version/digest mismatch.

This is not semantic drift and not an implementation bug. It is the correctness/availability tradeoff of activating a new policy while a required path still contains old independently managed copies.

## Runtime

Official 11-round medians:

| System | Median requests/s | Median elapsed for 50k requests |
| --- | ---: | ---: |
| `software_shared_registry` | 316,035/s | 158.210 ms |
| `software_independent_copies` | **324,115/s** | **154.266 ms** |
| `proofbit_contract` | 317,041/s | 157.708 ms |

ProofBit vs shared conventional throughput:

```text
317,040.9 / 316,035.2 = 1.0032x
```

or about +0.3% in this run.

That difference is far too small to treat as a stable crossover on a shared GitHub runner.

The independent-copy implementation is also slightly faster in this Python fixture even though it has a larger management/update surface. Runtime after a completed safe rollout and rollout-management cost are separate axes.

**No runtime winner is claimed.**

## Four-axis interpretation

### Utility

All systems are 100% correct after safe activation.

**Result: tie.**

### Proof / trust

The shared conventional receipt and ProofBit token both bind the request to an exact policy version, required-mask and stable policy digest in this frozen benchmark.

**Result: no externally observable ProofBit-specific advantage in TC06.**

### Cost

Independent policy copies pay 8x update/regression/active-descriptor work at eight components.

Shared conventional software and ProofBit both avoid that replicated policy-copy cost in the frozen model.

**Result: single-authoritative-contract architecture wins; ProofBit does not uniquely own the win.**

### Speed

All three implementations are close after safe activation. The small ordering is not treated as universal.

**Result: no ProofBit speed win.**

## What TC06 falsified

TC06 falsifies or narrows several tempting narratives:

1. **"Only ProofBit can reduce policy evolution to one authoritative update."**
   Not shown. A conventional data-driven shared registry with a typed receipt gets the same frozen update surface.

2. **"Independent components inevitably become unsafe during rollout."**
   False in this fixture. Competent version/digest checks fail closed. The cost is replicated updates and, under early activation, availability loss.

3. **"ProofBit's 32-byte token gives a representation advantage."**
   Not shown. The conventional shared receipt is exactly the same size.

4. **"A tiny throughput difference proves a crossover."**
   Not supported. ProofBit and shared software differ by only about 0.3% in the official median.

## Current evidence-supported conclusion

The narrow supported statement is:

> Replicating trust-policy state across independently managed components scales update and regression surface with the number of copies. A single authoritative, version-bound contract plus a propagated receipt avoids that replication. ProofBit can represent this pattern natively, but TC06 demonstrates that competent conventional shared-policy software can reproduce the same correctness, update surface and representation size.

The remaining ProofBit hypothesis must therefore move beyond benefits obtainable simply by introducing a good shared policy registry and typed receipt.

## Next falsifiable experiment: PB-TRUST-COMPOSE-07

The next useful boundary is **cross-language / cross-ownership conformance**, where one shared runtime library is not automatically available.

Candidate design:

```text
Python service
   -> Rust service
   -> Node/TypeScript service
   -> independently versioned adapter
   -> durable outcome consumer
```

Compare:

1. conventional per-language policy libraries generated/implemented from one spec;
2. conventional shared wire contract + conformance suite;
3. ProofBit canonical binary contract + conformance suite.

Evolve the same trust policy and introduce only realistic integration pressure:

```text
unknown field / version
integer width mismatch
canonicalization mismatch
old consumer
retry identity mismatch
outcome-schema evolution
```

Measure:

```text
cross-language oracle accuracy
silent semantic divergence
number of language-specific code updates
number of generated artifacts
conformance-suite failures caught before activation
wire bytes
runtime
rollout blocking
```

No deliberately buggy implementation should be used. If an ordinary canonical wire schema plus generated validators matches ProofBit, that is another valid negative ProofBit result.

## Claim boundary

These results are Python software-reference evidence. They do not establish real organizational engineering-hours savings, deployment-system behavior, cross-language ABI behavior, cryptographic authenticity, distributed consensus, silicon performance, energy/area savings, novelty, patentability, or universal superiority over conventional policy services.
