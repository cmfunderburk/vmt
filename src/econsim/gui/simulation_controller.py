"""SimulationController – orchestrates high-level simulation control for GUI.

Phase A responsibilities:
* Hold reference to Simulation
* Provide step() for manual stepping in turn mode
* Provide metrics snapshot (ticks, remaining resources, hash if available)
* Teardown hook (future extension point)
"""
from __future__ import annotations

from typing import Optional, Deque
from collections import deque
from time import perf_counter

from econsim.simulation.world import Simulation


class SimulationController:
    def __init__(self, simulation: Simulation):
        self.simulation = simulation
        self._hash_cache: Optional[str] = None
        self._paused: bool = False
        self._step_times: Deque[float] = deque(maxlen=64)
        # Playback control (turn mode / educational pacing). None => unrestricted (per-frame) stepping.
        self._playback_tps: float | None = None
        self._last_auto_step_time: float | None = None
        # Persistent RNG for manual stepping to avoid per-call re-seeding divergence.
        # Seed priority: simulation.config.seed (if present) else fixed fallback.
        seed = 0
        try:
            cfg = getattr(simulation, "config", None)
            if cfg is not None and hasattr(cfg, "seed"):
                seed = int(getattr(cfg, "seed"))
        except Exception:  # pragma: no cover - defensive
            seed = 0
        import random as _r
        self._manual_rng = _r.Random(seed)
        # Mode flag (decision vs legacy). Default True unless an explicit legacy marker is later injected.
        # The EmbeddedPygameWidget passes decision_mode to its own stepping path; we mirror via a public setter.
        self._use_decision_mode: bool = True
        # Respawn interval mirrors simulation's internal setting; exposed for UI control.
        try:
            self._respawn_interval_cache = simulation._respawn_interval  # type: ignore[attr-defined]
        except Exception:
            self._respawn_interval_cache = 20  # Default to every 20 turns
        # Bilateral exchange GUI master toggle (Phase 2). Default off.
        self._bilateral_enabled: bool = False
        # Granular trade gating (draft vs execution) exposed to GUI. Execution implies draft.
        self._trade_draft_enabled: bool = False
        self._trade_exec_enabled: bool = False
        # Debug overlay flag (user-facing; maps to env for existing overlay code path)
        self._trade_debug_enabled: bool = False
        # Foraging enable (new gating; default on). Mirrors env flag ECONSIM_FORAGE_ENABLED.
        self._forage_enabled: bool = True

    # --- Bilateral Exchange Feature Flag (GUI-scope; does not auto-set env) -----
    def set_bilateral_enabled(self, enabled: bool) -> None:
        """Enable/disable bilateral exchange (enumeration + execution + GUI info).

        For initial implementation, we map this to the existing environment flag
        expectations used inside Simulation.step. To avoid mid-test/global leakage,
        we set os.environ keys on transition only. Future refactor could plumb
        flags directly into Simulation.step call path instead of env usage.
        """
        import os
        want = bool(enabled)
        if want == self._bilateral_enabled:
            return
        self._bilateral_enabled = want
        if want:
            os.environ["ECONSIM_TRADE_DRAFT"] = "1"
            os.environ["ECONSIM_TRADE_EXEC"] = "1"
            os.environ["ECONSIM_TRADE_GUI_INFO"] = "1"
            self._trade_draft_enabled = True
            self._trade_exec_enabled = True
        else:
            # Remove flags (gracefully) so subsequent steps skip enumeration
            for k in ("ECONSIM_TRADE_DRAFT", "ECONSIM_TRADE_EXEC", "ECONSIM_TRADE_GUI_INFO"):
                if k in os.environ:
                    del os.environ[k]
            self._trade_draft_enabled = False
            self._trade_exec_enabled = False

    def bilateral_enabled(self) -> bool:
        return self._bilateral_enabled

    # --- Granular Trade Toggles --------------------------------------------
    def set_trade_draft_enabled(self, enabled: bool) -> None:
        """Enable/disable only draft enumeration.

        If execution currently enabled and draft is being disabled, execution is also disabled
        (execution logically depends on draft intents). Does NOT flip the user-facing bilateral
        master toggle automatically (they can be decoupled for advanced exploration).
        """
        import os
        want = bool(enabled)
        if want == self._trade_draft_enabled:
            return
        self._trade_draft_enabled = want
        if want:
            os.environ["ECONSIM_TRADE_DRAFT"] = "1"
            # Keep bilateral master coherent if both granular toggles active
            if self._trade_exec_enabled:
                os.environ["ECONSIM_TRADE_EXEC"] = "1"
            self._bilateral_enabled = self._trade_exec_enabled and True
        else:
            # Turning off draft disables execution too
            if "ECONSIM_TRADE_DRAFT" in os.environ:
                del os.environ["ECONSIM_TRADE_DRAFT"]
            if self._trade_exec_enabled:
                self.set_trade_exec_enabled(False)
            self._bilateral_enabled = False

    def trade_draft_enabled(self) -> bool:
        return self._trade_draft_enabled

    def set_trade_exec_enabled(self, enabled: bool) -> None:
        """Enable/disable execution (implies draft).

        Enabling execution auto-enables draft. Disabling execution leaves draft state untouched.
        """
        import os
        want = bool(enabled)
        if want == self._trade_exec_enabled:
            return
        self._trade_exec_enabled = want
        if want:
            # Ensure draft on first
            if not self._trade_draft_enabled:
                self.set_trade_draft_enabled(True)
            os.environ["ECONSIM_TRADE_EXEC"] = "1"
            os.environ["ECONSIM_TRADE_GUI_INFO"] = "1"  # enable summary line
            self._bilateral_enabled = True
        else:
            if "ECONSIM_TRADE_EXEC" in os.environ:
                del os.environ["ECONSIM_TRADE_EXEC"]
            # GUI info summary depends on execution; remove but leave draft intact
            if "ECONSIM_TRADE_GUI_INFO" in os.environ:
                del os.environ["ECONSIM_TRADE_GUI_INFO"]
            self._bilateral_enabled = self._trade_draft_enabled and False

    def trade_exec_enabled(self) -> bool:
        return self._trade_exec_enabled

    # --- Trade Debug Overlay Toggle ----------------------------------------
    def set_trade_debug_enabled(self, enabled: bool) -> None:
        import os
        want = bool(enabled)
        if want == self._trade_debug_enabled:
            return
        self._trade_debug_enabled = want
        if want:
            # Reuse existing draft flag requirement. Do not force execution.
            if not self._trade_draft_enabled:
                self.set_trade_draft_enabled(True)
            os.environ["ECONSIM_TRADE_DRAFT"] = "1"
            os.environ["ECONSIM_TRADE_DEBUG_OVERLAY"] = "1"
        else:
            # Intentionally do not remove ECONSIM_TRADE_DRAFT; user might rely on draft without debug
            if "ECONSIM_TRADE_DEBUG_OVERLAY" in os.environ:
                del os.environ["ECONSIM_TRADE_DEBUG_OVERLAY"]

    def trade_debug_enabled(self) -> bool:
        return self._trade_debug_enabled

    # --- Foraging Gating ---------------------------------------------------
    def set_forage_enabled(self, enabled: bool) -> None:
        import os
        want = bool(enabled)
        if want == self._forage_enabled:
            return
        self._forage_enabled = want
        if want:
            os.environ["ECONSIM_FORAGE_ENABLED"] = "1"
        else:
            # Explicitly set to "0" (instead of deleting) so Simulation.step's default
            # fallback (which assumes unset == enabled) does not re-enable foraging.
            os.environ["ECONSIM_FORAGE_ENABLED"] = "0"

    def forage_enabled(self) -> bool:
        return self._forage_enabled

    def last_trade_summary(self) -> str | None:
        """Return a succinct human-readable summary of the last executed trade.

        None if feature disabled or no trade executed yet. Pure read-only formatting.
        """
        if not self._bilateral_enabled:
            return None
        mc = getattr(self.simulation, "metrics_collector", None)
        if mc is None:
            return None
        lt = getattr(mc, "last_executed_trade", None)
        if not lt:
            return None
        try:
            return (
                f"step {lt.get('step')} seller {lt.get('seller')} → buyer {lt.get('buyer')} "
                f"give {lt.get('give_type')} / take {lt.get('take_type')} ΔU={lt.get('delta_utility'):.3f}"
            )
        except Exception:
            return None

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def is_paused(self) -> bool:
        return self._paused

    def set_decision_mode(self, enabled: bool) -> None:
        """Setter used by GUI layer to align manual stepping mode with widget decision_mode."""
        self._use_decision_mode = bool(enabled)

    def manual_step(self, count: int = 1) -> None:
        """Perform one or more manual steps using persistent RNG and honoring active mode.

        Uses the same decision vs legacy semantics as the widget timer path to
        preserve determinism when mixing manual + auto stepping.
        """
        steps = max(1, count)
        for _ in range(steps):
            self.simulation.step(self._manual_rng, use_decision=self._use_decision_mode)
            self._record_step_timestamp()
        # Reset scheduling anchor so an immediate auto step does not fire right after manual stepping.
        self._last_auto_step_time = None

    # --- Playback Rate -------------------------------------------------
    def set_playback_tps(self, tps: float | None) -> None:
        """Set desired automatic playback stepping rate (turns per second).

        tps=None disables throttling (reverts to per-frame stepping when unpaused).
        Values <=0 are treated as None.
        """
        if tps is None or tps <= 0:
            self._playback_tps = None
        else:
            # Clamp to a reasonable upper bound to avoid UI accidents.
            self._playback_tps = min(float(tps), 20.0)
        self._last_auto_step_time = None

    def playback_tps(self) -> float | None:
        return self._playback_tps

    # --- Respawn Interval Control ---------------------------------------
    def set_respawn_interval(self, interval: int | None) -> None:
        """Expose respawn pacing to GUI.

        None / <=0 disables respawn; 1 = every step; N = every Nth step.
        Deterministic given identical user interaction sequence.
        """
        try:
            self.simulation.set_respawn_interval(interval)  # type: ignore[attr-defined]
            self._respawn_interval_cache = interval
        except Exception:  # pragma: no cover - defensive
            pass

    def respawn_interval(self) -> int | None:
        return getattr(self, "_respawn_interval_cache", None)

    def set_respawn_rate(self, rate: float) -> None:
        """Set the respawn rate (fraction of deficit respawned each time).
        
        Rate should be between 0.0 and 1.0, where:
        - 0.1 = respawn 10% of deficit each time
        - 1.0 = respawn 100% of deficit each time (full replenishment)
        """
        try:
            scheduler = getattr(self.simulation, "respawn_scheduler", None)
            if scheduler is not None:
                scheduler.respawn_rate = max(0.0, min(1.0, float(rate)))
        except Exception:  # pragma: no cover - defensive
            pass

    def respawn_rate(self) -> float:
        """Get the current respawn rate."""
        try:
            scheduler = getattr(self.simulation, "respawn_scheduler", None)
            if scheduler is not None:
                return scheduler.respawn_rate
        except Exception:
            pass
        return 1.0  # Default to 100%

    def _should_step_now(self, now: float) -> bool:
        """Return True if an auto step should occur at this timestamp.

        If no playback_tps is set, always returns True (legacy behavior).
        """
        if self._playback_tps is None:
            return True
        interval = 1.0 / max(0.0001, self._playback_tps)
        if self._last_auto_step_time is None:
            self._last_auto_step_time = now
            return True
        if now - self._last_auto_step_time >= interval:
            # Allow exactly one step; advance anchor by integer multiples to prevent drift build-up.
            skipped = int((now - self._last_auto_step_time) // interval)
            self._last_auto_step_time += max(1, skipped) * interval
            return True
        return False

    def determinism_hash(self) -> str:
        collector = getattr(self.simulation, "metrics_collector", None)
        if collector is None:
            return "(metrics disabled)"
        # Return cached if already computed
        if self._hash_cache is not None:
            return self._hash_cache
        return self.refresh_hash()

    def refresh_hash(self) -> str:
        collector = getattr(self.simulation, "metrics_collector", None)
        if collector is None:
            return "(metrics disabled)"
        try:
            h = collector.determinism_hash()
            self._hash_cache = h
            return h
        except Exception:
            return self._hash_cache or "<hash error>"

    def ticks(self) -> int:
        return self.simulation.steps

    def remaining_resources(self) -> int:
        grid = getattr(self.simulation, "grid", None)
        if grid is None:
            return 0
        try:
            return sum(1 for _ in grid.iter_resources())  # type: ignore[attr-defined]
        except Exception:
            return 0

    def steps_per_second_estimate(self) -> float:
        times = self._step_times
        if len(times) < 2:
            return 0.0
        span = times[-1] - times[0]
        if span <= 0:
            return 0.0
        return (len(times) - 1) / span

    # --- Agent Introspection (Read-Only; UI metrics) -----------------------
    def list_agent_ids(self) -> list[int]:
        """Return deterministic ordered list of agent IDs.

        Stable ordering leverages underlying simulation.agents ordering;
        we sort by id to ensure UI dropdown remains stable even if internal
        insertion order changes in future extensions.
        """
        agents = getattr(self.simulation, "agents", [])
        try:
            return [int(getattr(a, "id")) for a in sorted(agents, key=lambda a: getattr(a, "id", 0))]
        except Exception:
            return []

    def agent_carry_bundle(self, agent_id: int) -> tuple[int, int]:
        """Return (good1, good2) carrying bundle for agent or (0,0) if not found."""
        agents = getattr(self.simulation, "agents", [])
        for a in agents:
            if getattr(a, "id", None) == agent_id:
                inv = getattr(a, "carrying", {})
                return int(inv.get("good1", 0)), int(inv.get("good2", 0))
        return (0, 0)

    def agent_home_bundle(self, agent_id: int) -> tuple[int, int]:
        """Return (good1, good2) home inventory for agent or (0,0) if not found."""
        agents = getattr(self.simulation, "agents", [])
        for a in agents:
            if getattr(a, "id", None) == agent_id:
                inv = getattr(a, "home_inventory", {})
                return int(inv.get("good1", 0)), int(inv.get("good2", 0))
        return (0, 0)

    def agent_carry_utility(self, agent_id: int) -> float | None:
        """Compute utility of the agent's total wealth (carrying + home inventory).

        Returns None if preference or agent not accessible. This is a pure
        computation using already-held state; no mutation performed.
        """
        agents = getattr(self.simulation, "agents", [])
        for a in agents:
            if getattr(a, "id", None) == agent_id:
                pref = getattr(a, "preference", None)
                if pref is None or not hasattr(pref, "utility"):
                    return None
                carry_inv = getattr(a, "carrying", {})
                home_inv = getattr(a, "home_inventory", {})
                # Preference utility expects a bundle (x,y) or mapping; implementations accept tuple.
                try:
                    # Total wealth = carrying + home inventory
                    g1_total = float(carry_inv.get("good1", 0)) + float(home_inv.get("good1", 0))
                    g2_total = float(carry_inv.get("good2", 0)) + float(home_inv.get("good2", 0))
                    return float(pref.utility((g1_total, g2_total)))  # type: ignore[arg-type]
                except Exception:
                    return None
        return None

    def agent_preference_type(self, agent_id: int) -> str | None:
        """Get the preference type name for the specified agent.

        Returns the TYPE_NAME of the agent's preference or None if not accessible.
        """
        agents = getattr(self.simulation, "agents", [])
        for a in agents:
            if getattr(a, "id", None) == agent_id:
                pref = getattr(a, "preference", None)
                if pref is None:
                    return None
                try:
                    # Get the TYPE_NAME attribute from the preference
                    return getattr(pref, "TYPE_NAME", None)
                except Exception:
                    return None
        return None

    # Internal hook used by widget when auto-stepping
    def _record_step_timestamp(self) -> None:
        self._step_times.append(perf_counter())
        # Invalidate hash cache (new step implies potential hash change)
        self._hash_cache = None

    def teardown(self) -> None:
        # Placeholder for future resource clean shutdown hooks
        pass

__all__ = ["SimulationController"]
