# VMT EconSim Logging

Based on the comprehensive analysis in `formatting_plan.md` and current logging system state.

## 📋 Implementation Phases

### Phase 1: Foundation Cleanup (Low Risk, High Impact)
**Status**: Ready to implement  
**Risk Level**: Minimal - Pure formatting changes  
**Estimated Time**: 2-3 hours  

#### 1.1 Agent ID Standardization
- [x] Create `format_agent_id(agent_id: int) -> str` helper function
- [x] Return zero-padded format: `A{agent_id:03d}` (A000, A001, A002...)
- [x] Replace all direct f-string agent formatting with helper in debug_logger.py
- [x] Replace agent formatting in embedded_pygame.py overlay system
- [x] Replace key usages in GUI panel files (trade_inspector, event_log)
- [x] Add virtual environment note to copilot instructions
- [ ] Update tests to expect consistent `A\d{3}` format
- [ ] **Files modified**: `src/econsim/gui/debug_logger.py`, `src/econsim/gui/embedded_pygame.py`, `src/econsim/gui/panels/trade_inspector_panel.py`, `src/econsim/gui/panels/event_log_panel.py`, `.github/copilot-instructions.md`

#### 1.2 Delta Sign Normalization ✅ COMPLETE
- [x] Replace manual `Δ{sign}{delta:.2f}` with helper function `format_delta()`
- [x] Eliminate `+-0.0` artifacts in utility logging
- [x] **Files modified**: `src/econsim/gui/debug_logger.py`, panels, overlays
- [x] **Test cases**: Verified +-0.0 artifacts eliminated, negative values preserved for debugging
- [x] **Implementation**: Added `format_delta(value: float) -> str` helper with special handling for small positives (rounds to 0.0) vs small negatives (preserved for debugging)m TODOs (2025-09-26)

#### 1.3 Timestamp Precision Standardization ✅ COMPLETE
- [x] Fix all timestamps to 1 decimal place: `f"+{seconds:.1f}s"`
- [x] Ensure consistent precision across all message types
- [x] **Files modified**: `src/econsim/gui/debug_logger.py`
- [x] **Implementation**: Wall clock time counting from 0.0s at simulation initialization (not step-based calculation)

#### 1.4 Remove Duplicate Phase Lines ✅ COMPLETE
- [x] Identify source of duplicate `PHASE{n}@turn:` vs `PHASE TRANSITION:` lines
- [x] Keep only `PHASE{n}@{turn}: {description}` format  
- [x] Ensure single source of truth for phase transitions
- [x] **Files modified**: `MANUAL_TESTS/test_1_baseline_simple.py`, `MANUAL_TESTS/framework/phase_manager.py`
- [x] **Implementation**: Removed duplicate `log_comprehensive()` calls that created `PHASE TRANSITION:` entries alongside structured `PHASE{n}@{turn}:` format

### Phase 2: Grammar & Structure Consistency (Medium Risk)
**Status**: Ready after Phase 1  
**Risk Level**: Low-Medium - Logic changes but no state impact  
**Estimated Time**: 3-4 hours  

#### 2.1 Periodic Summary Consolidation
- [ ] Audit all periodic logging sources
- [ ] Standardize on `S{step} P: {steps_per_sec}s/s {frame_ms}ms R{resources}` format
- [ ] Move periodic emission inside main step pipeline (no retroactive logging)
- [ ] Add chronological order test: periodic lines appear in step order
- [ ] **Files to modify**: Performance logging in world.py, debug_logger.py

#### 2.2 Batch Mode Switch Grammar
- [ ] Replace `SPAM_BATCH` with structured `BATCH M:` format
- [ ] Implement consistent aggregation: `{count} agents {old}→{new}`
- [ ] For small groups (≤5): include agent IDs `ids=[A001,A007,...]`
- [ ] For large groups (>5): show count only
- [ ] **Files to modify**: `src/econsim/gui/debug_logger.py`

#### 2.3 Reason Annotation Standardization
- [ ] Standardize suffix patterns: `(stagnation)`, `(paired for trade)`, `(force_deposit)`
- [ ] Ensure consistent application across all mode transitions
- [ ] Document reason codes in logging README
- [ ] **Files to modify**: Agent transition logging, debug_logger.py

### Phase 3: Semantic Enhancements (Medium-High Risk)
**Status**: Requires Phase 1-2 completion  
**Risk Level**: Medium - New features, potential performance impact  
**Estimated Time**: 4-6 hours  

#### 3.1 Trade+Utility Bundling (Optional Feature Flag)
- [ ] Design bundled format: `S{step} T: A{s}↔A{b} {give}→{recv} Δ{du} | U {s}:{old}→{new} Δ{delta}; {b}:{old}→{new} Δ{delta}`
- [ ] Implement behind `ECONSIM_LOG_BUNDLE_TRADES=1` flag
- [ ] Ensure utility values are already computed (no recomputation)
- [ ] Add test coverage for bundled vs unbundled formats
- [ ] **Files to modify**: Trade execution logging, debug_logger.py

#### 3.2 Trade Burst Sequence Tokens
- [ ] Add sequence tokens for multi-trade steps: `S825.1`, `S825.2`, etc.
- [ ] Implement stable ordering (deterministic iteration)
- [ ] Ensure sequence tokens don't affect determinism hash
- [ ] **Files to modify**: Trade logging, debug_logger.py

#### 3.3 Structured Metadata Suffix
- [ ] Add key-value metadata: `|r={resource_count}|ph={phase_number}`
- [ ] Keep hash-neutral (excluded from determinism calculations)
- [ ] Make configurable via log level/format flags
- [ ] **Files to modify**: Periodic logging, debug_logger.py

### Phase 4: Advanced Features (Future/Optional)
**Status**: Post Phase 3, design-dependent  
**Risk Level**: High - Major architectural changes  
**Estimated Time**: 8-12 hours  

#### 4.1 Per-Phase Summary Blocks
- [ ] Design phase transition summary format
- [ ] Collect metrics: avg utility, trade count, resource count, FPS
- [ ] Emit at phase boundaries
- [ ] **Dependencies**: Metrics collection system

#### 4.2 Anomaly Detection
- [ ] Define thresholds for "large" utility deltas
- [ ] Flag unusual patterns: mass mode switches, utility spikes
- [ ] Keep hash-neutral and performance-aware
- [ ] **Dependencies**: Historical data analysis

#### 4.3 Session Diagnostics
- [ ] Implement session-end diagnostics block
- [ ] Count message types: `{M:1234,T:210,P:40,PHASE:5,BATCH:12}`
- [ ] Detect late periodic logging (>2 real-time ticks after step)
- [ ] **Files to modify**: Session finalization, debug_logger.py

## 🧪 Testing Strategy

### Phase 1 Tests
- [ ] Add regex tests for agent ID format: `A\d{3}`
- [ ] Add regex tests for delta format: no `\+-` patterns
- [ ] Add phase line uniqueness test: only one format appears
- [ ] Add timestamp precision test: consistent decimal places

### Phase 2 Tests
- [ ] Add chronological order test for periodic lines
- [ ] Add batch format validation tests
- [ ] Add reason annotation coverage tests

### Phase 3 Tests
- [ ] Add bundling format validation (when flag enabled)
- [ ] Add sequence token ordering tests
- [ ] Add metadata suffix parsing tests

## 🎯 Success Criteria

### Phase 1 Acceptance
- [ ] All agent IDs match `A\d{3}` pattern (100% compliance)
- [ ] No `+-` patterns in any log output
- [ ] No duplicate phase transition lines
- [ ] All timestamps have exactly 1 decimal place

### Phase 2 Acceptance
- [ ] All periodic lines appear in chronological step order
- [ ] Consistent `BATCH M:` grammar for all aggregated switches
- [ ] Reason annotations applied consistently

### Phase 3 Acceptance
- [ ] Bundled trade format works correctly (when enabled)
- [ ] Sequence tokens maintain deterministic ordering
- [ ] Metadata suffixes parse correctly and remain hash-neutral

## 🚨 Risk Mitigation

### Determinism Protection
- [ ] Run full determinism test suite after each phase
- [ ] Verify hash parity remains stable
- [ ] Test with/without new features to ensure no state impact

### Performance Monitoring
- [ ] Run performance tests after each phase
- [ ] Monitor for allocation increases in hot loops
- [ ] Validate FPS remains ≥30 (target 60)

### Rollback Plan
- [ ] Git branch per phase for easy reversion
- [ ] Feature flags for optional enhancements
- [ ] Maintain legacy format compatibility during transition

## 📊 Implementation Priority

**Recommended Order**: Phase 1 → Phase 2 → Evaluate Phase 3 need

**Rationale**:
- Phase 1 provides immediate visual improvement with zero risk
- Phase 2 addresses parser ambiguity and consistency issues
- Phase 3 should be evaluated based on actual educational usage patterns

## 🔄 Next Steps Discussion Points

1. **Agent ID Format**: Confirm zero-padded `A000-A999` vs alternatives
2. **Bundling Priority**: Is trade+utility bundling essential for educational clarity?
3. **Performance Budget**: What's acceptable overhead for enhanced logging?
4. **Feature Flags**: Which enhancements should be permanently enabled vs optional?
5. **Timeline**: Preferred implementation schedule and testing phases

---

**Status**: Ready for implementation discussion and prioritization  
**Last Updated**: 2025-09-26  
**Dependencies**: Current logging system in `src/econsim/gui/debug_logger.py`