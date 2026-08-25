from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PAYLOAD = b"HOSTILE\n"


def direct(path: Path) -> None:
    with path.open("ab", buffering=0) as fp:
        fp.write(PAYLOAD)


def shell_redirect(path: Path) -> None:
    subprocess.run(
        ["/bin/sh", "-c", 'printf "HOSTILE\\n" >> "$1"', "sh", str(path)],
        check=True,
    )


def symlink_alias(path: Path, alias: Path) -> None:
    try:
        alias.unlink()
    except FileNotFoundError:
        pass
    alias.symlink_to(path)
    direct(alias)


def rename_replace(path: Path) -> None:
    backup = path.with_suffix(".bak")
    try:
        backup.unlink()
    except FileNotFoundError:
        pass
    path.rename(backup)
    path.write_bytes(PAYLOAD)


def inherited_fd(fd: int) -> None:
    os.write(fd, PAYLOAD)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    parser.add_argument("--path")
    parser.add_argument("--alias")
    parser.add_argument("--fd", type=int)
    args = parser.parse_args()
    try:
        if args.mode == "direct":
            direct(Path(args.path))
        elif args.mode == "shell":
            shell_redirect(Path(args.path))
        elif args.mode == "symlink":
            symlink_alias(Path(args.path), Path(args.alias))
        elif args.mode == "rename_replace":
            rename_replace(Path(args.path))
        elif args.mode == "fd":
            inherited_fd(args.fd)
        else:
            raise ValueError(args.mode)
    except (PermissionError, FileNotFoundError, OSError, subprocess.CalledProcessError):
        return 13
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
