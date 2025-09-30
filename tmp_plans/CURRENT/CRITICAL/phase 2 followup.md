I'll inspect the simulation directory and current step implementation to evaluate Phase 2 progress. 

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation)

I'll inspect the execution subdirectory to see which handlers exist. 

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution)

I'll inspect handler files to assess implemented parts. 

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/handlers)

I'll read the handler files and executor to evaluate completeness. 

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/context.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/result.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/handlers/protocol.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/handlers/movement_handler.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/handlers/collection_handler.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/handlers/trading_handler.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/handlers/metrics_handler.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/handlers/respawn_handler.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/step_executor.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/execution/__init__.py)

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/world.py#1-1), lines 1 to 220

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/world.py#220-220), lines 220 to 440

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/world.py#440-440), lines 440 to 660

Read [](file:///home/chris/PROJECTS/vmt/src/econsim/simulation/features.py)

Created 14 todos

Phase 2 status analyzed. Here's where things stand and what’s missing, plus a structured action list.

## Current Phase 2 Status (Assessment)

Implemented / Partial:
- Execution framework directory exists with `StepExecutor`, `StepContext`, `StepResult`.
- `MovementHandler` implemented (substantial logic extracted, emits mode change events).
- `CollectionHandler` implemented (legacy pass + placeholder metrics for decision mode).
- Public API in __init__.py exports movement & collection.
  
Missing / Incomplete:
- `TradingHandler`, `MetricsHandler`, `RespawnHandler` files are empty.
- `handlers/protocol.py` is empty: no `StepHandler` Protocol or shared base.
- No `BaseStepHandler` abstraction (handlers directly reference a non-existent base in imports).
- `StepExecutor.execute_step` returns a dict of metrics, but `world.step` incorrectly expects `step_result.performance_data`.
- Large chunk of old monolithic step logic was accidentally pasted inside `_initialize_step_executor` after handler list creation (looks like a merge artifact) — must be removed; also references undefined `use_decision`, `foraged_ids`, etc. This code duplicates logic that should live in handlers.
- Trading, respawn, metrics, hash-neutral parity, pairing cleanup, performance spike detection, and observer flush behavior are still all in the old block in `world.step` (actually now inside `_initialize_step_executor`, which is wrong).
- `world.step` currently: builds context and calls executor but doesn’t perform post-step flush responsibilities (observer flush remains embedded in old logic blob).
- No tests added yet for handlers; determinism risk high until extraction is finished and validated.
- Collection metrics for decision mode are placeholders (tracking not implemented).
- No event types yet for resource collection or trades (not strictly required now but should be stubbed).
- Documentation (plan + README) not yet updated to reflect partial migration.

Risk Hotspots:
- Keeping legacy monolithic logic inside `_initialize_step_executor` defeats decomposition and may mask divergences.
- Missing handler protocol/base means current handlers rely on unimplemented imports (`from .. import BaseStepHandler`).
- Potential behavior drift when we re-home trading logic unless tie-break and ordering preserved (need to copy carefully from original pre-refactor version, not the artifact block).
- Performance metrics logic currently mixed with legacy logging calls (some GUI logger references remain).

## Proposed Completion Strategy (High-Level)

1. Introduce `StepHandler` Protocol + `BaseStepHandler` to standardize timing + error isolation.
2. Clean `_initialize_step_executor` by removing stray monolithic logic.
3. Implement remaining handlers in strict original order:
   movement → collection → trading → metrics → respawn.
4. Reconstruct `TradingHandler` using original code path:
   - Build cell map
   - Filter via foraged set passed from Movement/Collection (need cross-handler data? Option: movement returns set; we can add a lightweight shared scratchpad in context or attach to simulation transiently)
   - Enumerate intents
   - Execute single intent
   - Metrics + highlight + pairing cleanup + hash-neutral restoration deferred to MetricsHandler if splitting makes sense (or stay in trading handler with care).
5. Implement `RespawnHandler` (interval logic + metrics).
6. Implement `MetricsHandler`:
   - steps/sec rolling window
   - performance spike detection
   - pairing flush
   - observer registry flush_step call should probably remain outside handlers (end-of-step) OR be part of MetricsHandler as last stage—pick one (lean: final responsibility of world.step for clarity).
7. Adjust `world.step` orchestration:
   - Only: init executor, build context, execute, increment step counter, flush observers, expire highlights.
8. Enhance `CollectionHandler` to compute decision-mode collection metrics deterministically (pre/post resource count delta + maybe per-agent diffs via inventory delta snapshot taken at handler start—requires O(n) copy; acceptable).
9. Add unit tests targeting each handler’s invariants + determinism integration tests across feature flag matrix.
10. Validate performance (<1% regression) and update baselines if stable.
11. Update docs and mark Phase 2 near-complete.

## Todo List (Actionable)

I’ve created a detailed todo list with statuses and next steps. Let me know if you’d like any items reprioritized or collapsed.

Would you like me to start by implementing the handler protocol/base and cleaning the executor initialization (items 2 & 4), then proceed sequentially? If yes, I’ll mark item 2 in-progress and begin edits. Just give me the go-ahead or any preference adjustments (e.g., move pairing cleanup to a different handler, or keep observer flush inside executor).