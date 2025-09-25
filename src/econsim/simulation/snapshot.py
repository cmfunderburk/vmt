"""Simulation snapshot & replay utilities (established Gate 5, unchanged in Gate 6).

Provides a minimal, deterministic serialization of simulation state to
support replay / hash verification tests. Metrics hash itself is not
stored; recomputation during replay should yield identical digests for
the same number of steps when dynamics are deterministic.
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
    step: int
    grid: Dict[str, Any]
    agents: List[Dict[str, Any]]

    def serialize(self) -> dict[str, Any]:  # pragma: no cover (thin wrapper)
        return {"step": self.step, "grid": self.grid, "agents": self.agents}

    @staticmethod
    def from_sim(sim: Simulation) -> "Snapshot":
        # Use existing serialize helpers for grid & agents
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
        # Rebuild grid
        grid = Grid.deserialize(data["grid"])  # type: ignore[arg-type]
        agents_payload = data.get("agents", [])
        agents: list[Agent] = []
        for payload in agents_payload:  # type: ignore[assignment]
            pref = PreferenceFactory.from_serialized(payload["preference"])  # type: ignore[index]
            home = payload.get("home")
            if isinstance(home, (list, tuple)) and len(home) == 2:  # type: ignore[arg-type]
                hx = int(home[0])  # type: ignore[index]
                hy = int(home[1])  # type: ignore[index]
            else:  # fallback: use current position
                hx = int(payload["x"])
                hy = int(payload["y"])
            # Get sprite type with fallback
            sprite_type = payload.get("sprite_type", "agent_emoji_builder")
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
        # Note: metrics collector / respawn scheduler intentionally not auto-restored
        # (tests attach them if needed for hash reproduction)
        # Step counter restored for informational parity
        sim._steps = int(data.get("step", 0))  # type: ignore[attr-defined]
        return sim


def take_snapshot(sim: Simulation) -> Snapshot:
    """Public helper to create a Snapshot (convenience wrapper)."""
    return Snapshot.from_sim(sim)


def restore_snapshot(snapshot: Snapshot) -> Simulation:
    """Public helper to restore a Simulation from an existing Snapshot."""
    return Snapshot.restore(snapshot.serialize())


__all__ = ["Snapshot", "take_snapshot", "restore_snapshot"]
