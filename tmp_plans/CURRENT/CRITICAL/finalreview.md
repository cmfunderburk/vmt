Here's a focused review of your Agent refactor plan: what's solid, what's underspecified, and where hidden risk still lives before you start cutting code.

**Last Updated**: October 2, 2025  
**Status**: Updated with decisions from `pre_implementation_decisions.md`

## ✅ Strengths (Keep As-Is)
- Phased sequencing is sensible: low‑risk extraction → structural decomposition → higher abstraction (state machine / commands).
- Clear success criteria (hash stability, perf envelope, LOC reduction).
- Component boundaries (movement, inventory, trading partner, target selection) align with real cohesion splits already implied in the monolith.
- Testing structure anticipates both unit + regression layers (good forward stance).
- Event emitter abstraction is directionally correct (removes ad hoc emission clutter).

## ⚠️ Critical Gaps / Ambiguities (Needs Clarification Before Start)

### 1. Determinism & Hash Stability ✅ RESOLVED
**Temporary Refactor Policy – Deferred Baseline Enforcement**: We are *intentionally deferring strict determinism hash parity checks* until the full Agent refactor (all phases) is complete. Interim component extractions may legitimately reorder internal attributes or introduce structural wrappers that would cause transient hash drift. During Phases 1–3:
  - We will still record observed hashes for reference (capture after each phase), but **CI will not fail** on hash mismatch.
  - Any unexpected *behavioral* divergence (different event sequences, resource counts, trade counts) still blocks merges.
  - No new hash fields or metrics are to be added unless clearly marked "EXCLUDED FROM FINAL HASH" in code comments.
  - After Phase 3 completion, we will run a stabilization pass to (a) re‑generate `baselines/determinism_hashes.json`, (b) document rationale for any intentional differences, and (c) re‑enable strict hash gating.
  - If a bug fix requires immediate baseline change mid‑refactor, we create a focused PR labeled `determinism:update-pre-refactor` with justification.

This policy reduces refactor friction while preserving traceability: we differentiate *structural* vs *behavioral* changes and only lock the structural view once composition boundaries settle.

**RESOLVED** → See `pre_implementation_decisions.md` Section 2:
- ✅ **Explicit Hash Contract**: Whitelist of participating fields defined (spatial, inventory, mode, trading state, identity)
- ✅ **Component Nesting Rules**: Aliases preserve hash surface; components don't add hash fields
- ✅ **Serialization Strategy**: Flatten component state (Section 6 of pre_implementation_decisions.md)
- ✅ **Hash Calculation Reference**: Implementation provided with optional field handling
- ⚠️ **Movement/Selection Ordering**: Legacy tie-break validation via test fixture baseline comparison (Phase 1 testing)
- ⚠️ **Import Order Determinism**: Rule established - feature/config resolution only at construction time (to validate during implementation)

### 2. Backward Compatibility Surface ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Sections 1, 4:
- ✅ **Inventory Mutation Invariant**: Strict in-place mutation contract documented (Section 4)
  - Components MUST mutate dicts in place; NEVER rebind `self.carrying` or `self.home_inventory`
  - Identity preservation tests added to validation criteria
  - Code review checklist provided
- ✅ **Mode Management Strategy**: Hybrid approach chosen (Section 1)
  - `agent.mode` remains single source of truth (external field)
  - `AgentModeStateMachine` validates transitions and emits events (does not own state)
  - State machine mirrors `agent.mode` but doesn't own it
- ⚠️ **API Audit**: Planned as immediate pre-Phase 1 artifact
  - Generate public Agent methods/attributes list
  - Freeze in `docs/agent_public_api_freeze.md`
  - Use for compatibility validation throughout refactor

### 3. Event Emission Path Consistency
**Resolved Policy (Pre‑implementation Decision)**
1. **Single Emission Path**: All agent‑origin events (mode changes, resource collection, trade intent / execution, pairing lifecycle, inventory deposits/withdrawals, movement) MUST be enqueued into the `StepEventBuffer` first; only the buffer’s `end_step()` flush may call `ObserverRegistry.notify()`. *No direct observer logger or direct registry calls inside agent components.*
2. **Movement Batching**: Per step, each agent emits at most one `MovementSummaryEvent` (old_pos → new_pos). Intermediate tile hops are not individually logged. If position unchanged, no movement event is produced.
3. **Ordering Determinism**: Movement summaries are appended after movement logic completes but before any later phase (e.g., collection/trading) emits dependent events, preserving: `mode / pairing changes` (if triggered at start) → `movement summaries` → `collection` → `trade` → `post-step metrics` sequence. Within a step, agent ordering = original agent list order.
4. **Performance Constraint**: Movement batching target overhead <0.2% of per-step time (validated via micro benchmark after Phase 1.1). Data stored transiently as `(agent_id, old_x, old_y, new_x, new_y)` tuples; conversion to event objects deferred until flush.
5. **EventEmitter API Adjustment**: `emit_movement` becomes `queue_movement_summary(old_pos, new_pos)` → delegates to `StepEventBuffer.queue_movement_summary(...)`. No global observer logger pathway retained.
6. **Failure Isolation**: Any exception during summary construction is trapped and logged once; failure to create a movement summary must not suppress subsequent (collection/trade) events.
7. **Future Extension Point**: If path reconstruction is later needed, optional debug flag `ECONSIM_DEBUG_PATHS` may switch summary payload from displacement to hop list; default remains minimal displacement.

#### 3.1 Hybrid Observability Strategy (FINAL DECISION)
Adopt **Hybrid Model (Option 3)**: Semantic, *decision-bearing* events continue to flow through observers; purely *mechanical* changes are reconstructible from `StepDelta` and only elevated to log lines when explicitly requested.

| Category | Source of Truth | Always Emitted Event? | Reconstructible from StepDelta? | Notes |
|----------|-----------------|-----------------------|----------------------------------|-------|
| Mode change | Observer event (`AgentModeChangeEvent`) | Yes | Yes (mode delta) | Semantic reason preserved only in event (reason string) |
| Pairing start/end | Observer events | Yes | Partial (partner ids) | Cooldown / meeting point reasoned in event |
| Trade execution | Observer event (`TradeExecutionEvent`) | Yes (max 1) | Yes (executed_trade) | Diagnostic fields (ΔU, parity) only in event |
| Resource collection | Observer event (`ResourceCollectionEvent`) | Yes | Yes (inventory/resource despawn) | Keep for educational trace |
| Movement summary | Buffered event OR derived | Yes (1 per agent if moved) | Yes (agent_position_changes) | Event kept minimal; StepDelta has full coordinates |
| Inventory deltas | StepDelta | No | Yes (inventory/home deltas) | Only surfaced if expansion flag enabled |
| Spawn/Despawn | StepDelta | No | Yes (resource_spawns / despawns) | Optional expansion lines |
| Rollback | Observer meta event (`RollbackEvent`) | Yes | Yes (implicit via applied inverse) | Not expanded into per-delta events unless debug flag set |

**Environment Flags**:
* `ECONSIM_DEBUG_EXPAND_DELTAS=1` – After flush, generate synthetic debug lines from latest `StepDelta` for mechanical categories (inventory adjustments, resource spawn/despawn). Default: off.
* `ECONSIM_DEBUG_ROLLBACK_EVENTS=1` – Emit granular restoration lines (position revert, inventory revert) during rollback. Default: off (only summary RollbackEvent).

**Expansion Order (when enabled)**: movement summary (already an event) → inventory deltas → resource despawns → resource spawns (mirrors inverse rollback ordering for cognitive consistency). All synthetic lines are tagged category=META/DELTA and excluded from determinism hashing.

**Rationale**:
* Reduces event volume & memory while preserving semantic clarity for UI and educational observers.
* Keeps rollback and replay minimal: only need `StepDelta` ring + semantic event stream; delta expansion is *derived*, never authoritative.
* Avoids bloating `StepDelta` with narrative reasoning fields (those remain in semantic events only, preventing duplication).

**Implementation Tasks**:
1. Add `DeltaExpander` utility invoked post `event_buffer.end_step()` iff flag enabled.
2. Tag synthetic lines distinctly (`category="DELTA"`).
3. Update observer docs & structured logging filters to ignore DELTA by default.
4. Add tests:
  * `test_delta_expansion_disabled_default` – no synthetic lines.
  * `test_delta_expansion_enabled_includes_inventory_change`.
  * `test_delta_expansion_does_not_affect_hash` (hash unchanged with/without flag).
5. Ensure movement summary duplication avoided: if movement event present, expansion does not re-emit.

**Failure Modes & Guards**:
* If expansion raises, swallow with single warning; never block step loop.
* Assert (dev mode) that every synthetic line maps to an existing delta tuple (no orphan generation).
* Guarantee ordering stable by constructing a single list in defined sequence before emission.

**Future Extensibility**: Additional mechanical categories (e.g., future energy system) extend `StepDelta` and expansion logic without altering observer event contract.

### 4. Trading Partner Component ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Section 3:
- ✅ **State Transition Table**: Complete table with 6 events documented
  - Pairing initiation, meeting point arrival, trade execution, session end (normal/stagnation), pairing rejection
  - All state changes, cooldowns, and ordering rules explicitly defined
- ✅ **Tie-Break Ordering**: Lower `agent.id` initiates pairing (processes partner state first)
- ✅ **Cooldown Management**: Two-tier system defined
  - General cooldown: 3 steps after any pairing ends
  - Per-partner cooldown: 20 steps after session with specific partner
- ✅ **Edge Cases**: Documented and resolved
  - Simultaneous unpair: deterministic ordering (lower ID first), atomic mutual operations
  - Unreachable meeting point: stagnation timer ends session
  - No death/respawn mechanics (not implemented in current system)
- ✅ **Pairing Algorithm**: Detailed implementation with deterministic midpoint calculation provided

### 5. Target Selection Strategies

#### 5.1 Canonical Per‑Turn Decision Flow (Flag Matrix)
Let FORAGE = `ECONSIM_FORAGE_ENABLED == 1`; EXCHANGE = trading fully enabled (both `ECONSIM_TRADE_DRAFT==1` AND `ECONSIM_TRADE_EXEC==1`). Draft without execution is treated as EXCHANGE disabled for behavior selection (enumeration-only mode yields no pairing actions).

Case A: FORAGE=ON, EXCHANGE=ON
```
if inventory empty:
  forage until at least one good held (skip trade pairing evaluation)
scan perception radius (resources + agents)
if no agents AND no resources:
  path toward home (idle if already there)
else:
  evaluate bilateral trade pairing opportunities using distance‑discounted utility (discount factor uses half distance to reflect meeting point: ΔU_adj = ΔU_raw / (1 + 0.5 * d))
  if exists mutually positive pairing (both agents gain from >=1 potential 1‑for‑1 swap):
    establish pairing → compute meeting point (midpoint) → move toward meeting point
    once co-located at meeting point:
      perform at most ONE 1‑for‑1 exchange per step iff trade increases utility for both (individually rational)
      repeat in subsequent steps until no individually rational trade remains
    conclude pairing (cooldowns applied)
  else:
    forage: select best resource target via unified selection algorithm
    if no resource target available after scan: path toward home
```

Case B: FORAGE=ON, EXCHANGE=OFF
```
scan perception radius (resources only)
if resources found:
  pick highest distance‑discounted utility target
  path one step toward target; collect if arrived
else:
  path toward home (idle if already there)
repeat
```

Case C: FORAGE=OFF, EXCHANGE=ON
```
if carrying inventory empty:
  if home inventory non‑empty: return home & withdraw all; continue
  else: return home & idle (waiting state)
scan perception radius (agents only)
if candidate agent(s) found:
  evaluate pairing (same algorithm as Case A)
  proceed with meeting point movement & limited 1‑for‑1 execution
else:
  path toward home (idle if already there)
```

Case D: FORAGE=OFF, EXCHANGE=OFF
```
return home
deposit any carried goods (single bulk deposit action)
idle thereafter
```

Gating Rule (Inventory Priming): In Case A the agent MUST hold at least one unit before entering pairing evaluation to avoid degenerately offering zero-goods trades; this short‑circuits to pure foraging until inventory non‑empty.

#### 5.2 Deterministic Candidate & Pairing Ordering
All resource candidate evaluations and trade pairing evaluations MUST use the canonical priority tuple:
```
(-ΔU_adj, distance, x, y)
```
Where:
* `ΔU_adj` = adjusted utility gain after distance discount. For resource targeting: `ΔU_adj = ΔU_raw / (1 + k * d^2)` (existing unified selection rule). For pairing: use half-distance discount: `ΔU_pair = ΔU_raw / (1 + 0.5 * d)` because agents meet halfway.
* `distance` = Manhattan distance from agent to candidate (or to meeting point for pairing evaluation)
* `(x, y)` = candidate coordinates (or chosen meeting point) as deterministic spatial tiebreakers

Trade intent execution ordering (when multiple viable pair trades exist) continues to follow existing rule (already established elsewhere):
```
(-ΔU_trade, seller_id, buyer_id, give_type, take_type)
```
Only one trade may execute per step.

#### 5.3 Strategy Interface Contract
Each active strategy implementation (initially `ResourceTargetStrategy` and conditional `PartnerPairingStrategy`) MUST return a structured result. (Leontief prospecting is **removed/deferred**—see 5.6.)
```python
@dataclass
class TargetCandidate:
  position: tuple[int,int]
  delta_u_raw: float
  distance: int
  kind: Literal['resource','prospect','pairing']
  aux: dict[str, Any]  # optional metadata (e.g., resource_type, partner_id)
```
Central selector applies discounting + canonical priority tuple; strategies **must not** pre‑embed tie‑break ordering to avoid drift.

#### 5.4 Resource Iteration Determinism
All strategy resource scans MUST iterate via `grid.iter_resources_sorted()`; if unavailable, wrapper enforces sorted fallback:
```python
iterator = getattr(grid, 'iter_resources_sorted', None) or _sorted_wrapper(grid.iter_resources())
```
Add assertion in dev mode: `assert is_sorted_by_xyz(iterator)` (stripped in production) to catch regressions early.

#### 5.5 Strategy Registration / Extension Seam
Introduce a deterministic registry (ordered list) built once per Agent instantiation:
```python
self._strategies = [
  ResourceTargetStrategy(),
  # PartnerPairingStrategy inserted conditionally if EXCHANGE enabled
]
```
Ordering is explicit; no dynamic discovery, no reliance on module import order. Future extensions append at end or insert with a documented migration note. Registry creation MUST NOT depend on runtime RNG or unordered dict iteration.

#### 5.6 Prospecting (Leontief) Status – Removal / Rework Plan
The prior “Leontief prospecting” heuristic (complementary bundle scouting) is being **removed for this refactor cycle** due to:
* Low incremental pedagogical value vs standard resource targeting.
* Added complexity in caching + special scoring path that increased maintenance surface.
* Risk of silent divergence from unified tie‑break contract.

Refactor Actions:
1. Delete/skip any `LeontiefProspectingStrategy` class or prospect cache helpers (do not stub; eliminate imports to avoid dead code drift).
2. Remove tests that assert prospecting‑specific behavior; replace with a single regression asserting Leontief preference types still function via generic resource targeting.
3. Ensure Leontief agents now use the same unified resource targeting (distance‑discounted utility) without a special second pass.
4. If future re‑introduction is desired, re‑add behind feature flag `ECONSIM_LEONTIEF_PROSPECT_V2=1` with clear performance/educational justification.

Behavioral Expectation Post‑Removal:
* Leontief agents may collect slightly more unbalanced bundles early; overall utility convergence remains deterministic and hash impact acceptable (hash gating deferred until stabilization phase; see Section 1 policy).
* No change to ordering or selection tuple; all candidates flow through the same pipeline.

Documentation / Commit Message Template:
```
agent: remove leontief prospecting path (simplify selection pipeline, hash deferred)
Rationale: reduces code paths & maintenance; no educational regression expected. Future reinstate requires flag + micro benchmark.
```

Risk Mitigation:
* Add a short-lived comparison script (optional) to confirm aggregate utility trajectory (mean over 50 steps) for Leontief agents stays within historical variance.
* If removal exposes latent dependency, abort and reintroduce a minimal no-op stub raising clear error.

#### 5.7 Failure & Fallback Behavior
If all strategies yield no candidate (empty list), agent enters fallback path toward home (or idle if already there) per flag matrix case logic.

#### 5.8 Testing Additions (Augment Section 8 References)
* Test canonical ordering: ensure two candidates with identical adjusted utility and distance order strictly by `(x,y)`.
* Test pairing discount vs resource discount (half distance vs quadratic term) does not invert previously established resource preferences when EXCHANGE disabled.
* Test registry stability: hash of strategy class names list remains unchanged across runs.
* Test Leontief prospect candidate integrates seamlessly with same tie‑break pipeline.

#### 5.9 Performance Guardrail Specific to Strategies
Micro benchmark target: full candidate evaluation (12x12 grid, perception radius default) < 0.15 ms median per agent on baseline hardware; pairing evaluation adds ≤ 25% overhead vs resource-only mode.

### 6. Command Pattern & Step Rollback Strategy (UPDATED)

**Change in Assumption**: We now explicitly intend to support limited step rollback / rewind (educational “scrub backwards a few steps” feature). Previous prohibition on rollback is **deprecated** and should be treated as stale documentation.

#### 6.1 Rollback Scope & Goals
| Aspect | Target |
|--------|--------|
| Depth | Configurable ring buffer of last N steps (default 50; hard cap 500) |
| Granularity | Whole-step atomic rollback (no mid-step partial) |
| Determinism | Replaying from seed + recorded deltas must reproduce identical hashes post-stabilization phase |
| Overhead | <3% additional per-step time; <1.5 KB average delta footprint per step (typical small scenario) |
| Memory Bound | Ring buffer size * avg delta size (e.g. 50 * 1.5 KB ≈ 75 KB) |
| API | `simulation.rollback(steps=1)` returning new current step index |

#### 6.2 Why NOT Full Command Objects
Rollback requires *state deltas*, not necessarily reversible per-action objects. A full Command pattern adds allocation & indirection cost for every micro action (move, collect, trade) while we only need the net effect per simulation step. Command objects also encourage premature “undo” semantics at the action level (e.g. un-applying a movement) whereas our architecture treats the **step** as the atomic deterministic unit.

#### 6.3 Chosen Design: StepDelta Log
Each committed step appends a compact `StepDelta` record containing only mutated facts:
```python
@dataclass(slots=True)
class StepDelta:
  step_number: int
  agent_position_changes: list[tuple[int, int, int, int, int]]  # (agent_id, old_x, old_y, new_x, new_y)
  agent_mode_changes: list[tuple[int, str, str]]                # (agent_id, old_mode, new_mode)
  inventory_deltas: list[tuple[int, str, int]]                  # (agent_id, good_name, delta_qty)
  home_inventory_deltas: list[tuple[int, str, int]]             # same schema
  resource_spawns: list[tuple[int, int, str]]                   # (x,y,type)
  resource_despawns: list[tuple[int, int, str]]                 # (x,y,type)
  executed_trade: tuple[int, int, str, str] | None              # (seller_id,buyer_id,give_type,take_type)
  rng_step_seed: int                                            # seed used for that step (derived)
```
Inverse application rules are deterministic and linear (apply lists in reverse order for rollback). No arbitrary user-defined logic required.

#### 6.4 RNG Strategy for Rewind Safety
Adopt **per-step deterministic sub-seeding**: `step_rng_seed = base_seed ^ (step_number * 0x9E3779B97F4A7C15)`. On rollback we restore `current_step` and re-derive the seed; no need to snapshot RNG internal state. This eliminates hidden divergence if rollback chain applied repeatedly.

#### 6.5 Rollback Algorithm (High-Level)
```
def rollback(k):
  assert 0 < k <= len(delta_ring)
  for _ in range(k):
    delta = delta_ring.pop()          # last StepDelta
    apply_inverse(delta)              # reverse mutations
    current_step = delta.step_number - 1
  recompute_cached_metrics_if_needed()
```
`apply_inverse` processes deltas in this order for safety:
1. Trades (re-credit goods) if present
2. Inventory/home deltas (negate quantities)
3. Resource spawns → despawn; resource despawns → respawn
4. Agent positions (revert coordinates)
5. Agent modes (restore old modes) – emit a synthetic rollback mode event only if educational logging enabled

#### 6.6 Interaction with Event Buffer
Events themselves are *not* “undone” historically; on rollback we emit a single `RollbackEvent(step_from=X, step_to=Y, count=k)` for observability. Reconstructing past event streams is out of scope (costly & rarely pedagogically necessary). This keeps rollback cheap and clear that history has branched.

#### 6.7 Determinism Considerations
| Potential Drift Source | Mitigation |
|------------------------|-----------|
| Component internal caches | Recompute or clear caches on rollback (movement / selection have no persistent cache post-refactor) |
| Mode transition side effects | Record old/new mode; revert directly without re-running decision logic |
| Trade cooldown / partner state | Extend `StepDelta` with partner cooldown adjustments if any change; reverse numerically |
| RNG consumption differences | Per-step sub-seeding ensures identical future draws after rewind |

#### 6.8 Why Command Pattern Still Deferred
| Need | StepDelta Satisfies? | Command Needed? |
|------|----------------------|-----------------|
| Step rewind (N recent) | Yes | No |
| Action-level undo mid-step | Not in scope | Would require commands |
| External script injection | Future—can wrap after selection stage | Maybe later |
| Branch exploration (what-if) | Can clone sim + replay deltas | Not yet |

#### 6.9 Minimal Extension Hook (Future-Proofing)
Expose an optional post-step callback:
```python
def on_step_committed(step_number: int, delta: StepDelta) -> None: ...
```
Allows future persistence or streaming without entangling the core loop with command abstractions.

#### 6.10 Test Plan Additions for Rollback
1. `test_rollback_single_step_positions_inventory`
2. `test_rollback_multiple_steps_trade_state`
3. `test_rollback_rerun_hash_equivalence` (hash gating deferred; store observed hash & ensure rerun after rollback+forward equals same value provisional)
4. `test_rollback_mode_restoration`
5. `test_rollback_rng_repeatability` (collect first N random choices, rollback, re-run, assert identical sequence)

#### 6.11 Performance Guardrail Measurement
Add micro benchmark capturing: baseline step time vs step+delta logging vs step+rollback sequence (rollback 10 steps) – ensure overhead <3% and rollback cost < (N * 0.5 * baseline_step_time).

#### 6.12 Documentation / Commit Template
```
agent: introduce StepDelta log & rollback ring (command pattern deferred)
Implements limited N-step rewind with per-step deterministic sub-seeding. No action-level commands; minimal overhead (<3% target). Future extensibility via on_step_committed hook.
```

**Decision**: Proceed with StepDelta-based rollback; defer full Command pattern until a concrete feature (script injection / multi-action scheduling) demands it.

### 7. Performance Guardrails ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Section 5:
- ✅ **Policy Clarified**: Performance tests are **strictly informational**, do NOT block merges
  - CI passes regardless of performance changes
  - Developer triggers action only if explicitly concerned
  - Otherwise, assume performance is acceptable
- ✅ **Measurement Protocol**: 5-sample median with 2% observation threshold
  - 1 warmup run (discarded)
  - 5 measurement runs
  - Median used for comparison
  - Threshold breach generates informational report only
- ✅ **Micro-Benchmarks**: Targets defined for all components
  - Movement: <0.5µs per move
  - Inventory: <1.0µs per operation
  - Target selection: <150µs per scan (12x12 grid)
  - All targets are informational guidelines, not pass/fail criteria

### 8. Testing Plan Gaps ⚠️ PARTIALLY RESOLVED
**RESOLVED**:
- ✅ **Mutation Safety Tests**: Planned in `pre_implementation_decisions.md` Section 4
  - Identity preservation tests for inventory dicts
  - Visibility tests for mutations through aliases
  - Code review checklist for inventory methods

**REMAINING**:
- ⚠️ **Behavioral Equivalence Oracle**: Need to define canonical event sequences
  - Which test scenarios produce reference event logs?
  - How to capture and compare (MD5 hash of event stream)?
  - Add targeted fixture for event log validation
- ⚠️ **Determinism API**: Verify `sim.get_determinism_hash()` exists or use correct API
  - Check if it's `metrics_collector.get_hash()` or similar
  - Document actual hash extraction method
- ⚠️ **Phase Gating for Tests**: Decide approach for tests depending on unimplemented modules
  - Option A: Add tests only when implementing (cleaner CI)
  - Option B: Create empty shims + failing TODO tests early (visible roadmap)

### 9. Serialization / Snapshot / Replay ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Section 6:
- ✅ **Strategy Chosen**: Flatten component state (no format versioning yet)
  - Component nesting is internal implementation detail
  - Snapshot format unchanged from pre-refactor
  - Components NOT serialized; only their data via exposed aliases
- ✅ **Compatibility Test**: Planned in validation criteria
  - Pre-refactor snapshot → load with post-refactor code
  - Run forward N steps and verify hash equivalence
  - Round-trip test: serialize → deserialize → verify state
- ✅ **Future Migration Path**: Versioning strategy documented if later needed
  - But deferred until concrete need emerges

### 10. Incremental Merge Strategy
- Plan assumes long-lived branch. Recommend per-phase PRs with locked baseline comparison:
  - Phase 1 PR: movement + emitter + utility (hash stable)
  - Phase 2 PRa: inventory (hash stable)
  - Phase 2 PRb: trading partner (hash stable)
  - Phase 2 PRc: selection strategies (possible hash change? Pre-approve)
  - Phase 3 PR: state machine + (optional) commands (hash stable)
- Define “permit hash change?” decision tree (only if bug fix + new test covers it).

### 11. Feature Flag / Toggle Strategy ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Section 7:
- ✅ **Naming Scheme**: Per-component pattern `ECONSIM_AGENT_<COMPONENT>_REFACTOR=<0|1>`
  - `ECONSIM_AGENT_MOVEMENT_REFACTOR`
  - `ECONSIM_AGENT_INVENTORY_REFACTOR`
  - `ECONSIM_AGENT_TRADING_REFACTOR`
  - `ECONSIM_AGENT_SELECTION_REFACTOR`
  - `ECONSIM_AGENT_STATE_MACHINE_REFACTOR`
  - `ECONSIM_AGENT_COMMANDS_REFACTOR` (optional)
- ✅ **Accelerated Rollout**: **1-day testing per flag** before removal
  - Day 1: Implement with flag=0
  - Day 2: Enable flag=1, full test suite validation
  - Day 3: Remove flag + delete legacy code path
- ✅ **Rationale**: Minimize technical debt from flag proliferation
  - Flags are temporary rollback safety nets only
  - Not long-term configuration
- ✅ **Implementation**: `agent_flags.py` module with `get_refactor_flags()` and `is_refactor_enabled()` helpers

### 12. Logging & Observability Integration ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Section 8:
- ✅ **Rule Established**: "No print(), no direct GUI logs; only observer or structured logger"
- ✅ **Event Emission Philosophy**: Components use `AgentEventEmitter` for all events
- ✅ **Error Handling**: Event emission failures swallowed with single warning (non-critical)

### 13. Mode Enumeration Completeness ⚠️ TO VALIDATE
**TO VALIDATE** → See `pre_implementation_decisions.md` Section 1:
- ✅ **Valid Transitions Defined**: FORAGE, RETURN_HOME, IDLE, MOVE_TO_PARTNER
- ⚠️ **Current AgentMode Enum**: Need to validate against existing enum during Phase 1
  - Confirm no trading-specific modes missing (e.g., TRADING state)
  - Ensure transition map covers all existing mode paths
  - Add invalid transition test with debug logging

### 14. Error Handling Philosophy ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Section 8:
- ✅ **Principle**: Components raise exceptions; only outer step loop swallows
- ✅ **Exception**: Event emission failures swallowed with single warning (non-critical)
- ✅ **Pattern Examples**: Provided for components, agent methods, and step executor

### 15. Naming & Package Layout ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Section 8:
- ✅ **Consistent Subpackage Structure**: All components get subpackages
  - `components/movement/` with `core.py` and `utils.py`
  - `components/inventory/` with `core.py`
  - `components/trading_partner/` with `core.py`
  - `components/target_selection/` with base, resource_selection, unified_selection
  - Leontief prospecting REMOVED per Section 5.6
- ✅ **Exports**: Each subpackage `__init__.py` exports main classes and utilities

### 16. Dependency Direction Rules ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Section 8:
- ✅ **Rule 1**: TYPE_CHECKING for Agent references in components (no runtime imports)
- ✅ **Rule 2**: No circular instantiation (components instantiated BY agent only)
- ✅ **Rule 3**: Late local imports for optional dependencies
- ✅ **Examples Provided**: Code patterns for each rule

### 17. Utility Duplication Risks ✅ RESOLVED
**RESOLVED** → See `pre_implementation_decisions.md` Section 8:
- ✅ **Canonical Location**: `src/econsim/simulation/utils/spatial.py`
- ✅ **Functions Centralized**: `manhattan_distance()`, `calculate_meeting_point()`
- ✅ **Migration Plan**: Remove duplicates from `grid.py`, `agent.py` after refactor

### 18. Prospecting Performance Claims ✅ N/A (Leontief Removal)
**NOT APPLICABLE** → Per Section 5.6, Leontief prospecting is being **removed** for this refactor cycle.
- ✅ **Decision**: Remove prospecting path entirely (no benchmark needed)
- ✅ **Rationale**: Low pedagogical value, maintenance burden, tie-break divergence risk
- ✅ **Future**: Re-add behind `ECONSIM_LEONTIEF_PROSPECT_V2` flag if needed with clear justification

## 🔁 Pre‑Implementation Additions Status

| Area | Action | Status |
|------|--------|--------|
| Determinism spec | Add determinism contract doc listing hash fields + tie-break rules | ✅ COMPLETE (Section 2 of pre_implementation_decisions.md) |
| API audit | Generate public Agent attributes/methods and freeze in `docs/agent_public_api.md` | ⚠️ PLANNED (immediate artifact before Phase 1) |
| Toggle strategy | Document feature flags + removal plan | ✅ COMPLETE (Section 7 of pre_implementation_decisions.md) |
| Serialization | Decide snapshot strategy & add test | ✅ COMPLETE (Section 6 of pre_implementation_decisions.md) |
| Event routing | Formalize event emission path | ✅ COMPLETE (Section 3 already documented) |
| Performance harness | Add micro benchmarks | ✅ COMPLETE (Section 5 of pre_implementation_decisions.md) |
| State machine | Align transition map + invalid transition test | ✅ COMPLETE (Section 1 of pre_implementation_decisions.md) |
| Commands (optional) | Justify or defer | ✅ DEFERRED (StepDelta-based rollback chosen, commands defer to Phase 4+) |

## 🧪 Extra Tests Worth Adding

| Test | Status | Notes |
|------|--------|-------|
| 1. Hash equivalence (pre/post refactor, 50 steps, 3 seeds) | ⚠️ PLANNED | Add during Phase 1 validation |
| 2. Attribute alias identity (`id(agent.carrying)` unchanged) | ✅ SPECIFIED | Section 4 of pre_implementation_decisions.md |
| 3. Pairing determinism (lowest ID initiator) | ✅ SPECIFIED | Section 3 of pre_implementation_decisions.md |
| 4. Mode transition rejection (invalid transitions) | ✅ SPECIFIED | Section 1 of pre_implementation_decisions.md |
| 5. Leontief prospecting tie-break | ✅ N/A | Prospecting removed per Section 5.6 |
| 6. Inventory utility epsilon path (zero handling) | ⚠️ GOOD ADDITION | Add to Phase 2.1 inventory tests |

## 🚫 Deferred Items (Per Pre-Implementation Decisions)

| Item | Status | Rationale |
|------|--------|-----------|
| Command pattern | ✅ DEFERRED to Phase 4+ | StepDelta-based rollback satisfies rewind needs; commands not needed until script injection/multi-action scheduling |
| Full property delegation for mode | ✅ DEFERRED to Phase 3 (optional) | Hybrid approach (agent.mode authoritative) sufficient for Phases 1-2; can evolve later if valuable |
| Snapshot format versioning | ✅ DEFERRED | Flatten strategy works; versioning only if future concrete need emerges |
| Leontief prospecting | ✅ REMOVED | Not deferred, fully removed; reinstate behind flag if needed with justification |

## 🩹 Risk Hotspots (Monitor During Implementation)

| Risk | Trigger | Mitigation | Status |
|------|---------|------------|--------|
| Silent hash drift | Adding nested dataclasses | ✅ Hash contract documented; flatten serialization; components don't add hash fields | MITIGATED |
| Performance regression | Extra indirection layers | ✅ Informational monitoring only; non-blocking | POLICY SET |
| Attribute alias breakage | Accidental dict rebinding | ✅ Strict in-place mutation contract; identity tests; code review checklist | MITIGATED |
| Event ordering change | Mixed emitter pathways | ✅ Single emission via StepEventBuffer; AgentEventEmitter abstraction | RESOLVED |
| Circular imports | Strategy/partner importing Agent | ✅ TYPE_CHECKING rules; no runtime imports; late local imports | MITIGATED |

## ✅ Final Pre-Phase 1 Checklist

| Item | Status | Reference |
|------|--------|-----------|
| 1. Determinism contract doc | ✅ COMPLETE | Section 2 of pre_implementation_decisions.md |
| 2. API symbol freeze list for `Agent` | ⚠️ TO CREATE | Immediate artifact (use grep/codebase_search) |
| 3. Event emission pathway | ✅ COMPLETE | Section 3 (already documented) |
| 4. Commands decision | ✅ DEFERRED | StepDelta rollback chosen; commands to Phase 4+ |
| 5. Snapshot/serialization stance | ✅ COMPLETE | Section 6 of pre_implementation_decisions.md |
| 6. Mode management strategy | ✅ COMPLETE | Section 1 of pre_implementation_decisions.md (hybrid approach) |
| 7. Trading partner cooldowns | ✅ COMPLETE | Section 3 of pre_implementation_decisions.md |
| 8. Performance protocol | ✅ COMPLETE | Section 5 of pre_implementation_decisions.md (informational only) |
| 9. Feature flag naming/rollout | ✅ COMPLETE | Section 7 of pre_implementation_decisions.md (1-day testing) |
| 10. Package layout | ✅ COMPLETE | Section 8 of pre_implementation_decisions.md |

## 🚦 Remaining Gaps Before Implementation

### Critical (Must Resolve)
1. **API Audit** (⚠️): Generate and freeze public Agent API before Phase 1
   - Action: Run grep for public methods/attributes
   - Document in `docs/agent_public_api_freeze.md`
   - Estimated time: 30 minutes

### Important (Validate During Phase 1)
2. **AgentMode Enum Completeness** (⚠️): Validate against existing implementation
   - Confirm FORAGE, RETURN_HOME, IDLE, MOVE_TO_PARTNER cover all cases
   - Check for any TRADING or other states in current code
   - Estimated time: 15 minutes during Phase 1 setup

3. **Determinism Hash API** (⚠️): Verify correct method name
   - Check if `sim.get_determinism_hash()` exists or use alternative
   - Document actual API in test templates
   - Estimated time: 5 minutes

4. **Behavioral Equivalence Oracle** (⚠️): Define for regression testing
   - Select 2-3 canonical test scenarios
   - Capture event sequence MD5 hashes
   - Add fixture for event log validation
   - Estimated time: 1 hour during Phase 1 testing

### Optional (Can Defer)
5. **Phase Gating for Tests**: Decide shims vs just-in-time test addition
   - Recommendation: Just-in-time (add tests when implementing) for cleaner CI
   - Can revisit if roadmap visibility becomes issue

## 📝 Summary

**Overall Status**: **95% Ready for Implementation**

**Resolved**: 18 critical gaps/ambiguities addressed in `pre_implementation_decisions.md`

**Remaining**: 4 items (1 critical, 3 important validations)

**Recommended Next Action**: 
1. Generate Agent API freeze document (30 min)
2. Proceed to Phase 1 implementation
3. Validate remaining items during Phase 1 setup/testing

**Document Cross-Reference**: All major decisions now live in `pre_implementation_decisions.md` with this document serving as a resolved/remaining status tracker.