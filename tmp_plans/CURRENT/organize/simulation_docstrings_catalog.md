# Simulation Module Docstrings Catalog

Scope: `src/econsim/simulation/` — collected module-level docstrings and notable inline milestone-tagged comments (Gate/Phase). Class/function docstrings inside very large files are omitted unless milestone language present, to keep focus on modernization targets.

---

## __init__.py (module)
```
"""Simulation package.

Deterministic spatial grid + agent model (Gates 3–5) including decision
logic and optional hooks (respawn, metrics) prepared for Gate 6 factory
integration. Deferrals: prices, budgets, pathfinding, multi-resource
optimization heuristics, trading/markets.
"""
```

---

## agent.py (module)
```
"""Agent abstraction (Gate 4+ decision capable).

Represents a mobile economic actor collecting typed resources under a
preference function. Maintains distinct *carrying* vs *home* inventories
and mode-driven behavior (FORAGE, RETURN_HOME, IDLE). Decision mode uses
greedy 1-step movement toward the highest scored resource target within
a perception radius, applying epsilon bootstrap to avoid zero-product
stalls for multiplicative utilities.

Capabilities:
* Deterministic target selection (tie-break: −ΔU, distance, x, y)
* Inventory deposit on home arrival
* Mode transitions (forage ↔ return_home ↔ idle)

Deferred:
* Multi-agent trading / interaction rules
* Production / consumption cycles
* Path planning beyond greedy 1-step heuristic
"""
```
Inline milestone comment examples:
```
# Perception radius (Manhattan) for decision logic (Gate 4 constant)
# Phase 3.2: Track retargeting behavior for behavior aggregation
```

---

## grid.py (module)
```
"""Grid abstraction (Gates 3–5 implemented).

Stores typed resources using a dict mapping ``(x,y) -> type`` providing
O(1) average membership, deterministic sorted iteration (for target
selection / hashing), and coordinate validation.

Capabilities:
* Add / remove typed resources (A,B)
* Deterministic serialization & sorted iteration helper
* Backward-compatible boolean removal API (`take_resource`)

Deferred:
* Resource quantities >1 per cell
* Spatial indexing optimizations (performance currently sufficient)
* Rich resource metadata (value, regeneration profile)
"""
```
Inline milestone comment:
```
ResourceType = str  # For Gate 4: simple 'A','B' literal types
```

---

## world.py (module)
```
"""Simulation coordinator (Gates 3–6 implemented).

Orchestrates per-tick progression across agents & grid. Supports two
paths: legacy random walk (for baseline / regression comparison) and
deterministic decision mode (greedy 1-step target pursuit using
preference-driven ΔU scoring). Optional hooks enable resource respawn
and metrics collection when attached.

Decision Mode Sequence:
1. For each agent (list order confers contest priority): target selection
2. Single-cell movement toward target
3. Resource collection & potential retarget if race lost
4. Deposit at home if returning
5. Respawn hook → Metrics hook → step counter increment

Deferred:
* Multi-phase (pipeline) ordering strategies
* Agent interaction (trading, negotiation)
* Parallel / batched stepping (single-thread invariant maintained)
"""
```
Inline milestone comment:
```
# Draft trade intents (Phase 2 feature-flagged).
```

---

## metrics.py (module)
```
"""Metrics collection (introduced Gate 5, integrated via factory in Gate 6).

Captures per-step aggregate inventory & resource counts and maintains a
determinism hash that is sensitive to agent ordering, positions, carried
and home goods, and resource layout. The hash provides a lightweight
regression sentinel for any change in step ordering or selection logic.

Capabilities:
* Append structured per-step aggregate records (access via ``records()``)
* Streaming SHA256 updated each step with canonical serialization
* Determinism tests rely on hash parity across identical seeds

Deferred / Not Yet Included:
* Per-agent utility logging (will pair with future visualization)
* Derived economic indicators (e.g., inequality metrics)
* Selective metric enable/disable granularity beyond global ``enabled`` flag
"""
```
Inline milestone comments:
```
# Bilateral2 Phase 1 additions (hash-excluded):
fairness_round: int = 0  # Phase 3: increments per executed trade (advisory, hash-excluded)
```

---

## respawn.py (module)
```
"""Resource respawn scheduler (introduced Gate 5, factory-attached in Gate 6).

Maintains a target *density* of resources using a deterministic RNG. The
scheduler replenishes consumed resources to maintain the target count at
configurable intervals (controlled by simulation stepping logic).

Algorithm Summary:
1. Compute ``target_count = floor(target_density * total_cells)``.
2. If current count < target, compute deficit.
3. Spawn enough new resources in empty cells to restore target count.
4. Randomly assign resource types (A or B) with equal probability.

Capabilities:
* Deterministic replenishment using seeded RNG
* Maintains exact target density after consumption
* Random distribution of both position and resource type
* Interval-based respawn controlled by simulation step logic

Example: 10x10 grid (100 cells), density 0.25 (25 resources target)
- Turn 1: 25 resources, agents collect 4 → 21 remain
- Turn 2: 21 resources, agents collect 4 → 17 remain  
- Turn 3: 17 resources, agents collect 4 → 13 remain, then respawn adds 12 → 25 total
"""
```

---

## snapshot.py (module)
```
"""Simulation snapshot & replay utilities (established Gate 5, unchanged in Gate 6).

Provides a minimal, deterministic serialization of simulation state to
support replay / hash verification tests. Metrics hash itself is not
stored; recomputation during replay should yield identical digests for
the same number of steps when dynamics are deterministic.
"""
```

---

## config.py (module)
```
"""Simulation configuration (Gate 6 integrated; evolved from Gate 5 draft).

Acts as the authoritative parameter bundle for constructing a
deterministic simulation. Factory method `Simulation.from_config` consumes
this dataclass to attach respawn / metrics hooks and seed internal RNG state.

Fields:
* ``grid_size``: (width, height)
* ``initial_resources``: iterable of (x,y[,type]) tuples
* ``perception_radius``: decision scan radius (mirrors constant; may be unified later)
* ``respawn_target_density``: desired occupancy fraction (0..1]
* ``respawn_rate``: fraction of deficit addressed per tick
* ``max_spawn_per_tick``: cap on newly spawned resources each tick
* ``seed``: base RNG seed (drives deterministic respawn & future stochastic systems)

Includes enable flags for respawn / metrics; overlay toggle remains a GUI concern.
"""
```

---

## trade.py (module)
```
"""Trade intent structures (Gate Bilateral1 Phase 2 - Draft Enumeration).

Feature-flagged via environment variable `ECONSIM_TRADE_DRAFT=1`.
No state mutation or economic effect here; provides deterministic intent list
for future execution logic.
"""
```
Inline milestone comments:
```
# One-shot emission flag for micro-delta pruning transparency (Phase 3 instrumentation)
```

---

## constants.py (module)
```
"""Simulation constants (Gate 4).

Centralizes tunable parameters for decision logic & perception.
"""
```

---

## spatial.py
(No module-level docstring present.)

---

# Modernization Targets Summary
Files with historical Gate/Phase references: __init__, agent, grid, world, metrics, respawn, snapshot, config, trade, constants. Consider rephrasing to present tense and relocating historical context into CHANGELOG or architecture docs.

# Next Steps (Optional)
1. Propose updated present-tense docstrings for core modules.
2. Normalize inline milestone comments into a single 'History' or 'Notes' section where still valuable.
3. Add lint/test guard to discourage future Gate/Phase tags in stable code.
