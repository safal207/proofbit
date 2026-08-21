from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.model import Evidence, ProofProcessor

MAGIC = 0x5042463A
VERSION = 5
MASK = 0x1F
STATEMENT = 0xA0A0A0A0A0A0A001
AUTHORITY = 0xA17E0007
EPOCH = 7
TOKEN = struct.Struct(">IHHIQQIIQQB3x")


def digest() -> int:
    return int.from_bytes(hashlib.sha256(b"PB-TC10|v5|mask=31").digest()[:8], "big")


def parse_token(raw: bytes):
    if len(raw) != TOKEN.size:
        return None
    try:
        magic, version, flags, mask, dig, statement, authority, epoch, replay, provenance, outcome = TOKEN.unpack(raw)
    except struct.error:
        return None
    if any(raw[53:56]):
        return None
    return {
        "magic": magic,
        "version": version,
        "flags": flags,
        "mask": mask,
        "digest": dig,
        "statement": statement,
        "authority": authority,
        "epoch": epoch,
        "replay": replay,
        "provenance": provenance,
        "outcome": outcome,
    }


def static_valid(x, requested_statement: int) -> bool:
    return bool(
        x
        and x["magic"] == MAGIC
        and x["version"] == VERSION
        and x["flags"] == 0
        and x["mask"] == MASK
        and x["digest"] == digest()
        and x["statement"] == requested_statement
        and x["provenance"] != 0
        and x["replay"] != 0
    )


class Broker:
    def __init__(self, mode: str, resource: Path) -> None:
        self.mode = mode
        self.resource = resource
        self.current_epoch = EPOCH
        self.consumed: set[int] = set()
        self.effects = 0
        self.proof = ProofProcessor(authority=AUTHORITY, epoch=EPOCH)
        self.fp = resource.open("a", encoding="utf-8", buffering=1)

    def authorize_software(self, x, requested: int) -> bool:
        if not static_valid(x, requested):
            return False
        if x["authority"] != AUTHORITY or x["epoch"] != self.current_epoch:
            return False
        if x["replay"] in self.consumed:
            return False
        self.consumed.add(x["replay"])
        return True

    def authorize_proofbit(self, x, requested: int) -> bool:
        if not static_valid(x, requested):
            return False
        self.proof.epoch = self.current_epoch
        statement = f"effect:{x['statement']:016x}"
        evidence = Evidence(
            statement=statement,
            value=True,
            proof_id=x["replay"],
            authority=x["authority"],
            epoch=x["epoch"],
            provenance=x["provenance"],
        )
        self.proof.store_evidence(0, evidence)
        return self.proof.guarded_execute(
            0,
            expected_statement=f"effect:{requested:016x}",
            single_use=True,
        )

    def execute(self, message: dict) -> dict:
        raw = bytes.fromhex(message["token_hex"])
        requested = int(message["requested_statement"], 16)
        request_id = str(message["request_id"])
        x = parse_token(raw)

        if self.mode == "application_owned_resource":
            authorized = True
        elif self.mode == "software_os_reference_monitor":
            authorized = self.authorize_software(x, requested)
        elif self.mode == "proofbit_os_boundary":
            authorized = self.authorize_proofbit(x, requested)
        else:
            raise ValueError(self.mode)

        effect = False
        if authorized:
            self.fp.write(f"EFFECT\t{request_id}\n")
            self.fp.flush()
            self.effects += 1
            effect = True
        return {
            "authorized": authorized,
            "effect": effect,
            "outcome_proven": effect,
            "effects": self.effects,
        }

    def handle(self, message: dict) -> dict:
        op = message.get("op")
        if op == "execute":
            return self.execute(message)
        if op == "stats":
            return {"effects": self.effects, "uid": __import__("os").getuid()}
        if op == "shutdown":
            return {"shutdown": True}
        raise ValueError(op)

    def close(self) -> None:
        self.fp.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--resource", required=True)
    args = parser.parse_args()
    broker = Broker(args.mode, Path(args.resource))
    try:
        for line in sys.stdin:
            if not line.strip():
                continue
            message = json.loads(line)
            result = broker.handle(message)
            print(json.dumps(result, separators=(",", ":")), flush=True)
            if message.get("op") == "shutdown":
                break
    finally:
        broker.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
