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
import zlib


BENCHMARK_ID = "PB-TRUST-COMPOSE-05"
VERSION = "0.1"
PROTOCOL = "PB-TC05/v0.1 durable-corruption-recovery"

NO_OFFSET = (1 << 64) - 1
CURRENT_EPOCH = 1
ACTION_STATEMENT = 0x50524F4F46424954
WRONG_STATEMENT = 0x4241445354415445

# Base payload is the exact 48-byte TC04 record. TC05 adds a 32-bit CRC and
# 32 reserved bits. Every compared system uses the same 56-byte durable record.
BASE = struct.Struct(">IBBBBQQQQQ")
RECORD = struct.Struct(">IBBBBQQQQQII")
HEAD = struct.Struct(">Q")

SYSTEMS = (
    "software_scan_repair",
    "software_indexed_integrity",
    "proofbit_receipts",
)

FAULTS = (
    "CLEAN",
    "JOURNAL_WRITTEN_HEAD_NOT_UPDATED",
    "HEAD_UPDATED_RECORD_TRUNCATED",
    "STALE_HEAD_AFTER_RESTART",
    "BROKEN_PREV_POINTER",
    "STATEMENT_REBOUND_IN_DURABLE_RECORD",
    "EPOCH_REBOUND_IN_DURABLE_RECORD",
    "DUPLICATE_CONFLICTING_OUTCOME_RECEIPT",
)

EXPECTED = {
    "CLEAN": "PROVEN",
    "JOURNAL_WRITTEN_HEAD_NOT_UPDATED": "PROVEN",
    "HEAD_UPDATED_RECORD_TRUNCATED": "UNKNOWN",
    "STALE_HEAD_AFTER_RESTART": "PROVEN",
    "BROKEN_PREV_POINTER": "UNKNOWN",
    "STATEMENT_REBOUND_IN_DURABLE_RECORD": "UNKNOWN",
    "EPOCH_REBOUND_IN_DURABLE_RECORD": "UNKNOWN",
    "DUPLICATE_CONFLICTING_OUTCOME_RECEIPT": "CONFLICT",
}

HEAD_SPECIFIC = {
    "JOURNAL_WRITTEN_HEAD_NOT_UPDATED",
    "STALE_HEAD_AFTER_RESTART",
}

K_REQUEST = 1
K_AUTHORIZED = 2
K_EXECUTED = 3
K_OUTCOME_OK = 4
K_OUTCOME_FAIL = 5


def fault_applicable(system: str, fault: str) -> bool:
    if system == "software_scan_repair" and fault in HEAD_SPECIFIC:
        return False
    return True


def _payload(
    tx_id: int,
    kind: int,
    statement_id: int,
    proof_id: int,
    epoch: int,
    prev_offset: int,
    receipt_id: int,
) -> bytes:
    return BASE.pack(
        tx_id,
        kind,
        1,
        0,
        0,
        statement_id,
        proof_id,
        epoch,
        prev_offset,
        receipt_id,
    )


def pack_record(
    tx_id: int,
    kind: int,
    *,
    statement_id: int = ACTION_STATEMENT,
    proof_id: int,
    epoch: int = CURRENT_EPOCH,
    prev_offset: int = NO_OFFSET,
    receipt_id: int,
) -> bytes:
    payload = _payload(
        tx_id,
        kind,
        statement_id,
        proof_id,
        epoch,
        prev_offset,
        receipt_id,
    )
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    return payload + struct.pack(">II", crc, 0)


def unpack_record(raw: bytes) -> dict:
    if len(raw) != RECORD.size:
        raise ValueError("torn_record")
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
        crc,
        reserved2,
    ) = RECORD.unpack(raw)
    payload = BASE.pack(
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
    )
    return {
        "tx_id": tx_id,
        "kind": kind,
        "statement_id": statement_id,
        "proof_id": proof_id,
        "epoch": epoch,
        "prev_offset": prev_offset,
        "receipt_id": receipt_id,
        "crc_valid": (zlib.crc32(payload) & 0xFFFFFFFF) == crc,
        "reserved2": reserved2,
    }


def semantic_valid(record: dict) -> bool:
    # Strong conventional indexed software deliberately checks the same binding
    # fields as the ProofBit receipt chain. The distinction is architectural,
    # not an artificially weakened application-policy control.
    return (
        record["crc_valid"]
        and record["tx_id"] == 0
        and record["statement_id"] == ACTION_STATEMENT
        and record["epoch"] == CURRENT_EPOCH
        and record["proof_id"] != 0
        and record["receipt_id"] != 0
    )


def _paths(root: Path) -> tuple[Path, Path]:
    return root / "journal.bin", root / "heads.bin"


def _write_head(path: Path, offset: int) -> None:
    with path.open("r+b", buffering=0) as handle:
        handle.seek(0)
        handle.write(HEAD.pack(offset))
        os.fsync(handle.fileno())


def _read_head(path: Path) -> int:
    raw = path.read_bytes()
    if len(raw) != HEAD.size:
        return NO_OFFSET
    return HEAD.unpack(raw)[0]


def _prepare_case(root: Path, system: str, fault: str) -> dict:
    journal_path, head_path = _paths(root)
    journal_path.write_bytes(b"")
    if system == "software_scan_repair":
        head_path.write_bytes(b"")
    else:
        head_path.write_bytes(HEAD.pack(NO_OFFSET))

    offsets: list[int] = []
    receipt = 1

    def append(
        kind: int,
        *,
        update_head: bool = True,
        statement_id: int = ACTION_STATEMENT,
        epoch: int = CURRENT_EPOCH,
        prev_override: int | None = None,
        truncate_to: int | None = None,
    ) -> int:
        nonlocal receipt
        prev = offsets[-1] if offsets else NO_OFFSET
        if prev_override is not None:
            prev = prev_override
        offset = journal_path.stat().st_size
        raw = pack_record(
            0,
            kind,
            statement_id=statement_id,
            proof_id=receipt,
            epoch=epoch,
            prev_offset=prev,
            receipt_id=receipt,
        )
        with journal_path.open("ab", buffering=0) as handle:
            handle.write(raw if truncate_to is None else raw[:truncate_to])
            os.fsync(handle.fileno())
        if truncate_to is None:
            offsets.append(offset)
        if system != "software_scan_repair" and update_head:
            _write_head(head_path, offset)
        receipt += 1
        return offset

    append(K_REQUEST)
    append(K_AUTHORIZED)
    executed_offset = append(K_EXECUTED)

    if fault == "CLEAN":
        append(K_OUTCOME_OK)
    elif fault == "JOURNAL_WRITTEN_HEAD_NOT_UPDATED":
        append(K_OUTCOME_OK, update_head=False)
    elif fault == "HEAD_UPDATED_RECORD_TRUNCATED":
        # The head may point at bytes that were only partially persisted.
        partial_offset = journal_path.stat().st_size
        append(K_OUTCOME_OK, update_head=False, truncate_to=RECORD.size // 2)
        if system != "software_scan_repair":
            _write_head(head_path, partial_offset)
    elif fault == "STALE_HEAD_AFTER_RESTART":
        append(K_OUTCOME_OK)
        if system != "software_scan_repair":
            _write_head(head_path, executed_offset)
    elif fault == "BROKEN_PREV_POINTER":
        append(K_OUTCOME_OK, prev_override=7)
    elif fault == "STATEMENT_REBOUND_IN_DURABLE_RECORD":
        # CRC is recomputed over the rebound statement so this is a semantic
        # binding fault, not merely a checksum fault.
        append(K_OUTCOME_OK, statement_id=WRONG_STATEMENT)
    elif fault == "EPOCH_REBOUND_IN_DURABLE_RECORD":
        # Likewise: structurally valid record, wrong trust epoch.
        append(K_OUTCOME_OK, epoch=CURRENT_EPOCH + 1)
    elif fault == "DUPLICATE_CONFLICTING_OUTCOME_RECEIPT":
        append(K_OUTCOME_OK)
        append(K_OUTCOME_FAIL)
    else:
        raise ValueError(f"unknown fault: {fault}")

    return {
        "fault": fault,
        "expected_state": EXPECTED[fault],
        "applicable": fault_applicable(system, fault),
    }


def _scan_recover(journal_path: Path) -> dict:
    records: list[tuple[int, dict]] = []
    inspected = 0
    detected_corruption = 0
    previous_accepted_offset = NO_OFFSET
    last_valid_offset = NO_OFFSET

    with journal_path.open("rb", buffering=0) as handle:
        offset = 0
        while True:
            raw = handle.read(RECORD.size)
            if not raw:
                break
            inspected += 1
            if len(raw) != RECORD.size:
                detected_corruption += 1
                break
            record = unpack_record(raw)
            if not semantic_valid(record):
                detected_corruption += 1
                offset += RECORD.size
                continue
            expected_prev = previous_accepted_offset
            if record["prev_offset"] != expected_prev:
                detected_corruption += 1
                offset += RECORD.size
                continue
            records.append((offset, record))
            last_valid_offset = offset
            previous_accepted_offset = offset
            offset += RECORD.size

    return {
        "records": records,
        "records_inspected": inspected,
        "detected_corruption": detected_corruption,
        "last_valid_offset": last_valid_offset,
    }


def _state(records: list[tuple[int, dict]]) -> str:
    kinds = [record["kind"] for _, record in records]
    has_exec = K_EXECUTED in kinds
    has_ok = K_OUTCOME_OK in kinds
    has_fail = K_OUTCOME_FAIL in kinds
    if has_ok and has_fail:
        return "CONFLICT"
    if has_exec and (has_ok or has_fail):
        return "PROVEN"
    return "UNKNOWN"


def _indexed_chain(journal_path: Path, head_path: Path) -> dict:
    size = journal_path.stat().st_size
    head = _read_head(head_path)
    inspected = 0
    detected = 0
    records: list[tuple[int, dict]] = []
    seen: set[int] = set()
    offset = head

    if head == NO_OFFSET:
        return {
            "valid": False,
            "records": [],
            "records_inspected": 0,
            "detected_corruption": 1,
            "reason": "missing_head",
        }

    # A complete durable record beyond the head proves that the index is stale.
    if head + RECORD.size < size:
        return {
            "valid": False,
            "records": [],
            "records_inspected": 0,
            "detected_corruption": 1,
            "reason": "tail_beyond_head",
        }
    if head + RECORD.size > size:
        return {
            "valid": False,
            "records": [],
            "records_inspected": 0,
            "detected_corruption": 1,
            "reason": "head_points_to_partial_record",
        }

    with journal_path.open("rb", buffering=0) as handle:
        while offset != NO_OFFSET:
            if offset in seen or offset % RECORD.size != 0 or offset + RECORD.size > size:
                detected += 1
                return {
                    "valid": False,
                    "records": records,
                    "records_inspected": inspected,
                    "detected_corruption": detected,
                    "reason": "invalid_pointer",
                }
            seen.add(offset)
            handle.seek(offset)
            raw = handle.read(RECORD.size)
            inspected += 1
            if len(raw) != RECORD.size:
                detected += 1
                return {
                    "valid": False,
                    "records": records,
                    "records_inspected": inspected,
                    "detected_corruption": detected,
                    "reason": "torn_record",
                }
            record = unpack_record(raw)
            if not semantic_valid(record):
                detected += 1
                return {
                    "valid": False,
                    "records": records,
                    "records_inspected": inspected,
                    "detected_corruption": detected,
                    "reason": "binding_or_crc_failure",
                }
            records.append((offset, record))
            next_offset = record["prev_offset"]
            if next_offset != NO_OFFSET and next_offset >= offset:
                detected += 1
                return {
                    "valid": False,
                    "records": records,
                    "records_inspected": inspected,
                    "detected_corruption": detected,
                    "reason": "non_backward_pointer",
                }
            offset = next_offset

    records.reverse()
    # Verify forward continuity after reversing.
    previous = NO_OFFSET
    for record_offset, record in records:
        if record["prev_offset"] != previous:
            return {
                "valid": False,
                "records": records,
                "records_inspected": inspected,
                "detected_corruption": detected + 1,
                "reason": "broken_chain_continuity",
            }
        previous = record_offset

    return {
        "valid": True,
        "records": records,
        "records_inspected": inspected,
        "detected_corruption": detected,
        "reason": "ok",
    }


def _recover_case(root: Path, system: str, fault: str) -> dict:
    journal_path, head_path = _paths(root)
    started = time.perf_counter_ns()
    repair_scanned = 0
    repair_writes = 0
    detected = 0

    if system == "software_scan_repair":
        scan = _scan_recover(journal_path)
        records = scan["records"]
        inspected = scan["records_inspected"]
        detected = scan["detected_corruption"]
    else:
        chain = _indexed_chain(journal_path, head_path)
        inspected = chain["records_inspected"]
        detected = chain["detected_corruption"]
        if chain["valid"]:
            records = chain["records"]
        else:
            scan = _scan_recover(journal_path)
            records = scan["records"]
            repair_scanned = scan["records_inspected"]
            inspected += scan["records_inspected"]
            detected += scan["detected_corruption"]
            safe_head = scan["last_valid_offset"]
            if safe_head != _read_head(head_path):
                _write_head(head_path, safe_head)
                repair_writes += 1

    recovered = _state(records)
    elapsed_ns = time.perf_counter_ns() - started
    expected = EXPECTED[fault]
    applicable = fault_applicable(system, fault)

    # A silent false reconstruction is a confident PROVEN result where the
    # corruption oracle requires UNKNOWN or CONFLICT.
    silent_false = int(recovered == "PROVEN" and expected != "PROVEN")
    conflict_detected = int(recovered == "CONFLICT")
    return {
        "fault": fault,
        "applicable": applicable,
        "expected_state": expected,
        "recovered_state": recovered,
        "oracle_correct": recovered == expected,
        "silent_false_reconstruction": silent_false,
        "detected_corruption": detected,
        "detected_conflict": conflict_detected,
        "records_inspected": inspected,
        "repair_scan_records": repair_scanned,
        "repair_writes": repair_writes,
        "recovery_elapsed_ns": elapsed_ns,
        "journal_bytes": journal_path.stat().st_size,
        "index_bytes": head_path.stat().st_size,
    }


def _recover_round_worker(root: str, system: str, result_path: str) -> None:
    base = Path(root)
    results = []
    for fault in FAULTS:
        results.append(_recover_case(base / fault, system, fault))
    Path(result_path).write_text(json.dumps(results, sort_keys=True))


def _run_round(system: str) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"proofbit-tc05-{system}-") as tmp:
        root = Path(tmp)
        for fault in FAULTS:
            case = root / fault
            case.mkdir()
            _prepare_case(case, system, fault)

        result_path = root / "result.json"
        ctx = mp.get_context("fork")
        started = time.perf_counter_ns()
        proc = ctx.Process(
            target=_recover_round_worker,
            args=(str(root), system, str(result_path)),
        )
        proc.start()
        proc.join()
        restart_wall_ns = time.perf_counter_ns() - started
        if proc.exitcode != 0:
            raise RuntimeError(f"TC05 recovery worker failed: {system} exit={proc.exitcode}")
        cases = json.loads(result_path.read_text())

    applicable = [case for case in cases if case["applicable"]]
    return {
        "system": system,
        "cases": cases,
        "applicable_cases": len(applicable),
        "oracle_accuracy": (
            sum(case["oracle_correct"] for case in applicable) / len(applicable)
            if applicable
            else 0.0
        ),
        "silent_false_reconstruction": sum(
            case["silent_false_reconstruction"] for case in applicable
        ),
        "detected_corruption": sum(case["detected_corruption"] for case in applicable),
        "detected_conflict": sum(case["detected_conflict"] for case in applicable),
        "unknown_recoveries": sum(
            case["recovered_state"] == "UNKNOWN" for case in applicable
        ),
        "conflict_recoveries": sum(
            case["recovered_state"] == "CONFLICT" for case in applicable
        ),
        "records_inspected": sum(case["records_inspected"] for case in applicable),
        "repair_scan_records": sum(case["repair_scan_records"] for case in applicable),
        "repair_writes": sum(case["repair_writes"] for case in applicable),
        "recovery_elapsed_ns": sum(case["recovery_elapsed_ns"] for case in applicable),
        "restart_wall_ns": restart_wall_ns,
        "persisted_bytes": sum(
            case["journal_bytes"] + case["index_bytes"] for case in applicable
        ),
    }


def _aggregate(system: str, rounds: list[dict]) -> dict:
    first = rounds[0]
    numeric = (
        "records_inspected",
        "repair_scan_records",
        "repair_writes",
        "recovery_elapsed_ns",
        "restart_wall_ns",
        "persisted_bytes",
    )
    return {
        "system": system,
        "rounds": len(rounds),
        "fault_coverage": first["applicable_cases"] / len(FAULTS),
        "applicable_cases_per_round": first["applicable_cases"],
        "oracle_accuracy": min(row["oracle_accuracy"] for row in rounds),
        "silent_false_reconstruction": sum(
            row["silent_false_reconstruction"] for row in rounds
        ),
        "detected_corruption": sum(row["detected_corruption"] for row in rounds),
        "detected_conflict": sum(row["detected_conflict"] for row in rounds),
        "median": {
            key: statistics.median(row[key] for row in rounds) for key in numeric
        },
        "raw_recovery_elapsed_ns": [row["recovery_elapsed_ns"] for row in rounds],
        "case_results": first["cases"],
    }


def run_benchmark(rounds: int = 11) -> dict:
    if rounds <= 0:
        raise ValueError("rounds must be positive")

    per_system: dict[str, list[dict]] = {name: [] for name in SYSTEMS}
    orders: list[list[str]] = []
    for round_index in range(rounds):
        shift = round_index % len(SYSTEMS)
        order = SYSTEMS[shift:] + SYSTEMS[:shift]
        orders.append(list(order))
        for system in order:
            per_system[system].append(_run_round(system))

    systems = {
        system: _aggregate(system, per_system[system]) for system in SYSTEMS
    }
    indexed = systems["software_indexed_integrity"]
    proof = systems["proofbit_receipts"]

    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "rounds": rounds,
        "faults": list(FAULTS),
        "expected_states": EXPECTED,
        "measurement_orders": orders,
        "record_bytes": RECORD.size,
        "head_index_bytes": HEAD.size,
        "systems": systems,
        "primary_comparison": "software_indexed_integrity vs proofbit_receipts",
        "primary_ratios": {
            "proofbit_vs_indexed_recovery_elapsed": (
                proof["median"]["recovery_elapsed_ns"]
                / indexed["median"]["recovery_elapsed_ns"]
            ),
            "proofbit_vs_indexed_persisted_bytes": (
                proof["median"]["persisted_bytes"]
                / indexed["median"]["persisted_bytes"]
            ),
            "proofbit_vs_indexed_repair_scan_records": (
                proof["median"]["repair_scan_records"]
                / indexed["median"]["repair_scan_records"]
                if indexed["median"]["repair_scan_records"]
                else 0.0
            ),
        },
        "no_single_winner_score": True,
        "fairness": (
            "software_indexed_integrity and proofbit_receipts use the same 56-byte "
            "CRC-protected record, 8-byte head, statement/epoch/identity checks, "
            "chain validation, scan fallback, and safe-head repair policy"
        ),
        "caveats": [
            "TC05 injects deterministic file-level corruption after durable writes; it is not a physical media fault test",
            "CRC32 is an integrity detector for the benchmark, not a cryptographic authenticity mechanism",
            "semantic rebound faults deliberately recompute CRC so statement/epoch checks are exercised independently of checksums",
            "software_indexed_integrity is intentionally a strong conventional anti-strawman control",
            "no silicon, energy, network, novelty, patentability, or universal performance claim",
        ],
    }


def _print_human(report: dict) -> None:
    print(f"{report['benchmark_id']} {report['protocol']}")
    print(
        "system                        coverage accuracy silent_false "
        "repair_scan repair_writes recovery_ms"
    )
    for name in SYSTEMS:
        system = report["systems"][name]
        med = system["median"]
        print(
            f"{name:29s} {system['fault_coverage']:8.3f} "
            f"{system['oracle_accuracy']:8.3f} "
            f"{system['silent_false_reconstruction']:12d} "
            f"{med['repair_scan_records']:11.0f} "
            f"{med['repair_writes']:13.0f} "
            f"{med['recovery_elapsed_ns']/1_000_000:10.3f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=11)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_benchmark(args.rounds)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report)


if __name__ == "__main__":
    main()
