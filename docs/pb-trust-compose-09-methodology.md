# PB-TRUST-COMPOSE-09 — Enforcement Bypass / Trusted Computing Base

## Question

Can a trust decision remain authoritative if application code can bypass the place where validation happened?

TC09 moves the comparison from **policy correctness** to **mandatory enforcement topology**.

## Systems

1. `application_validator`
   - a competent application validator checks the same 56-byte authorization token on the normal path;
   - the protected effect worker itself does not enforce the token;
   - cached approval, alternate entrypoints, replayed dispatches, and direct effect calls can therefore cross the validation/execution gap.

2. `software_reference_monitor`
   - strongest conventional anti-strawman;
   - one mandatory validation point lives inside the only process allowed to write the protected effect resource;
   - final-boundary checks include exact framing, statement binding, authority, epoch, replay and provenance;
   - the worker emits the outcome receipt.

3. `proofbit_execution_boundary`
   - the same protected worker topology;
   - final authorization is expressed through `ProofProcessor` / `Evidence`;
   - `expected_statement` binds authorization to the exact requested action;
   - epoch and consume-once replay checks execute at the side-effect seam;
   - actual outcome is still a separate worker receipt.

A tie between `software_reference_monitor` and ProofBit is a valid negative result.

## Frozen attacks

```text
VALID_API
DIRECT_CALL_INVALID_AUTHORITY
ALTERNATE_ENTRYPOINT_STALE
CACHED_APPROVAL_AFTER_EPOCH_CHANGE
MUTATE_AFTER_VALIDATE_REBIND
REPLAY_AFTER_VALIDATE
DESERIALIZATION_BYPASS
FALSE_SUCCESS_SELF_REPORT
```

The replay case first executes one legitimate request, then reuses the already-approved dispatch. The cached-approval case changes the worker epoch *after* application validation but before execution.

## Oracle

For `VALID_API`, both the side effect and terminal success must be true.

For every attack case:
- protected side effect must remain false;
- terminal success must remain false.

`FALSE_SUCCESS_SELF_REPORT` forces the device operation to fail after authorization. The application-level architecture accepts the caller claim as its terminal report; the two mandatory-boundary architectures use the worker receipt.

## Real boundary used

The benchmark launches a real persistent Python subprocess for each enforcement architecture and performs real file writes for successful protected effects.

The logical entrypoint labels (`normal`, `direct`, `alternate`, `cached`, `mutated`, `replay`, `deser-bypass`) share one stdio IPC transport. TC09 therefore measures enforcement placement, not transport diversity.

## Fairness / anti-strawman

- Same authorization token shape: 56 bytes.
- Same statement, authority, epoch, replay and provenance semantics.
- Same protected resource worker.
- Same valid workload.
- The conventional reference monitor is allowed every final-boundary check that ProofBit uses.
- The monitor maintains its own consume-once replay set.
- Both strong systems use the worker's actual result as terminal outcome authority.
- Measurement order rotates across 11 rounds.
- Runtime comparison uses only repeated valid requests because blocked attacks perform less I/O and are not throughput-comparable.

## Resource-isolation assumption

The protected effect file is writable only by the worker process **inside this fixture**.

This is the central claim boundary. TC09 does **not** test an attacker who has OS/native write access to the protected resource. If such access exists, both a software reference monitor and the software ProofBit worker can be bypassed.

That deeper privilege/hardware boundary is intentionally left for a later experiment.

## Metrics

- oracle accuracy;
- unsafe protected side effects;
- false terminal success;
- number of bypass failures;
- mandatory effect-boundary checks;
- terminal outcome authority;
- median valid-path effects/second;
- exact per-round raw rates.

No single winner score is produced.

## Falsifiers

ProofBit has no unique TC09 enforcement advantage if a conventional mandatory reference monitor:
- blocks every tested bypass;
- produces zero false success;
- preserves the same valid availability;
- does so with comparable TCB placement.

If application validation also blocks every bypass despite enforcement remaining outside the effect worker, the benchmark hypothesis is falsified in the other direction.

## Claim boundary

This is a software reference experiment on one Linux runner:
- real subprocess isolation;
- real file side effects;
- logical, not physically distinct, alternate entrypoints;
- no kernel privilege boundary;
- no malicious native process with direct resource access;
- no cryptographic authenticity;
- no silicon, energy, novelty, patentability or universal-superiority claim.
