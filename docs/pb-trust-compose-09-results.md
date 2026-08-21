# PB-TRUST-COMPOSE-09 — Executed Results

## Status

Executed in GitHub Actions on the cleaned TC09 harness.

Official evidence:

- workflow: `pb-trust-compose-09`
- run: `32481079088`
- job: `96767366996`
- Ubuntu 24.04.4
- CPython 3.12.14
- 11 rotated-order rounds
- 500 valid requests/system/round for the valid-path runtime measurement
- real persistent Python subprocess worker
- real protected-effect file writes

All four TC09 tests, the executable benchmark, and the frozen enforcement oracle passed.

## Frozen attack result

| System | Oracle accuracy | Unsafe side effects | False success | Bypass failures |
| --- | ---: | ---: | ---: | ---: |
| application validator | 12.5% | **6** | **1** | **7** |
| software reference monitor | **100%** | **0** | **0** | **0** |
| ProofBit execution boundary | **100%** | **0** | **0** | **0** |

The seven failing application-level cases are not evidence that the validator algorithm is weak. The normal-path validator is competent. The failures arise because validation is separated from the only authoritative effect boundary, so already-validated state or alternate entrypoints can cross the validation/execution gap.

The two mandatory-boundary architectures block all tested bypasses:

```text
DIRECT_CALL_INVALID_AUTHORITY
ALTERNATE_ENTRYPOINT_STALE
CACHED_APPROVAL_AFTER_EPOCH_CHANGE
MUTATE_AFTER_VALIDATE_REBIND
REPLAY_AFTER_VALIDATE
DESERIALIZATION_BYPASS
FALSE_SUCCESS_SELF_REPORT
```

`VALID_API` still executes successfully in all three systems.

## TCB placement

| Metric | Application validator | Software reference monitor | ProofBit boundary |
| --- | ---: | ---: | ---: |
| mandatory effect-boundary checks | 0 | **1** | **1** |
| application validation sites | 1 | 0 | 0 |
| protected-resource writer processes | 1 | 1 | 1 |
| terminal outcome authority | application report | worker receipt | worker receipt |

This is the central negative result:

> A conventional mandatory software reference monitor exactly reproduces ProofBit's tested bypass resistance in TC09. The safety benefit belongs to mandatory effect-boundary enforcement and authoritative outcome receipts, not uniquely to ProofBit.

## Valid-path runtime

Median over 11 rotated rounds:

| System | Valid effects/s |
| --- | ---: |
| application validator | **8,673.9/s** |
| software reference monitor | 8,227.2/s |
| ProofBit execution boundary | 7,840.8/s |

Ratios:

```text
ProofBit / software reference monitor = 0.9530x
software reference monitor / application validator = 0.9485x
ProofBit / application validator = 0.9040x
```

The raw per-round values overlap and the measurement includes Python subprocess IPC plus file I/O. TC09 therefore does not claim a stable runtime winner. The safety comparison is the primary result.

## What TC09 does prove

Within the frozen software fixture:

- application validation before the side-effect seam is bypassable under the tested TOCTOU/replay/rebinding/direct-entry patterns;
- moving validation into the mandatory effect worker closes those tested bypasses;
- a competent conventional reference monitor closes them just as well as ProofBit;
- outcome grounding must be authoritative at or after the effect, not a caller self-report.

## What TC09 does **not** prove

The protected effect file is writable only by the worker process **inside this fixture**.

TC09 explicitly does not test a process with direct OS/native write access to the protected resource. If an attacker can write the resource without traversing the worker, both the software reference monitor and the software ProofBit boundary can be bypassed.

The logical `direct` / `alternate` / `deser-bypass` labels share one stdio IPC transport; this is an enforcement-placement benchmark, not a multi-transport benchmark.

No kernel privilege boundary, cryptographic authenticity, hardware enforcement, energy, novelty, patentability, or universal-superiority claim is made.

## Next falsifiable boundary

`PB-TRUST-COMPOSE-10`: resource / privilege bypass.

Move the protected resource behind an OS-enforced capability boundary and compare:

1. application validator;
2. software reference monitor with file/socket permissions or a broker process;
3. ProofBit-style proof-aware boundary;
4. an explicit hostile/native writer attempting to bypass the broker.

Measure:

- direct resource-write success;
- privilege/capability escape surface;
- number of trusted writers;
- enforcement points;
- unsafe side effects;
- outcome auditability;
- valid-path cost.

If OS capability isolation plus a conventional reference monitor again matches ProofBit, that is another valid negative result and the remaining unique ProofBit hypothesis moves closer to actual ISA/memory/hardware enforcement.
