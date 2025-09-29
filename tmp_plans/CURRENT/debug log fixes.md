# Debug Log Instrumentation Completeness Review

Date: 2025-09-28
Context: Post-architectural refactor to structured-only logging (.jsonl). Single source of truth established. Need to audit and complete missing instrumentation events.

## 1. Current State: Structured-Only Logging (.jsonl)
✅ **Working Events** (confirmed in latest logs):
- mode_transition (MODE) - Individual agent transitions with structured context
- mode_batch (MODE_BATCH) - Batch transitions with agent arrays  
- periodic_summary (SIMULATION) - Performance metrics every 25 steps
- micro_delta_threshold (TRADE) - Proper structured event at simulation start
- trade (TRADE) - Individual trade executions with raw text
- phase_transition (PHASE) - Phase changes with structured metadata
- session_end (SESSION) - Clean structured session termination

❌ **Problematic** (FIXED in architectural refactor):
- ~~Duplicate micro_delta_threshold~~: No longer occurs since compact log eliminated
- ~~Mixed format pollution~~: Pure JSON Lines now

❌ **Missing Instrumentation** (gaps to address):
- trade_intent_funnel (TRADE)
- trade_intent_none / trade_intent_none_executed (TRADE) [context dependent]
- perf_spike (PERF) [conditional]
- partner_search (PAIRING)
- partner_reject (PAIRING)
- selection_sample (DECISIONS, compact prefix USAMP)
- respawn_cycle / respawn_skipped (RESOURCES) [density dependent]
- stagnation_trigger (STAGNATION) [long-run condition]
- target_churn (DECISIONS, prefix CHURN)
- overlay_state (SIMULATION) [when toggles change]
- config_update (SIMULATION) [dynamic logging adjustments]

## 2. Root Cause Analysis (Updated for Structured-Only)
| Gap | Likely Cause | Priority | Notes |
|-----|--------------|----------|-------|
| Missing funnel events | Builder call missing or condition not met | HIGH | Critical for trade analysis |
| ~~micro_delta duplicate~~ | ~~FIXED~~ | ~~N/A~~ | ~~Eliminated with compact log removal~~ |
| perf_spike absent | Threshold not reached or builder not called | MEDIUM | May be conditional on performance degradation |
| partner_search / reject absent | Unified selection path conditions not met or builder not called | Re-check `_unified_selection_pass` instrumentation. |
| selection_sample absent | Sampling trigger not executed (interval missing) | Add periodic or probability-based trigger with deterministic cadence. |
| respawn events absent | Density sufficient (no deficit) or logging disabled | Confirm respawn logic & builder call. |
| stagnation_trigger absent | Run length too short or condition not reached | Might be acceptable; confirm instrumentation still present. |
| target_churn absent | Retarget tracking list not updated or emission condition missing | Inspect `_recent_retargets` maintenance. |
| overlay_state absent | No overlay toggles changed during run | Acceptable if not toggled; ensure builder wired. |
| config_update absent | No dynamic config changes performed | Acceptable; builder available. |

## 3. Action Plan (Structured-Only Focus)

### Phase 1: High Priority Gaps (Blocking Trade Analysis)
1. **Restore trade_intent_funnel emission**:
   - Audit `world.py` trade intent enumeration; verify `build_trade_intent_funnel` call exists and conditions met
   - Emit structured event with `{drafted, pruned, executed}` counts per step
2. **Verify partner search instrumentation**:
   - Ensure calls to `build_partner_search` and `build_partner_reject` appear in unified selection path after evaluation. Add sampling logic if absent.
5. Selection sample emission:
   - Introduce deterministic periodic sample: e.g., every N steps (env var `ECONSIM_SELECTION_SAMPLE_PERIOD`, default 200) or a low fixed step modulo, using no randomness (preserves determinism).
6. Perf spike event:
   - Confirm rolling mean + threshold code path still calls `build_perf_spike`. If threshold too high, add env override `ECONSIM_PERF_SPIKE_FACTOR` (default e.g. 1.35) to tune.
7. Respawn cycle/skipped:
   - Verify builder calls located in respawn logic; emit `respawn_skipped` when gating condition fails (density adequate). Adjust to log first occurrence per mode configuration to avoid spam.
8. Target churn:
   - Ensure retarget tracking list updated whenever agent target changes; schedule periodic emission every K steps (env `ECONSIM_CHURN_WINDOW` + `ECONSIM_CHURN_EMIT_PERIOD`).
9. Stagnation trigger:
   - Review threshold variable; confirm builder call not accidentally removed; optional: emit a sampled early warning once half-threshold reached (flag gated) for visibility (future enhancement, not required now).
10. Overlay state / config_update:
    - Confirm builder functions exist; wire overlay toggles in GUI if not already; leave as “on demand” (no constant polling).

## 4. Structured Logging Principles
- **Pure JSON Lines**: All events must be valid JSON objects with consistent schema
- **Determinism Preserved**: No random sampling, use step-modulo patterns only
- **Append-Only Fields**: Extend existing events, don't remove structured fields
- **Performance Conscious**: Batch expensive operations, avoid per-agent overhead

## 5. Implementation Strategy
- **Direct Structured Emission**: Use `emit_built_event()` directly, skip raw text parsing
- **Efficient Batching**: Group related events (mode transitions already batched)
- **Sparse Sampling**: Limit analytics events to every 200+ steps to maintain 60+ FPS
- **Schema Consistency**: Use existing event patterns as templates

## 6. Implementation Checklist
- [ ] Patch `debug_logger._parse_trade` (or earlier bundler decision) to return early if line begins with `TI:`.
- [ ] Confirm and, if missing, re-add funnel builder call in `world.py` after enumeration (with drafted/pruned metrics).
- [ ] Validate micro-delta guard variable persists; add if absent.
- [ ] Audit unified selection path for partner_search / partner_reject calls; add deterministic sampling (e.g., first 3 per step or step%P==0 for sample emission).
- [ ] Add selection_sample periodic emission (e.g., step%250==0) with top-N ranking snapshot.
- [ ] Verify perf spike code path; optionally add env factor override; keep default logic unchanged if not necessary.
- [ ] Check respawn logic and ensure both cycle and skipped events can emit (first occurrence + every M steps optional throttle).
- [ ] Ensure retarget tracking updated; implement churn emission every `CHURN_EMIT_PERIOD` reading window length env or config.
- [ ] Confirm stagnation trigger builder call still present.
- [ ] Create or update doc enumerating each event: trigger condition, category, structured fields.
- [ ] Run determinism test suite and perf check.

## 7. Open Questions / Points to Confirm
- Should selection_sample include both resource & trade candidates always, or only when unified selection active? (Proposed: only when unified active to avoid confusion.)
- Acceptable frequency for target churn emission? (Default suggestion: every 500 steps.)
- Keep micro_delta_threshold event at step -1 (initial enumeration context) or assign first real step? (Currently step -1 used; acceptable if documented.)

## 8. Risks
- Overlapping category gating could still filter new events at non-VERBOSE levels (need to verify categories appear in EVENTS level if they are considered events; may require classification update if necessary).
- Potential performance regression if churn or selection snapshots allocate large candidate arrays each emission (mitigate by slicing top N for compact line only; structured can include full list sparingly).

## 6. Next Steps Discussion

### Architectural Benefits Achieved ✅
- **Eliminated complexity**: No more dual-file management
- **Single source of truth**: Pure structured JSON Lines format  
- **GUI integration**: Reads structured logs, formats for human display
- **Clean session management**: Proper JSON session_end events

### Immediate Priorities for Instrumentation Gaps
1. **Audit existing builders**: Check which `build_*` methods exist but aren't being called
2. **Identify missing conditions**: Determine why certain events aren't triggering
3. **Add missing instrumentation**: Focus on trade analysis gaps first
4. **Validate with tests**: Ensure new events appear in typical simulation runs

### Questions for Discussion
- **Scope**: Should we tackle all missing events or focus on trade/performance analysis?
- **Priority**: Which gaps are blocking current analysis workflows?
- **Testing**: How should we validate that new events are working correctly?
- **Performance**: What's our acceptable overhead budget for additional instrumentation?

## 7. Acceptance Criteria (Updated)
- ✅ Pure structured JSON log format (no format pollution)
- ✅ Clean session management with structured session_end
- [ ] Trade funnel events appear when trading enabled
- [ ] Partner selection metrics available during unified selection
- [ ] Performance spike detection functional
- [ ] All new events preserve determinism (hash tests pass)
- [ ] Simulation maintains 60+ FPS target with new instrumentation

---
Ready for discussion and next phase planning.
