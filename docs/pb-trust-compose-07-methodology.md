# PB-TRUST-COMPOSE-07 methodology

Protocol: `PB-TC07/v0.1 cross-language-conformance`.

## Question

When the same trust contract crosses Python, Rust, and Node runtimes, do independently encoded validators, a conventional canonical contract, and a ProofBit canonical contract preserve the same semantics?

## Frozen wire contract

- policy descriptor: 16 bytes, big-endian;
- trust token: 56 bytes, big-endian;
- statement ID is `0xFEDCBA9876543210`, intentionally above JavaScript's safe integer range;
- known primitive mask: statement, authority, epoch, replay, provenance, outcome;
- strict length and reserved-field validation.

## Compared systems

1. `software_per_language`: each language owns the current policy constants in validator source.
2. `software_canonical_contract`: strongest conventional anti-strawman; one 16-byte canonical descriptor drives generic validators in all languages.
3. `proofbit_contract`: the same 16-byte descriptor and 56-byte wire representation, interpreted as a ProofBit proof contract.

The conventional canonical control deliberately receives the same representation and validation semantics as ProofBit. A tie is a valid negative result.

## Frozen conformance vectors

- valid high-64-bit statement;
- unknown version;
- unknown required bit;
- policy digest mismatch;
- little-endian re-encoding;
- old v4 consumer token;
- replay ID zero;
- provenance ID zero;
- missing outcome evidence;
- authority mismatch;
- epoch mismatch;
- non-zero reserved flags;
- trailing byte;
- truncated token.

Every language must independently match the same oracle. Cross-language disagreement is a first-class failure even if a fail-closed pipeline would happen to reject the request.

## Policy evolution surface

The frozen v1->v5 evolution has four transitions. The ownership model counts:

- per-language validators: three managed policy sources, therefore 12 source updates;
- conventional canonical contract: four descriptor updates and zero validator-source updates inside the frozen primitive set;
- ProofBit contract: four descriptor updates and zero verifier-source updates inside the same frozen primitive set.

All three still require language-level conformance testing: 3 languages x 4 transitions = 12 conformance invocations. These counts model update surface, not engineering hours.

## Runtime

The dedicated workflow compiles a real Rust validator and executes real Python, Rust, and Node processes over the same vectors. Eleven rounds rotate system order. Runtime is secondary to correctness and semantic agreement.

## Claim boundary

This is Linux software-reference evidence on one CI runner. It does not model separate organizations, network transports, generated SDK release processes, cryptographic authenticity, hostile code, silicon, energy, novelty, patentability, or universal superiority. Benefits reproduced by `software_canonical_contract` belong to canonical-contract architecture rather than uniquely to ProofBit.
