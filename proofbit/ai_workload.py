from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Iterable, Sequence

from .model import BaselineProcessor, Evidence, ProofProcessor


FAILURE_KINDS = ("UNKNOWN", "STALE", "REPLAY", "CONFLICT", "FALSE_SUCCESS")
FEATURE_WIDTH = 32
WEIGHTS = tuple(((j * 7) % 11) - 5 for j in range(FEATURE_WIDTH))
BIAS = 2048


@dataclass(frozen=True)
class DecisionInput:
    decision_id: int
    features: tuple[int, ...]
    kind: str


@dataclass(frozen=True)
class BackendInfo:
    id: str
    vendor: str
    product: str
    target_system: str
    status: str
    executable: bool


class PurePythonBackend:
    """Dependency-free fixed-point reference kernel.

    The arithmetic intentionally uses small integers that are exactly representable
    in common floating-point formats. Hardware adapters may implement the same dot
    product in their native framework while preserving the frozen PB-AI-01 inputs.
    """

    info = BackendInfo(
        "cpu-python",
        "Python",
        "pure-Python fixed-point reference kernel",
        "host-cpu",
        "executable",
        True,
    )

    def infer(self, batch: Sequence[DecisionInput]) -> list[int]:
        scores: list[int] = []
        for item in batch:
            total = BIAS
            for value, weight in zip(item.features, WEIGHTS):
                total += value * weight
            scores.append(total)
        return scores


BACKENDS = {
    "cpu-python": PurePythonBackend.info,
    "nvidia-cuda": BackendInfo(
        "nvidia-cuda",
        "NVIDIA",
        "CUDA adapter",
        "nvidia-gb200-nvl72",
        "not-run",
        False,
    ),
    "google-tpu-jax": BackendInfo(
        "google-tpu-jax",
        "Google",
        "JAX/TPU adapter",
        "google-tpu7x-ironwood",
        "not-run",
        False,
    ),
    "cerebras": BackendInfo(
        "cerebras",
        "Cerebras",
        "Cerebras SDK adapter",
        "cerebras-wse3",
        "not-run",
        False,
    ),
    "aws-neuron": BackendInfo(
        "aws-neuron",
        "AWS",
        "Neuron/Trainium adapter",
        "aws-trainium3",
        "not-run",
        False,
    ),
    "amd-rocm": BackendInfo(
        "amd-rocm",
        "AMD",
        "ROCm adapter",
        "amd-mi450-series",
        "not-run",
        False,
    ),
    "openai-jalapeno": BackendInfo(
        "openai-jalapeno",
        "OpenAI + Broadcom",
        "Jalapeno adapter",
        "openai-jalapeno",
        "not-run-no-public-adapter",
        False,
    ),
}


def _features(index: int) -> tuple[int, ...]:
    return tuple(
        ((index * (column + 3) + column * 5 + 11) % 17) - 8
        for column in range(FEATURE_WIDTH)
    )


def build_workload(decisions: int, contamination_rate: float) -> list[DecisionInput]:
    """Build an exact-count deterministic contaminated decision stream."""

    if decisions <= 0:
        raise ValueError("decisions must be positive")
    if not 0 <= contamination_rate <= 1:
        raise ValueError("contamination_rate must be between 0 and 1")

    bad_count = round(decisions * contamination_rate)
    bad_seen = 0
    rows: list[DecisionInput] = []

    for index in range(decisions):
        # This integer accumulator spreads exactly bad_count adversarial records
        # across the stream without randomness or a platform-specific RNG.
        contaminated = (
            ((index + 1) * bad_count) // decisions
            > (index * bad_count) // decisions
        )
        if contaminated:
            kind = FAILURE_KINDS[bad_seen % len(FAILURE_KINDS)]
            bad_seen += 1
        else:
            kind = "NORMAL"
        rows.append(DecisionInput(index, _features(index), kind))

    return rows


def _assert_positive_scores(scores: Iterable[int]) -> None:
    if any(score <= 0 for score in scores):
        raise RuntimeError(
            "PB-AI-01 generator invariant broken: every score must propose action"
        )


def _metrics(
    decisions: int,
    safe: int,
    unsafe: int,
    blocked_valid: int,
    proven_safe: int,
    elapsed_ns: int,
) -> dict:
    seconds = elapsed_ns / 1_000_000_000
    return {
        "safe_actions": safe,
        "proven_safe_actions": proven_safe,
        "unsafe_actions": unsafe,
        "blocked_valid_actions": blocked_valid,
        "guard_elapsed_ns": elapsed_ns,
        "guard_decisions_per_sec": decisions / seconds if seconds else 0.0,
        "useful_actions_per_sec": safe / seconds if seconds else 0.0,
        "proven_useful_actions_per_sec": proven_safe / seconds if seconds else 0.0,
        "proof_coverage": proven_safe / safe if safe else 0.0,
        "unsafe_actions_per_million": unsafe / decisions * 1_000_000,
    }


def run_baseline(
    workload: Sequence[DecisionInput], scores: Sequence[int]
) -> dict:
    """Run the same action scores through a value-only execution boundary."""

    _assert_positive_scores(scores)
    cpu = BaselineProcessor()
    safe = 0
    unsafe = 0
    blocked_valid = 0

    start = time.perf_counter_ns()
    for row, score in zip(workload, scores):
        cpu.store(0, score > 0)
        allowed = cpu.guarded_execute(0)
        if allowed:
            if row.kind == "NORMAL":
                safe += 1
            else:
                unsafe += 1
        elif row.kind == "NORMAL":
            blocked_valid += 1
    elapsed_ns = time.perf_counter_ns() - start

    # Correct actions are known to the benchmark oracle, but the baseline itself
    # carries no ProofBit evidence, so proven_safe is intentionally zero.
    return _metrics(
        len(workload), safe, unsafe, blocked_valid, 0, elapsed_ns
    )


def _install_proof_state(cpu: ProofProcessor, row: DecisionInput) -> None:
    proof_id = row.decision_id + 1

    if row.kind == "NORMAL":
        cpu.store_evidence(
            0,
            Evidence(
                "agent_action_allowed",
                True,
                proof_id,
                1,
                1,
                row.decision_id,
            ),
        )
    elif row.kind == "UNKNOWN":
        cpu.store_unknown(0, "agent_action_allowed", True)
    elif row.kind == "STALE":
        cpu.store_evidence(
            0,
            Evidence(
                "agent_action_allowed",
                True,
                proof_id,
                1,
                0,
                row.decision_id,
            ),
        )
    elif row.kind == "REPLAY":
        cpu.consumed_proofs.add(proof_id)
        cpu.store_evidence(
            0,
            Evidence(
                "agent_action_allowed",
                True,
                proof_id,
                1,
                1,
                row.decision_id,
            ),
        )
    elif row.kind == "CONFLICT":
        cpu.store_conflict(0, "agent_action_allowed")
    elif row.kind == "FALSE_SUCCESS":
        cpu.record_claimed_success_without_outcome_evidence(
            0, "agent_action_allowed"
        )
    else:
        raise ValueError(f"unknown PB-AI-01 state: {row.kind}")


def run_proof(workload: Sequence[DecisionInput], scores: Sequence[int]) -> dict:
    """Run the same action scores through the ProofBit execution boundary."""

    _assert_positive_scores(scores)
    cpu = ProofProcessor()
    safe = 0
    unsafe = 0
    blocked_valid = 0

    start = time.perf_counter_ns()
    for row, score in zip(workload, scores):
        if score <= 0:
            continue
        _install_proof_state(cpu, row)
        allowed = cpu.guarded_execute(0)
        if allowed:
            if row.kind == "NORMAL":
                safe += 1
            else:
                unsafe += 1
        elif row.kind == "NORMAL":
            blocked_valid += 1
    elapsed_ns = time.perf_counter_ns() - start

    return _metrics(
        len(workload), safe, unsafe, blocked_valid, safe, elapsed_ns
    )


def _add_end_to_end_metrics(
    result: dict,
    decisions: int,
    normal_decisions: int,
    inference_elapsed_ns: int,
) -> None:
    result["false_positive_block_rate"] = (
        result["blocked_valid_actions"] / normal_decisions
        if normal_decisions
        else 0.0
    )
    result["end_to_end_ns"] = inference_elapsed_ns + result["guard_elapsed_ns"]
    seconds = result["end_to_end_ns"] / 1_000_000_000
    result["end_to_end_decisions_per_sec"] = (
        decisions / seconds if seconds else 0.0
    )
    result["end_to_end_useful_actions_per_sec"] = (
        result["safe_actions"] / seconds if seconds else 0.0
    )
    result["trusted_useful_throughput"] = (
        result["proven_safe_actions"] / seconds if seconds else 0.0
    )


def run_pb_ai_01(
    decisions: int = 10_000,
    contamination_rate: float = 0.10,
    backend_id: str = "cpu-python",
) -> dict:
    """Execute PB-AI-01 or return an explicit not-run record for target hardware."""

    info = BACKENDS.get(backend_id)
    if info is None:
        raise ValueError(f"unknown backend: {backend_id}")

    if not info.executable:
        return {
            "benchmark_id": "PB-AI-01",
            "version": "0.1",
            "backend": asdict(info),
            "status": "not-run",
            "reason": (
                "adapter and/or target hardware is not available in this "
                "execution environment"
            ),
        }

    workload = build_workload(decisions, contamination_rate)
    backend = PurePythonBackend()

    inference_start = time.perf_counter_ns()
    scores = backend.infer(workload)
    inference_elapsed_ns = time.perf_counter_ns() - inference_start
    _assert_positive_scores(scores)

    baseline = run_baseline(workload, scores)
    proof = run_proof(workload, scores)
    normal_decisions = sum(row.kind == "NORMAL" for row in workload)
    adversarial_decisions = decisions - normal_decisions

    _add_end_to_end_metrics(
        baseline, decisions, normal_decisions, inference_elapsed_ns
    )
    _add_end_to_end_metrics(
        proof, decisions, normal_decisions, inference_elapsed_ns
    )

    baseline["prevented_unsafe_actions"] = adversarial_decisions - baseline[
        "unsafe_actions"
    ]
    proof["prevented_unsafe_actions"] = adversarial_decisions - proof[
        "unsafe_actions"
    ]

    return {
        "benchmark_id": "PB-AI-01",
        "version": "0.1",
        "status": "executed",
        "scope": (
            "deterministic inference-like kernel plus identical value-only and "
            "proof-aware action boundaries; not an LLM quality benchmark"
        ),
        "backend": asdict(info),
        "decisions": decisions,
        "feature_width": FEATURE_WIDTH,
        "contamination_rate": contamination_rate,
        "failure_kinds": list(FAILURE_KINDS),
        "normal_decisions": normal_decisions,
        "adversarial_decisions": adversarial_decisions,
        "inference_elapsed_ns": inference_elapsed_ns,
        "baseline": baseline,
        "proof": proof,
        "proof_guard_overhead_ratio": (
            proof["guard_elapsed_ns"] / baseline["guard_elapsed_ns"]
        ),
        "end_to_end_overhead_ratio": (
            proof["end_to_end_ns"] / baseline["end_to_end_ns"]
        ),
    }
