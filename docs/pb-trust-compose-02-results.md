# PB-TRUST-COMPOSE-02 Results

## Status

`EXECUTED`

Frozen protocol:

```text
PB-TC02/v0.1 real-ipc-trust-transport
```

Official repeated run:

- GitHub Actions run: `32473721038`
- job: `96745660934`
- runner: GitHub-hosted Ubuntu 24.04.4
- Python: CPython 3.12.14
- benchmark head: `cc2801628b401137df51888497fb52116deb2ef1`
- rounds: 5 independent full pipeline runs
- trials per round: 2,000
- contamination: 12%
- process boundaries: 1, 2, 4, 8

Each round contains:

- 1,760 `VALID`;
- 40 `UNKNOWN`;
- 40 `STALE_AUTHORITY`;
- 40 `REPLAY`;
- 40 `CONFLICT`;
- 40 `REBIND_STATEMENT`;
- 40 `FALSE_SUCCESS`.

## Correctness

Every implementation in every round and at every tested boundary depth produced:

- 2,000 / 2,000 oracle-correct trials;
- 0 unsafe authorization dispatches;
- 0 false-success claims;
- 0 missed valid dispatches.

PB-TC02 therefore does **not** show a correctness advantage over competent conventional software.

## Fair controls

Three implementations were executed:

1. `software_json` — conventional trust policy with a canonical JSON request envelope;
2. `software_compact` — the same conventional trust policy with the exact same 42-byte binary request format used by ProofBit;
3. `proofbit_compact` — the same 42-byte request format decoded into ProofBit evidence and evaluated through `ProofProcessor`.

The compact conventional control is the primary comparison for proof-semantics overhead. JSON comparisons mainly expose encoding and payload-size effects.

## Median throughput

Median of five independent full pipeline rounds:

| Process boundaries | Software JSON | Software compact | ProofBit compact | ProofBit / compact | ProofBit / JSON |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 13,040/s | 22,796/s | 18,877/s | **0.828x** | 1.448x |
| 2 | 7,340/s | 12,545/s | 11,362/s | **0.906x** | 1.548x |
| 4 | 3,970/s | 7,327/s | 7,034/s | **0.960x** | 1.772x |
| 8 | 2,110/s | 3,928/s | 3,823/s | **0.973x** | 1.812x |

### Primary result

The earlier single-run observation of a slight ProofBit win at eight boundaries did **not** survive repeated measurement.

On five-round medians, compact conventional software remains faster at every tested boundary depth.

However, the relative ProofBit overhead shrinks as IPC depth grows:

```text
PB / compact software throughput

1 boundary   0.828x
2            0.906x
4            0.960x
8            0.973x
```

This is consistent with fixed ProofBit semantic work becoming a smaller fraction of end-to-end latency as real IPC transport dominates. It is not evidence of a universal crossover.

## Payload cost

Mean encoded request size is deterministic:

```text
software_json     234.6755 bytes
software_compact   42 bytes
proofbit_compact   42 bytes
```

The compact request is about 5.59x smaller than the JSON request in this frozen workload.

Because `software_compact` and `proofbit_compact` use the exact same request record and the same 2-byte result record, their IPC application-payload totals are identical:

| Boundaries | Compact total IPC payload / trial | JSON total IPC payload / trial |
| ---: | ---: | ---: |
| 1 | 44 B | 236.6755 B |
| 2 | 86 B | 471.351 B |
| 4 | 170 B | 940.702 B |
| 8 | 338 B | 1,879.404 B |

These counters cover application payload bytes passed through `send_bytes` / `recv_bytes`. They exclude multiprocessing framing, kernel buffers/copies, and network packet overhead.

## What the result supports

PB-TC02 supports a narrow result:

> Compact encoding materially reduces payload size and improves this same-host IPC workload relative to the JSON control. When compact conventional software and compact ProofBit use the same wire representation, conventional software remains faster on the current Python reference, while the relative ProofBit runtime penalty narrows as process-boundary cost increases.

## What the result does not support

PB-TC02 does **not** support claims that:

- ProofBit is faster than competent compact conventional software;
- ProofBit has a stable IPC crossover by eight boundaries;
- binary encoding itself is a ProofBit advantage;
- local Python IPC predicts production RPC/network behavior;
- current Python timings predict silicon performance;
- the 42-byte format is a cryptographic proof format;
- ProofBit is universally superior.

## Relationship to PB-TRUST-COMPOSE-01

PB-TC01 showed a large apparent advantage over software that reconstructs nine metadata fields object-by-object at every modeled boundary, while a shared immutable software envelope remained faster.

PB-TC02 replaces that synthetic reconstruction cost with real process transport and adds a compact conventional-software control. The large TC01 speed advantage does not persist against that stronger control.

This is an important negative result: a well-designed conventional compact trust envelope is a strong baseline and must remain in future ProofBit comparisons.

## Next falsifiable target

The next useful experiment should test where proof-native semantics can provide value that is not merely an encoding choice:

- in-flight epoch invalidation;
- stale cached authorization after a context change;
- duplicate delivery across processes;
- statement rebinding after decode;
- authority revocation while requests are in flight;
- derived decisions that must preserve provenance;
- separate asynchronous outcome receipt;
- audit reconstruction after partial process failure.

The comparison must keep the compact conventional software control and measure both operational correctness and the amount of validation/invalidation/audit work required.
