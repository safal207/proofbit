# PB-HW-04 — Physical proof-memory / cache economics

## Question

PB-HW-03 showed that a four-parent composition primitive can reduce instruction issue work, but all four evidences arrived directly on input lanes. PB-HW-04 asks what happens when those evidences must be fetched from **synthesizable physical memory**.

The experiment tests whether four-parent trust composition remains useful after paying for memory ports, bank conflicts, caching, invalidation, replay state, and separate outcome evidence — and whether any benefit remains unique to ProofBit after a strong conventional memory design receives the same resources.

## Frozen record

Evidence table:

```text
1024 entries × 64 bits
```

Each 64-bit record contains the fields needed by the common oracle:

- epistemic state,
- authority,
- epoch/freshness,
- 10-bit evidence identity,
- provenance,
- execution context,
- statement payload.

All architectures also maintain consume-once parent replay state and preserve separate outcome evidence.

## Compared physical organizations

### 1. Single-port conventional

- one `1024×64` block-style evidence table;
- one parent read is issued per cycle;
- four-parent composition therefore serializes memory access.

### 2. Four-bank conventional

- same total logical evidence capacity;
- four `256×64` banks selected by `address[1:0]`;
- at most one read per bank per cycle;
- conflict-free four-parent sets can issue together;
- same-bank sets serialize and expose bank-conflict stalls.

### 3. Multi-port conventional cache — primary anti-strawman

- four coherent `1024×64` evidence-table replicas, one physical read lane each;
- 16-entry direct-mapped cache;
- four concurrent parent reads on a miss;
- warm all-hit path bypasses physical table reads;
- a table update or explicit invalidation clears a matching cache line.

### 4. ProofBit cache

The ProofBit wrapper uses the **same physical core** as the strong conventional multi-port cache. It receives no free port, storage, cache, replay, invalidation, or outcome machinery.

If the two synthesize and execute identically, that is the expected strong negative result.

## Deterministic executable workload

The Icarus testbench exercises:

1. cold conflict-free cache miss;
2. warm all-hit reuse after a deliberately failed statement-binding attempt, so parents were not consumed;
3. four addresses mapped to one bank;
4. warm same-bank request;
5. cache invalidation followed by one stale-record refetch;
6. parent replay rejection;
7. successful separate outcome receipt;
8. false outcome after successful authorization.

The warm-up composition intentionally uses the wrong derived statement. That fills cache state but does **not** consume parent replay identities.

## Frozen cache accounting

```text
cold conflict-free: 0 hits / 4 misses
warm conflict-free: 4 hits / 0 misses
same-bank cold:     0 hits / 4 misses
same-bank warm:     4 hits / 0 misses
post invalidation:  3 hits / 1 miss
```

## Primary measurements

Simulation:

- common safety/oracle failures;
- compose latency in cycles for cold, warm, bank-conflict, warm-conflict, and post-invalidation paths;
- replay rejection;
- separate outcome correctness;
- equality of strong conventional and ProofBit cache latencies.

Structural synthesis:

- LUT;
- FF;
- LUTRAM cells;
- RAMB18 / RAMB36 and RAMB18-equivalent count;
- core cells excluding top-level I/O;
- total cells;
- `ltp -noff` logic-depth proxy;
- logical physical evidence bits;
- cache data/tag/valid bits;
- replay-state bits.

## Anti-strawman rule

The key ProofBit comparison is **not** against the single-port or banked baseline. It is against `multiport_conventional_cache`, which has the same four read lanes, same replicated evidence storage, same cache capacity, same replay semantics, same invalidation behavior, and same outcome contract.

Any benefit shared by those two belongs to the memory/cache organization, not uniquely to ProofBit.

## Falsifiers

A ProofBit-specific memory advantage is **not established** if the strong conventional cache matches ProofBit in:

- safety,
- cache hit/miss latency,
- invalidation behavior,
- bank-conflict immunity,
- mapped BRAM/LUTRAM/LUT/FF resources,
- logic-depth proxy.

A four-read architecture is not considered “free”: replicated evidence-table bits and mapped block memories are reported explicitly.

## Claim boundary

This is synthesizable reference Verilog simulated with Icarus and structurally mapped by Yosys `synth_xilinx -family xc7`.

It does **not** establish FPGA board timing, ASIC PPA, power/energy, ECC cost, coherent system fabric cost, physical placement/routing, speculative execution behavior, IOMMU/firmware-root security, silicon performance, novelty, patentability, or universal superiority.
