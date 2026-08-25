# PB-TRANSITION-02 Results

## Status

**EXECUTED / COMMON SOFTWARE-REFERENCE SCORECARD**

GitHub Actions run: `32469996704`  
Job: `PB-TRANSITION-02 common workload` / `96734593758`

Environment:

```text
Ubuntu 24.04.4
CPython 3.12.14
Rust 1.98.0
x86_64 GitHub-hosted runner
```

Pinned external inputs:

```text
CaPU       b04c6bd2b5f9518d33a951184f18e98ebddfa714
MORPHOS    9e84fb812be4ec96ab08744dc43ae1e308ba8392
```

Protocol:

```text
PB-T02/v0.1 binary-endpoint alternating-direction deterministic-insufficient-support
```

Workload:

```text
10,000 total trials
 9,000 VALID
 1,000 INSUFFICIENT_SUPPORT
 5,000 requests 0 -> 1
 5,000 requests 1 -> 0
```

Common oracle:

```text
VALID                 -> final_state == target
INSUFFICIENT_SUPPORT  -> final_state == source
```

## Scorecard

| System | Oracle accuracy | Unsafe unsupported | Missed valid | Native justification coverage | Evidence category | Trials/s | Correct useful/s | Justified useful/s |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| Raw software baseline | 90% | 1,000 | 0 | 0% | none | 3,244,502 | 2,920,052 | 0 |
| Software-guarded baseline | 100% | 0 | 0 | 0% | application boolean guard | 3,150,257 | 2,835,231 | 0 |
| ProofBit | 100% | 0 | 0 | 100% | statement/value/authority/epoch-bound evidence | 324,461 | 292,015 | 292,015 |
| CaPU P6 | 100% | 0 | 0 | 100% | cause + durable commit | 4,388,161 | 3,949,345 | 3,949,345 |
| MORPHOS | 100% | 0 | 0 | 100% | deterministic A/M/C phase-transition trace | 81,609 | 73,448 | 73,448 |

All speed values above come from the same GitHub Actions job/host, but they remain **software-reference implementation results**, not normalized hardware performance. CaPU is Rust, while the other current implementations in this job are Python; each architecture also performs different native work.

## Utility

The raw baseline demonstrates the consequence of unconditional execution:

```text
1,000 unsupported requests -> 1,000 unsafe transitions
```

Every guarded architecture/control preserved all 1,000 unsupported source states while completing all 9,000 valid transitions:

```text
SoftwareGuarded  10,000 / 10,000 oracle-correct
ProofBit         10,000 / 10,000 oracle-correct
CaPU             10,000 / 10,000 oracle-correct
MORPHOS          10,000 / 10,000 oracle-correct
```

## The important negative result

A conventional application-level boolean guard is already sufficient for this deliberately simple workload.

Measured in this run:

```text
SoftwareGuarded: ~3.15M trials/s
ProofBit:        ~0.324M trials/s
```

The current Python ProofBit semantic reference is therefore about **9.7x slower** than the simple guarded Python control on PB-T02.

This is not a failure of the benchmark. It is the intended anti-strawman result:

> proof-native machinery should not be justified for a workload whose complete authority model is one trusted boolean.

ProofBit must earn its additional cost on richer contracts where the boolean guard is no longer sufficient: provenance, authority, freshness, replay, conflict, derivation, execution binding, and outcome grounding.

## CaPU result

CaPU P6 produced:

```text
10,000 / 10,000 oracle-correct
0 unsafe unsupported transitions
0 missed valid transitions
100% cause+commit coverage on valid transitions
~4.39M trials/s
```

The Rust P6 software reference was about `1.39x` the measured throughput of the CPython software-guarded control in this run. This must **not** be interpreted as a processor-hardware speedup: language/runtime and implementation work differ.

The useful result is semantic plus executable:

> the common VALID/INSUFFICIENT_SUPPORT oracle can be represented directly through CaPU's existing cause + durable-commit boundary without weakening the P6 rule.

## MORPHOS result

MORPHOS produced:

```text
10,000 / 10,000 oracle-correct
0 unsafe unsupported transitions
0 missed valid transitions
100% native transition-trace coverage
20,000 lattice steps
18,000 phase changes
~81.6k trials/s
```

VALID transitions use two above-threshold pulses through the real single-cell A/M/C simulator. INSUFFICIENT_SUPPORT uses two sub-threshold pulses and leaves the source endpoint unchanged.

The reported simulated drive magnitude (`~8300` total model units) is dimensionless and is **not joules or physical energy**.

## Proof / justification interpretation

The three `100%` native-coverage results do not mean the evidence is equivalent.

```text
ProofBit
  statement/value + provenance + authority + epoch evidence

CaPU
  cause + durable commit / transition legitimacy

MORPHOS
  deterministic phase-transition trace
```

They answer different justification questions. PB-T02 records coverage categorically and intentionally has no cross-architecture numeric proof-strength score.

The software-guarded baseline is oracle-correct but its application boolean is not counted as a native proof object. This prevents correctness from being confused with provenance/authority evidence while still giving conventional software a fair behavioral control.

## Cost interpretation

PB-T02 v0.1 measures only:

```text
software wall-clock time
architecture-specific operation counters
```

It does not yet measure:

```text
hardware energy
silicon area
physical memory overhead
power / thermals
manufacturing cost
```

Native step counts are not hardware cycles and are not directly comparable across architectures.

## Current conclusion

PB-TRANSITION-02 establishes a valid common denominator, but it is intentionally too simple to justify ProofBit by itself.

The useful frontier is now visible:

```text
simple trusted boolean policy
    -> ordinary software guard is enough

richer evidence / authority / temporal failure semantics
    -> must be tested next
```

This is the correct transition to `PB-TRANSITION-03` rather than optimizing PB-T02 until ProofBit appears to win.

## Next benchmark

Freeze a common transition oracle that includes, at minimum:

```text
VALID
UNKNOWN
STALE_AUTHORITY
REPLAY
CONFLICT
FALSE_SUCCESS / missing outcome evidence
```

Then compare increasingly capable conventional software enforcement against ProofBit and CaPU, while MORPHOS receives only the fault classes its native transition model can express without semantic substitution.

The benchmark should preserve `UNSUPPORTED` explicitly rather than award a safety point for an unmodelled failure class.
