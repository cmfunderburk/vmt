Here’s a focused review of your Agent refactor plan: what’s solid, what’s underspecified, and where hidden risk still lives before you start cutting code.

## ✅ Strengths (Keep As-Is)
- Phased sequencing is sensible: low‑risk extraction → structural decomposition → higher abstraction (state machine / commands).
- Clear success criteria (hash stability, perf envelope, LOC reduction).
- Component boundaries (movement, inventory, trading partner, target selection) align with real cohesion splits already implied in the monolith.
- Testing structure anticipates both unit + regression layers (good forward stance).
- Event emitter abstraction is directionally correct (removes ad hoc emission clutter).

## ⚠️ Critical Gaps / Ambiguities (Needs Clarification Before Start)

### 1. Determinism & Hash Stability
**Temporary Refactor Policy – Deferred Baseline Enforcement**: We are *intentionally deferring strict determinism hash parity checks* until the full Agent refactor (all phases) is complete. Interim component extractions may legitimately reorder internal attributes or introduce structural wrappers that would cause transient hash drift. During Phases 1–3:
  - We will still record observed hashes for reference (capture after each phase), but **CI will not fail** on hash mismatch.
  - Any unexpected *behavioral* divergence (different event sequences, resource counts, trade counts) still blocks merges.
  - No new hash fields or metrics are to be added unless clearly marked “EXCLUDED FROM FINAL HASH” in code comments.
  - After Phase 3 completion, we will run a stabilization pass to (a) re‑generate `baselines/determinism_hashes.json`, (b) document rationale for any intentional differences, and (c) re‑enable strict hash gating.
  - If a bug fix requires immediate baseline change mid‑refactor, we create a focused PR labeled `determinism:update-pre-refactor` with justification.

This policy reduces refactor friction while preserving traceability: we differentiate *structural* vs *behavioral* changes and only lock the structural view once composition boundaries settle.

- Not specified how you’ll detect acceptable “no-op differences” (e.g., added metrics keys that shouldn’t enter hash). Need explicit rule: WHICH agent fields participate in determinism hashing today and how to guarantee that component nesting (e.g. `self._inventory`) doesn’t accidentally get serialized.
- No statement whether new components must be excluded from snapshot/replay serialization (if snapshots exist). If serialization walks `__dict__`, composition may alter payload ordering → subtle hash drift.
- Movement logic: Are there any legacy tie‑break subtleties (e.g., prior code used ordered candidate filtering before RNG)? Your random movement keeps a fixed list, but confirm ordering matches current code exactly (test fixture baseline comparison needed).
- Target selection extraction: You plan strategy objects, but their import paths could shift timing of class creation or flag evaluation (if environment variables read at import). Need rule: “All feature/config resolution occurs only at Simulation/Agent construction time” to preserve deterministic import order across processes.

### 2. Backward Compatibility Surface
- External code/tests likely access: `agent.carrying`, `agent.home_inventory`, `agent.inventory`, `agent.trade_partner_id`, `agent.meeting_point`, `agent.mode`, maybe mutating dicts in place. You’re aliasing via `object.__setattr__`—BUT:
  - If a component later replaces its internal dict (e.g., `self.carrying = {…}`) aliases break.
  - Need invariant: “Inventory component mutates dictionaries in place; never rebinds them.”
- Methods removed vs wrapped: Plan doesn’t list the current public Agent methods you must preserve verbatim. You need an API audit checklist before Phase 1 PR (generate symbol list + grep usages).
- Mode transitions: You introduce `AgentModeStateMachine.current_mode` but existing code sets `agent.mode` or calls `_set_mode`. How will you avoid drift between the two? Either:
  - (a) Keep `agent.mode` as single source of truth and have state machine write into it, or
  - (b) Fully encapsulate and turn `mode` into a property delegating to state machine. Plan doesn’t choose.

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

### 4. Trading Partner Component
- Cooldown semantics currently implicit. Need explicit rule table:
  - When pairing succeeds: set mutual state + meeting point (tie-break ordering?).
  - When session ends: exactly which counters reset vs preserved.
  - Edge cases: simultaneous unpair (two handlers touching same pair), agent removal, respawn relocation.
- `pair_with_agent` mutates partner’s internal component directly—introduces bilateral side effects. Better: a pure helper or coordinator ensuring atomicity (or deterministic order based on agent id). Document ordering tie-break: lower `agent.id` always initiates pairing?

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

### 7. Performance Guardrails
- Current plan says “within 2% baseline” but lacks:
  - Measurement variance protocol (e.g., run 5 samples, discard warmup, take median).
  - Threshold breach handling (auto revert? open regression ticket?).
  - Micro-benchmark for new hot methods (movement, selection). Recommend adding `tests/performance/test_agent_micro.py`.

### 8. Testing Plan Gaps
- No plan for mutation safety tests (ensuring alias dicts remain identical objects before/after operations).
- Absent “behavioral equivalence” oracle: which scenarios produce a canonical sequence of (mode changes, resource counts, trades) to assert unchanged? Add targeted fixture capturing event log MD5.
- Determinism regression test sketch references `sim.get_determinism_hash()` which may not exist; ensure actual API (`metrics_collector`?) is correct.
- New unit tests rely on soon-to-exist modules—phase gating: you should create empty shims + failing TODO tests early, or add them only when implementing to avoid red CI noise.

### 9. Serialization / Snapshot / Replay
- If snapshots capture full agent state, moving internals into nested components alters attribute graph shape. Need explicit decision:
  - Either flatten component state into snapshot structure unchanged OR version snapshot format with migration (#snap_version in payload).
- Provide compatibility test: pre-refactor snapshot → load with post-refactor code → produce identical hash after N steps.

### 10. Incremental Merge Strategy
- Plan assumes long-lived branch. Recommend per-phase PRs with locked baseline comparison:
  - Phase 1 PR: movement + emitter + utility (hash stable)
  - Phase 2 PRa: inventory (hash stable)
  - Phase 2 PRb: trading partner (hash stable)
  - Phase 2 PRc: selection strategies (possible hash change? Pre-approve)
  - Phase 3 PR: state machine + (optional) commands (hash stable)
- Define “permit hash change?” decision tree (only if bug fix + new test covers it).

### 11. Feature Flag / Toggle Strategy
- Mentions “feature flags” but doesn’t define their names or load point. Add explicit envs:
  - `ECONSIM_AGENT_INVENTORY_V2=1`
  - `ECONSIM_AGENT_TRADING_V2=1`
  - etc. Or opt for a single progressive mode integer. Clarify removal timeline post-stabilization.

### 12. Logging & Observability Integration
- New components may want lightweight internal debug traces—should they:
  - Use existing observer events (avoid explosion)?
  - Use structured logger categories (SPATIAL, INVENTORY, TRADING)?
- Establish rule: “No print(), no direct GUI logs; only observer or structured logger.”

### 13. Mode Enumeration Completeness
- State machine transitions list omits trading‑specific or stagnation recovery modes (if present today). Validate current `AgentMode` enum vs proposed transitions; else you risk silent invalidation of edge path (e.g., MOVE_TO_PARTNER → TRADING maybe needed).

### 14. Error Handling Philosophy
- Components swallow errors? Currently movement methods are pure; event emitter swallows exceptions. Define uniform principle: only outer step loop swallows; components raise except for explicitly marked non-critical logging failures.

### 15. Naming & Package Layout
- Mixed naming: `components/movement.py`, `components/trading_partner.py`, then a nested `components/target_selection/`. Decide if all multi-object domains get a subpackage for consistency (e.g., `movement/` with utils, not top-level single file).

### 16. Dependency Direction Rules
- Components should not import `Agent` except where strictly required (e.g., trading partner needing partner fields). Plan currently has trading partner referencing `..agent import Agent` via TYPE_CHECKING maybe—must codify “runtime imports only in TYPE_CHECKING blocks; no circular instantiation.”

### 17. Utility Duplication Risks
- `manhattan_distance` appears in multiple modules historically (grid, selection?). Confirm you will centralize it in one canonical utility (maybe `simulation/utils/spatial.py`) to avoid divergence.

### 18. Prospecting Performance Claims
- Plan claims “optimized resource caching” but provides no benchmark target (e.g., ≤ X µs per 12×12 grid, ≤ Y allocations). Add micro metric to assert improvement vs baseline (even if equal).

## 🔁 Suggested Pre‑Implementation Additions

| Area | Action |
|------|--------|
| Determinism spec | Add a short “Agent determinism contract” section listing all attributes considered in hash + ordering/tie-break rules |
| API audit | Generate current public Agent attributes/methods and freeze in `docs/agent_public_api.md` |
| Toggle strategy | Document temp feature flags + removal plan |
| Serialization | Decide snapshot strategy (flatten vs versioned) & add test |
| Event routing | Formalize event emission path (buffer-first or unified logger) |
| Performance harness | Add micro benchmarks before Phase 2 (movement, selection) |
| State machine | Align transition map with full existing enum + add invalid transition test |
| Commands (optional) | Justify with a concrete future feature or defer |

## 🧪 Extra Tests Worth Adding

1. Hash equivalence test comparing pre/post refactor agent state after 50 steps across 3 seeds.
2. Attribute alias identity: `id(agent.carrying)` unchanged after deposit/withdraw.
3. Pairing determinism: Two agents at symmetric positions always pick lowest id initiator (log ordering).
4. Mode transition rejection: Invalid transitions (FORAGE→FORAGE) no duplicate event emission.
5. Leontief prospecting tie-break: When utilities equal, ordering uses `(distance,x,y)` still.
6. Inventory utility epsilon path: Both goods zero vs one zero produce stable expected value.

## 🚫 Things to Consider Deferring
- Command pattern (unless a near-term planner or scripting agent will use it).
- Full mode state machine if existing `_set_mode` already encodes invariants (could wrap first, then later formalize transitions).

## 🩹 Risk Hotspots (Flag Early)
| Risk | Trigger | Mitigation |
|------|---------|------------|
| Silent hash drift | Adding nested dataclasses | Freeze & unit test deterministic serialization view |
| Performance regression | Extra indirection layers | Collect per-step handler time bins pre-phase, compare after each PR |
| Attribute alias breakage | Accidental dict rebinding | Add test + code comment “Do not rebind carrying/home_inventory” |
| Event ordering change | Mixed emitter pathways | Single emission abstraction with step-buffer first |
| Circular imports | Strategy/partner importing Agent | TYPE_CHECKING only + late local imports inside methods |

## ✅ Minimal Clarifications to Add Before First Commit
1. Determinism contract doc (1 page, list of tie-breakers + hashed fields).
2. API symbol freeze list for `Agent`.
3. Single statement on event emission pathway.
4. Decision on commands (in or postponed).
5. Snapshot/serialization stance.
6. Mode/backward compatibility strategy (`agent.mode` authoritative or delegated property).

Let me know which of these you’d like help drafting (e.g., determinism contract doc, API audit script, initial test scaffolds) and I can generate them before you start Phase 1. Would you like me to prepare those artifacts next?