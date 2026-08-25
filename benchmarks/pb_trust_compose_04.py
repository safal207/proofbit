from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
from pathlib import Path
import statistics
import struct
import tempfile
import time
from typing import Iterable


BENCHMARK_ID = "PB-TRUST-COMPOSE-04"
VERSION = "0.1"
PROTOCOL = "PB-TC04/v0.1 crash-recovery-audit"
CRASH_EXIT_CODE = 97
NO_OFFSET = (1 << 64) - 1
CURRENT_EPOCH = 1
ACTION_STATEMENT = 0x50524F4F46424954  # "PROOFBit"-like stable integer tag.

# Equal fixed-width durable event/receipt record for every system.
# tx_id, kind, value, flags, reserved, statement_id, proof_id, epoch,
# prev_offset, receipt_id
RECORD = struct.Struct(">IBBBBQQQQQ")
HEAD = struct.Struct(">Q")

SYSTEMS = ("software_scan", "software_indexed", "proofbit_receipts")
STATES = (
    "NOT_AUTHORIZED",
    "AUTHORIZED_NOT_EXECUTED",
    "EXECUTED_OUTCOME_UNKNOWN",
    "EXECUTED_OUTCOME_PROVEN",
    "CONFLICT",
)

K_REQUEST = 1
K_AUTHORIZED = 2
K_EXECUTED = 3
K_OUTCOME_OK = 4
K_OUTCOME_FAIL = 5
K_RETRY_SEEN = 6


def build_workload(transactions: int) -> list[dict]:
    if transactions <= 0:
        raise ValueError("transactions must be positive")
    rows: list[dict] = []
    for tx_id in range(transactions):
        state = STATES[tx_id % len(STATES)]
        # Half of PROVEN outcomes are durable before the crash and half arrive
        # after restart. This freezes both timing orders without changing the
        # final recovery oracle.
        outcome_precrash = (
            state == "EXECUTED_OUTCOME_PROVEN" and ((tx_id // len(STATES)) % 2 == 0)
        )
        rows.append(
            {
                "tx_id": tx_id,
                "expected_state": state,
                "outcome_precrash": outcome_precrash,
            }
        )
    return rows


def _storage_paths(root: Path, system: str) -> tuple[Path, Path]:
    return root / f"{system}.journal", root / f"{system}.heads"


def _init_storage(root: Path, system: str, transactions: int) -> None:
    journal, heads = _storage_paths(root, system)
    journal.write_bytes(b"")
    if system == "software_scan":
        heads.write_bytes(b"")
        return
    with heads.open("wb", buffering=0) as handle:
        for _ in range(transactions):
            handle.write(HEAD.pack(NO_OFFSET))
        os.fsync(handle.fileno())


def _read_head(handle, tx_id: int) -> int:
    handle.seek(tx_id * HEAD.size)
    raw = handle.read(HEAD.size)
    if len(raw) != HEAD.size:
        raise RuntimeError("short durable head read")
    return HEAD.unpack(raw)[0]


def _write_head(handle, tx_id: int, offset: int) -> None:
    handle.seek(tx_id * HEAD.size)
    handle.write(HEAD.pack(offset))


def _append_record(
    journal_handle,
    head_handle,
    system: str,
    tx_id: int,
    kind: int,
    *,
    receipt_id: int,
    previous_offsets: dict[int, int] | None = None,
) -> int:
    if system == "software_scan":
        assert previous_offsets is not None
        prev = previous_offsets.get(tx_id, NO_OFFSET)
    else:
        assert head_handle is not None
        prev = _read_head(head_handle, tx_id)

    offset = journal_handle.seek(0, os.SEEK_END)
    proof_id = receipt_id if system == "proofbit_receipts" else 0
    journal_handle.write(
        RECORD.pack(
            tx_id,
            kind,
            1,
            0,
            0,
            ACTION_STATEMENT,
            proof_id,
            CURRENT_EPOCH,
            prev,
            receipt_id,
        )
    )

    if system == "software_scan":
        previous_offsets[tx_id] = offset
    else:
        _write_head(head_handle, tx_id, offset)
    return offset


def _precrash_writer(root: str, system: str, rows: list[dict]) -> None:
    root_path = Path(root)
    journal_path, heads_path = _storage_paths(root_path, system)
    previous_offsets: dict[int, int] = {}
    head_handle = None
    receipt_id = 1

    with journal_path.open("ab+", buffering=0) as journal_handle:
        if system != "software_scan":
            head_handle = heads_path.open("r+b", buffering=0)
        try:
            for row in rows:
                tx_id = row["tx_id"]
                _append_record(
                    journal_handle,
                    head_handle,
                    system,
                    tx_id,
                    K_REQUEST,
                    receipt_id=receipt_id,
                    previous_offsets=previous_offsets,
                )
                receipt_id += 1

                state = row["expected_state"]
                if state == "NOT_AUTHORIZED":
                    continue

                _append_record(
                    journal_handle,
                    head_handle,
                    system,
                    tx_id,
                    K_AUTHORIZED,
                    receipt_id=receipt_id,
                    previous_offsets=previous_offsets,
                )
                receipt_id += 1

                if state == "AUTHORIZED_NOT_EXECUTED":
                    continue

                _append_record(
                    journal_handle,
                    head_handle,
                    system,
                    tx_id,
                    K_EXECUTED,
                    receipt_id=receipt_id,
                    previous_offsets=previous_offsets,
                )
                receipt_id += 1

                if state == "EXECUTED_OUTCOME_PROVEN" and row["outcome_precrash"]:
                    _append_record(
                        journal_handle,
                        head_handle,
                        system,
                        tx_id,
                        K_OUTCOME_OK,
                        receipt_id=receipt_id,
                        previous_offsets=previous_offsets,
                    )
                    receipt_id += 1
                elif state == "CONFLICT":
                    # First outcome is durable before the crash. A contradictory
                    # outcome arrives after restart.
                    _append_record(
                        journal_handle,
                        head_handle,
                        system,
                        tx_id,
                        K_OUTCOME_OK,
                        receipt_id=receipt_id,
                        previous_offsets=previous_offsets,
                    )
                    receipt_id += 1

            os.fsync(journal_handle.fileno())
            if head_handle is not None:
                os.fsync(head_handle.fileno())
        finally:
            if head_handle is not None:
                head_handle.close()

    # Hard process exit after durable writes. No finally/atexit path is allowed
    # to manufacture a graceful shutdown marker.
    os._exit(CRASH_EXIT_CODE)


def _unpack_record(raw: bytes) -> dict:
    (
        tx_id,
        kind,
        value,
        flags,
        reserved,
        statement_id,
        proof_id,
        epoch,
        prev_offset,
        receipt_id,
    ) = RECORD.unpack(raw)
    return {
        "tx_id": tx_id,
        "kind": kind,
        "value": value,
        "flags": flags,
        "reserved": reserved,
        "statement_id": statement_id,
        "proof_id": proof_id,
        "epoch": epoch,
        "prev_offset": prev_offset,
        "receipt_id": receipt_id,
    }


def _read_record_at(handle, offset: int) -> dict:
    handle.seek(offset)
    raw = handle.read(RECORD.size)
    if len(raw) != RECORD.size:
        raise RuntimeError("short durable record read")
    return _unpack_record(raw)


def _scan_all(journal_path: Path) -> tuple[dict[int, list[dict]], int, dict[int, int]]:
    grouped: dict[int, list[dict]] = {}
    last_offsets: dict[int, int] = {}
    inspected = 0
    with journal_path.open("rb", buffering=0) as handle:
        offset = 0
        while True:
            raw = handle.read(RECORD.size)
            if not raw:
                break
            if len(raw) != RECORD.size:
                raise RuntimeError("torn journal record")
            record = _unpack_record(raw)
            grouped.setdefault(record["tx_id"], []).append(record)
            last_offsets[record["tx_id"]] = offset
            inspected += 1
            offset += RECORD.size
    return grouped, inspected, last_offsets


def _chain_for_tx(
    journal_handle,
    head_handle,
    tx_id: int,
    *,
    proof_validate: bool,
) -> tuple[list[dict], int, bool]:
    offset = _read_head(head_handle, tx_id)
    records: list[dict] = []
    inspected = 0
    valid = True
    seen_offsets: set[int] = set()

    while offset != NO_OFFSET:
        if offset in seen_offsets or offset % RECORD.size != 0:
            valid = False
            break
        seen_offsets.add(offset)
        record = _read_record_at(journal_handle, offset)
        inspected += 1
        if record["tx_id"] != tx_id:
            valid = False
            break
        if proof_validate:
            if record["statement_id"] != ACTION_STATEMENT:
                valid = False
            if record["epoch"] != CURRENT_EPOCH:
                valid = False
            if record["proof_id"] == 0:
                valid = False
        records.append(record)
        next_offset = record["prev_offset"]
        if next_offset != NO_OFFSET and next_offset >= offset:
            valid = False
            break
        offset = next_offset

    records.reverse()
    return records, inspected, valid


def _indexed_all(
    journal_path: Path,
    heads_path: Path,
    transactions: int,
    *,
    proof_validate: bool,
) -> tuple[dict[int, list[dict]], int, dict[int, bool]]:
    grouped: dict[int, list[dict]] = {}
    validity: dict[int, bool] = {}
    inspected = 0
    with journal_path.open("rb", buffering=0) as journal_handle, heads_path.open(
        "rb", buffering=0
    ) as head_handle:
        for tx_id in range(transactions):
            records, count, valid = _chain_for_tx(
                journal_handle,
                head_handle,
                tx_id,
                proof_validate=proof_validate,
            )
            grouped[tx_id] = records
            validity[tx_id] = valid
            inspected += count
    return grouped, inspected, validity


def _state_from_records(records: Iterable[dict], *, valid_chain: bool = True) -> tuple[str, int]:
    if not valid_chain:
        return "CONFLICT", 0
    kinds = [record["kind"] for record in records]
    execute_count = kinds.count(K_EXECUTED)
    has_auth = K_AUTHORIZED in kinds
    has_ok = K_OUTCOME_OK in kinds
    has_fail = K_OUTCOME_FAIL in kinds

    if has_ok and has_fail:
        return "CONFLICT", execute_count
    if execute_count:
        if has_ok or has_fail:
            return "EXECUTED_OUTCOME_PROVEN", execute_count
        return "EXECUTED_OUTCOME_UNKNOWN", execute_count
    if has_auth:
        return "AUTHORIZED_NOT_EXECUTED", execute_count
    return "NOT_AUTHORIZED", execute_count


def _reconstruct_all(
    root: Path,
    system: str,
    transactions: int,
) -> tuple[dict[int, tuple[str, int]], int, dict[int, int]]:
    journal_path, heads_path = _storage_paths(root, system)
    last_offsets: dict[int, int] = {}
    if system == "software_scan":
        grouped, inspected, last_offsets = _scan_all(journal_path)
        states = {
            tx_id: _state_from_records(grouped.get(tx_id, []))
            for tx_id in range(transactions)
        }
        return states, inspected, last_offsets

    grouped, inspected, validity = _indexed_all(
        journal_path,
        heads_path,
        transactions,
        proof_validate=(system == "proofbit_receipts"),
    )
    states = {
        tx_id: _state_from_records(
            grouped.get(tx_id, []),
            valid_chain=validity.get(tx_id, False),
        )
        for tx_id in range(transactions)
    }
    return states, inspected, last_offsets


def _max_receipt_id(journal_path: Path) -> int:
    grouped, _, _ = _scan_all(journal_path)
    return max(
        (record["receipt_id"] for records in grouped.values() for record in records),
        default=0,
    )


def _targeted_audit(
    root: Path,
    system: str,
    tx_ids: list[int],
) -> int:
    journal_path, heads_path = _storage_paths(root, system)
    inspected = 0
    if system == "software_scan":
        # A targeted audit has no durable index. Each independently requested
        # transaction scans the log to find its full history.
        for tx_id in tx_ids:
            with journal_path.open("rb", buffering=0) as handle:
                while True:
                    raw = handle.read(RECORD.size)
                    if not raw:
                        break
                    if len(raw) != RECORD.size:
                        raise RuntimeError("torn journal record")
                    inspected += 1
                    _ = _unpack_record(raw)
        return inspected

    with journal_path.open("rb", buffering=0) as journal_handle, heads_path.open(
        "rb", buffering=0
    ) as head_handle:
        for tx_id in tx_ids:
            _, count, _ = _chain_for_tx(
                journal_handle,
                head_handle,
                tx_id,
                proof_validate=(system == "proofbit_receipts"),
            )
            inspected += count
    return inspected


def _recovery_worker(
    root: str,
    system: str,
    rows: list[dict],
    audit_sample: int,
    result_path: str,
) -> None:
    root_path = Path(root)
    journal_path, heads_path = _storage_paths(root_path, system)
    transactions = len(rows)

    recovery_start = time.perf_counter_ns()
    before_states, first_inspected, last_offsets = _reconstruct_all(
        root_path, system, transactions
    )

    previous_offsets = last_offsets if system == "software_scan" else None
    head_handle = None
    receipt_id = _max_receipt_id(journal_path) + 1
    with journal_path.open("ab+", buffering=0) as journal_handle:
        if system != "software_scan":
            head_handle = heads_path.open("r+b", buffering=0)
        try:
            for row in rows:
                tx_id = row["tx_id"]
                state_before, execute_count_before = before_states[tx_id]

                # A duplicate/retry arrives after restart for anything that had
                # already executed. Recovery must not execute the side effect a
                # second time.
                if execute_count_before:
                    _append_record(
                        journal_handle,
                        head_handle,
                        system,
                        tx_id,
                        K_RETRY_SEEN,
                        receipt_id=receipt_id,
                        previous_offsets=previous_offsets,
                    )
                    receipt_id += 1

                expected = row["expected_state"]
                if expected == "EXECUTED_OUTCOME_PROVEN" and not row[
                    "outcome_precrash"
                ]:
                    _append_record(
                        journal_handle,
                        head_handle,
                        system,
                        tx_id,
                        K_OUTCOME_OK,
                        receipt_id=receipt_id,
                        previous_offsets=previous_offsets,
                    )
                    receipt_id += 1
                elif expected == "CONFLICT":
                    _append_record(
                        journal_handle,
                        head_handle,
                        system,
                        tx_id,
                        K_OUTCOME_FAIL,
                        receipt_id=receipt_id,
                        previous_offsets=previous_offsets,
                    )
                    receipt_id += 1

            os.fsync(journal_handle.fileno())
            if head_handle is not None:
                os.fsync(head_handle.fileno())
        finally:
            if head_handle is not None:
                head_handle.close()

    final_states, second_inspected, _ = _reconstruct_all(
        root_path, system, transactions
    )
    recovery_elapsed_ns = time.perf_counter_ns() - recovery_start

    correct = 0
    duplicate_side_effects = 0
    false_terminal_success = 0
    ambiguous_terminal_states = 0
    for row in rows:
        state, execute_count = final_states[row["tx_id"]]
        if state == row["expected_state"]:
            correct += 1
        if execute_count > 1:
            duplicate_side_effects += execute_count - 1
        if state == "EXECUTED_OUTCOME_PROVEN" and row["expected_state"] == "EXECUTED_OUTCOME_UNKNOWN":
            false_terminal_success += 1
        if state not in STATES:
            ambiguous_terminal_states += 1

    sample_ids = [row["tx_id"] for row in rows[: min(audit_sample, transactions)]]
    targeted_records = _targeted_audit(root_path, system, sample_ids)

    summary = {
        "system": system,
        "architecture": {
            "software_scan": "Conventional append-only durable event log / no durable per-transaction index",
            "software_indexed": "Conventional append-only durable event log + per-transaction durable head index",
            "proofbit_receipts": "ProofBit typed receipt chain + per-transaction durable head index",
        }[system],
        "oracle_accuracy": correct / transactions,
        "duplicate_side_effects_after_retry": duplicate_side_effects,
        "false_terminal_success": false_terminal_success,
        "ambiguous_terminal_states": ambiguous_terminal_states,
        "full_recovery_records_inspected": first_inspected + second_inspected,
        "targeted_audit_records_inspected": targeted_records,
        "recovery_elapsed_ns": recovery_elapsed_ns,
        "trusted_recovered_states_per_sec": transactions
        / (recovery_elapsed_ns / 1_000_000_000),
        "persisted_journal_bytes": journal_path.stat().st_size,
        "persisted_index_bytes": heads_path.stat().st_size,
        "persisted_total_bytes": journal_path.stat().st_size
        + heads_path.stat().st_size,
        "authority_reestablishment_messages": 1,
        "restart_processes": 1,
        "audit_sample_transactions": len(sample_ids),
    }
    Path(result_path).write_text(json.dumps(summary, sort_keys=True))


def _run_system_once(
    root: Path,
    system: str,
    rows: list[dict],
    audit_sample: int,
) -> dict:
    _init_storage(root, system, len(rows))
    ctx = mp.get_context("fork")

    crash_process = ctx.Process(
        target=_precrash_writer,
        args=(str(root), system, rows),
    )
    crash_process.start()
    crash_process.join()
    if crash_process.exitcode != CRASH_EXIT_CODE:
        raise RuntimeError(
            f"{system} did not exercise hard crash: exit={crash_process.exitcode}"
        )

    result_path = root / f"{system}.result.json"
    restart_start = time.perf_counter_ns()
    recovery_process = ctx.Process(
        target=_recovery_worker,
        args=(str(root), system, rows, audit_sample, str(result_path)),
    )
    recovery_process.start()
    recovery_process.join()
    restart_wall_ns = time.perf_counter_ns() - restart_start
    if recovery_process.exitcode != 0:
        raise RuntimeError(
            f"{system} recovery process failed: exit={recovery_process.exitcode}"
        )

    result = json.loads(result_path.read_text())
    result["hard_crash_exit_code"] = crash_process.exitcode
    result["restart_wall_ns"] = restart_wall_ns
    return result


def _aggregate_rounds(rounds: list[dict]) -> dict:
    first = rounds[0]
    numeric_medians = {}
    for key in (
        "recovery_elapsed_ns",
        "restart_wall_ns",
        "trusted_recovered_states_per_sec",
        "persisted_journal_bytes",
        "persisted_index_bytes",
        "persisted_total_bytes",
        "full_recovery_records_inspected",
        "targeted_audit_records_inspected",
    ):
        numeric_medians[key] = statistics.median(row[key] for row in rounds)

    return {
        "system": first["system"],
        "architecture": first["architecture"],
        "rounds": len(rounds),
        "oracle_accuracy": min(row["oracle_accuracy"] for row in rounds),
        "duplicate_side_effects_after_retry": sum(
            row["duplicate_side_effects_after_retry"] for row in rounds
        ),
        "false_terminal_success": sum(row["false_terminal_success"] for row in rounds),
        "ambiguous_terminal_states": sum(
            row["ambiguous_terminal_states"] for row in rounds
        ),
        "hard_crash_exit_codes": [row["hard_crash_exit_code"] for row in rounds],
        "authority_reestablishment_messages_per_round": first[
            "authority_reestablishment_messages"
        ],
        "audit_sample_transactions": first["audit_sample_transactions"],
        "median": numeric_medians,
        "raw_trusted_recovered_states_per_sec": [
            row["trusted_recovered_states_per_sec"] for row in rounds
        ],
    }


def run_benchmark(
    transactions: int = 500,
    rounds: int = 5,
    audit_sample: int = 25,
) -> dict:
    if rounds <= 0:
        raise ValueError("rounds must be positive")
    rows = build_workload(transactions)
    counts = {state: 0 for state in STATES}
    for row in rows:
        counts[row["expected_state"]] += 1

    all_rounds: dict[str, list[dict]] = {system: [] for system in SYSTEMS}
    with tempfile.TemporaryDirectory(prefix="proofbit-tc04-") as tmp:
        base = Path(tmp)
        for round_index in range(rounds):
            round_root = base / f"round-{round_index}"
            round_root.mkdir()
            for system in SYSTEMS:
                system_root = round_root / system
                system_root.mkdir()
                all_rounds[system].append(
                    _run_system_once(system_root, system, rows, audit_sample)
                )

    systems = {system: _aggregate_rounds(all_rounds[system]) for system in SYSTEMS}
    indexed = systems["software_indexed"]["median"]
    proof = systems["proofbit_receipts"]["median"]

    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "scope": (
            "real hard process crash after fsync, fresh-process restart, retry, "
            "late/conflicting outcome receipts, durable reconstruction and targeted audit"
        ),
        "transactions_per_round": transactions,
        "rounds": rounds,
        "audit_sample_transactions": min(audit_sample, transactions),
        "terminal_state_counts": counts,
        "terminal_states": list(STATES),
        "record_bytes": RECORD.size,
        "head_index_bytes_per_transaction": HEAD.size,
        "systems": systems,
        "primary_ratios": {
            "proofbit_vs_software_indexed_recovery_throughput": (
                proof["trusted_recovered_states_per_sec"]
                / indexed["trusted_recovered_states_per_sec"]
            ),
            "proofbit_vs_software_indexed_persisted_bytes": (
                proof["persisted_total_bytes"] / indexed["persisted_total_bytes"]
            ),
            "proofbit_vs_software_indexed_targeted_audit_records": (
                proof["targeted_audit_records_inspected"]
                / indexed["targeted_audit_records_inspected"]
                if indexed["targeted_audit_records_inspected"]
                else 0.0
            ),
        },
        "no_single_winner_score": True,
        "comparison_rule": (
            "software_indexed is the primary anti-strawman control because it uses "
            "the same fixed-width record size and durable per-transaction head-index "
            "topology as proofbit_receipts; software_scan separately measures the cost "
            "of recovering/auditing an unindexed append-only log"
        ),
        "caveats": [
            "durability uses local file fsync on a GitHub-hosted Linux runner; storage hardware and filesystem behavior are not controlled",
            "the hard crash is a real os._exit process death but not a machine/power failure",
            "software_indexed is intentionally a strong conventional competitor",
            "proof receipts are semantic reference records, not cryptographic proofs",
            "record payload sizes are frozen for fairness and are not silicon storage claims",
            "no network, processor-cycle, energy, area, novelty, patentability, or universal crossover claim",
        ],
    }


def _print_human(report: dict) -> None:
    print(f"{report['benchmark_id']} {report['protocol']}")
    print(
        "system             accuracy  dup_effects  false_success  "
        "recovered/s  persisted_B  audit_records"
    )
    for name in SYSTEMS:
        system = report["systems"][name]
        median = system["median"]
        print(
            f"{name:18s} {system['oracle_accuracy']:8.3f} "
            f"{system['duplicate_side_effects_after_retry']:11d} "
            f"{system['false_terminal_success']:13d} "
            f"{median['trusted_recovered_states_per_sec']:11.1f} "
            f"{median['persisted_total_bytes']:11.0f} "
            f"{median['targeted_audit_records_inspected']:13.0f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transactions", type=int, default=500)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--audit-sample", type=int, default=25)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_benchmark(args.transactions, args.rounds, args.audit_sample)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)


if __name__ == "__main__":
    main()
