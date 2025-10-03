"""SimulationController – orchestrates high-level simulation control for GUI.

Phase A responsibilities:
* Hold reference to Simulation
* Provide step() for manual stepping in turn mode
* Provide metrics snapshot (ticks, remaining resources, hash if available)
* Teardown hook (future extension point)
"""
from __future__ import annotations

from typing import Optional, Deque, Any
from collections import deque
from time import perf_counter

from econsim.simulation.world import Simulation
from .utils import format_delta


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
        # Simplified behavior controls (replaces complex 4-checkbox system)
        self._forage_enabled: bool = True  # Default: foraging enabled
        self._bilateral_enabled: bool = False  # Will be set to True below to trigger env var setup
        
        # Trade tracking for event log
        self._trade_history: list[dict[str, Any]] = []  # Recent trades across all steps
        self._last_checked_step = -1  # Track which step we last checked for trades
        
        # Initialize bilateral exchange (this will set environment variables)
        self.set_bilateral_enabled(True)  # Default: bilateral exchange enabled for better debugging

    # --- Bilateral Exchange Feature Flag (GUI-scope; does not auto-set env) -----
    def set_bilateral_enabled(self, enabled: bool) -> None:
        """Enable/disable bilateral exchange (simplified from 4-checkbox system).
        
        When enabled: sets ECONSIM_TRADE_DRAFT=1, ECONSIM_TRADE_EXEC=1, ECONSIM_TRADE_GUI_INFO=1
        When disabled: removes all trade environment flags
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
        else:
            # Remove flags so subsequent steps skip trading entirely
            for k in ("ECONSIM_TRADE_DRAFT", "ECONSIM_TRADE_EXEC", "ECONSIM_TRADE_GUI_INFO"):
                if k in os.environ:
                    del os.environ[k]

    def bilateral_enabled(self) -> bool:
        return self._bilateral_enabled

    # --- Foraging Controls (Simplified Behavior System) -------------------
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
            delta_value = float(lt.get('delta_utility', 0)) if lt.get('delta_utility') is not None else 0.0
            return (
                f"step {lt.get('step')} seller {lt.get('seller')} → buyer {lt.get('buyer')} "
                f"give {lt.get('give_type')} / take {lt.get('take_type')} ΔU={format_delta(delta_value)}"
            )
        except Exception:
            return None

    def agent_trade_history(self, agent_id: int) -> list[dict[str, object]] | None:
        """Return the last 5 trades for a specific agent.
        
        Returns None if bilateral exchange disabled or no trades recorded.
        Each trade record contains: step, partner_id, gave, received, delta_utility, role.
        """
        if not self._bilateral_enabled:
            return None
        mc = getattr(self.simulation, "metrics_collector", None)
        if mc is None or not hasattr(mc, "agent_trade_histories"):
            return None
        
        return mc.agent_trade_histories.get(agent_id, [])

    # --- Stagnation / Trade Diagnostics ---------------------------------
    def agent_stagnation_steps(self, agent_id: int) -> int | None:
        """Return current stagnation step count for an agent (None if unavailable)."""
        for a in self.simulation.agents:
            if a.id == agent_id:
                return getattr(a, "trade_stagnation_steps", None)
        return None

    def agent_last_trade_utility(self, agent_id: int) -> float | None:
        """Return last recorded utility baseline used for stagnation detection."""
        for a in self.simulation.agents:
            if a.id == agent_id:
                return getattr(a, "last_trade_mode_utility", None)
        return None

    def trade_min_delta_threshold(self) -> float:
        """Expose the current minimum combined utility delta required for an intent to execute."""
        try:
            from econsim.simulation.trade import MIN_TRADE_DELTA  # local import keeps GUI decoupled
            return float(MIN_TRADE_DELTA)
        except Exception:
            return 0.0

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
            self.simulation.step(self._manual_rng)
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

    # --- Trade Inspector Support Methods -----------------------------------
    def trade_execution_enabled(self) -> bool:
        """Check if trade execution is enabled (simplified from granular controls)."""
        return self.bilateral_enabled()
    
    # Backward compatibility / inspector expectation: draft enabled mirrors bilateral flag in simplified model.
    def trade_draft_enabled(self) -> bool:
        return self.bilateral_enabled()
    
    def active_intents_count(self) -> int:
        """Get count of active trade intents."""
        try:
            intents = getattr(self.simulation, 'trade_intents', None)
            return len(intents) if intents else 0
        except Exception:
            return 0
    
    def get_active_intents(self) -> list[Any]:
        """Get list of active trade intents for inspector display."""
        try:
            intents = getattr(self.simulation, 'trade_intents', None)
            return list(intents) if intents else []
        except Exception:
            return []
    

    
    def calculate_total_welfare_change(self) -> float:
        """Calculate total welfare change from all current intents."""
        try:
            intents = self.get_active_intents()
            return sum(getattr(intent, 'delta_utility', 0.0) for intent in intents)
        except Exception:
            return 0.0
    
    def count_trading_pairs(self) -> int:
        """Count unique trading pairs in current intents."""
        try:
            intents = self.get_active_intents()
            pairs = set()
            for intent in intents:
                seller = getattr(intent, 'seller_id', None)
                buyer = getattr(intent, 'buyer_id', None)
                if seller is not None and buyer is not None:
                    # Normalize pair order for uniqueness
                    pair = tuple(sorted([seller, buyer]))
                    pairs.add(pair)
            return len(pairs)
        except Exception:
            return 0
    
    def analyze_preference_diversity(self) -> str:
        """Analyze preference type diversity among agents."""
        try:
            agents = getattr(self.simulation, 'agents', [])
            if not agents:
                return "No agents"
            
            # Count preference types
            pref_counts: dict[str, int] = {}
            for agent in agents:
                pref = getattr(agent, 'preference', None)
                if pref is not None:
                    pref_type = type(pref).__name__
                    pref_counts[pref_type] = pref_counts.get(pref_type, 0) + 1
            
            if not pref_counts:
                return "Unknown preferences"
            
            # Format diversity summary
            if len(pref_counts) == 1:
                pref_name = next(iter(pref_counts.keys())).replace('Preference', '')
                return f"Homogeneous ({pref_name})"
            else:
                return f"Mixed ({len(pref_counts)} types)"
                
        except Exception:
            return "Analysis error"
    
    def set_trade_visualization_options(self, *, show_arrows: bool, show_highlights: bool) -> None:
        """Set visualization options for enhanced trade display."""
        # Store options for renderer integration
        self._trade_viz_options = {
            'show_arrows': show_arrows,
            'show_highlights': show_highlights
        }
    
    def get_trade_visualization_options(self) -> dict[str, bool]:
        """Get current trade visualization options."""
        return getattr(self, '_trade_viz_options', {
            'show_arrows': True, 
            'show_highlights': True
        })
    
    def set_pause_on_trade(self, enabled: bool) -> None:
        """Set whether to pause simulation when trades occur."""
        self._pause_on_trade = bool(enabled)
    
    def should_pause_on_trade(self) -> bool:
        """Check if simulation should pause on trade execution."""
        return getattr(self, '_pause_on_trade', False)

    # --- Event Log Support --------------------------------------------------
    
    def get_current_step(self) -> int:
        """Get the current simulation step number."""
        return self.simulation.steps
    
    def get_recent_trades(self, step: int) -> list[dict[str, Any]]:
        """Get trade events that occurred in the specified step."""
        # First, update our trade history to check for any new trades
        self._update_trade_history()
        
        # Return trades that occurred in the requested step
        return [trade for trade in self._trade_history if trade.get('step') == step]
    
    def _update_trade_history(self) -> None:
        """Update internal trade history by checking for new trades."""
        if not self._bilateral_enabled:
            return
            
        mc = getattr(self.simulation, "metrics_collector", None)
        if mc is None:
            return
        
        current_step = self.simulation.steps
        
        # If we have a new step, check for new trades
        if current_step > self._last_checked_step:
            try:
                # GUI debug logging removed - will be rebuilt with current architecture if needed
                
                last_trade = mc.last_executed_trade
                
                if (last_trade and 
                    last_trade.get('step', -1) > self._last_checked_step):
                    
                    # DEBUG: Check the raw delta_utility value - logging removed
                    raw_delta_u = last_trade.get('delta_utility', 0)
                    
                    # Format trade for display (use trade's actual step, not current step)
                    trade_step = last_trade.get('step', current_step)
                    trade_info = {
                        'agent_a_id': last_trade.get('seller', '?'),
                        'agent_b_id': last_trade.get('buyer', '?'), 
                        'goods_a_to_b': last_trade.get('give_type', '?'),
                        'goods_b_to_a': last_trade.get('take_type', '?'),
                        'delta_utility': raw_delta_u,  # Use raw value, no conversion
                        'step': trade_step
                    }
                    
                    # Debug logging removed (legacy debug_logger elimination)
                    
                    # Add to history and trim to reasonable size
                    self._trade_history.append(trade_info)
                    if len(self._trade_history) > 50:  # Keep last 50 trades
                        self._trade_history = self._trade_history[-50:]
                    
                    # DEBUG: Confirm trade was added (legacy debug logging removed)
                else:
                    # Debug logging removed (legacy debug_logger elimination)
                    pass
                        
            except Exception:
                # Graceful fallback for trade detection
                pass
                
            self._last_checked_step = current_step
    
    def get_recent_target_selections(self, step: int) -> list[dict[str, Any]]:
        """Get agent target selection events for the specified step."""
        # For now, return empty list - this would require more extensive 
        # agent behavior tracking to implement properly
        # In a future implementation, agents could log their decision events
        return []

    def teardown(self) -> None:
        # Placeholder for future resource clean shutdown hooks
        pass

__all__ = ["SimulationController"]
