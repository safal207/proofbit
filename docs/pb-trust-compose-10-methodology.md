# PB-TRUST-COMPOSE-10 methodology

`PB-TC10/v0.1 resource-privilege-bypass`

## Question

TC09 showed that a mandatory software reference monitor at the authoritative side-effect seam can reproduce the software ProofBit safety result. TC10 moves the boundary one level lower:

> Can hostile application code bypass the broker and write the protected resource directly?

## Threat model

The scored attacker is a real subprocess running as the normal GitHub Actions runner UID. It does **not** invoke `sudo`.

For the two strong systems, the protected directory and file are owned by the separate `nobody` UID and use POSIX DAC permissions (`0700` directory, `0600` file). The only legitimate writer is a persistent broker process launched under that protected UID.

The benchmark harness itself has passwordless `sudo` because GitHub-hosted Ubuntu runners expose it. Harness privilege is used only to construct and clean up the privilege-separation fixture and to run the explicit same-privilege compromise probe. It is not given to the scored hostile process.

## Compared systems

### `application_owned_resource`

The application UID owns the protected resource. A competent application validator may validate the normal path, but the same UID can still open or retain a writable handle to the resource.

### `software_os_reference_monitor`

Strongest conventional anti-strawman:

- resource owned by a separate UID;
- application UID cannot traverse/write the protected directory;
- one broker under the resource UID is the only legitimate writer;
- the broker performs the full final trust validation;
- writable resource handles are not exposed to application code.

### `proofbit_os_boundary`

Exactly the same POSIX UID/DAC topology and resource ownership as the conventional reference monitor. The broker expresses final authority through `ProofProcessor` / `Evidence`, exact statement binding, epoch checks and consume-once replay semantics.

A tie is a valid negative result.

## Frozen unprivileged bypasses

1. `DIRECT_OPEN` — hostile subprocess opens the protected path directly.
2. `SHELL_REDIRECT` — hostile subprocess attempts a shell append.
3. `SYMLINK_ALIAS` — hostile subprocess writes through a symlink alias.
4. `RENAME_REPLACE` — hostile subprocess renames/replaces the protected pathname.
5. `INHERITED_FD` — application attempts to obtain a writable FD and leak it to a child.
6. `STALE_FD_AFTER_CHMOD` — after a writable FD is opened, path permissions are revoked; the inherited FD is then used anyway.

The last case intentionally captures an important Unix property: changing path permissions does not revoke an already-open writable file descriptor. Avoiding writable-handle leakage is therefore part of the architecture, not merely another `chmod` call.

## Same-privilege compromise probe

A separate probe executes a direct append **as the protected resource UID**. It is not scored as an unprivileged bypass.

Expected result for both strong software systems:

```text
same resource UID / root compromise
-> direct resource write succeeds
```

This is a falsifier for any claim that software ProofBit already provides a privilege boundary stronger than the OS TCB. If code executes with the resource owner's privilege, both software designs are bypassable in this fixture.

## Valid-path measurement

Each system also runs 250 valid effects per round through a persistent broker. Runtime excludes privilege-fixture setup and broker startup. Eleven rounds rotate system order. Valid-path throughput is secondary; bypass resistance is primary.

## Primary metrics

- unprivileged bypasses blocked;
- unsafe hostile resource writes;
- valid-path availability;
- same-privilege compromise success;
- mandatory OS privilege boundaries;
- writable-handle exposure;
- valid effects / second.

No single winner score is calculated.

## Claim boundary

This is a real POSIX UID/DAC experiment with real subprocesses and file writes on one ephemeral Linux runner. It is **not** a kernel exploit benchmark, namespace/container isolation benchmark, Linux `capability(7)` proof, cryptographic authorization system, hardware simulator, energy benchmark, novelty analysis or proof of universal superiority.
