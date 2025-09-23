# Phase P3 Decision Logic Issues & Options (2025-09-22)

## Summary
Implementing Phase P3 exposed two regressions: agents enter IDLE immediately (no resources collected) because ΔU scoring uses only carrying inventory (all zero) and distance > 0 reduces nothing—actually issue is they never move since target selection sets a target but movement only happens if target differs, then after collecting first move might not happen due to immediate idle condition. We also overrode `Simulation.step` default to use decision logic, breaking existing random-walk collection test expectations.

## Failures Observed
1. test_decision_determinism_basic: Fails final assertion because both agents end up IDLE while resources remain.
2. test_simulation_collection_progress: Now runs decision branch (default use_decision=True) and agent never collects any resource.

## Root Causes
- Movement logic: If target selected, we move horizontally if abs(dx)>abs(dy) else vertical. Likely fine. Real problem: Why target not set? Potential because all ΔU computations result in >0, but after selecting target and moving one step, collect() only triggers when at resource. That part is OK. The test shows zero collection over 50 steps, meaning target not pursued or is cleared prematurely.
- Inspection: After moving toward target, we call collect(); if not at resource collected=False; we do not clear target. So repeated steps should eventually reach resource. But test shows zero increments. Hypothesis: Decision loop re-selects target each step (because we call select_target when `self.target is None or self.mode in (IDLE, FORAGE)`). Since mode FORAGE triggers reselection every tick, tie-break chooses maybe nearest but continuous reselection resets target; movement occurs though. That should still move toward same or potentially switch; still should collect eventually. Another factor: ΔU calculation uses bundle with carrying only, which remains zero until first collection; with Cobb-Douglas with x=0,y=0, utility=0; adding 1 to either yields utility 0? Actually Cobb-Douglas returns 0 if either good quantity <=0. Starting bundle (0,0) => base_u=0. test_bundle for good1: (1,0) gives utility 0 (because y=0). Similarly (0,1) gives 0. So delta_u = 0, all filtered out (delta_u <=0). Thus no targets selected; mode becomes IDLE immediately. That's the core issue.

## Fix Strategy Considered
- Marginal utility with zero of the other good is zero under Cobb-Douglas; need bootstrap rule: treat incremental acquisition of a zero-good pair as positive by using a modified delta calculation: Evaluate utility at (bundle + ε for the other good) or treat delta for first unit as positive constant. Simplest: Introduce bootstrap rule: if base bundle has a zero in the other good, compute candidate utility with that other good set to epsilon (e.g., 1e-6) before evaluation to get positive delta.

- Alternative: Use (carrying + home_inventory) totals so if home has some goods deposited, deltas become positive. Initially all zero so still issue.

## Decision Point (Need your preference):
A. Introduce epsilon bootstrap for Cobb-Douglas only (generalizable).
B. Special-case: If base_u == 0 and resource adds one unit of a good currently zero, set delta_u = 1.0 heuristic.
C. Instead of pure preference for initial step, allow any resource to have delta_u=1 until first collection (simplest deterministic tie-break via position order).

## Recommendation
Option C (uniform positive delta for first unit of any good when both goods not yet >0) keeps logic simple and deterministic, and educationally agents start collecting. After first unit collected, one good is >0; second good still yields zero utility if its quantity is zero, so we need second bootstrap when one good >0 and the other is zero to encourage diversification or else agent will never switch. Cobb-Douglas utility stays zero until both goods >0, so we must extend bootstrap: treat delta_u as 1.0 if adding a good turns its quantity from 0→1 regardless of the other good values. Once both goods >0, use real ΔU.

Thus implement bootstrap rule: if target good quantity before addition is 0, define effective delta_u = 1.0 (or compute with temporary epsilon for other zeros). This satisfies preference shift test later because real ΔU eventually used.

## Tie-break
Unchanged under bootstrap.

## Simulation Default Behavior
- Option to revert Simulation.step default to use_decision=False until Gate 4 fully integrated to avoid breaking legacy tests.

## Next Steps Pending Confirmation
1. Implement bootstrap (constant 1.0 when quantity of that good is zero) in select_target.
2. Adjust selection gating to avoid reselection every tick (only reselection when target None or resource collected / mode change).
3. Consider changing Simulation.step default use_decision back to False until new tests cover decision path.
4. Re-run full suite, add determinism test updates.

## Awaiting Confirmation
Need choice on:
1. Bootstrap methodology: A (epsilon), B (constant 1.0), C (two-phase constant as described) — recommended C.
2. Simulation.step default: keep True or revert to False (recommend revert to False now).

(Provide confirmation, e.g., "Use C and revert default" to proceed.)
