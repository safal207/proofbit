# PB-TRUST-COMPOSE-01 methodology

Protocol: `PB-TC01/v0.1 composed-trust-propagation`

## Question

Does ProofBit earn its extra machinery when one trust decision must survive many component boundaries, rather than one local guard?

The experiment is deliberately falsifiable. Conventional software is given competent controls, including a best-case same-process implementation that shares one immutable trust envelope instead of copying metadata at every hop.

## Frozen oracle

The deterministic stream contains `VALID` plus six fault classes:

- `UNKNOWN`
- `STALE_AUTHORITY`
- `REPLAY`
- `CONFLICT`
- `REBIND_STATEMENT`
- `FALSE_SUCCESS`

Expected behavior:

| Kind | Dispatch | Terminal success |
| --- | --- | --- |
| VALID | yes | yes |
| FALSE_SUCCESS | yes | no |
| all other faults | no | no |

`FALSE_SUCCESS` therefore cannot be “solved” by blocking dispatch.

`REBIND_STATEMENT` tests action binding directly: evidence created for action A must not authorize action B.

## Systems

### 1. Conventional software — shared helper

A strong non-ProofBit control. One immutable `SoftwareMessage` is shared by reference across component hops and evaluated by a centralized trust guard at the side-effect boundary.

This intentionally avoids metadata reconstruction cost. If this design remains equally correct and cheaper, that is a valid negative result for ProofBit.

### 2. Conventional software — serialized plumbing

The same oracle and guard, but all trust fields are reconstructed explicitly at every modeled serialization/RPC boundary.

The benchmark counts field assignments deterministically. This represents one common distributed-software shape, not all possible conventional architectures.

### 3. ProofBit semantic reference

The current Python `ProofProcessor` carries evidence to the final side-effect boundary and requires the proof statement to match the expected action.

Logical `proof_ref_hops` are counted separately from measured runtime. They are a model of a future proof plane, not evidence that current hardware transports one compact proof reference.

## Boundary sweep

Default component-boundary counts:

`1, 2, 4, 8, 16, 32`

Default stream:

- 10,000 trials
- 12% contamination
- 8,800 valid trials
- 200 trials for each of the six fault classes

## Metrics

Correctness first:

- oracle accuracy
- unsafe authorization dispatches
- false-success claims
- missed valid dispatches
- per-fault correctness

Composition work:

- component boundary count
- explicit metadata field assignments
- shared-object reference hops
- logical proof-reference hops

Cost:

- elapsed wall-clock time in CPython
- trials per second
- throughput ratios versus the two software controls

## Interpretation rules

1. No single winner score.
2. The shared software helper is not downgraded because it lacks ProofBit objects.
3. Equal oracle correctness does not imply equal audit/evidence semantics.
4. Field-assignment counts are deterministic benchmark operations, not hardware bytes or energy.
5. `proof_ref_hops` are conceptual logical operations, not measured physical transport.
6. Python throughput is not silicon, cycle, area, power, cryptographic-verifier, or network performance.
7. Any measured crossover applies only to this frozen reference implementation.
8. If conventional structured software stays simpler, equally correct, and cheaper as boundaries increase, the composition hypothesis is not supported by this benchmark.

## RED -> GREEN statement-binding preflight

Before this benchmark was added, an executable regression was introduced for action rebinding.

Baseline behavior lacked an `expected_statement` binding at `ProofProcessor.guarded_execute()`; CI failed only the two new statement-binding tests. The minimal fix adds optional expected-statement binding before proof consumption so a rejected rebinding attempt cannot burn a valid single-use grant.

This preflight is part of the evidence packet because it demonstrates that the composition benchmark changed an actual executable boundary rather than only adding documentation.
