"""Deterministic multi-preference demo (Gate 5 showcase).

Run a small simulation under different preference specifications and emit
per-step agent state plus a determinism hash derived from the MetricsCollector.

Example:
    python scripts/demo_single_agent.py --pref all --steps 25

Outputs a section per preference with:
- Step table (step,id,x,y,c_g1,c_g2,h_g1,h_g2)
- Final determinism hash
- (Optional) replay hash parity if --replay specified

The decision path is deterministic (no RNG used) once initial grid and
agent placement are fixed. The external RNG argument is still passed to
`Simulation.step` for signature compatibility.
"""
from __future__ import annotations

import argparse
import os
import random
from typing import Iterable

from econsim.simulation.world import Simulation
from econsim.simulation.grid import Grid
from econsim.simulation.agent import Agent
from econsim.simulation.metrics import MetricsCollector
from econsim.simulation.snapshot import take_snapshot, restore_snapshot  # type: ignore
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.preferences.perfect_substitutes import PerfectSubstitutesPreference
from econsim.preferences.leontief import LeontiefPreference
from PyQt6.QtWidgets import QApplication, QMainWindow  # type: ignore
from PyQt6.QtCore import QTimer  # type: ignore
from econsim.gui.embedded_pygame import EmbeddedPygameWidget

# Headless safety for CI / non-display environments
if not os.environ.get("DISPLAY"):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


def build_grid(width: int = 20, height: int = 15) -> Grid:
    grid = Grid(width, height)
    # Patterned placement of A/B resources (stable deterministic layout)
    idx = 0
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            rtype = "A" if (idx % 2 == 0) else "B"
            grid.add_resource(x, y, rtype)
            idx += 1
    return grid


def build_agents(n: int, preference: "Preference") -> list[Agent]:  # type: ignore[name-defined]
    agents: list[Agent] = []
    for i in range(n):
        # Spread agents diagonally; wrap if exceeding bounds at runtime
        agents.append(Agent(id=i, x=i, y=i, preference=preference))
    return agents


def run_demo(pref_name: str, preference: "Preference", steps: int, n_agents: int, seed: int, replay: bool):  # type: ignore[name-defined]
    print(f"\n=== Preference: {pref_name} ===")
    grid = build_grid()
    agents = build_agents(n_agents, preference)
    sim = Simulation(grid=grid, agents=agents, config=None)
    # Attach deterministic systems
    sim._rng = random.Random(seed)  # type: ignore[attr-defined]
    sim.metrics_collector = MetricsCollector()

    rng_external = random.Random(seed + 999)  # unused for decision path

    header_printed = False
    for _ in range(steps):
        sim.step(rng_external, use_decision=True)
        # Pull last metrics entry (recorded inside step)
        rec = list(sim.metrics_collector.records())[-1]  # type: ignore[arg-type]
        if not header_printed:
            print("step,id,x,y,carry_g1,carry_g2,home_g1,home_g2")
            header_printed = True
        for a in sim.agents:
            print(
                f"{rec['step']},{a.id},{a.x},{a.y},{a.carrying['good1']},{a.carrying['good2']},{a.home_inventory['good1']},{a.home_inventory['good2']}"
            )

    h1 = sim.metrics_collector.determinism_hash()  # type: ignore[arg-type]
    print(f"Final hash: {h1}")

    if replay:
        # Take snapshot at initial state (before any steps) to mirror baseline progression
        # This requires rebuilding an initial sim and snapshotting it.
        init_grid = build_grid()
        init_agents = build_agents(n_agents, preference)
        init_sim = Simulation(grid=init_grid, agents=init_agents, config=None)
        init_sim._rng = random.Random(seed)  # type: ignore[attr-defined]
        init_sim.metrics_collector = MetricsCollector()
        snap = take_snapshot(init_sim)
        # Forward run from initial snapshot baseline
        rng_fwd = random.Random(seed + 999)
        forward_hashes: list[str] = []
        for _ in range(steps):
            init_sim.step(rng_fwd, use_decision=True)
            forward_hashes.append(init_sim.metrics_collector.determinism_hash())  # type: ignore[arg-type]
        # Replay from snapshot and reproduce hash progression
        sim_re = restore_snapshot(snap)
        sim_re._rng = random.Random(seed)  # type: ignore[attr-defined]
        sim_re.metrics_collector = MetricsCollector()
        rng2 = random.Random(seed + 999)
        replay_hashes: list[str] = []
        for _ in range(steps):
            sim_re.step(rng2, use_decision=True)
            replay_hashes.append(sim_re.metrics_collector.determinism_hash())
        parity = "MATCH" if replay_hashes == forward_hashes else "MISMATCH"
        print(f"Replay parity: {parity}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run deterministic multi-preference demo")
    p.add_argument("--steps", type=int, default=25, help="Number of decision steps to run")
    p.add_argument("--agents", type=int, default=1, help="Number of agents")
    p.add_argument(
        "--pref",
        choices=["cd", "subs", "leontief", "all"],
        default="all",
        help="Preference(s) to run",
    )
    p.add_argument("--seed", type=int, default=1234, help="Base seed for deterministic systems")
    p.add_argument("--replay", action="store_true", help="Perform snapshot+replay hash parity check")
    p.add_argument("--gui", action="store_true", help="Launch GUI visualization instead of printing table")
    p.add_argument("--turn-mode", action="store_true", help="GUI: enable discrete turn stepping (space=1 step, enter=5 steps, a=auto toggle, q=quit)")
    p.add_argument("--auto-interval", type=int, default=500, help="GUI turn mode: interval (ms) when auto-run toggled on")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    prefs: list[tuple[str, object]]
    if args.pref == "all":
        prefs = [
            ("CobbDouglas", CobbDouglasPreference(alpha=0.5)),
            ("PerfectSubstitutes", PerfectSubstitutesPreference(a=0.5, b=0.5)),
            ("Leontief", LeontiefPreference(a=1.0, b=1.0)),
        ]
    else:
        if args.pref == "cd":
            prefs = [("CobbDouglas", CobbDouglasPreference(alpha=0.5))]
        elif args.pref == "subs":
            prefs = [("PerfectSubstitutes", PerfectSubstitutesPreference(a=0.5, b=0.5))]
        else:
            prefs = [("Leontief", LeontiefPreference(a=1.0, b=1.0))]

    if args.gui:
        # GUI mode: only the first preference is visualized (warn if more requested)
        name, pref = prefs[0]
        # Build simulation and attach internal RNG + metrics for optional hash (not printed here)
        grid = build_grid()
        agents = build_agents(args.agents, pref)
        sim = Simulation(grid=grid, agents=agents, config=None)
        sim._rng = random.Random(args.seed)  # type: ignore[attr-defined]
        sim.metrics_collector = MetricsCollector()

        # Wrap simulation so widget's RNG-based step triggers decision mode each tick
        class DecisionWrapper:
            def __init__(self, sim: Simulation, max_steps: int | None, turn_mode: bool):
                self._sim = sim
                self._ext_rng = random.Random(args.seed + 999)
                self._max = max_steps
                self._count = 0
                self.turn_mode = turn_mode
                self.pending_steps = 0
                self.auto = False
                self.auto_timer: QTimer | None = None

            def _maybe_finish(self):
                if self._max is not None and self._count >= self._max:
                    h = self._sim.metrics_collector.determinism_hash()  # type: ignore[arg-type]
                    print(f"\n[GUI] Completed {self._count} steps. Final hash: {h}")
                    app = QApplication.instance()
                    if app is not None:
                        app.quit()

            def enqueue(self, n: int = 1):
                self.pending_steps += n

            def toggle_auto(self, interval_ms: int):
                if not self.turn_mode:
                    return
                self.auto = not self.auto
                if self.auto:
                    if self.auto_timer is None:
                        self.auto_timer = QTimer()
                        self.auto_timer.timeout.connect(lambda: self.enqueue(1))  # type: ignore[arg-type]
                    self.auto_timer.start(interval_ms)
                    print(f"[TurnMode] Auto-run ON ({interval_ms} ms)")
                else:
                    if self.auto_timer:
                        self.auto_timer.stop()
                    print("[TurnMode] Auto-run OFF")

            def step(self, rng):  # signature expected by widget
                # In continuous mode: always advance one decision step.
                # In turn mode: only advance if pending_steps > 0.
                if self.turn_mode:
                    if self.pending_steps <= 0:
                        return
                    self.pending_steps -= 1
                self._sim.step(self._ext_rng, use_decision=True)
                self._count += 1
                self._maybe_finish()

        class TurnWidget(EmbeddedPygameWidget):  # pragma: no cover (GUI)
            def __init__(self, wrapper: DecisionWrapper):
                super().__init__(simulation=wrapper)
                self._wrapper = wrapper

            def keyPressEvent(self, event):  # type: ignore[override]
                key = event.key()
                # Qt key codes: use Qt enums indirectly to avoid import clutter
                from PyQt6.QtCore import Qt  # type: ignore
                if key == Qt.Key.Key_Space:  # single step
                    self._wrapper.enqueue(1)
                elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                    self._wrapper.enqueue(5)
                elif key == Qt.Key.Key_A:  # toggle auto
                    self._wrapper.toggle_auto(args.auto_interval)
                elif key == Qt.Key.Key_Q:
                    app = QApplication.instance()
                    if app is not None:
                        app.quit()
                else:
                    super().keyPressEvent(event)

        app = QApplication.instance() or QApplication([])
        win = QMainWindow()
        win.setWindowTitle(f"EconSim Demo – {name} preference")
        wrapper = DecisionWrapper(sim, args.steps, args.turn_mode)
        if args.turn_mode:
            widget = TurnWidget(wrapper)
            print("[TurnMode] Controls: SPACE=1 step, ENTER=5 steps, A=auto toggle, Q=quit")
        else:
            widget = EmbeddedPygameWidget(simulation=wrapper)
        win.setCentralWidget(widget)
        win.resize(640, 480)
        win.show()
        return app.exec()
    else:
        for name, pref in prefs:
            run_demo(name, pref, steps=args.steps, n_agents=args.agents, seed=args.seed, replay=args.replay)
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
