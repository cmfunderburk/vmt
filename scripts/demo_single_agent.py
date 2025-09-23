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
from typing import Iterable, Optional, Callable, Any
from time import perf_counter
from collections import deque

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
from econsim.simulation.respawn import RespawnScheduler

# Headless safety for CI / non-display environments
if not os.environ.get("DISPLAY"):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


def build_grid(width: int = 20, height: int = 15, *, density: Optional[float] = None, seed: Optional[int] = None) -> Grid:
    """Build a grid, optionally using a deterministic random density scatter.

    When density is None, revert to the prior patterned placement (checkerboard half-fill).
    When density is provided (0 < d <= 1), iterate all cells and add a resource with
    probability d using a deterministic RNG derived from the provided seed. Resource
    type alternates deterministically (A/B) by incrementing a counter for each placed
    resource to retain stable counts across runs with same seed+density.
    """
    grid = Grid(width, height)
    if density is None:
        idx = 0
        for y in range(0, height, 2):
            for x in range(0, width, 2):
                rtype = "A" if (idx % 2 == 0) else "B"
                grid.add_resource(x, y, rtype)
                idx += 1
        return grid
    # Deterministic scatter
    if not (0 < density <= 1):  # defensive; argparse should guard
        raise ValueError("density must be in (0,1]")
    # Seed isolation: offset seed to avoid colliding with other RNG streams
    rng = random.Random((seed or 0) + 1001)
    placed = 0
    for y in range(height):
        for x in range(width):
            if rng.random() <= density:
                rtype = "A" if (placed % 2 == 0) else "B"
                grid.add_resource(x, y, rtype)
                placed += 1
    return grid


def build_agents(n: int, preference: "Preference") -> list[Agent]:  # type: ignore[name-defined]
    agents: list[Agent] = []
    for i in range(n):
        # Spread agents diagonally; wrap if exceeding bounds at runtime
        agents.append(Agent(id=i, x=i, y=i, preference=preference))
    return agents


def run_demo(
    pref_name: str,
    preference: "Preference",  # type: ignore[name-defined]
    steps: int,
    n_agents: int,
    seed: int,
    replay: bool,
    density: Optional[float] = None,
):
    print(f"\n=== Preference: {pref_name} ===")
    grid = build_grid(density=density, seed=seed)
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
        init_grid = build_grid(density=density, seed=seed)
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
    # Bundle 3 visualization / pedagogical enhancement flags (implementation staged)
    p.add_argument(
        "--density",
        type=float,
        default=None,
        help="Random resource placement density (0<d<=1) overriding patterned grid (deterministic with seed).",
    )
    p.add_argument(
        "--respawn-every",
        type=int,
        default=0,
        help="Respawn resources every N turns (0 disables; gated deterministic respawn).",
    )
    p.add_argument(
        "--grid-lines",
        action="store_true",
        help="Show grid lines (auto-on in turn mode later unless explicitly omitted).",
    )
    p.add_argument(
        "--fade-ms",
        type=int,
        default=600,
        help="Resource fade-out duration in milliseconds after collection (0 disables).",
    )
    p.add_argument(
        "--tail-length",
        "--tail",
        type=int,
        default=8,
        help="Breadcrumb tail length per agent (0 disables tails).",
    )
    p.add_argument(
        "--no-overlay",
        action="store_true",
        help="Disable overlay HUD (step/resources/agent state) in turn mode.",
    )
    p.add_argument(
        "--pause-start",
        action="store_true",
        help="Start paused (no initial auto steps) in turn mode; user must press space/enter.",
    )
    p.add_argument(
        "--no-tails",
        action="store_true",
        help="Disable breadcrumb tails even if tail-length > 0.",
    )
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
        grid = build_grid(density=args.density, seed=args.seed)
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
                # Hooks for turn visualization state updates
                self.on_pre_step: Callable[[], Any] | None = None
                self.on_post_step: Callable[[], Any] | None = None
                self._respawn_every = args.respawn_every if args.respawn_every > 0 else None
                # Expose underlying simulation attributes so base widget rendering finds them
                # (Needed for resources, agents, and gridlines to display.)
                self.grid = sim.grid  # same object reference
                self.agents = sim.agents  # list reference updates in place
                # Optionally prime one step so user immediately sees state if not explicitly paused
                if self.turn_mode and not args.pause_start:
                    self.pending_steps = 1
                if self._respawn_every:
                    # Attach scheduler but we'll invoke manually to respect gating
                    sim.respawn_scheduler = RespawnScheduler(
                        target_density=0.18 if args.density is None else min(1.0, max(0.0, args.density)),
                        max_spawn_per_tick=4,
                        respawn_rate=0.5,
                    )

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
                if self.on_pre_step:
                    try:
                        self.on_pre_step()
                    except Exception:
                        pass
                self._sim.step(self._ext_rng, use_decision=True)
                self._count += 1
                # Respawn gating: invoke only on multiples of respawn_every
                if self._respawn_every and self._sim.respawn_scheduler and (self._count % self._respawn_every == 0):
                    try:
                        self._sim.respawn_scheduler.step(self._sim.grid, self._sim._rng, step_index=self._count)  # type: ignore[arg-type]
                    except Exception:
                        pass
                if self.on_post_step:
                    try:
                        self.on_post_step()
                    except Exception:
                        pass
                # If turn mode becomes idle after this step, emit help once
                if self.turn_mode and self.pending_steps == 0 and self._count == 1:
                    print("[TurnMode] Idle. Press SPACE (1 step), ENTER (5 steps), A (auto-run), or Q (quit).")
                self._maybe_finish()

        class TurnWidget(EmbeddedPygameWidget):  # pragma: no cover (GUI)
            def __init__(self, wrapper: DecisionWrapper):
                super().__init__(simulation=wrapper)
                self._wrapper = wrapper
                # Static background removes legacy animation for clarity
                self.static_background = True
                # Ensure key events received without clicking
                from PyQt6.QtCore import Qt  # type: ignore
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                self._tail_length = 0 if args.no_tails else max(0, int(args.tail_length))
                self._tails: dict[int, deque[tuple[int, int]]] = {}
                self._prev_pos: dict[int, tuple[int, int]] = {}
                self._just_moved: set[int] = set()
                # Fade state
                self._fade_duration_ms = max(0, int(args.fade_ms))
                self._pre_resources: set[tuple[int,int,str]] = set()
                self._fading: list[tuple[int,int,str,float]] = []  # (x,y,type,start_time)

            def _capture_pre(self):
                if self._fade_duration_ms <= 0:
                    return
                sim_obj = self._wrapper._sim
                grid = getattr(sim_obj, "grid", None)
                if not grid:
                    return
                try:
                    self._pre_resources = set((x, y, t) for x, y, t in grid.iter_resources())  # type: ignore[arg-type]
                except Exception:
                    self._pre_resources = set()

            def _capture_post(self):
                sim_obj = self._wrapper._sim
                agents = getattr(sim_obj, "agents", [])
                grid = getattr(sim_obj, "grid", None)
                moved: set[int] = set()
                for a in agents:
                    aid = getattr(a, "id", 0)
                    pos = (getattr(a, "x", 0), getattr(a, "y", 0))
                    prev = self._prev_pos.get(aid)
                    if prev != pos:
                        moved.add(aid)
                        self._prev_pos[aid] = pos
                        if self._tail_length > 0:
                            dq = self._tails.setdefault(aid, deque(maxlen=self._tail_length))
                            if not dq or dq[-1] != pos:
                                dq.append(pos)
                self._just_moved = moved
                # Fade diff detection
                if self._fade_duration_ms > 0 and grid is not None:
                    try:
                        post = set((x, y, t) for x, y, t in grid.iter_resources())  # type: ignore[arg-type]
                    except Exception:
                        post = set()
                    removed = self._pre_resources - post
                    now = perf_counter()
                    for x, y, t in removed:
                        self._fading.append((x, y, t, now))
                    # Prune stale fading entries
                    if self._fading:
                        dur = self._fade_duration_ms / 1000.0
                        self._fading = [fr for fr in self._fading if (now - fr[3]) <= dur]

            def _draw_tails_and_highlights(self):
                if self._tail_length <= 0:
                    return
                sim_obj = self._wrapper._sim
                grid = getattr(sim_obj, "grid", None)
                agents = getattr(sim_obj, "agents", None)
                if not grid or not agents:
                    return
                # Mirror scaling logic from widget for consistency
                w, h = EmbeddedPygameWidget.SURFACE_SIZE
                gw = getattr(grid, "width", 1)
                gh = getattr(grid, "height", 1)
                cell_w = max(2, w // max(1, gw))
                cell_h = max(2, h // max(1, gh))
                import pygame as _pg
                for aid, dq in self._tails.items():
                    pts = list(dq)
                    alpha_step = 180 // max(1, len(pts))
                    alpha = 40
                    for (tx, ty) in pts:
                        rect = _pg.Rect(tx * cell_w, ty * cell_h, cell_w, cell_h)
                        s = _pg.Surface((cell_w, cell_h), _pg.SRCALPHA)
                        s.fill((255, 255, 255, min(200, alpha)))
                        self._surface.blit(s, rect.topleft)
                        alpha += alpha_step
                # Highlights (outline) for agents that just moved
                for aid in self._just_moved:
                    pos = self._prev_pos.get(aid)
                    if pos is None:
                        continue
                    ax, ay = pos
                    rect = _pg.Rect(ax * cell_w, ay * cell_h, cell_w, cell_h)
                    _pg.draw.rect(self._surface, (255, 255, 255), rect, 2)

            def _draw_fading_resources(self):
                if self._fade_duration_ms <= 0 or not self._fading:
                    return
                sim_obj = self._wrapper._sim
                grid = getattr(sim_obj, "grid", None)
                if not grid:
                    return
                w, h = EmbeddedPygameWidget.SURFACE_SIZE
                gw = getattr(grid, "width", 1)
                gh = getattr(grid, "height", 1)
                cell_w = max(2, w // max(1, gw))
                cell_h = max(2, h // max(1, gh))
                import pygame as _pg
                RES_COLORS = {
                    "A": (240, 240, 60),
                    "B": (60, 200, 255),
                }
                now = perf_counter()
                dur = self._fade_duration_ms / 1000.0
                new_list: list[tuple[int,int,str,float]] = []
                for x, y, t, start in self._fading:
                    elapsed = now - start
                    if elapsed > dur:
                        continue
                    alpha = int(255 * max(0.0, 1.0 - (elapsed / dur)))
                    base = RES_COLORS.get(t, (200, 200, 200))
                    s = _pg.Surface((cell_w, cell_h), _pg.SRCALPHA)
                    s.fill((*base, alpha))
                    self._surface.blit(s, (x * cell_w, y * cell_h))
                    new_list.append((x, y, t, start))
                self._fading = new_list

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

            def _update_scene(self):  # override to inject fading, tails, highlights
                super()._update_scene()
                self._draw_fading_resources()
                self._draw_tails_and_highlights()

        app = QApplication.instance() or QApplication([])
        win = QMainWindow()
        win.setWindowTitle(f"EconSim Demo – {name} preference")
        wrapper = DecisionWrapper(sim, args.steps, args.turn_mode)
        if args.turn_mode:
            widget = TurnWidget(wrapper)
            wrapper.on_pre_step = widget._capture_pre
            wrapper.on_post_step = widget._capture_post
            print("[TurnMode] Controls: SPACE=1 step, ENTER=5 steps, A=auto toggle, Q=quit")
        else:
            widget = EmbeddedPygameWidget(simulation=wrapper)
        # Grid lines default on in turn mode unless user omitted flag (future: add explicit no-grid flag)
        widget.show_grid_lines = bool(args.grid_lines or args.turn_mode)
        widget.show_overlay = not args.no_overlay and args.turn_mode
        win.setCentralWidget(widget)
        win.resize(640, 480)
        win.show()
        return app.exec()
    else:
        for name, pref in prefs:
            run_demo(
                name,
                pref,
                steps=args.steps,
                n_agents=args.agents,
                seed=args.seed,
                replay=args.replay,
                density=args.density,
            )
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
