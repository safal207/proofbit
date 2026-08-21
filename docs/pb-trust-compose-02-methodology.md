# PB-TRUST-COMPOSE-02 Methodology

## Question

PB-TRUST-COMPOSE-01 showed that field-by-field trust metadata reconstruction can become expensive as component boundaries grow, while a strong shared-object software control remains competitive.

PB-TRUST-COMPOSE-02 asks a narrower follow-up:

> What happens when trust metadata must actually cross process boundaries and both conventional software and ProofBit pay real encode, decode, IPC, scheduling, and validation costs?

## Frozen protocol

```text
PB-TC02/v0.1 real-ipc-trust-transport
```

Default workload:

- 2,000 trials;
- 12% contamination;
- 1, 2, 4, and 8 worker-process boundaries;
- 6 equally distributed fault classes:
  - `UNKNOWN`;
  - `STALE_AUTHORITY`;
  - `REPLAY`;
  - `CONFLICT`;
  - `REBIND_STATEMENT`;
  - `FALSE_SUCCESS`.

Oracle:

- `VALID` -> dispatch yes, terminal success yes;
- `FALSE_SUCCESS` -> dispatch yes, terminal success no;
- all other fault classes -> dispatch no, terminal success no.

## Real transport boundary

The benchmark uses Python `multiprocessing.Pipe` and `send_bytes` / `recv_bytes`.

For N boundaries, a request is decoded and re-encoded by N worker processes before final authorization/outcome evaluation. The final worker returns a fixed 2-byte `(dispatched, terminal_success)` result record to the parent. Worker startup happens before the timed region. Process scheduling, encode/decode, IPC system calls, and final validation are inside the measured wall-clock path.

This is real same-host process IPC, but it is **not** a network benchmark and not representative of a specific production RPC stack.

## Three competent systems

### 1. `software_json`

Conventional structured software trust policy carried as a canonical compact JSON envelope.

It checks:

- evidence presence;
- exact statement/action binding;
- authority;
- epoch;
- replay;
- conflict;
- separate outcome evidence.

### 2. `software_compact`

Anti-strawman control.

The exact same conventional software policy uses the same fixed-width compact binary record as the ProofBit path. This prevents a `binary beats JSON` result from being misreported as a ProofBit result.

### 3. `proofbit_compact`

The same compact binary record is decoded into ProofBit evidence and evaluated through `ProofProcessor`, including exact `expected_statement` side-effect binding and separate outcome evidence.

## Compact record

v0.1 uses a fixed 42-byte network-order request record containing:

```text
kind
flags
action_id
statement_id
proof_id
authority
epoch
provenance
outcome_proof_id
```

The integer action/statement ids are benchmark registry ids. They are **not** cryptographic hashes and do not constitute a security claim.

## Measurement order

Always interpret results in this order:

1. oracle correctness;
2. unsafe authorization / false-success behavior;
3. statement binding;
4. request payload bytes;
5. application payload bytes carried across real IPC edges;
6. end-to-end throughput.

No synthetic winner score is permitted.

## Metrics

Per implementation and boundary depth:

- oracle-correct trials;
- unsafe authorization dispatches;
- false-success claims;
- missed valid dispatches;
- wall-clock elapsed ns;
- trials/s;
- encoded request payload bytes;
- mean request payload bytes;
- request application-payload bytes across IPC edges;
- response application-payload bytes;
- total application-payload bytes passed to `send_bytes`/`recv_bytes`;
- transport message count;
- validation-boundary count.

The byte counters are intentionally named **IPC payload bytes**. They do not include `multiprocessing` framing, pipe metadata, kernel buffers/copies, scheduler overhead expressed as bytes, or network packet overhead.

## Fairness controls

1. All systems receive the same deterministic trial stream and oracle.
2. `software_compact` uses the same fixed-width wire encoding as `proofbit_compact`.
3. ProofBit does not get cryptographic verification credit; no cryptographic verifier runs.
4. Worker process startup is excluded from the timed region for all systems.
5. Process scheduling and encode/decode remain inside end-to-end timing.
6. Unsupported physical interpretations are not inferred from Python IPC timing.
7. Negative results must remain in the scorecard.

## What would falsify the transport advantage hypothesis?

If compact conventional software remains equally correct and consistently faster or cheaper than ProofBit under the same wire encoding and real IPC boundaries, PB-TC02 does not support a ProofBit transport-performance advantage.

If JSON is slower but compact software and ProofBit are similar, the result belongs primarily to encoding choice rather than proof-native semantics.

## Non-claims

PB-TC02 is not:

- a silicon benchmark;
- a CPU/GPU/TPU performance comparison;
- a network/RPC benchmark;
- a cryptographic proof benchmark;
- a physical energy/area measurement;
- a universal crossover claim;
- a novelty or patentability claim.
