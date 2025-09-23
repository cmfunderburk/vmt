"""Metrics collection scaffold (Gate 5).

Defines the interface for capturing per-step agent & aggregate metrics
plus a determinism hash. Logic will be filled in during Gate 5 proper.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Iterable, List, Dict

from .world import Simulation  # type: ignore (circular safe at runtime since only used type-wise)


@dataclass(slots=True)
class MetricsCollector:
    """Collect per-step metrics and build a determinism hash.

    Hash goal: any divergence in agent positions, inventories, resource layout,
    or step ordering produces different digest. Implementation uses a streaming
    SHA256 updated with a canonical serialization each step.
    """

    enabled: bool = True
    _records: List[Dict[str, Any]] = field(default_factory=lambda: [])
    _hash: Any | None = field(default=None, init=False, repr=False)  # sha256 object

    def __post_init__(self) -> None:  # pragma: no cover - simple init
        self._hash = hashlib.sha256()

    def _update_hash(self, payload: str) -> None:
        if self._hash is not None:
            self._hash.update(payload.encode())

    def record(self, step: int, sim: Simulation) -> None:  # pragma: no cover (exercised indirectly)
        if not self.enabled or self._hash is None:
            return

        # Aggregate metrics
        agent_count = len(sim.agents)
        resource_count = sim.grid.resource_count()

        total_carrying_good1 = 0
        total_carrying_good2 = 0
        total_home_good1 = 0
        total_home_good2 = 0

        agent_snap: list[tuple[int, int, int, int, int, int]] = []
        # (id,x,y,cg1,cg2,hg1,hg2) but keep tuple small; combine some
        for a in sim.agents:
            cg1 = a.carrying.get("good1", 0)
            cg2 = a.carrying.get("good2", 0)
            hg1 = a.home_inventory.get("good1", 0)
            hg2 = a.home_inventory.get("good2", 0)
            total_carrying_good1 += cg1
            total_carrying_good2 += cg2
            total_home_good1 += hg1
            total_home_good2 += hg2
            agent_snap.append((a.id, a.x, a.y, cg1, cg2, hg1 + hg2))

        entry = {
            "step": step,
            "agents": agent_count,
            "resources": resource_count,
            "carry_g1": total_carrying_good1,
            "carry_g2": total_carrying_good2,
            "home_g1": total_home_good1,
            "home_g2": total_home_good2,
        }
        self._records.append(entry)

        # Canonical serialization for hash: step|agent_count|resource_count|sorted(agent tuples)|sorted(resources)
        # Resources already have a stable order via serialize()
        resource_serial = sim.grid.serialize()["resources"]  # list[(x,y,type)] sorted
        agent_snap.sort()  # sort by id, then position
        # Build a compact string
        comp = [
            f"s={step}",
            f"ac={agent_count}",
            f"rc={resource_count}",
            "A=" + ";".join(
                f"{i},{x},{y},{c1},{c2},{h}" for (i, x, y, c1, c2, h) in agent_snap
            ),
            "R=" + ";".join(f"{x},{y},{t}" for (x, y, t) in resource_serial),
        ]
        payload = "|".join(comp)
        self._update_hash(payload)

    def determinism_hash(self) -> str:
        if self._hash is None:
            return ""
        return self._hash.hexdigest()

    def records(self) -> Iterable[Dict[str, Any]]:  # lightweight accessor
        return tuple(self._records)


__all__ = ["MetricsCollector"]
