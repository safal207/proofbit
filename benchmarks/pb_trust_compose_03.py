#!/usr/bin/env python3
"""PB-TRUST-COMPOSE-03 dynamic trust over real local IPC.

The benchmark compares three competent implementations on the same compact
records and frozen oracle:

* software_eager: conventional software with replicated epoch caches and eager
  revocation updates to every worker;
* software_lazy: conventional software that revalidates at the final dispatch
  seam and only updates that authoritative gate;
* proofbit_lazy: the same lazy topology, but the final gate evaluates the
  authorization and outcome evidence through ProofProcessor.

The experiment is deliberately designed so that a strong conventional lazy
control can falsify any claim that lazy end-to-end trust is uniquely ProofBit.
It measures correctness first, then real IPC application-payload bytes,
revocation traffic, executed validation events, and wall-clock throughput.
It is not a network, cryptographic, silicon, area, or energy benchmark.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import multiprocessing as mp
from pathlib import Path
import queue
import statistics
import struct
import sys
import time
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.model import EpistemicState, Evidence, ProofProcessor

BENCHMARK_ID = "PB-TRUST-COMPOSE-03"
VERSION = "0.1"
PROTOCOL = "PB-TC03/v0.1 dynamic-trust-real-ipc"
SYSTEMS = ("software_eager", "software_lazy", "proofbit_lazy")
FAULT_KINDS = (
    "IN_FLIGHT_REVOKE",
    "REPLAY",
    "REBIND_STATEMENT",
    "PROVENANCE_DROP",
    "FALSE_SUCCESS",
)
DEFAULT_BOUNDARIES = (1, 2, 4, 8)

FRAME_ACTION = 1
FRAME_OUTCOME = 2
FLAG_BLOCKED = 1 << 0

ACTION = struct.Struct("!BBBBIIQIIQ")
# type, kind_id, flags, reserved, action_id, statement_id, proof_id,
# authority, issued_epoch, provenance
OUTCOME = struct.Struct("!BIIQIQ")
# type, action_id, authority, proof_id, epoch, provenance
CONTROL = struct.Struct("!BI")
# control_type=1, new_epoch
RESPONSE = struct.Struct("!B?")
# response_type (action=1/outcome=2), boolean decision
STOP = b""
CONTROL_EPOCH = 1

KIND_TO_ID = {"VALID": 0, **{kind: index + 1 for index, kind in enumerate(FAULT_KINDS)}}
ID_TO_KIND = {value: key for key, value in KIND_TO_ID.items()}


@dataclass(frozen=True)
class Trial:
    index: int
    kind: str
    action_id: int


@dataclass(frozen=True)
class ActionMessage:
    kind: str
    flags: int
    action_id: int
    statement_id: int
    proof_id: int
    authority: int
    issued_epoch: int
    provenance: int


@dataclass(frozen=True)
class OutcomeMessage:
    action_id: int
    authority: int
    proof_id: int
    epoch: int
    provenance: int


class SoftwareDynamicGuard:
    def __init__(self, authority: int = 1, epoch: int = 1) -> None:
        self.authority = authority
        self.epoch = epoch
        self.consumed: set[int] = set()
        self.dispatched: set[int] = set()
        self.completed: set[int] = set()

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def authorize(self, message: ActionMessage) -> bool:
        if message.flags & FLAG_BLOCKED:
            return False
        if message.statement_id != message.action_id:
            return False
        if message.provenance != message.action_id:
            return False
        if message.authority != self.authority or message.issued_epoch != self.epoch:
            return False
        if message.proof_id in self.consumed:
            return False
        self.consumed.add(message.proof_id)
        self.dispatched.add(message.action_id)
        return True

    def outcome(self, message: OutcomeMessage) -> bool:
        if message.action_id not in self.dispatched:
            return False
        if message.action_id in self.completed:
            return False
        if message.provenance != message.action_id:
            return False
        if message.authority != self.authority or message.epoch != self.epoch:
            return False
        self.completed.add(message.action_id)
        return True


class ProofBitDynamicGuard:
    def __init__(self, authority: int = 1, epoch: int = 1) -> None:
        self.cpu = ProofProcessor(authority=authority, epoch=epoch)
        self.dispatched: set[int] = set()
        self.completed: set[int] = set()

    def set_epoch(self, epoch: int) -> None:
        self.cpu.epoch = epoch

    def authorize(self, message: ActionMessage) -> bool:
        if message.flags & FLAG_BLOCKED:
            return False
        # Provenance is part of this workload's consumption contract. The
        # reference ProofProcessor does not yet encode that policy itself, so
        # the guard makes the same explicit comparison as the software control.
        if message.provenance != message.action_id:
            return False
        evidence = Evidence(
            statement=f"action:{message.statement_id}",
            value=True,
            proof_id=message.proof_id,
            authority=message.authority,
            epoch=message.issued_epoch,
            provenance=message.provenance,
        )
        self.cpu.store_evidence(message.action_id, evidence)
        dispatched = self.cpu.guarded_execute(
            message.action_id,
            expected_statement=f"action:{message.action_id}",
        )
        if dispatched:
            self.dispatched.add(message.action_id)
        return dispatched

    def outcome(self, message: OutcomeMessage) -> bool:
        if message.action_id not in self.dispatched:
            return False
        if message.action_id in self.completed:
            return False
        if message.provenance != message.action_id:
            return False
        evidence = Evidence(
            statement=f"outcome:{message.action_id}",
            value=True,
            proof_id=message.proof_id,
            authority=message.authority,
            epoch=message.epoch,
            provenance=message.provenance,
        )
        state = self.cpu.verify(evidence, consume=True)
        if state is EpistemicState.PROVEN_TRUE:
            self.completed.add(message.action_id)
            return True
        return False


def _validate_inputs(
    trials: int, contamination_rate: float, boundaries: Iterable[int], rounds: int
) -> tuple[int, tuple[int, ...]]:
    if trials <= 0:
        raise ValueError("trials must be positive")
    if not 0 <= contamination_rate <= 1:
        raise ValueError("contamination_rate must be between 0 and 1")
    normalized = tuple(int(item) for item in boundaries)
    if not normalized or any(item <= 0 for item in normalized):
        raise ValueError("boundaries must contain positive integers")
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    return round(trials * contamination_rate), normalized


def build_trials(trials: int, contamination_rate: float) -> list[Trial]:
    bad_count, _ = _validate_inputs(trials, contamination_rate, (1,), 1)
    bad_seen = 0
    rows: list[Trial] = []
    for index in range(trials):
        contaminated = ((index + 1) * bad_count) // trials > (index * bad_count) // trials
        if contaminated:
            kind = FAULT_KINDS[bad_seen % len(FAULT_KINDS)]
            bad_seen += 1
        else:
            kind = "VALID"
        rows.append(Trial(index=index, kind=kind, action_id=index + 1))
    return rows


def expected(kind: str) -> tuple[bool, bool | None, bool]:
    if kind == "VALID":
        return True, None, True
    if kind == "REPLAY":
        return True, False, True
    if kind == "FALSE_SUCCESS":
        return True, None, False
    if kind in {"IN_FLIGHT_REVOKE", "REBIND_STATEMENT", "PROVENANCE_DROP"}:
        return False, None, False
    raise ValueError(kind)


def encode_action(message: ActionMessage) -> bytes:
    return ACTION.pack(
        FRAME_ACTION,
        KIND_TO_ID[message.kind],
        message.flags,
        0,
        message.action_id,
        message.statement_id,
        message.proof_id,
        message.authority,
        message.issued_epoch,
        message.provenance,
    )


def decode_action(payload: bytes) -> ActionMessage:
    (
        frame_type,
        kind_id,
        flags,
        _reserved,
        action_id,
        statement_id,
        proof_id,
        authority,
        issued_epoch,
        provenance,
    ) = ACTION.unpack(payload)
    if frame_type != FRAME_ACTION:
        raise ValueError("not an action frame")
    return ActionMessage(
        kind=ID_TO_KIND[kind_id],
        flags=flags,
        action_id=action_id,
        statement_id=statement_id,
        proof_id=proof_id,
        authority=authority,
        issued_epoch=issued_epoch,
        provenance=provenance,
    )


def encode_outcome(message: OutcomeMessage) -> bytes:
    return OUTCOME.pack(
        FRAME_OUTCOME,
        message.action_id,
        message.authority,
        message.proof_id,
        message.epoch,
        message.provenance,
    )


def decode_outcome(payload: bytes) -> OutcomeMessage:
    frame_type, action_id, authority, proof_id, epoch, provenance = OUTCOME.unpack(payload)
    if frame_type != FRAME_OUTCOME:
        raise ValueError("not an outcome frame")
    return OutcomeMessage(action_id, authority, proof_id, epoch, provenance)


def _set_action_flags(payload: bytes, flags: int) -> bytes:
    message = decode_action(payload)
    return encode_action(
        ActionMessage(
            kind=message.kind,
            flags=flags,
            action_id=message.action_id,
            statement_id=message.statement_id,
            proof_id=message.proof_id,
            authority=message.authority,
            issued_epoch=message.issued_epoch,
            provenance=message.provenance,
        )
    )


def _mutate_action(payload: bytes, mutation_stage: bool) -> bytes:
    if not mutation_stage:
        return payload
    message = decode_action(payload)
    statement_id = message.statement_id
    provenance = message.provenance
    if message.kind == "REBIND_STATEMENT":
        statement_id += 10_000_000
    elif message.kind == "PROVENANCE_DROP":
        provenance = 0
    if statement_id == message.statement_id and provenance == message.provenance:
        return payload
    return encode_action(
        ActionMessage(
            kind=message.kind,
            flags=message.flags,
            action_id=message.action_id,
            statement_id=statement_id,
            proof_id=message.proof_id,
            authority=message.authority,
            issued_epoch=message.issued_epoch,
            provenance=provenance,
        )
    )


def _drain_controls(control_recv: Any, current_epoch: int) -> tuple[int, int]:
    updates = 0
    while control_recv.poll():
        payload = control_recv.recv_bytes()
        control_type, epoch = CONTROL.unpack(payload)
        if control_type != CONTROL_EPOCH:
            raise ValueError("unknown control frame")
        current_epoch = epoch
        updates += 1
    return current_epoch, updates


def _worker(
    recv_conn: Any,
    send_conn: Any,
    control_recv: Any,
    stats_queue: Any,
    *,
    index: int,
    boundaries: int,
    system: str,
    mutation_index: int,
    barrier_ack_send: Any | None,
    barrier_release_recv: Any | None,
) -> None:
    final = index == boundaries - 1
    eager = system == "software_eager"
    proofbit = system == "proofbit_lazy"
    current_epoch = 1
    software_guard = SoftwareDynamicGuard() if final and not proofbit else None
    proof_guard = ProofBitDynamicGuard() if final and proofbit else None
    stats = {
        "epoch_checks": 0,
        "full_authorization_validations": 0,
        "outcome_validations": 0,
        "control_updates": 0,
        "mutations": 0,
        "audit_records": 0,
    }
    try:
        while True:
            payload = recv_conn.recv_bytes()
            if payload == STOP:
                if not final:
                    send_conn.send_bytes(STOP)
                break

            frame_type = payload[0]
            if frame_type == FRAME_ACTION:
                message = decode_action(payload)
                if (
                    index == 0
                    and message.kind == "IN_FLIGHT_REVOKE"
                    and barrier_ack_send is not None
                    and barrier_release_recv is not None
                ):
                    barrier_ack_send.send_bytes(b"R")
                    barrier_release_recv.recv_bytes()

                current_epoch, updates = _drain_controls(control_recv, current_epoch)
                stats["control_updates"] += updates
                if final:
                    if software_guard is not None:
                        software_guard.set_epoch(current_epoch)
                    if proof_guard is not None:
                        proof_guard.set_epoch(current_epoch)

                before = payload
                payload = _mutate_action(payload, index == mutation_index)
                if payload != before:
                    stats["mutations"] += 1

                message = decode_action(payload)
                if eager:
                    stats["epoch_checks"] += 1
                    if message.issued_epoch != current_epoch:
                        payload = _set_action_flags(payload, message.flags | FLAG_BLOCKED)

                if final:
                    stats["full_authorization_validations"] += 1
                    message = decode_action(payload)
                    if proof_guard is not None:
                        decision = proof_guard.authorize(message)
                    else:
                        assert software_guard is not None
                        decision = software_guard.authorize(message)
                    stats["audit_records"] += 1
                    send_conn.send_bytes(RESPONSE.pack(FRAME_ACTION, decision))
                else:
                    send_conn.send_bytes(payload)

            elif frame_type == FRAME_OUTCOME:
                current_epoch, updates = _drain_controls(control_recv, current_epoch)
                stats["control_updates"] += updates
                if final:
                    if software_guard is not None:
                        software_guard.set_epoch(current_epoch)
                    if proof_guard is not None:
                        proof_guard.set_epoch(current_epoch)
                    message = decode_outcome(payload)
                    stats["outcome_validations"] += 1
                    if proof_guard is not None:
                        decision = proof_guard.outcome(message)
                    else:
                        assert software_guard is not None
                        decision = software_guard.outcome(message)
                    stats["audit_records"] += 1
                    send_conn.send_bytes(RESPONSE.pack(FRAME_OUTCOME, decision))
                else:
                    send_conn.send_bytes(payload)
            else:
                raise ValueError(f"unknown frame type {frame_type}")
    finally:
        stats_queue.put(stats)
        recv_conn.close()
        send_conn.close()
        control_recv.close()
        if barrier_ack_send is not None:
            barrier_ack_send.close()
        if barrier_release_recv is not None:
            barrier_release_recv.close()


def _new_kind_metrics() -> dict[str, int]:
    return {
        "trials": 0,
        "oracle_correct": 0,
        "unsafe_dispatches": 0,
        "false_success_claims": 0,
        "missed_valid_dispatches": 0,
        "replay_duplicates_accepted": 0,
    }


def _score(
    per_kind: dict[str, dict[str, int]],
    kind: str,
    primary: bool,
    duplicate: bool | None,
    terminal: bool,
) -> None:
    expected_primary, expected_duplicate, expected_terminal = expected(kind)
    row = per_kind[kind]
    row["trials"] += 1
    if (primary, duplicate, terminal) == (
        expected_primary,
        expected_duplicate,
        expected_terminal,
    ):
        row["oracle_correct"] += 1
    if kind in {"IN_FLIGHT_REVOKE", "REBIND_STATEMENT", "PROVENANCE_DROP"} and primary:
        row["unsafe_dispatches"] += 1
    if kind == "FALSE_SUCCESS" and terminal:
        row["false_success_claims"] += 1
    if kind in {"VALID", "REPLAY", "FALSE_SUCCESS"} and not primary:
        row["missed_valid_dispatches"] += 1
    if kind == "REPLAY" and duplicate:
        row["replay_duplicates_accepted"] += 1


def _run_once(rows: list[Trial], *, boundaries: int, system: str) -> dict[str, Any]:
    if system not in SYSTEMS:
        raise ValueError(system)
    ctx = mp.get_context("fork")
    edges = [ctx.Pipe(duplex=False) for _ in range(boundaries + 1)]
    control_edges = [ctx.Pipe(duplex=False) for _ in range(boundaries)]
    barrier_ack_recv, barrier_ack_send = ctx.Pipe(duplex=False)
    barrier_release_recv, barrier_release_send = ctx.Pipe(duplex=False)
    stats_queue = ctx.Queue()
    processes: list[mp.Process] = []
    mutation_index = boundaries // 2

    for index in range(boundaries):
        process = ctx.Process(
            target=_worker,
            args=(edges[index][0], edges[index + 1][1], control_edges[index][0], stats_queue),
            kwargs={
                "index": index,
                "boundaries": boundaries,
                "system": system,
                "mutation_index": mutation_index,
                "barrier_ack_send": barrier_ack_send if index == 0 else None,
                "barrier_release_recv": barrier_release_recv if index == 0 else None,
            },
        )
        process.start()
        processes.append(process)

    parent_send = edges[0][1]
    parent_recv = edges[-1][0]
    control_senders = [item[1] for item in control_edges]
    per_kind = {kind: _new_kind_metrics() for kind in ("VALID", *FAULT_KINDS)}

    current_epoch = 1
    data_request_bytes = 0
    outcome_request_bytes = 0
    response_bytes = 0
    control_payload_bytes = 0
    data_messages = 0
    outcome_messages = 0
    response_messages = 0
    control_messages = 0
    revocations = 0
    action_sends = 0
    outcome_sends = 0

    started = time.perf_counter_ns()
    try:
        for row in rows:
            action = ActionMessage(
                kind=row.kind,
                flags=0,
                action_id=row.action_id,
                statement_id=row.action_id,
                proof_id=row.index + 1,
                authority=1,
                issued_epoch=current_epoch,
                provenance=row.action_id,
            )
            payload = encode_action(action)
            parent_send.send_bytes(payload)
            action_sends += 1
            data_request_bytes += len(payload) * boundaries
            data_messages += boundaries

            if row.kind == "IN_FLIGHT_REVOKE":
                barrier_ack_recv.recv_bytes()
                current_epoch += 1
                revocations += 1
                targets = range(boundaries) if system == "software_eager" else (boundaries - 1,)
                control_payload = CONTROL.pack(CONTROL_EPOCH, current_epoch)
                for target in targets:
                    control_senders[target].send_bytes(control_payload)
                    control_messages += 1
                    control_payload_bytes += len(control_payload)
                barrier_release_send.send_bytes(b"G")

            response = parent_recv.recv_bytes()
            response_type, primary = RESPONSE.unpack(response)
            if response_type != FRAME_ACTION:
                raise RuntimeError("expected action response")
            response_bytes += len(response)
            response_messages += 1

            duplicate: bool | None = None
            if row.kind == "REPLAY":
                parent_send.send_bytes(payload)
                action_sends += 1
                data_request_bytes += len(payload) * boundaries
                data_messages += boundaries
                response = parent_recv.recv_bytes()
                response_type, duplicate = RESPONSE.unpack(response)
                if response_type != FRAME_ACTION:
                    raise RuntimeError("expected duplicate action response")
                response_bytes += len(response)
                response_messages += 1

            terminal = False
            if row.kind in {"VALID", "REPLAY"} and primary:
                outcome = OutcomeMessage(
                    action_id=row.action_id,
                    authority=1,
                    proof_id=1_000_000 + row.index,
                    epoch=current_epoch,
                    provenance=row.action_id,
                )
                outcome_payload = encode_outcome(outcome)
                parent_send.send_bytes(outcome_payload)
                outcome_sends += 1
                outcome_request_bytes += len(outcome_payload) * boundaries
                outcome_messages += boundaries
                response = parent_recv.recv_bytes()
                response_type, terminal = RESPONSE.unpack(response)
                if response_type != FRAME_OUTCOME:
                    raise RuntimeError("expected outcome response")
                response_bytes += len(response)
                response_messages += 1

            _score(per_kind, row.kind, primary, duplicate, terminal)

        parent_send.send_bytes(STOP)
    finally:
        parent_send.close()
        parent_recv.close()
        barrier_ack_recv.close()
        barrier_release_send.close()
        for sender in control_senders:
            sender.close()
        for process in processes:
            process.join(timeout=15)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            if process.exitcode != 0:
                raise RuntimeError(f"dynamic trust worker exited with {process.exitcode}")

    elapsed_ns = time.perf_counter_ns() - started
    worker_stats = []
    for _ in processes:
        try:
            worker_stats.append(stats_queue.get(timeout=5))
        except queue.Empty as exc:
            raise RuntimeError("missing worker statistics") from exc
    stats_queue.close()

    trials = len(rows)
    correct = sum(item["oracle_correct"] for item in per_kind.values())
    unsafe = sum(item["unsafe_dispatches"] for item in per_kind.values())
    false_success = sum(item["false_success_claims"] for item in per_kind.values())
    missed = sum(item["missed_valid_dispatches"] for item in per_kind.values())
    replay_accepted = sum(item["replay_duplicates_accepted"] for item in per_kind.values())
    seconds = elapsed_ns / 1_000_000_000
    validation_events = {
        key: sum(item[key] for item in worker_stats)
        for key in (
            "epoch_checks",
            "full_authorization_validations",
            "outcome_validations",
            "control_updates",
            "mutations",
            "audit_records",
        )
    }
    total_request_payload = data_request_bytes + outcome_request_bytes
    total_ipc_payload = total_request_payload + response_bytes + control_payload_bytes
    transport_messages = data_messages + outcome_messages + response_messages + control_messages

    return {
        "system": system,
        "architecture": (
            "Conventional CPU / eager replicated trust cache"
            if system == "software_eager"
            else (
                "Conventional CPU / lazy dispatch-seam revalidation"
                if system == "software_lazy"
                else "ProofBit / lazy proof-aware dispatch-seam revalidation"
            )
        ),
        "boundaries": boundaries,
        "worker_processes": boundaries,
        "trials": trials,
        "revocations": revocations,
        "oracle_correct_trials": correct,
        "oracle_accuracy": correct / trials,
        "unsafe_authorization_dispatches": unsafe,
        "false_success_claims": false_success,
        "missed_valid_dispatches": missed,
        "replay_duplicates_accepted": replay_accepted,
        "per_kind": per_kind,
        "elapsed_ns": elapsed_ns,
        "trials_per_sec": trials / seconds if seconds else 0.0,
        "action_record_bytes": ACTION.size,
        "outcome_record_bytes": OUTCOME.size,
        "control_record_bytes": CONTROL.size,
        "response_record_bytes": RESPONSE.size,
        "action_sends": action_sends,
        "outcome_sends": outcome_sends,
        "data_request_ipc_payload_bytes": data_request_bytes,
        "outcome_request_ipc_payload_bytes": outcome_request_bytes,
        "response_ipc_payload_bytes": response_bytes,
        "control_ipc_payload_bytes": control_payload_bytes,
        "total_request_ipc_payload_bytes": total_request_payload,
        "total_ipc_payload_bytes": total_ipc_payload,
        "data_messages": data_messages,
        "outcome_messages": outcome_messages,
        "response_messages": response_messages,
        "control_messages": control_messages,
        "transport_messages": transport_messages,
        "validation_events": validation_events,
        "claim_boundary": (
            "Real same-host multiprocessing Pipe IPC with deterministic in-flight revocation barrier. "
            "Byte counters are application payload bytes passed to send_bytes/recv_bytes and exclude "
            "Pipe framing/kernel copies. No network, cryptographic, silicon, energy, or area claim."
        ),
    }


def _aggregate(runs: list[dict[str, Any]]) -> dict[str, Any]:
    first = runs[0]
    for run in runs[1:]:
        for key in (
            "oracle_accuracy",
            "unsafe_authorization_dispatches",
            "false_success_claims",
            "missed_valid_dispatches",
            "replay_duplicates_accepted",
            "control_messages",
            "control_ipc_payload_bytes",
            "total_request_ipc_payload_bytes",
            "total_ipc_payload_bytes",
            "validation_events",
        ):
            if run[key] != first[key]:
                raise RuntimeError(f"non-timing metric changed across rounds: {key}")
    throughputs = [run["trials_per_sec"] for run in runs]
    elapsed = [run["elapsed_ns"] for run in runs]
    return {
        "system": first["system"],
        "architecture": first["architecture"],
        "rounds": len(runs),
        "oracle_accuracy": first["oracle_accuracy"],
        "unsafe_authorization_dispatches": first["unsafe_authorization_dispatches"],
        "false_success_claims": first["false_success_claims"],
        "missed_valid_dispatches": first["missed_valid_dispatches"],
        "replay_duplicates_accepted": first["replay_duplicates_accepted"],
        "revocations": first["revocations"],
        "action_record_bytes": first["action_record_bytes"],
        "outcome_record_bytes": first["outcome_record_bytes"],
        "control_record_bytes": first["control_record_bytes"],
        "response_record_bytes": first["response_record_bytes"],
        "total_request_ipc_payload_bytes": first["total_request_ipc_payload_bytes"],
        "control_ipc_payload_bytes": first["control_ipc_payload_bytes"],
        "total_ipc_payload_bytes": first["total_ipc_payload_bytes"],
        "control_messages": first["control_messages"],
        "transport_messages": first["transport_messages"],
        "validation_events": first["validation_events"],
        "median_elapsed_ns": int(statistics.median(elapsed)),
        "median_trials_per_sec": statistics.median(throughputs),
        "min_trials_per_sec": min(throughputs),
        "max_trials_per_sec": max(throughputs),
        "raw_trials_per_sec": throughputs,
    }


def build_report(
    trials: int = 2_000,
    contamination_rate: float = 0.15,
    boundaries: Iterable[int] = DEFAULT_BOUNDARIES,
    rounds: int = 5,
) -> dict[str, Any]:
    _, normalized = _validate_inputs(trials, contamination_rate, boundaries, rounds)
    rows = build_trials(trials, contamination_rate)
    fault_counts = {
        kind: sum(1 for row in rows if row.kind == kind) for kind in ("VALID", *FAULT_KINDS)
    }
    scale: list[dict[str, Any]] = []
    for count in normalized:
        systems: dict[str, Any] = {}
        for system in SYSTEMS:
            runs = [_run_once(rows, boundaries=count, system=system) for _ in range(rounds)]
            systems[system] = _aggregate(runs)
        scale.append(
            {
                "boundaries": count,
                "systems": systems,
                "median_throughput_ratios": {
                    "proofbit_vs_software_eager": (
                        systems["proofbit_lazy"]["median_trials_per_sec"]
                        / systems["software_eager"]["median_trials_per_sec"]
                    ),
                    "proofbit_vs_software_lazy": (
                        systems["proofbit_lazy"]["median_trials_per_sec"]
                        / systems["software_lazy"]["median_trials_per_sec"]
                    ),
                    "software_lazy_vs_eager": (
                        systems["software_lazy"]["median_trials_per_sec"]
                        / systems["software_eager"]["median_trials_per_sec"]
                    ),
                },
            }
        )
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "scope": (
            "dynamic authority/replay/provenance/outcome trust maintenance over real same-host IPC; "
            "strong eager and lazy conventional controls; no single winner score"
        ),
        "trials_per_round": trials,
        "rounds": rounds,
        "contamination_rate": contamination_rate,
        "boundaries": list(normalized),
        "fault_kinds": list(FAULT_KINDS),
        "fault_counts": fault_counts,
        "record_bytes": {
            "action": ACTION.size,
            "outcome": OUTCOME.size,
            "control": CONTROL.size,
            "response": RESPONSE.size,
        },
        "no_single_winner_score": True,
        "comparison_rule": (
            "software_lazy vs proofbit_lazy is the primary semantic comparison because both use the "
            "same compact records and the same one-gate revocation topology; software_eager separately "
            "measures replicated-cache invalidation cost"
        ),
        "scale": scale,
        "caveats": [
            "software_lazy is a strong anti-strawman control and can falsify ProofBit-specific advantage",
            "in-flight revocation is deterministic: stage 0 acknowledges receipt, parent updates epoch, then releases the frame",
            "outcome success is accepted only from a separate outcome record after dispatch",
            "partial-process-failure audit reconstruction is deferred to a later experiment",
            "byte counters exclude multiprocessing framing and kernel copies",
            "no cryptographic proof verification is measured",
            "results are not processor, network, silicon, energy, area, novelty, patentability, or universal crossover claims",
        ],
    }


def _parse_boundaries(value: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=2_000)
    parser.add_argument("--contamination", type=float, default=0.15)
    parser.add_argument("--boundaries", type=_parse_boundaries, default=DEFAULT_BOUNDARIES)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report(
        trials=args.trials,
        contamination_rate=args.contamination,
        boundaries=args.boundaries,
        rounds=args.rounds,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"{BENCHMARK_ID} {PROTOCOL}")
    for row in report["scale"]:
        systems = row["systems"]
        print(f"boundaries={row['boundaries']}")
        for name in SYSTEMS:
            system = systems[name]
            print(
                f"  {name}: {system['median_trials_per_sec']:.1f}/s "
                f"control={system['control_messages']} "
                f"validation={system['validation_events']}"
            )
        print(f"  ratios={row['median_throughput_ratios']}")


if __name__ == "__main__":
    main()
