# PB-TRUST-COMPOSE-03 Methodology

## Question

PB-TRUST-COMPOSE-02 showed that, with identical compact records and a static trust oracle, competent conventional software remained faster than the current ProofBit Python reference while the relative ProofBit penalty narrowed as real IPC depth increased.

PB-TRUST-COMPOSE-03 asks a different question:

> When authority changes while an authorization is already in flight, what correctness and maintenance work is required to keep stale authority, replay, rebinding, provenance loss, and unsupported success from crossing a real process boundary?

The benchmark is designed to falsify a ProofBit-specific advantage if a strong conventional design can achieve the same result at equal or lower cost.

## Compared systems

All systems use the **same compact binary action, outcome, control, and response record formats**.

### `software_eager`

Conventional software with an epoch cache replicated at every process boundary.

When authority is revoked, the parent sends an epoch-update control record to **every worker**. Every worker checks the incoming action epoch against its local epoch before forwarding. The final worker also performs the full authorization decision.

This represents eager distributed cache invalidation.

### `software_lazy`

Conventional software using the same compact records, but only the final dispatch seam is authoritative.

Revocation updates only the final gate. Intermediate workers forward the evidence envelope without independently treating it as current authority.

This is a deliberately strong anti-strawman control.

### `proofbit_lazy`

Same lazy topology and same compact records as `software_lazy`, but the final authorization and outcome decisions are evaluated through the ProofBit reference model.

The benchmark **must not** attribute a benefit to ProofBit if `software_lazy` achieves the same semantics at equal or lower cost.

## Frozen dynamic faults

The workload distributes contamination deterministically across:

- `IN_FLIGHT_REVOKE`
- `REPLAY`
- `REBIND_STATEMENT`
- `PROVENANCE_DROP`
- `FALSE_SUCCESS`

All remaining trials are `VALID`.

### Oracle

| Kind | Primary dispatch | Duplicate dispatch | Terminal success |
| --- | --- | --- | --- |
| VALID | yes | n/a | yes |
| IN_FLIGHT_REVOKE | no | n/a | no |
| REPLAY | yes | no | yes |
| REBIND_STATEMENT | no | n/a | no |
| PROVENANCE_DROP | no | n/a | no |
| FALSE_SUCCESS | yes | n/a | no |

## Deterministic in-flight revocation

`IN_FLIGHT_REVOKE` is synchronized with a barrier:

1. parent sends an authorization frame;
2. worker 0 receives it;
3. worker 0 acknowledges receipt to the parent and blocks;
4. parent increments the authority epoch;
5. parent sends epoch-control records according to the compared topology;
6. parent releases worker 0;
7. the already-received old-epoch authorization continues through the pipeline.

Therefore the revocation occurs after the request has entered the process pipeline, not before it is issued.

## Replay

For a `REPLAY` trial, the exact same authorization record and proof identifier are delivered twice.

The first delivery is a valid single-use grant. The second must be rejected. A separate outcome receipt is then required for terminal success.

## Statement rebinding

At one deterministic intermediate stage, `REBIND_STATEMENT` changes the statement identifier while retaining the authorization proof identifier.

A proof for action A must not authorize mutated action B.

## Provenance loss

At one deterministic intermediate stage, `PROVENANCE_DROP` clears the provenance reference.

The consumption contract requires provenance to remain bound to the action. Both competent software and ProofBit controls enforce this explicit workload policy.

## Outcome grounding

Authorization and terminal success are separate.

`VALID` and the accepted first delivery of `REPLAY` receive a separate compact outcome record after dispatch. `FALSE_SUCCESS` does not receive an outcome record and must therefore remain non-terminal.

## Metrics

Correctness is evaluated before performance:

- oracle accuracy;
- unsafe authorization dispatches;
- false-success claims;
- missed valid dispatches;
- replay duplicates accepted.

Maintenance and transport metrics:

- control messages;
- control application-payload bytes;
- request/outcome application-payload bytes;
- response application-payload bytes;
- total application-payload bytes carried across real IPC edges;
- executed epoch checks;
- full authorization validations;
- outcome validations;
- applied control updates;
- mutation events;
- audit decision records;
- elapsed wall-clock time;
- trials per second.

Five independent full pipeline rounds are used for the official scorecard; throughput is summarized by the median while raw round values are retained.

## Primary comparison

The primary semantic comparison is:

```text
software_lazy  vs  proofbit_lazy
```

They have:

- identical compact records;
- identical lazy one-gate revocation topology;
- the same frozen oracle;
- the same actual process pipeline.

`software_eager` is a separate architecture experiment measuring replicated-cache invalidation work.

## Claim boundary

This is software reference evidence using same-host Python `multiprocessing.Pipe` IPC.

Application-payload byte counters exclude Pipe framing, kernel copies, scheduler internals, and physical transport details.

The benchmark does **not** measure:

- network RPC;
- cryptographic proof verification;
- processor cycles;
- chip area;
- energy;
- silicon implementation;
- patentability or novelty.

## Deferred question

Partial-process-failure audit reconstruction is intentionally deferred. It deserves a separate crash/recovery fixture rather than a simulated counter inside this benchmark.
