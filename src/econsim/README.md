# EconSim Core Package

High-level overview of the `econsim` package: deterministic educational micro‑economics spatial simulation with a PyQt6 GUI hosting an embedded Pygame surface.

## Architecture Summary
- Single threaded; one QTimer (≈16 ms) drives simulation + render.
- Determinism invariants: ordered resource iteration, tie-break key for target selection, separated RNG streams (external vs internal), immutable constants.
- Feature flags manage foraging, trading, visualization overlays.

## Directory Map
- `main.py` – CLI / entry-point glue (if used) for launching GUI or demos.
- `gui/` – All Qt widgets, controller, panels, start menu, embedded Pygame renderer.
- `simulation/` – Core model: agents, grid, world step orchestration, trade, metrics, respawn, snapshot.
- `preferences/` – Pure utility preference functions/classes (Cobb-Douglas, Perfect Substitutes, Leontief) + factory.

Each subfolder contains its own README with detailed per-file class/function purpose listings (see below).

## Root Module Files
### `__init__.py`
Exposes top-level package version/hooks (currently minimal – acts as namespace initializer).

### `main.py`
Typical pattern: quick-launch harness (if present) to run the GUI using default configuration. (If currently a stub, future refactor may incorporate CLI arguments for seed, grid size, or headless perf run.)

## Extension / Refactor Guidance
Upcoming refactor should:
- Keep step loop O(agents+resources); avoid pathfinding or global all-pairs scans.
- Maintain separation between rendering (side-effects) and pure utility calculations.
- Expand metrics / logging behind flags to preserve determinism baseline.

See subfolder READMEs for exhaustive inventories.
