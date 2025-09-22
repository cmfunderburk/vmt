# Gate 1 Risk Register

| ID | Risk | Category | Impact | Likelihood | Mitigation | Trigger / Watch Signal | Status |
|----|------|----------|--------|------------|------------|-------------------------|--------|
| R1 | Pygame embed fails in QWidget | Integration | Medium | Medium | Use off-screen Surface -> QImage paint fallback | Segfaults / blank region | Open |
| R2 | Event loop starvation (while True) | Stability | High | Low | Enforce QTimer 16ms pattern; code review guard | UI freeze / unresponsive close | Controlled |
| R3 | FPS below 30 for trivial render | Performance | Medium | Medium | Reduce surface size; avoid per-frame conversion | avg_fps < 30 in perf output | Open |
| R4 | Teardown leaking SDL resources | Resource | Medium | Low | Centralize cleanup in closeEvent; idempotent quit | Warnings on exit / zombie proc | Open |
| R5 | CI headless incompatibility | Tooling | Medium | Low | Add QT_QPA_PLATFORM=offscreen or xvfb if needed | CI failure creating QApplication | Open |
| R6 | Scope creep (agents/economics early) | Scope | High | Medium | Gate 1 checklist + guardrails; PR review | Non-render code added prematurely | Open |
| R7 | CPU overuse due to inefficient blits | Performance | Low | Medium | Limit surface size; reuse QImage buffer | High steady CPU with trivial scene | Open |
| R8 | Memory growth each frame | Performance | Medium | Low | Reuse surface; no per-frame object churn | RSS climb over 5s test | Open |
| R9 | Over-engineering logging/config | Productivity | Medium | Medium | Defer until Gate 2; comment reminders | New config/log modules appear | Open |
| R10 | Pygame + PyQt version incompat future | Dependency | Medium | Low | Pin versions after success; lock file post-G1 | Unexpected break after upgrade | Pending |

## Mitigation Playbook Details
- Fallback Rendering Path: Always maintain off-screen Surface pipeline until native handle embedding proven stable.
- Performance Measurement: Use `scripts/perf_stub.py` after each render path change; paste JSON in PR.
- Exit Validation: Manual check with `ps -ef | grep python` (no lingering process) after closing window.
- Guardrails Enforcement: Add header comment in new modules: `# Gate 1: Do not add agents/economics here.`

## Escalation Criteria
- Two consecutive failed attempts to stabilize embedding → lock in off-screen approach; postpone native embed experiment to dedicated spike.
- avg_fps <25 after optimizations → document constraint; proceed (still acceptable for Gate 1) while creating follow-up perf task.

## Decision Log (Updates)
- (Pending) None yet; log deviations here.

---
Owner: Chris F.
Created: 2025-09-22
