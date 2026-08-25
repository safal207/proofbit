# PB-TRANSITION-02 Methodology

## Question

Can different computing architectures satisfy the same externally frozen state-transition contract while preserving their own native execution and justification semantics?

`PB-TRANSITION-02` is the first deliberately small common-denominator workload across:

- conventional software without a support check;
- conventional software with an application guard;
- ProofBit;
- CaPU;
- COSMIC ORGANICS / MORPHOS.

It is not a claim that those systems implement the same internal mechanism.

## Frozen protocol

```text
PB-T02/v0.1
binary-endpoint
alternating-direction
deterministic-insufficient-support
```

Default run:

```text
trials                 10,000
VALID                    9,000
INSUFFICIENT_SUPPORT     1,000
0 -> 1 requests           5,000
1 -> 0 requests           5,000
```

The insufficient-support cases are spread deterministically over the stream. No random-number generator is used.

## Common oracle

For every trial there is a source state and the opposite target state.

```text
VALID:
    final_state == target

INSUFFICIENT_SUPPORT:
    final_state == source
```

The second rule matters: an unsupported transition must not happen merely because the requested target is syntactically valid.

## Adapter mapping

| System | VALID mapping | INSUFFICIENT_SUPPORT mapping | Native evidence category |
| --- | --- | --- | --- |
| Raw software baseline | unconditional transition | unconditional transition | none |
| Software-guarded baseline | `support == true` | `support == false` | application boolean guard |
| ProofBit | statement/value/authority/epoch-bound evidence | `UNKNOWN` | ProofBit evidence object |
| CaPU P6 | cause + durable commit | missing cause/commit | causal commit decision |
| MORPHOS | two above-threshold pulses through A/M/C | two sub-threshold pulses | deterministic phase-transition trace |

The mappings share the external oracle, not an internal ontology.

## Why the software-guarded baseline is mandatory

Comparing a proof-aware architecture only with an unconditional CPU baseline would be a strawman. Ordinary software can enforce a simple boolean precondition cheaply.

`BaselineSoftwareGuarded` is therefore a first-class control. If it satisfies this simple workload faster and more cheaply than a proof-native architecture, the result is preserved.

The research question is not whether proof is required for every conditional branch. Later benchmark families must test where richer semantics such as provenance, authority, freshness, replay resistance, conflict preservation, derivation, and outcome grounding change the engineering tradeoff.

## Metrics

### Utility

```text
correct_valid_transitions
invalid_transitions_preserved
unsafe_invalid_transitions
missed_valid_transitions
oracle_accuracy
```

### Proof / justification

```text
native_justified_valid_transitions
native_justification_coverage
evidence_kind
```

`native_justification_coverage` means only that the architecture produced its declared native evidence on successful valid trials. It does **not** mean all evidence kinds are equally strong.

The following are categorical and must not be collapsed into one proof score:

```text
application boolean guard
ProofBit evidence
CaPU cause + commit
MORPHOS transition trace
```

### Speed

```text
elapsed_ns
trials_per_sec
correct_useful_transitions_per_sec
justified_useful_throughput
```

For the strongest current software comparison, all adapters should be executed in one GitHub Actions job on the same hosted runner. Language/runtime differences remain part of the measured software-reference result.

### Cost

Version 0.1 has only software execution time plus architecture-specific operation counters.

The following are explicitly unavailable and must not be inferred:

```text
hardware energy
silicon area
physical memory overhead
power
thermal cost
manufacturing cost
```

MORPHOS's simulated drive magnitude is dimensionless model data, not joules. Native step counts are architecture-specific and are not directly comparable as hardware cycles.

## Ranking rule

Do not compute one synthetic winner score.

Interpret in this order:

```text
same workload
  -> oracle correctness
  -> false accept / false reject behavior
  -> native evidence semantics
  -> speed and measured cost
```

A system can be faster while providing weaker evidence. Another can provide richer evidence while being slower. Both facts should remain visible.

## Scientific boundary

PB-TRANSITION-02 is a deterministic software research benchmark. It is not:

- a CPU/GPU/TPU silicon benchmark;
- a physical energy experiment;
- proof that MORPHOS is a material processor;
- proof that CaPU, ProofBit, and MORPHOS evidence are equivalent;
- evidence of universal architecture superiority.

## Next step

PB-TRANSITION-03 should preserve a common external oracle while adding richer failure semantics, especially stale authority, replay, conflict, and outcome grounding. That is where proof-native or causal architectures should be tested against increasingly capable conventional software guards rather than against a deliberately weak baseline.
