#!/usr/bin/env python3
"""PB-TRUST-COMPOSE-02 real IPC transport benchmark.

This benchmark replaces PB-TC01's modeled component hops with actual process
boundaries using multiprocessing Pipe send_bytes/recv_bytes. It compares three
competent implementations of the same frozen trust oracle:

1. JSON software trust envelope;
2. compact binary software trust envelope;
3. compact binary ProofBit envelope validated through ProofProcessor.

Every implementation performs real encode -> process transport -> decode work.
The benchmark measures correctness, wire bytes, wall-clock throughput, and the
number of transport/validation operations. It is a software/IPC reference
benchmark, not a silicon, network, energy, or cryptographic benchmark.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import multiprocessing as mp
from pathlib import Path
import struct
import sys
import time
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.model import EpistemicState, Evidence, ProofProcessor

BENCHMARK_ID = "PB-TRUST-COMPOSE-02"
VERSION = "0.1"
PROTOCOL = "PB-TC02/v0.1 real-ipc-trust-transport"
FAULT_KINDS = (
    "UNKNOWN",
    "STALE_AUTHORITY",
    "REPLAY",
    "CONFLICT",
    "REBIND_STATEMENT",
    "FALSE_SUCCESS",
)
AUTHORIZATION_FAULTS = {
    "UNKNOWN",
    "STALE_AUTHORITY",
    "REPLAY",
    "CONFLICT",
    "REBIND_STATEMENT",
}
DEFAULT_BOUNDARIES = (1, 2, 4, 8)

COMPACT = struct.Struct("!BBIIQIIQQ")
FLAG_EVIDENCE_PRESENT = 1 << 0
FLAG_VALUE = 1 << 1
FLAG_CONFLICT = 1 << 2
FLAG_OUTCOME = 1 << 3
FLAG_REPLAY_SEED = 1 << 4

KIND_TO_ID = {"VALID": 0, **{kind: index + 1 for index, kind in enumerate(FAULT_KINDS)}}
ID_TO_KIND = {value: key for key, value in KIND_TO_ID.items()}
RESULT = struct.Struct("!??")
STOP = b""


@dataclass(frozen=True)
class Trial:
    index: int
    kind: str
    action_id: int
    statement_id: int


@dataclass(frozen=True)
class Envelope:
    kind: str
    action_id: int
    statement_id: int
    evidence_present: bool
    value: bool
    proof_id: int
    authority: int
    epoch: int
    provenance: int
    conflict: bool
    outcome_evidence: bool
    outcome_proof_id: int
    replay_seed: bool


class SoftwareTrustGuard:
    def __init__(self, authority: int = 1, epoch: int = 1) -> None:
        self.authority = authority
        self.epoch = epoch
        self.consumed: set[int] = set()

    def authorize(self, message: Envelope) -> bool:
        if not message.evidence_present or message.conflict:
            return False
        if message.statement_id != message.action_id:
            return False
        if message.authority != self.authority or message.epoch != self.epoch:
            return False
        if message.proof_id in self.consumed:
            return False
        self.consumed.add(message.proof_id)
        return message.value

    @staticmethod
    def terminal_success(message: Envelope, dispatched: bool) -> bool:
        return dispatched and message.outcome_evidence


def _validate_inputs(
    trials: int, contamination_rate: float, boundaries: Iterable[int]
) -> tuple[int, tuple[int, ...]]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= contamination_rate <= 1:
        raise ValueError("contamination_rate must be between 0 and 1")
    normalized = tuple(int(item) for item in boundaries)
    if not normalized or any(item <= 0 for item in normalized):
        raise ValueError("boundaries must contain positive integers")
    return round(trials * contamination_rate), normalized


def build_trials(trials: int, contamination_rate: float) -> list[Trial]:
    bad_count, _ = _validate_inputs(trials, contamination_rate, (1,))
    bad_seen = 0
    rows: list[Trial] = []
    for index in range(trials):
        contaminated = ((index + 1) * bad_count) // trials > (
            index * bad_count
        ) // trials
        if contaminated:
            kind = FAULT_KINDS[bad_seen % len(FAULT_KINDS)]
            bad_seen += 1
        else:
            kind = "VALID"
        action_id = index + 1
        statement_id = action_id + 10_000_000 if kind == "REBIND_STATEMENT" else action_id
        rows.append(Trial(index, kind, action_id, statement_id))
    return rows


def expected(kind: str) -> tuple[bool, bool]:
    if kind == "VALID":
        return True, True
    if kind == "FALSE_SUCCESS":
        return True, False
    if kind in AUTHORIZATION_FAULTS:
        return False, False
    raise ValueError(kind)


def envelope(row: Trial) -> Envelope:
    proof_id = row.index + 1
    return Envelope(
        kind=row.kind,
        action_id=row.action_id,
        statement_id=row.statement_id,
        evidence_present=row.kind != "UNKNOWN",
        value=True,
        proof_id=proof_id,
        authority=1,
        epoch=0 if row.kind == "STALE_AUTHORITY" else 1,
        provenance=row.index,
        conflict=row.kind == "CONFLICT",
        outcome_evidence=row.kind == "VALID",
        outcome_proof_id=1_000_000 + row.index,
        replay_seed=row.kind == "REPLAY",
    )


def encode_json(message: Envelope) -> bytes:
    return json.dumps(asdict(message), sort_keys=True, separators=(",", ":")).encode()


def decode_json(payload: bytes) -> Envelope:
    return Envelope(**json.loads(payload.decode()))


def _flags(message: Envelope) -> int:
    flags = 0
    if message.evidence_present:
        flags |= FLAG_EVIDENCE_PRESENT
    if message.value:
        flags |= FLAG_VALUE
    if message.conflict:
        flags |= FLAG_CONFLICT
    if message.outcome_evidence:
        flags |= FLAG_OUTCOME
    if message.replay_seed:
        flags |= FLAG_REPLAY_SEED
    return flags


def encode_compact(message: Envelope) -> bytes:
    return COMPACT.pack(
        KIND_TO_ID[message.kind],
        _flags(message),
        message.action_id,
        message.statement_id,
        message.proof_id,
        message.authority,
        message.epoch,
        message.provenance,
        message.outcome_proof_id,
    )


def decode_compact(payload: bytes) -> Envelope:
    (
        kind_id,
        flags,
        action_id,
        statement_id,
        proof_id,
        authority,
        epoch,
        provenance,
        outcome_proof_id,
    ) = COMPACT.unpack(payload)
    return Envelope(
        kind=ID_TO_KIND[kind_id],
        action_id=action_id,
        statement_id=statement_id,
        evidence_present=bool(flags & FLAG_EVIDENCE_PRESENT),
        value=bool(flags & FLAG_VALUE),
        proof_id=proof_id,
        authority=authority,
        epoch=epoch,
        provenance=provenance,
        conflict=bool(flags & FLAG_CONFLICT),
        outcome_evidence=bool(flags & FLAG_OUTCOME),
        outcome_proof_id=outcome_proof_id,
        replay_seed=bool(flags & FLAG_REPLAY_SEED),
    )


def _proofbit_decide(cpu: ProofProcessor, message: Envelope) -> tuple[bool, bool]:
    statement = f"action:{message.statement_id}"
    expected_statement = f"action:{message.action_id}"
    if not message.evidence_present:
        cpu.store_unknown(0, statement, message.value)
    elif message.conflict:
        cpu.store_conflict(0, statement)
    else:
        if message.replay_seed:
            cpu.consumed_proofs.add(message.proof_id)
        cpu.store_evidence(
            0,
            Evidence(
                statement,
                message.value,
                message.proof_id,
                message.authority,
                message.epoch,
                message.provenance,
            ),
        )
    dispatched = cpu.guarded_execute(0, expected_statement=expected_statement)
    if message.outcome_evidence and dispatched:
        outcome = Evidence(
            f"outcome:{message.action_id}",
            True,
            message.outcome_proof_id,
            1,
            1,
            message.provenance,
        )
        terminal = cpu.verify(outcome, consume=False) is EpistemicState.PROVEN_TRUE
    elif dispatched:
        cpu.record_claimed_success_without_outcome_evidence(
            1, f"outcome:{message.action_id}"
        )
        terminal = cpu.load(1).state is EpistemicState.PROVEN_TRUE
    else:
        terminal = False
    return dispatched, terminal


def _worker(
    recv_conn: Any,
    send_conn: Any,
    codec: str,
    final: bool,
    proofbit: bool,
) -> None:
    decoder: Callable[[bytes], Envelope] = decode_json if codec == "json" else decode_compact
    encoder: Callable[[Envelope], bytes] = encode_json if codec == "json" else encode_compact
    software_guard = SoftwareTrustGuard() if final and not proofbit else None
    proof_cpu = ProofProcessor() if final and proofbit else None
    try:
        while True:
            payload = recv_conn.recv_bytes()
            if payload == STOP:
                if not final:
                    send_conn.send_bytes(STOP)
                break
            message = decoder(payload)
            if final:
                if proofbit:
                    assert proof_cpu is not None
                    dispatched, terminal = _proofbit_decide(proof_cpu, message)
                else:
                    assert software_guard is not None
                    if message.replay_seed:
                        software_guard.consumed.add(message.proof_id)
                    dispatched = software_guard.authorize(message)
                    terminal = software_guard.terminal_success(message, dispatched)
                send_conn.send_bytes(RESULT.pack(dispatched, terminal))
            else:
                send_conn.send_bytes(encoder(message))
    finally:
        recv_conn.close()
        send_conn.close()


def _new_kind_metrics() -> dict[str, int]:
    return {
        "trials": 0,
        "oracle_correct": 0,
        "unsafe_dispatches": 0,
        "false_success_claims": 0,
        "missed_valid_dispatches": 0,
    }


def _score(
    per_kind: dict[str, dict[str, int]], kind: str, dispatched: bool, terminal: bool
) -> None:
    expected_dispatch, expected_terminal = expected(kind)
    row = per_kind[kind]
    row["trials"] += 1
    if (dispatched, terminal) == (expected_dispatch, expected_terminal):
        row["oracle_correct"] += 1
    if kind in AUTHORIZATION_FAULTS and dispatched:
        row["unsafe_dispatches"] += 1
    if kind == "FALSE_SUCCESS" and terminal:
        row["false_success_claims"] += 1
    if kind == "VALID" and not dispatched:
        row["missed_valid_dispatches"] += 1


def _run_pipeline(
    rows: list[Trial], *, boundaries: int, codec: str, proofbit: bool
) -> dict[str, Any]:
    ctx = mp.get_context("fork")
    edges = [ctx.Pipe(duplex=False) for _ in range(boundaries + 1)]
    processes: list[mp.Process] = []
    for index in range(boundaries):
        recv_conn = edges[index][0]
        send_conn = edges[index + 1][1]
        process = ctx.Process(
            target=_worker,
            args=(recv_conn, send_conn, codec, index == boundaries - 1, proofbit),
        )
        process.start()
        processes.append(process)

    parent_send = edges[0][1]
    parent_recv = edges[-1][0]
    encoder: Callable[[Envelope], bytes] = encode_json if codec == "json" else encode_compact
    per_kind = {kind: _new_kind_metrics() for kind in ("VALID", *FAULT_KINDS)}
    payload_bytes = 0
    wire_bytes = 0
    transport_messages = 0
    started = time.perf_counter_ns()
    try:
        for row in rows:
            payload = encoder(envelope(row))
            payload_bytes += len(payload)
            wire_bytes += len(payload) * boundaries
            transport_messages += boundaries
            parent_send.send_bytes(payload)
            result = parent_recv.recv_bytes()
            dispatched, terminal = RESULT.unpack(result)
            _score(per_kind, row.kind, dispatched, terminal)
        parent_send.send_bytes(STOP)
    finally:
        parent_send.close()
        parent_recv.close()
        for process in processes:
            process.join(timeout=10)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            if process.exitcode != 0:
                raise RuntimeError(f"transport worker exited with {process.exitcode}")
    elapsed_ns = time.perf_counter_ns() - started

    trials = len(rows)
    correct = sum(item["oracle_correct"] for item in per_kind.values())
    unsafe = sum(item["unsafe_dispatches"] for item in per_kind.values())
    false_success = sum(item["false_success_claims"] for item in per_kind.values())
    missed = sum(item["missed_valid_dispatches"] for item in per_kind.values())
    seconds = elapsed_ns / 1_000_000_000
    return {
        "architecture": "ProofBit" if proofbit else "Conventional CPU / software trust envelope",
        "implementation": (
            "compact binary ProofBit envelope + ProofProcessor"
            if proofbit
            else (
                "JSON trust envelope + SoftwareTrustGuard"
                if codec == "json"
                else "compact binary trust envelope + SoftwareTrustGuard"
            )
        ),
        "codec": codec,
        "boundaries": boundaries,
        "worker_processes": boundaries,
        "trials": trials,
        "oracle_correct_trials": correct,
        "oracle_accuracy": correct / trials,
        "unsafe_authorization_dispatches": unsafe,
        "false_success_claims": false_success,
        "missed_valid_dispatches": missed,
        "per_kind": per_kind,
        "elapsed_ns": elapsed_ns,
        "trials_per_sec": trials / seconds if seconds else 0.0,
        "payload_bytes": payload_bytes,
        "mean_payload_bytes": payload_bytes / trials,
        "wire_bytes": wire_bytes,
        "transport_messages": transport_messages,
        "mean_wire_bytes_per_trial": wire_bytes / trials,
        "validation_boundaries": trials,
        "claim_boundary": (
            "Real local process IPC using multiprocessing Pipe. Transport is same-host "
            "kernel IPC, not network/RPC, silicon, or cryptographic verification."
        ),
    }


def build_report(
    trials: int = 2_000,
    contamination_rate: float = 0.12,
    boundaries: Iterable[int] = DEFAULT_BOUNDARIES,
) -> dict[str, Any]:
    _, normalized = _validate_inputs(trials, contamination_rate, boundaries)
    rows = build_trials(trials, contamination_rate)
    scale: list[dict[str, Any]] = []
    for count in normalized:
        software_json = _run_pipeline(rows, boundaries=count, codec="json", proofbit=False)
        software_compact = _run_pipeline(rows, boundaries=count, codec="compact", proofbit=False)
        proofbit_compact = _run_pipeline(rows, boundaries=count, codec="compact", proofbit=True)
        scale.append(
            {
                "boundaries": count,
                "systems": {
                    "software_json": software_json,
                    "software_compact": software_compact,
                    "proofbit_compact": proofbit_compact,
                },
                "throughput_ratios": {
                    "proofbit_vs_software_json": (
                        proofbit_compact["trials_per_sec"] / software_json["trials_per_sec"]
                    ),
                    "proofbit_vs_software_compact": (
                        proofbit_compact["trials_per_sec"] / software_compact["trials_per_sec"]
                    ),
                },
                "payload_size_ratios": {
                    "proofbit_vs_software_json": (
                        proofbit_compact["mean_payload_bytes"] / software_json["mean_payload_bytes"]
                    ),
                    "proofbit_vs_software_compact": (
                        proofbit_compact["mean_payload_bytes"] / software_compact["mean_payload_bytes"]
                    ),
                },
            }
        )

    fault_counts = {kind: 0 for kind in ("VALID", *FAULT_KINDS)}
    for row in rows:
        fault_counts[row.kind] += 1
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "scope": (
            "same-host real process IPC trust-envelope transport; correctness first, "
            "then actual encoded bytes and end-to-end wall-clock throughput"
        ),
        "trials": trials,
        "contamination_rate": contamination_rate,
        "fault_kinds": list(FAULT_KINDS),
        "fault_counts": fault_counts,
        "boundaries": list(normalized),
        "compact_record_bytes": COMPACT.size,
        "scale": scale,
        "no_single_winner_score": True,
        "comparison_order": [
            "oracle correctness",
            "unsafe authorization / false-success behavior",
            "statement binding",
            "actual encoded payload bytes",
            "actual local IPC wire bytes",
            "end-to-end process IPC throughput",
        ],
        "caveats": [
            "software_compact is the anti-strawman binary control and uses the same compact record as ProofBit",
            "multiprocessing Pipe is local IPC, not network RPC",
            "worker startup is outside timed region but process scheduling is inside transport latency",
            "compact ids are benchmark registry ids, not cryptographic statement hashes",
            "no cryptographic proof verification is measured",
            "results are not processor, silicon, area, energy, or universal crossover claims",
        ],
    }


def _parse_boundaries(value: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=2_000)
    parser.add_argument("--contamination", type=float, default=0.12)
    parser.add_argument("--boundaries", default="1,2,4,8")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(
        trials=args.trials,
        contamination_rate=args.contamination,
        boundaries=_parse_boundaries(args.boundaries),
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for row in report["scale"]:
            print(f"boundaries={row['boundaries']}")
            for name, system in row["systems"].items():
                print(
                    f"  {name}: {system['trials_per_sec']:.1f}/s "
                    f"payload={system['mean_payload_bytes']:.1f}B "
                    f"correct={system['oracle_accuracy']:.3f}"
                )


if __name__ == "__main__":
    main()
