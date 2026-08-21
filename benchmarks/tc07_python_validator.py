from __future__ import annotations
import argparse
from pathlib import Path
import struct

MAGIC = 0x50424637
KNOWN_MASK = 0x3F
CURRENT_VERSION = 5
CURRENT_MASK = 0x3F
CURRENT_DIGEST = 0xC43CD04DF228379F
STATEMENT = 0xFEDCBA9876543210
AUTHORITY = 0xA17E0007
EPOCH = 7
TOKEN = struct.Struct('>IHHIQQIIQQB3x')
POLICY = struct.Struct('>HHIQ')


def parse_policy(hex_text: str) -> tuple[int, int, int]:
    raw = bytes.fromhex(hex_text)
    if len(raw) != POLICY.size:
        raise ValueError('policy length')
    version, reserved, mask, digest = POLICY.unpack(raw)
    if reserved != 0:
        raise ValueError('policy reserved')
    return version, mask, digest


def validate(raw: bytes, mode: str, policy_hex: str | None) -> bool:
    if len(raw) != TOKEN.size:
        return False
    try:
        magic, version, flags, mask, digest, statement, authority, epoch, replay, provenance, outcome = TOKEN.unpack(raw)
    except struct.error:
        return False
    if mode == 'manual':
        policy_version, policy_mask, policy_digest = CURRENT_VERSION, CURRENT_MASK, CURRENT_DIGEST
    else:
        if not policy_hex:
            return False
        try:
            policy_version, policy_mask, policy_digest = parse_policy(policy_hex)
        except ValueError:
            return False
    if magic != MAGIC or flags != 0:
        return False
    if any(raw[53:56]):
        return False
    if version != policy_version or mask != policy_mask or (mask & ~KNOWN_MASK):
        return False
    if digest != policy_digest:
        return False
    if statement != STATEMENT or authority != AUTHORITY or epoch != EPOCH:
        return False
    if mask & 0x08 and replay == 0:
        return False
    if mask & 0x10 and provenance == 0:
        return False
    if mask & 0x20 and outcome != 1:
        return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=('manual','canonical','proofbit'), required=True)
    ap.add_argument('--policy-hex')
    ap.add_argument('input')
    args = ap.parse_args()
    out=[]
    for line in Path(args.input).read_text().splitlines():
        if not line:
            continue
        name, expected, raw_hex = line.split('\t')
        accepted = validate(bytes.fromhex(raw_hex), args.mode, args.policy_hex)
        out.append(f'{name}\t{int(accepted)}')
    print('\n'.join(out))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
