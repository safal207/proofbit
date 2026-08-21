from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass, replace
from itertools import product
import json
import statistics
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from proofbit.model import Evidence, ProofProcessor

BENCHMARK_ID = "PB-TRUST-COMPOSE-11"
VERSION = "0.1"
PROTOCOL = "PB-TC11/v0.1 isa-memory-enforcement"

ACTION_A = 0xA1
ACTION_B = 0xB2
AUTHORITY = 7
SYSTEMS = ("flat_value_machine", "tagged_capability_machine", "proofbit_machine")
OPS = (
    "FORGE",
    "MUTATE_B",
    "MUTATE_EPOCH",
    "RAW_ROUNDTRIP",
    "CLONE",
    "SWAP",
    "EFFECT_A",
    "EFFECT_B",
)
SCENARIOS = (
    "FORGE_NO_AUTH",
    "REBIND_VALID_A_TO_B",
    "STALE_AFTER_EPOCH",
    "REPLAY_CONSUMED",
    "DUPLICATE_ONE_AUTH",
    "RAW_RECONSTRUCTION",
)


@dataclass
class Token:
    action: int
    epoch: int
    nonce: int
    authority: int = AUTHORITY
    provenance: int = 1
    allow: bool = True
    tagged: bool = False
    raw_derived: bool = False


class Machine:
    def __init__(self, system: str, epoch: int = 1) -> None:
        self.system = system
        self.epoch = epoch
        self.reg: Token | None = None
        self.shadow: Token | None = None
        self.consumed: set[int] = set()
        self.effects: list[tuple[int, bool]] = []
        self.proof = ProofProcessor(authority=AUTHORITY, epoch=epoch)

    def mint_trusted(self, *, action: int, epoch: int, nonce: int) -> Token:
        return Token(
            action=action,
            epoch=epoch,
            nonce=nonce,
            tagged=self.system != "flat_value_machine",
        )

    def _effect_flat(self, action: int) -> bool:
        token = self.reg
        allowed = bool(token and token.allow)
        if allowed:
            self.effects.append((action, bool(token.raw_derived)))
        return allowed

    def _effect_capability(self, action: int) -> bool:
        token = self.reg
        allowed = bool(
            token
            and token.tagged
            and token.allow
            and token.action == action
            and token.authority == AUTHORITY
            and token.epoch == self.epoch
            and token.nonce not in self.consumed
        )
        if allowed:
            self.consumed.add(token.nonce)
            self.effects.append((action, bool(token.raw_derived)))
        return allowed

    def _effect_proofbit(self, action: int) -> bool:
        token = self.reg
        if not token or not token.tagged or not token.allow or token.provenance == 0:
            return False
        self.proof.epoch = self.epoch
        evidence = Evidence(
            statement=f"effect:{token.action:02x}",
            value=True,
            proof_id=token.nonce,
            authority=token.authority,
            epoch=token.epoch,
            provenance=token.provenance,
        )
        address = 1
        self.proof.store_evidence(address, evidence)
        allowed = self.proof.guarded_execute(
            address,
            single_use=True,
            expected_statement=f"effect:{action:02x}",
        )
        if allowed:
            self.effects.append((action, bool(token.raw_derived)))
        return allowed

    def effect(self, action: int) -> bool:
        if self.system == "flat_value_machine":
            return self._effect_flat(action)
        if self.system == "tagged_capability_machine":
            return self._effect_capability(action)
        if self.system == "proofbit_machine":
            return self._effect_proofbit(action)
        raise ValueError(self.system)

    def step(self, op: str) -> None:
        if op == "FORGE":
            self.reg = Token(
                action=ACTION_A,
                epoch=self.epoch,
                nonce=999,
                tagged=False,
                raw_derived=True,
            )
        elif op == "MUTATE_B" and self.reg is not None:
            self.reg = replace(
                self.reg,
                action=ACTION_B,
                tagged=False if self.system != "flat_value_machine" else self.reg.tagged,
            )
        elif op == "MUTATE_EPOCH" and self.reg is not None:
            self.reg = replace(
                self.reg,
                epoch=self.epoch,
                tagged=False if self.system != "flat_value_machine" else self.reg.tagged,
            )
        elif op == "RAW_ROUNDTRIP" and self.reg is not None:
            self.reg = replace(self.reg, tagged=False, raw_derived=True)
        elif op == "CLONE" and self.reg is not None:
            self.shadow = deepcopy(self.reg)
        elif op == "SWAP":
            self.reg, self.shadow = self.shadow, self.reg
        elif op == "EFFECT_A":
            self.effect(ACTION_A)
        elif op == "EFFECT_B":
            self.effect(ACTION_B)

    def privileged_debug_effect(self, action: int) -> None:
        self.effects.append((action, False))

    def dma_effect(self, action: int) -> None:
        self.effects.append((action, False))


def setup(system: str, scenario: str) -> Machine:
    m = Machine(system)
    if scenario == "REBIND_VALID_A_TO_B":
        m.reg = m.mint_trusted(action=ACTION_A, epoch=1, nonce=10)
    elif scenario == "STALE_AFTER_EPOCH":
        m.reg = m.mint_trusted(action=ACTION_A, epoch=1, nonce=11)
        m.epoch = 2
        m.proof.epoch = 2
    elif scenario == "REPLAY_CONSUMED":
        m.reg = m.mint_trusted(action=ACTION_A, epoch=1, nonce=12)
        if system == "proofbit_machine":
            m.proof.consumed_proofs.add(12)
        else:
            m.consumed.add(12)
    elif scenario == "DUPLICATE_ONE_AUTH":
        m.reg = m.mint_trusted(action=ACTION_A, epoch=1, nonce=13)
    elif scenario == "RAW_RECONSTRUCTION":
        m.reg = m.mint_trusted(action=ACTION_A, epoch=1, nonce=14)
    return m


def unsafe(scenario: str, m: Machine) -> bool:
    actions = [action for action, _ in m.effects]
    if scenario == "FORGE_NO_AUTH":
        return ACTION_A in actions
    if scenario == "REBIND_VALID_A_TO_B":
        return ACTION_B in actions
    if scenario in ("STALE_AFTER_EPOCH", "REPLAY_CONSUMED"):
        return ACTION_A in actions
    if scenario == "DUPLICATE_ONE_AUTH":
        return actions.count(ACTION_A) >= 2
    if scenario == "RAW_RECONSTRUCTION":
        return any(action == ACTION_A and raw for action, raw in m.effects)
    raise ValueError(scenario)


def search_scenario(system: str, scenario: str, max_program_len: int) -> dict:
    tested = bypasses = 0
    shortest = None
    examples: list[list[str]] = []
    for length in range(1, max_program_len + 1):
        for sequence in product(OPS, repeat=length):
            tested += 1
            m = setup(system, scenario)
            for op in sequence:
                m.step(op)
            if unsafe(scenario, m):
                bypasses += 1
                if shortest is None:
                    shortest = length
                if len(examples) < 3:
                    examples.append(list(sequence))
    return {
        "programs_tested": tested,
        "bypass_programs": bypasses,
        "shortest_bypass_length": shortest,
        "example_bypasses": examples,
    }


def exhaustive_search(system: str, max_program_len: int) -> dict:
    rows = {
        scenario: search_scenario(system, scenario, max_program_len)
        for scenario in SCENARIOS
    }
    return {
        "scenarios": rows,
        "total_programs_tested": sum(x["programs_tested"] for x in rows.values()),
        "total_bypass_programs": sum(x["bypass_programs"] for x in rows.values()),
        "scenario_coverage": len(rows),
        "scenarios_with_bypass": sum(x["bypass_programs"] > 0 for x in rows.values()),
    }


def valid_path(system: str, iterations: int) -> dict:
    m = Machine(system)
    start = time.perf_counter_ns()
    for nonce in range(1, iterations + 1):
        m.reg = m.mint_trusted(action=ACTION_A, epoch=1, nonce=nonce)
        if not m.effect(ACTION_A):
            raise AssertionError(f"{system}: valid effect blocked at nonce {nonce}")
    elapsed = time.perf_counter_ns() - start
    return {
        "elapsed_ns": elapsed,
        "effects_per_sec": iterations / (elapsed / 1_000_000_000),
        "effects": len(m.effects),
    }


def privileged_escape_probe(system: str) -> dict:
    debug = Machine(system)
    debug.privileged_debug_effect(ACTION_B)
    dma = Machine(system)
    dma.dma_effect(ACTION_B)
    privileged_mint = Machine(system)
    privileged_mint.reg = privileged_mint.mint_trusted(
        action=ACTION_B, epoch=1, nonce=77
    )
    minted_effect = privileged_mint.effect(ACTION_B)
    return {
        "debug_bypass_effect": ACTION_B in [a for a, _ in debug.effects],
        "dma_bypass_effect": ACTION_B in [a for a, _ in dma.effects],
        "privileged_mint_effect": bool(minted_effect),
        "scored": False,
    }


def logical_metadata() -> dict:
    return {
        "flat_value_machine": {
            "unforgeable_tag": False,
            "logical_authority_fields": ["allow"],
            "mandatory_effect_check": False,
        },
        "tagged_capability_machine": {
            "unforgeable_tag": True,
            "logical_authority_fields": ["tag", "action", "issuer", "epoch", "nonce"],
            "mandatory_effect_check": True,
        },
        "proofbit_machine": {
            "unforgeable_tag": True,
            "logical_authority_fields": [
                "tag",
                "statement",
                "authority",
                "epoch",
                "proof_id",
                "provenance",
            ],
            "mandatory_effect_check": True,
        },
    }


def run(*, max_program_len: int, valid_iterations: int, rounds: int) -> dict:
    search = {system: exhaustive_search(system, max_program_len) for system in SYSTEMS}
    runtime_samples = {system: [] for system in SYSTEMS}
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
            runtime_samples[system].append(valid_path(system, valid_iterations))
    runtime = {}
    for system, rows in runtime_samples.items():
        rates = [row["effects_per_sec"] for row in rows]
        runtime[system] = {
            "median_valid_effects_per_sec": statistics.median(rates),
            "raw_valid_effects_per_sec": rates,
            "valid_effects_per_round": valid_iterations,
        }
    privileged = {system: privileged_escape_probe(system) for system in SYSTEMS}
    return {
        "benchmark_id": BENCHMARK_ID,
        "version": VERSION,
        "protocol": PROTOCOL,
        "max_attacker_program_len": max_program_len,
        "attacker_opcodes": list(OPS),
        "attack_scenarios": list(SCENARIOS),
        "search": search,
        "runtime": runtime,
        "runtime_orders": orders,
        "logical_metadata": logical_metadata(),
        "privileged_escape_probes": privileged,
        "primary_anti_strawman": "tagged_capability_machine",
        "no_single_winner_score": True,
        "tag_axiom": (
            "Unprivileged FORGE, field mutation and RAW_ROUNDTRIP cannot create "
            "or preserve the authorization tag in either strong machine. "
            "This is a model axiom, not measured hardware behavior."
        ),
        "claim_boundary": (
            "Executable Python ISA/memory reference model with exhaustive bounded "
            "attacker-program search. No RTL, transistor, cache-coherence, speculative-"
            "execution, cryptographic, cycle-accurate, energy/area, silicon, novelty, "
            "patentability or universal-superiority claim. DEBUG/DMA/privileged mint "
            "are explicit unscored escape classes."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-program-len", type=int, default=5)
    parser.add_argument("--valid-iterations", type=int, default=10000)
    parser.add_argument("--rounds", type=int, default=11)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.max_program_len < 1 or args.valid_iterations < 1 or args.rounds < 1:
        raise SystemExit("positive benchmark sizes required")
    report = run(
        max_program_len=args.max_program_len,
        valid_iterations=args.valid_iterations,
        rounds=args.rounds,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for system in SYSTEMS:
            row = report["search"][system]
            speed = report["runtime"][system]["median_valid_effects_per_sec"]
            print(
                f"{system}: bypasses={row['total_bypass_programs']} "
                f"programs={row['total_programs_tested']} "
                f"valid_effects/s={speed:,.1f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
