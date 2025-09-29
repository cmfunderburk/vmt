# Debug Log Fixes (Phase 3 Instrumentation Reconciliation)

Date: 2025-09-28
Context: Post-category normalization (PERF, TRADE) and launcher override removal. Observed logs show partial Phase 3 events only.

## 1. Observed vs Expected Events
Observed (both compact + structured):
- mode_transition (MODE)
- mode_batch (MODE_BATCH)
- periodic_summary (SIMULATION)
- micro_delta_threshold (proper structured event)
- trade (TRADE) executions
- phase_transition (PHASE)

Observed but Problematic:
- Duplicate micro_delta_threshold representation: a second structured line misclassified as event=trade with raw `TI: micro_delta_threshold=...`.

Missing (expected instrumentation):
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

## 2. Root Cause Hypotheses
| Gap | Likely Cause | Notes |
|-----|--------------|-------|
| Missing funnel events | Builder call dropped or gated | Post-refactor indentation fix may have removed invocation. |
| micro_delta duplicate | Trade bundler parses `TI:` lines as trades | Needs pattern exclusion or dedicated category. |
| perf_spike absent | Threshold not crossed or invocation removed | Verify `build_perf_spike` call site still exists with new category. |
| partner_search / reject absent | Unified selection path conditions not met or builder not called | Re-check `_unified_selection_pass` instrumentation. |
| selection_sample absent | Sampling trigger not executed (interval missing) | Add periodic or probability-based trigger with deterministic cadence. |
| respawn events absent | Density sufficient (no deficit) or logging disabled | Confirm respawn logic & builder call. |
| stagnation_trigger absent | Run length too short or condition not reached | Might be acceptable; confirm instrumentation still present. |
| target_churn absent | Retarget tracking list not updated or emission condition missing | Inspect `_recent_retargets` maintenance. |
| overlay_state absent | No overlay toggles changed during run | Acceptable if not toggled; ensure builder wired. |
| config_update absent | No dynamic config changes performed | Acceptable; builder available. |

## 3. Remediation Actions (Proposed Order)
1. Deduplicate micro_delta_threshold:
   - In trade parsing/bundling, skip lines starting with `TI:` (regex `^TI:`) from trade classification.
   - Optionally tag them as meta if needed (currently builder already emits micro_delta event). 
2. Restore / verify trade_intent_funnel emission:
   - Inspect `world.py` trade intent enumeration segment; ensure `build_trade_intent_funnel` call executed if drafting attempted or `drafted>0`.
3. Harden micro-delta one-shot guard:
   - Confirm state variable (e.g., `_micro_delta_emitted`) persists and not reset each step.
4. Partner search & reject:
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

## 4. Determinism Safeguards
- No new random draws; periodic sampling must be step-modulo based.
- Do not alter ordering of existing iteration over agents/resources.
- Keep new env flags read once per step (string→int conversion) without fallback randomness.
- Append-only changes: do not remove existing structured fields.

## 5. Performance Considerations
- Avoid per-step string regex on every trade line for exclusion: pre-check prefix (`message.startswith('TI:')`) before heavier parsing.
- Reuse small static compiled regex objects if needed (module scope) to avoid allocation.
- Limit selection / churn / respawn / churn emission to sparse cadence (e.g., every 200 steps) to keep overhead <2%.

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

## 9. Acceptance Criteria
- No duplicate micro_delta structured entries.
- At least one trade_intent_funnel event appears in structured log under typical run with trading enabled.
- Partner search or selection sample events appear when unified selection active.
- No new nondeterminism (hash unchanged in determinism tests).
- Performance test shows <2% degradation vs pre-fix baseline.
- Documentation updated outlining new events and triggers.

---
End of plan draft.
