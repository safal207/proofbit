from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import dataclass, replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.model import Evidence, ProofProcessor

BENCHMARK_ID = "PB-TRUST-COMPOSE-12"
VERSION = "0.1"
PROTOCOL = "PB-TC12/v0.1 whole-system-coherence"
ACTION = 0xA1
AUTHORITY = 7
SYSTEMS = (
    "cpu_only_tag_machine",
    "whole_system_capability_machine",
    "whole_system_proofbit_machine",
)
SCENARIOS = (
    "DEBUG_DIRECT_EFFECT",
    "DMA_DIRECT_EFFECT",
    "DEBUG_FORGED_TAG",
    "CONTEXT_SWITCH_LEAK",
    "CACHE_TAG_DATA_SPLIT",
    "SNAPSHOT_REPLAY_ROLLBACK",
)
CHANNELS = ("cpu", "debug", "dma")


@dataclass
class Token:
    action: int = ACTION
    epoch: int = 1
    nonce: int = 1
    context: int = 1
    object_version: int = 1
    authority: int = AUTHORITY
    provenance: int = 1
    allow: bool = True
    tagged: bool = False


class WholeMachine:
    def __init__(self, system: str) -> None:
        self.system = system
        self.epoch = 1
        self.context = 1
        self.object_version = 1
        self.effects: list[tuple[str, int]] = []
        self.partial_consumed_by_context: dict[int, set[int]] = {1: set()}
        self.global_consumed: set[int] = set()
        self.proof = ProofProcessor(authority=AUTHORITY, epoch=1)

    @property
    def strong(self) -> bool:
        return self.system != "cpu_only_tag_machine"

    def mint(
        self,
        nonce: int,
        *,
        context: int | None = None,
        object_version: int | None = None,
    ) -> Token:
        return Token(
            nonce=nonce,
            context=self.context if context is None else context,
            object_version=(
                self.object_version if object_version is None else object_version
            ),
            provenance=self.context if context is None else context,
            tagged=True,
        )

    def debug_forge_tag(self, nonce: int) -> Token:
        # CPU-only tagging leaves debug metadata mint outside the protected
        # authority path. Whole-system designs route minting through the same
        # protected tag/proof authority and therefore return an untagged object.
        return Token(
            nonce=nonce,
            context=self.context,
            object_version=self.object_version,
            provenance=self.context,
            tagged=not self.strong,
        )

    def _partial_authorize(self, token: Token) -> bool:
        consumed = self.partial_consumed_by_context.setdefault(self.context, set())
        allowed = bool(
            token.tagged
            and token.allow
            and token.action == ACTION
            and token.authority == AUTHORITY
            and token.epoch == self.epoch
            and token.nonce not in consumed
        )
        if allowed:
            consumed.add(token.nonce)
        return allowed

    def _cap_authorize(self, token: Token) -> bool:
        allowed = bool(
            token.tagged
            and token.allow
            and token.action == ACTION
            and token.authority == AUTHORITY
            and token.epoch == self.epoch
            and token.context == self.context
            and token.object_version == self.object_version
            and token.nonce not in self.global_consumed
        )
        if allowed:
            self.global_consumed.add(token.nonce)
        return allowed

    def _proof_authorize(self, token: Token) -> bool:
        if not (
            token.tagged
            and token.allow
            and token.provenance == self.context
            and token.object_version == self.object_version
        ):
            return False
        self.proof.epoch = self.epoch
        evidence = Evidence(
            statement=f"effect:{token.action:02x}:objv:{token.object_version}",
            value=True,
            proof_id=token.nonce,
            authority=token.authority,
            epoch=token.epoch,
            provenance=token.provenance,
        )
        self.proof.store_evidence(1, evidence)
        return self.proof.guarded_execute(
            1,
            single_use=True,
            expected_statement=f"effect:{ACTION:02x}:objv:{self.object_version}",
        )

    def authorize(self, token: Token) -> bool:
        if self.system == "cpu_only_tag_machine":
            return self._partial_authorize(token)
        if self.system == "whole_system_capability_machine":
            return self._cap_authorize(token)
        if self.system == "whole_system_proofbit_machine":
            return self._proof_authorize(token)
        raise ValueError(self.system)

    def effect(self, channel: str, token: Token) -> bool:
        if channel in ("debug", "dma") and self.system == "cpu_only_tag_machine":
            self.effects.append((channel, token.nonce))
            return True
        allowed = self.authorize(token)
        if allowed:
            self.effects.append((channel, token.nonce))
        return allowed

    def switch_context(self, new_context: int) -> None:
        self.context = new_context
        self.partial_consumed_by_context.setdefault(new_context, set())

    def rollback_partial_consumed(self, snapshot: dict[int, set[int]]) -> None:
        if self.system == "cpu_only_tag_machine":
            self.partial_consumed_by_context = {
                key: set(value) for key, value in snapshot.items()
            }
        # Strong machines keep monotonic replay state outside guest snapshots.


def run_scenario(system: str, scenario: str) -> dict:
    machine = WholeMachine(system)
    unsafe = False

    if scenario == "DEBUG_DIRECT_EFFECT":
        unsafe = machine.effect("debug", Token(nonce=100, tagged=False))
    elif scenario == "DMA_DIRECT_EFFECT":
        unsafe = machine.effect("dma", Token(nonce=101, tagged=False))
    elif scenario == "DEBUG_FORGED_TAG":
        unsafe = machine.effect("cpu", machine.debug_forge_tag(102))
    elif scenario == "CONTEXT_SWITCH_LEAK":
        token = machine.mint(103, context=1)
        machine.switch_context(2)
        unsafe = machine.effect("cpu", token)
    elif scenario == "CACHE_TAG_DATA_SPLIT":
        token = machine.mint(104, object_version=1)
        machine.object_version = 2
        unsafe = machine.effect("cpu", token)
    elif scenario == "SNAPSHOT_REPLAY_ROLLBACK":
        token = machine.mint(105)
        before = {
            key: set(value)
            for key, value in machine.partial_consumed_by_context.items()
        }
        first = machine.effect("cpu", token)
        if not first:
            raise AssertionError(f"{system}: replay prelude rejected")
        machine.rollback_partial_consumed(before)
        unsafe = machine.effect("cpu", token)
    else:
        raise ValueError(scenario)

    return {"unsafe_effect": bool(unsafe), "blocked": not bool(unsafe)}


def scored_matrix(system: str) -> dict:
    rows = {scenario: run_scenario(system, scenario) for scenario in SCENARIOS}
    unsafe = sum(row["unsafe_effect"] for row in rows.values())
    return {
        "scenarios": rows,
        "scenario_count": len(rows),
        "unsafe_effects": unsafe,
        "blocked_attacks": len(rows) - unsafe,
        "oracle_accuracy": (len(rows) - unsafe) / len(rows),
    }


def valid_path(system: str, iterations: int) -> dict:
    machine = WholeMachine(system)
    start = time.perf_counter_ns()
    for index in range(iterations):
        channel = CHANNELS[index % len(CHANNELS)]
        token = machine.mint(index + 1)
        if not machine.effect(channel, token):
            raise AssertionError(f"{system}: valid {channel} effect rejected")
    elapsed_ns = time.perf_counter_ns() - start
    return {
        "effects": len(machine.effects),
        "elapsed_ns": elapsed_ns,
        "effects_per_sec": iterations / (elapsed_ns / 1_000_000_000),
    }


def deeper_escape_probe(system: str) -> dict:
    return {
        "physical_tag_store_tamper_bypass": True,
        "malicious_firmware_bypass": True,
        "scored": False,
    }


def logical_metadata() -> dict:
    return {
        "cpu_only_tag_machine": {
            "enforced_domains": ["cpu"],
            "global_replay_state": False,
            "context_binding": False,
            "object_version_binding": False,
        },
        "whole_system_capability_machine": {
            "enforced_domains": ["cpu", "debug", "dma", "cache", "context"],
            "global_replay_state": True,
            "context_binding": True,
            "object_version_binding": True,
        },
        "whole_system_proofbit_machine": {
            "enforced_domains": ["cpu", "debug", "dma", "cache", "context"],
            "global_replay_state": True,
            "context_binding": True,
            "object_version_binding": True,
        },
    }


def run(rounds: int, valid_iterations: int) -> dict:
    safety = {system: scored_matrix(system) for system in SYSTEMS}
    samples = {system: [] for system in SYSTEMS}
    orders = []
    permutations = (
        SYSTEMS,
        (SYSTEMS[1], SYSTEMS[2], SYSTEMS[0]),
        (SYSTEMS[2], SYSTEMS[0], SYSTEMS[1]),
    )
    for round_index in range(rounds):
        order = permutations[round_index % len(permutations)]
        orders.append(list(order))
        for system in order:
            samples[system].append(valid_path(system, valid_iterations))

    runtime = {}
    for system, rows in samples.items():
        rates = [row["effects_per_sec"] for row in rows]
        runtime[system] = {
            "median_valid_effects_per_sec": statistics.median(rates),
            "raw_valid_effects_per_sec": rates,
            "valid_effects_per_round": valid_iterations,
        }

    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "scenarios": list(SCENARIOS),
        "channels": list(CHANNELS),
        "safety": safety,
        "runtime": runtime,
        "runtime_orders": orders,
        "logical_metadata": logical_metadata(),
        "deeper_escape_probes": {
            system: deeper_escape_probe(system) for system in SYSTEMS
        },
        "primary_anti_strawman": "whole_system_capability_machine",
        "no_single_winner_score": True,
        "coherence_axiom": (
            "Whole-system capability and ProofBit models are both granted an "
            "unforgeable metadata plane across CPU/debug/DMA/cache/context domains. "
            "This is a model axiom, not measured hardware behavior."
        ),
        "claim_boundary": (
            "Executable Python whole-system coherence reference model. No RTL, "
            "physical DMA/IOMMU, cache protocol, speculative execution, firmware, "
            "physical tag RAM, cycle accuracy, area/energy, silicon, novelty, "
            "patentability or universal-superiority claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=11)
    parser.add_argument("--valid-iterations", type=int, default=10000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.rounds < 1 or args.valid_iterations < 1:
        raise SystemExit("positive benchmark sizes required")
    report = run(args.rounds, args.valid_iterations)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for system in SYSTEMS:
            print(
                f"{system}: unsafe={report['safety'][system]['unsafe_effects']} "
                f"speed={report['runtime'][system]['median_valid_effects_per_sec']:.1f}/s"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
