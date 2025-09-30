"""Deterministic simulation state serialization for testing and replay.

Provides minimal, reproducible serialization of simulation state to support
regression testing and hash verification. Captures essential simulation state
(agents, grid, step count) while excluding non-deterministic components like
metrics collectors and respawn schedulers.

Restoration guarantees identical simulation dynamics when combined with
identical configuration and RNG seeds, enabling precise regression testing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Dict

from .world import Simulation
from .grid import Grid
from .agent import Agent
from econsim.preferences.factory import PreferenceFactory


@dataclass(slots=True)
class Snapshot:
    """Deterministic simulation state snapshot for testing and replay.
    
    Captures essential simulation state including agent positions, inventories,
    preferences, grid resources, and step count. Excludes non-deterministic
    components (metrics, respawn schedulers) to ensure reproducible restoration.
    
    Attributes:
        step: Current simulation step count
        grid: Serialized grid state with resource positions/types
        agents: List of serialized agent states with full inventory data
    """
    step: int
    grid: Dict[str, Any]
    agents: List[Dict[str, Any]]

    def serialize(self) -> dict[str, Any]:
        """Export snapshot to JSON-serializable dictionary."""
        return {"step": self.step, "grid": self.grid, "agents": self.agents}

    @staticmethod
    def from_sim(sim: Simulation) -> "Snapshot":
        """Create snapshot from current simulation state.
        
        Args:
            sim: Active simulation to capture
            
        Returns:
            Snapshot containing essential simulation state
        """
        # Capture grid and agent states using existing serialization
        grid_data = sim.grid.serialize()
        agents_data: List[Dict[str, Any]] = []
        for a in sim.agents:
            agents_data.append(
                {
                    "id": a.id,
                    "x": a.x,
                    "y": a.y,
                    "home": (a.home_x, a.home_y),
                    "carrying": dict(a.carrying),
                    "home_inventory": dict(a.home_inventory),
                    "preference": a.preference.serialize(),
                    "sprite_type": a.sprite_type,
                }
            )
        return Snapshot(step=sim.steps, grid=grid_data, agents=agents_data)

    @staticmethod
    def restore(data: dict[str, Any]) -> Simulation:
        """Restore simulation from snapshot data.
        
        Args:
            data: Serialized snapshot data dictionary
            
        Returns:
            Simulation with restored state (excludes metrics/respawn components)
        """
        # Rebuild grid and agents from serialized data
        grid = Grid.deserialize(data["grid"])  # type: ignore[arg-type]
        agents_payload = data.get("agents", [])
        agents: list[Agent] = []
        for payload in agents_payload:  # type: ignore[assignment]
            pref = PreferenceFactory.from_serialized(payload["preference"])  # type: ignore[index]
            home = payload.get("home")
            if isinstance(home, (list, tuple)) and len(home) == 2:  # type: ignore[arg-type]
                hx = int(home[0])  # type: ignore[index]
                hy = int(home[1])  # type: ignore[index]
            else:  # fallback: use current position as home
                hx = int(payload["x"])
                hy = int(payload["y"])
            sprite_type = payload.get("sprite_type", "agent_explorer")
            a = Agent(
                id=int(payload["id"]),
                x=int(payload["x"]),
                y=int(payload["y"]),
                preference=pref,
                home_x=hx,
                home_y=hy,
                sprite_type=sprite_type,
            )
            # Restore inventories
            for k, v in payload.get("carrying", {}).items():  # type: ignore[index]
                a.carrying[k] = int(v)
            for k, v in payload.get("home_inventory", {}).items():  # type: ignore[index]
                a.home_inventory[k] = int(v)
            agents.append(a)
        sim = Simulation(grid=grid, agents=agents, config=None)
        # Exclude metrics/respawn components for deterministic reproduction
        sim._steps = int(data.get("step", 0))  # type: ignore[attr-defined]
        return sim


def take_snapshot(sim: Simulation) -> Snapshot:
    """Create snapshot from active simulation state.
    
    Args:
        sim: Simulation to capture
        
    Returns:
        Snapshot containing essential state for reproduction
    """
    return Snapshot.from_sim(sim)


def restore_snapshot(snapshot: Snapshot) -> Simulation:
    """Restore simulation from snapshot with deterministic guarantees.
    
    Args:
        snapshot: Previously captured simulation snapshot
        
    Returns:
        Simulation with restored state ready for continued execution
    """
    return Snapshot.restore(snapshot.serialize())


__all__ = ["Snapshot", "take_snapshot", "restore_snapshot"]
