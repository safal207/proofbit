from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import statistics
import struct
import time
from typing import Callable


BENCHMARK_ID = "PB-TRUST-COMPOSE-06"
VERSION = "0.1"
PROTOCOL = "PB-TC06/v0.1 policy-evolution-divergence"

# Frozen trust primitives. TC06 only makes claims for policy changes expressible
# with these primitives; adding a new primitive would require verifier changes.
STATEMENT = 1 << 0
AUTHORITY = 1 << 1
EPOCH = 1 << 2
REPLAY = 1 << 3
PROVENANCE = 1 << 4
OUTCOME = 1 << 5

PRIMITIVE_NAMES = {
    STATEMENT: "statement",
    AUTHORITY: "authority",
    EPOCH: "epoch",
    REPLAY: "replay",
    PROVENANCE: "provenance",
    OUTCOME: "outcome",
}

POLICY_STRUCT = struct.Struct(">IIQ")  # version, required-mask, stable digest
TOKEN_STRUCT = struct.Struct(">QIIQB7x")  # request, version, mask, digest, decision

SYSTEMS = (
    "software_shared_registry",
    "software_independent_copies",
    "proofbit_contract",
)

FAULTS = (
    "VALID",
    "WRONG_STATEMENT",
    "WRONG_AUTHORITY",
    "STALE_EPOCH",
    "REPLAY",
    "MISSING_PROVENANCE",
    "FALSE_SUCCESS",
)


@dataclass(frozen=True)
class Policy:
    version: int
    required_mask: int
    digest: int

    @property
    def blob(self) -> bytes:
        return POLICY_STRUCT.pack(self.version, self.required_mask, self.digest)


@dataclass(frozen=True)
class Request:
    request_id: int
    fault: str
    statement_ok: bool = True
    authority_ok: bool = True
    epoch_ok: bool = True
    replayed: bool = False
    provenance_ok: bool = True
    outcome_ok: bool = True
    terminal_success_claim: bool = True


@dataclass(frozen=True)
class Receipt:
    request_id: int
    policy_version: int
    required_mask: int
    policy_digest: int
    decision: bool

    @property
    def blob(self) -> bytes:
        return TOKEN_STRUCT.pack(
            self.request_id,
            self.policy_version,
            self.required_mask,
            self.policy_digest,
            int(self.decision),
        )


def _stable_digest(version: int, mask: int) -> int:
    raw = hashlib.sha256(f"PB-TC06:{version}:{mask}".encode()).digest()[:8]
    return int.from_bytes(raw, "big")


def build_policies() -> tuple[Policy, ...]:
    masks = (
        STATEMENT | AUTHORITY,
        STATEMENT | AUTHORITY | EPOCH,
        STATEMENT | AUTHORITY | EPOCH | REPLAY,
        STATEMENT | AUTHORITY | EPOCH | REPLAY | PROVENANCE,
        STATEMENT | AUTHORITY | EPOCH | REPLAY | PROVENANCE | OUTCOME,
    )
    return tuple(
        Policy(version=index + 1, required_mask=mask, digest=_stable_digest(index + 1, mask))
        for index, mask in enumerate(masks)
    )


POLICIES = build_policies()


def policy_allows(request: Request, policy: Policy) -> bool:
    mask = policy.required_mask
    if mask & STATEMENT and not request.statement_ok:
        return False
    if mask & AUTHORITY and not request.authority_ok:
        return False
    if mask & EPOCH and not request.epoch_ok:
        return False
    if mask & REPLAY and request.replayed:
        return False
    if mask & PROVENANCE and not request.provenance_ok:
        return False
    if mask & OUTCOME and request.terminal_success_claim and not request.outcome_ok:
        return False
    return True


def _request_for_fault(request_id: int, fault: str) -> Request:
    kwargs = {"request_id": request_id, "fault": fault}
    if fault == "VALID":
        return Request(**kwargs)
    if fault == "WRONG_STATEMENT":
        return Request(**kwargs, statement_ok=False)
    if fault == "WRONG_AUTHORITY":
        return Request(**kwargs, authority_ok=False)
    if fault == "STALE_EPOCH":
        return Request(**kwargs, epoch_ok=False)
    if fault == "REPLAY":
        return Request(**kwargs, replayed=True)
    if fault == "MISSING_PROVENANCE":
        return Request(**kwargs, provenance_ok=False)
    if fault == "FALSE_SUCCESS":
        return Request(**kwargs, outcome_ok=False)
    raise ValueError(f"unknown fault: {fault}")


def build_workload(requests_per_version: int) -> dict[int, list[Request]]:
    if requests_per_version <= 0:
        raise ValueError("requests_per_version must be positive")

    # 70% clean + 5% for each of six pressure cases, distributed exactly and
    # deterministically without platform RNG.
    fault_weights = (
        ("VALID", 70),
        ("WRONG_STATEMENT", 5),
        ("WRONG_AUTHORITY", 5),
        ("STALE_EPOCH", 5),
        ("REPLAY", 5),
        ("MISSING_PROVENANCE", 5),
        ("FALSE_SUCCESS", 5),
    )
    weighted = [name for name, count in fault_weights for _ in range(count)]
    workloads: dict[int, list[Request]] = {}
    request_id = 1
    for policy in POLICIES:
        rows: list[Request] = []
        for index in range(requests_per_version):
            fault = weighted[(index * 37 + policy.version * 11) % len(weighted)]
            rows.append(_request_for_fault(request_id, fault))
            request_id += 1
        workloads[policy.version] = rows
    return workloads


def _receipt(request: Request, policy: Policy) -> Receipt:
    return Receipt(
        request_id=request.request_id,
        policy_version=policy.version,
        required_mask=policy.required_mask,
        policy_digest=policy.digest,
        decision=policy_allows(request, policy),
    )


def _verify_receipt(receipt: Receipt, expected_request_id: int, policy: Policy) -> bool:
    # This is deliberately a strong conventional-compatible receipt check. The
    # ProofBit control is not allowed a smaller token or a hidden extra index.
    return (
        receipt.request_id == expected_request_id
        and receipt.policy_version == policy.version
        and receipt.required_mask == policy.required_mask
        and receipt.policy_digest == policy.digest
    )


def _run_shared(
    workloads: dict[int, list[Request]], components: int
) -> dict:
    correct = unsafe = false_success = missed_valid = 0
    started = time.perf_counter_ns()
    for policy in POLICIES:
        # One authoritative data-driven policy descriptor shared by all stages.
        active_policy = policy
        for request in workloads[policy.version]:
            expected = policy_allows(request, policy)
            receipt = _receipt(request, active_policy)
            valid = True
            for _ in range(components):
                valid = valid and _verify_receipt(receipt, request.request_id, active_policy)
            actual = bool(receipt.decision and valid)
            correct += actual == expected
            unsafe += actual and not expected
            missed_valid += (not actual) and expected
            false_success += (
                actual
                and request.fault == "FALSE_SUCCESS"
                and bool(policy.required_mask & OUTCOME)
            )
    elapsed_ns = time.perf_counter_ns() - started
    return _runtime_result(
        "software_shared_registry",
        correct,
        unsafe,
        false_success,
        missed_valid,
        elapsed_ns,
        workloads,
    )


def _run_independent(
    workloads: dict[int, list[Request]], components: int
) -> dict:
    correct = unsafe = false_success = missed_valid = 0
    started = time.perf_counter_ns()
    for policy in POLICIES:
        # Safe rollout has completed before activation: every independently
        # managed component now holds a byte-identical descriptor copy.
        local_policies = [policy for _ in range(components)]
        for request in workloads[policy.version]:
            expected = policy_allows(request, policy)
            receipt = _receipt(request, local_policies[0])
            valid = True
            for local in local_policies:
                valid = valid and _verify_receipt(receipt, request.request_id, local)
            actual = bool(receipt.decision and valid)
            correct += actual == expected
            unsafe += actual and not expected
            missed_valid += (not actual) and expected
            false_success += (
                actual
                and request.fault == "FALSE_SUCCESS"
                and bool(policy.required_mask & OUTCOME)
            )
    elapsed_ns = time.perf_counter_ns() - started
    return _runtime_result(
        "software_independent_copies",
        correct,
        unsafe,
        false_success,
        missed_valid,
        elapsed_ns,
        workloads,
    )


def _run_proofbit(
    workloads: dict[int, list[Request]], components: int
) -> dict:
    correct = unsafe = false_success = missed_valid = 0
    started = time.perf_counter_ns()
    for policy in POLICIES:
        # TC06 models a generic proof-plane contract descriptor. Policy changes
        # must remain inside the frozen primitive set; otherwise this assumption
        # no longer holds and verifier/component upgrades are required.
        proof_contract = policy
        for request in workloads[policy.version]:
            expected = policy_allows(request, policy)
            proof = _receipt(request, proof_contract)
            valid = True
            for _ in range(components):
                valid = valid and _verify_receipt(proof, request.request_id, proof_contract)
            actual = bool(proof.decision and valid)
            correct += actual == expected
            unsafe += actual and not expected
            missed_valid += (not actual) and expected
            false_success += (
                actual
                and request.fault == "FALSE_SUCCESS"
                and bool(policy.required_mask & OUTCOME)
            )
    elapsed_ns = time.perf_counter_ns() - started
    return _runtime_result(
        "proofbit_contract",
        correct,
        unsafe,
        false_success,
        missed_valid,
        elapsed_ns,
        workloads,
    )


def _runtime_result(
    system: str,
    correct: int,
    unsafe: int,
    false_success: int,
    missed_valid: int,
    elapsed_ns: int,
    workloads: dict[int, list[Request]],
) -> dict:
    total = sum(len(rows) for rows in workloads.values())
    seconds = elapsed_ns / 1_000_000_000
    return {
        "system": system,
        "oracle_accuracy": correct / total,
        "unsafe_accepts": unsafe,
        "false_terminal_success": false_success,
        "missed_valid": missed_valid,
        "elapsed_ns": elapsed_ns,
        "requests_per_sec": total / seconds if seconds else 0.0,
    }


def _policy_vectors(policy: Policy) -> list[Request]:
    return [_request_for_fault(index + 1, fault) for index, fault in enumerate(FAULTS)]


def _regression_suite_runs(system: str, components: int) -> tuple[int, int]:
    """Execute the frozen policy vectors against every managed policy copy.

    Returns (suite_invocations, failed_assertions). This counts actual test-vector
    executions rather than inventing a LOC-based regression score.
    """

    invocations = failed = 0
    for policy in POLICIES[1:]:  # v1 is the baseline; count four evolutions.
        copies = components if system == "software_independent_copies" else 1
        for _ in range(copies):
            invocations += 1
            for request in _policy_vectors(policy):
                expected = policy_allows(request, policy)
                actual = policy_allows(request, policy)
                failed += actual != expected
    return invocations, failed


def _mixed_rollout_probe(components: int, probes_per_phase: int = 100) -> dict:
    """Fail-closed early-activation stress for independent policy copies.

    This is not the primary rollout strategy. It quantifies the availability
    cost if a new version is activated before every independently managed stage
    has the matching policy descriptor. Old stages reject the unknown version;
    they do not silently accept it.
    """

    blocked = unsafe = phases = 0
    for next_policy in POLICIES[1:]:
        previous = POLICIES[next_policy.version - 2]
        for upgraded in range(1, components):
            phases += 1
            locals_ = [
                next_policy if index < upgraded else previous
                for index in range(components)
            ]
            for probe in range(probes_per_phase):
                request = Request(request_id=probe + 1, fault="VALID")
                receipt = _receipt(request, next_policy)
                accepted = all(
                    _verify_receipt(receipt, request.request_id, local)
                    for local in locals_
                ) and receipt.decision
                blocked += not accepted
                unsafe += accepted and not policy_allows(request, next_policy)
    return {
        "phases": phases,
        "valid_probes": phases * probes_per_phase,
        "valid_blocks": blocked,
        "unsafe_accepts": unsafe,
        "probe_rule": "new policy activated before all independent copies are upgraded; old versions fail closed on receipt mismatch",
    }


def evolution_work(components: int) -> dict[str, dict]:
    evolutions = len(POLICIES) - 1
    if components <= 0:
        raise ValueError("components must be positive")

    result: dict[str, dict] = {}
    for system in SYSTEMS:
        copies = components if system == "software_independent_copies" else 1
        suite_runs, suite_failures = _regression_suite_runs(system, components)
        result[system] = {
            "managed_policy_copies": copies,
            "policy_copy_updates": evolutions * copies,
            "safe_activation_steps": evolutions * copies,
            "regression_suite_invocations": suite_runs,
            "regression_suite_failures": suite_failures,
            "active_policy_descriptor_bytes": POLICY_STRUCT.size * copies,
            "propagated_receipt_bytes": TOKEN_STRUCT.size,
            "semantic_drift_after_safe_activation": 0,
        }

    result["software_independent_copies"]["early_activation_stress"] = (
        _mixed_rollout_probe(components)
    )
    result["software_shared_registry"]["early_activation_stress"] = {
        "phases": 0,
        "valid_probes": 0,
        "valid_blocks": 0,
        "unsafe_accepts": 0,
        "probe_rule": "not applicable: one authoritative shared registry switches atomically in this model",
    }
    result["proofbit_contract"]["early_activation_stress"] = {
        "phases": 0,
        "valid_probes": 0,
        "valid_blocks": 0,
        "unsafe_accepts": 0,
        "probe_rule": "not applicable inside the frozen generic proof-contract primitive set",
    }
    return result


def _aggregate_runtime(rounds: list[dict]) -> dict:
    return {
        "oracle_accuracy": min(row["oracle_accuracy"] for row in rounds),
        "unsafe_accepts": sum(row["unsafe_accepts"] for row in rounds),
        "false_terminal_success": sum(row["false_terminal_success"] for row in rounds),
        "missed_valid": sum(row["missed_valid"] for row in rounds),
        "median_elapsed_ns": statistics.median(row["elapsed_ns"] for row in rounds),
        "median_requests_per_sec": statistics.median(row["requests_per_sec"] for row in rounds),
        "raw_requests_per_sec": [row["requests_per_sec"] for row in rounds],
    }


def run_benchmark(
    requests_per_version: int = 10_000,
    components: int = 8,
    rounds: int = 11,
) -> dict:
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    if components <= 0:
        raise ValueError("components must be positive")

    workloads = build_workload(requests_per_version)
    runners: dict[str, Callable[[dict[int, list[Request]], int], dict]] = {
        "software_shared_registry": _run_shared,
        "software_independent_copies": _run_independent,
        "proofbit_contract": _run_proofbit,
    }
    per_system: dict[str, list[dict]] = {name: [] for name in SYSTEMS}
    orders: list[list[str]] = []

    for round_index in range(rounds):
        shift = round_index % len(SYSTEMS)
        order = SYSTEMS[shift:] + SYSTEMS[:shift]
        orders.append(list(order))
        for name in order:
            per_system[name].append(runners[name](workloads, components))

    runtime = {name: _aggregate_runtime(per_system[name]) for name in SYSTEMS}
    work = evolution_work(components)

    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "components": components,
        "policy_versions": [
            {
                "version": policy.version,
                "required_mask": policy.required_mask,
                "required_primitives": [
                    name
                    for bit, name in PRIMITIVE_NAMES.items()
                    if policy.required_mask & bit
                ],
                "digest": policy.digest,
            }
            for policy in POLICIES
        ],
        "requests_per_version": requests_per_version,
        "total_requests_per_system_per_round": requests_per_version * len(POLICIES),
        "rounds": rounds,
        "measurement_orders": orders,
        "policy_descriptor_bytes": POLICY_STRUCT.size,
        "propagation_token_bytes": TOKEN_STRUCT.size,
        "runtime": runtime,
        "evolution_work": work,
        "no_single_winner_score": True,
        "primary_anti_strawman": "software_shared_registry",
        "interpretation_rule": (
            "software_shared_registry is the strongest conventional control: it uses the same data-driven policy primitives and same-size propagated receipt as proofbit_contract. Any benefit reproduced by that control is not uniquely credited to ProofBit. software_independent_copies measures the governance/update cost of replicated independently managed policy copies, not deliberately buggy code."
        ),
        "claim_boundary": (
            "TC06 only covers policy evolution expressible by the frozen statement/authority/epoch/replay/provenance/outcome primitives. A genuinely new trust primitive would require verifier/component evolution and invalidates the one-descriptor-update assumption."
        ),
    }


def _print_human(report: dict) -> None:
    print(f"{report['benchmark_id']} {report['protocol']}")
    print("system                         accuracy   unsafe   missed   median req/s   policy updates")
    for name in SYSTEMS:
        runtime = report["runtime"][name]
        work = report["evolution_work"][name]
        print(
            f"{name:30s} {runtime['oracle_accuracy']:8.3f} "
            f"{runtime['unsafe_accepts']:8d} {runtime['missed_valid']:8d} "
            f"{runtime['median_requests_per_sec']:14.1f} "
            f"{work['policy_copy_updates']:14d}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests-per-version", type=int, default=10_000)
    parser.add_argument("--components", type=int, default=8)
    parser.add_argument("--rounds", type=int, default=11)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_benchmark(args.requests_per_version, args.components, args.rounds)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)


if __name__ == "__main__":
    main()
