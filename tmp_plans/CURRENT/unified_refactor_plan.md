# Unified VMT Refactoring Plan

*Generated on 2025-01-27*

## Executive Summary

This document provides a comprehensive, unified plan to refactor the two largest files in the VMT codebase: `debug_logger.py` (8.2K tokens, 1,610 lines) and `world.py` (5.9K tokens, 1,059 lines). The plan addresses shared concerns, eliminates duplication, and creates a cohesive architecture that improves maintainability while preserving performance and determinism.

## Current State Analysis

### Shared Problems
1. **Environment Variable Dependencies**: Both files heavily rely on `os.environ` for configuration
2. **Mixed Responsibilities**: Core logic mixed with logging, performance tracking, and configuration
3. **Monolithic Design**: Single classes handling multiple concerns
4. **Tight Coupling**: Direct dependencies between subsystems
5. **Verbose Documentation**: Excessive docstring repetition across both files

### File-Specific Issues

#### debug_logger.py
- Complex singleton pattern with extensive buffering logic
- Multiple event builders and parsing methods
- 1,610 lines in single class
- Complex state management with multiple buffer types

#### world.py
- Massive 400+ line step method
- Complex conditional logic based on environment variables
- Mixed simulation logic with logging and performance tracking
- Deep nesting and multiple execution branches

## Unified Refactoring Strategy

### Phase 0: Determinism & Ordering Safeguard Tests (Pre-Refactor)

Purpose: Freeze current externally observable behaviors (ordering, RNG usage, action/trade sequences) before any structural changes. These tests act as a trip‑wire so refactors cannot silently alter determinism or tie‑break semantics.

#### Scope Covered
1. Action & trade execution sequence snapshot
2. Trade intent ordering (full tie-break tuple)
3. Resource pickup ordering under unified selection logic
4. RNG draw count & sequence invariance (external vs internal RNG separation)

#### Test Artifacts
Planned file locations (subject to minor adjustment during implementation):
- `tests/unit/determinism/test_action_trade_sequence_freeze.py`
- `tests/unit/determinism/test_trade_intent_ordering.py`
- `tests/unit/determinism/test_resource_pickup_ordering.py`
- `tests/unit/determinism/test_rng_call_counts.py`

#### 0.1 Action & Trade Sequence Snapshot Freeze
Goal: For a fixed seed & config, capture the first N (e.g. 300) executed resource pickups and executed trades (at most one per step) and assert exact sequence equality on subsequent runs.
Mechanics:
- Instrument existing code via lightweight hooks (no logic changes) to append tuples to an in‑memory list.
- Tuple schema (append‑only, documented in test):
    `(step, event_type, agent_id, resource_or_trade_type, x, y, utility_delta)`
- Persist baseline as a JSON fixture under `tests/fixtures/determinism/action_trade_sequence_baseline.json` generated once and reviewed.
- Test compares new run vs baseline; on mismatch, prints first differing index and surrounding context (±3 entries) for rapid diagnosis.

#### 0.2 Trade Candidate Tie-Break Ordering
Goal: Validate the intent ordering key EXACTLY matches documented invariant:
`(-ΔU, seller_id, buyer_id, give_type, take_type)` (priority flag may reorder ONLY by injecting its effect without altering multiset; any priority mode will have its own asserted ordering if currently supported).
Mechanics:
- Construct controlled scenario with crafted agents producing intents having identical ΔU except for systematic variation in each secondary key.
- Assert the sorted order of intent identity tuples equals expected list.
- Parametrize with / without priority flag env var (if active in current code) to ensure stable alternate ordering.

#### 0.3 Resource Pickup Ordering (Unified Strategy)
Goal: When unified selection path is active, verify resource pickup decisions follow distance‑discounted utility selection rules AND tie‑break ordering: `(-ΔU, distance, x, y)` (distance squared if that is what production code uses—test will match current implementation precisely after inspection).
Mechanics:
- Enable unified mode flags (forage + trade draft as required) while disabling trades execution to isolate pickups.
- Place deterministic set of resources with equal base ΔU but varying distances and coordinates; run one step; capture final chosen ordering of executed pickups.
- Assert ordering matches baseline expected tuple list.

#### 0.4 RNG Draw Count & Sequence Invariance
Goal: Ensure refactor does not change number or ordering of calls to external vs internal RNG streams per step.
Mechanics:
- Implement a counting proxy/wrapper for `ext_rng` that records each method call (`random`, `randrange`, `uniform`, etc.) in a simple list of `(method, args_shape)` where args are shape‑hashed (not raw values) to minimize brittleness while still catching count/order shifts.
- Capture per-step call counts + cumulative signature for first M steps (e.g. 200) into baseline JSON: `tests/fixtures/determinism/rng_profile_baseline.json`.
- Test replays scenario and asserts identical sequence; on mismatch surfaces first divergence.
- Internal RNG (`Simulation._rng`) similarly wrapped if feasible without invasive changes; else count its call total per step.

#### Acceptance Criteria for Phase 0
- All four tests green and committed before starting Phase 1.
- Baselines reviewed manually & annotated with a header block explaining generation date, config seed, and invariants covered.
- CI pipeline fails on any divergence unless baseline is intentionally regenerated (explicit flag / manual step documented).

#### Regenerating Baselines (Controlled Procedure)
1. Run `pytest -k determinism --regenerate-baselines` (new marker/CLI option to be added) which overwrites JSON fixtures.
2. Open a diff and manually verify only expected intentional changes (e.g., newly appended fields) appear.
3. Commit with message: `tests: update determinism baselines (explain reason)`.
4. Never regenerate implicitly inside normal test runs.

#### Documentation Addendum
A short `docs/architecture/determinism_tests.md` file will be added summarizing:
- Invariants captured
- How to safely update baselines
- Common causes of failure & triage flow

---

### Phase 0.5: RNG Separation & Call Order Freeze (Augments Phase 0)

Purpose: Make the external (`ext_rng`) vs internal (`Simulation._rng`) randomness boundaries explicit, freeze the per-step call ordering and counts, and provide a code review checklist so structural refactors cannot unintentionally shift randomness consumption (which would cascade into ordering changes elsewhere).

#### 0.5.1 Canonical RNG Call Order (Current Behavior Documentation Placeholder)
The exact current order will be extracted and documented prior to structural edits. Expected high-level sequence per step (subject to confirmation during baseline capture):
1. Agent movement / random walk decisions (legacy mode only)
2. Foraging target / selection RNG (when foraging path active)
3. Unified selection: any stochastic tie-break resolution or sampling (if present)
4. Trade intent generation randomness (if generation uses RNG)
5. Trade selection randomness (ONLY if priority / random fallback occurs; otherwise deterministic sort)
6. Respawn resource placement RNG (internal RNG only)
7. Any late-step metrics / ancillary RNG (should be NONE; test will assert absence)

This list will be converted into an enforced checklist under `docs/architecture/determinism_tests.md` once the introspection script outputs the concrete ordered method names.

#### 0.5.2 Instrumentation Strategy
Introduce a thin wrapper class `CountingRNG` that delegates to `random.Random` and records:
- Ordered list of calls: `(step, stream, method, args_signature)` where `stream` ∈ {`ext`,`internal`}.
- `args_signature` is a stable abstraction (e.g., number of args + types + sentinel for ranges) instead of raw values to avoid brittleness.
- Per-step summary hash: SHA256 of concatenated method names; stored for quick diff surface in failures.

Wrapper added ONLY in tests via dependency injection (do not modify production path or alter call counts). Internal RNG wrapping achieved by monkeypatching after `Simulation.from_config` (if direct replacement is feasible) or by subclassing a small adapter if internal RNG attribute assignment is blocked.

#### 0.5.3 Baseline Artifact
File: `tests/fixtures/determinism/rng_call_order_baseline.json`
Structure:
```json
{
  "meta": {"generated_on": "<iso>", "seed": 123, "steps": 200, "version": 1},
  "per_step": [
      {"step": 0, "ext_calls": ["randrange","random"], "internal_calls": ["randrange"], "ext_hash": "...", "internal_hash": "..."},
      ...
  ],
  "cumulative": {"ext_total": 1234, "internal_total": 567, "ext_sequence_hash": "...", "internal_sequence_hash": "..."}
}
```

#### 0.5.4 Test Definition
File: `tests/unit/determinism/test_rng_call_order_freeze.py`
Behavior:
1. Runs simulation for M steps (default 200) with defined config flags (forage + trade draft + respawn + metrics ON to maximize exercised paths; trade exec ON to include trade logic).
2. Captures instrumentation output.
3. Loads baseline JSON and asserts:
    - Per-step counts identical.
    - Per-step ordered method name list identical.
    - Cumulative sequence hash identical.
4. On failure, diff engine prints first differing step with side-by-side lists and suggests regenerating baseline if intentional.

CLI option `--regenerate-rng-baseline` parallels Phase 0 regeneration flow; combined option `--regenerate-baselines` triggers both.

#### 0.5.5 Code Review Checklist (Added to Docs)
Before merging any refactor touching simulation step logic:
- [ ] Does diff show added/removed RNG calls? If yes, justify & update baseline intentionally.
- [ ] Are any RNG calls moved across logical phases (movement → trade, etc.)? Provide rationale.
- [ ] Are tie-break deterministic sorts still pure (no RNG injected)?
- [ ] Internal RNG use restricted to respawn / placement only? If expanded, document justification.

#### 0.5.6 Failure Triage Guidance
If test fails:
1. Inspect first differing step output.
2. If added call arises from logging or debugging instrumentation, remove or guard under `if debug_flag`.
3. If ordering changed but counts equal, check for refactor inadvertently iterating in different sequence (e.g., changed container type).
4. If internal RNG call count shifted while external stable: verify respawn / home placement logic not executed earlier.

#### 0.5.7 Acceptance Criteria
- Baseline generated & committed.
- Test reliably passes 5 consecutive CI runs (flakiness check) by re-executing same seed.
- Documentation updated with concrete finalized call order list.

---

### Gap 4 (Logging Schema Stability) – Deferred (EXPLICIT)
Status: Intentionally deferred until after Gap 5 (buffer semantics) and initial modular logger scaffolding land.

Rationale for Deferral:
- Need to snapshot current buffer flush ordering first (Gap 5) because schema baselines are sensitive to emission order.
- Risk of double baseline churn if we capture schema before stabilizing flush boundaries.
- Avoids premature lock-in of fields that may later be reclassified (e.g., moving aggregation counters from per-event to per-batch).

Non-Negotiable Constraints Still In Effect During Deferral:
- Do NOT rename existing categories.
- Maintain existing compact JSON formatting (no pretty print, keep separators=(',',':')).
- Preserve sign + three-decimal formatting for any utility deltas.
- Do not drop envelope fields already present (step, timestamp/relative time, category) even temporarily.

Trigger to Re-Activate Gap 4:
- After Gap 5 tests (flush semantics) are green AND modular logging code paths produce identical event counts for a 2k-step scenario.

Temporary Guard Tests (Lightweight):
- Smoke test asserting category set stable.
- Smoke test asserting envelope key presence.

Planned Future Artifacts (when resumed):
- `tests/fixtures/logging_schema_v1.json` baseline.
- `tests/unit/logging/test_logging_schema_freeze.py`.
- Doc: `docs/architecture/logging_schema.md`.

---

### Gap 5 (Buffer Flush Semantics) – Detailed Plan (IN NEED OF REVIEW)

Goal: Formalize, test, and freeze the precise conditions under which each log buffer (trade, transition, performance, aggregation, generic) flushes to the structured log so that refactoring buffer logic cannot:
1. Shift event emission to different steps.
2. Coalesce or split batches unexpectedly.
3. Reorder events across categories at step boundaries.

#### 5.1 Inventory of Existing Buffer Types (Proposed Classification)
| Buffer | Purpose | Current Flush Signals (Hypothesized) | Ordering Sensitivity | Aggregation? |
|--------|---------|--------------------------------------|----------------------|--------------|
| TradeBuffer | Per-trade (draft, prune, execute) events | Step change OR capacity | High (ties with execution sequence) | No (one line per event) |
| TransitionBuffer | Agent mode/state transitions | Step change OR time window | Medium (in-step grouping ok) | Yes (may batch) |
| BundleBuffer (if present) | Batch summary (funnels/pruning) | Explicit call after drafting | High (must follow raw intents) | Yes |
| PerfBuffer / Periodic | Performance summaries (FPS, frame_ms) | Interval (N steps) | Low | Yes |
| GenericDebugBuffer | Ad hoc debug lines | Capacity OR finalize | Low | No |

NOTE: Actual buffers will be confirmed by code spelunking before tests are authored; this table becomes the source of truth updated with empirical data.

#### 5.2 Canonical Flush Policy Specification (To Codify)
For each buffer we define:
```
flush_trigger: enum {STEP_CHANGE, INTERVAL, CAPACITY, EXPLICIT, FINALIZE}
primary_key_order: stable sort key for emitted events (if multiple)
batch_shape: single | list[events] | aggregated_summary
must_flush_on_finalize: bool
max_latency_steps: int (guaranteed upper bound before emission)
```

Example YAML (to possibly store under `schema/buffer_policies.yaml`):
```yaml
trade:
  flush_trigger: STEP_CHANGE
  batch_shape: single
  primary_key_order: [sequence_observed]
  must_flush_on_finalize: true
  max_latency_steps: 1
transition:
  flush_trigger: STEP_CHANGE
  batch_shape: list
  primary_key_order: [agent_id, new_mode]
  must_flush_on_finalize: true
perf:
  flush_trigger: INTERVAL
  interval_steps: 500
  batch_shape: summary
  primary_key_order: []
  must_flush_on_finalize: true
```

#### 5.3 Required Tests
1. `test_buffer_trade_flush_on_step_change.py`
    - Create scenario with multiple trades across 3 steps.
    - Assert: trade events for step N appear before any step N+1 trades; no trade lines for step N emitted after step increment.
2. `test_transition_buffer_batching.py`
    - Force multiple agent transitions within one step.
    - Assert: either combined batch or multiple lines—match baseline; no cross-step leakage.
3. `test_perf_buffer_interval.py`
    - Set interval to small value (e.g., 10) via env/config.
    - Assert periodic summary appears exactly at multiples (10,20,30...).
4. `test_finalize_forces_flush.py`
    - Populate each buffer without hitting natural flush; call finalize; assert all pending data emitted.
5. `test_capacity_flush_behavior.py`
    - Reduce capacity (e.g., 2) for a buffer; add 3 events; assert flush occurred after overflow threshold.
6. `test_no_reordering_across_categories.py`
    - Interleave trade + transition events in contrived order; ensure relative emission order across categories within a step matches baseline (or documented deterministic merge rule).

#### 5.4 Baseline Fixture for Flush Sequences
File: `tests/fixtures/logging/flush_sequence_baseline.json`
Structure:
```json
{
  "meta": {"seed": 123, "steps": 25, "version": 1},
  "events": [
      {"idx":0,"step":0,"category":"TRADE","raw":"..."},
      {"idx":1,"step":0,"category":"AGENT_MODE","raw":"..."}
  ],
  "flush_boundaries": [0,5,11,...]  // indices where a flush boundary occurred
}
```

#### 5.5 Instrumentation Hook
Add (temporary) debug hook in logger core (guarded by `ECONSIM_LOG_DEBUG_FLUSH=1`) that appends a marker event or callback when a buffer flush occurs; test harness captures marker to build `flush_boundaries` list. Removed or disabled (flag off) in production builds to avoid overhead.

#### 5.6 Acceptance Criteria for Gap 5
- All buffer policy tests passing with baseline fixture.
- Document `buffer_policies.yaml` (or table in docs) checked in.
- Flush boundary baseline stable over 5 consecutive CI runs.
- No per-step latency regression (compare pre/post average number of events delayed >1 step == 0 except permitted interval buffers).

#### 5.7 Failure Triage Guidelines
Symptom -> Likely Cause -> Action:
- Missing final trade events -> finalize flush not invoked or policy mismatch -> ensure `finalize_log_session()` called or mark buffer `must_flush_on_finalize`.
- Duplicate perf summaries -> interval counter not reset -> reset state after emission.
- Cross-step transition leakage -> last_step tracking bug -> verify step advancement logic in buffer.
- Out-of-order trade vs transition -> combined flush ordering logic changed -> enforce stable merge rule (documented comparator).

#### 5.8 Timeline Impact
Add explicit tasks to Week 1/2 to codify + test buffer policies BEFORE large logger refactor replaces internals.

---

### Gap 6 (Trade Execution Semantics) – Confirmed Ordering Tuple

Status: AGREED – Use full current ordering tuple for deterministic trade selection.

#### 6.1 Canonical Ordering (Baseline)
Primary selection key (without priority flag):
```
(-ΔU, seller_id, buyer_id, give_type, take_type)
```
Where:
- `ΔU` = utility gain to the system (or executing agent as currently defined) BEFORE any distance discounting (must remain consistent with pre-refactor logic).
- Negative sign sorts largest positive utility first.
- `seller_id`, `buyer_id` provide stable tie-break preserving agent list order neutrality (agent list order itself is invariant, we just use IDs).
- `give_type`, `take_type` finalize deterministic ordering for otherwise identical agent pairs.

#### 6.2 Priority Mode Extension
If a priority flag (e.g., `ECONSIM_PRIORITY_TRADE=1`) is active, ordering is modified ONLY by injecting a higher-precedence segment at the start of the tuple; base multiset and subsequent relative ordering must remain unchanged.

Proposed tuple under priority flag:
```
(priority_rank, -ΔU, seller_id, buyer_id, give_type, take_type)
```
Where `priority_rank` is a small integer (0 = high priority, 1 = normal). Priority logic MUST NOT:
1. Filter out trades.
2. Change ΔU calculation.
3. Reorder trades with same priority relative to baseline ordering.

If no priority classification currently exists, this remains a no-op and test path still asserts identity relative to baseline sequence.

#### 6.3 Single Execution Constraint
Exactly one trade may execute per step when trade execution is enabled (`trade_exec` flag). This constraint remains enforced AFTER selection logic chooses the highest-ranked candidate. Remaining intents are discarded (or carried to next step ONLY if that was pre-existing behavior – confirm before locking test). Plan assumes they are re-generated per step (stateless drafting) – verify; if stateful, incorporate into determinism baseline.

#### 6.4 Collection Phase Requirements
Trade intents enumeration MUST:
1. Iterate agents in existing agent list order (never sorted mid-step).
2. Aggregate each agent's intents without introducing intermediate sorts that change RNG call count.
3. Avoid quadratic partner scans—preserve current complexity (expected O(n + intents)).
4. Avoid distance recomputation thrash; reuse existing computed metrics if available.

#### 6.5 Tests to Implement
1. `test_trade_intent_ordering_tuple_freeze.py`
    - Construct contrived intents covering permutations of secondary tie-break keys.
    - Assert produced ordered identity list (without priority) equals baseline fixture.
2. `test_trade_intent_ordering_with_priority.py`
    - Enable priority flag.
    - Provide a mix of high/normal priority intents with overlapping ΔU values.
    - Assert ordering matches transformed tuple while preserving intra-priority baseline ordering.
3. `test_single_trade_execution_enforced.py`
    - Generate >1 high-ranking intents; assert only first executes and post-step inventories reflect exactly one applied delta.
4. `test_no_execution_when_exec_flag_disabled.py`
    - Confirm drafting occurs (if that’s current behavior) but no inventory change.
5. `test_trade_order_stability_over_steps.py`
    - For stable environment & seed, run N steps; record executed trade identity hash sequence; compare to baseline.

#### 6.6 Baseline Fixture
File: `tests/fixtures/trade/trade_ordering_baseline.json`
Structure:
```json
{
  "meta": {"seed": 123, "version": 1},
  "ordering_no_priority": [
      {"seller":1,"buyer":2,"give":"WOOD","take":"STONE","dU":1.2},
      {"seller":1,"buyer":2,"give":"WOOD","take":"FOOD","dU":1.2}
  ],
  "ordering_with_priority": [
      {"seller":3,"buyer":4,"give":"FOOD","take":"STONE","dU":2.0,"priority":0},
      {"seller":1,"buyer":2,"give":"WOOD","take":"STONE","dU":1.2,"priority":1}
  ]
}
```

#### 6.7 Instrumentation Hook (Optional / Test-Only)
Add a light hook `Simulation._capture_trade_selection(candidate_list, chosen)` (activated by `ECONSIM_TRADE_DEBUG_SELECTION=1`) to emit a structured debug event capturing:
```json
{"event":"TRADE_SELECTION","candidates": [... tuple keys ...], "chosen": {...}}
```
Used ONLY in tests / debugging; disabled in production by default.

#### 6.8 Determinism Interaction
- Changing the ordering tuple or injecting extra RNG calls during trade drafting will break Phase 0 baselines.
- Tests should run AFTER determinism baselines so any tuple mismatch yields fast, interpretable failure.

#### 6.9 Performance Considerations
- Sorting complexity: O(k log k) where k = number of drafted intents. Guardrail: ensure k << n * average intents per agent; monitor via test logging metrics (optional counter of intents per step) to detect accidental explosion.
- If priority is added, computing `priority_rank` must be O(k) with trivial branching.

#### 6.10 Acceptance Criteria
- All trade ordering tests green (with & without priority flag).
- Determinism baseline unaffected (hash unchanged) after introducing instrumentation guarded flags.
- Single-trade execution test verifies no multi-execution regression.
- Performance test shows no >1% regression in steps/sec on trade-heavy scenario (compared to pre-change baseline).

#### 6.11 Timeline Additions
Add to Week 2 (adjacent to logging modules) or early Week 3:
- [ ] Implement trade ordering tests + baseline fixture
- [ ] Add optional trade selection debug hook
- [ ] Run perf micro-benchmark for trade-heavy config (store comparison result)

### Gap 7 (Unified Selection Strategy Complexity) – Finalized Specification

Status: SPECIFIED & READY FOR TEST AUTHORING

#### 7.1 Core Principle (Utility Primacy)
Utility delta (base ΔU computed for the individual agent or system exactly as today) is ALWAYS the primary ordering dimension. All other factors (distance, coordinates, IDs, types) exist solely to produce stable deterministic tie‑breaks. Distance discounting is a transformation used only to compare heterogeneous action types (e.g., distant resource pickup vs immediate trade) without altering the canonical tie‑break ordering for equal effective values.

#### 7.2 Candidate Set & Data Model
We unify (a) resource pickup opportunities and (b) (optionally flagged) trade execution intents into a single linear scan that selects at most one action per agent decision cycle (subject to existing per-step trade execution cap = 1).

Data structure (internal only; NOT serialized, NOT part of determinism hash schema):
```python
@dataclass
class SelectionCandidate:
     kind: Literal['pickup','trade']
     agent_id: int
     base_delta: float          # Raw ΔU (>0 only; filtered early)
     effective_delta: float     # ΔU' after distance discount (pickup) or == base_delta (trade)
     distance_sq: int           # 0 for trades (or omitted); used only for tie-break + discount
     coord: tuple[int,int]      # Resource (x,y) or agent position for trade anchor
     tie_break: tuple           # Canonical tuple described below
     payload: Any               # Reference to resource or trade intent object
```

Memory note: All instances allocated once per enumeration pass; no secondary copies; enumeration aims O(R_visible + T_drafted).

#### 7.3 Distance Discount Formula
Apply ONLY to resource pickup candidates (trades currently have no spatial decay):
```
ΔU' = ΔU / (1 + k * d²)
```
Where `d²` is squared grid distance (already available / cheaply computed) and `k = config.distance_scaling_factor` (existing SimConfig field). Trades use `effective_delta = base_delta` (no distance penalty). This preserves legacy trade valuations while allowing distant resources to fall behind nearer trades of slightly lower base ΔU when pedagogically relevant.

Rationale: Avoid changing base ΔU semantics (teaching clarity) while enabling intuitive spatial opportunity cost balancing.

#### 7.4 Early Filtering
Candidates with `base_delta <= 0` are discarded BEFORE any distance discounting, allocation, or tie-break tuple construction. This keeps complexity linear and guards against negative or zero utility noise altering RNG call counts or ordering.

#### 7.5 Tie-Break Ordering (Unchanged Invariant)
Selection chooses candidate with maximal `effective_delta`. On ties in `effective_delta` (after discount):
1. Compare by `-base_delta` (so higher base ΔU preferred if discount collision)
2. Resource vs trade: no explicit priority beyond effective/base ordering (if equal effective & base, fall through)
3. For pickups: `(distance_sq, x, y)`
4. For trades: re-use existing trade ordering suffix (already stabilized): `(seller_id, buyer_id, give_type, take_type)` — but this is embedded INSIDE the candidate's `tie_break` tuple so we do NOT recompute or merge sorts across types; we only compare when both candidates are trades.

Unified comparator logic (conceptual):
```
if A.effective_delta != B.effective_delta: choose larger
elif A.base_delta != B.base_delta: choose larger
else:
     if A.kind == B.kind == 'pickup': compare (A.distance_sq, A.coord.x, A.coord.y)
     elif A.kind == B.kind == 'trade': compare trade_tie_break(A) vs trade_tie_break(B)
     else: # cross-kind truly identical utility and no further discriminant
            fall back to stable agent_id, then kind ('pickup' < 'trade' for stability) to avoid nondeterminism
```
Cross-kind final fallback only triggers in contrived scenarios (identical utilities, identical positions & trade keys); included for formal completeness and deterministic total ordering.

#### 7.6 Complexity Enforcement (O(n))
Implementation prohibits a full sort of all candidates on the hot path. We perform a SINGLE linear scan maintaining the current best candidate per agent decision context. Optional debug instrumentation (explanations list, full ordering dump) is guarded by `ECONSIM_LOG_DECISION_REASONING=1` and executed ONLY AFTER the winner is chosen; it may create a secondary sorted view for logging but MUST NOT influence selection or call extra RNG.

Prohibited patterns:
- Sorting the entire candidate list in production path
- Two-pass discount recomputation
- Building per-resource nested trade comparisons (quadratic)

#### 7.7 Implementation Steps
1. Introduce `SelectionCandidate` (internal module, e.g., `simulation/selection.py`).
2. Add generator `_enumerate_pickup_candidates(agent)` using spatial index iteration already provided (respect `Grid.iter_resources_sorted()` if needed for determinism, but we do NOT rely on iteration order for correctness—tie-breaks cover it). Precompute distance_sq once.
3. Add generator `_enumerate_trade_candidates(agent)` reusing existing drafted intents (no new draft logic; do NOT change intent enumeration order).
4. In unified selection routine `_select_best_action(agent, ext_rng)`:
    - Initialize `best=None`
    - For each candidate from both generators: early filter base<=0, compute effective (only pickups), compare with current best using comparator (inline function; no tuple materialization if possible for micro perf) and update.
    - Return best candidate (or None) and execute accordingly respecting single-trade-per-step global constraint.
5. If debug reasoning enabled: build explanatory record (list of (rank,effective_delta, tie_break_repr)) by sorting a lightweight projection list; attach to structured log line (excluded from determinism hash per existing rule for trade/debug metrics).

#### 7.8 Determinism Safeguards
- The linear scan's only ordering dependency is iteration order of resource enumeration & trade intent listing; both are already deterministic and tested (Phase 0 baselines). Comparator enforces a total ordering independent of enumeration path.
- No RNG calls added; selection remains pure deterministic comparison.
- Debug reasoning path executed post-selection only; must not allocate random or mutate simulation state.

#### 7.9 Testing Plan
New tests (some extend previously listed resource pickup ordering test):
1. `test_unified_selection_pickup_vs_trade_priority.py`
    - Scenario where a distant high base ΔU resource vs a nearer moderate ΔU trade crosses after discount (ensure trade chosen if effective higher, or resource if discount still dominates).
2. `test_unified_selection_tie_break_pickups.py`
    - Multiple resources with identical base ΔU leading to equal effective (same distance) — assert coordinate ordering tie-break.
3. `test_unified_selection_trade_vs_pickup_exact_tie.py`
    - Construct artificial case equal effective & base ΔU; ensure stable fallback ordering (documented) – snapshot expected winner.
4. `test_unified_selection_no_positive_candidates.py`
    - All base ΔU <= 0 → returns None (agent idle) without errors.
5. `test_unified_selection_debug_reasoning_side_effect_free.py`
    - Enable reasoning flag; verify winner unchanged vs disabled run and determinism hash identical.

Fixtures / Baselines:
`tests/fixtures/selection/unified_selection_examples.json` capturing canonical scenarios (effective vs base comparisons & winners).

#### 7.10 Performance Benchmark
Add perf harness: `tests/perf/test_unified_selection_perf.py` (or augment existing perf tool) measuring mean step time over 200 steps with config:
```
agents=500, resources=1000, forage_enabled=1, trade_draft=1, trade_exec=0, distance_scaling_factor=1.5
```
Store baseline JSON `tests/fixtures/perf/unified_selection_baseline.json` with:
```json
{"meta":{"seed":123,"steps":200,"version":1},"avg_step_time_ms":X.YZ}
```
Acceptance: post‑implementation regression must be < +2% over baseline (allow ±0.5 ms noise); enforced by test with tolerance window.

#### 7.11 Acceptance Criteria
- Linear scan only (verified by code review + absence of `sorted(` in hot path).
- All selection tests green.
- No change to determinism baselines (action/trade sequence & RNG counts) vs pre-gap implementation.
- Perf test: <2% regression.
- Debug reasoning path produces stable, hash-excluded structured lines when flag enabled.

#### 7.12 Documentation Additions
- Update `copilot-instructions.md` Unified Selection Algorithm (already references distance-discount) to clarify production comparator & no full sort guarantee.
- Add short section in `docs/architecture/determinism_tests.md` enumerating selection-specific invariants and tie-break ladder.

#### 7.13 Future Extension Hooks (Non-Blocking)
- Potential future distance penalty for trades (transaction friction) would introduce `trade_distance_sq` concept; design keeps field optional to allow extension without schema reorder.
- Multi-action per step (not planned) would require changing single best selection logic; keep candidate enumeration decoupled so can return k-best using partial selection algorithm (still O(n + k log k)).

---

---
---

### Phase 1: Shared Infrastructure (Week 1)

#### Step 1.1: Introduce `VMTConfig` Wrapper (Layered Configuration)
Strategy: Keep existing `SimConfig` strictly focused on core simulation parameters (grid size, seeds, respawn & metrics enabling, etc.) and introduce a higher-level `VMTConfig` that composes:
```python
@dataclass
class VMTConfig:
    sim: SimConfig  # existing object (unchanged semantics)
    # Feature flags (behavioral)
    legacy_random: bool = False
    forage_enabled: bool = True
    trade_draft: bool = False
    trade_exec: bool = False
    priority_trade: bool = False
    hash_neutral_trade: bool = False
    # Logging / diagnostics
    log_level: str = "VERBOSE"
    log_categories: Optional[Set[str]] = None
    log_format: str = "STRUCTURED_ONLY"
    log_bundle_trades: bool = False
    log_explanations: bool = False
    performance_log_interval: int = 1000
```

Key Principles:
1. Isolation: Only `SimConfig` participates in determinism hash & snapshot unless explicitly extended (allowlist enforced by test).
2. Clarity: New operational / logging / pedagogical flags never pollute core simulation schema.
3. Composition Over Mutation: No fields added to `SimConfig` in this refactor phase (append-only changes there reserved for truly core sim semantics).
4. Controlled Access: Simulation code receives a `VMTConfig` but passes `vmt_config.sim` to routines expecting legacy `SimConfig` to avoid churn.

Helper Constructors:
```python
@classmethod
def from_environment(cls, **overrides):
    base = SimConfig.from_environment(**{k: v for k, v in overrides.items() if k in SimConfig.__dataclass_fields__})
    feature_kwargs = {k: v for k,v in overrides.items() if k not in SimConfig.__dataclass_fields__}
    # read ECONSIM_* env vars for wrapper-scoped fields not overridden
    return cls(sim=base, **_load_wrapper_env(**feature_kwargs))
```

Execution Mode API:
```python
def execution_mode(self) -> str:
    if self.legacy_random: return "random"
    if self.forage_enabled and self.trade_draft: return "unified"
    if self.forage_enabled: return "forage"
    return "idle"
```

Logging Category Check:
```python
def should_log_category(self, category: str) -> bool:
    return True if not self.log_categories else category in self.log_categories
```

Migration Steps:
1. Introduce `VMTConfig` (no usages) + tests for env parsing equivalence of existing flags (smoke test only).
2. Update factory: `Simulation.from_config` to accept either `SimConfig` (legacy) or `VMTConfig` (new). Branch: if SimConfig passed, wrap via `VMTConfig(sim=config)` with default wrapper fields.
3. Gradually replace internal sites reading env flags with references to `self.config.<flag>` (wrapper). Core code that only needs base parameters still uses `self.config.sim` to access original fields.
4. Once all direct `os.environ` reads replaced, add a lint/test guard forbidding new env reads outside `config` modules.
5. Document new API usage & deprecate direct flag env reads (warning note in docs + code comment).

Risk Mitigation:
- Adapter path ensures zero breakage for external users constructing only `SimConfig`.
- Determinism hash test asserts wrapper fields excluded (explicit allowlist of hashed fields origin = `sim`).
- Snapshot parity test (pre/post introduction) ensures no schema drift in core snapshots.

Tests To Add:
- `test_vmtconfig_environment_parity.py`: matrix of env combos verifying parity with legacy behavior.
- `test_vmtconfig_execution_mode.py`: covers all mode branches.
- `test_vmtconfig_log_category_filter.py`: empty, single, multiple categories.
- `test_simulation_factory_accepts_both.py`: asserts factory wraps `SimConfig` transparently.

Open Questions:
- Should wrapper fields be persisted in session metadata file (non-deterministic)? (Initial: yes for reproducibility, but excluded from determinism hash unless behavioral.)
- Should we add a `to_dict(include_runtime: bool=False)` for selective export? (Likely yes.)

Acceptance Criteria for Step 1.1:
- `VMTConfig` introduced + tests green.
- Simulation can be constructed with previous `SimConfig` code unchanged.
- No changes to determinism hash result for baseline scenario.
- Documentation updated with separation rationale & usage examples.

#### Step 1.2: Create Shared Performance Tracking
**File**: `src/econsim/core/performance.py`

```python
"""Unified performance tracking for VMT."""

import time
from typing import Dict, Any, Optional
from collections import deque
from .config import VMTConfig

class PerformanceTracker:
    """Unified performance tracking for simulation and logging."""
    
    def __init__(self, config: VMTConfig):
        self.config = config
        self.step_times = deque(maxlen=100)
        self.last_log_step = 0
        self.total_steps = 0
        self.start_time = time.time()
    
    def track_step(self, step_num: int, start_time: float, end_time: float) -> None:
        """Track step performance metrics."""
        step_time = end_time - start_time
        self.step_times.append(step_time)
        self.total_steps = step_num
        
        # Log performance at intervals
        if step_num - self.last_log_step >= self.config.performance_log_interval:
            self._log_performance(step_num)
            self.last_log_step = step_num
    
    def _log_performance(self, step_num: int) -> None:
        """Log performance statistics."""
        if not self.step_times:
            return
        
        avg_time = sum(self.step_times) / len(self.step_times)
        fps = 1.0 / avg_time if avg_time > 0 else 0
        min_time = min(self.step_times)
        max_time = max(self.step_times)
        
        print(f"Performance at step {step_num}:")
        print(f"  Avg step time: {avg_time:.4f}s")
        print(f"  FPS: {fps:.1f}")
        print(f"  Min time: {min_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  Total steps: {self.total_steps}")
    
    def get_current_fps(self) -> float:
        """Get current FPS based on recent step times."""
        if not self.step_times:
            return 0.0
        avg_time = sum(self.step_times) / len(self.step_times)
        return 1.0 / avg_time if avg_time > 0 else 0.0
    
    def get_average_step_time(self) -> float:
        """Get average step time in seconds."""
        if not self.step_times:
            return 0.0
        return sum(self.step_times) / len(self.step_times)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            'fps': self.get_current_fps(),
            'avg_step_time': self.get_average_step_time(),
            'total_steps': self.total_steps,
            'uptime': time.time() - self.start_time
        }
    
    def reset(self) -> None:
        """Reset performance tracking."""
        self.step_times.clear()
        self.last_log_step = 0
        self.total_steps = 0
        self.start_time = time.time()
```

### Phase 2: Logging System Refactoring (Week 1-2)

#### Step 2.1: Create Logging Infrastructure
**File**: `src/econsim/gui/logging/__init__.py`

```python
"""Logging system for VMT GUI."""

from .logger import GUILogger
from .convenience import (
    get_gui_logger,
    log_agent_mode,
    log_trade,
    log_simulation,
    log_utility_change,
    log_performance,
    finalize_log_session
)
from .formatters import format_agent_id, format_delta

__all__ = [
    "GUILogger",
    "get_gui_logger",
    "log_agent_mode",
    "log_trade",
    "log_simulation", 
    "log_utility_change",
    "log_performance",
    "finalize_log_session",
    "format_agent_id",
    "format_delta"
]
```

#### Step 2.2: Create Modular Logging Components
**Files**: 
- `src/econsim/gui/logging/logger.py` (Simplified main logger)
- `src/econsim/gui/logging/event_builders.py` (Event construction)
- `src/econsim/gui/logging/buffers.py` (Message buffering)
- `src/econsim/gui/logging/parsers.py` (Message parsing)
- `src/econsim/gui/logging/file_manager.py` (File I/O)
- `src/econsim/gui/logging/formatters.py` (Formatting utilities)
- `src/econsim/gui/logging/convenience.py` (Global access functions)

### Phase 3: Simulation System Refactoring (Week 2-3)

#### Step 3.1: Create Simulation Infrastructure
**File**: `src/econsim/simulation/__init__.py`

```python
"""Simulation system for VMT."""

from .world import Simulation
from .execution_strategies import ExecutionStrategyFactory
from .step_components import StepComponentManager
from .performance_tracker import SimulationPerformanceTracker

__all__ = [
    "Simulation",
    "ExecutionStrategyFactory", 
    "StepComponentManager",
    "SimulationPerformanceTracker"
]
```

#### Step 3.2: Create Modular Simulation Components
**Files**:
- `src/econsim/simulation/execution_strategies.py` (Execution modes)
- `src/econsim/simulation/step_components.py` (Step execution)
- `src/econsim/simulation/performance_tracker.py` (Simulation-specific performance)

### Phase 4: Integration and Coordination (Week 3-4)

#### Step 4.1: Create Unified World Class
**File**: `src/econsim/simulation/world.py` (Refactored)

```python
"""Unified simulation coordinator with integrated logging."""

import random
import time
from typing import List, Optional, Union
from .performance_tracker import PerformanceTracker
from .execution_strategies import ExecutionStrategyFactory
from .step_components import StepComponentManager
from ..gui.logging import get_gui_logger
from .config import SimConfig  # existing core
from ..core.config import VMTConfig  # new wrapper location (final path subject to layout decision)

ConfigLike = Union[SimConfig, VMTConfig]

class Simulation:
    """Unified simulation coordinator with integrated logging and performance tracking."""

    def __init__(self, grid, agents, config: ConfigLike):
        # Normalize to VMTConfig
        if isinstance(config, SimConfig):
            config = VMTConfig(sim=config)  # default wrapper
        self.config = config
        self.grid = grid
        self.agents = agents
        self.step_count = 0

        # Strategy depends on wrapper's execution_mode()
        self.execution_strategy = ExecutionStrategyFactory.create(self, config)
        self.step_components = StepComponentManager(self, config)
        self.performance_tracker = PerformanceTracker(config)
        self.logger = get_gui_logger()
    
    def step(self, rng: random.Random, *, use_decision: bool = False):
        """Execute one simulation step with integrated logging and performance tracking."""
        start_time = time.time()
        
        # Execute the main simulation logic
        self.execution_strategy.execute(rng, use_decision)
        
        # Execute all step components
        self.step_components.execute_all(rng, self.step_count)
        
        # Track performance
        end_time = time.time()
        self.performance_tracker.track_step(self.step_count, start_time, end_time)
        
        # Log performance if needed
        if self.config.should_log_category("PERF"):
            self._log_step_performance(start_time, end_time)
        
        self.step_count += 1
    
    def _log_step_performance(self, start_time: float, end_time: float):
        """Log step performance metrics."""
        step_time = end_time - start_time
        fps = 1.0 / step_time if step_time > 0 else 0
        
        self.logger.log("PERF", 
            f"Step {self.step_count}: {step_time:.4f}s, FPS: {fps:.1f}", 
            self.step_count)
    
    def get_performance_stats(self) -> dict:
        """Get current performance statistics."""
        return self.performance_tracker.get_stats()
    
    def reset_performance_tracking(self):
        """Reset performance tracking."""
        self.performance_tracker.reset()
    
    @classmethod
    def from_config(cls, config: ConfigLike, agent_positions: Optional[List[tuple]] = None):
        """Factory accepting either SimConfig (legacy) or VMTConfig (preferred)."""
        # Implementation remains unchanged except for wrapper normalization.
        pass
```

#### Step 4.2: Update Main Debug Logger
**File**: `src/econsim/gui/debug_logger.py` (Refactored)

```python
"""Centralized GUI debug logging system for VMT EconSim.

Provides unified logging to timestamped files in gui_logs/ directory.
All debug output from simulation components should use this logging system
instead of direct print statements for better organization and GUI integration.
"""

# Import all functionality from new modules
from .logging.logger import GUILogger
from .logging.convenience import (
    get_gui_logger,
    log_agent_mode,
    log_trade,
    log_simulation,
    log_utility_change,
    log_performance,
    finalize_log_session
)
from .logging.formatters import format_agent_id, format_delta

# Maintain backward compatibility
__all__ = [
    "GUILogger",
    "get_gui_logger", 
    "log_agent_mode",
    "log_trade", 
    "log_simulation",
    "log_utility_change",
    "log_performance",
    "finalize_log_session",
    "format_agent_id",
    "format_delta"
]
```

## Implementation Timeline

### Pre-Week (Phase 0 Safeguards)
- [ ] Implement action/trade sequence snapshot freeze test & baseline fixture
- [ ] Implement trade intent ordering tie-break test
- [ ] Implement resource pickup ordering test (unified selection path)
- [ ] Implement RNG call count & sequence test (external & internal RNG)
- [ ] Add baseline fixture regeneration CLI flag / pytest option
- [ ] Add determinism tests documentation (`docs/architecture/determinism_tests.md`)
- [ ] CI gating: determinism tests required green before Phase 1 merges

### Pre-Week (Phase 0.5 RNG Call Order Freeze)
- [ ] Document concrete current per-step RNG call order list (ext vs internal)
- [ ] Implement CountingRNG wrapper (test-only)
- [ ] Generate `rng_call_order_baseline.json` fixture (200 steps)
- [ ] Add `test_rng_call_order_freeze.py`
- [ ] Add `--regenerate-rng-baseline` pytest option & integrate with combined `--regenerate-baselines`
- [ ] Update determinism docs with finalized call order & review checklist
- [ ] Flakiness check: run RNG freeze test 5x locally / CI matrix

### Week 1: Foundation
- [ ] Introduce `VMTConfig` wrapper (composition of existing `SimConfig` + new domains)
- [ ] Add `VMTConfig.from_environment()` helper (wraps `SimConfig.from_environment()`)
- [ ] Add environment parity test (legacy env reads vs wrapper fields)
- [ ] Determinism hash allowlist test (assert wrapper fields excluded)
- [ ] Introduce shared performance tracking (`core/performance.py` or integrate) referencing wrapper
- [ ] Scaffold logging infrastructure modules (interfaces + stubs only)
- [ ] Add factory test: `Simulation.from_config` accepts both `SimConfig` and `VMTConfig`
- [ ] Catalog existing buffers via instrumentation (temporary logging of flush points)
- [ ] Draft `buffer_policies.yaml` (or table) from empirical data
- [ ] Add smoke tests for flush on step change & finalize
- [ ] Implement `ECONSIM_LOG_DEBUG_FLUSH` hook (guarded; off by default)

### Week 2: Logging System
- [ ] Implement all logging modules
- [ ] Create event builders and parsers
- [ ] Implement buffer management
- [ ] Create file I/O manager
- [ ] Test logging system components
- [ ] Implement full buffer policy tests (capacity, interval, batching)
- [ ] Generate `flush_sequence_baseline.json`
- [ ] Remove/disable debug flush hook in production path (leave test flag)
- [ ] Add trade ordering baseline fixture & core ordering test (no priority)

### Week 3: Simulation System
- [ ] Create execution strategies
- [ ] Implement step components
- [ ] Create simulation performance tracker
- [ ] Refactor main Simulation class
- [ ] Test simulation components
- [ ] Add priority trade ordering test & baseline (if priority flag enabled)
- [ ] Add trade selection debug hook & verify determinism unaffected

### Week 4: Integration & Testing
- [ ] Integrate logging and simulation systems
- [ ] Update main debug_logger.py
- [ ] Create comprehensive unit tests
- [ ] Create integration tests
- [ ] Performance validation
- [ ] Documentation updates

## Expected Benefits

### Unified Architecture
- **Shared Configuration**: Single source of truth for all environment variables
- **Integrated Performance Tracking**: Unified performance monitoring across systems
- **Consistent Logging**: Standardized logging interface for all components
- **Reduced Duplication**: Eliminate duplicate configuration and performance code

### Code Quality Improvements
- **Reduced Complexity**: Break down monolithic files into focused modules
- **Better Separation of Concerns**: Clear boundaries between logging, simulation, and configuration
- **Improved Testability**: Isolated components easier to unit test
- **Enhanced Maintainability**: Modular design easier to understand and modify

### Performance Benefits
- **Unified Performance Tracking**: Single performance monitoring system
- **Reduced Memory Usage**: Smaller object graphs and shared components
- **Better Caching**: Isolated components can be optimized independently
- **Faster Imports**: Reduced circular dependencies

### Developer Experience
- **Unified Interface**: Single configuration system for all components
- **Consistent APIs**: Standardized interfaces across logging and simulation
- **Better Documentation**: Focused, modular documentation
- **Easier Extension**: New features can be added as new components

## Risk Mitigation

### Backward Compatibility
- Maintain all existing public APIs
- Preserve all convenience functions
- Keep same file structure for imports
- No breaking changes to existing code

### Performance Impact
- Benchmark before and after refactoring
- Maintain deterministic behavior
- Preserve existing performance characteristics
- Monitor logging overhead (<2% as specified)

### Testing Strategy
- Comprehensive unit tests for all new modules
- Integration tests for complete workflows
- Performance regression testing
- Determinism validation with existing tests

## Success Criteria

### Code Quality Metrics
- [ ] Reduce debug_logger.py from 1,610 lines to <200 lines
- [ ] Reduce world.py from 1,059 lines to <300 lines
- [ ] Create 10+ focused modules with single responsibilities
- [ ] Achieve 90%+ test coverage for new modules
- [ ] Maintain all existing functionality

### Performance Metrics
- [ ] No performance regression in logging overhead
- [ ] Maintain <2% logging overhead as specified
- [ ] Preserve deterministic behavior
- [ ] Maintain FPS targets (≥30 FPS, target ~60 FPS)

### Architecture Metrics
- [ ] Unified configuration system eliminates environment variable duplication
- [ ] Shared performance tracking reduces code duplication
- [ ] Modular design enables independent testing and optimization
- [ ] Clear separation of concerns improves maintainability

## Conclusion

This unified refactoring plan addresses both the debug logger and world.py files as part of a cohesive architecture. By creating shared infrastructure for configuration and performance tracking, we eliminate duplication while improving maintainability and testability.

The phased approach ensures minimal risk while delivering significant improvements to code organization, performance, and developer experience. The result will be a cleaner, more maintainable codebase that's easier to understand, test, and extend while maintaining the performance and determinism characteristics required by the VMT project.
