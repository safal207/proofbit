# ProofBit Benchmark Matrix — v0.1

This file maps the executable evidence in the repository. It is a navigation and interpretation guide, not a synthetic leaderboard.

## Permanent comparison rule

```text
semantic coverage
-> correctness / unsafe behavior
-> proof and audit properties
-> cost
-> speed
```

Do not rank raw throughput across unlike workload domains. Unsupported semantics are reported as unassessed, never counted as prevented.

## Four evaluation axes

| Axis | Question |
|---|---|
| Utility | Did the system permit useful work and prevent the frozen failures? |
| Proof | What evidence, authority, freshness, provenance, replay, context, and outcome semantics are retained? |
| Cost | What software work, bytes, storage, state, LUT, FF, BRAM, transactions, and coordination are required? |
| Speed | What latency, throughput, cycles, stalls, or issue work are measured inside the same frozen workload? |

North-star metric:

```text
Trusted Useful Throughput
  = correctly permitted useful actions with sufficient evidence
    / end-to-end second
```

## Benchmark families

### 1. Semantic seed and cross-architecture transition tests

| ID | Core question | Compared systems | Key result |
|---|---|---|---|
| PB-MEM / PB-GUARD / PB-AI-01 | Can proof-aware state and guarded effects be modeled and attacked? | Value-only baseline vs ProofProcessor / cache | Reference semantics work, but carry substantial Python overhead |
| PB-ARCH-01 | How do ProofBit, CaPU, and value-only controls differ in semantic coverage? | Baseline, ProofBit, CaPU | ProofBit covered the full frozen trust-fault set; CaPU was faster on its narrower wired semantics |
| PB-TRANSITION-01 | Can MORPHOS preserve its frozen transition/recovery mechanism? | MORPHOS native workload | Frozen transfer/recovery behavior passed; not throughput-ranked against guard workloads |
| PB-TRANSITION-02 | Can several architectures run one binary transition oracle? | Raw/guarded software, ProofBit, CaPU, MORPHOS | Good software guard solved the simple task cheaply; architecture evidence types remained distinct |
| PB-TRANSITION-03 | Can systems separate authorization, freshness, replay, conflict, and outcome? | Raw software, full software guard, ProofBit, partial CaPU/MORPHOS adapters | Full software guard and ProofBit both reached 100% correctness; software was much faster in Python |

Primary files:

```text
benchmarks/pb_arch_01.py
benchmarks/pb_transition_01.py
benchmarks/pb_transition_02.py
benchmarks/pb_transition_03.py
```

### 2. Trust propagation, transport, and dynamic maintenance

| ID | Core question | Primary anti-strawman | Key result |
|---|---|---|---|
| PB-TC01 | Does repeated trust-field reconstruction create a composition crossover? | Shared immutable software envelope | ProofBit beat explicit field reconstruction, but shared software remained faster |
| PB-TC02 | Does the result survive real IPC and identical compact encoding? | 42-byte compact conventional record | Compact software remained faster at every tested depth; ProofBit overhead narrowed as IPC dominated |
| PB-TC03 | Does dynamic revocation favor proof-native propagation? | Lazy final software authority | Lazy software and ProofBit matched safety; eager fanout did more maintenance work, but no ProofBit-specific crossover survived |

Primary files:

```text
benchmarks/pb_trust_compose_01.py
benchmarks/pb_trust_compose_02.py
benchmarks/pb_trust_compose_02_median.py
benchmarks/pb_trust_compose_03.py
```

### 3. Crash recovery, durable evidence, and corruption

| ID | Core question | Primary anti-strawman | Key result |
|---|---|---|---|
| PB-TC04 | Can truth be reconstructed after real process crash and retry? | Same-size indexed conventional receipt log | Same recovery correctness and footprint; indexed chains reduced targeted audit work by 500x versus scan |
| PB-TC05 | Will damaged evidence be silently reconstructed as truth? | Indexed integrity log with semantic binding and repair | Both strong systems returned `UNKNOWN`/`CONFLICT` safely with identical repair work |

Primary files:

```text
benchmarks/pb_trust_compose_04.py
benchmarks/pb_trust_compose_04_stability.py
benchmarks/pb_trust_compose_05.py
```

### 4. Policy evolution, language conformance, and release skew

| ID | Core question | Primary anti-strawman | Key result |
|---|---|---|---|
| PB-TC06 | Does one contract reduce policy-copy divergence? | Shared conventional registry | Independent copies paid N-times update/regression work; shared software matched ProofBit |
| PB-TC07 | Do semantics survive Python/Rust/Node boundaries? | Canonical conventional descriptor and validators | 100% agreement for both canonical systems; no unique ProofBit advantage |
| PB-TC08 | What happens when independently released consumers lag policy? | Canonical runtime under version skew | Canonical software and ProofBit preserved availability for known primitives; both failed closed for a genuinely new primitive |

Primary files:

```text
benchmarks/pb_trust_compose_06.py
benchmarks/pb_trust_compose_07.py
benchmarks/pb_trust_compose_08.py
benchmarks/tc07_*_validator.*
benchmarks/tc08_*_validator.*
```

### 5. Enforcement placement and privilege boundaries

| ID | Core question | Primary anti-strawman | Key result |
|---|---|---|---|
| PB-TC09 | Can application validation be bypassed before the effect? | Mandatory software reference monitor | Application-only validation failed 7/8 frozen cases; both mandatory strong systems passed all |
| PB-TC10 | Can hostile same-user code bypass the protected resource? | Separate POSIX UID + broker | Both strong designs blocked 6/6 unprivileged routes; both failed the same-privilege/root probe |
| PB-TC11 | Does a non-forgeable metadata plane stop bounded attacker programs? | Tagged capability ISA model | Capability and ProofBit had zero bypasses; flat value machine had many |
| PB-TC12 | Must tags/proofs remain coherent across CPU, debug, DMA, context, and rollback? | Whole-system capability model | Both whole-system strong designs blocked all six frozen attacks; CPU-only tags failed |

Primary files:

```text
benchmarks/pb_trust_compose_09.py
benchmarks/tc09_effect_worker.py
benchmarks/pb_trust_compose_10.py
benchmarks/tc10_privileged_broker.py
benchmarks/tc10_hostile_writer.py
benchmarks/pb_trust_compose_11.py
benchmarks/pb_trust_compose_12.py
```

### 6. RTL and physical memory economics

| ID | Core question | Primary anti-strawman | Key result |
|---|---|---|---|
| PB-HW-01 | Does a proof tag map differently from an equal capability tag? | Equal-semantics capability RTL | Identical LUT/FF/BRAM/cell/depth mapping |
| PB-HW-02 | What is the incremental price of richer trust semantics? | Full conventional evidence RTL | Rich semantics cost substantially more than minimal capability; conventional and ProofBit full designs were identical |
| PB-HW-03 | Is a dedicated four-parent composition primitive useful? | Conventional `COMPOSE4` | Primitive reduced transactions `6 -> 2` and issue cycles `4 -> 1`; conventional and ProofBit primitives were identical |
| PB-HW-04 | What does real multi-read evidence memory cost? | Equal physical multi-read conventional cache | Warm compose reached 1 cycle, but required 4x evidence storage; conventional and ProofBit cache mapped identically |

Primary files:

```text
rtl/pb_hw_01.v
rtl/pb_hw_02.v
rtl/pb_hw_03.v
rtl/pb_hw_04.v
benchmarks/pb_hw_01.py
benchmarks/pb_hw_02.py
benchmarks/pb_hw_03.py
benchmarks/pb_hw_04.py
```

## Official PB-HW-04 physical result

Icarus Verilog 12.0 and Yosys 0.33, Xilinx-7 structural mapping:

| Metric | Single-port | Banked | Conventional cache | ProofBit cache |
|---|---:|---:|---:|---:|
| Cold compose cycles | 4 | 2 | 2 | 2 |
| Warm compose cycles | 4 | 2 | 1 | 1 |
| Same-bank cold cycles | 4 | 5 | 2 | 2 |
| Same-bank warm cycles | 4 | 5 | 1 | 1 |
| RAMB36 | 2 | 4 | 8 | 8 |
| LUT | 6,966 | 7,645 | 10,213 | 10,213 |
| FF | 1,286 | 1,335 | 2,148 | 2,148 |
| Core cells excluding I/O | 8,943 | 10,018 | 13,213 | 13,213 |
| Logic-depth proxy | 36 | 59 | 100 | 100 |
| Logical evidence bits | 65,536 | 65,536 | 262,144 | 262,144 |

Functional oracle: `52 checks / 0 failures`.

## Reproduction

Run the full Python regression suite:

```bash
python -m unittest discover -s tests -v
```

Run a representative software trust matrix:

```bash
python benchmarks/pb_transition_03.py --json
```

Install open-source RTL tools on Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y iverilog yosys
```

Run the latest physical evidence-memory benchmark:

```bash
python benchmarks/pb_hw_04.py --json
```

For the exact frozen oracles, tool versions, and assertions, use the dedicated workflows under `.github/workflows/`.

## Interpretation guardrails

- Python throughput is not silicon throughput.
- Yosys `ltp -noff` is a structural path proxy, not post-route timing.
- Xilinx primitive counts are not ASIC PPA.
- GitHub-hosted runner measurements do not establish energy efficiency.
- Equal correctness does not imply equal evidence semantics.
- Equal semantics and topology should be expected to synthesize similarly.
- External accelerator specifications remain reference-only until the same executable workload runs on the target.
- No single winner score is permitted.
