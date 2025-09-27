# Logging Style Conformance & Improvement Analysis (2025-09-26)

Source Log Reviewed: `2025-09-26 22-02-02 GUI.log` (baseline scenario, enhanced-tests path)

## 1. Conformance Highlights
- Header present (session start, level, format) + separator
- Core patterns: mode switches, trades, phase lines, periodic summaries, session terminator
- Deterministic prefixes: `S{step}` and time offset `+{seconds}s`
- Trade lines include participants, goods, delta utility

## 2. Deviations & Inconsistencies
| Category | Observation | Impact | Action Priority |
|----------|-------------|--------|-----------------|
| Agent ID format | Mixed `A002` vs `A0`, `A15` | Inconsistent grep / visual alignment | Low (formatting) |
| Sign formatting | `+-1.0`, `+-0.0` appear | Noise / potential confusion | Low |
| Duplicate phase lines | Both `PHASEn@turn:` and `PHASE TRANSITION:` | Redundant vertical space | Low |
| Periodic summary ordering | `S100 PERIODIC STATUS` appears later than initial S100 lines | Temporal confusion | Medium |
| Two periodic styles | Raw `S25: Agents: ...` vs `S50: PERIODIC STATUS:` | Mixed grammar | Medium |
| SPAM_BATCH dual semantics | Single vs aggregated forms under same tag | Parser ambiguity | Medium |
| Trade ↔ utility linkage | Utility deltas not always adjacent to trades | Harder causal reading | Medium |
| Repetitive invariant fields | `Decision: True` always repeated | Log bloat | Low |
| Reason annotation inconsistency | Some stagnation lines annotated, others not | Context loss | Low |
| Trade burst ordering | Multiple trades same timestamp w/o explicit ordering token | Debug sequence ambiguity | Medium |
| Batch counts omit IDs | Aggregated SPAM lacks agent list | Traceability gap | Medium |

## 3. Improvement Tiers
### Tier 1 (Low-Risk Formatting)
1. Uniform agent IDs (recommend zero-padded width=3)  
2. Normalize delta sign (eliminate `+-`; convert near-zero to `+0.0`)  
3. Single phase transition line (keep `PHASE{n}@{turn}: desc`)  
4. Emit periodic summaries inside the step (no retroactive logging)  
5. Consolidate periodic grammar: adopt `S{step} P:` variant  
6. Standardize reason suffix `(stagnation)` / `(paired for trade)`  
7. Replace `SPAM_BATCH` with `BATCH` and structured payload  
8. Fixed timestamp precision (e.g. one decimal place)  

### Tier 2 (Medium – Aggregation & Context)
1. Trade+utility bundling line (emit paired utility changes)  
2. Batch mode switches (threshold-based) with sample IDs  
3. Add sequence token for multi-line same-step bursts (`S825.1`)  
4. Structured key-value suffix (e.g. `|r=150|ph=2`)  

### Tier 3 (Semantic Enhancements)
1. Per-phase summary block at transition (avg utility, trades, resources, FPS mean)  
2. Anomaly detection lines (large negative/positive deltas)  
3. Cumulative counters every 250 steps (trades total, % positive)  

### Tier 4 (Future / Optional)
1. Parallel JSON structured log (hash-neutral)  
2. Gzip-on-close archival with manifest line  
3. Determinism hash checkpoints every N steps  

## 4. Canonical Revised Grammar (Proposal)
- Mode Switch: `+Ts S{step} M: A{id} {old}->{new} c{carry} @(x,y) [reason]`
- Trade (bundled): `+Ts S{step} T: A{s}↔A{b} {give}->{recv} Δ{du} | U {s}:{o}->{n} Δ{d}; {b}:{o}->{n} Δ{d}`
- Periodic Perf: `+Ts S{step} P: {steps_per_sec}s/s {frame_ms}ms R{res} Ū{avg} Trades{count}`
- Phase Transition: `+Ts S{turn} PHASE: {from}->{to} {label}`
- Batch Switch: `+Ts S{step} BATCH M: {count} {old}->{new} ids=[A001,A007,...]`

## 5. Root Cause Hypotheses
| Issue | Likely Cause | Mitigation |
|-------|--------------|------------|
| Late periodic lines | Logged from delayed timer / post-loop aggregator | Move emission inside main frame pipeline post-step |
| Mixed agent ID formatting | Direct f-string usage scattered | Central `format_agent_id()` helper |
| `+-` sign artifacts | Double sign join + negative zero float | Sanitize with `if abs(x)<eps: x=0` then `f"{x:+.1f}"` |
| SPAM_BATCH ambiguity | Shared label for two internal code paths | Single aggregator function; distinct label grammar |
| Duplicate phase lines | Controller + phase manager both log | Single source of truth (phase manager) |
| Trade ordering ambiguity | Iteration over dict / set or un-sequenced list | Stable list + enumerate sequence index token |

## 6. Diagnostics Before Refactor
Add single session-end block (temporary, hash-neutral):
```
SESSION DIAGNOSTICS: types={M:1234,T:210,P:40,PHASE:5,BATCH:12} late_periodic=3 max_trade_burst=7
```
Plus optional detection: any periodic step logged >2 real-time ticks after its step.

## 7. Implementation Order (Incremental Safety)
1. Helpers (ID + delta formatting) + replace usages
2. Remove duplicate phase line; confirm test coverage unaffected
3. Relocate periodic emission; add guard test asserting chronological order
4. Batch grammar unification (`BATCH` structure)
5. Optional trade+utility bundling behind feature flag

## 8. Determinism & Performance Considerations
- All Tier 1 changes are formatting-only: state & ordering unaffected (keeps determinism hash stable).  
- Avoid additional per-step allocations: reuse buffers for bundling; preallocate format strings where hot.  
- If bundling utilities: ensure underlying utility retrieval uses already-computed values (no recomputation loops).  

## 9. Acceptance Criteria for Cleanup Pass
- No `+-` patterns in new logs (regex `\+-` absent)
- No duplicate phase lines (count of `PHASE TRANSITION:` = 0)
- Periodic lines strictly increasing in step & appear once per interval
- Agent IDs match regex `A\d{3}` (or chosen canonical variant) 100%
- BATCH lines uniform JSON-ish key=value token format

## 10. Open Questions (For Next Discussion)
1. Do we standardize on zero-padded IDs (readability) or raw (brevity)?
2. Is bundling trade + utility mandatory or flag-gated for pedagogical pacing?
3. Desired periodic interval (currently 25 steps sometimes implied) — fix at 25 or adaptive on variance?
4. Include avg utility in periodic perf line by default?

---
Prepared for follow-on implementation planning. All recommendations are determinism-safe if confined to formatting layer.
