# EconSim VMT – Bottom‑Up Rewrite (Student Guide)

Who this is for: a 2nd‑year CS student who wants to learn by rebuilding this project from the ground up. You will implement a tiny, deterministic “world” with agents that move on a grid to collect resources, then (optionally) plug it into a GUI.

You’ll learn: clean Python design, test‑driven development, simple AI decisions, and how to keep results reproducible.

Date: 2025‑09‑25

**Important Idea**: Start headless (no GUI). Build the engine first, prove it with tests, then add visuals later.

**What you’ll ship (milestone by milestone)**
- A core engine that can step through time deterministically
- A small test suite that proves your rules
- A minimal CLI runner to watch it work
- Optional: a simple GUI adapter that reuses the existing widget

**Vocabulary**
- Deterministic: same inputs → same outputs every run
- RNG/seed: a “random number generator” that is predictable when seeded
- Bundle: a pair (x, y) representing two goods

**Prerequisites**
- Python classes, functions, modules, imports
- Dataclasses and type hints
- Basics of unit testing with pytest
- Git basics (commit, branch) and virtualenv

---

**Big Picture**
- Engine (no GUI): model, agents, rules → easy to test
- UI (GUI): draws what the engine says → built after the engine

We will mirror the current code’s ideas, but write them cleanly in a new package so you can compare and learn.

---

**Project Shape You’ll Create**
- New package for your rewrite: `src/econsim2/core` (engine) and `src/econsim2/ui` (optional GUI)
- Keep the original code as reference in `src/econsim/`

Commands you’ll use:
- Create folders/files, run tests with `pytest -q`, and run a small `python -m` script for your CLI.

---

**Milestone 0 – Setup**
- Create a virtual environment and install dev tools.
- Make folders for the new engine.
- Verify pytest runs with a dummy test.

Steps
- `python3 -m venv vmt-dev && source vmt-dev/bin/activate`
- `pip install -e .[dev]` (project already defines dev extras)
- `mkdir -p src/econsim2/core/preferences src/econsim2/ui`
- Add empty `__init__.py` to new folders.
- Add `tests/e2_core/test_sanity.py` with `assert 1+1==2`.

Done when: pytest passes.

---

**Milestone 1 – Types & Config**
- Create small types and a configuration object with basic checks.

Files
- `src/econsim2/core/types.py` (define `Bundle = tuple[float, float]`, `Coord = tuple[int,int]`)
- `src/econsim2/core/config.py` (class `SimConfig` with: `grid_size`, `initial_resources`, `seed`, flags for `enable_respawn`, `enable_metrics`)

Tests
- Invalid grid sizes raise errors
- Viewport or extra fields are optional for now; keep it simple

Done when: constructing and validating a `SimConfig` works.

---

**Milestone 2 – Grid**
- Store resources in cells.

What it does
- Holds a dictionary from `(x,y)` to a type like `'A'` or `'B'`
- Lets you add a resource, check if one exists, and remove it
- Can iterate resources in a sorted, stable order (for reproducible behavior)

Files
- `src/econsim2/core/grid.py` with: `add_resource`, `has_resource`, `take_resource_type`, `iter_resources`, `iter_resources_sorted`, `serialize`, `deserialize`

Tests
- Adding/removing works
- Out‑of‑bounds raises ValueError
- Sorted iteration order is stable

Done when: grid tests pass and serialization round‑trips.

---

**Milestone 3 – Preferences (Utility Functions)**
- Implement how agents value goods.

Start with three:
- Cobb‑Douglas: `U(x,y) = x^a * y^(1-a)` (0<a<1)
- Perfect Substitutes: `U(x,y) = a*x + b*y` (a,b>0)
- Leontief: `U(x,y) = min(x/a, y/b)` (a,b>0)

Files
- `src/econsim2/core/preferences/base.py` (abstract class + validation helper)
- `src/econsim2/core/preferences/cobb_douglas.py`
- `src/econsim2/core/preferences/perfect_substitutes.py`
- `src/econsim2/core/preferences/leontief.py`
- `src/econsim2/core/preferences/factory.py` (string → class)

Tests
- Utility results are correct for simple bundles
- Parameters validate (bad inputs raise)

Done when: you can create a preference from the factory and call `utility((x,y))`.

---

**Milestone 4 – Agent**
- An agent walks on the grid and picks up resources.

Agent state
- Position `(x,y)`
- Two inventories: carrying (in hand) and home (stored)
- Mode: FORAGE, RETURN_HOME, or IDLE

Behavior
- Legacy move: random step in 4 directions or stay (bounded by grid)
- Collect: if standing on a resource, convert type `'A'`→`good1`, `'B'`→`good2`
- Deposit: when at home, move carrying → home inventory
- Decision target: choose a nearby resource that increases utility the most (greedy 1 step)

Files
- `src/econsim2/core/agent.py`

Tests
- Random move stays in bounds
- Collect/Deposit update the right inventory
- Decision picks a target by scoring: bigger utility gain wins; break ties by shorter distance, then lower (x,y)

Done when: one agent can walk, pick up, and deposit in tests.

---

**Milestone 5 – Simulation (World)**
- The world steps all agents forward by one tick.

Rules per step
- Decision mode: for each agent, pick/refresh target, move 1 cell toward it, collect, maybe deposit
- Legacy mode: random move for each agent, then collect
- Increase a step counter

Files
- `src/econsim2/core/world.py` (class `Simulation(grid, agents, config)` with `step(rng, use_decision: bool)`)

Tests
- Two agents contest a resource: only one can get it; other should retarget next step
- Step counter increments; behavior is deterministic with a fixed seed and the same inputs

Done when: stepping N times gives the same result every run.

---

**Milestone 6 – Respawn & Metrics (Optional but Recommended)**
- Respawn keeps a target density of resources by adding a few each tick.
- Metrics builds a “determinism hash” so you can detect changes.

Files
- `src/econsim2/core/respawn.py` (density target, rate, max per tick, alternating type A↔B)
- `src/econsim2/core/metrics.py` (streaming SHA‑256 over a canonical summary)

Tests
- No overshoot when filling resources
- Hash changes when state changes; stays the same when you repeat the same run

Done when: you can print a stable hash at the end of a run.

---

**Milestone 7 – Snapshot/Replay**
- Save the world (grid + agents) and restore it later.

Files
- `src/econsim2/core/snapshot.py` (`Snapshot.from_sim(sim)` and `Snapshot.restore(data)`)

Tests
- Round‑trip: take snapshot → restore → equality of key fields
- Replay: step 20, snapshot, step 20 more, restore, step 20 → same final hash as original

Done when: snapshots help you prove determinism.

---

**Milestone 8 – Simple Public API (Facade)**
- Provide a few functions that are easy to import and use.

Files
- `src/econsim2/core/api.py` with: `from_config`, `step`, `metrics_hash`, `snapshot`, `restore`

Tests
- A small end‑to‑end test that does everything through `api.py`

Done when: outside code never needs to import internals.

---

**Milestone 9 – CLI Runner (See It Work)**
- Write a tiny script that builds a world, runs 100 steps, and prints stats.

Files
- `src/cli/econ.py` with a `main()` that:
  - builds a config
  - creates agents at fixed homes
  - steps N times
  - prints: steps, remaining resources, optional determinism hash

Run with: `python -m cli.econ`

Done when: you can watch it run in the terminal.

---

**Milestone 10 – Optional GUI Adapter**
- If you want visuals, adapt the existing widget to read from your engine.

Files
- `src/econsim2/ui/renderer.py` (or use the existing `src/econsim/gui/embedded_pygame.py` as a reference)
- Pass your simulation to the widget and draw agents/resources as colored squares

Done when: the GUI shows your world and keeps running at ~60 FPS.

---

**Determinism: the “Why” and the “How”**
- Why: You can test your code reliably. If a change breaks logic, the hash changes.
- How: always seed RNGs, keep a stable sort order, and avoid hidden randomness.
- Tie‑break: when two choices look equal, pick the one with smaller distance, then smaller x, then smaller y.

Small example
- If two resources give the same utility gain, prefer the closer one. If distance ties, pick the left‑most (smaller x). If still tied, the top‑most (smaller y).

---

**Testing Basics (with pytest)**
- Make `tests/e2_core/` and add tests as you go.
- Test one small behavior at a time.

Example
```python
def test_grid_add_and_take():
    g = Grid(4, 4, [])
    g.add_resource(1, 1, 'A')
    assert g.has_resource(1, 1)
    assert g.take_resource_type(1, 1) == 'A'
    assert not g.has_resource(1, 1)
```

Run: `pytest -q`

---

**Performance (keep it simple)**
- Your engine should be fast enough for small grids (≤64×64) and a few dozen agents.
- Avoid big allocations in tight loops.
- Optional micro‑bench: time 4000 decision steps and keep it under ~1 second locally.

---

**Git Workflow Tips**
- Create a branch per milestone.
- Commit small, test often.
- If a test starts failing randomly, check seeds and sort orders first.

---

**Common Pitfalls**
- Forgetting to seed RNGs (use `random.Random(seed)`, do not use `random` module globally)
- Iterating a dict directly when you needed a sorted order
- Changing scoring or tie‑break rules mid‑project (tests will catch this)
- Mixing GUI code into the engine (harder to test)

---

**Stretch Goals (after core is working)**
- Add trading between nearby agents (both utilities improve)
- Add consumption so agents must keep gathering
- Add overlay visuals (grid lines, IDs) in the GUI

---

**Quick Checklist**
- Milestone 0: environment + pytest OK
- Milestone 1: config validates
- Milestone 2: grid works + serializes
- Milestone 3: preferences compute utility
- Milestone 4: agent moves/collects/deposits
- Milestone 5: simulation steps deterministically
- Milestone 6: respawn + metrics hash
- Milestone 7: snapshot/restore
- Milestone 8: simple API facade
- Milestone 9: CLI runner
- Milestone 10: optional GUI adapter

You can do this—one small step at a time. Keep tests small, keep rules clear, and keep runs reproducible.
