# Debug Logging Phase 3 Plan (Draft)

Purpose: Extend logging to cover currently opaque but educationally valuable micro-events while preserving determinism and <1% overhead when enabled. Focus: partner search path, unified selection rationale sampling, respawn scheduler transparency, stagnation/reset mechanics, trade intent funnel quality, and configuration diffs.

## Dual-Output Invariant (New)
Every new Phase 3 event MUST emit:
- Compact human-readable line appended to `gui_logs/<timestamp> GUI.log` (respecting existing log level / category filtering).
- Structured JSONL record appended to `gui_logs/structured/<timestamp> GUI.jsonl` with envelope fields: `ts_rel, category, step, event, ...payload`.

Rules:
- Structured emission is unconditional once the logger is initialized (even if compact line suppressed by aggregation); category gating still applies to avoid unwanted generation cost.
- Event additions are append-only to schema version 1; no version bump unless we break or rename existing keys.
- New keys are optional for downstream parsers; avoid renaming existing fields.
- Payload key order: stable logical grouping (identifiers, counts, metrics, reasons).
- No additional RNG calls or mutation of simulation state for logging.

## 1. Current Coverage (Observed / Documented)
- Mode transitions (single + batch) with reason + carrying count
- Phase transitions with step anchors
- Performance periodic snapshots (steps/sec, ms, counts, phase)
- Batch migrations (S-1 BATCH M lines)
- (In other runs) trade execution lines + utility deltas (when trades occur)
- Potential (not always enabled) resource collection/spawn lines
- Economic utility change explanations (when env flags set)

## 2. Identified Gaps / Blind Spots
| Area | Gap Description | Impact | Priority |
|------|-----------------|--------|---------|
| Partner Search | No visibility into pairing attempts, rejections, cooldown decrements | Hard to debug why few trades occur | High |
| Trade Intent Funnel | Only final executed trade logged; draft enumeration volume & filter reasons invisible | Can't assess pruning effectiveness | High |
| Stagnation Rule | Forced return_home after 100 idle-improvement steps only visible as normal mode change | Loss of root-cause clarity | High |
| Unified Selection | No sampled rationale when decision mode ON (distance-discounted ranking) unless verbose decisions flooding | Hard to teach weighted utility vs distance | Medium |
| Respawn Scheduler | Interval trigger vs skipped cycles (density already satisfied) unseen | Misinterpreting apparent stagnation | Medium |
| Hash / Determinism Changes | Structural schema extensions not logged in-session | Post-hoc triage harder | Medium |
| Config Runtime Changes | `log_config` updates silent beyond env-based boot | Hard to trace shifting verbosity mid-session | Medium |
| Performance Outliers | Only periodic snapshot; spikes between intervals lost | Hidden transient bottlenecks | Medium |
| Trade Stagnation (No Beneficial intents) | No explicit log line when zero intents or all below micro-delta threshold | Ambiguous lack of trades | Medium |
| Agent Target Churn | Rapid retargeting due to close ΔU not summarized | Potential wasted movement undiagnosed | Low |
| Overlay Toggles | Visual layer changes not logged (could confuse analysts) | Minor confusion | Low |

## 3. Proposed New Log Points
Legend: Cat = New / existing category tag; Gate = existing env flag or new one; Cost = est. overhead when enabled.

### 3.1 Partner Search Lifecycle
Compact (success): `PS: A012 scanned=5 eligible=2 chosen=A019 method=nearest-first cooldowns(g=0,p=0)`
Compact (sampled rejection): `PSR: A012 reject=A017 reason=partner_cooldown` (sample 1 per k attempts)
Structured JSON examples:
```json
{"category":"PAIRING","event":"partner_search","agent":12,"scanned":5,"eligible":2,"chosen":19,"method":"nearest-first","cooldowns":{"global":0,"partner":0}}
{"category":"PAIRING","event":"partner_reject","agent":12,"candidate":17,"reason":"partner_cooldown","sampled":true}
```
Category: new `PAIRING` (env `ECONSIM_DEBUG_PAIRING=1`).
Determinism: observational only. Cost: O(sampled events). Sampling k configurable (default 10).

### 3.2 Trade Intent Funnel Summary (per step when draft on)
Compact: `TI: drafted=34 pruned_micro=5 pruned_nonpositive=12 executed=1 maxΔU=0.023`
Structured JSON:
```json
{"category":"TRADES","event":"trade_intent_funnel","drafted":34,"pruned_micro":5,"pruned_nonpositive":12,"executed":1,"max_delta_u":0.023}
```
Category: reuse `TRADES`. Cost: O(1). Source: enumeration counts.

### 3.3 Zero / Idle Trade Annotation
Compact:
- No intents: `TI: none (no_viable_partners)`
- None executed: `TI: none_executed reason=all_filtered_or_micro`
Structured JSON:
```json
{"category":"TRADES","event":"trade_intent_none","cause":"no_viable_partners"}
{"category":"TRADES","event":"trade_intent_none_executed","reason":"all_filtered_or_micro","drafted":12}
```
Category: `TRADES`.

### 3.4 Stagnation Trigger Detail
Compact: `STAG: A007 threshold=100 last_improve=1320 action=return_home deposit`
Structured JSON:
```json
{"category":"STAGNATION","event":"stagnation_trigger","agent":7,"threshold":100,"last_improve":1320,"action":"return_home","deposit":true}
```
Category: new `STAGNATION` (env `ECONSIM_DEBUG_STAGNATION=1`) OR reuse `AGENT_MODE` if we want fewer categories (decision pending). Cost: rare.

### 3.5 Unified Selection Sample (lightweight)
Every N steps (default 50), one rotating agent (deterministic `step % agent_count`).
Compact: `USAMP: A003 k=1.5 cand=[R@(12,9) d=5 ΔU=0.80 ΔU'=0.73, TRADE(A007) d=2 ΔU=0.31 ΔU'=0.26, R@(8,11) d=6 ΔU=0.77 ΔU'=0.67]`
Structured JSON:
```json
{"category":"DECISIONS","event":"selection_sample","agent":3,"k":1.5,"candidates":[{"type":"RESOURCE","pos":[12,9],"d":5,"delta_u":0.80,"delta_u_discounted":0.73},{"type":"TRADE","partner":7,"d":2,"delta_u":0.31,"delta_u_discounted":0.26},{"type":"RESOURCE","pos":[8,11],"d":6,"delta_u":0.77,"delta_u_discounted":0.67}]}
```
Env gate: `ECONSIM_DEBUG_SELECTION_SAMPLE=1`.

### 3.6 Respawn Attempt Transparency
Compact (attempt): `RESP: step=400 deficit=18 target_density=0.25 plan=5 placed=5 remaining=13`
Compact (skipped): `RESP: step=420 skipped (density_satisfied)`
Structured JSON:
```json
{"category":"RESOURCES","event":"respawn_cycle","step":400,"deficit":18,"target_density":0.25,"planned":5,"placed":5,"remaining":13}
{"category":"RESOURCES","event":"respawn_skipped","step":420,"reason":"density_satisfied"}
```
Category: `RESOURCES`.

### 3.7 Config Change Diff (runtime)
Compact: `CFG: level=EVENTS→VERBOSE add={TRADES,PERFORMANCE} remove={DECISIONS} explanations=on`
Structured JSON:
```json
{"category":"SIMULATION","event":"config_update","changes":{"level":{"old":"EVENTS","new":"VERBOSE"},"added_categories":["TRADES","PERFORMANCE"],"removed_categories":["DECISIONS"],"explanations":{"old":false,"new":true}}}
```
Category: `SIMULATION`.

### 3.8 Performance Outlier Spike
Compact: `PERF_SPIKE: step=950 time=14.2ms mean=8.1ms agents=20 resources=225 phase=3`
Structured JSON:
```json
{"category":"PERFORMANCE","event":"perf_spike","step":950,"time_ms":14.2,"rolling_mean_ms":8.1,"agents":20,"resources":225,"phase":3}
```
Category: reuse `PERFORMANCE` (avoid new token). Window size 50.

### 3.9 Trade Micro-Delta Threshold Context (first occurrence)
Compact: `TI: micro_delta_threshold=1e-5 (activating prune)`
Structured JSON:
```json
{"category":"TRADES","event":"micro_delta_threshold","threshold":1e-5,"activated":true}
```
Category: `TRADES` (one-shot per session).

### 3.10 Agent Target Churn Summary (periodic)
Compact: `CHURN: window=200 retarget_events=54 distinct_agents=11 top_agent=A004 count=9`
Structured JSON:
```json
{"category":"DECISIONS","event":"target_churn","window":200,"retarget_events":54,"distinct_agents":11,"top_agent_id":4,"top_agent_events":9}
```
Category: `DECISIONS`.

### 3.11 Overlay Toggle Events
Compact: `OVL: grid=on ids=off arrows=on trades=on highlight=on`
Structured JSON:
```json
{"category":"SIMULATION","event":"overlay_state","grid":true,"ids":false,"arrows":true,"trades":true,"highlight":true}
```
Category: `SIMULATION` (only on change).

## 4. Data Schemas (Concise)
| Event (event field) | Fields (payload keys, excluding envelope) |
|---------------------|---------------------------------------------------------|
| partner_search | agent, scanned, eligible, chosen, method, cooldowns{global,partner} |
| partner_reject | agent, candidate, reason, sampled |
| trade_intent_funnel | drafted, pruned_micro, pruned_nonpositive, executed, max_delta_u |
| trade_intent_none | cause |
| trade_intent_none_executed | reason, drafted |
| stagnation_trigger | agent, threshold, last_improve, action, deposit |
| selection_sample | agent, k, candidates[{type,pos|partner,d,delta_u,delta_u_discounted}] |
| respawn_cycle | step, deficit, target_density, planned, placed, remaining |
| respawn_skipped | step, reason |
| config_update | changes{...diff objects...} |
| perf_spike | step, time_ms, rolling_mean_ms, agents, resources, phase |
| micro_delta_threshold | threshold, activated |
| target_churn | window, retarget_events, distinct_agents, top_agent_id, top_agent_events |
| overlay_state | grid, ids, arrows, trades, highlight |

## 5. Determinism & Performance Safeguards
- All logs are observational; no new RNG calls.
- Sampling (USAMP, CHURN) uses deterministic modulus scheduling.
- Counters stored in simulation scope; excluded from determinism hash (confirm test coverage before merge).
- Feature-gated via new env flags where risk of verbosity exists.
- Cost model: Each added O(1) string format; loops avoided; candidate list truncated to top N=3 for selection sample.

## 6. Implementation Steps (Ordered)
1. Add new env flags & categories (PAIRING, STAGNATION; reuse existing others) + update `_should_log_category`.
2. Extend `debug_logger` with helper functions that build BOTH `compact_str` and `structured_payload` (single source of truth) returning a pair.
3. Wire instrumentation points (each call site invokes helper, then logger writes compact (if level/category passes) AND always structured side-channel):
   - Partner search loop (before commit to pair) -> PS / rejection sample
   - Trade intent enumeration -> funnel summary + micro-delta threshold one-shot
   - Stagnation rule trigger site -> STAG
   - Selection function -> conditional sampling (only when scheduled step & agent chosen)
   - Respawn scheduler -> RESP lines
   - Config manager update method -> CFG diff
   - Performance monitor (existing periodic) -> add rolling mean & spike detection
   - Target assignment changes -> increment churn counters
   - Overlay toggle handler -> OVL snapshot
4. Add tests (both compact + structured assertions):
   - Determinism test verifying hash unchanged with new flags off
   - Unit test for funnel summary formatting (parse & validate counts)
   - Spike detection test using synthetic timings
   - Config diff test (ensure only changed fields printed)
   - Stagnation trigger log presence test (force condition with low threshold override)
5. Update docs: `DEBUG_LOGGING_OPTIONS.md` + brief note in `README.md` + environment variable reference.
6. Update `.github/copilot-instructions.md` only if new hash-excluded metrics are introduced (else skip). Structured events remain hash-excluded.

## 7. Flag Naming Proposal
- `ECONSIM_DEBUG_PAIRING=1`
- `ECONSIM_DEBUG_SELECTION_SAMPLE=1`
- `ECONSIM_DEBUG_STAGNATION=1` (optional; otherwise reuse AGENT_MODES)
- `ECONSIM_DEBUG_CHURN=1` (if churn separated; else fold into DECISIONS)

## 8. Risk Assessment
| Risk | Mitigation |
|------|------------|
| Verbose logs harming performance | Sampling + gating flags |
| Hash drift from counters | Keep counters non-serialized; confirm via determinism tests |
| Duplicate category sprawl | Reuse existing where logically consistent (TRADES, DECISIONS, RESOURCES) |
| Developer confusion on sampling intervals | Document defaults; maybe runtime config fields |
| Overlapping event semantics (PS vs TRADES) | Distinct prefixes (PS, TI) |

## 9. Acceptance Criteria
- With all new flags OFF: zero diff in determinism hash & no new log lines (compact or structured) for new event types.
- Enabling each flag produces expected exemplar line in BOTH files within 5 steps (scenario permitting).
- Performance overhead measured via `scripts/perf_stub.py` <1% delta (document sample output).
- Documentation updated and consistent with output.
- Tests protect funnel summary formatting & spike detection.

## 10. Open Questions (For Feedback)
- Should churn summary include average ΔU of discarded previous targets? (cost: extra accumulation)
- Merge pairing into `SPATIAL` or keep dedicated `PAIRING` for clarity?
- Add JSON STRUCTURED format option for funnel & sample lines (future dashboard)? (Already covered by dual-output requirement.)

---
Draft complete – awaiting feedback for adjustments (scope trims, naming tweaks, additional events desired).
