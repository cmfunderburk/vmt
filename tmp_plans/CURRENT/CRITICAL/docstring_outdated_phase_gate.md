# Outdated / Phase/Gate Referencing Docstrings Report

Goal: Identify long docstrings with references to phased/gated implementation stages (Gate X, Phase Y, Unified Selection milestones) that may now be outdated or overly historical. Empty/missing docstrings intentionally ignored.

## Criteria
- Contains terms: Gate, Phase, "Unified Selection", or milestone sub-phases (e.g., Phase 3.1, Gate 5)
- Non-trivial length (multi-line or includes capability/deferral lists)
- Potentially outdated temporal framing versus current stable architecture

---

## simulation/metrics.py (module docstring)
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
Reason: Historical Gate 5/6 integration language; may be simplified to present-tense role.

---

## simulation/config.py (module docstring)
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
Reason: References Gate 5/6 evolution; could be reframed as stable core config API.

---

## simulation/respawn.py (module docstring)
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
Reason: Gate milestone reference; content mostly stable but intro can drop historical phrasing.

---

## simulation/snapshot.py (module docstring)
```
"""Simulation snapshot & replay utilities (established Gate 5, unchanged in Gate 6).

Provides a minimal, deterministic serialization of simulation state to
support replay / hash verification tests. Metrics hash itself is not
stored; recomputation during replay should yield identical digests for
the same number of steps when dynamics are deterministic.
"""
```
Reason: Historical comparison wording ("unchanged in Gate 6").

---

## simulation/constants.py (module docstring)
```
"""Simulation constants (Gate 4).
"""
```
Reason: Gate number only; replace with purpose-centric description.

---

## simulation/__init__.py (module docstring)
```
"""Simulation package.

Deterministic spatial grid + agent model (Gates 3–5) including decision
logic and optional hooks (respawn, metrics) prepared for Gate 6 factory
integration. Deferrals: prices, budgets, pathfinding, multi-resource
optimization heuristics, trading/markets.
"""
```
Reason: Gate staging sequence; could be modernized to present features + future roadmap.

---

## simulation/agent.py (module header comment + lines)
```
"""Agent abstraction (Gate 4+ decision capable).
...
# Perception radius (Manhattan) for decision logic (Gate 4 constant)
"""
```
Reason: Gate-era labels; update to stable semantics.

---

## preferences/base.py (module docstring + class docstring)
```
"""Base Preference interface (Gate 2 foundation).
...
class Preference:
    """Abstract base for all preference types (2-good Gate 2 scope).

    Extension points:
    - Add N-good support ... Gate 3+.
    """
```
Reason: Gate framing; extension notes fine but could decouple from gate numbering.

---

## preferences/perfect_substitutes.py (module docstring)
```
"""Perfect Substitutes preference stub (Gate 2).

Planned utility (future): U(x,y) = a*x + b*y with a,b > 0.
Current Gate 2 scope: parameter schema + NotImplemented utility to keep
focus on core architecture until at least one full implementation is stable.
"""
```
Reason: Historical scope phrasing; may want to reflect current readiness or remove staged wording.

---

## preferences/helpers.py (module docstring)
```
"""Helper utilities for preference-based economic calculations (Gate Bilateral1 Phase 1).

Currently exposes marginal_utility() to support future bilateral trade heuristics.
Design goals:
* Deterministic ordering of returned goods
* Pure function (no mutation of inputs or preference state)
* O(k) where k = number of distinct goods observed (currently fixed 2)
* Zero allocations avoided beyond tiny dict (acceptable scale)

Note: Uses carrying+home aggregate to reflect total wealth context while
trade operations will remain restricted to *carrying* inventory.
"""
```
Reason: Phase label retained; probably can shift to generic educational trade utility context.

---

## gui/_enhanced_trade_visualization.py (module docstring)
```
"""Enhanced Trade Flow Visualization (Educational Phase 2).

Extends existing trade debug overlay with visual indicators, arrows, and educational enhancements.
Maintains performance discipline and feature-flag gating while adding student-friendly visualization.
"""
```
Reason: Phase-specific branding; may prefer feature name only.

---

## preferences/__init__.py (module docstring)
```
"""Preference architecture package (Gate 2 foundation).

- Keep bundle representation minimal (tuple[float, float]) for Gate 2.
"""
```
Reason: Gate 2 mentions; replace with design rationale without milestone tag.

---

## preferences/cobb_douglas.py (module docstring)
```
"""Cobb-Douglas preference implementation (Gate 2).
"""
Reason: Gate tag only.

---

## preferences/leontief.py (module docstring)
```
"""Leontief preference stub (Gate 2).
"""
Reason: Gate tag only; verify if still a stub.

---

## preferences/types.py (module docstring)
```
"""Type aliases and lightweight protocol hints for preferences (Gate 2).
"""
Reason: Gate tag only.

---

## preferences/factory.py (module docstring)
```
"""Preference factory & registry (Gate 2).
"""
Reason: Gate tag only.

---

## gui/debug_logger.py (multiple inline comments & section headers)
Examples:
```
# Trade+Utility bundling buffers (Phase 3.1)
# Phase 3.1: Correlation ID and Causal Chain tracking
# Phase 3.2: Multi-Dimensional Agent Behavior Aggregation
# ---------------- Phase 3 Event Builder Helpers -----------------
```
Reason: Inline phase references throughout; consider consolidating into a single module-level explanation.

---

## tools/launcher/framework/debug_orchestrator.py (module docstring & comments)
```
... future enhancements (like Phase 3.2 behavior tracking, Phase 3.4 event clustering, etc.) ...
# Set initial environment for Phase 1 (both enabled)
# This ensures Phase 3.2 behavior tracking, Phase 3.4 clustering, etc. work automatically
```
Reason: Phase milestone scheduling persists in comments; may now be stable features.

---

## tools/launcher/framework/ui_components.py (phase mapping)
```
1: "Phase 1: Both enabled"
2: "Phase 2: Foraging only"
3: "Phase 3: Exchange only"
```
Reason: User-facing labels—determine if still pedagogically needed or should be renamed to neutral scenario labels.

---

## simulation/metrics.py (field comments)
```
# Bilateral2 Phase 1 additions (hash-excluded):
fairness_round: int = 0  # Phase 3: increments per executed trade (advisory, hash-excluded)
```
Reason: Embedded phase annotations in dataclass fields.

---

## simulation/agent.py (inline)
```
# Perception radius (Manhattan) for decision logic (Gate 4 constant)
```
Reason: Historical constant provenance; could simplify.

---

# Summary
Total flagged docstring/inline documentation locations: 23
Primary modernization need: Remove or rephrase historical Gate/Phase chronology in stable components; consolidate phase-specific inline comments into higher-level present-tense design notes.

# Next Suggested Actions
1. Prioritize module-level docstrings in core simulation (`simulation/*.py`) for modernization.
2. Decide whether educational phase terminology remains part of public pedagogy (e.g., launcher UI) before removal.
3. Convert repeated Phase 3.x inline comments in `gui/debug_logger.py` into a single enumerated capability list.
4. Standardize preference module docstrings to describe economic form & purpose sans Gate tags.
5. Add a brief CONTRIBUTING note about avoiding historical milestone tags in future docstrings.
