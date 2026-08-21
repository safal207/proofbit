from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import pwd
import shutil
import statistics
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

BENCHMARK_ID = "PB-TRUST-COMPOSE-10"
VERSION = "0.1"
PROTOCOL = "PB-TC10/v0.1 resource-privilege-bypass"
MAGIC = 0x5042463A
VERSION_ID = 5
MASK = 0x1F
STATEMENT = 0xA0A0A0A0A0A0A001
AUTHORITY = 0xA17E0007
EPOCH = 7
TOKEN = struct.Struct(">IHHIQQIIQQB3x")
SYSTEMS = (
    "application_owned_resource",
    "software_os_reference_monitor",
    "proofbit_os_boundary",
)
STRONG_SYSTEMS = SYSTEMS[1:]
ATTACKS = (
    "DIRECT_OPEN",
    "SHELL_REDIRECT",
    "SYMLINK_ALIAS",
    "RENAME_REPLACE",
    "INHERITED_FD",
    "STALE_FD_AFTER_CHMOD",
)


def digest() -> int:
    return int.from_bytes(hashlib.sha256(b"PB-TC10|v5|mask=31").digest()[:8], "big")


def pack_token(replay: int) -> bytes:
    return TOKEN.pack(
        MAGIC,
        VERSION_ID,
        0,
        MASK,
        digest(),
        STATEMENT,
        AUTHORITY,
        EPOCH,
        replay,
        22,
        0,
    )


def app_validate(raw: bytes) -> bool:
    if len(raw) != TOKEN.size:
        return False
    try:
        magic, version, flags, mask, dig, statement, authority, epoch, replay, provenance, outcome = TOKEN.unpack(raw)
    except struct.error:
        return False
    return bool(
        magic == MAGIC
        and version == VERSION_ID
        and flags == 0
        and mask == MASK
        and dig == digest()
        and statement == STATEMENT
        and authority == AUTHORITY
        and epoch == EPOCH
        and replay != 0
        and provenance != 0
        and not any(raw[53:56])
    )


def require_privilege_fixture() -> tuple[int, int]:
    if shutil.which("sudo") is None:
        raise RuntimeError("TC10 requires sudo on the ephemeral benchmark runner")
    subprocess.run(["sudo", "-n", "true"], check=True, stdout=subprocess.DEVNULL)
    account = pwd.getpwnam("nobody")
    subprocess.run(
        ["sudo", "-n", "-u", "nobody", "true"],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return account.pw_uid, account.pw_gid


def sudo(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["sudo", "-n", *args],
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def prepare_resource(base: Path, system: str, label: str, protected_uid: int, protected_gid: int) -> tuple[Path, Path]:
    directory = base / label
    directory.mkdir(mode=0o700)
    resource = directory / "protected.log"
    resource.write_bytes(b"")
    os.chmod(resource, 0o600)
    if system in STRONG_SYSTEMS:
        sudo("chown", "-R", f"{protected_uid}:{protected_gid}", str(directory))
        sudo("chmod", "700", str(directory))
        sudo("chmod", "600", str(resource))
    return directory, resource


def hostile_script(root: Path) -> str:
    return str(root / "benchmarks" / "tc10_hostile_writer.py")


def run_child(cmd: list[str], *, pass_fds: tuple[int, ...] = ()) -> bool:
    result = subprocess.run(
        cmd,
        pass_fds=pass_fds,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def attack(system: str, attack_name: str, root: Path, base: Path, protected_uid: int, protected_gid: int) -> bool:
    _, resource = prepare_resource(base, system, attack_name.lower(), protected_uid, protected_gid)
    script = hostile_script(root)
    if attack_name == "DIRECT_OPEN":
        return run_child([sys.executable, script, "--mode", "direct", "--path", str(resource)])
    if attack_name == "SHELL_REDIRECT":
        return run_child([sys.executable, script, "--mode", "shell", "--path", str(resource)])
    if attack_name == "SYMLINK_ALIAS":
        alias_dir = base / f"alias-{attack_name.lower()}"
        alias_dir.mkdir(mode=0o700)
        alias = alias_dir / "alias.log"
        return run_child(
            [
                sys.executable,
                script,
                "--mode",
                "symlink",
                "--path",
                str(resource),
                "--alias",
                str(alias),
            ]
        )
    if attack_name == "RENAME_REPLACE":
        return run_child([sys.executable, script, "--mode", "rename_replace", "--path", str(resource)])
    if attack_name in ("INHERITED_FD", "STALE_FD_AFTER_CHMOD"):
        try:
            fd = os.open(resource, os.O_WRONLY | os.O_APPEND)
        except OSError:
            return False
        try:
            if attack_name == "STALE_FD_AFTER_CHMOD":
                os.chmod(resource, 0)
            return run_child(
                [sys.executable, script, "--mode", "fd", "--fd", str(fd)],
                pass_fds=(fd,),
            )
        finally:
            try:
                if attack_name == "STALE_FD_AFTER_CHMOD":
                    os.chmod(resource, 0o600)
            except OSError:
                pass
            os.close(fd)
    raise ValueError(attack_name)


def same_privilege_compromise(system: str, base: Path, protected_uid: int, protected_gid: int) -> bool:
    _, resource = prepare_resource(base, system, "same-privilege", protected_uid, protected_gid)
    if system in STRONG_SYSTEMS:
        result = subprocess.run(
            [
                "sudo",
                "-n",
                "-u",
                "nobody",
                "--",
                "/bin/sh",
                "-c",
                'printf "COMPROMISED\\n" >> "$1"',
                "sh",
                str(resource),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        result = subprocess.run(
            ["/bin/sh", "-c", 'printf "COMPROMISED\\n" >> "$1"', "sh", str(resource)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    return result.returncode == 0


def send(proc: subprocess.Popen, message: dict) -> dict:
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    if not line:
        stderr = proc.stderr.read() if proc.stderr is not None else ""
        raise RuntimeError(f"broker exited unexpectedly: {stderr}")
    return json.loads(line)


def start_broker(system: str, root: Path, resource: Path) -> subprocess.Popen:
    script = str(root / "benchmarks" / "tc10_privileged_broker.py")
    base = [sys.executable, script, "--mode", system, "--resource", str(resource)]
    if system in STRONG_SYSTEMS:
        cmd = [
            "sudo",
            "-n",
            "-u",
            "nobody",
            "--",
            "env",
            f"PYTHONPATH={root}",
            *base,
        ]
    else:
        cmd = base
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=root,
    )


def stop_broker(proc: subprocess.Popen) -> None:
    try:
        if proc.poll() is None:
            send(proc, {"op": "shutdown"})
    except Exception:
        pass
    if proc.poll() is None:
        proc.wait(timeout=5)
    for stream in (proc.stdin, proc.stdout, proc.stderr):
        if stream is not None:
            stream.close()


def valid_path(system: str, root: Path, base: Path, count: int, protected_uid: int, protected_gid: int) -> dict:
    _, resource = prepare_resource(base, system, "valid", protected_uid, protected_gid)
    proc = start_broker(system, root, resource)
    try:
        start = time.perf_counter_ns()
        accepted = 0
        broker_uid = None
        for i in range(count):
            raw = pack_token(100_000 + i)
            if system == "application_owned_resource" and not app_validate(raw):
                raise AssertionError("application validator rejected frozen valid token")
            result = send(
                proc,
                {
                    "op": "execute",
                    "token_hex": raw.hex(),
                    "requested_statement": hex(STATEMENT),
                    "request_id": f"valid-{i}",
                },
            )
            if not (result["effect"] and result["outcome_proven"]):
                raise AssertionError(f"{system}: valid effect rejected")
            accepted += 1
        elapsed = time.perf_counter_ns() - start
        broker_uid = send(proc, {"op": "stats"})["uid"]
    finally:
        stop_broker(proc)
    return {
        "accepted": accepted,
        "opportunities": count,
        "availability": accepted / count,
        "elapsed_ns": elapsed,
        "valid_effects_per_sec": count / (elapsed / 1e9),
        "broker_uid": broker_uid,
    }


def run_once(system: str, root: Path, round_base: Path, valid_count: int, protected_uid: int, protected_gid: int) -> dict:
    system_base = round_base / system
    system_base.mkdir(mode=0o755)
    attack_rows = []
    for name in ATTACKS:
        succeeded = attack(system, name, root, system_base, protected_uid, protected_gid)
        attack_rows.append({"name": name, "hostile_write_succeeded": succeeded})
    compromise = same_privilege_compromise(system, system_base, protected_uid, protected_gid)
    perf = valid_path(system, root, system_base, valid_count, protected_uid, protected_gid)
    unsafe = sum(int(x["hostile_write_succeeded"]) for x in attack_rows)
    return {
        "attacks": attack_rows,
        "unsafe_resource_writes": unsafe,
        "bypasses_blocked": len(ATTACKS) - unsafe,
        "bypass_oracle_accuracy": (len(ATTACKS) - unsafe) / len(ATTACKS),
        "same_privilege_compromise_succeeds": compromise,
        "valid_path": perf,
    }


def tcb_surface(protected_uid: int) -> dict:
    return {
        "application_owned_resource": {
            "mandatory_os_uid_boundary": 0,
            "resource_owner": "application_uid",
            "writable_handle_exposed_to_application": True,
            "mandatory_effect_validator": 0,
        },
        "software_os_reference_monitor": {
            "mandatory_os_uid_boundary": 1,
            "resource_owner_uid": protected_uid,
            "writable_handle_exposed_to_application": False,
            "mandatory_effect_validator": 1,
        },
        "proofbit_os_boundary": {
            "mandatory_os_uid_boundary": 1,
            "resource_owner_uid": protected_uid,
            "writable_handle_exposed_to_application": False,
            "mandatory_effect_validator": 1,
        },
    }


def run(rounds: int, valid_count: int) -> dict:
    protected_uid, protected_gid = require_privilege_fixture()
    root = Path(__file__).resolve().parents[1]
    permutations = (
        SYSTEMS,
        (SYSTEMS[1], SYSTEMS[2], SYSTEMS[0]),
        (SYSTEMS[2], SYSTEMS[0], SYSTEMS[1]),
    )
    raw = {system: [] for system in SYSTEMS}
    orders: list[list[str]] = []
    base = Path(tempfile.mkdtemp(prefix="proofbit-tc10-"))
    os.chmod(base, 0o755)
    try:
        for round_index in range(rounds):
            order = permutations[round_index % len(permutations)]
            orders.append(list(order))
            round_base = base / f"round-{round_index}"
            round_base.mkdir(mode=0o755)
            for system in order:
                raw[system].append(
                    run_once(
                        system,
                        root,
                        round_base,
                        valid_count,
                        protected_uid,
                        protected_gid,
                    )
                )
    finally:
        sudo("rm", "-rf", str(base), check=False)

    results = {}
    runtime = {}
    for system, rows in raw.items():
        first = rows[0]
        attack_signatures = [
            tuple(x["hostile_write_succeeded"] for x in row["attacks"])
            for row in rows
        ]
        results[system] = {
            "unsafe_resource_writes_per_round": first["unsafe_resource_writes"],
            "bypasses_blocked_per_round": first["bypasses_blocked"],
            "bypass_oracle_accuracy": first["bypass_oracle_accuracy"],
            "attack_results": first["attacks"],
            "attack_results_consistent_across_rounds": len(set(attack_signatures)) == 1,
            "same_privilege_compromise_success_rate": sum(
                int(row["same_privilege_compromise_succeeds"]) for row in rows
            )
            / len(rows),
            "valid_path_availability": first["valid_path"]["availability"],
            "broker_uid": first["valid_path"]["broker_uid"],
        }
        rates = [row["valid_path"]["valid_effects_per_sec"] for row in rows]
        runtime[system] = {
            "median_valid_effects_per_sec": statistics.median(rates),
            "raw_valid_effects_per_sec": rates,
        }

    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "rounds": rounds,
        "valid_requests_per_system_per_round": valid_count,
        "hostile_uid": os.getuid(),
        "hostile_user": getpass.getuser(),
        "protected_uid": protected_uid,
        "protected_user": "nobody",
        "attacks": list(ATTACKS),
        "results": results,
        "runtime": runtime,
        "tcb_surface": tcb_surface(protected_uid),
        "measurement_orders": orders,
        "primary_anti_strawman": "software_os_reference_monitor",
        "same_privilege_probe_scored": False,
        "same_privilege_boundary": "If hostile code obtains the protected resource owner's UID or root, both software_os_reference_monitor and software ProofBit can be bypassed by direct resource writes. This is measured as an explicit unscored compromise probe.",
        "stale_fd_rule": "chmod/path permission changes do not revoke an already-open writable file descriptor; avoiding handle leakage is part of the protected-resource topology.",
        "no_single_winner_score": True,
        "claim_boundary": "Real POSIX UID/DAC separation, real subprocesses, real file writes, and a same-privilege compromise probe on one ephemeral Linux runner. The hosted runner orchestrator itself has passwordless sudo, but the scored hostile subprocess is intentionally unprivileged and never invokes sudo. No kernel exploit, namespace/container isolation, Linux capability(7) proof, cryptography, hardware, energy, novelty, patentability, or universal-superiority claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=11)
    parser.add_argument("--valid-requests", type=int, default=250)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run(args.rounds, args.valid_requests)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for system in SYSTEMS:
            row = result["results"][system]
            speed = result["runtime"][system]["median_valid_effects_per_sec"]
            print(
                f"{system}: blocked={row['bypasses_blocked_per_round']}/{len(ATTACKS)} "
                f"unsafe={row['unsafe_resource_writes_per_round']} speed={speed:.1f}/s"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
